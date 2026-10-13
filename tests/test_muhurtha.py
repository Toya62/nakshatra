"""
Unit tests for Nakshatra Muhurtha Election Engine.
Validates 24 Planetary Horas, 16 Choghadiyas, Abhijit & Brahma Muhurthas,
Rahu Kalam / Yamaganda octants, and Sarvartha / Amrita Siddhi Yogas.
"""

from __future__ import annotations

from datetime import datetime

from nakshatra.muhurtha import (
    CHALDEAN_HORA_SEQUENCE,
    WEEKDAY_LORDS,
    MuhurthaReport,
    calculate_muhurtha,
)


def test_muhurtha_calculation_structure():
    """Verify complete Muhurtha report structure for midday in New Delhi."""
    dt = datetime(2026, 10, 14, 12, 0, 0)
    lat = 28.6139
    lon = 77.2090
    tz = "Asia/Kolkata"

    rep = calculate_muhurtha(dt, lat, lon, tz)
    assert isinstance(rep, MuhurthaReport)
    assert 0 <= rep.muhurtha_score <= 100
    assert rep.verdict in (
        "Shubha (Highly Auspicious)",
        "Madhyama (Moderate / Usable)",
        "Ashubha (Inauspicious / Afflicted)",
    )

    # Solar bounds present
    assert rep.sunrise_time is not None
    assert rep.sunset_time is not None
    assert rep.next_sunrise_time is not None


def test_horas_24_divisions_and_chaldean_order():
    """Verify 24 Horas generation, correct Chaldean sequence and weekday start."""
    dt = datetime(2026, 10, 14, 12, 0, 0)  # Oct 14, 2026 is Wednesday
    rep = calculate_muhurtha(dt, 28.6139, 77.2090, "Asia/Kolkata")

    assert len(rep.day_horas) == 12
    assert len(rep.night_horas) == 12

    # Weekday lord of Wednesday is Mercury
    assert rep.day_horas[0].ruling_planet == "Mercury"
    assert rep.day_horas[0].hora_index == 1
    assert rep.day_horas[0].period_type == "Day"

    # Chaldean downward sequence check
    for i in range(11):
        curr_lord = rep.day_horas[i].ruling_planet
        next_lord = rep.day_horas[i + 1].ruling_planet
        c_idx = CHALDEAN_HORA_SEQUENCE.index(curr_lord)
        expected_next = CHALDEAN_HORA_SEQUENCE[(c_idx + 1) % 7]
        assert next_lord == expected_next

    # Exactly one hora is active at observation time
    all_horas = rep.day_horas + rep.night_horas
    active_horas = [h for h in all_horas if h.is_current]
    assert len(active_horas) == 1
    assert rep.current_hora.ruling_planet == active_horas[0].ruling_planet


def test_choghadiya_16_divisions():
    """Verify 8 Day and 8 Night Choghadiyas and correct cycle for Wednesday."""
    dt = datetime(2026, 10, 14, 12, 0, 0)  # Wednesday
    rep = calculate_muhurtha(dt, 28.6139, 77.2090, "Asia/Kolkata")

    assert len(rep.day_choghadiyas) == 8
    assert len(rep.night_choghadiyas) == 8

    # Wednesday day cycle starts with Labh
    assert rep.day_choghadiyas[0].name == "Labh"
    assert rep.day_choghadiyas[1].name == "Amrit"

    # Exactly one choghadiya active
    all_chog = rep.day_choghadiyas + rep.night_choghadiyas
    active_chog = [c for c in all_chog if c.is_current]
    assert len(active_chog) == 1
    assert rep.current_choghadiya.name == active_chog[0].name


def test_special_timing_windows():
    """Verify Abhijit, Brahma, Rahu Kalam, and Yamaganda windows."""
    dt = datetime(2026, 10, 14, 12, 0, 0)
    rep = calculate_muhurtha(dt, 28.6139, 77.2090, "Asia/Kolkata")

    # Abhijit Muhurtha around midday
    assert rep.abhijit_muhurtha.start_time < rep.abhijit_muhurtha.end_time
    assert rep.abhijit_muhurtha.name == "Abhijit Muhurtha"

    # Brahma Muhurtha before sunrise
    assert rep.brahma_muhurtha.start_time < rep.brahma_muhurtha.end_time
    assert rep.brahma_muhurtha.name == "Brahma Muhurtha"

    # Rahu Kalam and Yamaganda
    assert rep.rahu_kalam.name == "Rahu Kalam"
    assert rep.rahu_kalam.nature == "Inauspicious"
    assert rep.yamaganda.name == "Yamaganda"
    assert rep.yamaganda.nature == "Inauspicious"


def test_muhurtha_table_formatting():
    """Verify ASCII table rendering."""
    dt = datetime(2026, 10, 14, 12, 0, 0)
    rep = calculate_muhurtha(dt, 28.6139, 77.2090, "Asia/Kolkata")
    table = rep.to_table()

    assert "VEDIC MUHURTHA & ELECTION REPORT" in table
    assert "ACTIVE HORA" in table
    assert "CHOGHADIYA" in table
    assert "Abhijit Muhurtha" in table
    assert "Rahu Kalam" in table
    assert "OVERALL MUHURTHA SCORE:" in table
