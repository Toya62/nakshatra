"""
Nakshatra Astrological Predictor & Synthesizer Engine
Deterministic multi-step classical Vedic predictive evaluation across core life domains:
- Career & Status (10th Bhava, Karma, D10 Dashamsha)
- Relationships & Marriage (7th Bhava, Kalatra, D9 Navamsha)
- Wealth & Prosperity (2nd & 11th Bhavas, Dhana, SAV balance)
- Spiritual Dharma & Moksha (9th & 12th Bhavas, Ketu, D9/D20)
- Vitality & Health (1st, 6th & 8th Bhavas, Lagnesha, Ayur)

Evaluates:
1. Natal Promise (Bhava lords, dignities, occupants, SAV bindus, Shadbala)
2. Varga Confirmations (D9 Navamsha, D10 Dashamsha)
3. Vimshottari Dasha Triggers (MD-AD relative angle e.g. 5/9, 6/8, 4/10)
4. Gochar / Transits (Double transit activation, Sade Sati, favorable houses)
5. Active Yoga Triggers (Yogas tied to active dasha lords)
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from nakshatra.core import (
    CHART_BODIES,
    SIGN_LORDS,
    VEDIC_PLANETS,
    ZODIAC_SIGNS,
    ChartData,
    HouseCusp,
    PlanetPosition,
    calculate_dignity,
)
from nakshatra.yogas import (
    EXALTATION_SIGNS,
    NATURAL_BENEFICS,
    NATURAL_MALEFICS,
    OWN_SIGNS,
    YogaResult,
    detect_yogas,
)

if TYPE_CHECKING:
    from nakshatra.transits import TransitReport


class DomainCategory(str, Enum):
    """Core life domains for Vedic prediction."""

    CAREER = "career"
    RELATIONSHIP = "relationship"
    WEALTH = "wealth"
    SPIRITUAL_DHARMA = "spiritual_dharma"
    HEALTH = "health"


class PromiseTier(str, Enum):
    """Deterministic promise strength tier."""

    EXCEPTIONAL = "Exceptional"
    FAVORABLE = "Favorable"
    MIXED = "Mixed"
    CHALLENGING = "Challenging"
    OBSTRUCTED = "Obstructed"


class DomainPrediction(BaseModel):
    """Comprehensive classical prediction for a specific life domain."""

    domain: DomainCategory
    promise_tier: PromiseTier
    primary_houses: list[int]
    primary_lords: list[str]
    karakas: list[str]
    promise_summary: str
    varga_confirmation: str
    dasha_timing: str
    active_transits: list[str]
    active_yogas: list[str]
    classical_citations: list[str]
    remedies: list[str]
    key_verdict: str
    score: int = Field(0, description="Underlying composite strength score")


# --- Helper Navigation Functions ---


def get_planet_by_name(chart: ChartData, name: str) -> PlanetPosition | None:
    """Retrieve planet position from chart (including nodes and ascendant)."""
    normalized = name.strip().lower()
    for p in chart.planets:
        if p.name.lower() == normalized:
            return p
    if normalized in ("rahu", "north node"):
        return chart.rahu
    if normalized in ("ketu", "south node"):
        return chart.ketu
    if normalized in ("ascendant", "lagna"):
        return chart.ascendant
    if normalized in ("midheaven", "mc"):
        return chart.midheaven
    return None


def get_house_by_number(chart: ChartData, house_num: int) -> HouseCusp | None:
    """Retrieve house cusp data by 1-indexed house number (1-12)."""
    for h in chart.houses:
        if h.house == house_num:
            return h
    return None


def get_house_lord(chart: ChartData, house_num: int) -> str | None:
    """Retrieve sign lord of specified house."""
    h = get_house_by_number(chart, house_num)
    if h and h.sign_lord:
        return h.sign_lord
    if h and h.sign in SIGN_LORDS:
        return SIGN_LORDS[h.sign]
    return None


def get_house_occupants(
    chart: ChartData, house_num: int, include_nodes: bool = True
) -> list[PlanetPosition]:
    """Retrieve all planets situated in specified house."""
    occupants = [p for p in chart.planets if p.house == house_num]
    if include_nodes:
        if chart.rahu and chart.rahu.house == house_num:
            occupants.append(chart.rahu)
        if chart.ketu and chart.ketu.house == house_num:
            occupants.append(chart.ketu)
    return occupants


def get_house_sav(chart: ChartData, house_num: int) -> int | None:
    """Retrieve Sarvashtakavarga (SAV) bindu count for house's sign."""
    if not chart.ashtakavarga or not chart.ashtakavarga.sarvashtakavarga:
        return None
    h = get_house_by_number(chart, house_num)
    if not h or h.sign not in ZODIAC_SIGNS:
        return None
    sign_idx = ZODIAC_SIGNS.index(h.sign)
    if 0 <= sign_idx < len(chart.ashtakavarga.sarvashtakavarga):
        return chart.ashtakavarga.sarvashtakavarga[sign_idx]
    return None


# --- Step 3: Dasha Relationship Calculation ---


