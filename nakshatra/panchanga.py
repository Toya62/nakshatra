"""
Nakshatra Panchanga Engine
Calculates the 5 limbs of Vedic time (Panchanga):
1. Tithi (Lunar phase and percentage left)
2. Vara (Vedic weekday from Sunrise)
3. Nakshatra (Lunar constellation and percentage left)
4. Yoga (Solilunar angular sum and percentage left)
5. Karana (Half-tithi and percentage left)
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import swisseph as swe
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from pydantic import BaseModel, Field

from nakshatra.core import (
    Ayanamsa,
    format_tz_offset,
    get_nakshatra,
)

# 30 Tithis
TITHI_NAMES = [
    "Shukla Pratipada",
    "Shukla Dvitiya",
    "Shukla Tritiya",
    "Shukla Chaturthi",
    "Shukla Panchami",
    "Shukla Shashthi",
    "Shukla Saptami",
    "Shukla Ashtami",
    "Shukla Navami",
    "Shukla Dashami",
    "Shukla Ekadashi",
    "Shukla Dvadashi",
    "Shukla Trayodashi",
    "Shukla Chaturdashi",
    "Purnima",
    "Krishna Pratipada",
    "Krishna Dvitiya",
    "Krishna Tritiya",
    "Krishna Chaturthi",
    "Krishna Panchami",
    "Krishna Shashthi",
    "Krishna Saptami",
    "Krishna Ashtami",
    "Krishna Navami",
    "Krishna Dashami",
    "Krishna Ekadashi",
    "Krishna Dvadashi",
    "Krishna Trayodashi",
    "Krishna Chaturdashi",
    "Amavasya",
]

# Tithi ruling planets in classical Parashara cycle (Sun to Rahu)
TITHI_LORDS = [
    "Sun",
    "Moon",
    "Mars",
    "Mercury",
    "Jupiter",
    "Venus",
    "Saturn",
    "Rahu",
    "Sun",
    "Moon",
    "Mars",
    "Mercury",
    "Jupiter",
    "Venus",
    "Saturn",
    "Sun",
    "Moon",
    "Mars",
    "Mercury",
    "Jupiter",
    "Venus",
    "Saturn",
    "Rahu",
    "Sun",
    "Moon",
    "Mars",
    "Mercury",
    "Jupiter",
    "Venus",
    "Saturn",
]

# 27 Solilunar Yogas
YOGA_NAMES = [
    "Vishkambha",
    "Priti",
    "Ayushman",
    "Saubhagya",
    "Shobhana",
    "Atiganda",
    "Sukarma",
    "Dhriti",
    "Shoola",
    "Ganda",
    "Vriddhi",
    "Dhruva",
    "Vyaghata",
    "Harshana",
    "Vajra",
    "Siddhi",
    "Vyatipata",
    "Variyan",
    "Parigha",
    "Shiva",
    "Siddha",
    "Sadhya",
    "Shubha",
    "Shukla",
    "Brahma",
    "Indra",
    "Vaidhriti",
]

YOGA_LORDS = [
    "Saturn",
    "Mercury",
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
]

# 7 Repeating Movable Karanas
MOVABLE_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
MOVABLE_KARANA_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# 4 Fixed Karanas
FIXED_KARANAS = {
    1: ("Kinstughna", "Mars"),
    57: ("Shakuni", "Saturn"),
    58: ("Chatushpada", "Sun"),
    59: ("Naga", "Moon"),
}

# 7 Vedic Weekdays (Vara)
VARA_NAMES = [
    "Ravivara (Sunday)",
    "Somavara (Monday)",
    "Mangalavara (Tuesday)",
    "Budhavara (Wednesday)",
    "Guruvara (Thursday)",
    "Shukravara (Friday)",
    "Shanivara (Saturday)",
]
VARA_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


class TithiData(BaseModel):
    index: int = Field(..., description="1-30")
    name: str
    paksha: str = Field(..., description="Shukla or Krishna")
    lord: str
    degrees_elapsed: float
    percentage_left: float


class NakshatraData(BaseModel):
    index: int = Field(..., description="1-27")
    name: str
    pada: int = Field(..., description="1-4")
    lord: str
    degrees_elapsed: float
    percentage_left: float


class YogaData(BaseModel):
    index: int = Field(..., description="1-27")
    name: str
    lord: str
    degrees_elapsed: float
    percentage_left: float


class KaranaData(BaseModel):
    index: int = Field(..., description="1-60")
    name: str
    lord: str
    is_vishti_bhadra: bool
    degrees_elapsed: float
    percentage_left: float


class VaraData(BaseModel):
    index: int = Field(..., description="0-6 (0=Sunday, 3=Wednesday)")
    name: str
    lord: str
    is_pre_sunrise: bool = False


class PanchangaData(BaseModel):
    """Complete 5-limb Vedic calendar data."""

    timestamp: str
    latitude: float
    longitude: float
    timezone: str
    sunrise_time: str | None = None
    sunset_time: str | None = None
    sun_longitude: float
    moon_longitude: float
    tithi: TithiData
    nakshatra: NakshatraData
    yoga: YogaData
    karana: KaranaData
    vara: VaraData

    def to_table(self) -> str:
        """Format Panchanga into formatted ASCII table."""
        lines = []
        lines.append("=" * 76)
        lines.append("                         VEDIC PANCHANGA REPORT")
        lines.append("=" * 76)
        lines.append(f" Date & Time    : {self.timestamp} ({self.timezone})")
        lines.append(
            f" Coordinates    : {abs(self.latitude):.4f}°{'N' if self.latitude >= 0 else 'S'}, {abs(self.longitude):.4f}°{'E' if self.longitude >= 0 else 'W'}"
        )
        if self.sunrise_time and self.sunset_time:
            lines.append(
                f" Solar Markers  : Sunrise {self.sunrise_time} | Sunset {self.sunset_time}"
            )
        lines.append("-" * 76)
        lines.append(f" 1. VARA (Day)  : {self.vara.name} (Lord: {self.vara.lord})")
        lines.append(
            f" 2. TITHI       : {self.tithi.name} ({self.tithi.paksha}) - {self.tithi.percentage_left:.2f}% left (Lord: {self.tithi.lord})"
        )
        lines.append(
            f" 3. NAKSHATRA   : {self.nakshatra.name} (Pada {self.nakshatra.pada}) - {self.nakshatra.percentage_left:.2f}% left (Lord: {self.nakshatra.lord})"
        )
        lines.append(
            f" 4. YOGA        : {self.yoga.name} - {self.yoga.percentage_left:.2f}% left (Lord: {self.yoga.lord})"
        )
        bhadra_alert = " [BHADRA/VISHTI]" if self.karana.is_vishti_bhadra else ""
        lines.append(
            f" 5. KARANA      : {self.karana.name}{bhadra_alert} - {self.karana.percentage_left:.2f}% left (Lord: {self.karana.lord})"
        )
        lines.append("-" * 76)
        lines.append(
            f" Celestial Posi : Sun {self.sun_longitude:.4f}° | Moon {self.moon_longitude:.4f}°"
        )
        lines.append("=" * 76)
        return "\n".join(lines)


def calculate_panchanga(
    dt: datetime,
    latitude: float,
    longitude: float,
    timezone_str: str,
    ayanamsa: Ayanamsa = Ayanamsa.JHORA_LAHIRI,
) -> PanchangaData:
    """
    Calculate accurate Panchanga (Tithi, Vara, Nakshatra, Yoga, Karana).
    """
    if dt.tzinfo is None:
        local_dt = dt.replace(tzinfo=ZoneInfo(timezone_str))
    else:
        local_dt = dt.astimezone(ZoneInfo(timezone_str))

    utcoffset = local_dt.utcoffset()
    offset_sec = utcoffset.total_seconds() if utcoffset is not None else 0.0
    t_h = local_dt.hour + (local_dt.minute / 60.0) + (local_dt.second / 3600.0)
    t_tz_str = format_tz_offset(offset_sec)

    m_dt = Datetime([local_dt.year, local_dt.month, local_dt.day], t_h, t_tz_str)
    m_pos = GeoPos(latitude, longitude)

    maya_ayanamsa = "lahiri" if ayanamsa == Ayanamsa.JHORA_LAHIRI else ayanamsa.value
    ayan_offset = (56.5318 / 3600.0) if ayanamsa == Ayanamsa.JHORA_LAHIRI else 0.0

    chart = Chart(
        m_dt,
        m_pos,
        IDs=["Sun", "Moon"],
        zodiac="sidereal",
        ayanamsa=maya_ayanamsa,
        hsys="Whole Sign",
    )

    # JHora Lahiri is 56.5318" SMALLER than standard Lahiri, so a sidereal
    # longitude under JHora is the standard-Lahiri longitude PLUS the offset
    # — same convention as core.py (which adds jhora_offset_deg). The old
    # code subtracted it here, putting panchanga ~113" away from the natal
    # chart for JHora charts.
    sun_lon = (chart.get("Sun").lon + ayan_offset) % 360.0
    moon_lon = (chart.get("Moon").lon + ayan_offset) % 360.0

    # 1. Sunrise / Sunset calculation via Swiss Ephemeris
    swe.set_ephe_path("")
    geopos_tuple = (longitude, latitude, 0.0)
    jd_ut = m_dt.jd

    # Compute sunrise on local date using midnight JD as starting point
    midnight_dt = Datetime([local_dt.year, local_dt.month, local_dt.day], 0.0, t_tz_str)
    jd_midnight = midnight_dt.jd

    flag_rise = swe.CALC_RISE | swe.BIT_DISC_CENTER
    flag_set = swe.CALC_SET | swe.BIT_DISC_CENTER

    t_rise_res = swe.rise_trans(jd_midnight, swe.SUN, flag_rise, geopos_tuple, 0.0, 0.0)
    t_set_res = swe.rise_trans(jd_midnight, swe.SUN, flag_set, geopos_tuple, 0.0, 0.0)

    sunrise_jd = t_rise_res[1][0] if t_rise_res[0] == 0 else None
    sunset_jd = t_set_res[1][0] if t_set_res[0] == 0 else None
    calendar_sunrise_jd = sunrise_jd
    calendar_sunset_jd = sunset_jd

    # Check if observation time is before sunrise today
    is_pre_sunrise = False
    if sunrise_jd is not None and jd_ut < sunrise_jd:
        is_pre_sunrise = True
        # If before sunrise today, previous day's sunrise/sunset define the solar day
        from datetime import timedelta

        prev_day = local_dt.date() - timedelta(days=1)
        prev_midnight_dt = Datetime([prev_day.year, prev_day.month, prev_day.day], 0.0, t_tz_str)
        prev_rise_res = swe.rise_trans(
            prev_midnight_dt.jd, swe.SUN, flag_rise, geopos_tuple, 0.0, 0.0
        )
        prev_set_res = swe.rise_trans(
            prev_midnight_dt.jd, swe.SUN, flag_set, geopos_tuple, 0.0, 0.0
        )
        if prev_rise_res[0] == 0:
            sunrise_jd = prev_rise_res[1][0]
        if prev_set_res[0] == 0:
            sunset_jd = prev_set_res[1][0]

    # 2. Vara (Vedic weekday from Sunrise)
    weekday_idx = local_dt.weekday()  # Monday is 0, Sunday is 6
    # Map Python weekday to Sunday=0:
    # Python: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
    # Vedic: Sun=0, Mon=1, Tue=2, Wed=3, Thu=4, Fri=5, Sat=6
    sun_based_weekday = (weekday_idx + 1) % 7
    if is_pre_sunrise:
        sun_based_weekday = (sun_based_weekday - 1) % 7

    vara_name = VARA_NAMES[sun_based_weekday]
    vara_lord = VARA_LORDS[sun_based_weekday]
    vara_data = VaraData(
        index=sun_based_weekday,
        name=vara_name,
        lord=vara_lord,
        is_pre_sunrise=is_pre_sunrise,
    )

    # 3. Tithi (Moon - Sun angle)
    tithi_diff = (moon_lon - sun_lon) % 360.0
    tithi_idx = min(int(tithi_diff / 12.0) + 1, 30)  # 1 to 30
    tithi_span_elapsed = tithi_diff % 12.0
    tithi_pct_left = (1.0 - (tithi_span_elapsed / 12.0)) * 100.0
    paksha = "Shukla" if tithi_idx <= 15 else "Krishna"
    tithi_name = TITHI_NAMES[tithi_idx - 1]
    tithi_lord = TITHI_LORDS[tithi_idx - 1]

    tithi_data = TithiData(
        index=tithi_idx,
        name=tithi_name,
        paksha=paksha,
        lord=tithi_lord,
        degrees_elapsed=round(tithi_span_elapsed, 4),
        percentage_left=round(tithi_pct_left, 2),
    )

    # 4. Nakshatra
    nak_name, nak_lord, nak_pada = get_nakshatra(moon_lon)
    nakshatra_span = 360.0 / 27.0
    moon_lon_mod = moon_lon % 360.0
    nak_idx = min(int(moon_lon_mod / nakshatra_span) + 1, 27)
    nak_span_elapsed = moon_lon_mod % nakshatra_span
    nak_pct_left = (1.0 - (nak_span_elapsed / nakshatra_span)) * 100.0

    nakshatra_data = NakshatraData(
        index=nak_idx,
        name=nak_name,
        pada=nak_pada,
        lord=nak_lord,
        degrees_elapsed=round(nak_span_elapsed, 4),
        percentage_left=round(nak_pct_left, 2),
    )

    # 5. Yoga (Moon + Sun angle)
    yoga_sum = (sun_lon + moon_lon) % 360.0
    yoga_idx = min(int(yoga_sum / nakshatra_span) + 1, 27)  # 1 to 27
    yoga_span_elapsed = yoga_sum % nakshatra_span
    yoga_pct_left = (1.0 - (yoga_span_elapsed / nakshatra_span)) * 100.0
    yoga_name = YOGA_NAMES[yoga_idx - 1]
    yoga_lord = YOGA_LORDS[yoga_idx - 1]

    yoga_data = YogaData(
        index=yoga_idx,
        name=yoga_name,
        lord=yoga_lord,
        degrees_elapsed=round(yoga_span_elapsed, 4),
        percentage_left=round(yoga_pct_left, 2),
    )

    # 6. Karana (Half-tithi: 6 degrees each, 1-60)
    karana_idx = min(int(tithi_diff / 6.0) + 1, 60)  # 1 to 60
    karana_span_elapsed = tithi_diff % 6.0
    karana_pct_left = (1.0 - (karana_span_elapsed / 6.0)) * 100.0

    if karana_idx in FIXED_KARANAS:
        k_name, k_lord = FIXED_KARANAS[karana_idx]
    else:
        # Movable karanas cycle 1 to 7 starting from index 2
        m_idx = (karana_idx - 2) % 7
        k_name = MOVABLE_KARANAS[m_idx]
        k_lord = MOVABLE_KARANA_LORDS[m_idx]

    karana_data = KaranaData(
        index=karana_idx,
        name=k_name,
        lord=k_lord,
        is_vishti_bhadra=(k_name == "Vishti"),
        degrees_elapsed=round(karana_span_elapsed, 4),
        percentage_left=round(karana_pct_left, 2),
    )

    # Format Sunrise / Sunset strings
    def _jd_to_time_str(jd: float | None) -> str | None:
        if jd is None:
            return None
        # Convert JD UT to local time
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

    sunrise_str = _jd_to_time_str(calendar_sunrise_jd)
    sunset_str = _jd_to_time_str(calendar_sunset_jd)

    return PanchangaData(
        timestamp=local_dt.strftime("%Y-%m-%d %H:%M:%S"),
        latitude=latitude,
        longitude=longitude,
        timezone=timezone_str,
        sunrise_time=sunrise_str,
        sunset_time=sunset_str,
        sun_longitude=round(sun_lon, 6),
        moon_longitude=round(moon_lon, 6),
        tithi=tithi_data,
        nakshatra=nakshatra_data,
        yoga=yoga_data,
        karana=karana_data,
        vara=vara_data,
    )
