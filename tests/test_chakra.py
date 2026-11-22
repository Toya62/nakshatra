"""
Unit tests for Nakshatra Chakra Systems (Navatara, Compound, Ghatchakra).
"""

from __future__ import annotations

from nakshatra.chakra import (
    _WEEKDAY_LORDS,
    attach_ghati_count,
    calculate_chakra,
)
from nakshatra.core import BirthData, calculate_chart


def _live_example_chart():
    """17 Feb 1984, 09:31, Kathmandu — the chart shown on the live site."""
    birth = BirthData(
        year=1984,
        month=2,
        day=17,
        hour=9,
        minute=31,
        latitude=27.7172,
        longitude=85.3240,
        timezone="Asia/Kathmandu",
    )
    return calculate_chart(birth)


def test_attach_ghati_count_true_sunrise():
    """Ghatis count from the TRUE local sunrise, not a fixed 06:00 UTC.

    Kathmandu sunrise on 17 Feb 1984 is ~06:26 local; 09:31 is 184.6 min
    later = 7 whole ghatis. The old code labelled the local time as UTC and
    used a fixed 06:00 sunrise, giving 8.
    """
    assert attach_ghati_count(_live_example_chart()) == 7


def test_attach_ghati_count_pre_sunrise():
    """A pre-sunrise birth counts ghatis since the previous day's sunrise.

    22 May 1997 04:53 Kathmandu is before sunrise (~05:19), so the old code
    clamped the negative elapsed time to 0 -> 12. The true count is 10
    ghatis since the previous sunrise, and the Vedic weekday is Wednesday
    (the civil day is Thursday, but the Vedic day starts at sunrise).
    """
    birth = BirthData(
        year=1997,
        month=5,
        day=22,
        hour=4,
        minute=53,
        latitude=27.8667,
        longitude=83.4833,
        timezone="Asia/Kathmandu",
    )
    chart = calculate_chart(birth)
    assert attach_ghati_count(chart) == 10
    rep = chart.get_chakra()
    assert rep.ghati_count == 10
    assert rep.birth_weekday == "Wednesday"


def test_ghatchakra_weekday_anchor():
    """The lord cycle is anchored on the weekday lord of the birth day.

    17 Feb 1984 is a Friday (Venus). With 7 ghatis elapsed, house 1 is
    ruled by Jupiter — Venus advanced 6 lords — and the cycle runs
    Jupiter, Venus, Saturn, Sun, Moon, Mars, Mercury, ...
    """
    rep = _live_example_chart().get_chakra()
    rulers = [g.ruler for g in rep.ghatchakra]
    assert rep.ghati_count == 7
    assert rep.birth_weekday == "Friday"
    assert rulers == [
        "Jupiter", "Venus", "Saturn", "Sun", "Moon", "Mars",
        "Mercury", "Jupiter", "Venus", "Saturn", "Sun", "Moon",
    ]
    # These are weekday lords, not sign lords: house 1 (Aries) is NOT ruled
    # by Mars, and the old unanchored code's Moon is gone too.
    assert rep.ghatchakra[0].ruler != "Mars"
    assert rep.ghatchakra[0].ruler != "Moon"
    # Signs still count from the birth Lagna as before.
    assert [g.sign for g in rep.ghatchakra[:3]] == ["Aries", "Taurus", "Gemini"]


def test_calculate_chakra_default_weekday_preserved():
    """Direct callers passing only ghati_count keep the old Monday anchor."""
    rep = calculate_chakra(_live_example_chart(), ghati_count=1)
    assert rep.ghatchakra[0].ruler == _WEEKDAY_LORDS[0]  # Moon
    assert rep.birth_weekday == "Monday"


def test_chakra_report_structure():
    """Navatara and compound sections are unchanged by the ghati fix."""
    rep = _live_example_chart().get_chakra()
    assert len(rep.navatara) == 7
    assert len(rep.compound_relationships) == 21
    assert len(rep.ghatchakra) == 12
    assert rep.janma_nakshatra
    assert rep.summary
