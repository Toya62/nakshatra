"""
Geocoding and Historical Timezone / DST Resolution Engine.

Resolves place names to geographical coordinates (latitude, longitude)
and IANA timezone identifiers, with exact astronomical and civil
daylight saving time (DST) offset calculation at the birth epoch.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PlaceResult(BaseModel):
    """Geocoded place with astronomical coordinates and IANA timezone."""

    name: str = Field(..., description="Full canonical place name")
    city: str = Field(..., description="City or district name")
    country: str = Field(..., description="Country name")
    latitude: float = Field(
        ..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (+ North)"
    )
    longitude: float = Field(
        ..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (+ East)"
    )
    timezone: str = Field(..., description="Standard IANA timezone string (e.g., 'Asia/Kathmandu')")
    elevation_m: float | None = Field(
        default=None, description="Elevation above sea level in meters"
    )


class TimezoneOffsetInfo(BaseModel):
    """Historical timezone offset and daylight saving status at a given epoch."""

    timezone: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    utc_offset_seconds: int = Field(..., description="Total seconds ahead/behind UTC")
    utc_offset_str: str = Field(
        ..., description="Formatted UTC offset string, e.g. '+05:45' or '+02:00'"
    )
    is_dst: bool = Field(..., description="True if Daylight Saving Time was active at this epoch")
    tz_abbreviation: str = Field(
        ..., description="Timezone abbreviation, e.g., 'NPT', 'IST', 'EDT', 'CEST'"
    )


# Curated offline database loaded from data file
try:
    from nakshatra.data.builtin_places import BUILTIN_PLACES
except ImportError:
    BUILTIN_PLACES: list[dict[str, Any]] = []

def search_places(query: str, limit: int = 8) -> list[PlaceResult]:
    """
    Search places matching query text.
    First checks instant local database of key spiritual and major centers.
    Falls back to online Nominatim lookup if query is unknown or few results.
    """
    q_norm = query.strip().lower()
    if not q_norm:
        return [
            PlaceResult(
                name=p["name"],
                city=p["city"],
                country=p["country"],
                latitude=p["lat"],
                longitude=p["lon"],
                timezone=p["tz"],
            )
            for p in BUILTIN_PLACES[:limit]
        ]

    # Filter local database
    matches: list[PlaceResult] = []
    for p in BUILTIN_PLACES:
        target = f"{p['name']} {p['city']} {p['country']}".lower()
        if q_norm in target:
            matches.append(
                PlaceResult(
                    name=p["name"],
                    city=p["city"],
                    country=p["country"],
                    latitude=p["lat"],
                    longitude=p["lon"],
                    timezone=p["tz"],
                )
            )
            if len(matches) >= limit:
                return matches

    # If local matches found, return them
    if matches:
        return matches

    # Fallback to online OpenStreetMap Nominatim geocoder
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit={limit}&addressdetails=1"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "NakshatraVedicAstrologyEngine/0.1.0"},
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data:
                lat = float(item["lat"])
                lon = float(item["lon"])
                addr = item.get("address", {})
                city = (
                    addr.get("city")
                    or addr.get("town")
                    or addr.get("village")
                    or item.get("name", query)
                )
                country = addr.get("country", "")
                tz_approx = _estimate_timezone_from_coords(lat, lon)
                matches.append(
                    PlaceResult(
                        name=item.get("display_name", query),
                        city=city,
                        country=country,
                        latitude=lat,
                        longitude=lon,
                        timezone=tz_approx,
                    )
                )
                if len(matches) >= limit:
                    break
    except Exception as e:
        logger.debug("Online geocoding fallback failed: %s", e)

    return matches


def _estimate_timezone_from_coords(lat: float, lon: float) -> str:
    """Approximate IANA timezone based on geographical coordinates if offline."""
    # Nepal & North India bounds
    if 26.0 <= lat <= 31.0 and 80.0 <= lon <= 88.5:
        # Check Nepal territory
        if 26.3 <= lat <= 30.5 and 80.0 <= lon <= 88.2:
            return "Asia/Kathmandu"
        return "Asia/Kolkata"
    # Myanmar territory (approx 9.5N - 28.5N, 92.2E - 101.2E)
    if 9.5 <= lat <= 28.5 and 92.2 <= lon <= 101.2:
        return "Asia/Yangon"
    if 8.0 <= lat <= 37.0 and 68.0 <= lon <= 97.0:
        return "Asia/Kolkata"
    if 47.0 <= lat <= 55.0 and 5.0 <= lon <= 15.0:
        return "Europe/Berlin"
    if 50.0 <= lat <= 60.0 and -8.0 <= lon <= 2.0:
        return "Europe/London"
    if 24.0 <= lat <= 50.0 and -125.0 <= lon <= -66.0:
        if lon > -85.0:
            return "America/New_York"
        if lon > -105.0:
            return "America/Chicago"
        return "America/Los_Angeles"
    return "UTC"


def resolve_timezone_offset(
    timezone: str,
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
) -> TimezoneOffsetInfo:
    """
    Resolve historical civil offset and daylight saving time (DST) status
    for an exact date and time in the specified IANA timezone.
    """
    tz = ZoneInfo(timezone)
    dt = datetime(year, month, day, hour, minute, tzinfo=tz)

    offset = dt.utcoffset()
    total_seconds = int(offset.total_seconds()) if offset is not None else 0

    sign = "+" if total_seconds >= 0 else "-"
    abs_sec = abs(total_seconds)
    hours = abs_sec // 3600
    minutes = (abs_sec % 3600) // 60
    offset_str = f"{sign}{hours:02d}:{minutes:02d}"

    dst = dt.dst()
    is_dst = dst is not None and dst.total_seconds() != 0
    tz_abbr = dt.tzname() or timezone

    return TimezoneOffsetInfo(
        timezone=timezone,
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        utc_offset_seconds=total_seconds,
        utc_offset_str=offset_str,
        is_dst=is_dst,
        tz_abbreviation=tz_abbr,
    )
