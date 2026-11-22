"""
Unit tests for Nakshatra Rashi Fal (Moon-sign horoscope) Engine.
"""

from __future__ import annotations

from datetime import datetime, timezone

from nakshatra.core import BirthData
from nakshatra.rashi_fal import calculate_rashi_fal


def _live_example_birth():
    """17 Feb 1984, 09:31, Kathmandu — the chart shown on the live site."""
    return BirthData(
        year=1984,
        month=2,
        day=17,
        hour=9,
        minute=31,
        latitude=27.7172,
        longitude=85.3240,
        timezone="Asia/Kathmandu",
    )


def test_all_nine_grahas_including_rahu_ketu():
    """Rahu and Ketu must appear: the old lookup only searched
    chart.planets (Sun..Saturn), so the table showed 7 grahas."""
    r = calculate_rashi_fal(
        _live_example_birth(),
        period="daily",
        reference_date=datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc),
    )
    assert len(r.graha_results) == 9
    by_planet = {g.planet: g for g in r.graha_results}
    assert by_planet["Rahu"].house_from_moon == 7
    assert by_planet["Ketu"].house_from_moon == 1
    assert by_planet["Saturn"].house_from_moon == 8
    assert by_planet["Venus"].favourable is True
    assert {g.verdict_key for g in r.graha_results} <= {
        "excellent",
        "good",
        "mixed",
        "challenging",
        "difficult",
    }


def test_mixed_transits_score_zero():
    """A 'mixed' transit is neutral, not a failure.

    On 2026-12-20 the live example has 3 good, 2 mixed, 2 challenging and
    2 difficult transits. The old +1/-1 rule scored it 3 - 6 = -3
    (Difficult); the corrected weights give 3 - 4 = -1 (Challenging).
    """
    r = calculate_rashi_fal(
        _live_example_birth(),
        period="daily",
        reference_date=datetime(2026, 12, 20, 12, 0, tzinfo=timezone.utc),
    )
    keys = [g.verdict_key for g in r.graha_results]
    assert keys.count("good") == 3
    assert keys.count("mixed") == 2
    assert keys.count("challenging") == 2
    assert keys.count("difficult") == 2
    assert r.overall_score == -1
    assert r.overall_verdict.startswith("Challenging")


def test_live_example_day_is_genuinely_difficult():
    """22 Nov 2026 stays Difficult — but now for the right reasons: 6 of 9
    grahas are challenging/difficult (incl. Saturn 8th from Moon) and only
    Venus is favourable. The fix is not a whitewash."""
    r = calculate_rashi_fal(
        _live_example_birth(),
        period="daily",
        reference_date=datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc),
    )
    assert r.overall_score == -5
    assert r.overall_verdict.startswith("Difficult")
    assert r.moon_sign == "Leo"
    assert r.reference_date == "2026-11-22"
