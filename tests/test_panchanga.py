"""
Unit tests for Nakshatra Panchanga Engine.
Validates exact calculations of Tithi, Vara, Nakshatra, Yoga, and Karana
against Jagannatha Hora reference data (TNP LCP chart).
"""

from datetime import datetime

from nakshatra.core import Ayanamsa
from nakshatra.panchanga import (
    FIXED_KARANAS,
    PanchangaData,
    calculate_panchanga,
)


def test_panchanga_tnp_reference_concordance():
    """
    Validate against JHora reference chart TNP LCP:
    Date: May 22, 1997, 04:53:00 (+05:45)
    Place: 27N52, 83E29 (Palpa, Nepal)
    JHora Reference:
      Tithi: Pournimasya (Sa) (43.13% left)
      Vedic Weekday: Wednesday (Me)
      Nakshatra: Visakha (Ju) (10.45% left)
      Yoga: Parigha (Sa) (32.07% left)
      Karana: Bava (Su) (86.26% left)
    """
    dt = datetime(1997, 5, 22, 4, 53, 0)
    lat = 27.866667
    lon = 83.483333
    tz = "Asia/Kathmandu"

    p = calculate_panchanga(dt, lat, lon, tz, ayanamsa=Ayanamsa.JHORA_LAHIRI)

    assert isinstance(p, PanchangaData)

    # 1. Vara (Pre-sunrise Wednesday / Budhavara)
    assert p.vara.is_pre_sunrise is True
    assert "Wednesday" in p.vara.name or "Budhavara" in p.vara.name
    assert p.vara.lord == "Mercury"

    # 2. Tithi (Purnima / Pournimasya, Saturn lord, ~43.1% left)
    assert p.tithi.name == "Purnima"
    assert p.tithi.paksha == "Shukla"
    assert p.tithi.lord == "Saturn"
    assert abs(p.tithi.percentage_left - 43.13) < 0.2

    # 3. Nakshatra (Visakha / Vishakha, Pada 4, Jupiter lord, ~10.5% left)
    assert "Vishakha" in p.nakshatra.name or "Visakha" in p.nakshatra.name
    assert p.nakshatra.pada == 4
    assert p.nakshatra.lord == "Jupiter"
    assert abs(p.nakshatra.percentage_left - 10.45) < 0.5

    # 4. Yoga (Parigha, Saturn lord, ~32.1% left)
    assert p.yoga.name == "Parigha"
    assert p.yoga.lord == "Saturn"
    assert abs(p.yoga.percentage_left - 32.07) < 0.8

    # 5. Karana (Bava, Sun lord, ~86.2% left)
    assert p.karana.name == "Bava"
    assert p.karana.lord == "Sun"
    assert p.karana.is_vishti_bhadra is False
    assert abs(p.karana.percentage_left - 86.26) < 0.3


def test_panchanga_post_sunrise_weekday():
    """Verify that after sunrise, standard civil weekday is used."""
    dt = datetime(1997, 5, 22, 12, 0, 0)  # Noon
    p = calculate_panchanga(dt, 27.866667, 83.483333, "Asia/Kathmandu")

    assert p.vara.is_pre_sunrise is False
    assert "Thursday" in p.vara.name or "Guruvara" in p.vara.name
    assert p.vara.lord == "Jupiter"


def test_panchanga_fixed_karanas_mapping():
    """Verify the 4 fixed karanas are present and mapped correctly."""
    assert 1 in FIXED_KARANAS
    assert FIXED_KARANAS[1] == ("Kinstughna", "Mars")
    assert 57 in FIXED_KARANAS
    assert FIXED_KARANAS[57] == ("Shakuni", "Saturn")
    assert 58 in FIXED_KARANAS
    assert FIXED_KARANAS[58] == ("Chatushpada", "Sun")
    assert 59 in FIXED_KARANAS
    assert FIXED_KARANAS[59] == ("Naga", "Moon")


def test_panchanga_table_formatting():
    """Verify table rendering of Panchanga."""
    dt = datetime(1997, 5, 22, 4, 53, 0)
    p = calculate_panchanga(dt, 27.866667, 83.483333, "Asia/Kathmandu")
    tbl = p.to_table()

    assert "VEDIC PANCHANGA REPORT" in tbl
    assert "1. VARA" in tbl
    assert "2. TITHI" in tbl
    assert "3. NAKSHATRA" in tbl
    assert "4. YOGA" in tbl
    assert "5. KARANA" in tbl
