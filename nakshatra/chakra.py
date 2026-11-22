"""
nakshatra/chakra.py
Vedic Chakra Systems: Navatara, Compound (Panchadha Maitri) Relationship,
and Ghatchakra.

These are the classical support chakras that platforms such as Nava Kundali
expose alongside the birth chart:

* Navatara Chakra — the 9 Tara (Janma, Sampat, Vipat, Kshema, Pratyari,
  Sadhaka, Vadha, Mitra, Ati-Mitra) of every planet counted from the birth
  (Janma) nakshatra. Good taras: Sampat, Kshema, Sadhaka, Mitra, Ati-Mitra.
  Bad taras: Janma, Vipat, Pratyari, Vadha.
* Compound Relationship — Panchadha Maitri: natural friendship (Naisargika)
  combined with temporary friendship (Tatkalika) from house position, yielding
  intimate friend / friend / enemy / bitter enemy / neutral for every planet
  pair.
* Ghatchakra — the ghati-count wheel derived from ghatis elapsed since
  sunrise; each house is assigned a ruling planet cycling through the
  weekday-lord sequence starting from the Ghati Lagna. NOTE on the
  convention: the classical Ghatika Lagna is a SIGN (ghatis since sunrise
  counted from the birth Lagna, e.g. Vaanchanadhiyam on Jaimini), while
  this wheel is the derived weekday-lord cycle used by modern software
  (e.g. Nava Kundali): the cycle is anchored on the weekday lord of the
  birth day and advances one lord per ghati elapsed since sunrise. The
  rulers are therefore weekday lords, NOT the sign lords of the houses —
  Aries in house 1 is ruled by the weekday-cycle lord for that ghati,
  not by Mars. The UI must label them "Ghati Lord" to avoid that
  misreading.
"""

from __future__ import annotations

from pydantic import BaseModel

from nakshatra.core import NAKSHATRAS, ZODIAC_SIGNS, ChartData, PlanetPosition

VEDIC_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Python weekday Monday=0 ... Sunday=6 -> weekday lord
_WEEKDAY_LORDS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]

# Python weekday Monday=0 ... Sunday=6 -> weekday name
_WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Nine taras in order from Janma (birth nakshatra).
TARAS = [
    "Janma",  # 1 - birth, caution to body
    "Sampat",  # 2 - wealth, gain
    "Vipat",  # 3 - danger, loss
    "Kshema",  # 4 - welfare, protection
    "Pratyari",  # 5 - opposition, conflict
    "Sadhaka",  # 6 - accomplishment, fulfilment
    "Vadha",  # 7 - death-like, severe obstruction
    "Mitra",  # 8 - friend, support
    "Ati-Mitra",  # 9 - supreme friend, great support
]

GOOD_TARAS = {"Sampat", "Kshema", "Sadhaka", "Mitra", "Ati-Mitra"}
BAD_TARAS = {"Janma", "Vipat", "Pratyari", "Vadha"}

NAKSHATRA_INDEX: dict[str, int] = {name: i for i, (name, _) in enumerate(NAKSHATRAS)}

# Natural (naisargika) friendship & enmity among the 7 grahas.
NATURAL_FRIENDS: dict[str, set[str]] = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
NATURAL_ENEMIES: dict[str, set[str]] = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
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


def _natural_relation(a: str, b: str) -> str:
    if a == b:
        return "neutral"
    if b in NATURAL_FRIENDS.get(a, set()):
        return "friend"
    if b in NATURAL_ENEMIES.get(a, set()):
        return "enemy"
    return "neutral"


def _temporary_relation(from_planet: str, to_planet: str, chart: ChartData) -> str:
    """Temporary (tatkalika) friendship from house position.

    Planets in houses 2, 3, 4, 10, 11 from ``from_planet`` are temporary
    friends; planets in houses 5, 7, 8, 9, 12 are temporary enemies; the
    planet's own house (1) is self/neutral.
    """
    fp = _planet_by_name(chart, from_planet)
    tp = _planet_by_name(chart, to_planet)
    if fp is None or tp is None:
        return "neutral"
    if fp.house == tp.house:
        return "neutral"
    house_from = ((tp.house - fp.house) % 12) + 1  # fp's own house = 1
    if house_from in {2, 3, 4, 10, 11}:
        return "friend"
    if house_from in {5, 7, 8, 9, 12}:
        return "enemy"
    return "neutral"


