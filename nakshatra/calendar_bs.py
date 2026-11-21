"""
Nepali Bikram Sambat (BS) Calendar & Devanagari Sanskrit Nomenclature.

Provides accurate conversion between Gregorian (AD) and Bikram Sambat (BS),
along with canonical Devanagari designations for Grahas, Rasis, and Nakshatras.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import nepali_datetime  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

# Canonical Devanagari mappings
DEVANAGARI_PLANETS: dict[str, str] = {
    "Sun": "सूर्य",
    "Moon": "चन्द्र",
    "Mars": "मङ्गल",
    "Mercury": "बुध",
    "Jupiter": "बृहस्पति (गुरु)",
    "Venus": "शुक्र",
    "Saturn": "शनि",
    "Rahu": "राहु",
    "Ketu": "केतु",
    "Ascendant": "लग्न",
    "Midheaven": "दशम भाव (MC)",
}

DEVANAGARI_SIGNS: dict[str, str] = {
    "Aries": "मेष",
    "Taurus": "वृष",
    "Gemini": "मिथुन",
    "Cancer": "कर्कट",
    "Leo": "सिंह",
    "Virgo": "कन्या",
    "Libra": "तुला",
    "Scorpio": "वृश्चिक",
    "Sagittarius": "धनु",
    "Capricorn": "मकर",
    "Aquarius": "कुम्भ",
    "Pisces": "मीन",
}

DEVANAGARI_NAKSHATRAS: list[str] = [
    "अश्विनी",
    "भरणी",
    "कृत्तिका",
    "रोहिणी",
    "मृगशिरा",
    "आर्द्रा",
    "पुनर्वसु",
    "पुष्य",
    "आश्लेषा",
    "मघा",
    "पूर्वाफाल्गुनी",
    "उत्तराफाल्गुनी",
    "हस्त",
    "चित्रा",
    "स्वाती",
    "विशाखा",
    "अनुराधा",
    "ज्येष्ठा",
    "मूल",
    "पूर्वाषाढ़ा",
    "उत्तराषाढ़ा",
    "श्रवण",
    "धनिष्ठा",
    "शतभिषा",
    "पूर्वाभाद्रपद",
    "उत्तराभाद्रपद",
    "रेवती",
]

NEPALI_MONTHS: list[dict[str, Any]] = [
    {"index": 1, "name_en": "Baishakh", "name_ne": "वैशाख"},
    {"index": 2, "name_en": "Jestha", "name_ne": "जेठ"},
    {"index": 3, "name_en": "Ashadh", "name_ne": "असार"},
    {"index": 4, "name_en": "Shrawan", "name_ne": "साउन"},
    {"index": 5, "name_en": "Bhadra", "name_ne": "भदौ"},
    {"index": 6, "name_en": "Ashwin", "name_ne": "असोज"},
    {"index": 7, "name_en": "Kartik", "name_ne": "कात्तिक"},
    {"index": 8, "name_en": "Mangsir", "name_ne": "मंसिर"},
    {"index": 9, "name_en": "Poush", "name_ne": "पुस"},
    {"index": 10, "name_en": "Magh", "name_ne": "माघ"},
    {"index": 11, "name_en": "Falgun", "name_ne": "फागुन"},
    {"index": 12, "name_en": "Chaitra", "name_ne": "चैत"},
]


class BikramSambatDate(BaseModel):
    """Nepali Bikram Sambat representation of an astronomical epoch."""

    year: int = Field(..., description="Bikram Sambat year, e.g. 2054")
    month: int = Field(..., ge=1, le=12, description="Month 1-12 (Baishakh=1)")
    month_name_en: str = Field(..., description="English transliteration of Nepali month")
    month_name_ne: str = Field(..., description="Devanagari Nepali month")
    day: int = Field(..., ge=1, le=32, description="Day of the month (Gate)")
    formatted: str = Field(..., description="Formatted string: e.g. '2054 Jestha 09'")
    formatted_ne: str = Field(..., description="Formatted Devanagari string: e.g. '२०५४ जेठ ०९'")


class GregorianDate(BaseModel):
    """Gregorian date representation."""

    year: int = Field(..., description="Gregorian year, e.g. 1997")
    month: int = Field(..., ge=1, le=12, description="Month 1-12")
    day: int = Field(..., ge=1, le=31, description="Day of month")
    formatted: str = Field(..., description="Formatted string: e.g. '1997-05-22'")


def ad_to_bs(year: int, month: int, day: int) -> BikramSambatDate:
    """
    Convert Gregorian (AD) calendar date to Nepali Bikram Sambat (BS).
    Uses authentic Nepali Panchanga ephemeris tables via nepali_datetime,
    with mathematical fallback if outside supported range (1918-2043 AD).
    """
    g_date = date(year, month, day)

    try:
        bs_dt = nepali_datetime.date.from_datetime_date(g_date)
        bs_year = bs_dt.year
        bs_month = bs_dt.month
        bs_day = bs_dt.day
    except (ValueError, OverflowError):
        # Fallback approximation: BS is ~56 years, 8 months, 17 days ahead of AD
        if month < 4 or (month == 4 and day < 14):
            bs_year = year + 56
            bs_month = ((month + 8) % 12) or 12
        else:
            bs_year = year + 57
            bs_month = month - 3
        bs_day = min(day, 30)

    m_info = NEPALI_MONTHS[bs_month - 1]

    devanagari_digits = str.maketrans("0123456789", "०१२३४५६७८९")
    f_en = f"{bs_year} {m_info['name_en']} {bs_day:02d}"
    f_ne = f"{str(bs_year).translate(devanagari_digits)} {m_info['name_ne']} {f'{bs_day:02d}'.translate(devanagari_digits)}"

    return BikramSambatDate(
        year=bs_year,
        month=bs_month,
        month_name_en=m_info["name_en"],
        month_name_ne=m_info["name_ne"],
        day=bs_day,
        formatted=f_en,
        formatted_ne=f_ne,
    )


def bs_to_ad(year: int, month: int, day: int) -> GregorianDate:
    """
    Convert Nepali Bikram Sambat (BS) date to Gregorian (AD) calendar date.
    """
    try:
        bs_dt = nepali_datetime.date(year, month, day)
        ad_dt = bs_dt.to_datetime_date()
        return GregorianDate(
            year=ad_dt.year,
            month=ad_dt.month,
            day=ad_dt.day,
            formatted=ad_dt.isoformat(),
        )
    except Exception:
        # Fallback approximation: AD is ~56.7 years behind BS
        approx_year = year - 57 if month > 8 else year - 56
        approx_month = (month + 3) if month <= 9 else (month - 9)
        approx_day = min(day, 28)
        ad_dt = date(approx_year, approx_month, approx_day)
        return GregorianDate(
            year=ad_dt.year,
            month=ad_dt.month,
            day=ad_dt.day,
            formatted=ad_dt.isoformat(),
        )


def get_devanagari_chart_labels(planet_name: str, sign_name: str) -> dict[str, str]:
    """Return authentic Devanagari representation for Graha and Rasi."""
    return {
        "planet_en": planet_name,
        "planet_ne": DEVANAGARI_PLANETS.get(planet_name, planet_name),
        "sign_en": sign_name,
        "sign_ne": DEVANAGARI_SIGNS.get(sign_name, sign_name),
    }