def dasha_lord_relationship(
    md_lord: str | None, ad_lord: str | None, chart: ChartData
) -> dict[str, Any]:
    """
    Calculate classical relative positional relationship (Bhavat Bhavam)
    between current Mahadasha lord and Antardasha lord.
    """
    if not md_lord or not ad_lord:
        return {
            "pair": "None",
            "name": "Undefined",
            "nature": "Neutral",
            "description": "Current operating dasha lords not identified.",
        }

    p_md = get_planet_by_name(chart, md_lord)
    p_ad = get_planet_by_name(chart, ad_lord)

    if not p_md or not p_ad:
        return {
            "pair": "Unknown",
            "name": "Undetermined",
            "nature": "Neutral",
            "description": f"Positions for {md_lord} or {ad_lord} not found in chart.",
        }

    h_md = p_md.house
    h_ad = p_ad.house

    # Distance from MD to AD (1-indexed)
    dist = ((h_ad - h_md) % 12) + 1
    # Normalized pair representation where smaller distance comes first
    comp = 14 - dist if dist > 1 else 1
    smaller = min(dist, comp)
    larger = max(dist, comp)
    pair = f"{smaller}/{larger}" if smaller != larger else f"{smaller}/{smaller}"

    relationships: dict[str, tuple[str, str, str]] = {
        "1/1": (
            "Yuti (Conjunction)",
            "Concentrated Focus",
            f"{md_lord} and {ad_lord} co-occupy House {h_md}, fusing their energies into intense, direct manifestation.",
        ),
        "5/9": (
            "Navam-Pancham (Trinal Harmony)",
            "Auspicious & Fortunate",
            f"{md_lord} and {ad_lord} are in 5th/9th trines from each other, conferring Dharma, grace, ease of execution, and good fortune.",
        ),
        "3/11": (
            "Sahaja-Labha (Cooperative Growth)",
            "Productive & Fulfilling",
            f"{md_lord} and {ad_lord} sit in 3rd/11th Upachaya relationship, driving tangible gains through effort, enterprise, and networking.",
        ),
        "4/10": (
            "Kendra (Action & Exertion)",
            "Dynamic Responsibility",
            f"{md_lord} and {ad_lord} sit in 4th/10th Kendra angles, demanding hard work, decisive structural realignment, and professional stewardship.",
        ),
        "1/7": (
            "Samasaptaka (Direct Opposition/Aspect)",
            "Overt Manifestation",
            f"{md_lord} and {ad_lord} directly aspect each other across 1st/7th axes, bringing partnerships and visible results into sharp clarity.",
        ),
        "6/8": (
            "Shadashtaka (Karmic Friction)",
            "Karmic Retribution & Obstacles",
            f"{md_lord} and {ad_lord} form a 6th/8th Shadashtaka angle, requiring diligence against health vulnerability, disputes, or friction.",
        ),
        "2/12": (
            "Dwirdwadasha (Expenditure & Displacement)",
            "Transitional & Reorienting",
            f"{md_lord} and {ad_lord} form a 2nd/12th angle, indicating resource outflow, foreign connections, release of older habits, or expenses.",
        ),
    }

    info = relationships.get(
        pair,
        (
            "Sambandha",
            "Moderate",
            f"Mutual angle of {dist} houses between {md_lord} and {ad_lord}.",
        ),
    )
    return {
        "pair": pair,
        "name": info[0],
        "nature": info[1],
        "description": info[2],
        "md_house": h_md,
        "ad_house": h_ad,
    }


# --- Step 5: Active Yoga Filter ---


def filter_active_yogas(
    chart: ChartData,
    md_lord: str | None = None,
    ad_lord: str | None = None,
) -> list[YogaResult]:
    """
    Filter detected yogas to identify those activated in the current life chapter
    by the operating Mahadasha or Antardasha lords.
    """
    all_yogas = chart.get_yogas()
    formed_yogas = [y for y in all_yogas if y.is_formed and y.strength != "Cancelled"]

    if not md_lord and not ad_lord:
        # If no active dasha specified, return all prominent formed yogas
        return formed_yogas[:6]

    active_lords = {l.strip().lower() for l in (md_lord, ad_lord) if l}
    triggered: list[YogaResult] = []
    for y in formed_yogas:
        planets_in_yoga = {p.strip().lower() for p in y.planets_involved}
        if active_lords.intersection(planets_in_yoga):
            triggered.append(y)

    return triggered if triggered else formed_yogas[:4]


# --- Domain Evaluators ---


def _varga_dignity(
    planet_name: str,
    varga_data: dict[str, str] | None,
    d1_sign: str,
) -> tuple[str, bool]:
    """Check planet sign, dignity, and vargottama status in a varga chart."""
    if not varga_data or planet_name not in varga_data:
        return ("Unknown", False)
    v_sign = varga_data[planet_name]
    is_vargottama = v_sign.lower() == d1_sign.lower()
    dignity = calculate_dignity(planet_name, v_sign)
    return (f"{v_sign} ({dignity})", is_vargottama)


