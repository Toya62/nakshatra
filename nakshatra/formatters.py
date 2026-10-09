"""
Nakshatra Output Formatters
Provides ASCII table, plain text, Markdown, CSV, and ASCII chart renderings of ChartData.
"""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nakshatra.core import ChartData


def _dec_to_dms(deg: float) -> str:
    """Format decimal degrees to DD° MM' SS\"."""
    d = int(deg)
    m_float = abs(deg - d) * 60.0
    m = int(m_float)
    s = round((m_float - m) * 60.0)
    if s >= 60:
        s = 0
        m += 1
    if m >= 60:
        m = 0
        d += 1
    return f"{d:02d}° {m:02d}' {s:02d}\""


def format_table(chart: ChartData) -> str:
    """Format chart into human-readable ASCII tables."""
    lines: list[str] = []
    b = chart.birth_data

    # Header
    lines.append("=" * 88)
    lines.append("                         NAKSHATRA VEDIC BIRTH CHART")
    lines.append("=" * 88)
    place_str = f" ({b.place_name})" if b.place_name else ""
    lines.append(f" Date of Birth : {b.year:04d}-{b.month:02d}-{b.day:02d} {b.hour:02d}:{b.minute:02d}:{b.second:02d}")
    lines.append(f" Coordinates   : {abs(b.latitude):.4f}°{'N' if b.latitude>=0 else 'S'}, {abs(b.longitude):.4f}°{'E' if b.longitude>=0 else 'W'}{place_str}")
    lines.append(f" Timezone      : {b.timezone}")
    lines.append(f" Ayanamsa      : {chart.ayanamsa.value.upper()} ({_dec_to_dms(chart.ayanamsa_value or 0.0)})")
    lines.append(f" House System  : {chart.house_system.value.replace('_', ' ').title()}")
    lines.append("-" * 88)

    # Planetary Positions Table
    lines.append(" PLANETARY POSITIONS")
    lines.append("-" * 88)
    lines.append(f"{'Body':<11} {'Sign':<12} {'Sign Deg':<13} {'Nakshatra':<16} {'Pada':<5} {'Hse':<4} {'Motion':<8} {'Speed':<9}")
    lines.append("-" * 88)

    # Ascendant first
    asc = chart.ascendant
    lines.append(f"{'Ascendant':<11} {asc.sign:<12} {_dec_to_dms(asc.degree_in_sign):<13} {asc.nakshatra:<16} {asc.pada:<5} {'1':<4} {'Direct':<8} {'-':<9}")

    for p in chart.planets + [chart.rahu, chart.ketu]:
        motion = "Retro" if p.retrograde else "Direct"
        spd = f"{p.speed:+.3f}°/d"
        lines.append(f"{p.name:<11} {p.sign:<12} {_dec_to_dms(p.degree_in_sign):<13} {p.nakshatra:<16} {p.pada:<5} {str(p.house):<4} {motion:<8} {spd:<9}")

    lines.append("-" * 88)

    # Divisional Charts (D1, D9 Navamsa, D10 Dasamsa)
    if chart.vargas:
        lines.append(" DIVISIONAL CHARTS (Rasi D1 & Navamsa D9)")
        lines.append("-" * 88)
        lines.append(f"{'Body':<11} {'D1 (Rasi)':<16} {'D9 (Navamsa)':<16} {'D10 (Dasamsa)':<16}")
        lines.append("-" * 88)
        d1 = chart.vargas.get("D1", {})
        d9 = chart.vargas.get("D9", {})
        d10 = chart.vargas.get("D10", {})
        for body in ["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "North Node", "South Node"]:
            lines.append(f"{body:<11} {d1.get(body, '-'):<16} {d9.get(body, '-'):<16} {d10.get(body, '-'):<16}")
        lines.append("-" * 88)

    # Vimshottari Dashas
    if chart.dashas:
        d = chart.dashas
        lines.append(f" VIMSHOTTARI DASHA  (Birth Nakshatra: {d.birth_nakshatra}, Balance: {d.balance_lord} {d.balance_years:.2f} yrs)")
        lines.append("-" * 88)
        if d.current_md and d.current_ad:
            curr_str = f" Active: MD [{d.current_md.lord}] -> AD [{d.current_ad.lord}]"
            if d.current_pd:
                curr_str += f" -> PD [{d.current_pd.lord}]"
            lines.append(curr_str)
            lines.append("-" * 88)
        lines.append(" Mahadashas Timeline:")
        for md in d.mahadashas:
            active_marker = " *" if d.current_md and d.current_md.lord == md.lord else ""
            dur_str = f"({md.duration_years:4.1f} yrs)" if md.duration_years is not None else ""
            lines.append(f"   {md.lord:<11} : {md.start[:10]} to {md.end[:10]} {dur_str}{active_marker}")
        lines.append("-" * 88)

    # Ashtakavarga
    if chart.ashtakavarga:
        av = chart.ashtakavarga
        lines.append(f" ASHTAKAVARGA (Sarvashtakavarga Grand Total: {av.grand_total} bindus)")
        lines.append("-" * 88)
        signs_short = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        header_row = f"{'Planet':<9} " + " ".join(f"{s:>4}" for s in signs_short) + " Total"
        lines.append(header_row)
        lines.append("-" * 88)
        for planet, bindus in av.bhinnashtakavarga.items():
            row_str = f"{planet:<9} " + " ".join(f"{b:>4}" for b in bindus) + f" {sum(bindus):>5}"
            lines.append(row_str)
        lines.append("-" * 88)
        sav_row = f"{'SAV':<9} " + " ".join(f"{b:>4}" for b in av.sarvashtakavarga) + f" {av.grand_total:>5}"
        lines.append(sav_row)
        lines.append("-" * 88)

    # Shadbala
    if chart.shadbala:
        lines.append(" SHADBALA (Planetary Strength in Rupas)")
        lines.append("-" * 88)
        lines.append(f"{'Planet':<9} {'Total Rupas':<12} {'Required':<10} {'Strength':<10} {'Sthana':<8} {'Dig':<8} {'Kala':<8}")
        lines.append("-" * 88)
        for p_name, sb in chart.shadbala.items():
            status = "STRONG" if sb.sufficient else "WEAK"
            lines.append(f"{p_name:<9} {sb.total_rupas:<12.2f} {sb.required_rupas:<10.2f} {status:<10} {sb.sthana_bala:<8.1f} {sb.dig_bala:<8.1f} {sb.kala_bala:<8.1f}")
        lines.append("-" * 88)

    # Upagrahas
    if chart.upagrahas:
        lines.append(" UPAGRAHAS (Shadow Planets)")
        lines.append("-" * 88)
        up_parts = [f"{u.name}: {u.sign} {_dec_to_dms(u.degree_in_sign)} (H{u.house})" for u in chart.upagrahas]
        lines.append("  " + " | ".join(up_parts[:3]))
        if len(up_parts) > 3:
            lines.append("  " + " | ".join(up_parts[3:]))
        lines.append("=" * 88)

    return "\n".join(lines)


def format_markdown(chart: ChartData) -> str:
    """Format chart into GitHub-flavored Markdown document."""
    md: list[str] = []
    b = chart.birth_data

    md.append(f"# Nakshatra Vedic Birth Chart")
    md.append("")
    md.append(f"**Date & Time**: `{b.year:04d}-{b.month:02d}-{b.day:02d} {b.hour:02d}:{b.minute:02d}:{b.second:02d}`  ")
    md.append(f"**Location**: `{abs(b.latitude):.4f}°{'N' if b.latitude>=0 else 'S'}, {abs(b.longitude):.4f}°{'E' if b.longitude>=0 else 'W'}` ({b.place_name or b.timezone})  ")
    md.append(f"**Ayanamsa**: `{chart.ayanamsa.value}` (`{_dec_to_dms(chart.ayanamsa_value or 0.0)}`) | **House System**: `{chart.house_system.value}`")
    md.append("")

    # Planets
    md.append("## Planetary Positions")
    md.append("")
    md.append("| Planet | Sign | Degree | Nakshatra | Pada | House | Motion | Speed |")
    md.append("|:---|:---|:---|:---|:---:|:---:|:---:|:---|")
    asc = chart.ascendant
    md.append(f"| **Ascendant** | {asc.sign} | {_dec_to_dms(asc.degree_in_sign)} | {asc.nakshatra} | {asc.pada} | 1 | Direct | - |")
    for p in chart.planets + [chart.rahu, chart.ketu]:
        motion = "Retrograde" if p.retrograde else "Direct"
        md.append(f"| **{p.name}** | {p.sign} | {_dec_to_dms(p.degree_in_sign)} | {p.nakshatra} | {p.pada} | {p.house} | {motion} | {p.speed:+.3f}°/d |")
    md.append("")

    # Dashas
    if chart.dashas:
        d = chart.dashas
        md.append("## Vimshottari Dasha")
        md.append("")
        md.append(f"- **Birth Nakshatra**: {d.birth_nakshatra} ({d.birth_nakshatra_lord})")
        md.append(f"- **Balance at Birth**: {d.balance_lord} ({d.balance_years:.2f} years)")
        if d.current_md and d.current_ad:
            curr = f"`MD: {d.current_md.lord}` → `AD: {d.current_ad.lord}`"
            if d.current_pd:
                curr += f" → `PD: {d.current_pd.lord}`"
            md.append(f"- **Current Active**: {curr}")
        md.append("")
        md.append("| Mahadasha Lord | Start Date | End Date | Duration (Years) |")
        md.append("|:---|:---|:---|:---:|")
        for md_period in d.mahadashas:
            dur_str = f"{md_period.duration_years:.1f}" if md_period.duration_years is not None else "-"
            md.append(f"| **{md_period.lord}** | {md_period.start[:10]} | {md_period.end[:10]} | {dur_str} |")
        md.append("")

    # Ashtakavarga
    if chart.ashtakavarga:
        av = chart.ashtakavarga
        md.append("## Ashtakavarga")
        md.append("")
        md.append(f"**Sarvashtakavarga Grand Total**: `{av.grand_total}` bindus")
        md.append("")
        signs = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
        header = "| Planet | " + " | ".join(signs) + " | Total |"
        sep = "|:---| " + " | ".join([":---:"] * 12) + " |:---:|"
        md.append(header)
        md.append(sep)
        for planet, bindus in av.bhinnashtakavarga.items():
            row = f"| **{planet}** | " + " | ".join(str(b) for b in bindus) + f" | {sum(bindus)} |"
            md.append(row)
        sav_row = f"| **SAV** | " + " | ".join(str(b) for b in av.sarvashtakavarga) + f" | **{av.grand_total}** |"
        md.append(sav_row)
        md.append("")

    # Shadbala
    if chart.shadbala:
        md.append("## Shadbala (Planetary Strength)")
        md.append("")
        md.append("| Planet | Total Rupas | Required Rupas | Status | Sthana | Dig | Kala | Cheshta |")
        md.append("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
        for p_name, sb in chart.shadbala.items():
            status = "Strong" if sb.sufficient else "Weak"
            md.append(f"| **{p_name}** | {sb.total_rupas:.2f} | {sb.required_rupas:.2f} | {status} | {sb.sthana_bala:.1f} | {sb.dig_bala:.1f} | {sb.kala_bala:.1f} | {sb.cheshta_bala:.1f} |")
        md.append("")

    return "\n".join(md)


def format_csv(chart: ChartData) -> str:
    """Format planets and houses into CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Body",
        "Sign",
        "Degree_In_Sign",
        "Longitude",
        "Nakshatra",
        "Pada",
        "Nakshatra_Lord",
        "House",
        "Retrograde",
        "Speed",
    ])

    asc = chart.ascendant
    writer.writerow([
        "Ascendant",
        asc.sign,
        f"{asc.degree_in_sign:.4f}",
        f"{asc.longitude:.4f}",
        asc.nakshatra,
        asc.pada,
        asc.nakshatra_lord,
        1,
        False,
        "0.0000",
    ])

    for p in chart.planets + [chart.rahu, chart.ketu]:
        writer.writerow([
            p.name,
            p.sign,
            f"{p.degree_in_sign:.4f}",
            f"{p.longitude:.4f}",
            p.nakshatra,
            p.pada,
            p.nakshatra_lord,
            p.house,
            p.retrograde,
            f"{p.speed:.4f}",
        ])

    return buf.getvalue()


def format_chart_diagram(chart: ChartData) -> str:
    """
    Render South Indian 4x4 style chart box diagram in ASCII.
    Layout:
    +-----------+-----------+-----------+-----------+
    | Pisces    | Aries     | Taurus    | Gemini    |
    | (House)   | (House)   | (House)   | (House)   |
    +-----------+-----------+-----------+-----------+
    | Aquarius  |                       | Cancer    |
    +-----------+      NAKSHATRA        +-----------+
    | Capricorn |      VEDIC D1         | Leo       |
    +-----------+                       +-----------+
    | Sagittarius| Scorpio  | Libra     | Virgo     |
    +-----------+-----------+-----------+-----------+
    """
    # Group bodies by sign
    sign_bodies: dict[str, list[str]] = {s: [] for s in [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]}

    sign_bodies[chart.ascendant.sign].append("Asc")
    for p in chart.planets + [chart.rahu, chart.ketu]:
        abbr = p.name[:2]
        if p.name in ("North Node", "Rahu"):
            abbr = "Ra"
        elif p.name in ("South Node", "Ketu"):
            abbr = "Ke"
        elif p.name == "Mercury":
            abbr = "Me"
        elif p.name == "Jupiter":
            abbr = "Ju"
        elif p.name == "Venus":
            abbr = "Ve"
        elif p.name == "Saturn":
            abbr = "Sa"
        elif p.name == "Sun":
            abbr = "Su"
        elif p.name == "Moon":
            abbr = "Mo"
        elif p.name == "Mars":
            abbr = "Ma"
        if p.retrograde:
            abbr += "(R)"
        sign_bodies[p.sign].append(abbr)

    def cell_lines(sign_name: str) -> tuple[str, str]:
        short_sign = sign_name[:3]
        bodies = sign_bodies.get(sign_name, [])
        bodies_str = " ".join(bodies) if bodies else "-"
        return f"{short_sign:<4}", f"{bodies_str:<12}"[:12]

    col_w = 14
    h_line = "+" + ("-" * col_w + "+") * 4

    p_s, p_b = cell_lines("Pisces")
    ar_s, ar_b = cell_lines("Aries")
    ta_s, ta_b = cell_lines("Taurus")
    ge_s, ge_b = cell_lines("Gemini")

    aq_s, aq_b = cell_lines("Aquarius")
    cn_s, cn_b = cell_lines("Cancer")

    cp_s, cp_b = cell_lines("Capricorn")
    le_s, le_b = cell_lines("Leo")

    sg_s, sg_b = cell_lines("Sagittarius")
    sc_s, sc_b = cell_lines("Scorpio")
    li_s, li_b = cell_lines("Libra")
    vi_s, vi_b = cell_lines("Virgo")

    mid_blank = " " * (col_w * 2 + 1)

    diagram = [
        h_line,
        f"| {p_s:<12} | {ar_s:<12} | {ta_s:<12} | {ge_s:<12} |",
        f"| {p_b:<12} | {ar_b:<12} | {ta_b:<12} | {ge_b:<12} |",
        h_line,
        f"| {aq_s:<12} |{mid_blank}| {cn_s:<12} |",
        f"| {aq_b:<12} |       NAKSHATRA VEDIC D1       | {cn_b:<12} |",
        f"|{'-' * col_w}+                +                +{'-' * col_w}|",
        f"| {cp_s:<12} |    Ayanamsa: {chart.ayanamsa.value:<10}    | {le_s:<12} |",
        f"| {cp_b:<12} |{mid_blank}| {le_b:<12} |",
        h_line,
        f"| {sg_s:<12} | {sc_s:<12} | {li_s:<12} | {vi_s:<12} |",
        f"| {sg_b:<12} | {sc_b:<12} | {li_b:<12} | {vi_b:<12} |",
        h_line,
    ]
    return "\n".join(diagram)
