"""
Unit tests for Nakshatra Gochar Transits Engine.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from nakshatra.core import BirthData, calculate_chart
from nakshatra.transits import (
    FAVORABLE_GOCHAR_HOUSES,
    VEDIC_ASPECTS,
    calculate_transits,
)


def _sample_chart():
    birth = BirthData(
        year=2000,
        month=1,
        day=1,
        hour=12,
        minute=0,
        latitude=23.1765,
        longitude=75.7885,
        timezone="Asia/Kolkata",
    )
    return calculate_chart(birth)


def test_transit_constants():
    """Verify classical Gochar rules and Vedic aspects are well formed."""
    assert 3 in FAVORABLE_GOCHAR_HOUSES["Sun"]
    assert 11 in FAVORABLE_GOCHAR_HOUSES["Saturn"]
    assert 7 in VEDIC_ASPECTS["Jupiter"]
    assert 5 in VEDIC_ASPECTS["Jupiter"]
    assert 9 in VEDIC_ASPECTS["Jupiter"]


def test_calculate_transits():
    """Verify transit calculation overlays properly on a natal chart."""
    chart = _sample_chart()
    t_dt = datetime(2026, 10, 18, 12, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    report = calculate_transits(chart, transit_date=t_dt)

    assert report.natal_lagna_sign == chart.ascendant.sign
    assert len(report.planets) >= 9
    planet_names = {t.name for t in report.planets}
    assert "Sun" in planet_names
    assert "Saturn" in planet_names
    assert "Jupiter" in planet_names

    # Check that houses are valid 1-12
    for t in report.planets:
        assert 1 <= t.house_from_lagna <= 12
        assert 1 <= t.house_from_moon <= 12
        assert t.sign in [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]


def test_sade_sati_detection():
    """Verify Sade Sati analysis returns structured data."""
    chart = _sample_chart()
    report = calculate_transits(chart)
    assert report.sade_sati is not None
    assert hasattr(report.sade_sati, "is_active")
    assert hasattr(report.sade_sati, "phase")