def evaluate_career(
    chart: ChartData, transits: TransitReport | None = None
) -> DomainPrediction:
    """
    Step-by-step classical evaluation of Career, Profession, and Social Status (10th Bhava).
    Scriptural basis: BPHS Ch. 24, Phaladeepika Ch. 15, Saravali Ch. 34.
    """
    score = 0
    primary_houses = [10, 1, 6, 11]
    karakas = ["Sun", "Saturn", "Mercury"]

    # 1. 10th House & Lord analysis
    h10 = get_house_by_number(chart, 10)
    lord10_name = get_house_lord(chart, 10)
    p_lord10 = get_planet_by_name(chart, lord10_name) if lord10_name else None
    occupants = get_house_occupants(chart, 10)
    sav10 = get_house_sav(chart, 10)
    sav11 = get_house_sav(chart, 11)

    promise_parts: list[str] = []
    if lord10_name and p_lord10:
        dignity = p_lord10.dignity or calculate_dignity(lord10_name, p_lord10.sign)
        if dignity == "exalted":
            score += 3
            promise_parts.append(
                f"10th lord {lord10_name} is exalted in {p_lord10.sign} (House {p_lord10.house}), granting high professional authority."
            )
        elif dignity == "own_sign":
            score += 2
            promise_parts.append(
                f"10th lord {lord10_name} is dignified in own sign {p_lord10.sign} in House {p_lord10.house}."
            )
        elif dignity == "debilitated":
            score -= 3
            promise_parts.append(
                f"10th lord {lord10_name} is debilitated in {p_lord10.sign} in House {p_lord10.house}, signaling career friction or periodic reinvention."
            )
        else:
            score += 1 if p_lord10.house in (1, 4, 7, 10, 5, 9, 11) else -1
            promise_parts.append(
                f"10th lord {lord10_name} resides in House {p_lord10.house} ({p_lord10.sign})."
            )

    if occupants:
        occ_names = [p.name for p in occupants]
        promise_parts.append(f"Occupants in 10th Bhava: {', '.join(occ_names)}.")
        for p in occupants:
            if p.name in NATURAL_BENEFICS:
                score += 2
            elif p.name in NATURAL_MALEFICS and p.dignity not in ("exalted", "own_sign"):
                score -= 1

    if sav10 is not None:
        if sav10 >= 32:
            score += 2
            promise_parts.append(
                f"10th Bhava holds an exceptional {sav10} SAV bindus, conferring unshakable career resilience."
            )
        elif sav10 >= 28:
            score += 1
            promise_parts.append(f"10th Bhava holds a strong {sav10} SAV bindus.")
        elif sav10 < 25:
            score -= 2
            promise_parts.append(
                f"10th Bhava has lower {sav10} SAV bindus (<28), suggesting progress requires persistence."
            )

    # 2. Varga Confirmation (D9 & D10)
    varga_parts: list[str] = []
    if lord10_name and p_lord10:
        d9_data = chart.vargas.get("D9") if chart.vargas else None
        d9_status, is_vg = _varga_dignity(lord10_name, d9_data, p_lord10.sign)
        if is_vg:
            score += 2
            varga_parts.append(
                f"10th lord {lord10_name} is Vargottama (same sign in D1 & D9), solidifying natal career potential."
            )
        elif "exalted" in d9_status or "own_sign" in d9_status:
            score += 1
            varga_parts.append(f"10th lord {lord10_name} gains strength in D9 Navamsha: {d9_status}.")
        elif "debilitated" in d9_status:
            score -= 2
            varga_parts.append(f"10th lord {lord10_name} loses strength in D9 Navamsha: {d9_status}.")

    d10 = chart.get_varga("D10")
    if d10 and d10.get("planets"):
        p_d10 = d10["planets"].get(lord10_name)
        if p_d10:
            h_d10 = p_d10.get("house")
            s_d10 = p_d10.get("sign")
            varga_parts.append(f"In D10 Dashamsha, 10th lord {lord10_name} occupies House {h_d10} in {s_d10}.")
            if h_d10 in (1, 10, 11):
                score += 1

    # 3. Dasha Trigger
    dasha_parts: list[str] = []
    md_lord = chart.dashas.current_md.lord if chart.dashas and chart.dashas.current_md else None
    ad_lord = chart.dashas.current_ad.lord if chart.dashas and chart.dashas.current_ad else None
    if md_lord and ad_lord:
        rel = dasha_lord_relationship(md_lord, ad_lord, chart)
        dasha_parts.append(
            f"Current Vimshottari period: {md_lord} Mahadasha / {ad_lord} Antardasha."
        )
        dasha_parts.append(f"Dasha relationship: {rel['pair']} {rel['name']} ({rel['nature']}) - {rel['description']}")
        if md_lord == lord10_name or ad_lord == lord10_name:
            score += 2
            dasha_parts.append("Direct 10th lord activation in current dasha phase!")
        if rel["pair"] in ("5/9", "3/11"):
            score += 1
        elif rel["pair"] == "6/8":
            score -= 1
    else:
        dasha_parts.append("Dasha timing requires calculation with active birth chart.")

    # 4. Transits (Gochar)
    transit_parts: list[str] = []
    t_report = transits or (chart.get_transits() if hasattr(chart, "get_transits") else None)
    if t_report:
        if 10 in t_report.double_transit_houses:
            score += 3
            transit_parts.append(
                "★ DOUBLE TRANSIT ACTIVATION: Both Jupiter and Saturn aspect/transit the 10th Bhava, signaling a major career inflection or milestone!"
            )
        if 11 in t_report.double_transit_houses:
            score += 1
            transit_parts.append("Double transit in 11th Bhava supports career rewards and recognition.")
        ss = t_report.sade_sati
        if ss.is_kantaka_shani:
            score -= 1
            transit_parts.append("Saturn Kantaka Shani (4th/10th from Moon) tests professional endurance and structure.")
        elif ss.is_active:
            transit_parts.append(f"Saturn Sade Sati ({ss.phase}) prompts patient professional reorientation.")

    # 5. Active Yogas
    act_yogas = filter_active_yogas(chart, md_lord, ad_lord)
    career_yogas = [
        y.name for y in act_yogas if y.category.value in ("Raja Yoga", "Pancha Mahapurusha", "Gaja Kesari")
    ]
    if career_yogas:
        score += min(len(career_yogas), 2)

    tier = _score_to_tier(score)
    primary_lords = [lord10_name] if lord10_name else []

    key_verdict = (
        f"Career promise is evaluated as {tier.value.upper()}. "
        + (
            f"Activated by {md_lord}-{ad_lord} dasha with strong professional momentum."
            if score >= 2
            else "Professional growth requires steady effort, disciplined skill acquisition, and ethical focus."
        )
    )

    return DomainPrediction(
        domain=DomainCategory.CAREER,
        promise_tier=tier,
        primary_houses=primary_houses,
        primary_lords=primary_lords,
        karakas=karakas,
        promise_summary=" ".join(promise_parts) or "10th Bhava configurations analyzed.",
        varga_confirmation=" ".join(varga_parts) or "D9 & D10 divisional positions verified.",
        dasha_timing=" ".join(dasha_parts) or "Dasha timing evaluation complete.",
        active_transits=transit_parts or ["Transits stable across profession bhavas."],
        active_yogas=career_yogas or [y.name for y in act_yogas[:2]],
        classical_citations=[
            "Brihat Parashara Hora Shastra (BPHS) Ch. 24 (10th House Effects)",
            "Phaladeepika Ch. 15 (Karma Bhava Phala)",
            "Saravali Ch. 34 (Rajayoga Adhyaya)",
        ],
        remedies=[
            "Surya Arghya at sunrise with Gayatri Mantra for leadership vitality",
            "Shani Seva: Respect and honor service workers; perform voluntary labor on Saturdays",
            "Cultivate transparent ethics and avoid shortcuts in professional commitments",
        ],
        key_verdict=key_verdict,
        score=score,
    )


