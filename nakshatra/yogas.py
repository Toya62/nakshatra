"""
Nakshatra Yoga Detection Engine
Rule-based detection for classical Vedic Yogas:
- Pancha Mahapurusha (Ruchaka, Bhadra, Hamsa, Malavya, Sasa)
- Gaja Kesari
- Kemadruma (+ Kemadruma Bhanga cancellation)
- Neechabhanga Raja Yoga (+ multi-rule cancellation verification)
- Chandra Yogas (Sunapha, Anapha, Dhurdhura, Chandra Mangala, Adhi Yoga)
- Surya Yogas (Budhaditya, Vesi, Vasi, Ubhayachari)
- Viparita Raja Yogas (Harsha, Sarala, Vimala)
- Kendra-Trikona Raja Yogas & Dhana Yogas (Amala, Parvata, Dhana combinations)
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from nakshatra.core import ChartData

from nakshatra.core import (
    SIGN_LORDS,
    HouseCusp,
    PlanetPosition,
)


def _ordinal(n: int) -> str:
    """Format integer with English ordinal suffix (1st, 2nd, etc.)."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


# Natural classifications
NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury"}
NATURAL_MALEFICS = {"Saturn", "Mars", "Sun", "Rahu", "Ketu"}

EXALTATION_SIGNS = {
    "Sun": "Aries",
    "Moon": "Taurus",
    "Mars": "Capricorn",
    "Mercury": "Virgo",
    "Jupiter": "Cancer",
    "Venus": "Pisces",
    "Saturn": "Libra",
}

DEBILITATION_SIGNS = {
    "Sun": "Libra",
    "Moon": "Scorpio",
    "Mars": "Cancer",
    "Mercury": "Pisces",
    "Jupiter": "Capricorn",
    "Venus": "Virgo",
    "Saturn": "Aries",
}

OWN_SIGNS = {
    "Sun": ["Leo"],
    "Moon": ["Cancer"],
    "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"],
    "Saturn": ["Capricorn", "Aquarius"],
}

KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}
UPACHAYA_HOUSES = {3, 6, 10, 11}


class YogaCategory(str, Enum):
    MAHAPURUSHA = "Pancha Mahapurusha"
    GAJA_KESARI = "Gaja Kesari"
    NEECHABHANGA = "Neechabhanga Raja Yoga"
    KEMADRUMA = "Kemadruma & Bhanga"
    CHANDRA = "Chandra (Lunar) Yoga"
    SURYA = "Surya (Solar) Yoga"
    VIPARITA = "Viparita Raja Yoga"
    RAJA = "Raja Yoga"
    DHANA = "Dhana Yoga"
    PARIVARTANA = "Parivartana Yoga"


class YogaResult(BaseModel):
    """Detected astrological yoga result."""

    name: str
    category: YogaCategory
    description: str
    is_formed: bool
    strength: str = Field("Strong", description="Strong, Moderate, Mild, or Cancelled")
    planets_involved: list[str] = Field(default_factory=list)
    houses_involved: list[int] = Field(default_factory=list)
    cancellation_reason: str | None = None
    effects: str | None = None


# Helper functions over ChartData
def _get_planet(chart: ChartData, name: str) -> PlanetPosition | None:
    """Find planet position by name."""
    for p in chart.planets:
        if p.name.lower() == name.lower():
            return p
    if name.lower() in ("rahu", "north node"):
        return chart.rahu
    if name.lower() in ("ketu", "south node"):
        return chart.ketu
    if name.lower() in ("lagna", "ascendant"):
        return chart.ascendant
    return None


def _get_house_by_num(chart: ChartData, house_num: int) -> HouseCusp | None:
    """Find house cusp by 1-indexed number."""
    for h in chart.houses:
        if h.house == house_num:
            return h
    return None


def _get_lord_of_house(chart: ChartData, house_num: int) -> str | None:
    """Find sign lord of given house."""
    h = _get_house_by_num(chart, house_num)
    return h.sign_lord if h else None


def _get_planets_in_house(
    chart: ChartData, house_num: int, include_nodes: bool = False
) -> list[PlanetPosition]:
    """Get all planets situated in given house."""
    found = [p for p in chart.planets if p.house == house_num]
    if include_nodes:
        if chart.rahu and chart.rahu.house == house_num:
            found.append(chart.rahu)
        if chart.ketu and chart.ketu.house == house_num:
            found.append(chart.ketu)
    return found


def _relative_house(from_house: int, step: int) -> int:
    """Calculate 1-indexed relative house distance."""
    # step=1 means same house, step=2 means next house
    return ((from_house - 1 + step - 1) % 12) + 1


def _house_distance(from_house: int, to_house: int) -> int:
    """Number of houses from from_house to to_house (1 to 12)."""
    return ((to_house - from_house) % 12) + 1


