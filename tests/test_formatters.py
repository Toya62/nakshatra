"""
Unit tests for Nakshatra Output Formatters (table, markdown, csv, diagram).
"""

from __future__ import annotations

from nakshatra.core import BirthData, calculate_chart
from nakshatra.formatters import (
    _dec_to_dms,
    format_chart_diagram,
    format_csv,
    format_markdown,
    format_table,
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
        place_name="Ujjain",
    )
    return calculate_chart(birth)


def test_dec_to_dms():
    """Verify conversion from decimal degrees to DMS string."""
    assert _dec_to_dms(0.0) == "00° 00' 00\""
    assert "15° 30'" in _dec_to_dms(15.5)


def test_format_table():
    """Verify ASCII table formatting."""
    chart = _sample_chart()
    out = format_table(chart)
    assert "NAKSHATRA VEDIC BIRTH CHART" in out
    assert "Ujjain" in out
    assert "Sun" in out
    assert "Ayanamsa" in out


def test_format_markdown():
    """Verify markdown output formatting."""
    chart = _sample_chart()
    out = format_markdown(chart)
    assert "# Nakshatra Vedic Birth Chart" in out
    assert "| Planet |" in out
    assert "Sun" in out


def test_format_csv():
    """Verify CSV output formatting."""
    chart = _sample_chart()
    out = format_csv(chart)
    assert "Body,Sign,Degree_In_Sign" in out
    assert "Ascendant,Pisces" in out
    assert "Sun,Sagittarius" in out


def test_format_chart_diagram():
    """Verify South Indian chart diagram formatting."""
    chart = _sample_chart()
    out = format_chart_diagram(chart, varga="D1")
    assert "+---" in out
    assert "|" in out