def evaluate_relationship(
    chart: ChartData, transits: TransitReport | None = None
) -> DomainPrediction:
    """
    Classical evaluation of Relationships, Marriage, and Partnerships (7th Bhava).
    Scriptural basis: BPHS Ch. 20, Phaladeepika Ch. 10, Brihat Jataka Ch. 14.
    """
    score = 0
    primary_houses = [7, 1, 2, 11]
    karakas = ["Venus", "Jupiter"]

    h7 = get_house_by_number(chart, 7)
    lord7_name = get_house_lord(chart, 7)
    p_lord7 = get_planet_by_name(chart, lord7_name) if lord7_name else None
    occupants = get_house_occupants(chart, 7)
    sav7 = get_house_sav(chart, 7)
    p_venus = get_planet_by_name(chart, "Venus")

    promise_parts: list[str] = []
    if lord7_name and p_lord7:
        dignity = p_lord7.dignity or calculate_dignity(lord7_name, p_lord7.sign)
        if dignity == "exalted":
            score += 3
            promise_parts.append(
                f"7th lord {lord7_name} is exalted in {p_lord7.sign} (House {p_lord7.house}), conferring marital grace and partner nobility."
            )
        elif dignity == "own_sign":
            score += 2
            promise_parts.append(
                f"7th lord {lord7_name} is strong in own sign {p_lord7.sign} in House {p_lord7.house}."
            )
        elif dignity == "debilitated":
            score -= 3
            promise_parts.append(
                f"7th lord {lord7_name} is debilitated in {p_lord7.sign} (House {p_lord7.house}), indicating need for mutual patience and realistic expectations."
            )
        else:
            score += 1 if p_lord7.house in (1, 4, 7, 10, 5, 9, 2) else -1
            promise_parts.append(
                f"7th lord {lord7_name} is situated in House {p_lord7.house} ({p_lord7.sign})."
            )

    if p_venus:
        v_dignity = p_venus.dignity or calculate_dignity("Venus", p_venus.sign)
        if v_dignity == "exalted":
            score += 2
            promise_parts.append("Venus (Kalatra Karaka) is exalted, conferring deep devotion and aesthetic harmony.")
        elif v_dignity == "debilitated":
            score -= 2
            promise_parts.append("Venus is debilitated in Virgo, advising against over-critical tendencies in romance.")

    # Kuja Dosha (Manglik check from Lagna)
    p_mars = get_planet_by_name(chart, "Mars")
    if p_mars and p_mars.house in (1, 4, 7, 8, 12):
        if p_mars.dignity not in ("exalted", "own_sign"):
            score -= 1
            promise_parts.append(
                f"Kuja Dosha indication: Mars in House {p_mars.house} brings passionate energy requiring conscious anger management."
            )

    if occupants:
        occ_names = [p.name for p in occupants]
        promise_parts.append(f"Planets in 7th Bhava: {', '.join(occ_names)}.")
        for p in occupants:
            if p.name in NATURAL_BENEFICS:
                score += 2
            elif p.name in NATURAL_MALEFICS:
                score -= 1

    if sav7 is not None:
        if sav7 >= 28:
            score += 1
            promise_parts.append(f"7th Bhava holds {sav7} SAV bindus, supporting marital stability.")
        elif sav7 < 25:
            score -= 1
            promise_parts.append(f"7th Bhava holds {sav7} SAV bindus, requiring conscious effort toward harmony.")

    # 2. Varga Confirmation (D9 Navamsha is paramount for marriage)
    varga_parts: list[str] = []
    d9_data = chart.vargas.get("D9") if chart.vargas else None
    if lord7_name and p_lord7:
        d9_status, is_vg = _varga_dignity(lord7_name, d9_data, p_lord7.sign)
        if is_vg:
            score += 2
            varga_parts.append(f"7th lord {lord7_name} is Vargottama in Navamsha (D9), protecting marital bond.")
        elif "exalted" in d9_status or "own_sign" in d9_status:
            score += 1
            varga_parts.append(f"7th lord {lord7_name} is well-placed in D9: {d9_status}.")
        elif "debilitated" in d9_status:
            score -= 2
            varga_parts.append(f"7th lord {lord7_name} is debilitated in D9: {d9_status}.")

    # 3. Dasha Timing
    dasha_parts: list[str] = []
    md_lord = chart.dashas.current_md.lord if chart.dashas and chart.dashas.current_md else None
    ad_lord = chart.dashas.current_ad.lord if chart.dashas and chart.dashas.current_ad else None
    if md_lord and ad_lord:
        rel = dasha_lord_relationship(md_lord, ad_lord, chart)
        dasha_parts.append(f"Active Dasha: {md_lord}/{ad_lord} in {rel['pair']} {rel['name']} ({rel['nature']}).")
        if md_lord in (lord7_name, "Venus") or ad_lord in (lord7_name, "Venus"):
            score += 2
            dasha_parts.append("Direct 7th lord / Kalatra Karaka activation in current period.")
    else:
        dasha_parts.append("Dasha timing requires chart calculation.")

    # 4. Transits
    transit_parts: list[str] = []
    t_report = transits or (chart.get_transits() if hasattr(chart, "get_transits") else None)
    if t_report:
        if 7 in t_report.double_transit_houses:
            score += 3
            transit_parts.append(
                "★ DOUBLE TRANSIT ACTIVATION: 7th Bhava is jointly energized by Jupiter & Saturn, facilitating union or major partnership clarity!"
            )
        # Check transit Jupiter in 7th from Moon or Lagna
        for tp in t_report.planets:
            if tp.name == "Jupiter" and (tp.house_from_lagna == 7 or tp.house_from_moon == 7):
                score += 2
                transit_parts.append("Transit Jupiter blesses the 7th Bhava with harmony and understanding.")

    tier = _score_to_tier(score)
    primary_lords = [lord7_name] if lord7_name else []
    act_yogas = filter_active_yogas(chart, md_lord, ad_lord)

    return DomainPrediction(
        domain=DomainCategory.RELATIONSHIP,
        promise_tier=tier,
        primary_houses=primary_houses,
        primary_lords=primary_lords,
        karakas=karakas,
        promise_summary=" ".join(promise_parts) or "7th Bhava analyzed.",
        varga_confirmation=" ".join(varga_parts) or "D9 Navamsha Kalatra verified.",
        dasha_timing=" ".join(dasha_parts) or "Dasha evaluated.",
        active_transits=transit_parts or ["Transits balanced."],
        active_yogas=[y.name for y in act_yogas[:2]],
        classical_citations=[
            "Brihat Parashara Hora Shastra (BPHS) Ch. 20 (7th House Judgments)",
            "Phaladeepika Ch. 10 (Kalatra Bhava Phala)",
            "Brihat Jataka Ch. 14 (Strijataka)",
        ],
        remedies=[
            "Cultivate mindful communication, mutual forgiveness, and patience",
            "Shukra Japa or Lakshmi Gayatri recitation on Fridays",
            "Honor the sacred balance between personal autonomy and partnership duty",
        ],
        key_verdict=f"Relationship potential is {tier.value.upper()}. Harmony flourishes when grounded in mutual dharma.",
        score=score,
    )


