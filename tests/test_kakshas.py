"""
Unit tests for Ashtakavarga Kakshas and Shodhita reductions.
Validates the 8-Kakshya transit division per sign and Trikona/Ekadhipatya reductions.
"""

from __future__ import annotations

from datetime import datetime

from nakshatra.core import BirthData, calculate_chart
from nakshatra.transits import calculate_transits


def test_shodhita_ashtakavarga_in_chart():
    """Verify Shodhita Ashtakavarga (reduced SAV & BAV) in natal chart."""
    birth = BirthData(1997, 5, 22, 4, 53, 0, 27.8667, 83.4833, "Asia/Kathmandu")
    chart = calculate_chart(birth)

    assert chart.ashtakavarga is not None
    assert chart.ashtakavarga.shodhita_sarvashtakavarga is not None
    assert len(chart.ashtakavarga.shodhita_sarvashtakavarga) == 12

    # Reduced SAV sum is substantially less than 337
    reduced_total = sum(chart.ashtakavarga.shodhita_sarvashtakavarga)
    assert reduced_total < 337
    assert reduced_total > 0

    assert chart.ashtakavarga.shodhita_bhinnashtakavarga is not None
    assert len(chart.ashtakavarga.shodhita_bhinnashtakavarga) == 7


def test_gochara_kakshyas_in_transits():
    """Verify 8 Kakshas (3°45' divisions) in transit report."""
    birth = BirthData(1997, 5, 22, 4, 53, 0, 27.8667, 83.4833, "Asia/Kathmandu")
    chart = calculate_chart(birth)

    transit_dt = datetime(2026, 10, 14, 12, 0, 0)
    report = calculate_transits(chart, transit_date=transit_dt)

    assert len(report.kakshya_summary) == 7

    # Check classical 7 planets have Kakshya properties
    for p in report.planets:
        if p.name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            assert p.kakshya_lord in (
                "Saturn",
                "Jupiter",
                "Mars",
                "Sun",
                "Venus",
                "Mercury",
                "Moon",
                "Ascendant",
            )
            assert 0 <= p.kakshya_index <= 7
            assert p.kakshya_range is not None
            assert isinstance(p.kakshya_has_bindu, bool)

    table = report.to_table()
    assert "GOCHARA KAKSHYAS (ASHTAKAVARGA SUB-TRANSITS)" in table
    assert "Kakshya Lord" in table
