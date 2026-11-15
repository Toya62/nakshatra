"""
nakshatra/varshaphal.py
Tajik Varshaphal (Annual / Barsha Fal) engine.

Computes the annual solar-return (Varshaphal) chart for a given target year
and synthesizes the classical Tajika indicators:

* Solar Return moment (transiting Sun returns to natal sidereal longitude)
* Muntha (progressed annual Ascendant) + Muntha lord
* Varsheshwara (Year Lord) — strongest among weekday lord, Muntha lord,
  Varshaphal Asc-lord and Varshaphal Sun-lord
* Sahams (Arabic Parts / sensitive points) — Punya, Jara, Roga, Bandhana,
  Gati, Kshema, etc., each with a documented classical formula
* Month-wise lords & themes for the 12 months of the Varshaphal year

All longitudes are sidereal using the same ayanamsa convention as the rest of
the engine (JHora-Lahiri default), so Varshaphal is directly comparable to the
natal D1 chart.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import swisseph
from mayaastrolib.vedic.ayanamsa import _AYANAMSA_LOCK, _swe_mode_for
from pydantic import BaseModel

from nakshatra.core import (
    SIGN_LORDS,
    ZODIAC_SIGNS,
    Ayanamsa,
    BirthData,
    ChartData,
    HouseSystem,
    PlanetPosition,
    calculate_chart,
    calculate_dignity,
    get_degree_in_sign,
    get_sign,
)

# ---------------------------------------------------------------------------
# Solar return (Varshaphal) moment
# ---------------------------------------------------------------------------

def _sidereal_sun_longitude(dt_utc: datetime, ayanamsa: Ayanamsa) -> float:
    """Sidereal Sun longitude at a UTC datetime, matching core.py convention."""
    base = "lahiri" if ayanamsa == Ayanamsa.JHORA_LAHIRI else ayanamsa.value
    jhora_offset = (56.5318 / 3600.0) if ayanamsa == Ayanamsa.JHORA_LAHIRI else 0.0
    swe_mode = _swe_mode_for(base)
    with _AYANAMSA_LOCK:
        swisseph.set_sid_mode(swe_mode)
    hour_decimal = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    jd = swisseph.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour_decimal)
    calc, _ = swisseph.calc_ut(jd, swisseph.SUN, swisseph.FLG_SIDEREAL)
    return (float(calc[0]) + jhora_offset) % 360.0


def _local_to_utc(dt_local: datetime, tz_name: str) -> datetime:
    """Convert a naive local datetime to UTC using zoneinfo."""
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(tz_name)
    aware = dt_local.replace(tzinfo=tz)
    return aware.astimezone(timezone.utc).replace(tzinfo=None)


def find_solar_return(
    birth: BirthData,
    natal_sun_lon: float,
    target_year: int,
    ayanamsa: Ayanamsa,
    search_days: int = 3,
) -> datetime:
    """Find the UTC instant when transiting Sun returns to natal Sun longitude.

    Searches a window around the birthday of ``target_year`` (±search_days)
    and refines the crossing by bisection to the nearest minute.
    """
    tz = birth.timezone
    start_local = datetime(target_year, birth.month, birth.day, 0, 0, 0)

    # Coarse hourly scan over [start - search_days, start + search_days]
    lo = _local_to_utc(start_local - timedelta(days=search_days), tz)
    hi = _local_to_utc(start_local + timedelta(days=search_days), tz)

    step = timedelta(hours=1)
    t = lo
    prev_t = lo
    prev_lon = _sidereal_sun_longitude(prev_t, ayanamsa)
    crossing: datetime | None = None

    while t <= hi:
        lon = _sidereal_sun_longitude(t, ayanamsa)
        # Detect when Sun crosses (or equals) the natal longitude going forward.
        if (prev_lon - natal_sun_lon) <= 0 and (lon - natal_sun_lon) >= 0:
            crossing = t
            break
        # Handle exact equality / wrap-around near 360->0
        if abs(lon - natal_sun_lon) < 1e-6:
            crossing = t
            break
        prev_t, prev_lon = t, lon
        t += step

    if crossing is None:
        # Fallback: return the birthday at local noon (best effort).
        return _local_to_utc(datetime(target_year, birth.month, birth.day, 12, 0, 0), tz)

    # Refine by bisection between prev_t (below) and crossing (above/equal).
    a, b = prev_t, crossing
    for _ in range(40):
        mid = a + (b - a) / 2
        mid_lon = _sidereal_sun_longitude(mid, ayanamsa)
        if (mid_lon - natal_sun_lon) >= 0:
            b = mid
        else:
            a = mid
    refined = b

    # Snap to the nearest minute for a stable, human-readable result.
    return refined.replace(second=0, microsecond=0)


# ---------------------------------------------------------------------------
# Helpers for house/sign placement within a chart (Whole Sign)
# ---------------------------------------------------------------------------

def _house_for_longitude(lon: float, asc_sign: str) -> int:
    """Whole-sign house number (1-12) for a longitude given the ascendant sign."""
    asc_idx = ZODIAC_SIGNS.index(asc_sign)
    lon_idx = int((lon % 360.0) / 30.0) % 12
    return ((lon_idx - asc_idx) % 12) + 1


def _planet_by_name(chart: ChartData, name: str) -> PlanetPosition | None:
    for p in chart.planets:
        if p.name == name:
            return p
    if chart.rahu and chart.rahu.name == name:
        return chart.rahu
    if chart.ketu and chart.ketu.name == name:
        return chart.ketu
    return None


# ---------------------------------------------------------------------------
# Sahams (sensitive points / Arabic parts)
# ---------------------------------------------------------------------------

# Each Saham: (name, meaning, formula string, p1, p2, p3) where the longitude is
# computed as (lon(p1) + lon(p2) - lon(p3)) mod 360. Planet names are the 7
# classical grahas plus "Ascendant" handled separately.
SAHAMS: list[tuple[str, str, str, str, str, str]] = [
    ("Punya Saham", "Fortune, merit and auspicious results for the year",
     "Jupiter + Venus − Saturn", "Jupiter", "Venus", "Saturn"),
    ("Jara Saham", "Mortality, critical health and end-of-cycle matters",
     "Saturn + Mars − Sun", "Saturn", "Mars", "Sun"),
    ("Roga Saham", "Disease, illness and physical vulnerability",
     "Saturn + Mars − Moon", "Saturn", "Mars", "Moon"),
    ("Bandhana Saham", "Bondage, restriction, legal entanglement",
     "Saturn + Mars − Mercury", "Saturn", "Mars", "Mercury"),
    ("Gati Saham", "Travel, movement and change of residence",
     "Jupiter + Mars − Sun", "Jupiter", "Mars", "Sun"),
    ("Kshema Saham", "Welfare, safety and protection from harm",
     "Jupiter + Venus − Mars", "Jupiter", "Venus", "Mars"),
    ("Dhana Saham", "Wealth accumulation and financial gains",
     "Venus + Jupiter − Saturn", "Venus", "Jupiter", "Saturn"),
    ("Karyesh Saham", "Fulfillment of undertakings and goals",
     "Sun + Jupiter − Saturn", "Sun", "Jupiter", "Saturn"),
]


def _compute_saham(chart: ChartData, p1: str, p2: str, p3: str) -> float | None:
    """Saham longitude = (p1 + p2 − p3) mod 360 using Varshaphal chart positions."""
    b1 = _planet_by_name(chart, p1)
    b2 = _planet_by_name(chart, p2)
    b3 = _planet_by_name(chart, p3)
    if not (b1 and b2 and b3):
        return None
    return (b1.longitude + b2.longitude - b3.longitude) % 360.0


# ---------------------------------------------------------------------------
# Varsheshwara (Year Lord) candidates
# ---------------------------------------------------------------------------

def _select_varsheshwara(
    chart: ChartData,
    muntha_lord: str,
    birth_weekday_lord: str,
) -> dict[str, Any]:
    """Pick the Year Lord from classical candidates by dignity & house strength.

    Candidates: birth-weekday lord, Muntha lord, Varshaphal ascendant lord,
    Varshaphal Sun sign lord. Scored by dignity in the Varshaphal chart plus a
    house bonus (Kendra/Trikona favourable, Dusthana unfavourable).
    """
    asc_sign = chart.ascendant.sign
    sun = _planet_by_name(chart, "Sun")
    sun_sign = sun.sign if sun else asc_sign

    candidates = [
        ("birth_weekday_lord", birth_weekday_lord, "Lord of the weekday of birth"),
        ("muntha_lord", muntha_lord, "Lord of the Muntha sign"),
        ("varshaphal_asc_lord", SIGN_LORDS[asc_sign], "Lord of the Varshaphal Ascendant"),
        ("varshaphal_sun_lord", SIGN_LORDS[sun_sign], "Lord of the Varshaphal Sun sign"),
    ]

    kendra_trikona = {1, 4, 7, 10, 1, 5, 9}
    dusthana = {6, 8, 12}

    scored: list[dict[str, Any]] = []
    for key, planet, rationale in candidates:
        p = _planet_by_name(chart, planet)
        if not p:
            continue
        dignity = p.dignity or calculate_dignity(planet, p.sign)
        dignity_score = {
            "exalted": 5.0,
            "own_sign": 4.0,
            "neutral": 2.0,
            "debilitated": 0.0,
        }.get(dignity, 2.0)
        house_bonus = 0.0
        if p.house in kendra_trikona:
            house_bonus += 2.0
        if p.house in dusthana:
            house_bonus -= 2.0
        score = dignity_score + house_bonus
        scored.append(
            {
                "key": key,
                "planet": planet,
                "rationale": rationale,
                "score": round(score, 2),
                "dignity": dignity,
                "house": p.house,
                "sign": p.sign,
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    winner = scored[0] if scored else {
        "key": "muntha_lord", "planet": muntha_lord, "rationale": "Muntha lord (fallback)",
        "score": 0.0, "dignity": "neutral", "house": 1, "sign": "",
    }
    return winner


# ---------------------------------------------------------------------------
# Month lords
# ---------------------------------------------------------------------------

# Python weekday(): Monday=0 ... Sunday=6
_WEEKDAY_LORDS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]
_WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

_MONTH_THEMES: dict[str, str] = {
    "Sun": "Authority, career, vitality, father, government matters.",
    "Moon": "Mind, emotions, mother, home, public dealings, travel.",
    "Mars": "Energy, courage, conflict, siblings, property, initiative.",
    "Mercury": "Intellect, speech, trade, writing, education, short journeys.",
    "Jupiter": "Wisdom, wealth, progeny, spirituality, teachers, expansion.",
    "Venus": "Relationships, marriage, pleasure, arts, luxury, comforts.",
    "Saturn": "Discipline, hard work, delays, service, longevity, structure.",
}


def _month_lords(solar_return_local: datetime) -> list[dict[str, Any]]:
    """Twelve month lords for the Varshaphal year.

    Month 1 is ruled by the lord of the weekday on which the solar return
    falls; subsequent months advance through the weekday-lord sequence.
    """
    wd_idx = solar_return_local.weekday()  # Monday=0
    lords = []
    for i in range(12):
        lord = _WEEKDAY_LORDS[(wd_idx + i) % 7]
        lords.append(
            {
                "month": i + 1,
                "month_name": f"Month {i + 1}",
                "lord": lord,
                "theme": _MONTH_THEMES[lord],
                "weekday": _WEEKDAY_NAMES[(wd_idx + i) % 7],
            }
        )
    return lords


# ---------------------------------------------------------------------------
# Main report builder
# ---------------------------------------------------------------------------

class SahamInfo(BaseModel):
    name: str
    meaning: str
    longitude: float
    sign: str
    degree_in_sign: float
    house: int
    formula: str


class MonthPrediction(BaseModel):
    month: int
    month_name: str
    lord: str
    theme: str
    weekday: str


class MunthaInfo(BaseModel):
    completed_years: int
    sign: str
    degree_in_sign: float
    longitude: float
    house: int
    lord: str


class VarsheshwaraInfo(BaseModel):
    planet: str
    rationale: str
    score: float
    dignity: str
    house: int
    sign: str


class VarshaphalReport(BaseModel):
    success: bool = True
    birth_year: int
    target_year: int
    completed_years: int
    solar_return_local: str
    solar_return_utc: str
    muntha: MunthaInfo
    varsheshwara: VarsheshwaraInfo
    sahams: list[SahamInfo]
    month_lords: list[MonthPrediction]
    varshaphal_chart: dict[str, Any]
    summary: str


def calculate_varshaphal(
    birth: BirthData,
    target_year: int | None = None,
    ayanamsa: Ayanamsa = Ayanamsa.JHORA_LAHIRI,
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN,
) -> VarshaphalReport:
    """Build the complete Tajik Varshaphal (Barsha Fal) report for ``target_year``.

    Args:
        birth: Natal birth data.
        target_year: Calendar year for the annual forecast. Defaults to the
            current Gregorian year.
        ayanamsa: Ayanamsa system (default jhora_lahiri).
        house_system: House system (default Whole Sign).
    """
    if target_year is None:
        target_year = datetime.now(timezone.utc).year

    # 1. Natal chart (to get natal Sun & Ascendant longitudes).
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
    natal_sun = _planet_by_name(natal, "Sun")
    if not natal_sun:
        raise ValueError("Unable to compute natal Sun position")
    natal_sun_lon = natal_sun.longitude
    natal_asc_sign = natal.ascendant.sign
    natal_asc_deg = natal.ascendant.degree_in_sign

    # Completed years at the target-year solar return.
    completed_years = target_year - birth.year

    # 2. Find the solar return moment (Sun returns to natal longitude).
    sr_utc = find_solar_return(birth, natal_sun_lon, target_year, ayanamsa)
    sr_local = sr_utc.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(birth.timezone)).replace(tzinfo=None)

    # 3. Cast the Varshaphal chart at the solar return, same place.
    sr_birth = BirthData(
        year=sr_local.year,
        month=sr_local.month,
        day=sr_local.day,
        hour=sr_local.hour,
        minute=sr_local.minute,
        second=sr_local.second,
        latitude=birth.latitude,
        longitude=birth.longitude,
        timezone=birth.timezone,
        place_name=birth.place_name,
    )
    varsh = calculate_chart(
        sr_birth,
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

    # 4. Muntha: progresses one sign per year from natal Ascendant.
    asc_idx = ZODIAC_SIGNS.index(natal_asc_sign)
    muntha_sign_idx = (asc_idx + completed_years) % 12
    muntha_sign = ZODIAC_SIGNS[muntha_sign_idx]
    muntha_deg = natal_asc_deg
    muntha_lon = (muntha_sign_idx * 30.0 + muntha_deg) % 360.0
    muntha_house = _house_for_longitude(muntha_lon, varsh.ascendant.sign)
    muntha_lord = SIGN_LORDS[muntha_sign]
    muntha = MunthaInfo(
        completed_years=completed_years,
        sign=muntha_sign,
        degree_in_sign=round(muntha_deg, 6),
        longitude=round(muntha_lon, 6),
        house=muntha_house,
        lord=muntha_lord,
    )

    # 5. Varsheshwara (Year Lord).
    # Birth weekday lord.
    birth_dt_local = datetime(birth.year, birth.month, birth.day)
    birth_wd_idx = birth_dt_local.weekday()
    birth_weekday_lord = _WEEKDAY_LORDS[birth_wd_idx]

    vsha = _select_varsheshwara(varsh, muntha_lord, birth_weekday_lord)
    varsheshwara = VarsheshwaraInfo(
        planet=vsha["planet"],
        rationale=vsha["rationale"],
        score=vsha["score"],
        dignity=vsha["dignity"],
        house=vsha["house"],
        sign=vsha["sign"],
    )

    # 6. Sahams.
    sahams: list[SahamInfo] = []
    for name, meaning, formula, p1, p2, p3 in SAHAMS:
        lon = _compute_saham(varsh, p1, p2, p3)
        if lon is None:
            continue
        sign = get_sign(lon)
        deg = get_degree_in_sign(lon)
        house = _house_for_longitude(lon, varsh.ascendant.sign)
        sahams.append(
            SahamInfo(
                name=name,
                meaning=meaning,
                longitude=round(lon, 6),
                sign=sign,
                degree_in_sign=round(deg, 6),
                house=house,
                formula=formula,
            )
        )

    # 7. Month lords.
    month_lords = [
        MonthPrediction(
            month=m["month"],
            month_name=m["month_name"],
            lord=m["lord"],
            theme=m["theme"],
            weekday=m["weekday"],
        )
        for m in _month_lords(sr_local)
    ]

    # 8. Master-style summary.
    vsha_planet = varsheshwara.planet
    summary = (
        f"For the Varshaphal year {target_year} (age {completed_years}), the solar return "
        f"falls on {sr_local.strftime('%A, %B %d, %Y')} at birth place. The Muntha (annual "
        f"progressed Ascendant) lies in {muntha.sign} (House {muntha.house}) under its lord "
        f"{muntha.lord}. The Varsheshwara — the planet governing this year — is "
        f"{vsha_planet} ({varsheshwara.rationale}, dignity: {varsheshwara.dignity}, "
        f"House {varsheshwara.house}). "
        f"Key sensitive points: Punya Saham in {sahams[0].sign if sahams else '—'} and "
        f"Jara Saham in {sahams[1].sign if len(sahams) > 1 else '—'} mark the year's "
        f"fortune and health watch-points respectively. Month-wise, each month is ruled "
        f"by its weekday lord beginning with {_WEEKDAY_LORDS[sr_local.weekday()]} "
        f"on the solar-return weekday."
    )

    # Compact chart snapshot for the UI.
    chart_snapshot = {
        "ascendant": varsh.ascendant.sign,
        "asc_degree": varsh.ascendant.degree_in_sign,
        "planets": [
            {
                "name": p.name,
                "sign": p.sign,
                "degree": p.degree_in_sign,
                "house": p.house,
                "retrograde": p.retrograde,
                "dignity": p.dignity,
            }
            for p in varsh.planets
        ],
        "houses": [
            {"house": h.house, "sign": h.sign, "degree": h.degree_in_sign}
            for h in varsh.houses
        ],
    }

    return VarshaphalReport(
        birth_year=birth.year,
        target_year=target_year,
        completed_years=completed_years,
        solar_return_local=sr_local.strftime("%Y-%m-%d %H:%M:%S"),
        solar_return_utc=sr_utc.strftime("%Y-%m-%d %H:%M:%S"),
        muntha=muntha,
        varsheshwara=varsheshwara,
        sahams=sahams,
        month_lords=month_lords,
        varshaphal_chart=chart_snapshot,
        summary=summary,
    )