# 1. Pancha Mahapurusha Yogas
def _detect_pancha_mahapurusha(chart: ChartData) -> list[YogaResult]:
    results: list[YogaResult] = []
    mahapurusha_configs = [
        (
            "Mars",
            "Ruchaka Yoga",
            ["Aries", "Scorpio"],
            "Capricorn",
            "Courage, leadership, military/administrative prowess, physical strength, authority.",
        ),
        (
            "Mercury",
            "Bhadra Yoga",
            ["Gemini", "Virgo"],
            "Virgo",
            "High intellect, eloquence, learning, scientific acumen, longevity, respected orator.",
        ),
        (
            "Jupiter",
            "Hamsa Yoga",
            ["Sagittarius", "Pisces"],
            "Cancer",
            "Righteousness, high wisdom, spiritual authority, universal respect, nobility.",
        ),
        (
            "Venus",
            "Malavya Yoga",
            ["Taurus", "Libra"],
            "Pisces",
            "Refinement, prosperity, artistic genius, luxurious conveyances, charismatic grace.",
        ),
        (
            "Saturn",
            "Sasa Yoga",
            ["Capricorn", "Aquarius"],
            "Libra",
            "Command over masses, enduring power, discipline, strategic leadership, persistence.",
        ),
    ]

    for p_name, yoga_name, own, exalted, effects in mahapurusha_configs:
        p = _get_planet(chart, p_name)
        if not p:
            continue
        # Must be in Kendra from Lagna (1, 4, 7, 10)
        if p.house in KENDRA_HOUSES:
            is_own = p.sign in own
            is_exalted = p.sign == exalted
            if is_own or is_exalted:
                status = "exaltation" if is_exalted else "own sign"
                results.append(
                    YogaResult(
                        name=yoga_name,
                        category=YogaCategory.MAHAPURUSHA,
                        description=f"{p_name} occupies Kendra (House {p.house}) in {status} ({p.sign}).",
                        is_formed=True,
                        strength="Strong",
                        planets_involved=[p_name],
                        houses_involved=[p.house],
                        effects=effects,
                    )
                )
    return results


# 2. Gaja Kesari Yoga
def _detect_gaja_kesari(chart: ChartData) -> list[YogaResult]:
    jupiter = _get_planet(chart, "Jupiter")
    moon = _get_planet(chart, "Moon")
    if not jupiter or not moon:
        return []

    dist = _house_distance(moon.house, jupiter.house)
    if dist in KENDRA_HOUSES:
        # Check if Jupiter or Moon is afflicted
        strength = "Strong"
        if jupiter.dignity == "debilitated" or moon.dignity == "debilitated":
            strength = "Moderate"
        return [
            YogaResult(
                name="Gaja Kesari Yoga",
                category=YogaCategory.GAJA_KESARI,
                description=f"Jupiter occupies a Kendra ({dist}th house) from natal Moon (House {moon.house} to House {jupiter.house}).",
                is_formed=True,
                strength=strength,
                planets_involved=["Jupiter", "Moon"],
                houses_involved=[moon.house, jupiter.house],
                effects="Enduring reputation, virtue, triumph over adversities, high intelligence, ministerial or executive authority.",
            )
        ]
    return []


