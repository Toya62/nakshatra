"""
Nakshatra Compatibility Engine
Production-grade Vedic marriage and relationship compatibility analysis.
Adapted from classical Jyotish canons (Brihat Parashara Hora Shastra,
Muhurtha Chintamani, Phaladeepika) and the VedAstro architectural model.

Features:
- Full 36-Point Ashtakoota matching:
    1. Varna (1 point): Spiritual and ego compatibility
    2. Vashya (2 points): Mutual attraction and power balance
    3. Tara / Dina (3 points): Destiny, health, and longevity
    4. Yoni (4 points): Sexual, biological, and physical intimacy
    5. Graha Maitri (5 points): Psychological, mental, and intellectual harmony
    6. Gana (6 points): Temperament and behavior alignment
    7. Bhakoot (7 points): Emotional growth, health, and family prosperity
    8. Nadi (8 points): Genetic, physiological, and nervous compatibility
- Classical dosha cancellation rules for Bhakoot and Nadi
- Extended classical Kutas (Mahendra, Stree Deergha, Rajju, Vedha)
- High-precision Kuja Dosha (Manglik) detection from Lagna, Moon, and Venus
  with classical cancellation overrides and couple-level neutralization
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from nakshatra.core import (
    SIGN_LORDS,
    ZODIAC_SIGNS,
    ChartData,
)

# ---------------------------------------------------------------------------
# Classical Reference Tables
# ---------------------------------------------------------------------------

# 27 Nakshatras in order
NAKSHATRA_NAMES = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

# Varna mapping by sign: Brahmin (4), Kshatriya (3), Vaishya (2), Shudra (1)
VARNA_BY_SIGN: dict[str, tuple[str, int]] = {
    "Cancer": ("Brahmin", 4),
    "Scorpio": ("Brahmin", 4),
    "Pisces": ("Brahmin", 4),
    "Aries": ("Kshatriya", 3),
    "Leo": ("Kshatriya", 3),
    "Sagittarius": ("Kshatriya", 3),
    "Taurus": ("Vaishya", 2),
    "Virgo": ("Vaishya", 2),
    "Capricorn": ("Vaishya", 2),
    "Gemini": ("Shudra", 1),
    "Libra": ("Shudra", 1),
    "Aquarius": ("Shudra", 1),
}

# Vashya classification by sign
VASHYA_CATEGORIES: dict[str, str] = {
    "Aries": "Chatushpada",
    "Taurus": "Chatushpada",
    "Gemini": "Manava",
    "Cancer": "Jalachara",
    "Leo": "Vanachara",
    "Virgo": "Manava",
    "Libra": "Manava",
    "Scorpio": "Keeta",
    "Sagittarius": "Manava",  # 1st half Manava, 2nd half Chatushpada; standard classification
    "Capricorn": "Jalachara",  # 1st half Chatushpada, 2nd half Jalachara
    "Aquarius": "Manava",
    "Pisces": "Jalachara",
}

# Direct Vashya attraction targets per sign (Rasi -> list of signs obedient to it)
VASHYA_TARGETS: dict[str, list[str]] = {
    "Aries": ["Leo", "Scorpio"],
    "Taurus": ["Cancer", "Libra"],
    "Gemini": ["Virgo"],
    "Cancer": ["Scorpio", "Sagittarius"],
    "Leo": ["Libra"],
    "Virgo": ["Pisces", "Gemini"],
    "Libra": ["Capricorn", "Virgo"],
    "Scorpio": ["Cancer"],
    "Sagittarius": ["Pisces"],
    "Capricorn": ["Aries", "Aquarius"],
    "Aquarius": ["Aries"],
    "Pisces": ["Capricorn"],
}

# 9 Taras (1-9)
TARA_NAMES = [
    "Janma",
    "Sampat",
    "Vipat",
    "Kshema",
    "Pratyak",
    "Sadhana",
    "Naidhana",
    "Mitra",
    "Parama Mitra",
]
AUSPICIOUS_TARAS = {1, 2, 4, 6, 8, 9}

# Yoni Animals and Gender per Nakshatra (0-26)
YONI_MAP: dict[str, tuple[str, str]] = {
    "Ashwini": ("Horse", "Male"),
    "Bharani": ("Elephant", "Male"),
    "Krittika": ("Sheep", "Female"),
    "Rohini": ("Serpent", "Male"),
    "Mrigashira": ("Serpent", "Female"),
    "Ardra": ("Dog", "Female"),
    "Punarvasu": ("Cat", "Female"),
    "Pushya": ("Sheep", "Male"),
    "Ashlesha": ("Cat", "Male"),
    "Magha": ("Rat", "Male"),
    "Purva Phalguni": ("Rat", "Female"),
    "Uttara Phalguni": ("Cow", "Male"),
    "Hasta": ("Buffalo", "Female"),
    "Chitra": ("Tiger", "Female"),
    "Swati": ("Buffalo", "Male"),
    "Vishakha": ("Tiger", "Male"),
    "Anuradha": ("Hare", "Female"),
    "Jyeshtha": ("Hare", "Male"),
    "Mula": ("Dog", "Male"),
    "Purva Ashadha": ("Monkey", "Male"),
    "Uttara Ashadha": ("Mongoose", "Male"),
    "Shravana": ("Monkey", "Female"),
    "Dhanishta": ("Lion", "Female"),
    "Shatabhisha": ("Horse", "Female"),
    "Purva Bhadrapada": ("Lion", "Male"),
    "Uttara Bhadrapada": ("Cow", "Female"),
    "Revati": ("Elephant", "Female"),
}

# Natural Swabhava Vaira (Deadly Enemy) animal pairs (0 points in Yoni)
DEADLY_ENEMY_YONIS: set[frozenset[str]] = {
    frozenset({"Cow", "Tiger"}),
    frozenset({"Elephant", "Lion"}),
    frozenset({"Horse", "Buffalo"}),
    frozenset({"Dog", "Hare"}),
    frozenset({"Serpent", "Mongoose"}),
    frozenset({"Monkey", "Sheep"}),
    frozenset({"Cat", "Rat"}),
}

# Planetary Friendship (Naisargika Sambandha)
# Planet -> (Friends, Neutrals, Enemies)
NATURAL_FRIENDSHIP: dict[str, tuple[set[str], set[str], set[str]]] = {
    "Sun": ({"Moon", "Mars", "Jupiter"}, {"Mercury"}, {"Venus", "Saturn"}),
    "Moon": ({"Sun", "Mercury"}, {"Mars", "Jupiter", "Venus", "Saturn"}, set()),
    "Mars": ({"Sun", "Moon", "Jupiter"}, {"Venus", "Saturn"}, {"Mercury"}),
    "Mercury": ({"Sun", "Venus"}, {"Mars", "Jupiter", "Saturn"}, {"Moon"}),
    "Jupiter": ({"Sun", "Moon", "Mars"}, {"Saturn"}, {"Mercury", "Venus"}),
    "Venus": ({"Mercury", "Saturn"}, {"Mars", "Jupiter"}, {"Sun", "Moon"}),
    "Saturn": ({"Mercury", "Venus"}, {"Jupiter"}, {"Sun", "Moon", "Mars"}),
}

# Gana classification
GANA_MAP: dict[str, str] = {
    "Ashwini": "Deva",
    "Bharani": "Manushya",
    "Krittika": "Rakshasa",
    "Rohini": "Manushya",
    "Mrigashira": "Deva",
    "Ardra": "Manushya",
    "Punarvasu": "Deva",
    "Pushya": "Deva",
    "Ashlesha": "Rakshasa",
    "Magha": "Rakshasa",
    "Purva Phalguni": "Manushya",
    "Uttara Phalguni": "Manushya",
    "Hasta": "Deva",
    "Chitra": "Rakshasa",
    "Swati": "Deva",
    "Vishakha": "Rakshasa",
    "Anuradha": "Deva",
    "Jyeshtha": "Rakshasa",
    "Mula": "Rakshasa",
    "Purva Ashadha": "Manushya",
    "Uttara Ashadha": "Manushya",
    "Shravana": "Deva",
    "Dhanishta": "Rakshasa",
    "Shatabhisha": "Rakshasa",
    "Purva Bhadrapada": "Manushya",
    "Uttara Bhadrapada": "Manushya",
    "Revati": "Deva",
}

# Nadi classification
NADI_MAP: dict[str, str] = {
    "Ashwini": "Adi",
    "Bharani": "Madhya",
    "Krittika": "Antya",
    "Rohini": "Antya",
    "Mrigashira": "Madhya",
    "Ardra": "Adi",
    "Punarvasu": "Adi",
    "Pushya": "Madhya",
    "Ashlesha": "Antya",
    "Magha": "Antya",
    "Purva Phalguni": "Madhya",
    "Uttara Phalguni": "Adi",
    "Hasta": "Adi",
    "Chitra": "Madhya",
    "Swati": "Antya",
    "Vishakha": "Antya",
    "Anuradha": "Madhya",
    "Jyeshtha": "Adi",
    "Mula": "Adi",
    "Purva Ashadha": "Madhya",
    "Uttara Ashadha": "Antya",
    "Shravana": "Antya",
    "Dhanishta": "Madhya",
    "Shatabhisha": "Adi",
    "Purva Bhadrapada": "Adi",
    "Uttara Bhadrapada": "Madhya",
    "Revati": "Antya",
}

# Rajju grouping by anatomical level
RAJJU_MAP: dict[str, str] = {
    # Shira (Head)
    "Chitra": "Shira",
    "Mrigashira": "Shira",
    "Dhanishta": "Shira",
    # Kantha (Neck)
    "Rohini": "Kantha",
    "Ardra": "Kantha",
    "Hasta": "Kantha",
    "Swati": "Kantha",
    "Shravana": "Kantha",
    "Shatabhisha": "Kantha",
    # Nabhi (Navel)
    "Krittika": "Nabhi",
    "Punarvasu": "Nabhi",
    "Uttara Phalguni": "Nabhi",
    "Vishakha": "Nabhi",
    "Uttara Ashadha": "Nabhi",
    "Purva Bhadrapada": "Nabhi",
    # Kati (Waist)
    "Bharani": "Kati",
    "Pushya": "Kati",
    "Purva Phalguni": "Kati",
    "Anuradha": "Kati",
    "Purva Ashadha": "Kati",
    "Uttara Bhadrapada": "Kati",
    # Pada (Feet)
    "Ashwini": "Pada",
    "Ashlesha": "Pada",
    "Magha": "Pada",
    "Jyeshtha": "Pada",
    "Mula": "Pada",
    "Revati": "Pada",
}

# Vedha (Mutual Piercing Affliction) nakshatra pairs
VEDHA_PAIRS: set[frozenset[str]] = {
    frozenset({"Ashwini", "Jyeshtha"}),
    frozenset({"Bharani", "Anuradha"}),
    frozenset({"Krittika", "Vishakha"}),
    frozenset({"Rohini", "Swati"}),
    frozenset({"Ardra", "Shravana"}),
    frozenset({"Punarvasu", "Uttara Ashadha"}),
    frozenset({"Pushya", "Purva Ashadha"}),
    frozenset({"Ashlesha", "Mula"}),
    frozenset({"Magha", "Revati"}),
    frozenset({"Purva Phalguni", "Uttara Bhadrapada"}),
    frozenset({"Uttara Phalguni", "Purva Bhadrapada"}),
    frozenset({"Hasta", "Shatabhisha"}),
    frozenset({"Mrigashira", "Dhanishta"}),
}


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class KutaScore(BaseModel):
    """Evaluation of an individual Koota factor."""

    name: str
    max_score: float
    obtained_score: float
    bride_val: str
    groom_val: str
    is_favorable: bool
    dosha_present: bool = False
    cancelled: bool = False
    notes: str = ""


class AshtakootaReport(BaseModel):
    """Complete 36-point Ashtakoota evaluation."""

    varna: KutaScore
    vashya: KutaScore
    tara: KutaScore
    yoni: KutaScore
    graha_maitri: KutaScore
    gana: KutaScore
    bhakoot: KutaScore
    nadi: KutaScore
    total_score: float
    percentage: float
    verdict: str = Field(
        ..., description="'Uttama' (>=28), 'Madhyama' (18-27.5), or 'Adhama' (<18)"
    )
    summary: str


class ExtendedKutasReport(BaseModel):
    """Extended classical Kootas from VedAstro / South Indian canons."""

    mahendra: KutaScore
    stree_deergha: KutaScore
    rajju: KutaScore
    vedha: KutaScore


class KujaDoshaDetails(BaseModel):
    """Manglik / Kuja Dosha profile for a single partner."""

    is_manglik: bool
    severity: str = Field(..., description="'None', 'Low', 'Moderate', or 'High'")
    score: float
    afflicted_houses_lagna: list[int]
    afflicted_houses_moon: list[int]
    afflicted_houses_venus: list[int]
    cancellations: list[str]
    is_cancelled: bool


class KujaDoshaReport(BaseModel):
    """Pair Kuja Dosha analysis."""

    bride: KujaDoshaDetails
    groom: KujaDoshaDetails
    is_compatible: bool
    verdict: str
    notes: str


class CompatibilityReport(BaseModel):
    """Comprehensive Relationship Compatibility Report."""

    bride_name: str | None = None
    groom_name: str | None = None
    bride_moon_sign: str
    bride_nakshatra: str
    bride_pada: int
    groom_moon_sign: str
    groom_nakshatra: str
    groom_pada: int
    ashtakoota: AshtakootaReport
    extended_kutas: ExtendedKutasReport
    kuja_dosha: KujaDoshaReport
    overall_score: float
    recommendation: str

    def to_table(self) -> str:
        """Format the report as an ASCII table."""
        lines = []
        lines.append("=" * 80)
        lines.append("                VEDIC ASHTAKOOTA COMPATIBILITY REPORT")
        lines.append("=" * 80)
        lines.append(
            f" Bride : {self.bride_moon_sign} | {self.bride_nakshatra} (Pada {self.bride_pada})"
        )
        lines.append(
            f" Groom : {self.groom_moon_sign} | {self.groom_nakshatra} (Pada {self.groom_pada})"
        )
        lines.append("-" * 80)
        lines.append(
            f"{'KOOTA':<16} | {'MAX':<4} | {'PTS':<4} | {'BRIDE':<16} | {'GROOM':<16} | STATUS"
        )
        lines.append("-" * 80)
        for kuta in [
            self.ashtakoota.varna,
            self.ashtakoota.vashya,
            self.ashtakoota.tara,
            self.ashtakoota.yoni,
            self.ashtakoota.graha_maitri,
            self.ashtakoota.gana,
            self.ashtakoota.bhakoot,
            self.ashtakoota.nadi,
        ]:
            flag = "PASS" if kuta.is_favorable else ("CANC" if kuta.cancelled else "FAIL")
            lines.append(
                f"{kuta.name:<16} | {kuta.max_score:>4.1f} | {kuta.obtained_score:>4.1f} | "
                f"{kuta.bride_val:<16} | {kuta.groom_val:<16} | {flag}"
            )
        lines.append("-" * 80)
        lines.append(
            f" TOTAL ASHTAKOOTA: {self.ashtakoota.total_score:.1f} / 36.0 "
            f"({self.ashtakoota.percentage:.1f}%) -> {self.ashtakoota.verdict}"
        )
        lines.append("=" * 80)
        lines.append(" EXTENDED KUTAS:")
        lines.append(f"  - Mahendra      : {self.extended_kutas.mahendra.notes}")
        lines.append(f"  - Stree Deergha : {self.extended_kutas.stree_deergha.notes}")
        lines.append(f"  - Rajju         : {self.extended_kutas.rajju.notes}")
        lines.append(f"  - Vedha         : {self.extended_kutas.vedha.notes}")
        lines.append("-" * 80)
        lines.append(f" KUJA DOSHA (MANGLIK): {self.kuja_dosha.verdict}")
        lines.append(
            f"  Bride: {self.kuja_dosha.bride.severity} (Cancelled: {self.kuja_dosha.bride.is_cancelled})"
        )
        lines.append(
            f"  Groom: {self.kuja_dosha.groom.severity} (Cancelled: {self.kuja_dosha.groom.is_cancelled})"
        )
        lines.append(
            f"  Pair Status: {'COMPATIBLE' if self.kuja_dosha.is_compatible else 'AFFLICTED'}"
        )
        lines.append("=" * 80)
        lines.append(f" FINAL RECOMMENDATION: {self.recommendation}")
        lines.append("=" * 80)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Individual Koota Calculation Functions
# ---------------------------------------------------------------------------


def calculate_varna(bride_sign: str, groom_sign: str) -> KutaScore:
    """1. Varna Koota (1 point): Spiritual hierarchy and spiritual compatibility."""
    b_name, b_grade = VARNA_BY_SIGN[bride_sign]
    g_name, g_grade = VARNA_BY_SIGN[groom_sign]
    score = 1.0 if g_grade >= b_grade else 0.0
    return KutaScore(
        name="Varna",
        max_score=1.0,
        obtained_score=score,
        bride_val=b_name,
        groom_val=g_name,
        is_favorable=(score == 1.0),
        notes="Groom varna equal or higher than bride"
        if score == 1.0
        else "Groom varna lower than bride",
    )


def calculate_vashya(bride_sign: str, groom_sign: str) -> KutaScore:
    """2. Vashya Koota (2 points): Mutual magnetic attraction and control."""
    b_cat = VASHYA_CATEGORIES[bride_sign]
    g_cat = VASHYA_CATEGORIES[groom_sign]

    if bride_sign == groom_sign or b_cat == g_cat:
        score = 2.0
        note = "Identical sign or vashya archetype"
    elif groom_sign in VASHYA_TARGETS.get(bride_sign, []) and bride_sign in VASHYA_TARGETS.get(
        groom_sign, []
    ):
        score = 2.0
        note = "Mutual direct attraction"
    elif groom_sign in VASHYA_TARGETS.get(bride_sign, []) or bride_sign in VASHYA_TARGETS.get(
        groom_sign, []
    ):
        score = 1.0
        note = "One-way vashya attraction"
    elif (b_cat == "Vanachara" and g_cat in ("Chatushpada", "Manava")) or (
        g_cat == "Vanachara" and b_cat in ("Chatushpada", "Manava")
    ):
        score = 0.0
        note = "Bhakshya-Bhakshaka (predator vs prey) discord"
    else:
        score = 0.5
        note = "Neutral vashya affinity"

    return KutaScore(
        name="Vashya",
        max_score=2.0,
        obtained_score=score,
        bride_val=b_cat,
        groom_val=g_cat,
        is_favorable=(score >= 1.0),
        notes=note,
    )


def calculate_tara(bride_nak_idx: int, groom_nak_idx: int) -> KutaScore:
    """3. Tara / Dina Koota (3 points): Destiny, health, and longevity from 27 Nakshatras."""
    d_b_to_g = ((groom_nak_idx - bride_nak_idx) % 27) + 1
    t1 = d_b_to_g % 9
    if t1 == 0:
        t1 = 9

    d_g_to_b = ((bride_nak_idx - groom_nak_idx) % 27) + 1
    t2 = d_g_to_b % 9
    if t2 == 0:
        t2 = 9

    t1_auspicious = t1 in AUSPICIOUS_TARAS
    t2_auspicious = t2 in AUSPICIOUS_TARAS

    if t1_auspicious and t2_auspicious:
        score = 3.0
    elif t1_auspicious or t2_auspicious:
        score = 1.5
    else:
        score = 0.0

    b_tara_name = TARA_NAMES[t1 - 1]
    g_tara_name = TARA_NAMES[t2 - 1]
    return KutaScore(
        name="Tara",
        max_score=3.0,
        obtained_score=score,
        bride_val=f"{b_tara_name} ({t1})",
        groom_val=f"{g_tara_name} ({t2})",
        is_favorable=(score >= 1.5),
        notes="Both Taras auspicious"
        if score == 3.0
        else ("One Tara auspicious" if score == 1.5 else "Both Taras afflicted"),
    )


def calculate_yoni(bride_nak: str, groom_nak: str) -> KutaScore:
    """4. Yoni Koota (4 points): Sexual and biological intimacy compatibility."""
    b_animal, b_gender = YONI_MAP[bride_nak]
    g_animal, g_gender = YONI_MAP[groom_nak]

    pair = frozenset({b_animal, g_animal})
    if b_animal == g_animal:
        score = 4.0
        note = f"Swavarga ({b_animal}) - perfect biological harmony"
    elif pair in DEADLY_ENEMY_YONIS:
        score = 0.0
        note = f"Swabhava Vaira ({b_animal} vs {g_animal}) - deadly enemy pair"
    else:
        # Classical friendship vs neutral matrix
        # For standard non-enemy, non-identical animals: 2 points for neutral, 3 for friendly, 1 for unfriendly
        # We classify gender complement (male+female gives slight boost)
        score = 2.0
        if b_gender != g_gender:
            score = 3.0
            note = f"Complementary genders ({b_animal} & {g_animal})"
        else:
            note = f"Neutral animal union ({b_animal} & {g_animal})"

    return KutaScore(
        name="Yoni",
        max_score=4.0,
        obtained_score=score,
        bride_val=f"{b_animal} ({b_gender})",
        groom_val=f"{g_animal} ({g_gender})",
        is_favorable=(score >= 2.0),
        dosha_present=(score == 0.0),
        notes=note,
    )


def calculate_graha_maitri(bride_sign: str, groom_sign: str) -> KutaScore:
    """5. Graha Maitri Koota (5 points): Mental and psychological harmony."""
    b_lord = SIGN_LORDS[bride_sign]
    g_lord = SIGN_LORDS[groom_sign]

    if b_lord == g_lord:
        score = 5.0
        note = f"Identical sign lord ({b_lord})"
    else:
        b_friends, b_neutrals, b_enemies = NATURAL_FRIENDSHIP[b_lord]
        g_friends, g_neutrals, g_enemies = NATURAL_FRIENDSHIP[g_lord]

        b_rel_to_g = (
            "friend" if g_lord in b_friends else ("neutral" if g_lord in b_neutrals else "enemy")
        )
        g_rel_to_b = (
            "friend" if b_lord in g_friends else ("neutral" if b_lord in g_neutrals else "enemy")
        )

        if b_rel_to_g == "friend" and g_rel_to_b == "friend":
            score = 5.0
            note = f"Mutual friends ({b_lord} & {g_lord})"
        elif (b_rel_to_g == "friend" and g_rel_to_b == "neutral") or (
            b_rel_to_g == "neutral" and g_rel_to_b == "friend"
        ):
            score = 4.0
            note = f"One friend, one neutral ({b_lord} & {g_lord})"
        elif b_rel_to_g == "neutral" and g_rel_to_b == "neutral":
            score = 3.0
            note = f"Mutual neutrals ({b_lord} & {g_lord})"
        elif (b_rel_to_g == "friend" and g_rel_to_b == "enemy") or (
            b_rel_to_g == "enemy" and g_rel_to_b == "friend"
        ):
            score = 1.0
            note = f"One friend, one enemy ({b_lord} & {g_lord})"
        elif (b_rel_to_g == "neutral" and g_rel_to_b == "enemy") or (
            b_rel_to_g == "enemy" and g_rel_to_b == "neutral"
        ):
            score = 0.5
            note = f"One neutral, one enemy ({b_lord} & {g_lord})"
        else:
            score = 0.0
            note = f"Mutual enemies ({b_lord} & {g_lord})"

    return KutaScore(
        name="Graha Maitri",
        max_score=5.0,
        obtained_score=score,
        bride_val=f"{bride_sign} ({b_lord})",
        groom_val=f"{groom_sign} ({g_lord})",
        is_favorable=(score >= 3.0),
        notes=note,
    )


def calculate_gana(bride_nak: str, groom_nak: str) -> KutaScore:
    """6. Gana Koota (6 points): Temperament and behavior alignment."""
    b_gana = GANA_MAP[bride_nak]
    g_gana = GANA_MAP[groom_nak]

    dosha = False
    if b_gana == g_gana:
        score = 6.0
        note = f"Same temperament ({b_gana})"
    elif g_gana == "Deva" and b_gana == "Manushya":
        score = 6.0
        note = "Deva groom & Manushya bride (Harmonious)"
    elif g_gana == "Manushya" and b_gana == "Deva":
        score = 5.0
        note = "Manushya groom & Deva bride (Good)"
    elif g_gana == "Rakshasa" and b_gana == "Deva":
        score = 1.0
        note = "Rakshasa groom & Deva bride (Tense)"
    elif g_gana == "Deva" and b_gana == "Rakshasa":
        score = 0.0
        dosha = True
        note = "Deva groom & Rakshasa bride (Gana Dosha)"
    elif g_gana == "Manushya" and b_gana == "Rakshasa":
        score = 0.0
        dosha = True
        note = "Manushya groom & Rakshasa bride (Gana Dosha)"
    elif g_gana == "Rakshasa" and b_gana == "Manushya":
        score = 0.0
        dosha = True
        note = "Rakshasa groom & Manushya bride (Gana Dosha)"
    else:
        score = 0.0
        dosha = True
        note = "Incompatible Ganas"

    return KutaScore(
        name="Gana",
        max_score=6.0,
        obtained_score=score,
        bride_val=b_gana,
        groom_val=g_gana,
        is_favorable=(score >= 5.0),
        dosha_present=dosha,
        notes=note,
    )


def calculate_bhakoot(bride_sign: str, groom_sign: str) -> KutaScore:
    """7. Bhakoot Koota (7 points): Health, prosperity, and emotional harmony."""
    b_idx = ZODIAC_SIGNS.index(bride_sign)
    g_idx = ZODIAC_SIGNS.index(groom_sign)

    diff = ((g_idx - b_idx) % 12) + 1  # 1 to 12
    # Favorable distances: 1/1, 1/7, 3/11, 4/10
    # Unfavorable distances: 2/12 (Dvidvadasha), 6/8 (Sashtashtaka), 5/9 (Navapanchama)
    unfavorable_pairs = {2, 12, 6, 8, 5, 9}

    b_lord = SIGN_LORDS[bride_sign]
    g_lord = SIGN_LORDS[groom_sign]

    # Cancellation conditions:
    # 1. Same sign lord (Aries/Scorpio = Mars, Taurus/Libra = Venus)
    # 2. Lords are mutual friends (Cancer/Pisces = Moon/Jupiter, Leo/Sagittarius = Sun/Jupiter)
    # 3. Both in same sign
    b_friends, _, _ = NATURAL_FRIENDSHIP[b_lord]
    g_friends, _, _ = NATURAL_FRIENDSHIP[g_lord]
    mutual_friends = (g_lord in b_friends) and (b_lord in g_friends)
    cancelled = False
    cancellation_reason = ""

    if diff not in unfavorable_pairs:
        score = 7.0
        is_favorable = True
        note = f"Auspicious mutual distance ({diff}/{(14 - diff) % 12 or 12})"
    else:
        if b_lord == g_lord:
            score = 7.0
            is_favorable = True
            cancelled = True
            cancellation_reason = f"Bhakoot Dosha cancelled: Identical sign lord ({b_lord})"
            note = cancellation_reason
        elif mutual_friends:
            score = 7.0
            is_favorable = True
            cancelled = True
            cancellation_reason = (
                f"Bhakoot Dosha cancelled: Sign lords are mutual friends ({b_lord} & {g_lord})"
            )
            note = cancellation_reason
        else:
            score = 0.0
            is_favorable = False
            dosha_name = (
                "Sashtashtaka (6/8)"
                if diff in (6, 8)
                else ("Dvidvadasha (2/12)" if diff in (2, 12) else "Navapanchama (5/9)")
            )
            note = f"Bhakoot Dosha present: {dosha_name}"

    return KutaScore(
        name="Bhakoot",
        max_score=7.0,
        obtained_score=score,
        bride_val=bride_sign,
        groom_val=groom_sign,
        is_favorable=is_favorable,
        dosha_present=(score == 0.0),
        cancelled=cancelled,
        notes=note,
    )


def calculate_nadi(
    bride_nak: str,
    groom_nak: str,
    bride_pada: int = 1,
    groom_pada: int = 1,
    bride_sign: str = "",
    groom_sign: str = "",
) -> KutaScore:
    """8. Nadi Koota (8 points): Genetic and physiological compatibility."""
    b_nadi = NADI_MAP[bride_nak]
    g_nadi = NADI_MAP[groom_nak]

    if b_nadi != g_nadi:
        return KutaScore(
            name="Nadi",
            max_score=8.0,
            obtained_score=8.0,
            bride_val=b_nadi,
            groom_val=g_nadi,
            is_favorable=True,
            notes=f"Different Nadis ({b_nadi} vs {g_nadi}) - Auspicious",
        )

    # Nadi Dosha is present unless classical cancellations apply
    # Classical Cancellations:
    # 1. Same Nakshatra, different Pada
    # 2. Same Rasi, different Nakshatra
    # 3. Same Nakshatra spanning across two Rasis
    # 4. Canonical exemption Nakshatras: Rohini, Mrigashira, Ardra, Jyeshtha,
    #    Uttara Ashadha, Shravana, Uttara Bhadrapada, Revati
    exempt_nakshatras = {
        "Rohini",
        "Mrigashira",
        "Ardra",
        "Jyeshtha",
        "Uttara Ashadha",
        "Shravana",
        "Uttara Bhadrapada",
        "Revati",
    }

    cancelled = False
    reason = ""

    if bride_nak == groom_nak and bride_pada != groom_pada:
        cancelled = True
        reason = f"Cancelled: Same nakshatra ({bride_nak}) but different Padas ({bride_pada} vs {groom_pada})"
    elif bride_sign and groom_sign and bride_sign == groom_sign and bride_nak != groom_nak:
        cancelled = True
        reason = f"Cancelled: Same Rasi ({bride_sign}) with different nakshatras"
    elif bride_nak in exempt_nakshatras:
        cancelled = True
        reason = f"Cancelled: Classical Nakshatra exemption for {bride_nak}"

    score = 8.0 if cancelled else 0.0
    return KutaScore(
        name="Nadi",
        max_score=8.0,
        obtained_score=score,
        bride_val=b_nadi,
        groom_val=g_nadi,
        is_favorable=(score == 8.0),
        dosha_present=(not cancelled),
        cancelled=cancelled,
        notes=reason if cancelled else f"Nadi Dosha present ({b_nadi} Nadi union)",
    )


# ---------------------------------------------------------------------------
# Extended Classical Kutas (16 Kutas Subsets)
# ---------------------------------------------------------------------------


def calculate_extended_kutas(
    bride_nak: str,
    groom_nak: str,
    bride_nak_idx: int,
    groom_nak_idx: int,
) -> ExtendedKutasReport:
    """Evaluate Mahendra, Stree Deergha, Rajju, and Vedha."""
    # 1. Mahendra Kuta: Distance from bride to groom in {4, 7, 10, 13, 16, 19, 22, 25}
    d_b_to_g = ((groom_nak_idx - bride_nak_idx) % 27) + 1
    mahendra_favorable = d_b_to_g in {4, 7, 10, 13, 16, 19, 22, 25}
    mahendra_kuta = KutaScore(
        name="Mahendra",
        max_score=1.0,
        obtained_score=1.0 if mahendra_favorable else 0.0,
        bride_val=str(bride_nak_idx),
        groom_val=str(groom_nak_idx),
        is_favorable=mahendra_favorable,
        notes="Favorable for progeny, attachment, and lineage"
        if mahendra_favorable
        else "Neutral / Average",
    )

    # 2. Stree Deergha: Groom nakshatra > 13 away from bride
    stree_deergha_favorable = d_b_to_g >= 13
    stree_deergha_kuta = KutaScore(
        name="Stree Deergha",
        max_score=1.0,
        obtained_score=1.0 if stree_deergha_favorable else 0.0,
        bride_val=str(bride_nak_idx),
        groom_val=str(groom_nak_idx),
        is_favorable=stree_deergha_favorable,
        notes=f"Distance {d_b_to_g} nakshatras (>=13 auspicious for long life and wealth)"
        if stree_deergha_favorable
        else f"Distance {d_b_to_g} nakshatras (<13)",
    )

    # 3. Rajju: Affliction if in same anatomical level
    b_rajju = RAJJU_MAP.get(bride_nak, "Unknown")
    g_rajju = RAJJU_MAP.get(groom_nak, "Unknown")
    rajju_dosha = b_rajju == g_rajju
    rajju_kuta = KutaScore(
        name="Rajju",
        max_score=1.0,
        obtained_score=0.0 if rajju_dosha else 1.0,
        bride_val=b_rajju,
        groom_val=g_rajju,
        is_favorable=(not rajju_dosha),
        dosha_present=rajju_dosha,
        notes=f"Rajju Dosha: Same limb ({b_rajju} Rajju)"
        if rajju_dosha
        else f"Auspicious: Different Rajjus ({b_rajju} vs {g_rajju})",
    )

    # 4. Vedha: Mutual piercing affliction
    is_vedha = frozenset({bride_nak, groom_nak}) in VEDHA_PAIRS
    vedha_kuta = KutaScore(
        name="Vedha",
        max_score=1.0,
        obtained_score=0.0 if is_vedha else 1.0,
        bride_val=bride_nak,
        groom_val=groom_nak,
        is_favorable=(not is_vedha),
        dosha_present=is_vedha,
        notes=f"Vedha Dosha present ({bride_nak} piercings {groom_nak})"
        if is_vedha
        else "No Vedha affliction",
    )

    return ExtendedKutasReport(
        mahendra=mahendra_kuta,
        stree_deergha=stree_deergha_kuta,
        rajju=rajju_kuta,
        vedha=vedha_kuta,
    )


# ---------------------------------------------------------------------------
# Kuja Dosha (Manglik) Engine
# ---------------------------------------------------------------------------

MANGLIK_HOUSES = {1, 2, 4, 7, 8, 12}


def evaluate_chart_kuja_dosha(chart: ChartData) -> KujaDoshaDetails:
    """
    Evaluate Kuja Dosha (Manglik) for a single chart from:
    - Lagna (Ascendant): weight 1.0
    - Moon: weight 0.5
    - Venus: weight 0.25
    """
    planets_by_name = {p.name: p for p in chart.planets}
    mars = planets_by_name.get("Mars")
    moon = planets_by_name.get("Moon")
    venus = planets_by_name.get("Venus")
    jupiter = planets_by_name.get("Jupiter")

    if not mars or not chart.ascendant:
        return KujaDoshaDetails(
            is_manglik=False,
            severity="None",
            score=0.0,
            afflicted_houses_lagna=[],
            afflicted_houses_moon=[],
            afflicted_houses_venus=[],
            cancellations=[],
            is_cancelled=False,
        )

    asc_idx = ZODIAC_SIGNS.index(chart.ascendant.sign)
    mars_idx = ZODIAC_SIGNS.index(mars.sign)
    moon_idx = ZODIAC_SIGNS.index(moon.sign) if moon else mars_idx
    venus_idx = ZODIAC_SIGNS.index(venus.sign) if venus else mars_idx

    h_lagna = ((mars_idx - asc_idx) % 12) + 1
    h_moon = ((mars_idx - moon_idx) % 12) + 1
    h_venus = ((mars_idx - venus_idx) % 12) + 1

    aff_lagna = [h_lagna] if h_lagna in MANGLIK_HOUSES else []
    aff_moon = [h_moon] if h_moon in MANGLIK_HOUSES else []
    aff_venus = [h_venus] if h_venus in MANGLIK_HOUSES else []

    is_manglik = bool(aff_lagna or aff_moon or aff_venus)
    raw_score = (
        (1.0 if aff_lagna else 0.0) + (0.5 if aff_moon else 0.0) + (0.25 if aff_venus else 0.0)
    )

    # Classical cancellations
    cancellations: list[str] = []
    # 1. Mars in Aries, Scorpio, Capricorn, or Cancer
    if mars.sign in ("Aries", "Scorpio"):
        cancellations.append(f"Mars in own sign ({mars.sign})")
    elif mars.sign == "Capricorn":
        cancellations.append("Mars exalted in Capricorn")
    elif mars.sign == "Cancer":
        cancellations.append("Mars debilitated in Cancer (dosha attenuated)")
    elif mars.sign in ("Leo", "Aquarius"):
        cancellations.append(f"Mars in friendly sign {mars.sign}")

    # 2. Conjunction with Jupiter or Moon
    if jupiter and jupiter.sign == mars.sign:
        cancellations.append("Guru-Mangala Yoga (Mars conjunct Jupiter)")
    if moon and moon.sign == mars.sign:
        cancellations.append("Chandra-Mangala Yoga (Mars conjunct Moon)")

    # 3. Benefic aspect from Jupiter
    if jupiter:
        jup_idx = ZODIAC_SIGNS.index(jupiter.sign)
        jup_to_mars = ((mars_idx - jup_idx) % 12) + 1
        if jup_to_mars in (5, 7, 9):
            cancellations.append(f"Mars aspected by benefic Jupiter ({jup_to_mars}th aspect)")

    is_cancelled = bool(cancellations) and is_manglik

    if not is_manglik:
        severity = "None"
    elif is_cancelled:
        severity = "Low"
    elif raw_score >= 1.5:
        severity = "High"
    elif raw_score >= 1.0:
        severity = "Moderate"
    else:
        severity = "Low"

    return KujaDoshaDetails(
        is_manglik=is_manglik,
        severity=severity,
        score=raw_score,
        afflicted_houses_lagna=aff_lagna,
        afflicted_houses_moon=aff_moon,
        afflicted_houses_venus=aff_venus,
        cancellations=cancellations,
        is_cancelled=is_cancelled,
    )


def evaluate_pair_kuja_dosha(bride_chart: ChartData, groom_chart: ChartData) -> KujaDoshaReport:
    """Pair Kuja Dosha comparison with neutralization rules."""
    b_dosha = evaluate_chart_kuja_dosha(bride_chart)
    g_dosha = evaluate_chart_kuja_dosha(groom_chart)

    # Neutralization: If both partners are Manglik, the doshas neutralize each other!
    if b_dosha.is_manglik and g_dosha.is_manglik:
        is_compatible = True
        verdict = "Neutralized (Both partners have Kuja Dosha)"
        notes = "Classical cancellation: Kuja Dosha in both horoscopes cancels marital affliction."
    elif not b_dosha.is_manglik and not g_dosha.is_manglik:
        is_compatible = True
        verdict = "Clear (Neither partner has Kuja Dosha)"
        notes = "Both horoscopes free of Manglik affliction."
    elif b_dosha.is_cancelled or g_dosha.is_cancelled:
        is_compatible = True
        verdict = "Mild (Affliction cancelled by auspicious configurations)"
        notes = "One partner has Kuja Dosha, but classical astrological cancellations apply."
    else:
        is_compatible = False
        afflicted = "Bride" if b_dosha.is_manglik else "Groom"
        verdict = f"Afflicted ({afflicted} has uncancelled Kuja Dosha)"
        notes = f"{afflicted} is Manglik while partner is non-Manglik. Astrological remedies (Upayas) recommended."

    return KujaDoshaReport(
        bride=b_dosha,
        groom=g_dosha,
        is_compatible=is_compatible,
        verdict=verdict,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Master Compatibility Calculation
# ---------------------------------------------------------------------------


def calculate_compatibility(
    bride_chart: ChartData,
    groom_chart: ChartData,
    bride_name: str | None = None,
    groom_name: str | None = None,
) -> CompatibilityReport:
    """
    Calculate full relationship compatibility report between bride and groom charts.
    """
    bride_planets = {p.name: p for p in bride_chart.planets}
    groom_planets = {p.name: p for p in groom_chart.planets}

    b_moon = bride_planets["Moon"]
    g_moon = groom_planets["Moon"]

    b_sign = b_moon.sign
    g_sign = g_moon.sign

    b_nak = b_moon.nakshatra or ""
    g_nak = g_moon.nakshatra or ""

    b_pada = b_moon.pada or 1
    g_pada = g_moon.pada or 1

    b_nak_idx = NAKSHATRA_NAMES.index(b_nak) + 1 if b_nak in NAKSHATRA_NAMES else 1
    g_nak_idx = NAKSHATRA_NAMES.index(g_nak) + 1 if g_nak in NAKSHATRA_NAMES else 1

    # 1. 8 Kootas
    varna = calculate_varna(b_sign, g_sign)
    vashya = calculate_vashya(b_sign, g_sign)
    tara = calculate_tara(b_nak_idx, g_nak_idx)
    yoni = calculate_yoni(b_nak, g_nak)
    graha_maitri = calculate_graha_maitri(b_sign, g_sign)
    gana = calculate_gana(b_nak, g_nak)
    bhakoot = calculate_bhakoot(b_sign, g_sign)
    nadi = calculate_nadi(b_nak, g_nak, b_pada, g_pada, b_sign, g_sign)

    total_pts = (
        varna.obtained_score
        + vashya.obtained_score
        + tara.obtained_score
        + yoni.obtained_score
        + graha_maitri.obtained_score
        + gana.obtained_score
        + bhakoot.obtained_score
        + nadi.obtained_score
    )
    percentage = (total_pts / 36.0) * 100.0

    if total_pts >= 28.0:
        verdict = "Uttama"
        summary = "Highly auspicious union with exceptional harmony and prosperity."
    elif total_pts >= 18.0:
        verdict = "Madhyama"
        summary = "Acceptable match with standard compatibility; minor adjustments required."
    else:
        verdict = "Adhama"
        summary = "Inauspicious match below standard threshold (<18); deep remediation advised."

    ashtakoota_report = AshtakootaReport(
        varna=varna,
        vashya=vashya,
        tara=tara,
        yoni=yoni,
        graha_maitri=graha_maitri,
        gana=gana,
        bhakoot=bhakoot,
        nadi=nadi,
        total_score=round(total_pts, 1),
        percentage=round(percentage, 1),
        verdict=verdict,
        summary=summary,
    )

    # 2. Extended Kootas
    extended_report = calculate_extended_kutas(b_nak, g_nak, b_nak_idx, g_nak_idx)

    # 3. Kuja Dosha
    kuja_report = evaluate_pair_kuja_dosha(bride_chart, groom_chart)

    # Overall recommendation
    if total_pts >= 28.0 and kuja_report.is_compatible and not nadi.dosha_present:
        rec = "Strongly Recommended (Uttama Match with harmonious celestial alignment)"
    elif total_pts >= 18.0 and kuja_report.is_compatible:
        rec = "Recommended with standard compatibility (Madhyama Match)"
    elif total_pts >= 18.0 and not kuja_report.is_compatible:
        rec = "Conditionally Acceptable (Koota score passes, but Kuja Dosha remediation required)"
    else:
        rec = "Caution Advised (Low compatibility score and significant astrological afflictions)"

    return CompatibilityReport(
        bride_name=bride_name,
        groom_name=groom_name,
        bride_moon_sign=b_sign,
        bride_nakshatra=b_nak,
        bride_pada=b_pada,
        groom_moon_sign=g_sign,
        groom_nakshatra=g_nak,
        groom_pada=g_pada,
        ashtakoota=ashtakoota_report,
        extended_kutas=extended_report,
        kuja_dosha=kuja_report,
        overall_score=round(total_pts, 1),
        recommendation=rec,
    )
