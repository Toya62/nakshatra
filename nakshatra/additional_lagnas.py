"""
nakshatra/additional_lagnas.py
Special Lagnas (Vishesha Lagna) Engine.

Computes the classical special ascendants used in Jaimini and Tajika/Parashara
practice that Nava Kundali and similar platforms expose:

  * Arudha Lagna (AL)      — Pada of the 1st house (image/perception of self).
  * Upapada Lagna (UL)     — Pada of the 12th house (marriage/companion).
  * Indu Lagna             — Prosperity lagna from the tithi at birth.
  * Bhrigu Lagna / Bindu   — Midpoint of Rahu and Moon longitudes (karmic trigger).
  * Ghati Lagna            — Power/authority lagna from ghatis elapsed at sunrise.
  * Sri Lagna              — Fortune/Dharma prominence from the 9th house axis.
  * Karakamsha Lagna       — Navamsa (D9) sign of the Atmakaraka (soul planet).

All longitudes are sidereal; house placement uses the chart's house system
(Whole Sign default), consistent with the rest of the Nakshatra engine. Each
lagna carries its classical rationale so the output reads like a master
astrologer's note rather than a bare table.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from nakshatra.chakra import ghati_context
from nakshatra.core import (
    SIGN_LORDS,
    ZODIAC_SIGNS,
    ChartData,
    PlanetPosition,
    get_degree_in_sign,
    get_sign,
)

VEDIC_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

MOVABLE_SIGNS = {"Aries", "Cancer", "Libra", "Capricorn"}
FIXED_SIGNS = {"Taurus", "Leo", "Scorpio", "Aquarius"}
DUAL_SIGNS = {"Gemini", "Virgo", "Sagittarius", "Pisces"}

NAVAMSA_STARTS: dict[str, int] = {
    # Movable: 1st navamsa = the sign itself (+0)
    "Aries": 0,
    "Cancer": 0,
    "Libra": 0,
    "Capricorn": 0,
    # Fixed: 1st navamsa = 9th sign from it (+8)
    "Taurus": 8,
    "Leo": 8,
    "Scorpio": 8,
    "Aquarius": 8,
    # Dual: 1st navamsa = 5th sign from it (+4)
    "Gemini": 4,
    "Virgo": 4,
    "Sagittarius": 4,
    "Pisces": 4,
}

# Classical one-line rationale for each special lagna.
LAGNA_RATIONALE: dict[str, str] = {
    "Arudha Lagna": "Image, public perception, and how the world sees the native (pada of the 1st).",
    "Upapada Lagna": "Marriage, spouse, and lasting companionship (pada of the 12th/Vyaya).",
    "Indu Lagna": "Wealth, prosperity, and financial flowering (tithi-based lunar lagna).",
    "Bhrigu Lagna": "Karmic trigger point — midpoint of Rahu and Moon; events cluster near transits to it.",
    "Ghati Lagna": "Authority, power, and worldly standing from ghatis elapsed at sunrise.",
    "Sri Lagna": "Fortune, dharma and auspicious blessings tied to the 9th/Bhagya axis.",
    "Karakamsha Lagna": "Soul's desires and spiritual direction — Atmakaraka's navamsa (D9) sign.",
}


def _planet_by_name(chart: ChartData, name: str) -> PlanetPosition | None:
    for p in chart.planets:
        if p.name == name:
            return p
    if chart.rahu and chart.rahu.name == name:
        return chart.rahu
    if chart.ketu and chart.ketu.name == name:
        return chart.ketu
    return None


def _sign_index(sign: str) -> int:
    return ZODIAC_SIGNS.index(sign)


def _house_for_longitude(lon: float, asc_sign: str) -> int:
    asc_idx = _sign_index(asc_sign)
    lon_idx = int((lon % 360.0) / 30.0) % 12
    return ((lon_idx - asc_idx) % 12) + 1


def _lon(lon: float) -> float:
    return (lon % 360.0 + 360.0) % 360.0


def _house_sign(chart: ChartData, house: int) -> str:
    """Whole-sign sign of a house (1-12) from the ascendant."""
    asc_idx = _sign_index(chart.ascendant.sign)
    return ZODIAC_SIGNS[(asc_idx + house - 1) % 12]


def _arudha_house(bhava_house: int, lord_house: int) -> int:
    """Arudha (pada) house of a bhava given its lord's house (1-indexed, mod 12)."""
    count = ((lord_house - bhava_house) % 12) + 1  # bhava=1 ... lord's house
    if count == 1:
        count = 10  # classical exception: pada on lord's own house -> 10th from lord
    return ((lord_house - 1) + (count - 1)) % 12 + 1


