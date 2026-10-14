"""
Unit tests for GDPR privacy guard, zero-log middleware, and privacy policy endpoint.
"""

from __future__ import annotations

import logging

from fastapi.testclient import TestClient

from nakshatra.api import app
from nakshatra.privacy import (
    PrivacySanitizerFilter,
    get_privacy_statement,
)


def test_get_privacy_statement():
    """Verify privacy statement documents GDPR compliance and zero retention."""
    stmt = get_privacy_statement()
    assert "policy" in stmt
    assert "Zero Persistence" in stmt["data_retention"]
    assert "GDPR" in stmt["gdpr_compliance"]["lawful_basis"]


def test_privacy_sanitizer_filter():
    """Verify logger filter scrubs coordinates and names from log records."""
    log_filter = PrivacySanitizerFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="GET /chart?latitude=27.8667&longitude=83.4833&place_name=Palpa HTTP/1.1",
        args=(),
        exc_info=None,
    )
    result = log_filter.filter(record)
    assert result is True
    assert "27.8667" not in record.msg
    assert "83.4833" not in record.msg
    assert "[SCRUBBED_GDPR]" in record.msg


def test_privacy_endpoint_and_headers():
    """Verify /privacy endpoint and automatic GDPR privacy response headers."""
    client = TestClient(app)

    res = client.get("/privacy")
    assert res.status_code == 200
    data = res.json()
    assert "Zero Persistence" in data["data_retention"]

    # Verify security & privacy headers injected by PrivacyMiddleware
    assert res.headers.get("x-data-policy") == "ephemeral-zero-retention"
    assert "GDPR" in res.headers.get("x-privacy-standard", "")
    assert res.headers.get("referrer-policy") == "no-referrer"
    assert "no-store" in res.headers.get("cache-control", "")
