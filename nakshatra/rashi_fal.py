"""
nakshatra/rashi_fal.py
Rashi Fal (Moon-sign Horoscope) Engine.

Rashi Fal is the classical Chandra-lagna based daily/monthly/yearly forecast:
every transit is read from the natal Moon sign treated as the 1st house.
Used widely in popular Jyotish (Rashi Phal) and exactly the feature Nava
Kundali exposes as "Rashi fal (Daily/Monthly/Yearly)".

Method:
  * Chandra Lagna = natal Moon sign as House 1.
  * Each transiting Graha is placed in a house from Chandra Lagna.
  * Classical Phaladeepika favourable houses (per graha) mark auspicious
    results; all other houses are challenging/neutral.
  * Double Transit: Jupiter + Saturn transiting the same house from Moon
    (especially 10th/11th/2nd) trigger major events.
  * Sade Sati from natal Moon is reported for the period.
  * Output: per-period overall verdict, graha-wise house results, and a
    master-style synthesis.

All longitudes sidereal (JHora-Lahiri default); houses per chart house system
(Whole Sign default), consistent with the rest of the Nakshatra engine.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel

from nakshatra.core import (
    ZODIAC_SIGNS,
    Ayanamsa,
    BirthData,
    HouseSystem,
    calculate_chart,
)
from nakshatra.transits import FAVORABLE_GOCHAR_HOUSES as TRANSIT_FAVORABLE

VEDIC_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

# Classical transit results by house from Chandra Lagna (Moon as 1st).
# Broad-brush classical results used when a house isn't explicitly favourable.
CHANDRA_LAGNA_HOUSE_RESULTS: dict[int, str] = {
    1: "Self, health, vitality and new beginnings — direct impact on body and mind.",
    2: "Wealth, family, speech and accumulated resources.",
    3: "Courage, siblings, short travel and initiative.",
    4: "Home, mother, comforts, vehicles and inner peace.",
    5: "Progeny, intellect, romance, creativity and past merit.",
    6: "Health challenges, enemies, debts and competitive struggles.",
    7: "Marriage, partnerships, public dealings and travel.",
    8: "Longevity, sudden events, transformations and hidden matters.",
    9: "Dharma, luck, gurus, higher learning and foreign travel.",
    10: "Career, authority, profession and public standing.",
    11: "Gains, income, friendships and fulfilment of desires.",
    12: "Expenditure, isolation, foreign matters and spiritual retreat.",
}

GOCHAR_VERDICT: dict[str, str] = {
    "excellent": "Excellent — auspicious results and progress.",
    "good": "Good — favourable support, steady gains.",
    "mixed": "Mixed — both gains and effort required.",
    "challenging": "Challenging — obstacles, delays or health care needed.",
    "difficult": "Difficult — restraint advised; avoid major new starts.",
}

_PERIOD_LABELS: dict[str, str] = {
    "daily": "Daily Rashi Fal",
    "monthly": "Monthly Rashi Fal",
    "yearly": "Yearly Rashi Fal",
}


class GrahaResult(BaseModel):
    planet: str
    sign: str
    house_from_moon: int
    degree_in_sign: float
    retrograde: bool
    favourable: bool
    verdict: str
    # Machine-readable verdict class: "excellent" | "good" | "mixed" |
    # "challenging" | "difficult". The UI badges on this, not on the
    # free-text verdict sentence.
    verdict_key: str


class RashiFalReport(BaseModel):
    success: bool = True
    period: str
    period_label: str
    reference_date: str
    moon_sign: str
    moon_nakshatra: str | None = None
    moon_house_from_self: int = 1
    overall_verdict: str
    overall_score: int  # -5 .. +5
    graha_results: list[GrahaResult]
    double_transit_houses: list[int]
    sade_sati_active: bool
    sade_sati_phase: str | None = None
    master_synthesis: str


def _house_from_moon(transit_lon: float, moon_sign: str) -> int:
    moon_idx = ZODIAC_SIGNS.index(moon_sign)
    transit_idx = int((transit_lon % 360.0) / 30.0) % 12
    return ((transit_idx - moon_idx) % 12) + 1


def _classify_verdict(planet: str, house: int) -> tuple[bool, str, str]:
    """Classify a transit house into (favourable, verdict_key, verdict)."""
    favourable_houses = TRANSIT_FAVORABLE.get(planet, [])
    favourable = house in favourable_houses
    if favourable:
        return True, "good", GOCHAR_VERDICT["good"]
    # Dusthana houses from Moon are tougher.
    if house in {6, 8, 12}:
        return False, "difficult", GOCHAR_VERDICT["difficult"]
    if house in {1, 4, 7, 10}:
        return False, "challenging", GOCHAR_VERDICT["challenging"]
    return False, "mixed", GOCHAR_VERDICT["mixed"]


# Overall-score weight per verdict class. A "mixed" transit is neutral by
# definition ("both gains and effort required") — the old code scored it -1,
# the same as a dusthana transit, which dragged every ordinary day to the
# -5 floor and made "Difficult" the modal verdict.
_SCORE_WEIGHTS: dict[str, int] = {
    "excellent": 1,
    "good": 1,
    "mixed": 0,
    "challenging": -1,
    "difficult": -1,
}


def _sade_sati(moon_sign: str, saturn_sign: str) -> tuple[bool, str | None]:
    moon_idx = ZODIAC_SIGNS.index(moon_sign)
    sat_idx = ZODIAC_SIGNS.index(saturn_sign)
    offset = (sat_idx - moon_idx) % 12  # 0 = same sign (2.5th), etc.
    # Sade Sati = Saturn transiting Moon sign, sign before, sign after.
    if offset in {0, 11, 1}:
        if offset == 11:
            phase = "Rising (Saturn in 12th from Moon)"
        elif offset == 0:
            phase = "Peak (Saturn in natal Moon sign)"
        else:
            phase = "Setting (Saturn in 2nd from Moon)"
        return True, phase
    return False, None


def calculate_rashi_fal(
    birth: BirthData,
    period: str = "daily",
    reference_date: datetime | None = None,
    ayanamsa: Ayanamsa = Ayanamsa.JHORA_LAHIRI,
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN,
) -> RashiFalReport:
    """Build the Rashi Fal (Moon-sign horoscope) report.

    Args:
        birth: Natal birth data.
        period: "daily" | "monthly" | "yearly".
        reference_date: Date for the forecast (default today).
        ayanamsa: Ayanamsa system.
        house_system: House system.
    """
    if period not in _PERIOD_LABELS:
        raise ValueError(f"period must be one of {list(_PERIOD_LABELS)}")

    if reference_date is None:
        reference_date = datetime.now(timezone.utc)

    # 1. Natal chart (Moon sign = Chandra Lagna).
    natal = calculate_chart(
        birth,
        ayanamsa=ayanamsa,
        house_system=house_system,
        include_dashas=False,
        include_vargas=False,
        include_ashtakavarga=False,
        include_shadbala=False,
        include_upagrahas=False,
        include_transits=False,
        include_panchanga=False,
        include_yogas=False,
    )
    moon = next((p for p in natal.planets if p.name == "Moon"), None)
    if not moon:
        raise ValueError("Unable to compute natal Moon position")
    moon_sign = moon.sign
    moon_nak = moon.nakshatra

    # 2. Transits at reference date (Sun..Ketu positions).
    ref_local = reference_date
    ref_birth = BirthData(
        year=ref_local.year,
        month=ref_local.month,
        day=ref_local.day,
        hour=ref_local.hour,
        minute=ref_local.minute,
        second=ref_local.second,
        latitude=birth.latitude,
        longitude=birth.longitude,
        timezone=birth.timezone,
        place_name=birth.place_name,
    )
    transit_chart = calculate_chart(
        ref_birth,
        ayanamsa=ayanamsa,
        house_system=house_system,
        include_dashas=False,
        include_vargas=False,
        include_ashtakavarga=False,
        include_shadbala=False,
        include_upagrahas=False,
        include_transits=False,
        include_panchanga=False,
        include_yogas=False,
    )

    # 3. Graha results from Chandra Lagna.
    graha_results: list[GrahaResult] = []
    score = 0
    # chart.planets holds Sun..Saturn only; Rahu/Ketu live on their own
    # fields — the old lookup silently dropped them, so only 7 of the 9
    # grahas were ever scored or shown.
    transit_positions = list(transit_chart.planets)
    if transit_chart.rahu is not None:
        transit_positions.append(transit_chart.rahu)
    if transit_chart.ketu is not None:
        transit_positions.append(transit_chart.ketu)
    for p_name in VEDIC_PLANETS:
        p = next((x for x in transit_positions if x.name == p_name), None)
        if p is None:
            continue
        house = _house_from_moon(p.longitude, moon_sign)
        favourable, verdict_key, verdict = _classify_verdict(p_name, house)
        score += _SCORE_WEIGHTS[verdict_key]
        graha_results.append(
            GrahaResult(
                planet=p_name,
                sign=p.sign,
                house_from_moon=house,
                degree_in_sign=round(p.degree_in_sign, 4),
                retrograde=p.retrograde,
                favourable=favourable,
                verdict=verdict,
                verdict_key=verdict_key,
            )
        )

    # Clamp score to -5..+5.
    score = max(-5, min(5, score))
    if score >= 3:
        overall = GOCHAR_VERDICT["excellent"]
    elif score >= 1:
        overall = GOCHAR_VERDICT["good"]
    elif score <= -3:
        overall = GOCHAR_VERDICT["difficult"]
    elif score <= -1:
        overall = GOCHAR_VERDICT["challenging"]
    else:
        overall = GOCHAR_VERDICT["mixed"]

    # 4. Double Transit (Jupiter + Saturn same house from Moon).
    jup = next((g for g in graha_results if g.planet == "Jupiter"), None)
    sat = next((g for g in graha_results if g.planet == "Saturn"), None)
    double_transit_houses: list[int] = []
    if jup and sat and jup.house_from_moon == sat.house_from_moon:
        double_transit_houses.append(jup.house_from_moon)

    # 5. Sade Sati from natal Moon.
    sat_sign = sat.sign if sat else ""
    sade_sati_active, sade_sati_phase = _sade_sati(moon_sign, sat_sign)

    # 6. Master synthesis.
    favourable_names = [g.planet for g in graha_results if g.favourable]
    unfavourable_names = [g.planet for g in graha_results if not g.favourable]
    parts: list[str] = []
    parts.append(
        f"{_PERIOD_LABELS[period]} for {moon_sign} Moon ({moon_nak or ''} nakshatra): "
        f"Chandra Lagna places your Moon sign as House 1, so every transit is read from there."
    )
    if favourable_names:
        parts.append(
            f"Supportive transits: {', '.join(favourable_names)} in favourable houses — "
            f"these areas flower this period."
        )
    if unfavourable_names:
        parts.append(
            f"Watchful transits: {', '.join(unfavourable_names)} in testing houses — "
            f"exercise restraint in the matters they signify."
        )
    if double_transit_houses:
        parts.append(
            f"Double Transit (Jupiter + Saturn) in House {double_transit_houses[0]} from Moon — "
            f"a major event trigger for the houses involved."
        )
    if sade_sati_active:
        parts.append(
            f"Sade Sati active — {sade_sati_phase}. Pace yourself; this is a maturing, not a destroying, phase."
        )
    master = " ".join(parts)

    return RashiFalReport(
        period=period,
        period_label=_PERIOD_LABELS[period],
        reference_date=ref_local.strftime("%Y-%m-%d"),
        moon_sign=moon_sign,
        moon_nakshatra=moon_nak,
        moon_house_from_self=1,
        overall_verdict=overall,
        overall_score=score,
        graha_results=graha_results,
        double_transit_houses=double_transit_houses,
        sade_sati_active=sade_sati_active,
        sade_sati_phase=sade_sati_phase,
        master_synthesis=master,
    )