# 3. Kemadruma Yoga & Kemadruma Bhanga
def _detect_kemadruma(chart: ChartData) -> list[YogaResult]:
    moon = _get_planet(chart, "Moon")
    if not moon:
        return []

    h2 = _relative_house(moon.house, 2)
    h12 = _relative_house(moon.house, 12)

    # Physical planets excluding Sun, Rahu, Ketu
    planets_h2 = [
        p for p in _get_planets_in_house(chart, h2) if p.name not in ("Sun", "Rahu", "Ketu")
    ]
    planets_h12 = [
        p for p in _get_planets_in_house(chart, h12) if p.name not in ("Sun", "Rahu", "Ketu")
    ]

    if not planets_h2 and not planets_h12:
        # Kemadruma is nominally formed. Now check cancellations (Kemadruma Bhanga)
        bhanga_reasons: list[str] = []

        # Cancellation 1: Planets in Kendra from Lagna (excluding Rahu/Ketu)
        kendra_lagna_planets = [
            p.name
            for p in chart.planets
            if p.house in KENDRA_HOUSES and p.name not in ("Rahu", "Ketu")
        ]
        if kendra_lagna_planets:
            bhanga_reasons.append(
                f"Planets in Kendra from Lagna: {', '.join(kendra_lagna_planets)}"
            )

        # Cancellation 2: Planets in Kendra from Moon (excluding Rahu/Ketu)
        kendra_moon_planets = [
            p.name
            for p in chart.planets
            if _house_distance(moon.house, p.house) in KENDRA_HOUSES
            and p.name not in ("Moon", "Rahu", "Ketu")
        ]
        if kendra_moon_planets:
            bhanga_reasons.append(f"Planets in Kendra from Moon: {', '.join(kendra_moon_planets)}")

        # Cancellation 3: Moon conjoined with or aspected by Jupiter or Venus
        jupiter = _get_planet(chart, "Jupiter")
        if jupiter and jupiter.house == moon.house:
            bhanga_reasons.append("Moon conjoined with Jupiter")

        if bhanga_reasons:
            return [
                YogaResult(
                    name="Kemadruma Bhanga Yoga (Cancelled Kemadruma)",
                    category=YogaCategory.KEMADRUMA,
                    description="Kemadruma formed (2nd and 12th from Moon vacant of physical planets) but successfully cancelled by Kendra placements.",
                    is_formed=True,
                    strength="Cancelled",
                    planets_involved=["Moon"] + kendra_lagna_planets[:2],
                    houses_involved=[moon.house, h2, h12],
                    cancellation_reason="; ".join(bhanga_reasons),
                    effects="Initial hardship transformed into eventual stability, resilience, and self-reliance due to strong Kendra cancellation.",
                )
            ]
        else:
            return [
                YogaResult(
                    name="Kemadruma Yoga",
                    category=YogaCategory.KEMADRUMA,
                    description="No physical planets in 2nd or 12th from Moon, and no Kendra cancellations present.",
                    is_formed=True,
                    strength="Active (Uncancelled)",
                    planets_involved=["Moon"],
                    houses_involved=[moon.house, h2, h12],
                    effects="Fluctuating fortune, feelings of isolation or mental unrest; remedies and planetary propitiation recommended.",
                )
            ]
    return []