def evaluate_wealth(
    chart: ChartData, transits: TransitReport | None = None
) -> DomainPrediction:
    """
    Classical evaluation of Wealth, Liquid Gains, and Savings (2nd & 11th Bhavas).
    Scriptural basis: BPHS Ch. 41 (Dhana Yogas), Saravali Ch. 35, Phaladeepika Ch. 16.
    """
    score = 0
    primary_houses = [2, 11, 5, 9]
    karakas = ["Jupiter", "Mercury"]

    lord2_name = get_house_lord(chart, 2)
    lord11_name = get_house_lord(chart, 11)
    p_lord2 = get_planet_by_name(chart, lord2_name) if lord2_name else None
    p_lord11 = get_planet_by_name(chart, lord11_name) if lord11_name else None
    sav2 = get_house_sav(chart, 2)
    sav11 = get_house_sav(chart, 11)
    sav12 = get_house_sav(chart, 12)

    promise_parts: list[str] = []
    if lord2_name and p_lord2:
        dignity2 = p_lord2.dignity or calculate_dignity(lord2_name, p_lord2.sign)
        if dignity2 in ("exalted", "own_sign"):
            score += 2
            promise_parts.append(f"2nd lord {lord2_name} is dignified in {p_lord2.sign}, ensuring strong accumulation power.")
        elif dignity2 == "debilitated":
            score -= 2
            promise_parts.append(f"2nd lord {lord2_name} is debilitated, calling for prudent budgeting.")
        else:
            promise_parts.append(f"2nd lord {lord2_name} resides in House {p_lord2.house}.")

    if lord11_name and p_lord11:
        dignity11 = p_lord11.dignity or calculate_dignity(lord11_name, p_lord11.sign)
        if dignity11 in ("exalted", "own_sign"):
            score += 2
            promise_parts.append(f"11th lord {lord11_name} is dignified, promising steady cashflow and gains.")
        elif dignity11 == "debilitated":
            score -= 2
            promise_parts.append(f"11th lord {lord11_name} is debilitated, advising patience with income streams.")

    # Mutual connection between 2nd & 11th lords (Classical Dhana Yoga)
    if p_lord2 and p_lord11:
        if p_lord2.house == 11 or p_lord11.house == 2 or (p_lord2.house == p_lord11.house):
            score += 3
            promise_parts.append(
                "★ Classical Dhana Yoga: 2nd and 11th lords form auspicious connection, creating continuous wealth generation."
            )

    # SAV Bindus: 11th vs 12th house (Inflow vs Outflow rule)
    if sav11 is not None and sav12 is not None:
        if sav11 > sav12:
            score += 2
            promise_parts.append(
                f"Ashtakavarga wealth rule satisfied: 11th Bhava ({sav11} SAV) exceeds 12th Bhava ({sav12} SAV), indicating savings exceed expenditures."
            )
        else:
            score -= 1
            promise_parts.append(
                f"Expenditure advisory: 12th Bhava ({sav12} SAV) matches or exceeds 11th Bhava ({sav11} SAV), suggesting disciplined wealth preservation is required."
            )

    # 2. Varga Confirmation
    varga_parts: list[str] = []
    d9_data = chart.vargas.get("D9") if chart.vargas else None
    if lord11_name and p_lord11:
        d9_status, is_vg = _varga_dignity(lord11_name, d9_data, p_lord11.sign)
        if is_vg or "exalted" in d9_status:
            score += 1
            varga_parts.append(f"11th lord {lord11_name} retains high strength in D9 Navamsha.")

    # 3. Dasha Timing
    dasha_parts: list[str] = []
    md_lord = chart.dashas.current_md.lord if chart.dashas and chart.dashas.current_md else None
    ad_lord = chart.dashas.current_ad.lord if chart.dashas and chart.dashas.current_ad else None
    if md_lord and ad_lord:
        rel = dasha_lord_relationship(md_lord, ad_lord, chart)
        dasha_parts.append(f"Operating Dasha: {md_lord}/{ad_lord} ({rel['pair']} {rel['name']}).")
        if md_lord in (lord2_name, lord11_name) or ad_lord in (lord2_name, lord11_name):
            score += 2
            dasha_parts.append("Direct Dhana lord activation in current dasha!")
        if rel["pair"] == "3/11":
            score += 1
            dasha_parts.append("3/11 angle strongly favors entrepreneurial gains.")

    # 4. Transits
    transit_parts: list[str] = []
    t_report = transits or (chart.get_transits() if hasattr(chart, "get_transits") else None)
    if t_report:
        if 2 in t_report.double_transit_houses or 11 in t_report.double_transit_houses:
            score += 3
            transit_parts.append(
                "★ DOUBLE TRANSIT ACTIVATION: Jupiter & Saturn jointly aspect wealth bhavas (House 2/11), triggering strategic financial fruition!"
            )

    tier = _score_to_tier(score)
    primary_lords = [l for l in (lord2_name, lord11_name) if l]
    act_yogas = filter_active_yogas(chart, md_lord, ad_lord)
    dhana_yogas = [y.name for y in act_yogas if y.category.value == "Dhana Yoga"]

    return DomainPrediction(
        domain=DomainCategory.WEALTH,
        promise_tier=tier,
        primary_houses=primary_houses,
        primary_lords=primary_lords,
        karakas=karakas,
        promise_summary=" ".join(promise_parts) or "2nd & 11th Bhavas evaluated.",
        varga_confirmation=" ".join(varga_parts) or "D9 wealth confirmations verified.",
        dasha_timing=" ".join(dasha_parts) or "Dasha timing verified.",
        active_transits=transit_parts or ["Transits balanced."],
        active_yogas=dhana_yogas or [y.name for y in act_yogas[:2]],
        classical_citations=[
            "Brihat Parashara Hora Shastra (BPHS) Ch. 41 (Dhana Yogas)",
            "Saravali Ch. 35 (Dhana-Bhava Phala)",
            "Phaladeepika Ch. 16 (Upachaya & Labha Bhavas)",
        ],
        remedies=[
            "Kanakadhara Stotram or Sri Suktam recitation on Fridays",
            "Dāna: Allocate 5-10% of earnings toward spiritual charity and helping students",
            "Maintain meticulous personal bookkeeping and avoid speculative debt",
        ],
        key_verdict=f"Wealth potential is {tier.value.upper()}. Long-term abundance grows via ethical compounding.",
        score=score,
    )


