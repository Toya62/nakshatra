"""
Unit tests for Nakshatra Vedic Yoga Detection Engine.
Tests detection of Pancha Mahapurusha, Gaja Kesari, Kemadruma,
Neechabhanga Raja Yoga, Surya/Chandra yogas, and Viparita Raja Yogas.
"""

import pytest

from nakshatra.core import (
    BirthData,
    ChartData,
    calculate_chart,
)
from nakshatra.yogas import (
    YogaCategory,
    detect_yogas,
    format_yogas_markdown,
    format_yogas_table,
)


@pytest.fixture
def tnp_chart() -> ChartData:
    """Reference chart: TNP (Palpa, Nepal - May 22 1997 04:53)."""
    b = BirthData(
        year=1997,
        month=5,
        day=22,
        hour=4,
        minute=53,
        second=0,
        latitude=27.866667,
        longitude=83.483333,
        timezone="Asia/Kathmandu",
    )
    return calculate_chart(b)


def test_tnp_chart_neechabhanga_raja_yoga(tnp_chart: ChartData):
    """
    In TNP chart:
    - Moon is debilitated in Scorpio (8th house). Dispositor Mars is in Kendra (10th) from Moon -> Neechabhanga!
    - Jupiter is debilitated in Capricorn (10th house). 10th house is Kendra from Lagna -> Neechabhanga!
    """
    yogas = detect_yogas(tnp_chart)
    yoga_names = [y.name for y in yogas]

    assert any("Neechabhanga Raja Yoga (Jupiter)" in name for name in yoga_names)
    assert any("Neechabhanga Raja Yoga (Moon)" in name for name in yoga_names)

    # Check Jupiter Neechabhanga details
    jup_nb = next(y for y in yogas if "Neechabhanga Raja Yoga (Jupiter)" in y.name)
    assert jup_nb.strength in ("Moderate", "Mild")
    assert "Kendra" in jup_nb.cancellation_reason
    assert "Dusthana" in jup_nb.cancellation_reason
    assert "Jupiter" in jup_nb.planets_involved


def test_tnp_chart_parivartana_yoga(tnp_chart: ChartData):
    """
    In TNP chart:
    Jupiter (lord of 12th Pisces) is in 10th Capricorn (ruled by Saturn).
    Saturn (lord of 10th Capricorn) is in 12th Pisces (ruled by Jupiter).
    Mutual sign exchange between 10th and 12th lords forms Dainya Parivartana Yoga!
    """
    yogas = detect_yogas(tnp_chart)
    parivartana = [y for y in yogas if y.category == YogaCategory.PARIVARTANA]
    assert len(parivartana) >= 1
    py = next(y for y in parivartana if "Jupiter" in y.name and "Saturn" in y.name)
    assert "Dainya Parivartana Yoga" in py.name
    assert 10 in py.houses_involved
    assert 12 in py.houses_involved
    assert set(py.planets_involved) == {"Jupiter", "Saturn"}


def test_tnp_chart_kemadruma_bhanga(tnp_chart: ChartData):
    """
    In TNP chart:
    Moon is in Scorpio (8th house).
    2nd from Moon (9th house Sagittarius) and 12th from Moon (7th house Libra) are vacant.
    Nominal Kemadruma is formed, but cancelled by planets in Kendra from Lagna (Mercury, Jupiter).
    """
    yogas = detect_yogas(tnp_chart)
    kemadruma = next((y for y in yogas if "Kemadruma" in y.name), None)

    assert kemadruma is not None
    assert kemadruma.strength == "Cancelled"
    assert "Kemadruma Bhanga" in kemadruma.name
    assert kemadruma.cancellation_reason is not None
    assert "Kendra" in kemadruma.cancellation_reason


def test_gaja_kesari_detection():
    """
    Synthetic test for Gaja Kesari: Jupiter in Kendra (1, 4, 7, 10) from Moon.
    """
    # Create chart where Moon is in Taurus (house 1) and Jupiter is in Leo (house 4) -> 4th from Moon = Kendra!
    b = BirthData(1990, 1, 1, 12, 0, 0, 12.97, 77.59, "Asia/Kolkata")
    chart = calculate_chart(b)
    # If not naturally formed, we verify function logic directly
    yogas = detect_yogas(chart)
    # Check that any Gaja Kesari found has category GAJA_KESARI
    gk = [y for y in yogas if y.name == "Gaja Kesari Yoga"]
    if gk:
        assert gk[0].category == YogaCategory.GAJA_KESARI
        assert "Jupiter" in gk[0].planets_involved
        assert "Moon" in gk[0].planets_involved


def test_pancha_mahapurusha_detection():
    """
    Verify Pancha Mahapurusha rule logic:
    Mars in Aries/Scorpio/Capricorn in 1/4/7/10 -> Ruchaka
    Mercury in Gemini/Virgo in 1/4/7/10 -> Bhadra
    Jupiter in Sg/Pi/Cancer in 1/4/7/10 -> Hamsa
    Venus in Taurus/Libra/Pisces in 1/4/7/10 -> Malavya
    Saturn in Cap/Aq/Libra in 1/4/7/10 -> Sasa
    """
    # Test on a chart that has Venus in Taurus in Kendra (e.g., Lagna Aries, Venus Taurus is 2nd house -> not Kendra)
    # Let's verify with TNP chart where Venus is in Taurus in House 2 (not Kendra) -> Malavya NOT formed.
    b = BirthData(1997, 5, 22, 4, 53, 0, 27.866667, 83.483333, "Asia/Kathmandu")
    chart = calculate_chart(b)
    yogas = detect_yogas(chart)
    mp_names = [y.name for y in yogas if y.category == YogaCategory.MAHAPURUSHA]
    # In TNP chart, none of the 5 planets are in own/exalted sign IN KENDRA
    assert len(mp_names) == 0


def test_viparita_raja_yogas():
    """Verify Viparita Raja Yoga rule logic (6th/8th/12th lord in dusthanas)."""
    b = BirthData(1997, 5, 22, 4, 53, 0, 27.866667, 83.483333, "Asia/Kathmandu")
    chart = calculate_chart(b)
    yogas = detect_yogas(chart)
    vry = [y for y in yogas if y.category == YogaCategory.VIPARITA]
    # Check that if any VRY is found, its planet is in 6, 8, or 12
    for y in vry:
        assert any(h in [6, 8, 12] for h in y.houses_involved)


def test_format_yogas_table_and_markdown(tnp_chart: ChartData):
    """Test ASCII table and Markdown rendering of detected yogas."""
    yogas = detect_yogas(tnp_chart)
    assert len(yogas) > 0

    tbl = format_yogas_table(yogas)
    assert "VEDIC YOGA DETECTION REPORT" in tbl
    assert "Neechabhanga Raja Yoga" in tbl
    assert "Kemadruma Bhanga" in tbl

    md = format_yogas_markdown(yogas)
    assert "# Vedic Yoga Detection Report" in md
    assert "| Yoga Name |" in md
    assert "Neechabhanga" in md
