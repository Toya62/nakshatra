"""
Unit tests for Nakshatra Compatibility Engine.
Validates 36-point Ashtakoota matching, classical dosha cancellations,
extended kutas (Mahendra, Stree Deergha, Rajju, Vedha), and Kuja Dosha.
"""

from __future__ import annotations

import pytest

from nakshatra.compatibility import (
    calculate_bhakoot,
    calculate_compatibility,
    calculate_extended_kutas,
    calculate_gana,
    calculate_graha_maitri,
    calculate_nadi,
    calculate_tara,
    calculate_varna,
    calculate_vashya,
    calculate_yoni,
    evaluate_chart_kuja_dosha,
    evaluate_pair_kuja_dosha,
)
from nakshatra.core import BirthData, calculate_chart


@pytest.fixture
def chart_bride():
    """Birth chart for bride: May 22, 1997, 04:53, Palpa, Nepal (Scorpio Moon / Vishakha)."""
    return calculate_chart(
        BirthData(1997, 5, 22, 4, 53, 0, 27.8667, 83.4833, "Asia/Kathmandu")
    )


@pytest.fixture
def chart_groom():
    """Birth chart for groom: Nov 28, 1995, 08:30, Delhi, India (Capricorn Moon / Dhanishta)."""
    return calculate_chart(
        BirthData(1995, 11, 28, 8, 30, 0, 28.6139, 77.2090, "Asia/Kolkata")
    )


def test_varna_koota():
    """Brahmin bride + Kshatriya groom -> 0.0 pts; Brahmin groom + Kshatriya bride -> 1.0 pt."""
    # Cancer (Brahmin) vs Leo (Kshatriya)
    assert calculate_varna("Cancer", "Leo").obtained_score == 0.0
    assert calculate_varna("Leo", "Cancer").obtained_score == 1.0
    # Both same varna -> 1.0 pt
    assert calculate_varna("Cancer", "Scorpio").obtained_score == 1.0


def test_vashya_koota():
    """Test Vashya sign harmony and predator/prey discord."""
    # Identical signs -> 2.0 pts
    assert calculate_vashya("Aries", "Aries").obtained_score == 2.0
    # Aries is attracted to Leo -> 1.0 or 2.0 pts
    assert calculate_vashya("Aries", "Leo").obtained_score >= 1.0
    # Leo (Vanachara) vs Taurus (Chatushpada) -> predator conflict (0.0 pt)
    assert calculate_vashya("Leo", "Taurus").obtained_score == 0.0


def test_tara_koota():
    """Test Tara calculations from nakshatra indices (1-27)."""
    # Same nakshatra (Janma 1) -> both favorable (3.0 pts)
    t_same = calculate_tara(1, 1)
    assert t_same.obtained_score == 3.0
    assert t_same.is_favorable is True

    # Ashwini (1) to Bharani (2: Sampat) and Bharani (2) to Ashwini (27 % 9 = 9: Parama Mitra) -> 3.0 pts
    t_1_2 = calculate_tara(1, 2)
    assert t_1_2.obtained_score == 3.0


def test_yoni_koota():
    """Test Yoni matching and deadly enemy zero score."""
    # Ashwini (Horse) and Shatabhisha (Horse) -> Swavarga 4.0 pts
    y_same = calculate_yoni("Ashwini", "Shatabhisha")
    assert y_same.obtained_score == 4.0
    assert y_same.dosha_present is False

    # Cow (Uttara Phalguni) vs Tiger (Chitra) -> Swabhava Vaira (0.0 pt)
    y_enemy = calculate_yoni("Uttara Phalguni", "Chitra")
    assert y_enemy.obtained_score == 0.0
    assert y_enemy.dosha_present is True


def test_graha_maitri_koota():
    """Test Moon sign lord friendship."""
    # Aries (Mars) & Leo (Sun) -> Mutual friends (5.0 pts)
    assert calculate_graha_maitri("Aries", "Leo").obtained_score == 5.0
    # Leo (Sun) & Sagittarius (Jupiter) -> Mutual friends (5.0 pts)
    assert calculate_graha_maitri("Leo", "Sagittarius").obtained_score == 5.0
    # Cancer (Moon) & Scorpio (Mars) -> One friend, one neutral (4.0 pts)
    assert calculate_graha_maitri("Cancer", "Scorpio").obtained_score == 4.0
    # Leo (Sun) & Capricorn (Saturn) -> Mutual enemies (0.0 pt)
    assert calculate_graha_maitri("Leo", "Capricorn").obtained_score == 0.0


