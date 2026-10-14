"""
Unit tests for geocoding and historical timezone/DST resolution engine.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from nakshatra.api import app
from nakshatra.geocoding import (
    PlaceResult,
    TimezoneOffsetInfo,
    resolve_timezone_offset,
    search_places,
)


def test_search_places_palpa():
    """Verify local search finds Palpa, Nepal accurately."""
    results = search_places("Palpa")
    assert len(results) > 0
    p = results[0]
    assert "Palpa" in p.name
    assert p.country == "Nepal"
    assert pytest.approx(p.latitude, abs=0.01) == 27.8667
    assert pytest.approx(p.longitude, abs=0.01) == 83.4833
    assert p.timezone == "Asia/Kathmandu"


def test_search_places_spiritual_centers():
    """Verify local search finds major Vedic spiritual centers."""
    varanasi = search_places("Varanasi")
    assert len(varanasi) > 0
    assert "India" in varanasi[0].country
    assert varanasi[0].timezone == "Asia/Kolkata"

    ujjain = search_places("Ujjain")
    assert len(ujjain) > 0
    assert pytest.approx(ujjain[0].latitude, abs=0.01) == 23.1765


def test_search_places_empty():
    """Empty query should return default major cities."""
    results = search_places("")
    assert len(results) > 0
    assert isinstance(results[0], PlaceResult)


def test_resolve_timezone_nepal_fixed_offset():
    """Nepal has a fixed +05:45 offset with no DST."""
    info = resolve_timezone_offset("Asia/Kathmandu", 1997, 5, 22, 4, 53)
    assert isinstance(info, TimezoneOffsetInfo)
    assert info.utc_offset_str == "+05:45"
    assert info.utc_offset_seconds == 20700
    assert not info.is_dst


def test_resolve_timezone_historical_dst_europe():
    """Verify European DST detection (Summer +02:00 vs Winter +01:00)."""
    # Summer epoch (July in Berlin)
    summer = resolve_timezone_offset("Europe/Berlin", 2026, 7, 15, 12, 0)
    assert summer.utc_offset_str == "+02:00"
    assert summer.is_dst
    assert summer.tz_abbreviation == "CEST"

    # Winter epoch (January in Berlin)
    winter = resolve_timezone_offset("Europe/Berlin", 2026, 1, 15, 12, 0)
    assert winter.utc_offset_str == "+01:00"
    assert not winter.is_dst
    assert winter.tz_abbreviation == "CET"


def test_api_geocode_endpoints():
    """Test FastAPI /geocode/search and /geocode/timezone HTTP endpoints."""
    client = TestClient(app)

    # Search endpoint
    res = client.get("/geocode/search?q=Kathmandu")
    assert res.status_code == 200
    items = res.json()
    assert len(items) > 0
    assert items[0]["city"] == "Kathmandu"
    assert items[0]["timezone"] == "Asia/Kathmandu"

    # Timezone endpoint
    res_tz = client.get(
        "/geocode/timezone?tz=Asia/Kathmandu&year=1997&month=5&day=22&hour=4&minute=53"
    )
    assert res_tz.status_code == 200
    tz_data = res_tz.json()
    assert tz_data["utc_offset_str"] == "+05:45"
    assert not tz_data["is_dst"]