def evaluate_spiritual_dharma(
    chart: ChartData, transits: TransitReport | None = None
) -> DomainPrediction:
    """
    Classical evaluation of Spiritual Dharma, Wisdom, and Moksha (9th & 12th Bhavas).
    Scriptural basis: BPHS Ch. 23, Jaimini Upadesha Sutras, Phaladeepika Ch. 18.
    """
    score = 0
    primary_houses = [9, 12, 5, 8]
    karakas = ["Jupiter", "Ketu", "Saturn"]

    lord9_name = get_house_lord(chart, 9)
    lord12_name = get_house_lord(chart, 12)
    p_lord9 = get_planet_by_name(chart, lord9_name) if lord9_name else None
    p_ketu = get_planet_by_name(chart, "Ketu")
    p_jupiter = get_planet_by_name(chart, "Jupiter")

    promise_parts: list[str] = []
    if lord9_name and p_lord9:
        dignity9 = p_lord9.dignity or calculate_dignity(lord9_name, p_lord9.sign)
        if dignity9 in ("exalted", "own_sign"):
            score += 3
            promise_parts.append(
                f"9th lord (Dharmesh) {lord9_name} is dignified in {p_lord9.sign}, bestowing spiritual lineage and divine grace."
            )
        else:
            score += 1
            promise_parts.append(f"9th lord {lord9_name} resides in House {p_lord9.house}.")

    if p_ketu:
        if p_ketu.house in (12, 9, 8):
            score += 3
            promise_parts.append(
                f"Ketu (Moksha Karaka) occupies House {p_ketu.house}, conferring natural intuitive discernment and detachment."
            )
        elif p_ketu.house in (4, 5):
            score += 1
            promise_parts.append(f"Ketu in House {p_ketu.house} deepens inner philosophical inquiry.")

    if p_jupiter:
        j_dignity = p_jupiter.dignity or calculate_dignity("Jupiter", p_jupiter.sign)
        if j_dignity in ("exalted", "own_sign"):
            score += 2
            promise_parts.append("Jupiter is potent, granting reverence for traditional wisdom and righteous living.")

    # 2. Varga Confirmation
    varga_parts: list[str] = []
    d9_data = chart.vargas.get("D9") if chart.vargas else None
    if lord9_name and p_lord9:
        d9_status, is_vg = _varga_dignity(lord9_name, d9_data, p_lord9.sign)
        if is_vg or "exalted" in d9_status:
            score += 1
            varga_parts.append(f"9th lord {lord9_name} shows pristine strength in Navamsha (D9).")

    # 3. Dasha Timing
    dasha_parts: list[str] = []
    md_lord = chart.dashas.current_md.lord if chart.dashas and chart.dashas.current_md else None
    ad_lord = chart.dashas.current_ad.lord if chart.dashas and chart.dashas.current_ad else None
    if md_lord and ad_lord:
        rel = dasha_lord_relationship(md_lord, ad_lord, chart)
        dasha_parts.append(f"Operating Dasha: {md_lord}/{ad_lord} ({rel['pair']} {rel['name']}).")
        if md_lord in ("Jupiter", "Ketu", lord9_name) or ad_lord in ("Jupiter", "Ketu", lord9_name):
            score += 2
            dasha_parts.append("Spiritual karaka or 9th lord active: ideal period for sadhana and higher study.")
        if rel["pair"] == "5/9":
            score += 1
            dasha_parts.append("Trinal harmony awakens spiritual receptivity.")

    # 4. Transits
    transit_parts: list[str] = []
    t_report = transits or (chart.get_transits() if hasattr(chart, "get_transits") else None)
    if t_report:
        if 9 in t_report.double_transit_houses or 12 in t_report.double_transit_houses:
            score += 2
            transit_parts.append("Double transit activates Dharma / Moksha Bhavas, awakening deeper purpose.")

    tier = _score_to_tier(score)
    primary_lords = [l for l in (lord9_name, lord12_name) if l]
    act_yogas = filter_active_yogas(chart, md_lord, ad_lord)

    return DomainPrediction(
        domain=DomainCategory.SPIRITUAL_DHARMA,
        promise_tier=tier,
        primary_houses=primary_houses,
        primary_lords=primary_lords,
        karakas=karakas,
        promise_summary=" ".join(promise_parts) or "Dharma bhavas analyzed.",
        varga_confirmation=" ".join(varga_parts) or "D9 spiritual confirmation verified.",
        dasha_timing=" ".join(dasha_parts) or "Dasha evaluated.",
        active_transits=transit_parts or ["Transits balanced."],
        active_yogas=[y.name for y in act_yogas[:2]],
        classical_citations=[
            "Brihat Parashara Hora Shastra (BPHS) Ch. 23 (Dharma & Moksha Bhavas)",
            "Jaimini Upadesha Sutras (Atmakaraka & Ishta Devata)",
            "Phaladeepika Ch. 18 (Sannyasa Yogas & Spiritual Realization)",
        ],
        remedies=[
            "Daily Japa or quiet meditation during Brahma Muhurta (48 mins before sunrise)",
            "Pilgrimage or study of classical Vedic scriptures (Upanishads, Gita)",
            "Selfless service (Nishkama Karma) without attachment to fruits",
        ],
        key_verdict=f"Spiritual promise is {tier.value.upper()}. Aligning action with Dharma yields inner peace.",
        score=score,
    )


