"""Tests for Bikram Sambat calendar conversions and Devanagari nomenclature."""

from fastapi.testclient import TestClient

from nakshatra.api import app
from nakshatra.calendar_bs import (
    DEVANAGARI_NAKSHATRAS,
    ad_to_bs,
    bs_to_ad,
    get_devanagari_chart_labels,
)


def test_ad_to_bs_known_date():
    """Verify known date conversion to Bikram Sambat."""
    res = ad_to_bs(1997, 5, 22)
    assert res.year == 2054
    assert res.month == 2
    assert res.month_name_en == "Jestha"
    assert res.month_name_ne == "जेठ"
    assert res.day == 9
    assert res.formatted == "2054 Jestha 09"
    assert "२०५४" in res.formatted_ne
    assert "जेठ" in res.formatted_ne


def test_bs_to_ad_bidirectional():
    """Verify converting BS back to AD produces original Gregorian date."""
    bs_res = ad_to_bs(2020, 1, 1)
    ad_res = bs_to_ad(bs_res.year, bs_res.month, bs_res.day)
    assert ad_res.year == 2020
    assert ad_res.month == 1
    assert ad_res.day == 1
    assert ad_res.formatted == "2020-01-01"


def test_devanagari_chart_labels():
    """Verify Sanskrit Devanagari nomenclature mapping."""
    labels = get_devanagari_chart_labels("Sun", "Aries")
    assert labels["planet_en"] == "Sun"
    assert labels["planet_ne"] == "सूर्य"
    assert labels["sign_en"] == "Aries"
    assert labels["sign_ne"] == "मेष"

    assert len(DEVANAGARI_NAKSHATRAS) == 27
    assert DEVANAGARI_NAKSHATRAS[0] == "अश्विनी"
    assert DEVANAGARI_NAKSHATRAS[26] == "रेवती"


def test_calendar_api_endpoints():
    """Verify FastAPI /calendar endpoints."""
    client = TestClient(app)

    # 1. /calendar/bs
    resp_bs = client.get("/calendar/bs", params={"year": 1997, "month": 5, "day": 22})
    assert resp_bs.status_code == 200
    data_bs = resp_bs.json()
    assert data_bs["year"] == 2054
    assert data_bs["month"] == 2
    assert data_bs["day"] == 9
    assert data_bs["formatted"] == "2054 Jestha 09"

    # 2. /calendar/ad
    resp_ad = client.get("/calendar/ad", params={"year": 2054, "month": 2, "day": 9})
    assert resp_ad.status_code == 200
    data_ad = resp_ad.json()
    assert data_ad["year"] == 1997
    assert data_ad["month"] == 5
    assert data_ad["day"] == 22

    # 3. /calendar/nomenclature
    resp_nom = client.get("/calendar/nomenclature")
    assert resp_nom.status_code == 200
    data_nom = resp_nom.json()
    assert "Sun" in data_nom["planets"]
    assert data_nom["planets"]["Sun"] == "सूर्य"
    assert "Aries" in data_nom["signs"]
    assert len(data_nom["nakshatras"]) == 27
