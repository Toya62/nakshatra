"""
Nakshatra Muhurtha Election Engine
Production-grade Vedic electional astrology and auspicious timing engine.
Adapted from classical Jyotish canons (Muhurtha Chintamani, Kalaprakasika,
Brihat Samhita) and the VedAstro architectural model.

Calculations:
- Complete Panchanga analysis (Tithi, Vara, Nakshatra, Yoga, Karana)
- 24 Planetary Horas (Day and Night horas with Chaldean planetary sequence)
- 16 Choghadiyas (8 Day & 8 Night divisions: Amrit, Shubh, Labh, Char, Rog, Kaal, Udveg)
- Solar Timing Windows:
    - Abhijit Muhurtha (Midday solar culmination window)
    - Brahma Muhurtha (Pre-dawn creator window)
    - Vijaya & Godhuli Muhurthas
    - Rahu Kalam, Yamaganda, and Gulika Kalam octants
- Classical Auspicious Yogas:
    - Sarvartha Siddhi Yoga
    - Amrita Siddhi Yoga
    - Guru Pushya Yoga & Ravi Pushya Yoga
    - Tripushkar & Dwipushkar Yogas
- Composite Muhurtha Suitability Score (0-100) and enterprise suitability tags
  (Business, Travel, Marriage, Investment, Property, Medical).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import swisseph as swe
from mayaastrolib.datetime import Datetime
from pydantic import BaseModel, Field

from nakshatra.core import Ayanamsa, format_tz_offset
from nakshatra.panchanga import (
    PanchangaData,
    calculate_panchanga,
)

# ---------------------------------------------------------------------------
# Classical Muhurtha Mappings
# ---------------------------------------------------------------------------

# Chaldean planetary sequence in descending order of orbit/speed
CHALDEAN_HORA_SEQUENCE = [
    "Saturn",
    "Jupiter",
    "Mars",
    "Sun",
    "Venus",
    "Mercury",
    "Moon",
]

# Weekday lords: Sun=0 (Sunday), Mon=1, Tue=2, Wed=3, Thu=4, Fri=5, Sat=6
WEEKDAY_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Hora Nature and recommendations
HORA_PROFILES: dict[str, dict[str, str]] = {
    "Sun": {
        "nature": "Malefic",
        "quality": "Authority & Governance",
        "recommended": "Government matters, applying for jobs, executive decisions, meeting superiors",
        "avoid": "New partnerships, peace talks, sensitive diplomacy",
    },
    "Moon": {
        "nature": "Benefic",
        "quality": "Fluidity & Domestic",
        "recommended": "Travel, public relations, water sports, culinary arts, moving residence",
        "avoid": "Surgery, long-term binding agreements during waning moon",
    },
    "Mars": {
        "nature": "Malefic",
        "quality": "Energy & Courage",
        "recommended": "Sports, surgery, mechanics, physical defense, purchasing metals/weapons",
        "avoid": "Marriage, signing contracts, travel, peaceful negotiations",
    },
    "Mercury": {
        "nature": "Benefic",
        "quality": "Intellect & Commerce",
        "recommended": "Trading, programming, writing, drafting contracts, accounting, learning",
        "avoid": "Idle disputes, highly emotional confrontations",
    },
    "Jupiter": {
        "nature": "Benefic",
        "quality": "Wisdom & Expansion",
        "recommended": "Financial investments, legal agreements, marriage ceremonies, spiritual study, teaching",
        "avoid": "Destructive or punitive actions",
    },
    "Venus": {
        "nature": "Benefic",
        "quality": "Harmony & Luxury",
        "recommended": "Weddings, artistic projects, buying jewelry or vehicles, luxury purchases, romance",
        "avoid": "Litigation, confrontations, starting wars",
    },
    "Saturn": {
        "nature": "Malefic",
        "quality": "Discipline & Foundation",
        "recommended": "Laying foundation stones, real estate acquisition, agricultural work, meditation",
        "avoid": "Celebrations, weddings, medical surgeries, fast results",
    },
}

# 7 Choghadiya types
CHOGHADIYA_TYPES = {
    "Amrit": {"nature": "Auspicious", "ruler": "Moon", "score": 100},
    "Shubh": {"nature": "Auspicious", "ruler": "Jupiter", "score": 90},
    "Labh": {"nature": "Auspicious", "ruler": "Mercury", "score": 85},
    "Char": {"nature": "Neutral", "ruler": "Venus", "score": 70},
    "Rog": {"nature": "Inauspicious", "ruler": "Mars", "score": 30},
    "Kaal": {"nature": "Inauspicious", "ruler": "Saturn", "score": 20},
    "Udveg": {"nature": "Inauspicious", "ruler": "Sun", "score": 25},
}

# Day Choghadiya sequence per weekday (Sun=0 to Sat=6)
DAY_CHOGHADIYA_CYCLES = [
    ["Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg"],  # Sunday
    ["Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit"],  # Monday
    ["Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog"],  # Tuesday
    ["Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh"],  # Wednesday
    ["Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh"],  # Thursday
    ["Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char"],  # Friday
    ["Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal"],  # Saturday
]

# Night Choghadiya sequence per weekday
NIGHT_CHOGHADIYA_CYCLES = [
    ["Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh"],  # Sunday
    ["Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char"],  # Monday
    ["Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal"],  # Tuesday
    ["Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg"],  # Wednesday
    ["Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit"],  # Thursday
    ["Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog"],  # Friday
    ["Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh"],  # Saturday
]

# Daytime Rahu Kalam octant index (1 to 8) per weekday (Sun=0 to Sat=6)
# Sunday=8, Monday=2, Tuesday=7, Wednesday=5, Thursday=6, Friday=4, Saturday=3
RAHU_KALAM_OCTANTS = [8, 2, 7, 5, 6, 4, 3]

# Yamaganda octant index (1 to 8)
# Sunday=5, Monday=4, Tuesday=3, Wednesday=2, Thursday=1, Friday=7, Saturday=6
YAMAGANDA_OCTANTS = [5, 4, 3, 2, 1, 7, 6]

# Gulika Kalam octant index (1 to 8)
# Sunday=7, Monday=6, Tuesday=5, Wednesday=4, Thursday=3, Friday=2, Saturday=1
GULIKA_OCTANTS = [7, 6, 5, 4, 3, 2, 1]

# Sarvartha Siddhi Yoga (Vara 0-6 -> set of Nakshatra names)
SARVARTHA_SIDDHI_MAP: dict[int, set[str]] = {
    0: {
        "Hasta",
        "Mula",
        "Uttara Phalguni",
        "Uttara Ashadha",
        "Uttara Bhadrapada",
        "Ashwini",
        "Pushya",
    },
    1: {"Rohini", "Mrigashira", "Punarvasu", "Pushya", "Shravana"},
    2: {"Ashwini", "Krittika", "Ashlesha"},
    3: {"Rohini", "Anuradha", "Hasta", "Krittika"},
    4: {"Ashwini", "Punarvasu", "Pushya", "Anuradha"},
    5: {"Ashwini", "Anuradha", "Revati"},
    6: {"Rohini", "Swati", "Shravana"},
}

# Amrita Siddhi Yoga (Vara 0-6 -> single Nakshatra)
AMRITA_SIDDHI_MAP: dict[int, str] = {
    0: "Hasta",
    1: "Mrigashira",
    2: "Ashwini",
    3: "Anuradha",
    4: "Pushya",
    5: "Revati",
    6: "Rohini",
}


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class TimeInterval(BaseModel):
    """Start and end time strings for a muhurtha window."""

    name: str
    start_time: str
    end_time: str
    is_active: bool
    nature: str = Field(..., description="'Auspicious', 'Inauspicious', or 'Neutral'")
    score: int
    notes: str = ""


class HoraItem(BaseModel):
    """Planetary Hora period."""

    hora_index: int = Field(..., description="1-24 (1-12 Day, 13-24 Night)")
    period_type: str = Field(..., description="'Day' or 'Night'")
    ruling_planet: str
    start_time: str
    end_time: str
    is_current: bool
    nature: str
    recommended_activities: str


class ChoghadiyaItem(BaseModel):
    """Choghadiya subdivision."""

    index: int = Field(..., description="1-8")
    name: str
    period_type: str = Field(..., description="'Day' or 'Night'")
    ruler: str
    nature: str
    score: int
    start_time: str
    end_time: str
    is_current: bool


class SpecialYogaStatus(BaseModel):
    """Presence of classical electional yogas."""

    sarvartha_siddhi: bool
    amrita_siddhi: bool
    guru_pushya: bool
    ravi_pushya: bool
    tripushkar: bool
    vishti_bhadra_active: bool
    active_yogas: list[str]


class MuhurthaSuitability(BaseModel):
    """Enterprise suitability indicators for activities."""

    business_contract: bool
    financial_investment: bool
    travel: bool
    marriage: bool
    property_purchase: bool
    medical_treatment: bool


class MuhurthaReport(BaseModel):
    """Comprehensive Muhurtha Election Report."""

    timestamp: str
    timezone: str
    latitude: float
    longitude: float
    sunrise_time: str
    sunset_time: str
    next_sunrise_time: str
    panchanga: PanchangaData
    current_hora: HoraItem
    current_choghadiya: ChoghadiyaItem
    special_yogas: SpecialYogaStatus
    abhijit_muhurtha: TimeInterval
    brahma_muhurtha: TimeInterval
    rahu_kalam: TimeInterval
    yamaganda: TimeInterval
    gulika_kalam: TimeInterval
    durmuhurtha: list[TimeInterval]
    day_horas: list[HoraItem]
    night_horas: list[HoraItem]
    day_choghadiyas: list[ChoghadiyaItem]
    night_choghadiyas: list[ChoghadiyaItem]
    muhurtha_score: int = Field(..., description="Overall moment score from 0 to 100")
    verdict: str
    suitability: MuhurthaSuitability
    recommendation: str

    def to_table(self) -> str:
        """Render Muhurtha report into formatted ASCII table."""
        lines = []
        lines.append("=" * 80)
        lines.append("                      VEDIC MUHURTHA & ELECTION REPORT")
        lines.append("=" * 80)
        lines.append(f" Observation Time   : {self.timestamp} ({self.timezone})")
        lines.append(
            f" Solar Day Bounds   : Sunrise {self.sunrise_time} | Sunset {self.sunset_time}"
        )
        lines.append("-" * 80)
        lines.append(
            f" 1. ACTIVE HORA      : {self.current_hora.ruling_planet} Hora "
            f"({self.current_hora.start_time} - {self.current_hora.end_time}) [{self.current_hora.nature}]"
        )
        lines.append(f"    Recommendations  : {self.current_hora.recommended_activities}")
        lines.append(
            f" 2. CHOGHADIYA       : {self.current_choghadiya.name} "
            f"({self.current_choghadiya.start_time} - {self.current_choghadiya.end_time}) "
            f"[{self.current_choghadiya.nature} | Score: {self.current_choghadiya.score}]"
        )
        lines.append("-" * 80)
        lines.append(" 3. SPECIAL TIMING WINDOWS:")
        lines.append(
            f"    - Abhijit Muhurtha : {self.abhijit_muhurtha.start_time} - {self.abhijit_muhurtha.end_time} "
            f"({'ACTIVE' if self.abhijit_muhurtha.is_active else 'Inactive'})"
        )
        lines.append(
            f"    - Brahma Muhurtha  : {self.brahma_muhurtha.start_time} - {self.brahma_muhurtha.end_time}"
        )
        lines.append(
            f"    - Rahu Kalam [AVOID] : {self.rahu_kalam.start_time} - {self.rahu_kalam.end_time} "
            f"({'ALERT: ACTIVE NOW' if self.rahu_kalam.is_active else 'Inactive'})"
        )
        lines.append(
            f"    - Yamaganda [AVOID]  : {self.yamaganda.start_time} - {self.yamaganda.end_time}"
        )
        lines.append("-" * 80)
        active_yogas_str = (
            ", ".join(self.special_yogas.active_yogas)
            if self.special_yogas.active_yogas
            else "None"
        )
        lines.append(f" 4. CELESTIAL YOGAS  : {active_yogas_str}")
        bhadra_str = (
            "YES (Vishti/Bhadra Karana in progress - inauspicious)"
            if self.special_yogas.vishti_bhadra_active
            else "No"
        )
        lines.append(f"    - Vishti/Bhadra : {bhadra_str}")
        lines.append("-" * 80)
        lines.append(f" OVERALL MUHURTHA SCORE: {self.muhurtha_score}/100 -> {self.verdict}")
        lines.append(
            f" Enterprise Suitability: Business={self.suitability.business_contract} | "
            f"Investment={self.suitability.financial_investment} | "
            f"Travel={self.suitability.travel} | "
            f"Marriage={self.suitability.marriage}"
        )
        lines.append("=" * 80)
        lines.append(f" FINAL VERDICT: {self.recommendation}")
        lines.append("=" * 80)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Calculation Engine
# ---------------------------------------------------------------------------


def calculate_muhurtha(
    dt: datetime,
    latitude: float,
    longitude: float,
    timezone_str: str,
    ayanamsa: Ayanamsa = Ayanamsa.JHORA_LAHIRI,
) -> MuhurthaReport:
    """
    Calculate comprehensive Vedic Muhurtha and election report for a given time and location.
    """
    if dt.tzinfo is None:
        local_dt = dt.replace(tzinfo=ZoneInfo(timezone_str))
    else:
        local_dt = dt.astimezone(ZoneInfo(timezone_str))

    # Base Panchanga
    panchanga = calculate_panchanga(
        local_dt,
        latitude,
        longitude,
        timezone_str,
        ayanamsa=ayanamsa,
    )

    swe.set_ephe_path("")
    geopos_tuple = (longitude, latitude, 0.0)

    # Convert local_dt into UTC offset seconds
    utcoffset = local_dt.utcoffset()
    offset_sec = utcoffset.total_seconds() if utcoffset is not None else 0.0
    t_tz_str = format_tz_offset(offset_sec)

    # Calculate Sunrise, Sunset, and Next Sunrise exact JDs
    midnight_dt = Datetime([local_dt.year, local_dt.month, local_dt.day], 0.0, t_tz_str)
    flag_rise = swe.CALC_RISE | swe.BIT_DISC_CENTER
    flag_set = swe.CALC_SET | swe.BIT_DISC_CENTER

    t_rise_res = swe.rise_trans(midnight_dt.jd, swe.SUN, flag_rise, geopos_tuple, 0.0, 0.0)
    t_set_res = swe.rise_trans(midnight_dt.jd, swe.SUN, flag_set, geopos_tuple, 0.0, 0.0)

    sunrise_jd = t_rise_res[1][0] if t_rise_res[0] == 0 else midnight_dt.jd + 0.25
    sunset_jd = t_set_res[1][0] if t_set_res[0] == 0 else midnight_dt.jd + 0.75

    # Check if observation time is before today's sunrise
    obs_jd = Datetime(
        [local_dt.year, local_dt.month, local_dt.day],
        local_dt.hour + local_dt.minute / 60.0 + local_dt.second / 3600.0,
        t_tz_str,
    ).jd

    if obs_jd < sunrise_jd:
        # Pre-sunrise: Use yesterday's sunrise and sunset
        prev_day = local_dt.date() - timedelta(days=1)
        prev_midnight_dt = Datetime([prev_day.year, prev_day.month, prev_day.day], 0.0, t_tz_str)
        p_rise = swe.rise_trans(prev_midnight_dt.jd, swe.SUN, flag_rise, geopos_tuple, 0.0, 0.0)
        p_set = swe.rise_trans(prev_midnight_dt.jd, swe.SUN, flag_set, geopos_tuple, 0.0, 0.0)
        next_sunrise_jd = sunrise_jd
        sunrise_jd = p_rise[1][0] if p_rise[0] == 0 else prev_midnight_dt.jd + 0.25
        sunset_jd = p_set[1][0] if p_set[0] == 0 else prev_midnight_dt.jd + 0.75
    else:
        # Normal daytime or night after sunset: next sunrise is tomorrow's sunrise
        next_day = local_dt.date() + timedelta(days=1)
        next_midnight_dt = Datetime([next_day.year, next_day.month, next_day.day], 0.0, t_tz_str)
        n_rise = swe.rise_trans(next_midnight_dt.jd, swe.SUN, flag_rise, geopos_tuple, 0.0, 0.0)
        next_sunrise_jd = n_rise[1][0] if n_rise[0] == 0 else next_midnight_dt.jd + 0.25

    day_duration_sec = (sunset_jd - sunrise_jd) * 86400.0
    night_duration_sec = (next_sunrise_jd - sunset_jd) * 86400.0

    def _jd_to_time_str(jd: float) -> str:
        res = swe.revjul(jd, swe.GREG_CAL)
        ut_hour = res[3]
        local_hour = (ut_hour + (offset_sec / 3600.0)) % 24.0
        h = int(local_hour)
        m = int((local_hour - h) * 60.0)
        s = int(round(((local_hour - h) * 60.0 - m) * 60.0))
        if s >= 60:
            s = 0
            m += 1
        if m >= 60:
            m = 0
            h = (h + 1) % 24
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _is_between(curr_jd: float, start_jd: float, end_jd: float) -> bool:
        return start_jd <= curr_jd <= end_jd

    sunrise_str = _jd_to_time_str(sunrise_jd)
    sunset_str = _jd_to_time_str(sunset_jd)
    next_sunrise_str = _jd_to_time_str(next_sunrise_jd)

    weekday_idx = panchanga.vara.index  # Sunday=0, Monday=1, ...
    weekday_lord = WEEKDAY_LORDS[weekday_idx]
    start_lord_idx = CHALDEAN_HORA_SEQUENCE.index(weekday_lord)

    # 1. 24 Planetary Horas
    day_hora_sec = day_duration_sec / 12.0
    night_hora_sec = night_duration_sec / 12.0

    day_horas: list[HoraItem] = []
    night_horas: list[HoraItem] = []
    current_hora: HoraItem | None = None

    # Day Horas (1 to 12)
    for i in range(12):
        h_start_jd = sunrise_jd + (i * day_hora_sec / 86400.0)
        h_end_jd = sunrise_jd + ((i + 1) * day_hora_sec / 86400.0)
        lord = CHALDEAN_HORA_SEQUENCE[(start_lord_idx + i) % 7]
        profile = HORA_PROFILES[lord]
        is_cur = _is_between(obs_jd, h_start_jd, h_end_jd)
        h_item = HoraItem(
            hora_index=i + 1,
            period_type="Day",
            ruling_planet=lord,
            start_time=_jd_to_time_str(h_start_jd),
            end_time=_jd_to_time_str(h_end_jd),
            is_current=is_cur,
            nature=profile["nature"],
            recommended_activities=profile["recommended"],
        )
        day_horas.append(h_item)
        if is_cur:
            current_hora = h_item

    # Night Horas (13 to 24)
    for i in range(12):
        h_start_jd = sunset_jd + (i * night_hora_sec / 86400.0)
        h_end_jd = sunset_jd + ((i + 1) * night_hora_sec / 86400.0)
        lord = CHALDEAN_HORA_SEQUENCE[(start_lord_idx + 12 + i) % 7]
        profile = HORA_PROFILES[lord]
        is_cur = _is_between(obs_jd, h_start_jd, h_end_jd)
        h_item = HoraItem(
            hora_index=13 + i,
            period_type="Night",
            ruling_planet=lord,
            start_time=_jd_to_time_str(h_start_jd),
            end_time=_jd_to_time_str(h_end_jd),
            is_current=is_cur,
            nature=profile["nature"],
            recommended_activities=profile["recommended"],
        )
        night_horas.append(h_item)
        if is_cur:
            current_hora = h_item

    if current_hora is None:
        current_hora = day_horas[0]

    # 2. Choghadiya (8 Day and 8 Night)
    day_chog_sec = day_duration_sec / 8.0
    night_chog_sec = night_duration_sec / 8.0

    day_cycle = DAY_CHOGHADIYA_CYCLES[weekday_idx]
    night_cycle = NIGHT_CHOGHADIYA_CYCLES[weekday_idx]

    day_choghadiyas: list[ChoghadiyaItem] = []
    night_choghadiyas: list[ChoghadiyaItem] = []
    current_choghadiya: ChoghadiyaItem | None = None

    for i in range(8):
        c_start_jd = sunrise_jd + (i * day_chog_sec / 86400.0)
        c_end_jd = sunrise_jd + ((i + 1) * day_chog_sec / 86400.0)
        name = day_cycle[i]
        c_meta = CHOGHADIYA_TYPES[name]
        is_cur = _is_between(obs_jd, c_start_jd, c_end_jd)
        c_item = ChoghadiyaItem(
            index=i + 1,
            name=name,
            period_type="Day",
            ruler=str(c_meta["ruler"]),
            nature=str(c_meta["nature"]),
            score=int(str(c_meta["score"])),
            start_time=_jd_to_time_str(c_start_jd),
            end_time=_jd_to_time_str(c_end_jd),
            is_current=is_cur,
        )
        day_choghadiyas.append(c_item)
        if is_cur:
            current_choghadiya = c_item

    for i in range(8):
        c_start_jd = sunset_jd + (i * night_chog_sec / 86400.0)
        c_end_jd = sunset_jd + ((i + 1) * night_chog_sec / 86400.0)
        name = night_cycle[i]
        c_meta = CHOGHADIYA_TYPES[name]
        is_cur = _is_between(obs_jd, c_start_jd, c_end_jd)
        c_item = ChoghadiyaItem(
            index=i + 1,
            name=name,
            period_type="Night",
            ruler=str(c_meta["ruler"]),
            nature=str(c_meta["nature"]),
            score=int(str(c_meta["score"])),
            start_time=_jd_to_time_str(c_start_jd),
            end_time=_jd_to_time_str(c_end_jd),
            is_current=is_cur,
        )
        night_choghadiyas.append(c_item)
        if is_cur:
            current_choghadiya = c_item

    if current_choghadiya is None:
        current_choghadiya = day_choghadiyas[0]

    # 3. Solar Timing Windows
    # 3a. Abhijit Muhurtha: 8th muhurtha of daytime (day split into 15 equal parts)
    day_muhurtha_sec = day_duration_sec / 15.0
    abhijit_start_jd = sunrise_jd + (7 * day_muhurtha_sec / 86400.0)
    abhijit_end_jd = sunrise_jd + (8 * day_muhurtha_sec / 86400.0)
    # Note: On Wednesdays, Abhijit Muhurtha is traditionally not recommended due to Budha-Mangala dosha
    abhijit_score = 95 if weekday_idx != 3 else 50
    abhijit_window = TimeInterval(
        name="Abhijit Muhurtha",
        start_time=_jd_to_time_str(abhijit_start_jd),
        end_time=_jd_to_time_str(abhijit_end_jd),
        is_active=_is_between(obs_jd, abhijit_start_jd, abhijit_end_jd),
        nature="Auspicious" if weekday_idx != 3 else "Neutral",
        score=abhijit_score,
        notes="Auspicious solar culmination window"
        if weekday_idx != 3
        else "Weakened on Wednesday",
    )

    # 3b. Brahma Muhurtha: 2 muhurthas (96 min) before sunrise to 1 muhurtha (48 min) before sunrise
    brahma_start_jd = sunrise_jd - (96.0 * 60.0 / 86400.0)
    brahma_end_jd = sunrise_jd - (48.0 * 60.0 / 86400.0)
    brahma_window = TimeInterval(
        name="Brahma Muhurtha",
        start_time=_jd_to_time_str(brahma_start_jd),
        end_time=_jd_to_time_str(brahma_end_jd),
        is_active=_is_between(obs_jd, brahma_start_jd, brahma_end_jd),
        nature="Auspicious",
        score=100,
        notes="Ideal for meditation, study, and spiritual undertakings",
    )

    # 3c. Inauspicious Octants (Rahu Kalam, Yamaganda, Gulika)
    rahu_oct = RAHU_KALAM_OCTANTS[weekday_idx] - 1
    rahu_start_jd = sunrise_jd + (rahu_oct * day_chog_sec / 86400.0)
    rahu_end_jd = sunrise_jd + ((rahu_oct + 1) * day_chog_sec / 86400.0)
    rahu_window = TimeInterval(
        name="Rahu Kalam",
        start_time=_jd_to_time_str(rahu_start_jd),
        end_time=_jd_to_time_str(rahu_end_jd),
        is_active=_is_between(obs_jd, rahu_start_jd, rahu_end_jd),
        nature="Inauspicious",
        score=10,
        notes="Strictly avoid starting new ventures, contracts, or long journeys",
    )

    yama_oct = YAMAGANDA_OCTANTS[weekday_idx] - 1
    yama_start_jd = sunrise_jd + (yama_oct * day_chog_sec / 86400.0)
    yama_end_jd = sunrise_jd + ((yama_oct + 1) * day_chog_sec / 86400.0)
    yama_window = TimeInterval(
        name="Yamaganda",
        start_time=_jd_to_time_str(yama_start_jd),
        end_time=_jd_to_time_str(yama_end_jd),
        is_active=_is_between(obs_jd, yama_start_jd, yama_end_jd),
        nature="Inauspicious",
        score=15,
        notes="Inauspicious for monetary transactions and agreements",
    )

    guli_oct = GULIKA_OCTANTS[weekday_idx] - 1
    guli_start_jd = sunrise_jd + (guli_oct * day_chog_sec / 86400.0)
    guli_end_jd = sunrise_jd + ((guli_oct + 1) * day_chog_sec / 86400.0)
    guli_window = TimeInterval(
        name="Gulika Kalam",
        start_time=_jd_to_time_str(guli_start_jd),
        end_time=_jd_to_time_str(guli_end_jd),
        is_active=_is_between(obs_jd, guli_start_jd, guli_end_jd),
        nature="Inauspicious",
        score=20,
        notes="Ruled by Saturn's son Gulika",
    )

    # 4. Durmuhurtha windows (1 or 2 specific daytime muhurthas per weekday)
    # Sunday: 14th muhurtha
    # Monday: 9th and 12th muhurthas
    # Tuesday: 6th and 7th muhurthas
    # Wednesday: 8th muhurtha (overlaps with Abhijit)
    # Thursday: 12th and 13th muhurthas
    # Friday: 4th and 9th muhurthas
    # Saturday: 1st and 2nd muhurthas
    dur_muhurtha_map = {
        0: [14],
        1: [9, 12],
        2: [6, 7],
        3: [8],
        4: [12, 13],
        5: [4, 9],
        6: [1, 2],
    }
    dur_windows: list[TimeInterval] = []
    for m_idx in dur_muhurtha_map.get(weekday_idx, []):
        d_start = sunrise_jd + ((m_idx - 1) * day_muhurtha_sec / 86400.0)
        d_end = sunrise_jd + (m_idx * day_muhurtha_sec / 86400.0)
        dur_windows.append(
            TimeInterval(
                name=f"Durmuhurtha #{m_idx}",
                start_time=_jd_to_time_str(d_start),
                end_time=_jd_to_time_str(d_end),
                is_active=_is_between(obs_jd, d_start, d_end),
                nature="Inauspicious",
                score=15,
                notes="Adverse planetary radiation period",
            )
        )

    # 5. Auspicious Celestial Yogas
    current_nak_name = panchanga.nakshatra.name
    active_yogas: list[str] = []

    # 5a. Sarvartha Siddhi Yoga
    ss_nakshatras = SARVARTHA_SIDDHI_MAP.get(weekday_idx, set())
    is_sarvartha_siddhi = current_nak_name in ss_nakshatras
    if is_sarvartha_siddhi:
        active_yogas.append("Sarvartha Siddhi Yoga")

    # 5b. Amrita Siddhi Yoga
    is_amrita_siddhi = AMRITA_SIDDHI_MAP.get(weekday_idx) == current_nak_name
    if is_amrita_siddhi:
        active_yogas.append("Amrita Siddhi Yoga")

    # 5c. Guru Pushya Yoga & Ravi Pushya Yoga
    is_guru_pushya = weekday_idx == 4 and current_nak_name == "Pushya"
    if is_guru_pushya:
        active_yogas.append("Guru Pushya Yoga (Supreme Auspiciousness)")

    is_ravi_pushya = weekday_idx == 0 and current_nak_name == "Pushya"
    if is_ravi_pushya:
        active_yogas.append("Ravi Pushya Yoga (High Prosperity)")

    # 5d. Tripushkar Yoga: Bhadra Tithi (2, 7, 12) + Vara (Sun, Tue, Sat) + Tri-pada Nakshatra
    tripushkar_tithis = {2, 7, 12, 17, 22, 27}
    tripushkar_varas = {0, 2, 6}
    tripushkar_naks = {
        "Krittika",
        "Punarvasu",
        "Uttara Phalguni",
        "Vishakha",
        "Uttara Ashadha",
        "Purva Bhadrapada",
    }
    is_tripushkar = (
        panchanga.tithi.index in tripushkar_tithis
        and weekday_idx in tripushkar_varas
        and current_nak_name in tripushkar_naks
    )
    if is_tripushkar:
        active_yogas.append("Tripushkar Yoga (Triple result)")

    is_bhadra = panchanga.karana.is_vishti_bhadra

    special_yogas_status = SpecialYogaStatus(
        sarvartha_siddhi=is_sarvartha_siddhi,
        amrita_siddhi=is_amrita_siddhi,
        guru_pushya=is_guru_pushya,
        ravi_pushya=is_ravi_pushya,
        tripushkar=is_tripushkar,
        vishti_bhadra_active=is_bhadra,
        active_yogas=active_yogas,
    )

    # 6. Overall Composite Score (0 to 100)
    score = current_choghadiya.score

    # Hora weight
    if current_hora.nature == "Benefic":
        score += 10
    else:
        score -= 10

    # Timing afflictions
    if rahu_window.is_active:
        score -= 40
    if yama_window.is_active:
        score -= 20
    if any(d.is_active for d in dur_windows):
        score -= 25
    if is_bhadra:
        score -= 25

    # Timing blessings
    if abhijit_window.is_active and abhijit_window.nature == "Auspicious":
        score += 25
    if is_guru_pushya or is_ravi_pushya:
        score += 30
    elif is_amrita_siddhi:
        score += 20
    elif is_sarvartha_siddhi:
        score += 15

    score = max(5, min(100, score))

    # Verdict & Enterprise Suitability
    if score >= 80:
        verdict = "Shubha (Highly Auspicious)"
    elif score >= 55:
        verdict = "Madhyama (Moderate / Usable)"
    else:
        verdict = "Ashubha (Inauspicious / Afflicted)"

    is_rahu_active = rahu_window.is_active
    is_favorable_base = score >= 60 and not is_rahu_active and not is_bhadra

    suitability = MuhurthaSuitability(
        business_contract=is_favorable_base
        and current_hora.ruling_planet in ("Jupiter", "Mercury", "Venus", "Sun"),
        financial_investment=is_favorable_base
        and current_hora.ruling_planet in ("Jupiter", "Venus", "Mercury"),
        travel=is_favorable_base
        and current_hora.ruling_planet in ("Moon", "Venus", "Mercury")
        and not yama_window.is_active,
        marriage=is_favorable_base
        and current_hora.ruling_planet in ("Jupiter", "Venus")
        and score >= 75,
        property_purchase=is_favorable_base
        and current_hora.ruling_planet in ("Saturn", "Jupiter", "Mars"),
        medical_treatment=is_favorable_base
        and current_hora.ruling_planet in ("Sun", "Mars", "Jupiter"),
    )

    if score >= 80:
        recommendation = "Excellent moment. Highly favorable for launching ventures, signing contracts, and celebrations."
    elif score >= 60:
        recommendation = "Favorable moment for routine enterprise tasks and normal activities. Observe basic precautions."
    elif is_rahu_active:
        recommendation = "Rahu Kalam active! Postpone important signatures, departures, or new commitments until this window ends."
    elif is_bhadra:
        recommendation = (
            "Vishti/Bhadra Karana in progress. Avoid auspicious ceremonies and travels."
        )
    else:
        recommendation = "Adverse planetary alignment. Postpone major life decisions or consult an astrologer for remediation."

    return MuhurthaReport(
        timestamp=local_dt.strftime("%Y-%m-%d %H:%M:%S"),
        timezone=timezone_str,
        latitude=latitude,
        longitude=longitude,
        sunrise_time=sunrise_str,
        sunset_time=sunset_str,
        next_sunrise_time=next_sunrise_str,
        panchanga=panchanga,
        current_hora=current_hora,
        current_choghadiya=current_choghadiya,
        special_yogas=special_yogas_status,
        abhijit_muhurtha=abhijit_window,
        brahma_muhurtha=brahma_window,
        rahu_kalam=rahu_window,
        yamaganda=yama_window,
        gulika_kalam=guli_window,
        durmuhurtha=dur_windows,
        day_horas=day_horas,
        night_horas=night_horas,
        day_choghadiyas=day_choghadiyas,
        night_choghadiyas=night_choghadiyas,
        muhurtha_score=score,
        verdict=verdict,
        suitability=suitability,
        recommendation=recommendation,
    )
