"""
nakshatra/kalsarp.py
Kalsarp (Kalasarpa) Dosha Analyzer.

Kalsarp Dosha forms when all seven classical Grahas (Sun, Moon, Mars, Mercury,
Jupiter, Venus, Saturn) are hemmed between Rahu and Ketu — i.e. every planet
falls within the zodiacal arc from Rahu to Ketu (or Ketu to Rahu) in the
direction of zodiacal motion.

Twelve classical Kalsarp types are named by the Rahu–Ketu house axis:

  1. Anant     — Rahu 1st / Ketu 7th
  2. Kulik     — Rahu 2nd / Ketu 8th
  3. Vasuki    — Rahu 3rd / Ketu 9th
  4. Shankhpal — Rahu 4th / Ketu 10th
  5. Padma     — Rahu 5th / Ketu 11th
  6. Mahapadma — Rahu 6th / Ketu 12th
  7. Takshak   — Rahu 7th / Ketu 1st
  8. Karkotak  — Rahu 8th / Ketu 2nd
  9. Shankhachur — Rahu 9th / Ketu 3rd
  10. Ghatak   — Rahu 10th / Ketu 4th
  11. Vishdhar — Rahu 11th / Ketu 5th
  12. Sheshnag — Rahu 12th / Ketu 6th

Classification:
  * Purna (Complete) Kalsarp — every classical planet lies inside the Rahu→Ketu arc.
  * Ardh (Partial) Kalsarp   — at least one planet falls outside the arc.

All longitudes are sidereal and house placement uses the chart's house system
(Whole Sign default), consistent with the rest of the Nakshatra engine.
"""

from __future__ import annotations

from pydantic import BaseModel

from nakshatra.core import ZODIAC_SIGNS, ChartData, PlanetPosition

VEDIC_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Rahu house → (Kalsarp type name, description)
KALSARP_TYPES: dict[int, tuple[str, str]] = {
    1: ("Anant", "Rahu in Lagna, Ketu in 7th — afflicts self, health, spouse and partnerships."),
    2: (
        "Kulik",
        "Rahu in 2nd, Ketu in 8th — afflicts wealth, family, speech and sudden gains/losses.",
    ),
    3: (
        "Vasuki",
        "Rahu in 3rd, Ketu in 9th — afflicts courage, siblings, effort, destiny and long journeys.",
    ),
    4: (
        "Shankhpal",
        "Rahu in 4th, Ketu in 10th — afflicts home, mother, comforts, career and public status.",
    ),
    5: (
        "Padma",
        "Rahu in 5th, Ketu in 11th — afflicts progeny, intellect, romance, gains and elder siblings.",
    ),
    6: (
        "Mahapadma",
        "Rahu in 6th, Ketu in 12th — afflicts health, enemies, debts, isolation and expenditure.",
    ),
    7: (
        "Takshak",
        "Rahu in 7th, Ketu in 1st — afflicts marriage, partnerships, self and physical vitality.",
    ),
    8: (
        "Karkotak",
        "Rahu in 8th, Ketu in 2nd — afflicts longevity, sudden events, wealth and family.",
    ),
    9: (
        "Shankhachur",
        "Rahu in 9th, Ketu in 3rd — afflicts dharma, luck, gurus, courage and short travel.",
    ),
    10: ("Ghatak", "Rahu in 10th, Ketu in 4th — afflicts career, authority, home and inner peace."),
    11: (
        "Vishdhar",
        "Rahu in 11th, Ketu in 5th — afflicts gains, friendships, progeny and creative intelligence.",
    ),
    12: (
        "Sheshnag",
        "Rahu in 12th, Ketu in 6th — afflicts expenditure, foreign matters, health and service.",
    ),
}

# Arc direction: Rahu → Ketu in zodiacal order.
_ZODIAC_INDEX = {sign: i for i, sign in enumerate(ZODIAC_SIGNS)}


def _lon_in_range(lon: float, start: float, end: float) -> bool:
    """True if lon lies in the forward zodiacal arc from start to end (inclusive of start, exclusive of end)."""
    start = start % 360.0
    end = end % 360.0
    if start == end:
        return True  # full circle
    if start < end:
        return start <= lon < end
    # wrap-around arc (e.g. 330° → 30°)
    return lon >= start or lon < end


def _planet_longitude(planet: PlanetPosition) -> float:
    return (planet.longitude % 360.0 + 360.0) % 360.0


