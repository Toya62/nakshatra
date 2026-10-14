"""Tests for licensing, Swiss Ephemeris disclosures, and corpus attributions."""

from fastapi.testclient import TestClient

from nakshatra.api import app
from nakshatra.licensing import get_licensing_statement


def test_get_licensing_statement():
    """Verify licensing disclosures and Swiss Ephemeris AGPL terms."""
    stmt = get_licensing_statement()
    assert stmt["platform_license"] == "GNU Affero General Public License v3.0 (AGPL-3.0)"
    assert "Swiss Ephemeris" in stmt["ephemeris"]["engine"]
    assert "AGPL-3.0" in stmt["ephemeris"]["dual_license"]
    assert "Astrodienst AG" in stmt["ephemeris"]["details"]
    assert len(stmt["corpus_works"]) >= 2
    assert any("BPHS" in w["work"] for w in stmt["corpus_works"])


def test_licensing_endpoint():
    """Verify GET /legal/licensing returns 200 OK with compliant metadata."""
    client = TestClient(app)
    resp = client.get("/legal/licensing")
    assert resp.status_code == 200
    data = resp.json()
    assert "ephemeris" in data
    assert data["ephemeris"]["python_binding"] == "pyswisseph"