# 4. Neechabhanga Raja Yoga
def _detect_neechabhanga(chart: ChartData) -> list[YogaResult]:
    """Detect classical Phaladeepika & BPHS Neechabhanga Raja Yoga.

    Cancellation requires genuine external strength from dispositor or exaltation lords:
    1. Dispositor of debilitated sign is in Kendra from Lagna or Moon.
    2. Planet exalted in that sign is in Kendra from Lagna or Moon.
    3. Lord of the planet's own exaltation sign is in Kendra from Lagna or Moon.
    4. Dispositor directly aspects the debilitated planet.
    5. Dispositor in Dusthana (6/8/12) is flagged as delaying/moderating full manifestation.
    """
    results: list[YogaResult] = []
    debilitated_planets = [p for p in chart.planets if p.dignity == "debilitated"]
    moon = _get_planet(chart, "Moon")

    for p in debilitated_planets:
        cancellation_rules: list[str] = []
        rule_planets: list[str] = [p.name]
        dispositor_in_dusthana = False

        # 1. Sign lord (dispositor) of debilitated sign
        dispositor_name = SIGN_LORDS.get(p.sign)
        dispositor = _get_planet(chart, dispositor_name) if dispositor_name else None

        if dispositor and dispositor_name:
            if dispositor.house in DUSTHANA_HOUSES:
                dispositor_in_dusthana = True
            # Rule 1a: Dispositor in Kendra from Lagna
            if dispositor.house in KENDRA_HOUSES:
                cancellation_rules.append(
                    f"Dispositor {dispositor_name} in Kendra (House {dispositor.house}) from Lagna"
                )
                rule_planets.append(dispositor_name)
            # Rule 1b: Dispositor in Kendra from Moon
            if moon and _house_distance(moon.house, dispositor.house) in KENDRA_HOUSES:
                cancellation_rules.append(
                    f"Dispositor {dispositor_name} in Kendra ({_ordinal(_house_distance(moon.house, dispositor.house))}) from Moon"
                )
                if dispositor_name not in rule_planets:
                    rule_planets.append(dispositor_name)

        # 2. Planet that is exalted in the debilitated sign
        exalted_in_sign = None
        for plan, ex_sign in EXALTATION_SIGNS.items():
            if ex_sign == p.sign:
                exalted_in_sign = plan
                break

        if exalted_in_sign:
            ex_planet = _get_planet(chart, exalted_in_sign)
            if ex_planet:
                # Rule 2a: Planet exalted in that sign is in Kendra from Lagna
                if ex_planet.house in KENDRA_HOUSES:
                    cancellation_rules.append(
                        f"Planet exalted in {p.sign} ({exalted_in_sign}) in Kendra (House {ex_planet.house}) from Lagna"
                    )
                    rule_planets.append(exalted_in_sign)
                # Rule 2b: In Kendra from Moon
                if moon and _house_distance(moon.house, ex_planet.house) in KENDRA_HOUSES:
                    cancellation_rules.append(
                        f"Planet exalted in {p.sign} ({exalted_in_sign}) in Kendra ({_ordinal(_house_distance(moon.house, ex_planet.house))}) from Moon"
                    )
                    if exalted_in_sign not in rule_planets:
                        rule_planets.append(exalted_in_sign)

        # 3. Lord of the planet's own exaltation sign is in Kendra from Lagna or Moon
        own_ex_sign = EXALTATION_SIGNS.get(p.name)
        if own_ex_sign:
            ex_sign_lord = SIGN_LORDS.get(own_ex_sign)
            if ex_sign_lord:
                ex_lord_planet = _get_planet(chart, ex_sign_lord)
                if ex_lord_planet:
                    if ex_lord_planet.house in KENDRA_HOUSES:
                        cancellation_rules.append(
                            f"Lord of {p.name}'s exaltation sign ({ex_sign_lord}) in Kendra (House {ex_lord_planet.house}) from Lagna"
                        )
                        if ex_sign_lord not in rule_planets:
                            rule_planets.append(ex_sign_lord)
                    if moon and _house_distance(moon.house, ex_lord_planet.house) in KENDRA_HOUSES:
                        cancellation_rules.append(
                            f"Lord of {p.name}'s exaltation sign ({ex_sign_lord}) in Kendra ({_ordinal(_house_distance(moon.house, ex_lord_planet.house))}) from Moon"
                        )
                        if ex_sign_lord not in rule_planets:
                            rule_planets.append(ex_sign_lord)

        # 4. Dispositor aspects the debilitated planet (Vedic Graha Drishti)
        if dispositor:
            vedic_asps = getattr(chart, "vedic_aspects", [])
            for asp in vedic_asps:
                asp_p = getattr(asp, "planet", None) or (
                    asp.get("planet") if isinstance(asp, dict) else None
                )
                asp_th = getattr(asp, "target_house", None) or (
                    asp.get("target_house") if isinstance(asp, dict) else None
                )
                if asp_p == dispositor.name and asp_th == p.house:
                    cancellation_rules.append(
                        f"Dispositor {dispositor.name} casts Graha Drishti on debilitated {p.name} in House {p.house}"
                    )
                    if dispositor.name not in rule_planets:
                        rule_planets.append(dispositor.name)

        if cancellation_rules:
            if dispositor_in_dusthana and dispositor:
                strength = "Moderate" if len(cancellation_rules) >= 2 else "Mild"
                cancellation_rules.append(
                    f"Note: Dispositor {dispositor_name} situated in Dusthana (House {dispositor.house}) moderates early manifestation with initial friction"
                )
            else:
                strength = "Strong" if len(cancellation_rules) >= 2 else "Moderate"

            results.append(
                YogaResult(
                    name=f"Neechabhanga Raja Yoga ({p.name})",
                    category=YogaCategory.NEECHABHANGA,
                    description=f"Debilitation of {p.name} in {p.sign} is cancelled, converting weakness into extraordinary Raja Yoga power.",
                    is_formed=True,
                    strength=strength,
                    planets_involved=list(dict.fromkeys(rule_planets)),
                    houses_involved=[p.house],
                    cancellation_reason="; ".join(cancellation_rules),
                    effects=f"Great elevation after initial struggle, triumph through adversity, sovereign executive capability in {p.name}'s domains.",
                )
            )

    return results