def _is_between_rah_ketu(planet_lon: float, rahu_lon: float, ketu_lon: float) -> bool:
    """Planet lies between Rahu and Ketu moving in zodiacal order (Rahu → Ketu)."""
    return _lon_in_range(planet_lon, rahu_lon, ketu_lon)


class KalsarpPlanetStatus(BaseModel):
    name: str
    sign: str
    house: int
    degree_in_sign: float
    longitude: float
    within_axis: bool


class KalsarpReport(BaseModel):
    success: bool = True
    has_kalsarp: bool
    classification: str  # "Purna" | "Ardh" | "None"
    rahu_house: int
    ketu_house: int
    kalsarp_type: str | None = None
    kalsarp_type_description: str | None = None
    rahu_sign: str | None = None
    ketu_sign: str | None = None
    axis_arc_degrees: float | None = None
    planets_within_axis: int
    total_classical_planets: int = 7
    planet_status: list[KalsarpPlanetStatus]
    summary: str


def analyze_kalsarp(chart: ChartData) -> KalsarpReport:
    """Detect Kalsarp Dosha and classify its type and severity.

    Args:
        chart: A fully calculated ChartData (natal). Must include Rahu and Ketu
            positions with house/sign.

    Returns:
        KalsarpReport with classification, type name, and per-planet axis status.
    """
    rahu = chart.rahu
    ketu = chart.ketu
    if rahu is None or ketu is None:
        raise ValueError("ChartData must include Rahu and Ketu positions")

    rahu_lon = _planet_longitude(rahu)
    ketu_lon = _planet_longitude(ketu)
    rahu_house = rahu.house
    ketu_house = ketu.house

    # Determine the Rahu→Ketu arc span in degrees (zodiacal order).
    arc = (ketu_lon - rahu_lon) % 360.0
    if arc == 0.0:
        arc = 360.0

    # Classify type by Rahu house.
    kalsarp_type = None
    kalsarp_type_desc = None
    if rahu_house in KALSARP_TYPES:
        kalsarp_type, kalsarp_type_desc = KALSARP_TYPES[rahu_house]

    # Evaluate each classical planet.
    planet_statuses: list[KalsarpPlanetStatus] = []
    within_count = 0
    for p_name in VEDIC_PLANETS:
        planet = next((p for p in chart.planets if p.name == p_name), None)
        if planet is None:
            continue
        lon = _planet_longitude(planet)
        within = _is_between_rah_ketu(lon, rahu_lon, ketu_lon)
        if within:
            within_count += 1
        planet_statuses.append(
            KalsarpPlanetStatus(
                name=p_name,
                sign=planet.sign,
                house=planet.house,
                degree_in_sign=round(planet.degree_in_sign, 4),
                longitude=round(lon, 4),
                within_axis=within,
            )
        )

    # Determine classification.
    if within_count == 0:
        classification = "None"
        has_kalsarp = False
        summary = "No Kalsarp Dosha: classical planets are not hemmed between Rahu and Ketu."
    elif within_count == len(VEDIC_PLANETS):
        classification = "Purna"
        has_kalsarp = True
        summary = (
            f"Purna (Complete) Kalsarp Dosha — all {within_count} classical planets lie within the "
            f"Rahu→Ketu axis ({kalsarp_type or 'unknown'}). This is the most intense form; "
            f"results of the houses involved are markedly modified until the axis is relieved by transit/dasha."
        )
    else:
        classification = "Ardh"
        has_kalsarp = True
        outside = len(VEDIC_PLANETS) - within_count
        summary = (
            f"Ardh (Partial) Kalsarp Dosha — {within_count} of {len(VEDIC_PLANETS)} classical planets lie within "
            f"the Rahu→Ketu axis ({kalsarp_type or 'unknown'}); {outside} planet(s) fall outside, which moderates "
            f"the intensity but the axis still colors the affected houses."
        )

    return KalsarpReport(
        has_kalsarp=has_kalsarp,
        classification=classification,
        rahu_house=rahu_house,
        ketu_house=ketu_house,
        kalsarp_type=kalsarp_type,
        kalsarp_type_description=kalsarp_type_desc,
        rahu_sign=rahu.sign,
        ketu_sign=ketu.sign,
        axis_arc_degrees=round(arc, 4),
        planets_within_axis=within_count,
        planet_status=planet_statuses,
        summary=summary,
    )