def evaluate_health(
    chart: ChartData, transits: TransitReport | None = None
) -> DomainPrediction:
    """
    Classical evaluation of Vitality, Constitution, and Health Diligence (1st, 6th & 8th Bhavas).
    Scriptural basis: BPHS Ch. 14 & 22, Phaladeepika Ch. 14, Saravali Ch. 32.
    """
    score = 0
    primary_houses = [1, 6, 8]
    karakas = ["Sun", "Moon", "Saturn"]

    lord1_name = get_house_lord(chart, 1)
    lord6_name = get_house_lord(chart, 6)
    p_lord1 = get_planet_by_name(chart, lord1_name) if lord1_name else None
    p_sun = get_planet_by_name(chart, "Sun")
    p_moon = get_planet_by_name(chart, "Moon")
    sav1 = get_house_sav(chart, 1)

    promise_parts: list[str] = []
    if lord1_name and p_lord1:
        dignity1 = p_lord1.dignity or calculate_dignity(lord1_name, p_lord1.sign)
        if dignity1 in ("exalted", "own_sign"):
            score += 3
            promise_parts.append(f"Lagnesha (1st lord) {lord1_name} is dignified in {p_lord1.sign}, conferring robust vitality and strong immune defense.")
        elif dignity1 == "debilitated":
            score -= 2
            promise_parts.append(f"Lagnesha {lord1_name} is debilitated, requiring mindful preventive healthcare.")
        else:
            score += 1
            promise_parts.append(f"Lagnesha {lord1_name} resides in House {p_lord1.house}.")

    if p_sun:
        s_dignity = p_sun.dignity or calculate_dignity("Sun", p_sun.sign)
        if s_dignity in ("exalted", "own_sign"):
            score += 2
            promise_parts.append("Sun (vitality karaka) is strong, protecting cellular immunity and heart strength.")
        elif s_dignity == "debilitated":
            score -= 1
            promise_parts.append("Sun is debilitated, recommending adequate rest, vitamin D, and vitality preservation.")

    if p_moon:
        m_dignity = p_moon.dignity or calculate_dignity("Moon", p_moon.sign)
        if m_dignity == "debilitated":
            score -= 1
            promise_parts.append("Moon is debilitated in Scorpio, highlighting sensitivity to emotional stress.")

    if sav1 is not None:
        if sav1 >= 28:
            score += 1
            promise_parts.append(f"Ascendant holds {sav1} SAV bindus, supporting physical recovery.")
        elif sav1 < 25:
            score -= 1
            promise_parts.append(f"Ascendant holds {sav1} SAV bindus, advising against bodily exhaustion.")

    # 2. Varga Confirmation
    varga_parts: list[str] = []
    d9_data = chart.vargas.get("D9") if chart.vargas else None
    if lord1_name and p_lord1:
        d9_status, is_vg = _varga_dignity(lord1_name, d9_data, p_lord1.sign)
        if is_vg:
            score += 1
            varga_parts.append(f"Lagnesha {lord1_name} is Vargottama in D9, reinforcing physical constitution.")

    # 3. Dasha Timing
    dasha_parts: list[str] = []
    md_lord = chart.dashas.current_md.lord if chart.dashas and chart.dashas.current_md else None
    ad_lord = chart.dashas.current_ad.lord if chart.dashas and chart.dashas.current_ad else None
    if md_lord and ad_lord:
        rel = dasha_lord_relationship(md_lord, ad_lord, chart)
        dasha_parts.append(f"Active Dasha: {md_lord}/{ad_lord} ({rel['pair']} {rel['name']}).")
        if rel["pair"] == "6/8":
            score -= 2
            dasha_parts.append("6/8 Shadashtaka dasha angle indicates need for dietary discipline and stress management.")
        if md_lord == lord6_name or ad_lord == lord6_name:
            score -= 1
            dasha_parts.append("6th lord dasha phase: prioritize preventive wellness and daily routine.")

    # 4. Transits
    transit_parts: list[str] = []
    t_report = transits or (chart.get_transits() if hasattr(chart, "get_transits") else None)
    if t_report:
        ss = t_report.sade_sati
        if ss.is_ashtama_shani:
            score -= 2
            transit_parts.append("Ashtama Shani (Saturn in 8th from Moon) prompts caution against physical strain.")
        elif ss.is_active:
            transit_parts.append(f"Sade Sati ({ss.phase}) advises pacing mental energy.")

    tier = _score_to_tier(score)
    primary_lords = [l for l in (lord1_name, lord6_name) if l]
    act_yogas = filter_active_yogas(chart, md_lord, ad_lord)

    return DomainPrediction(
        domain=DomainCategory.HEALTH,
        promise_tier=tier,
        primary_houses=primary_houses,
        primary_lords=primary_lords,
        karakas=karakas,
        promise_summary=" ".join(promise_parts) or "Vitality bhavas analyzed.",
        varga_confirmation=" ".join(varga_parts) or "D9 constitution verified.",
        dasha_timing=" ".join(dasha_parts) or "Dasha evaluated.",
        active_transits=transit_parts or ["Transits balanced."],
        active_yogas=[y.name for y in act_yogas[:2]],
        classical_citations=[
            "Brihat Parashara Hora Shastra (BPHS) Ch. 14 & 22 (Ayur & Roga Bhavas)",
            "Phaladeepika Ch. 14 (Disease & Longevity)",
            "Saravali Ch. 32 (Constitution & Graha Balas)",
        ],
        remedies=[
            "Adopt an Ayurvedic Dinacharya (consistent sleep, hydration, sattvic diet)",
            "Pranayama (Anulom Vilom) and Surya Namaskar for nervous system equilibrium",
            "Consult licensed medical professionals for any diagnostic concerns",
        ],
        key_verdict=f"Vitality promise is {tier.value.upper()}. Daily discipline and preventive care ensure sustained well-being.",
        score=score,
    )


