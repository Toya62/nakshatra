"""
Rate Limiting Middleware for Nakshatra API.

In-memory sliding-window counter rate limiter per client IP.
Configurable via RATE_LIMIT_PER_MINUTE env var (default: 60 rpm). Set to 0 to disable.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter per client IP."""

    def __init__(self, app: Any, requests_per_minute: int | None = None) -> None:
        super().__init__(app)
        if requests_per_minute is None:
            rpm_str = os.environ.get("RATE_LIMIT_PER_MINUTE", "60")
            try:
                self.rpm = int(rpm_str)
            except ValueError:
                self.rpm = 60
        else:
            self.rpm = requests_per_minute

        self._records: dict[str, list[float]] = defaultdict(list)
        self._exempt_paths = {"/health", "/docs", "/redoc", "/openapi.json", "/legal/licensing", "/privacy"}

    def _get_client_ip(self, request: Request) -> str:
        # Check forwarded headers first (behind Caddy / reverse proxy)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        return request.client.host if request.client else "127.0.0.1"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self.rpm <= 0 or request.url.path in self._exempt_paths:
            return await call_next(request)

        now = time.time()
        client_ip = self._get_client_ip(request)
        window_start = now - 60.0

        # Purge timestamps older than 60s
        timestamps = [t for t in self._records[client_ip] if t > window_start]
        self._records[client_ip] = timestamps

        if len(timestamps) >= self.rpm:
            retry_after = int(60.0 - (now - timestamps[0])) + 1
            headers = {
                "X-RateLimit-Limit": str(self.rpm),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(now + retry_after)),
                "Retry-After": str(max(1, retry_after)),
            }
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers=headers,
            )

        self._records[client_ip].append(now)
        remaining = max(0, self.rpm - len(self._records[client_ip]))
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rpm)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(now + 60))
        return response