def _compound_relation(natural: str, temporary: str) -> str:
    """Panchadha Maitri compound of natural + temporary relationship."""
    if natural == "friend" and temporary == "friend":
        return "intimate_friend"
    if natural == "friend" and temporary == "enemy":
        return "friend"
    if natural == "enemy" and temporary == "friend":
        return "friend"
    if natural == "enemy" and temporary == "enemy":
        return "bitter_enemy"
    if natural == "neutral" and temporary == "friend":
        return "friend"
    if natural == "neutral" and temporary == "enemy":
        return "enemy"
    return "neutral"


class NavataraEntry(BaseModel):
    planet: str
    nakshatra: str
    nakshatra_index: int
    count_from_janma: int
    tara: str
    nature: str  # "good" | "bad" | "neutral"


class CompoundPair(BaseModel):
    planet_a: str
    planet_b: str
    natural: str
    temporary: str
    compound: str


class GhatiHouse(BaseModel):
    house: int
    ruler: str
    sign: str


class ChakraReport(BaseModel):
    success: bool = True
    navatara: list[NavataraEntry]
    compound_relationships: list[CompoundPair]
    ghatchakra: list[GhatiHouse]
    janma_nakshatra: str
    janma_tara_lord_planet: str | None = None
    summary: str
    # Ghatchakra inputs, so the UI can show how the wheel was derived.
    ghati_count: int = 1
    birth_weekday: str = ""


def calculate_chakra(
    chart: ChartData, ghati_count: int = 1, weekday_idx: int = 0
) -> ChakraReport:
    """Compute Navatara, Compound Relationship and Ghatchakra for a chart.

    The Ghatchakra lord cycle is anchored on the weekday lord of the birth
    day (``weekday_idx``: Monday=0 ... Sunday=6, matching ``_WEEKDAY_LORDS``)
    and advances one lord per ghati elapsed since sunrise, then one lord per
    house: ``lord(h) = _WEEKDAY_LORDS[(weekday_idx + ghati_count + h - 2) % 7]``.
    The old formula omitted ``weekday_idx`` (implicitly anchoring every chart
    on Monday), so a Friday birth showed Moon ruling house 1 instead of the
    Friday-anchored cycle. ``weekday_idx`` defaults to 0 to preserve the old
    behaviour for direct callers; :func:`calculate_chakra_with_ghati`
    always passes the true birth weekday.
    """
    moon = _planet_by_name(chart, "Moon")
    janma_nakshatra = moon.nakshatra if moon and moon.nakshatra else NAKSHATRAS[0][0]
    janma_idx = (
        NAKSHATRAS.index((janma_nakshatra, _nakshatra_lord(janma_nakshatra)))
        if janma_nakshatra in [n[0] for n in NAKSHATRAS]
        else 0
    )

    # -------- Navatara Chakra --------
    navatara: list[NavataraEntry] = []
    for p_name in VEDIC_PLANETS:
        p = _planet_by_name(chart, p_name)
        if not p or not p.nakshatra:
            continue
        nak_idx = NAKSHATRAS.index((p.nakshatra, _nakshatra_lord(p.nakshatra)))
        count = ((nak_idx - janma_idx) % 27) + 1
        tara = TARAS[(count - 1) % 9]
        nature = "good" if tara in GOOD_TARAS else ("bad" if tara in BAD_TARAS else "neutral")
        navatara.append(
            NavataraEntry(
                planet=p_name,
                nakshatra=p.nakshatra,
                nakshatra_index=nak_idx,
                count_from_janma=count,
                tara=tara,
                nature=nature,
            )
        )

    # -------- Compound Relationship --------
    compound: list[CompoundPair] = []
    for i, a in enumerate(VEDIC_PLANETS):
        for b in VEDIC_PLANETS[i + 1 :]:
            natural = _natural_relation(a, b)
            temporary = _temporary_relation(a, b, chart)
            compound.append(
                CompoundPair(
                    planet_a=a,
                    planet_b=b,
                    natural=natural,
                    temporary=temporary,
                    compound=_compound_relation(natural, temporary),
                )
            )

    # -------- Ghatchakra --------
    asc_idx = ZODIAC_SIGNS.index(chart.ascendant.sign)
    ghatchakra: list[GhatiHouse] = []
    for h in range(1, 13):
        # Cycle weekday lords starting from the birth weekday lord,
        # advanced one lord per ghati elapsed since sunrise.
        lord_idx = (weekday_idx + ghati_count + h - 2) % 7
        ruler = _WEEKDAY_LORDS[lord_idx]
        sign_idx = (asc_idx + h - 1) % 12
        ghatchakra.append(
            GhatiHouse(
                house=h,
                ruler=ruler,
                sign=ZODIAC_SIGNS[sign_idx],
            )
        )

    good_count = sum(1 for n in navatara if n.nature == "good")
    bad_count = sum(1 for n in navatara if n.nature == "bad")
    intimate = [c for c in compound if c.compound == "intimate_friend"]
    bitter = [c for c in compound if c.compound == "bitter_enemy"]
    summary = (
        f"Janma Nakshatra: {janma_nakshatra}. Of {len(navatara)} planetary tara positions, "
        f"{good_count} are in good taras (Sampat/Kshema/Sadhaka/Mitra/Ati-Mitra) and "
        f"{bad_count} in bad taras (Janma/Vipat/Pratyari/Vadha). "
        f"Compound relationships: {len(intimate)} intimate-friend pairs, "
        f"{len(bitter)} bitter-enemy pairs among {len(compound)} planet pairs."
    )

    return ChakraReport(
        navatara=navatara,
        compound_relationships=compound,
        ghatchakra=ghatchakra,
        janma_nakshatra=janma_nakshatra,
        janma_tara_lord_planet=None,
        summary=summary,
        ghati_count=ghati_count,
        birth_weekday=_WEEKDAY_NAMES[weekday_idx % 7],
    )


