"""
Nakshatra Model Context Protocol (MCP) Server
Enterprise Vedic Astrology tools for AI agents (Claude Code, Cursor, VS Code, Gemini).

Provides deterministic astronomical ephemeris tools:
1. calculate_birth_chart: Sidereal positions, D1..D60, dashas, ashtakavarga, shadbala
2. get_daily_panchanga: 5 limbs of Vedic time (Tithi, Vara, Nakshatra, Yoga, Karana)
3. match_kundali_compatibility: 36-point Ashtakoota matching + Kuja Dosha
4. get_muhurtha_election: 24 Horas, 16 Choghadiyas, Abhijit, Rahu Kalam, Siddhi Yogas
5. get_transits_gochar: Gochara transits, Sade Sati, Ashtakavarga Kakshas (3°45')
6. detect_vedic_yogas: 40+ classical Parashara yogas
7. consult_scripture_rag: Scripture-grounded classical citations (BPHS, Phaladeepika)
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime

from mcp.server.mcpserver import MCPServer

from nakshatra.compatibility import calculate_compatibility
from nakshatra.core import (
    Ayanamsa,
    BirthData,
    HouseSystem,
    calculate_chart,
)
from nakshatra.muhurtha import calculate_muhurtha
from nakshatra.panchanga import calculate_panchanga
from nakshatra.transits import calculate_transits
from nakshatra.yogas import detect_yogas, format_yogas_markdown, format_yogas_table

server = MCPServer(
    name="nakshatra",
    instructions=(
        "Nakshatra Vedic Astrology Engine - Deterministic Swiss Ephemeris tools. "
        "Always use these tools for any astronomical degrees, planetary positions, "
        "dashas, compatibility scores, and muhurtha timings. Never calculate "
        "planetary coordinates mentally."
    ),
)


# ---------------------------------------------------------------------------
# Tool 1: Birth Chart Calculation
# ---------------------------------------------------------------------------


@server.tool(
    description=(
        "Calculate deterministic Vedic birth chart (Kundali) using Swiss Ephemeris. "
        "Computes sidereal planets, houses, Vimshottari dasha, Shodashavarga (D1..D60), "
        "Ashtakavarga, and Shadbala."
    )
)
def calculate_birth_chart(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int = 0,
    latitude: float = 0.0,
    longitude: float = 0.0,
    timezone: str = "UTC",
    place_name: str | None = None,
    ayanamsa: str = "jhora_lahiri",
    house_system: str = "WholeSign",
    format: str = "summary",
) -> str:
    """Calculate Vedic birth chart."""
    ay = Ayanamsa(ayanamsa) if ayanamsa in [a.value for a in Ayanamsa] else Ayanamsa.JHORA_LAHIRI
    hs = (
        HouseSystem(house_system)
        if house_system in [h.value for h in HouseSystem]
        else HouseSystem.WHOLE_SIGN
    )

    birth = BirthData(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        second=second,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        place_name=place_name,
    )
    chart = calculate_chart(birth, ayanamsa=ay, house_system=hs)

    if format == "json":
        return chart.model_dump_json(indent=2)

    # Summary format
    lines = []
    lines.append(f"VEDIC BIRTH CHART (KUNDALI): {place_name or f'{latitude}, {longitude}'}")
    lines.append(
        f"Date & Time: {year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d} ({timezone})"
    )
    lines.append(
        f"Ayanamsa: {ay.value} (Value: {chart.ayanamsa_value:.4f}°) | House System: {hs.value}"
    )
    lines.append(
        f"Ascendant (Lagna): {chart.ascendant.sign} ({chart.ascendant.degree_in_sign:.2f}°)"
    )
    lines.append("-" * 70)
    lines.append(
        f"{'Planet':<10} {'Sign':<12} {'Degree':<10} {'Nakshatra (Pada)':<20} {'House':<6} Retro"
    )
    lines.append("-" * 70)
    for p in chart.planets:
        r_flag = "(R)" if p.retrograde else "   "
        lines.append(
            f"{p.name:<10} {p.sign:<12} {p.degree_in_sign:05.2f}°    "
            f"{p.nakshatra} (Pada {p.pada}){'':<4} {p.house:<6} {r_flag}"
        )
    lines.append("-" * 70)
    if chart.dashas:
        lines.append(
            f"Vimshottari Balance at Birth: {chart.dashas.balance_lord} "
            f"({chart.dashas.balance_years:.2f} years, Nakshatra Lord: {chart.dashas.birth_nakshatra_lord})"
        )
        if chart.dashas.mahadashas:
            md0 = chart.dashas.mahadashas[0]
            lines.append(f"First Mahadasha: {md0.lord} ({md0.start} to {md0.end})")
    if chart.ashtakavarga:
        sav_str = " ".join(str(b) for b in chart.ashtakavarga.sarvashtakavarga)
        lines.append(
            f"Sarvashtakavarga (Aries..Pisces): {sav_str} (Total: {chart.ashtakavarga.grand_total})"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 2: Daily Panchanga
# ---------------------------------------------------------------------------


@server.tool(
    description=(
        "Calculate 5 limbs of Vedic time (Panchanga): Tithi, Vara, Nakshatra, "
        "Yoga, Karana, Bhadra/Vishti alerts, and solar markers (Sunrise/Sunset)."
    )
)
def get_daily_panchanga(
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    second: int = 0,
    latitude: float = 28.6139,
    longitude: float = 77.2090,
    timezone: str = "Asia/Kolkata",
    ayanamsa: str = "jhora_lahiri",
    format: str = "table",
) -> str:
    """Calculate Vedic Panchanga."""
    ay = Ayanamsa(ayanamsa) if ayanamsa in [a.value for a in Ayanamsa] else Ayanamsa.JHORA_LAHIRI
    dt = datetime(year, month, day, hour, minute, second)
    p = calculate_panchanga(dt, latitude, longitude, timezone, ayanamsa=ay)
    if format == "json":
        return p.model_dump_json(indent=2)
    return p.to_table()


# ---------------------------------------------------------------------------
# Tool 3: Kundali Matching & Compatibility (Ashtakoota + Kuja Dosha)
# ---------------------------------------------------------------------------


@server.tool(
    description=(
        "Calculate complete 36-point Ashtakoota marriage compatibility and Kuja Dosha (Manglik) "
        "analysis between Bride and Groom. Evaluates all 8 Kutas (Varna, Vashya, Tara, Yoni, "
        "Graha Maitri, Gana, Bhakoot, Nadi) with classical dosha cancellations and extended kutas."
    )
)
def match_kundali_compatibility(
    b_year: int,
    b_month: int,
    b_day: int,
    b_hour: int,
    b_minute: int,
    b_latitude: float,
    b_longitude: float,
    b_timezone: str,
    g_year: int,
    g_month: int,
    g_day: int,
    g_hour: int,
    g_minute: int,
    g_latitude: float,
    g_longitude: float,
    g_timezone: str,
    bride_name: str = "Bride",
    groom_name: str = "Groom",
    ayanamsa: str = "jhora_lahiri",
    format: str = "table",
) -> str:
    """Calculate relationship compatibility."""
    ay = Ayanamsa(ayanamsa) if ayanamsa in [a.value for a in Ayanamsa] else Ayanamsa.JHORA_LAHIRI
    b_birth = BirthData(
        b_year, b_month, b_day, b_hour, b_minute, 0, b_latitude, b_longitude, b_timezone
    )
    g_birth = BirthData(
        g_year, g_month, g_day, g_hour, g_minute, 0, g_latitude, g_longitude, g_timezone
    )

    b_chart = calculate_chart(b_birth, ayanamsa=ay)
    g_chart = calculate_chart(g_birth, ayanamsa=ay)

    report = calculate_compatibility(b_chart, g_chart, bride_name=bride_name, groom_name=groom_name)
    if format == "json":
        return report.model_dump_json(indent=2)
    return report.to_table()


# ---------------------------------------------------------------------------
# Tool 4: Muhurtha & Auspicious Election
# ---------------------------------------------------------------------------


@server.tool(
    description=(
        "Evaluate Vedic Muhurtha and electional astrology for a given timestamp and location. "
        "Computes 24 Chaldean Horas, 16 Choghadiyas, Abhijit & Brahma Muhurthas, Rahu Kalam octant, "
        "and classical Siddhi Yogas (Sarvartha Siddhi, Amrita Siddhi, Guru Pushya)."
    )
)
def get_muhurtha_election(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int = 0,
    latitude: float = 28.6139,
    longitude: float = 77.2090,
    timezone: str = "Asia/Kolkata",
    ayanamsa: str = "jhora_lahiri",
    format: str = "table",
) -> str:
    """Evaluate auspicious timing (Muhurtha)."""
    ay = Ayanamsa(ayanamsa) if ayanamsa in [a.value for a in Ayanamsa] else Ayanamsa.JHORA_LAHIRI
    dt = datetime(year, month, day, hour, minute, second)
    report = calculate_muhurtha(dt, latitude, longitude, timezone, ayanamsa=ay)
    if format == "json":
        return report.model_dump_json(indent=2)
    return report.to_table()


# ---------------------------------------------------------------------------
# Tool 5: Planetary Transits (Gochar) & Kakshas
# ---------------------------------------------------------------------------


@server.tool(
    description=(
        "Calculate Vedic planetary transits (Gochar) relative to a natal chart. "
        "Includes Saturn Sade Sati status, Double Transit (Jupiter + Saturn) manifestations, "
        "and Ashtakavarga Gochara Kakshas (8 sub-arc divisions of 3°45' with BAV bindu activation)."
    )
)
def get_transits_gochar(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    birth_minute: int,
    birth_latitude: float,
    birth_longitude: float,
    birth_timezone: str,
    transit_iso_datetime: str | None = None,
    transit_latitude: float | None = None,
    transit_longitude: float | None = None,
    ayanamsa: str = "jhora_lahiri",
    format: str = "table",
) -> str:
    """Calculate Gochar transits."""
    ay = Ayanamsa(ayanamsa) if ayanamsa in [a.value for a in Ayanamsa] else Ayanamsa.JHORA_LAHIRI
    birth = BirthData(
        birth_year,
        birth_month,
        birth_day,
        birth_hour,
        birth_minute,
        0,
        birth_latitude,
        birth_longitude,
        birth_timezone,
    )
    chart = calculate_chart(birth, ayanamsa=ay)

    t_dt = None
    if transit_iso_datetime:
        t_dt = datetime.fromisoformat(transit_iso_datetime)

    rep = calculate_transits(
        chart,
        transit_date=t_dt,
        transit_latitude=transit_latitude,
        transit_longitude=transit_longitude,
    )
    if format == "json":
        return rep.model_dump_json(indent=2)
    return rep.to_table()


# ---------------------------------------------------------------------------
# Tool 6: Classical Vedic Yogas Detection
# ---------------------------------------------------------------------------


@server.tool(
    description=(
        "Scan a natal horoscope for 40+ classical Parashara yogas (Raja Yogas, "
        "Dhana Yogas, Pancha Mahapurusha Yogas, Neecha Bhanga, Gajakesari, Budhaditya, etc.)."
    )
)
def detect_vedic_yogas(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int = 0,
    latitude: float = 28.6139,
    longitude: float = 77.2090,
    timezone: str = "Asia/Kolkata",
    ayanamsa: str = "jhora_lahiri",
    format: str = "table",
) -> str:
    """Detect Parashara Yogas."""
    ay = Ayanamsa(ayanamsa) if ayanamsa in [a.value for a in Ayanamsa] else Ayanamsa.JHORA_LAHIRI
    birth = BirthData(year, month, day, hour, minute, second, latitude, longitude, timezone)
    chart = calculate_chart(birth, ayanamsa=ay)
    yogas = detect_yogas(chart)

    if format == "json":
        return json.dumps([y.model_dump() for y in yogas], indent=2)
    if format == "markdown":
        return format_yogas_markdown(yogas)
    return format_yogas_table(yogas)


# ---------------------------------------------------------------------------
# Tool 7: Classical Scripture RAG Consultation
# ---------------------------------------------------------------------------


@server.tool(
    description=(
        "Consult canonical Vedic astrology texts (Brihat Parashara Hora Shastra, Phaladeepika) "
        "using hybrid BM25 + dense retrieval with verse citations and ethical guardrails."
    )
)
def consult_scripture_rag(
    question: str,
    top_k: int = 5,
    birth_year: int | None = None,
    birth_month: int | None = None,
    birth_day: int | None = None,
    birth_hour: int | None = None,
    birth_minute: int | None = None,
    birth_latitude: float | None = None,
    birth_longitude: float | None = None,
    birth_timezone: str | None = None,
) -> str:
    """Consult Vedic scriptures."""
    from nakshatra.ai.service import RAGService

    service = RAGService()

    birth_ctx = None
    if (
        birth_year is not None
        and birth_month is not None
        and birth_day is not None
        and birth_hour is not None
        and birth_minute is not None
        and birth_latitude is not None
        and birth_longitude is not None
        and birth_timezone is not None
    ):
        b = BirthData(
            birth_year,
            birth_month,
            birth_day,
            birth_hour,
            birth_minute,
            0,
            birth_latitude,
            birth_longitude,
            birth_timezone,
        )
        c = calculate_chart(b)
        birth_ctx = c.model_dump()

    try:
        answer, refs = service.ask(question, top_k=top_k, birth_context=birth_ctx)
        out = []
        out.append(f"CONSULTATION SYNTHESIS (Model: {answer.model}):")
        out.append(answer.answer)
        out.append("\nCANONICAL SCRIPTURAL CITATIONS:")
        for r in answer.citations:
            out.append(f"- {r.work} (Ch. {r.chapter}, V. {r.verse}): {r.text[:120]}...")
        return "\n".join(out)
    except Exception as e:
        return f"RAG Query failed: {str(e)}. Ensure corpus index is ingested via 'nakshatra rag ingest'."


# ---------------------------------------------------------------------------
# Server Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entrypoint for Nakshatra MCP Server."""
    parser = argparse.ArgumentParser(description="Nakshatra Model Context Protocol (MCP) Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport type (default: stdio for Claude Desktop / Cursor; sse for HTTP)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for SSE server")
    parser.add_argument("--port", type=int, default=8005, help="Port for SSE server")
    args = parser.parse_args()

    if args.transport == "stdio":
        server.run(transport="stdio")
    elif args.transport == "sse":
        server.run(transport="sse", host=args.host, port=args.port)
    else:
        server.run(transport=args.transport)


if __name__ == "__main__":
    main()