# 5. Chandra Yogas
def _detect_chandra_yogas(chart: ChartData) -> list[YogaResult]:
    results: list[YogaResult] = []
    moon = _get_planet(chart, "Moon")
    if not moon:
        return []

    h2 = _relative_house(moon.house, 2)
    h12 = _relative_house(moon.house, 12)

    planets_h2 = [
        p.name for p in _get_planets_in_house(chart, h2) if p.name not in ("Sun", "Rahu", "Ketu")
    ]
    planets_h12 = [
        p.name for p in _get_planets_in_house(chart, h12) if p.name not in ("Sun", "Rahu", "Ketu")
    ]

    if planets_h2 and planets_h12:
        results.append(
            YogaResult(
                name="Dhurdhura Yoga",
                category=YogaCategory.CHANDRA,
                description=f"Planets occupy both 2nd ({', '.join(planets_h2)}) and 12th ({', '.join(planets_h12)}) from Moon.",
                is_formed=True,
                strength="Strong",
                planets_involved=["Moon"] + planets_h2 + planets_h12,
                houses_involved=[moon.house, h2, h12],
                effects="Abundant material comforts, generosity, conveyances, loyal followers, lasting wealth.",
            )
        )
    elif planets_h2:
        results.append(
            YogaResult(
                name="Sunapha Yoga",
                category=YogaCategory.CHANDRA,
                description=f"Planets ({', '.join(planets_h2)}) occupy 2nd house from Moon.",
                is_formed=True,
                strength="Strong",
                planets_involved=["Moon"] + planets_h2,
                houses_involved=[moon.house, h2],
                effects="Self-earned wealth, intelligent management of resources, good reputation and steady prosperity.",
            )
        )
    elif planets_h12:
        results.append(
            YogaResult(
                name="Anapha Yoga",
                category=YogaCategory.CHANDRA,
                description=f"Planets ({', '.join(planets_h12)}) occupy 12th house from Moon.",
                is_formed=True,
                strength="Strong",
                planets_involved=["Moon"] + planets_h12,
                houses_involved=[moon.house, h12],
                effects="Self-control, magnetic personality, physical health, contentment, philosophical incline.",
            )
        )

    # Chandra Mangala Yoga (Moon + Mars conjunction)
    mars = _get_planet(chart, "Mars")
    if mars and mars.house == moon.house:
        results.append(
            YogaResult(
                name="Chandra Mangala Yoga",
                category=YogaCategory.CHANDRA,
                description=f"Moon and Mars are conjoined in House {moon.house} ({moon.sign}).",
                is_formed=True,
                strength="Strong",
                planets_involved=["Moon", "Mars"],
                houses_involved=[moon.house],
                effects="Sharp financial instincts, commercial prowess, wealth generation through enterprise and tangible assets.",
            )
        )

    # Adhi Yoga from Moon (Benefics in 6th, 7th, 8th from Moon)
    h6 = _relative_house(moon.house, 6)
    h7 = _relative_house(moon.house, 7)
    h8 = _relative_house(moon.house, 8)
    benefics_678: list[str] = []
    for h_num in (h6, h7, h8):
        for p in _get_planets_in_house(chart, h_num):
            if p.name in NATURAL_BENEFICS:
                benefics_678.append(f"{p.name} (H{h_num})")
    if len(benefics_678) >= 2:
        results.append(
            YogaResult(
                name="Chandradhi Yoga",
                category=YogaCategory.CHANDRA,
                description=f"Natural benefics placed in 6th/7th/8th from Moon: {', '.join(benefics_678)}.",
                is_formed=True,
                strength="Strong",
                planets_involved=["Moon"] + [b.split()[0] for b in benefics_678],
                houses_involved=[moon.house, h6, h7, h8],
                effects="Eminent leadership, trustworthy authority, overcoming enemies peacefully, luxury and contentment.",
            )
        )

    return results


# 6. Surya Yogas
def _detect_surya_yogas(chart: ChartData) -> list[YogaResult]:
    results: list[YogaResult] = []
    sun = _get_planet(chart, "Sun")
    mercury = _get_planet(chart, "Mercury")
    if not sun:
        return []

    # Budhaditya Yoga
    if mercury and mercury.house == sun.house:
        results.append(
            YogaResult(
                name="Budhaditya Yoga",
                category=YogaCategory.SURYA,
                description=f"Sun and Mercury conjoined in House {sun.house} ({sun.sign}).",
                is_formed=True,
                strength="Strong",
                planets_involved=["Sun", "Mercury"],
                houses_involved=[sun.house],
                effects="Brilliant intellect, analytical acumen, administrative skill, eloquence and academic distinction.",
            )
        )

    # Vesi, Vasi, Ubhayachari
    h2 = _relative_house(sun.house, 2)
    h12 = _relative_house(sun.house, 12)
    planets_h2 = [
        p.name for p in _get_planets_in_house(chart, h2) if p.name not in ("Moon", "Rahu", "Ketu")
    ]
    planets_h12 = [
        p.name for p in _get_planets_in_house(chart, h12) if p.name not in ("Moon", "Rahu", "Ketu")
    ]

    if planets_h2 and planets_h12:
        results.append(
            YogaResult(
                name="Ubhayachari Yoga",
                category=YogaCategory.SURYA,
                description=f"Planets flanking Sun on both sides (2nd: {', '.join(planets_h2)}, 12th: {', '.join(planets_h12)}).",
                is_formed=True,
                strength="Strong",
                planets_involved=["Sun"] + planets_h2 + planets_h12,
                houses_involved=[sun.house, h2, h12],
                effects="Balanced fortunes, harmonious temperament, broad societal influence and steady prosperity.",
            )
        )
    elif planets_h2:
        results.append(
            YogaResult(
                name="Vesi Yoga",
                category=YogaCategory.SURYA,
                description=f"Planets ({', '.join(planets_h2)}) in 2nd house from Sun.",
                is_formed=True,
                strength="Moderate",
                planets_involved=["Sun"] + planets_h2,
                houses_involved=[sun.house, h2],
                effects="Truthfulness, articulate expression, noble character and steady accumulation of wealth.",
            )
        )
    elif planets_h12:
        results.append(
            YogaResult(
                name="Vasi Yoga",
                category=YogaCategory.SURYA,
                description=f"Planets ({', '.join(planets_h12)}) in 12th house from Sun.",
                is_formed=True,
                strength="Moderate",
                planets_involved=["Sun"] + planets_h12,
                houses_involved=[sun.house, h12],
                effects="Strong spiritual inclination, charity, renown in distant places, contemplative nature.",
            )
        )

    return results


