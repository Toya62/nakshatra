"""
Unit tests for Nakshatra Special Lagnas — Ghati Lagna in particular.

Regression: Ghati Lagna shared the Chakra module's UTC/fixed-06:00 sunrise
bug (local birth time mislabelled as UTC), so its sign was wrong, and its
degree was a hardcoded 0.0 placeholder, so the UI always showed
"Degree: 0.00°". The longitude now follows the file's own Indu Lagna
convention: the ascendant's longitude carried forward by (ghati_count - 1)
signs from the true sunrise.
"""

from __future__ import annotations

from nakshatra.core import BirthData, calculate_chart


def _ghati(chart):
    return next(lagna for lagna in chart.get_special_lagnas().lagnas if lagna.name == "Ghati Lagna")


def test_ghati_lagna_live_example():
    """17 Feb 1984, 09:31, Kathmandu. True sunrise 06:26 -> 7 ghatis.
    Ascendant Aries 6.54 deg -> Ghati Lagna Libra 6.54 deg, House 7.
    The old code gave Scorpio House 8 at 0.00 deg."""
    birth = BirthData(
        year=1984, month=2, day=17, hour=9, minute=31,
        latitude=27.7172, longitude=85.3240, timezone="Asia/Kathmandu",
    )
    chart = calculate_chart(birth)
    g = _ghati(chart)
    assert g.sign == "Libra"
    assert g.house == 7
    assert g.lord == "Venus"
    assert abs(g.degree_in_sign - 6.54) < 0.01
    assert abs(g.longitude - 186.54) < 0.01
    # The degree is the birth Lagna's degree carried forward, not a placeholder.
    assert abs(g.degree_in_sign - (chart.ascendant.longitude % 30.0)) < 0.01


def test_ghati_lagna_pre_sunrise_birth():
    """22 May 1997, 04:53, Palpa — before sunrise, so ghatis count from the
    previous day's sunrise (10 ghatis). Ascendant Aries 28.86 deg ->
    Ghati Lagna Capricorn 28.86 deg, House 10."""
    birth = BirthData(
        year=1997, month=5, day=22, hour=4, minute=53,
        latitude=27.8667, longitude=83.4833, timezone="Asia/Kathmandu",
    )
    chart = calculate_chart(birth)
    g = _ghati(chart)
    assert g.sign == "Capricorn"
    assert g.house == 10
    assert abs(g.degree_in_sign - 28.86) < 0.01


def test_ghati_lagna_note_states_ghati_count():
    birth = BirthData(
        year=1984, month=2, day=17, hour=9, minute=31,
        latitude=27.7172, longitude=85.3240, timezone="Asia/Kathmandu",
    )
    notes = calculate_chart(birth).get_special_lagnas().notes
    assert any("Ghati Lagna: 7 ghatis" in n for n in notes)