def _nakshatra_lord(nakshatra_name: str) -> str:
    for name, lord in NAKSHATRAS:
        if name == nakshatra_name:
            return lord
    return ""


def _sunrise_hour_local(
    year: int, month: int, day: int, latitude: float, longitude: float, timezone_str: str
) -> float | None:
    """Local sunrise hour (0-24) for the given date/place, or None if the
    ephemeris cannot compute it (e.g. polar day/night)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    import swisseph as swe
    from mayaastrolib.datetime import Datetime

    from nakshatra.core import format_tz_offset

    try:
        probe = datetime(year, month, day, 12, 0, 0, tzinfo=ZoneInfo(timezone_str))
        offset_sec = probe.utcoffset().total_seconds() if probe.utcoffset() else 0.0
        t_tz_str = format_tz_offset(offset_sec)
        swe.set_ephe_path("")
        midnight = Datetime([year, month, day], 0.0, t_tz_str)
        res = swe.rise_trans(
            midnight.jd, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER,
            (longitude, latitude, 0.0), 0.0, 0.0,
        )
        if res[0] != 0:
            return None
        ut_hour = swe.revjul(res[1][0], swe.GREG_CAL)[3]
        return (ut_hour + offset_sec / 3600.0) % 24.0
    except Exception:
        return None


def ghati_context(chart: ChartData) -> tuple[int, int]:
    """(ghati_count, weekday_idx) for the birth.

    Ghatis are 24-minute units elapsed since local sunrise at the birthplace
    (true sunrise from the ephemeris; 06:00 local only if it cannot be
    computed), counted from the most recent sunrise — so a pre-sunrise birth
    counts ghatis since the previous day's sunrise. The count is mapped to
    1..12 (0 -> 12), preserving the previous convention. ``weekday_idx`` is
    the Vedic weekday (Monday=0 ... Sunday=6): the Vedic day starts at
    sunrise, so a pre-sunrise birth belongs to the previous civil day.
    """
    from datetime import date, timedelta

    b = chart.birth_data
    birth_hour = b.hour + b.minute / 60.0 + b.second / 3600.0

    sunrise = _sunrise_hour_local(b.year, b.month, b.day, b.latitude, b.longitude, b.timezone)
    if sunrise is None:
        sunrise = 6.0  # documented fallback: 06:00 local
    birth_date = date(b.year, b.month, b.day)
    if birth_hour < sunrise:
        # Pre-sunrise: count from the previous day's sunrise.
        prev = birth_date - timedelta(days=1)
        prev_sunrise = _sunrise_hour_local(
            prev.year, prev.month, prev.day, b.latitude, b.longitude, b.timezone
        )
        if prev_sunrise is None:
            prev_sunrise = sunrise
        elapsed_min = (24.0 - (prev_sunrise - birth_hour)) * 60.0
        birth_date = prev
    else:
        elapsed_min = (birth_hour - sunrise) * 60.0

    ghatis = max(0, int(elapsed_min // 24))
    return (ghatis % 12) or 12, birth_date.weekday()


# Attach ghati_count to chart so the analyzer can expose it; computed lazily
# here from the chart birth data (true local sunrise, 24 min per ghati).
def attach_ghati_count(chart: ChartData) -> int:
    return ghati_context(chart)[0]


def calculate_chakra_with_ghati(chart: ChartData) -> ChakraReport:
    """Convenience: compute chakra with ghati count derived from birth data."""
    ghati_count, weekday_idx = ghati_context(chart)
    return calculate_chakra(chart, ghati_count=ghati_count, weekday_idx=weekday_idx)