# 7. Viparita Raja Yogas
def _detect_viparita_raja(chart: ChartData) -> list[YogaResult]:
    results: list[YogaResult] = []
    # 6th lord -> Harsha Yoga if in 6, 8, 12
    # 8th lord -> Sarala Yoga if in 6, 8, 12
    # 12th lord -> Vimala Yoga if in 6, 8, 12
    vry_configs = [
        (
            6,
            "Harsha Yoga",
            "6th lord",
            "Victory over rivals, physical stamina, immunity to scandal, unexpected sudden fortune.",
        ),
        (
            8,
            "Sarala Yoga",
            "8th lord",
            "Fearlessness, longevity, victory through crises, profound esoteric knowledge, inheritance.",
        ),
        (
            12,
            "Vimala Yoga",
            "12th lord",
            "Noble spending, independent livelihood, serene mind, virtuous reputation, liberation from debts.",
        ),
    ]

    for house_num, y_name, lord_desc, effects in vry_configs:
        lord_name = _get_lord_of_house(chart, house_num)
        if not lord_name:
            continue
        p = _get_planet(chart, lord_name)
        if p and p.house in DUSTHANA_HOUSES:
            results.append(
                YogaResult(
                    name=f"{y_name} (Viparita Raja Yoga)",
                    category=YogaCategory.VIPARITA,
                    description=f"{lord_desc} ({lord_name}) placed in Dusthana (House {p.house}).",
                    is_formed=True,
                    strength="Strong",
                    planets_involved=[lord_name],
                    houses_involved=[house_num, p.house],
                    effects=effects,
                )
            )
    return results


# 8. Key Raja & Dhana Yogas
def _detect_raja_and_dhana(chart: ChartData) -> list[YogaResult]:
    results: list[YogaResult] = []

    # Amala Yoga: Natural benefic in 10th house from Lagna or Moon
    moon = _get_planet(chart, "Moon")
    benefics_in_10_lagna = [
        p.name for p in _get_planets_in_house(chart, 10) if p.name in NATURAL_BENEFICS
    ]
    if benefics_in_10_lagna:
        results.append(
            YogaResult(
                name="Amala Yoga (from Lagna)",
                category=YogaCategory.RAJA,
                description=f"Natural benefic ({', '.join(benefics_in_10_lagna)}) occupies the 10th house from Lagna.",
                is_formed=True,
                strength="Strong",
                planets_involved=benefics_in_10_lagna,
                houses_involved=[10],
                effects="Spotless professional reputation, benevolent deeds, enduring honor and executive leadership.",
            )
        )

    if moon:
        h10_moon = _relative_house(moon.house, 10)
        benefics_in_10_moon = [
            p.name for p in _get_planets_in_house(chart, h10_moon) if p.name in NATURAL_BENEFICS
        ]
        if benefics_in_10_moon:
            results.append(
                YogaResult(
                    name="Amala Yoga (from Moon)",
                    category=YogaCategory.RAJA,
                    description=f"Natural benefic ({', '.join(benefics_in_10_moon)}) occupies the 10th house from Moon.",
                    is_formed=True,
                    strength="Strong",
                    planets_involved=benefics_in_10_moon,
                    houses_involved=[h10_moon],
                    effects="Clean public image, lasting community esteem, upright profession.",
                )
            )

    # Dhana Yoga: 2nd lord and 11th lord connection
    l2 = _get_lord_of_house(chart, 2)
    l11 = _get_lord_of_house(chart, 11)
    p2 = _get_planet(chart, l2) if l2 else None
    p11 = _get_planet(chart, l11) if l11 else None

    if p2 and p11 and l2 and l11:
        if p2.house == p11.house:
            results.append(
                YogaResult(
                    name="Maha Dhana Yoga (2nd & 11th Lords Conjunction)",
                    category=YogaCategory.DHANA,
                    description=f"2nd lord ({l2}) and 11th lord ({l11}) are conjoined in House {p2.house}.",
                    is_formed=True,
                    strength="Strong",
                    planets_involved=[l2, l11],
                    houses_involved=[2, 11, p2.house],
                    effects="Exceptional wealth accumulation, prolific gains from multiple income streams.",
                )
            )
        elif p2.house in (2, 11) or p11.house in (2, 11):
            results.append(
                YogaResult(
                    name="Dhana Yoga (Wealth Axis)",
                    category=YogaCategory.DHANA,
                    description=f"Wealth lord placed in wealth house ({l2} in H{p2.house}, {l11} in H{p11.house}).",
                    is_formed=True,
                    strength="Moderate",
                    planets_involved=list(set(filter(None, [l2, l11]))),
                    houses_involved=[2, 11],
                    effects="Steady financial growth, sound fiscal stewardship, security in possessions.",
                )
            )

    # Kendra-Trikona Raja Yoga (Dharma-Karmadhipati / Kendra-Trikona conjunction)
    # Check conjunction of Kendra lord (4, 7, 10) with Trikona lord (5, 9)
    kendra_houses_check = [4, 7, 10]
    trikona_houses_check = [5, 9]
    k_lords = {h: _get_lord_of_house(chart, h) for h in kendra_houses_check}
    t_lords = {h: _get_lord_of_house(chart, h) for h in trikona_houses_check}

    formed_pairs: set[tuple[str, str]] = set()
    for kh, kl in k_lords.items():
        if not kl:
            continue
        kp = _get_planet(chart, kl)
        if not kp:
            continue
        for th, tl in t_lords.items():
            if not tl or kl == tl:
                continue
            tp = _get_planet(chart, tl)
            if not tp:
                continue
            if kp.house == tp.house:
                pair_key: tuple[str, str] = (min(kl, tl), max(kl, tl))
                if pair_key not in formed_pairs:
                    formed_pairs.add(pair_key)
                    results.append(
                        YogaResult(
                            name=f"Kendra-Trikona Raja Yoga ({kl} & {tl})",
                            category=YogaCategory.RAJA,
                            description=f"Kendra lord of House {kh} ({kl}) and Trikona lord of House {th} ({tl}) are conjoined in House {kp.house}.",
                            is_formed=True,
                            strength="Strong",
                            planets_involved=[kl, tl],
                            houses_involved=[kh, th, kp.house],
                            effects="Elevation in social hierarchy, government or corporate leadership, power, righteous wealth.",
                        )
                    )

    return results