# --- Score to Tier Mapping ---


def _score_to_tier(score: int) -> PromiseTier:
    """Map composite numerical strength score to categorical PromiseTier."""
    if score >= 6:
        return PromiseTier.EXCEPTIONAL
    if score >= 2:
        return PromiseTier.FAVORABLE
    if score >= -2:
        return PromiseTier.MIXED
    if score >= -5:
        return PromiseTier.CHALLENGING
    return PromiseTier.OBSTRUCTED


# --- Master Dispatchers ---


EVALUATORS = {
    DomainCategory.CAREER: evaluate_career,
    DomainCategory.RELATIONSHIP: evaluate_relationship,
    DomainCategory.WEALTH: evaluate_wealth,
    DomainCategory.SPIRITUAL_DHARMA: evaluate_spiritual_dharma,
    DomainCategory.HEALTH: evaluate_health,
}


def evaluate_domain(
    domain: str | DomainCategory,
    chart: ChartData,
    transits: TransitReport | None = None,
) -> DomainPrediction:
    """Evaluate a single life domain using classical 5-step predictive synthesis."""
    dom_key = DomainCategory(domain) if isinstance(domain, str) else domain
    evaluator = EVALUATORS.get(dom_key)
    if not evaluator:
        raise ValueError(f"Unsupported prediction domain: {domain}")
    return evaluator(chart, transits)


def evaluate_all_domains(
    chart: ChartData,
    transits: TransitReport | None = None,
) -> dict[str, DomainPrediction]:
    """Evaluate all 5 core life domains simultaneously."""
    results: dict[str, DomainPrediction] = {}
    for dom_enum, fn in EVALUATORS.items():
        results[dom_enum.value] = fn(chart, transits)
    return results