def test_gana_koota():
    """Test Gana temperament alignment."""
    # Both Deva -> 6.0 pts
    assert calculate_gana("Ashwini", "Pushya").obtained_score == 6.0
    # Deva groom & Rakshasa bride -> 0.0 pt (Gana Dosha)
    assert calculate_gana("Krittika", "Ashwini").obtained_score == 0.0
    assert calculate_gana("Krittika", "Ashwini").dosha_present is True


def test_bhakoot_koota_and_cancellation():
    """Test Bhakoot distances (favorable vs afflicted) and classical cancellations."""
    # 1/7 distance: Aries & Libra -> 7.0 pts
    assert calculate_bhakoot("Aries", "Libra").obtained_score == 7.0

    # 6/8 Sashtashtaka: Aries (Mars) & Scorpio (Mars) -> Same lord cancels Bhakoot Dosha!
    b_cancelled = calculate_bhakoot("Aries", "Scorpio")
    assert b_cancelled.obtained_score == 7.0
    assert b_cancelled.cancelled is True

    # 6/8 Sashtashtaka: Aries (Mars) & Virgo (Mercury) -> Uncancelled -> 0.0 pt
    b_afflicted = calculate_bhakoot("Aries", "Virgo")
    assert b_afflicted.obtained_score == 0.0
    assert b_afflicted.dosha_present is True


def test_nadi_koota_and_cancellation():
    """Test Nadi compatibility (8 pts for different Nadis, cancellation overrides)."""
    # Different Nadis: Ashwini (Adi) vs Bharani (Madhya) -> 8.0 pts
    n_diff = calculate_nadi("Ashwini", "Bharani")
    assert n_diff.obtained_score == 8.0
    assert n_diff.dosha_present is False

    # Same Nadi without cancellation: Ashwini (Adi) vs Ardra (Adi) -> 0.0 pt
    n_same = calculate_nadi("Ashwini", "Ardra")
    assert n_same.obtained_score == 0.0
    assert n_same.dosha_present is True

    # Same Nakshatra but different Padas: Ashwini Pada 1 vs Ashwini Pada 2 -> Cancelled!
    n_canc = calculate_nadi("Ashwini", "Ashwini", bride_pada=1, groom_pada=2)
    assert n_canc.obtained_score == 8.0
    assert n_canc.cancelled is True


def test_extended_kutas():
    """Test Mahendra, Stree Deergha, Rajju, and Vedha."""
    # Ashwini (1) & Jyeshtha (18) -> Vedha pair!
    ext = calculate_extended_kutas("Ashwini", "Jyeshtha", 1, 18)
    assert ext.vedha.dosha_present is True
    assert ext.vedha.obtained_score == 0.0

    # Ashwini (1) & Bharani (2) -> Distance 2, no Vedha
    ext_clean = calculate_extended_kutas("Ashwini", "Bharani", 1, 2)
    assert ext_clean.vedha.dosha_present is False
    assert ext_clean.vedha.obtained_score == 1.0


def test_kuja_dosha_evaluation(chart_bride, chart_groom):
    """Test Kuja Dosha detection on natal charts and pair compatibility."""
    b_kuja = evaluate_chart_kuja_dosha(chart_bride)
    g_kuja = evaluate_chart_kuja_dosha(chart_groom)

    assert isinstance(b_kuja.is_manglik, bool)
    assert isinstance(g_kuja.is_manglik, bool)

    pair_kuja = evaluate_pair_kuja_dosha(chart_bride, chart_groom)
    assert isinstance(pair_kuja.is_compatible, bool)
    assert len(pair_kuja.verdict) > 0


def test_calculate_compatibility_full_report(chart_bride, chart_groom):
    """Test complete relationship compatibility calculation."""
    report = calculate_compatibility(chart_bride, chart_groom, "Sita", "Rama")
    assert report.bride_name == "Sita"
    assert report.groom_name == "Rama"
    assert report.ashtakoota.total_score >= 0.0
    assert report.ashtakoota.total_score <= 36.0
    assert report.ashtakoota.verdict in ("Uttama", "Madhyama", "Adhama")

    table = report.to_table()
    assert "VEDIC ASHTAKOOTA COMPATIBILITY REPORT" in table
    assert "TOTAL ASHTAKOOTA:" in table
    assert "FINAL RECOMMENDATION:" in table
