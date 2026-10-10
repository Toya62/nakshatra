"""
API integration tests for Nakshatra FastAPI endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from nakshatra.api import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def chart_payload() -> dict:
    return {
        "year": 1997,
        "month": 5,
        "day": 22,
        "hour": 4,
        "minute": 53,
        "second": 0,
        "latitude": 27.8667,
        "longitude": 83.4833,
        "timezone": "Asia/Kathmandu",
        "place_name": "Palpa, Nepal",
    }


class TestChartEndpoint:
    """Tests for POST/GET /chart endpoints."""

    def test_post_chart_json_default(self, client: TestClient, chart_payload: dict):
        r = client.post("/chart", json=chart_payload)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")
        body = r.json()
        assert body["success"] is True
        data = body["data"]
        assert data["ayanamsa"] == "jhora_lahiri"
        assert data["house_system"] == "WholeSign"
        assert data["zodiac"] == "sidereal"
        assert len(data["planets"]) == 7
        assert data["ascendant"]["sign"] == "Aries"
        assert body["meta"]["ayanamsa_used"] == "jhora_lahiri"

    def test_post_chart_format_table(self, client: TestClient, chart_payload: dict):
        r = client.post("/chart?format=table", json=chart_payload)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/plain")
        assert "NAKSHATRA VEDIC BIRTH CHART" in r.text
        assert "PLANETARY POSITIONS" in r.text
        assert "VIMSHOTTARI DASHA" in r.text

    def test_post_chart_format_markdown(self, client: TestClient, chart_payload: dict):
        r = client.post("/chart?format=markdown", json=chart_payload)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/markdown")
        assert "# Nakshatra Vedic Birth Chart" in r.text
        assert "| Planet | Sign | Degree |" in r.text

    def test_post_chart_format_csv(self, client: TestClient, chart_payload: dict):
        r = client.post("/chart?format=csv", json=chart_payload)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/csv")
        assert r.text.startswith("Body,Sign,Degree_In_Sign")
        assert "Ascendant,Aries" in r.text

    def test_post_chart_format_diagram(self, client: TestClient, chart_payload: dict):
        r = client.post("/chart?format=diagram", json=chart_payload)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/plain")
        assert "NAKSHATRA VEDIC D1" in r.text
        assert "Asc" in r.text

    def test_post_chart_invalid_format(self, client: TestClient, chart_payload: dict):
        r = client.post("/chart?format=bogus", json=chart_payload)
        assert r.status_code == 422

    def test_get_chart_json(self, client: TestClient, chart_payload: dict):
        r = client.get("/chart", params=chart_payload)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")
        assert r.json()["data"]["ascendant"]["sign"] == "Aries"

    def test_get_chart_format_table(self, client: TestClient, chart_payload: dict):
        r = client.get("/chart", params={**chart_payload, "format": "table"})
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/plain")
        assert "NAKSHATRA VEDIC BIRTH CHART" in r.text

    def test_get_chart_invalid_format(self, client: TestClient, chart_payload: dict):
        r = client.get("/chart", params={**chart_payload, "format": "xml"})
        assert r.status_code == 422

    def test_chart_request_validation(self, client: TestClient, chart_payload: dict):
        bad = {**chart_payload, "month": 13}
        r = client.post("/chart", json=bad)
        assert r.status_code == 422


class TestChartDiagramEndpoint:
    """Tests for GET /chart/diagram."""

    def test_diagram_d1(self, client: TestClient, chart_payload: dict):
        r = client.get("/chart/diagram", params=chart_payload)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/plain")
        assert "NAKSHATRA VEDIC D1" in r.text

    def test_diagram_d9(self, client: TestClient, chart_payload: dict):
        r = client.get("/chart/diagram", params={**chart_payload, "varga": "D9"})
        assert r.status_code == 200
        assert "NAKSHATRA VEDIC D9" in r.text

    def test_diagram_d10(self, client: TestClient, chart_payload: dict):
        r = client.get("/chart/diagram", params={**chart_payload, "varga": "D10"})
        assert r.status_code == 200
        assert "NAKSHATRA VEDIC D10" in r.text


class TestTransitsEndpoint:
    """Tests for POST /transits."""

    def test_transits_with_date(self, client: TestClient, chart_payload: dict):
        payload = {**chart_payload, "transit_date": "2026-10-10T12:00:00"}
        r = client.post("/transits", json=payload)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")
        body = r.json()
        assert body["success"] is True
        data = body["data"]
        assert data["natal_lagna_sign"] == "Aries"
        assert data["natal_moon_sign"] == "Scorpio"
        assert data["ayanamsa"] == "jhora_lahiri"
        assert len(data["planets"]) == 9
        assert data["jupiter_gochar"]["sign"] == "Cancer"
        assert "sade_sati" in data
        assert "jupiter_gochar" in data
        assert "double_transit_houses" in data

    def test_transits_default_now(self, client: TestClient, chart_payload: dict):
        r = client.post("/transits", json=chart_payload)
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data["planets"]) == 9
        # transit_time should be populated (current time)
        assert data["transit_time"]

    def test_transits_with_location(self, client: TestClient, chart_payload: dict):
        payload = {
            **chart_payload,
            "transit_date": "2026-12-25T00:00:00",
            "transit_latitude": 40.7128,
            "transit_longitude": -74.0060,
        }
        r = client.post("/transits", json=payload)
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data["planets"]) == 9

    def test_transits_sade_sati_structure(self, client: TestClient, chart_payload: dict):
        payload = {**chart_payload, "transit_date": "2026-10-10T12:00:00"}
        r = client.post("/transits", json=payload)
        ss = r.json()["data"]["sade_sati"]
        assert isinstance(ss["is_active"], bool)
        assert ss["natal_moon_sign"] == "Scorpio"
        assert ss["saturn_sign"] == "Pisces"
        assert 1 <= ss["house_from_moon"] <= 12

    def test_transits_transit_planet_fields(self, client: TestClient, chart_payload: dict):
        payload = {**chart_payload, "transit_date": "2026-10-10T12:00:00"}
        r = client.post("/transits", json=payload)
        planets = r.json()["data"]["planets"]
        names = [p["name"] for p in planets]
        assert names == [
            "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
        ]
        for p in planets:
            assert 1 <= p["house_from_lagna"] <= 12
            assert 1 <= p["house_from_moon"] <= 12
            assert isinstance(p["is_favorable_gochar"], bool)

    def test_transits_request_validation(self, client: TestClient, chart_payload: dict):
        bad = {**chart_payload, "latitude": 120.0}
        r = client.post("/transits", json=bad)
        assert r.status_code == 422


class TestPanchangaEndpoints:
    """Tests for GET/POST /panchanga endpoints."""

    def test_get_panchanga_json(self, client: TestClient, chart_payload: dict):
        r = client.get("/panchanga", params=chart_payload)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")
        body = r.json()
        assert body["success"] is True
        p = body["data"]
        assert p["vara"]["name"] == "Budhavara (Wednesday)"
        assert p["vara"]["lord"] == "Mercury"
        assert p["tithi"]["name"] == "Purnima"
        assert p["tithi"]["lord"] == "Saturn"
        assert "Vishakha" in p["nakshatra"]["name"]
        assert p["yoga"]["name"] == "Parigha"
        assert p["karana"]["name"] == "Bava"

    def test_get_panchanga_table(self, client: TestClient, chart_payload: dict):
        r = client.get("/panchanga", params={**chart_payload, "format": "table"})
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/plain")
        assert "VEDIC PANCHANGA REPORT" in r.text
        assert "1. VARA" in r.text
        assert "2. TITHI" in r.text

    def test_post_panchanga_json(self, client: TestClient, chart_payload: dict):
        r = client.post("/panchanga", json=chart_payload)
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["data"]["tithi"]["name"] == "Purnima"

    def test_post_panchanga_table(self, client: TestClient, chart_payload: dict):
        r = client.post("/panchanga?format=table", json=chart_payload)
        assert r.status_code == 200
        assert "VEDIC PANCHANGA REPORT" in r.text


class TestYogaEndpoints:
    """Tests for GET/POST /yogas endpoints."""

    def test_get_yogas_json(self, client: TestClient, chart_payload: dict):
        r = client.get("/yogas", params=chart_payload)
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["total"] > 0
        names = [y["name"] for y in body["data"]]
        assert any("Neechabhanga Raja Yoga" in n for n in names)
        assert any("Kemadruma Bhanga" in n for n in names)

    def test_get_yogas_table(self, client: TestClient, chart_payload: dict):
        r = client.get("/yogas", params={**chart_payload, "format": "table"})
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/plain")
        assert "VEDIC YOGA DETECTION REPORT" in r.text

    def test_post_yogas_markdown(self, client: TestClient, chart_payload: dict):
        r = client.post("/yogas?format=markdown", json=chart_payload)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/markdown")
        assert "# Vedic Yoga Detection Report" in r.text

    def test_post_yogas_json(self, client: TestClient, chart_payload: dict):
        r = client.post("/yogas", json=chart_payload)
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["total"] > 0


class TestSystemEndpoints:
    """Tests for /health and / endpoints."""

    def test_health(self, client: TestClient):
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert "Swiss Ephemeris" in body["ephemeris"]

    def test_root(self, client: TestClient):
        r = client.get("/")
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "Nakshatra"
        assert "POST /transits" in body["endpoints"]
        assert "GET /panchanga" in body["endpoints"]
        assert "GET /yogas" in body["endpoints"]