def _navamsa_sign(planet_lon: float) -> str:
    """Navamsa (D9) sign for a sidereal longitude using the classical movable/fixed/dual starts."""
    sign = get_sign(planet_lon)
    deg_in_sign = get_degree_in_sign(planet_lon)
    navamsa_index = int(deg_in_sign / (30.0 / 9.0)) % 9
    start_offset = NAVAMSA_STARTS[sign]
    return ZODIAC_SIGNS[(start_offset + navamsa_index) % 12]


def _tithi_number(sun_lon: float, moon_lon: float) -> int:
    """Tithi number (1-30) from Sun-Moon longitudinal difference. 30 = Amavasya."""
    diff = _lon(moon_lon - sun_lon)
    if diff == 0.0:
        return 30
    t = int(diff // 12.0) + 1
    return min(max(t, 1), 30)


def _find_planet_longitude(chart: ChartData, name: str) -> float | None:
    p = _planet_by_name(chart, name)
    return _lon(p.longitude) if p else None


class SpecialLagna(BaseModel):
    name: str
    sign: str
    house: int
    degree_in_sign: float
    longitude: float
    lord: str
    rationale: str


class SpecialLagnasReport(BaseModel):
    success: bool = True
    lagnas: list[SpecialLagna]
    notes: list[str] = Field(default_factory=list)


def calculate_special_lagnas(chart: ChartData) -> SpecialLagnasReport:
    """Compute all special lagnas for a natal ChartData.

    Requires Rahu and Ketu positions (Bhrigu uses Rahu; Karakamsha uses all
    seven grahas to find the Atmakaraka).
    """
    rahu_lon = _find_planet_longitude(chart, "Rahu")
    moon_lon = _find_planet_longitude(chart, "Moon")
    sun_lon = _find_planet_longitude(chart, "Sun")
    asc_sign = chart.ascendant.sign
    asc_house_sign = {h: _house_sign(chart, h) for h in range(1, 13)}

    lagnas: list[SpecialLagna] = []
    notes: list[str] = []

    # -------- Arudha Lagna (pada of 1st / Lagnesha) --------
    lagnesha_name = SIGN_LORDS[asc_sign]
    lagnesha = _planet_by_name(chart, lagnesha_name)
    if lagnesha:
        al_house = _arudha_house(1, lagnesha.house)
        al_sign = asc_house_sign[al_house]
        al_lord = SIGN_LORDS[al_sign]
        p_lon = _lon(lagnesha.longitude)
        lagnas.append(
            SpecialLagna(
                name="Arudha Lagna",
                sign=al_sign,
                house=al_house,
                degree_in_sign=round(get_degree_in_sign(p_lon), 4),
                longitude=round(p_lon, 4),
                lord=al_lord,
                rationale=LAGNA_RATIONALE["Arudha Lagna"],
            )
        )
        notes.append(
            f"Arudha Lagna (AL): Lagnesha {lagnesha_name} in House {lagnesha.house} → AL in "
            f"House {al_house} ({al_sign}). {LAGNA_RATIONALE['Arudha Lagna']}"
        )

    # -------- Upapada Lagna (pada of 12th) --------
    twelfth_lord_name = SIGN_LORDS[asc_house_sign[12]]
    twelfth_lord = _planet_by_name(chart, twelfth_lord_name)
    if twelfth_lord:
        ul_house = _arudha_house(12, twelfth_lord.house)
        ul_sign = asc_house_sign[ul_house]
        ul_lord = SIGN_LORDS[ul_sign]
        p_lon = _lon(twelfth_lord.longitude)
        lagnas.append(
            SpecialLagna(
                name="Upapada Lagna",
                sign=ul_sign,
                house=ul_house,
                degree_in_sign=round(get_degree_in_sign(p_lon), 4),
                longitude=round(p_lon, 4),
                lord=ul_lord,
                rationale=LAGNA_RATIONALE["Upapada Lagna"],
            )
        )
        notes.append(
            f"Upapada Lagna (UL): 12th lord {twelfth_lord_name} in House {twelfth_lord.house} → UL in "
            f"House {ul_house} ({ul_sign}). {LAGNA_RATIONALE['Upapada Lagna']}"
        )

    # -------- Indu Lagna (tithi count from Moon sign) --------
    if moon_lon is not None and sun_lon is not None:
        tithi = _tithi_number(sun_lon, moon_lon)
        moon_idx = _sign_index(get_sign(moon_lon))
        indu_idx = (moon_idx + tithi - 1) % 12
        indu_sign = ZODIAC_SIGNS[indu_idx]
        indu_house = _house_for_longitude(_lon(moon_lon + (tithi - 1) * 30.0), asc_sign)
        indu_lord = SIGN_LORDS[indu_sign]
        lagnas.append(
            SpecialLagna(
                name="Indu Lagna",
                sign=indu_sign,
                house=indu_house,
                degree_in_sign=round(get_degree_in_sign(_lon(moon_lon + (tithi - 1) * 30.0)), 4),
                longitude=round(_lon(moon_lon + (tithi - 1) * 30.0), 4),
                lord=indu_lord,
                rationale=LAGNA_RATIONALE["Indu Lagna"],
            )
        )
        notes.append(
            f"Indu Lagna: Tithi {tithi} counted from Moon sign → {indu_sign} (House {indu_house}). "
            f"{LAGNA_RATIONALE['Indu Lagna']}"
        )

    # -------- Bhrigu Lagna / Bhrigu Bindu (Rahu-Moon midpoint) --------
    if rahu_lon is not None and moon_lon is not None:
        bindu_lon = _lon((rahu_lon + moon_lon) / 2.0)
        bindu_sign = get_sign(bindu_lon)
        bindu_house = _house_for_longitude(bindu_lon, asc_sign)
        bindu_lord = SIGN_LORDS[bindu_sign]
        lagnas.append(
            SpecialLagna(
                name="Bhrigu Lagna",
                sign=bindu_sign,
                house=bindu_house,
                degree_in_sign=round(get_degree_in_sign(bindu_lon), 4),
                longitude=round(bindu_lon, 4),
                lord=bindu_lord,
                rationale=LAGNA_RATIONALE["Bhrigu Lagna"],
            )
        )
        notes.append(
            f"Bhrigu Lagna/Bindu: Midpoint of Rahu ({get_sign(rahu_lon)}) and Moon "
            f"({get_sign(moon_lon)}) → {bindu_sign} (House {bindu_house}) at {get_degree_in_sign(bindu_lon):.2f}°. "
            f"{LAGNA_RATIONALE['Bhrigu Lagna']}"
        )

    # -------- Ghati Lagna (power/authority from ghatis at sunrise) --------
    # Shared ghati count with the Ghatchakra: whole 24-min ghatis since the
    # TRUE local sunrise (not a fixed 06:00, and not the local time
    # mislabelled as UTC, as the old code did). The longitude follows the
    # file's own Indu Lagna convention — the ascendant's longitude carried
    # forward by (ghati_count - 1) signs — so the degree in sign is the
    # birth Lagna's degree, not a hardcoded 0.00 placeholder.
    ghati_count, _weekday_idx = ghati_context(chart)
    ghati_lon = _lon(chart.ascendant.longitude + (ghati_count - 1) * 30.0)
    ghati_sign = get_sign(ghati_lon)
    ghati_idx = _sign_index(ghati_sign)
    ghati_house = ((ghati_idx - _sign_index(asc_sign)) % 12) + 1
    ghati_lord = SIGN_LORDS[ghati_sign]
    lagnas.append(
        SpecialLagna(
            name="Ghati Lagna",
            sign=ghati_sign,
            house=ghati_house,
            degree_in_sign=round(get_degree_in_sign(ghati_lon), 4),
            longitude=round(ghati_lon, 4),
            lord=ghati_lord,
            rationale=LAGNA_RATIONALE["Ghati Lagna"],
        )
    )
    notes.append(
        f"Ghati Lagna: {ghati_count} ghatis (24-min units) from sunrise → {ghati_sign} "
        f"(House {ghati_house}). {LAGNA_RATIONALE['Ghati Lagna']}"
    )

    # -------- Sri Lagna (9th / Bhagya axis prosperity) --------
    ninth_sign = asc_house_sign[9]
    ninth_lord_name = SIGN_LORDS[ninth_sign]
    ninth_lord = _planet_by_name(chart, ninth_lord_name)
    if ninth_lord:
        sri_house = ninth_lord.house
        sri_sign = asc_house_sign[sri_house]
        sri_lord = SIGN_LORDS[sri_sign]
        p_lon = _lon(ninth_lord.longitude)
        lagnas.append(
            SpecialLagna(
                name="Sri Lagna",
                sign=sri_sign,
                house=sri_house,
                degree_in_sign=round(get_degree_in_sign(p_lon), 4),
                longitude=round(p_lon, 4),
                lord=sri_lord,
                rationale=LAGNA_RATIONALE["Sri Lagna"],
            )
        )
        notes.append(
            f"Sri Lagna: 9th lord {ninth_lord_name} in House {ninth_lord.house} → Sri Lagna in "
            f"House {sri_house} ({sri_sign}). {LAGNA_RATIONALE['Sri Lagna']}"
        )

    # -------- Karakamsha Lagna (Atmakaraka's navamsa/D9 sign) --------
    atma_name = None
    atma_lon = -1.0
    for p_name in VEDIC_PLANETS:
        p = _planet_by_name(chart, p_name)
        if p:
            pl = _lon(p.longitude)
            if pl > atma_lon:
                atma_lon = pl
                atma_name = p_name
    if atma_name:
        atma = _planet_by_name(chart, atma_name)
        if atma is None:
            return SpecialLagnasReport(lagnas=lagnas, notes=notes)
        d9_sign = _navamsa_sign(_lon(atma.longitude))
        # Karakamsha Lagna house = house of the D9 sign from ascendant
        k_idx = _sign_index(d9_sign)
        a_idx = _sign_index(asc_sign)
        k_house = ((k_idx - a_idx) % 12) + 1
        k_lord = SIGN_LORDS[d9_sign]
        lagnas.append(
            SpecialLagna(
                name="Karakamsha Lagna",
                sign=d9_sign,
                house=k_house,
                degree_in_sign=round(get_degree_in_sign(_lon(atma.longitude)), 4),
                longitude=round(_lon(atma.longitude), 4),
                lord=k_lord,
                rationale=LAGNA_RATIONALE["Karakamsha Lagna"],
            )
        )
        notes.append(
            f"Karakamsha Lagna: Atmakaraka {atma_name} (highest longitude) → navamsa sign {d9_sign} "
            f"(House {k_house} from asc). {LAGNA_RATIONALE['Karakamsha Lagna']}"
        )

    return SpecialLagnasReport(lagnas=lagnas, notes=notes)


def format_special_lagnas_markdown(report: SpecialLagnasReport) -> str:
    """Render the special lagnas report as GitHub-flavored Markdown."""
    lines = ["# Special Lagnas (Vishesha Lagna)", ""]
    for item in report.lagnas:
        lines.append(f"## {item.name}")
        lines.append(
            f"- **Sign:** {item.sign}  •  **House:** {item.house}  •  **Lord:** {item.lord}"
        )
        lines.append(
            f"- **Longitude:** {item.longitude}°  •  **Degree in Sign:** {item.degree_in_sign}°"
        )
        lines.append(f"- **Classical basis:** {item.rationale}")
        lines.append("")
    if report.notes:
        lines.append("## Calculation Notes")
        for n in report.notes:
            lines.append(f"- {n}")
        lines.append("")
    lines.append("*All longitudes sidereal; houses per chart house system (Whole Sign default).*")
    return "\n".join(lines)