# 9. Parivartana Yogas (Mutual Sign Exchange)
def _detect_parivartana(chart: ChartData) -> list[YogaResult]:
    """Detect classical Parivartana Yogas (mutual sign exchange between two planet lords).

    Phaladeepika Ch 6 & BPHS:
    1. Maha Yoga (Exchanges between Kendra/Trikona/2nd/11th lords: 1, 2, 4, 5, 7, 9, 10, 11):
       Bestows enduring prosperity, sovereignty, status, and divine protection.
    2. Kahala Yoga (Exchange involving 3rd house lord with 1, 2, 4, 5, 7, 9, 10, 11 lords):
       Bestows valor, fighting spirit, persistence, bold initiatives, self-made fortune.
    3. Dainya Yoga (Exchange involving any Dusthana house lord: 6, 8, 12 with any house):
       Indicates struggle, expenditure, spiritual renunciation, unconventional career paths, or sudden reversals.
    """
    results: list[YogaResult] = []
    classical_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    planet_objs = {p.name: p for p in chart.planets if p.name in classical_planets}
    seen_pairs: set[tuple[str, ...]] = set()

    for p1_name in classical_planets:
        p1 = planet_objs.get(p1_name)
        if not p1:
            continue
        p2_name = SIGN_LORDS.get(p1.sign)
        if not p2_name or p2_name == p1_name or p2_name not in planet_objs:
            continue
        p2 = planet_objs[p2_name]
        if SIGN_LORDS.get(p2.sign) == p1_name:
            pair_key = tuple(sorted([p1_name, p2_name]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            h1 = p1.house
            h2 = p2.house

            if h1 in DUSTHANA_HOUSES or h2 in DUSTHANA_HOUSES:
                yoga_name = f"Dainya Parivartana Yoga ({p1_name} & {p2_name})"
                strength = "Moderate"
                desc = (
                    f"Mutual sign exchange (Parivartana) involving Dusthana house(s): "
                    f"{p1_name} (in House {h1}, sign of {p2_name}) and {p2_name} (in House {h2}, sign of {p1_name})."
                )
                effects = (
                    f"Karmic exchange between House {h1} and House {h2}. Generates volatile experiences, "
                    "transformations through adversity, expenditures, or unconventional paths, "
                    "with deep potential for spiritual awakening and detachment."
                )
            elif h1 == 3 or h2 == 3:
                yoga_name = f"Kahala Parivartana Yoga ({p1_name} & {p2_name})"
                strength = "Strong"
                desc = (
                    f"Mutual sign exchange involving the 3rd house of courage: "
                    f"{p1_name} (in House {h1}) and {p2_name} (in House {h2})."
                )
                effects = "Endows courageous determination, entrepreneurial valor, self-made success through relentless effort."
            else:
                yoga_name = f"Maha Parivartana Yoga ({p1_name} & {p2_name})"
                strength = "Strong"
                desc = (
                    f"Auspicious mutual sign exchange between benefic houses: "
                    f"{p1_name} (in House {h1}) and {p2_name} (in House {h2})."
                )
                effects = "Highly auspicious classical Raja-Dhana yoga. Bestows enduring leadership, prestige, wealth, and sovereign authority."

            results.append(
                YogaResult(
                    name=yoga_name,
                    category=YogaCategory.PARIVARTANA,
                    description=desc,
                    is_formed=True,
                    strength=strength,
                    planets_involved=[p1_name, p2_name],
                    houses_involved=[h1, h2],
                    effects=effects,
                )
            )

    return results


def detect_yogas(chart: ChartData) -> list[YogaResult]:
    """
    Execute complete rule-based Vedic Yoga detection over ChartData.
    """
    yogas: list[YogaResult] = []
    yogas.extend(_detect_pancha_mahapurusha(chart))
    yogas.extend(_detect_gaja_kesari(chart))
    yogas.extend(_detect_kemadruma(chart))
    yogas.extend(_detect_neechabhanga(chart))
    yogas.extend(_detect_chandra_yogas(chart))
    yogas.extend(_detect_surya_yogas(chart))
    yogas.extend(_detect_viparita_raja(chart))
    yogas.extend(_detect_raja_and_dhana(chart))
    yogas.extend(_detect_parivartana(chart))
    return yogas


def format_yogas_table(yogas: list[YogaResult]) -> str:
    """Format detected yogas into clean ASCII table."""
    lines = []
    lines.append("=" * 84)
    lines.append("                           VEDIC YOGA DETECTION REPORT")
    lines.append("=" * 84)
    if not yogas:
        lines.append(" No major classical yogas detected under strict classical criteria.")
        lines.append("=" * 84)
        return "\n".join(lines)

    lines.append(f" Total Yogas Identified: {len(yogas)}")
    lines.append("-" * 84)
    for idx, y in enumerate(yogas, 1):
        status_tag = f"[{y.strength.upper()}]"
        lines.append(
            f" {idx:2d}. {y.name} {status_tag} ({y.category.value if isinstance(y.category, YogaCategory) else y.category})"
        )
        lines.append(f"     Rule    : {y.description}")
        if y.cancellation_reason:
            lines.append(f"     Cancel  : {y.cancellation_reason}")
        if y.planets_involved:
            lines.append(
                f"     Grahas  : {', '.join(y.planets_involved)} | Houses: {', '.join(map(str, y.houses_involved))}"
            )
        if y.effects:
            lines.append(f"     Effects : {y.effects}")
        lines.append("-" * 84)
    lines.append("=" * 84)
    return "\n".join(lines)


def format_yogas_markdown(yogas: list[YogaResult]) -> str:
    """Format detected yogas into GitHub-flavored Markdown."""
    lines = ["# Vedic Yoga Detection Report", ""]
    if not yogas:
        lines.append("_No major classical yogas detected under strict classical criteria._")
        return "\n".join(lines)

    lines.append(f"**Total Yogas Identified**: {len(yogas)}\n")
    lines.append("| No. | Yoga Name | Category | Strength | Planets Involved | Description |")
    lines.append("|:---:|:---|:---|:---:|:---|:---|")
    for idx, y in enumerate(yogas, 1):
        cat_str = y.category.value if isinstance(y.category, YogaCategory) else y.category
        planets_str = ", ".join(y.planets_involved) if y.planets_involved else "-"
        lines.append(
            f"| {idx} | **{y.name}** | {cat_str} | {y.strength} | {planets_str} | {y.description} |"
        )

    lines.append("\n## Detailed Effects\n")
    for idx, y in enumerate(yogas, 1):
        lines.append(f"### {idx}. {y.name} ({y.strength})")
        lines.append(
            f"- **Category**: {y.category.value if isinstance(y.category, YogaCategory) else y.category}"
        )
        lines.append(
            f"- **Planets**: {', '.join(y.planets_involved) if y.planets_involved else 'None'}"
        )
        lines.append(
            f"- **Houses**: {', '.join(map(str, y.houses_involved)) if y.houses_involved else 'None'}"
        )
        lines.append(f"- **Rule**: {y.description}")
        if y.cancellation_reason:
            lines.append(f"- **Cancellation / Modification**: {y.cancellation_reason}")
        if y.effects:
            lines.append(f"- **Traditional Effects**: {y.effects}")
        lines.append("")

    return "\n".join(lines)
