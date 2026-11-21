"""
Unit tests for Nakshatra Dual-System Remedies & Upayas Engine (Parashari + Lal Kitab).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from nakshatra.api import app
from nakshatra.core import BirthData, calculate_chart
from nakshatra.remedies import (
    AfflictionSeverity,
    PlanetRemedy,
    RemediesReport,
    calculate_remedies,
)


@pytest.fixture(scope="module")
def sample_chart():
    """Deterministic sample birth chart."""
    birth = BirthData(
        year=1990,
        month=5,
        day=15,
        hour=14,
        minute=30,
        latitude=40.7128,
        longitude=-74.0060,
        timezone="America/New_York",
        place_name="New York, NY",
    )
    return calculate_chart(birth)


@pytest.fixture
def client():
    return TestClient(app)


class TestRemediesEngine:
    """Test deterministic calculation of Parashari + Lal Kitab remedies."""

    def test_calculate_remedies_structure(self, sample_chart):
        report = calculate_remedies(sample_chart)
        assert isinstance(report, RemediesReport)
        assert report.natal_lagna is not None
        assert report.natal_moon is not None
        assert report.total_afflictions > 0
        assert len(report.afflicted_planets) > 0
        assert len(report.general_guidelines) >= 3
        assert len(report.lal_kitab_precautions) >= 3

    def test_afflicted_planet_fields(self, sample_chart):
        report = calculate_remedies(sample_chart)
        for p in report.afflicted_planets:
            assert isinstance(p, PlanetRemedy)
            assert p.planet in (
                "Sun",
                "Moon",
                "Mars",
                "Mercury",
                "Jupiter",
                "Venus",
                "Saturn",
                "Rahu",
                "Ketu",
            )
            assert 1 <= p.house <= 12
            assert len(p.affliction_reasons) > 0
            assert p.severity in AfflictionSeverity

            # Parashari fields
            par = p.parashari
            assert par.deity is not None
            assert "Om " in par.beej_mantra
            assert par.gemstone is not None
            assert par.metal is not None
            assert len(par.charity_items) > 0
            assert par.charity_day is not None
            assert par.fasting_day is not None

            # Lal Kitab fields
            lk = p.lal_kitab
            assert lk.household_remedy is not None
            assert lk.symbolic_action is not None
            assert len(lk.forbidden_actions) > 0
            assert lk.creature_service is not None
            assert lk.duration_days == 43

    def test_chart_get_remedies_method(self, sample_chart):
        report = sample_chart.get_remedies()
        assert isinstance(report, RemediesReport)
        assert report.total_afflictions == len(report.afflicted_planets)


class TestRemediesAPIEndpoint:
    """Test POST /remedies endpoint."""

    def test_post_remedies(self, client: TestClient):
        payload = {
            "year": 1990,
            "month": 5,
            "day": 15,
            "hour": 14,
            "minute": 30,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "timezone": "America/New_York",
            "include_transits": True,
        }
        r = client.post("/remedies", json=payload)
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        data = body["data"]
        assert "afflicted_planets" in data
        assert len(data["afflicted_planets"]) > 0
        assert "lal_kitab_precautions" in data
        assert "general_guidelines" in data
