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

    def test_all_108_lal_kitab_combinations(self):
        """Verify all 108 (9 planets x 12 houses) Lal Kitab remedies are populated."""
        from nakshatra.remedies import _get_lal_kitab_upaya

        planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        for p in planets:
            for h in range(1, 13):
                upaya = _get_lal_kitab_upaya(p, h)
                assert upaya.household_remedy, f"Missing household remedy for {p} in house {h}"
                assert upaya.symbolic_action, f"Missing symbolic action for {p} in house {h}"
                assert len(upaya.forbidden_actions) >= 2, f"Insufficient precautions for {p} in house {h}"
                assert upaya.creature_service, f"Missing creature service for {p} in house {h}"
                assert upaya.duration_days == 43


    def test_no_after_sunset_in_lal_kitab_actions(self):
        """Lal Kitab ACTION fields must never prescribe evening/night acts.

        The page's own Golden Rule says all Lal Kitab upayas are daytime
        only, yet the data used to prescribe "after sunset" and "Saturday
        evening" feedings. Prohibitions in ``forbidden`` lists are exempt —
        forbidding a night act does not prescribe one.
        """
        from nakshatra.lal_kitab_data import LAL_KITAB_108_UPAYAS

        assert len(LAL_KITAB_108_UPAYAS) == 108
        for (planet, house), entry in LAL_KITAB_108_UPAYAS.items():
            for field in ("household", "symbolic", "creature"):
                text = entry[field].lower()
                assert "after sunset" not in text, f"{planet} H{house} {field}: {entry[field]}"
                assert "saturday evening" not in text, f"{planet} H{house} {field}: {entry[field]}"

    def test_exalted_planet_keeps_transit_remedy_but_no_gemstone(self):
        """Live example: exalted Saturn in Libra H7 gets a High remedy only
        because of Ashtama Shani transit pressure — and no gemstone.

        The old Golden Rule ("Never Remedy Exalted Grahas") was absolute
        while the engine prescribed the card anyway. The rule now covers
        strengthening only: the card stays (transit propitiation is
        legitimate) but the gemstone is withheld.
        """
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
        report = calculate_remedies(calculate_chart(birth))
        saturn = next(p for p in report.afflicted_planets if p.planet == "Saturn")
        assert saturn.dignity == "exalted"
        assert saturn.severity == AfflictionSeverity.HIGH
        assert saturn.affliction_reasons == [
            "Saturn Gochar pressure: ASHTAMA SHANI ACTIVE - Saturn in 8th from Moon (Pisces)"
        ]
        assert "Not prescribed" in saturn.parashari.gemstone
        assert "Blue Sapphire" in saturn.parashari.gemstone
        assert "Not prescribed" in saturn.parashari.substitute_gem
        # And the creature service is daytime now.
        assert saturn.lal_kitab.creature_service == (
            "Feed black crows and street dogs on Saturday mornings."
        )


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
