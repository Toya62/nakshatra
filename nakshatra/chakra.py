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
* Ghatchakra — the ghati-count wheel derived from ghatis elapsed at sunrise;
  each house is assigned a ruling planet cycling through the weekday-lord
  sequence starting from the Ghati Lagna.
"""

from __future__ import annotations

from pydantic import BaseModel

from nakshatra.core import NAKSHATRAS, ZODIAC_SIGNS, ChartData, PlanetPosition

VEDIC_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Python weekday Monday=0 ... Sunday=6 -> weekday lord
_WEEKDAY_LORDS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]

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


def calculate_chakra(chart: ChartData, ghati_count: int = 1) -> ChakraReport:
    """Compute Navatara, Compound Relationship and Ghatchakra for a chart."""
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
        # Cycle weekday lords starting from the Ghati Lagna house.
        lord_idx = (ghati_count + h - 2) % 7
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
    )


def _nakshatra_lord(nakshatra_name: str) -> str:
    for name, lord in NAKSHATRAS:
        if name == nakshatra_name:
            return lord
    return ""


# Attach ghati_count to chart so the analyzer can expose it; computed lazily
# here from the chart birth data (6 AM sunrise fallback, 24 min per ghati).
def attach_ghati_count(chart: ChartData) -> int:
    from datetime import datetime, timezone

    birth_dt = datetime(
        chart.birth_data.year,
        chart.birth_data.month,
        chart.birth_data.day,
        chart.birth_data.hour,
        chart.birth_data.minute,
        chart.birth_data.second,
        tzinfo=timezone.utc,
    )
    sunrise_local = datetime(
        chart.birth_data.year,
        chart.birth_data.month,
        chart.birth_data.day,
        6,
        0,
        0,
        tzinfo=timezone.utc,
    )
    ghatis = max(0, (birth_dt - sunrise_local).total_seconds() // (24 * 60))
    return int(ghatis % 12) or 12


def calculate_chakra_with_ghati(chart: ChartData) -> ChakraReport:
    """Convenience: compute chakra with ghati count derived from birth data."""
    ghati_count = attach_ghati_count(chart)
    return calculate_chakra(chart, ghati_count=ghati_count)
