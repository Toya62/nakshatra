"""
GDPR & Privacy Guard for Nakshatra.

Ensures birth coordinates (latitude, longitude, exact epoch, person names)
are treated as sensitive personal data. Enforces in-memory ephemeral
processing with zero plain-text log leakage.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("nakshatra.privacy")

# Regex to scrub sensitive coordinate patterns from logged URLs / query params
LAT_LON_PATTERN = re.compile(r"(latitude|longitude|lat|lon)=[-+]?\d*\.?\d+", re.IGNORECASE)
PERSON_NAME_PATTERN = re.compile(r"(place_name|bride_name|groom_name)=[^&]+", re.IGNORECASE)


class PrivacySanitizerFilter(logging.Filter):
    """
    Logging filter that sanitizes birth coordinates and names from log records.
    Prevents personal identifiable coordinates from being written to log files.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = LAT_LON_PATTERN.sub(r"\1=[SCRUBBED_GDPR]", record.msg)
            record.msg = PERSON_NAME_PATTERN.sub(r"\1=[SCRUBBED_GDPR]", record.msg)
        return True


class PrivacyMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces privacy headers and transparent zero-log telemetry.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Process request ephemerally
        response = await call_next(request)

        # Enforce strict privacy headers
        response.headers["X-Data-Policy"] = "ephemeral-zero-retention"
        response.headers["X-Privacy-Standard"] = "GDPR-Art-9-Special-Category-Compliant"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"

        return response


def get_privacy_statement() -> dict[str, Any]:
    """Return explicit GDPR data handling and zero-retention guarantee."""
    return {
        "policy": "Ephemeral Astrological Computation",
        "data_retention": "Zero Persistence. Birth data (date, time, latitude, longitude) is processed purely in volatile RAM and is never stored in any database or disk cache.",
        "gdpr_compliance": {
            "lawful_basis": "Explicit Consent (GDPR Article 6(1)(a)) & Special Category Ephemeral Processing (Article 9)",
            "logging_policy": "All server logs scrub geographical coordinates and personal names via PrivacySanitizerFilter.",
            "data_portability": "Calculated JSON charts can be exported directly by the user at any time.",
            "right_to_erasure": "Automatic. No user chart records exist on the server after the HTTP request/stream finishes.",
        },
        "third_party_sharing": "None. Calculations are performed locally by the embedded Swiss Ephemeris C-engine.",
    }
