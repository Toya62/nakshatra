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
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (+ North)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (+ East)")
    timezone: str = Field(..., description="Standard IANA timezone string (e.g., 'Asia/Kathmandu')")
    elevation_m: float | None = Field(default=None, description="Elevation above sea level in meters")


class TimezoneOffsetInfo(BaseModel):
    """Historical timezone offset and daylight saving status at a given epoch."""

    timezone: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    utc_offset_seconds: int = Field(..., description="Total seconds ahead/behind UTC")
    utc_offset_str: str = Field(..., description="Formatted UTC offset string, e.g. '+05:45' or '+02:00'")
    is_dst: bool = Field(..., description="True if Daylight Saving Time was active at this epoch")
    tz_abbreviation: str = Field(..., description="Timezone abbreviation, e.g., 'NPT', 'IST', 'EDT', 'CEST'")


# Curated offline database of major global cities & Vedic/South Asian centers
BUILTIN_PLACES: list[dict[str, Any]] = [
    # Nepal
    {"name": "Palpa (Tansen), Lumbini, Nepal", "city": "Palpa", "country": "Nepal", "lat": 27.8667, "lon": 83.4833, "tz": "Asia/Kathmandu"},
    {"name": "Kathmandu, Bagmati, Nepal", "city": "Kathmandu", "country": "Nepal", "lat": 27.7172, "lon": 85.3240, "tz": "Asia/Kathmandu"},
    {"name": "Pokhara, Gandaki, Nepal", "city": "Pokhara", "country": "Nepal", "lat": 28.2096, "lon": 83.9856, "tz": "Asia/Kathmandu"},
    {"name": "Lalitpur (Patan), Bagmati, Nepal", "city": "Lalitpur", "country": "Nepal", "lat": 27.6710, "lon": 85.3216, "tz": "Asia/Kathmandu"},
    {"name": "Bhaktapur, Bagmati, Nepal", "city": "Bhaktapur", "country": "Nepal", "lat": 27.6710, "lon": 85.4298, "tz": "Asia/Kathmandu"},
    {"name": "Lumbini, Rupandehi, Nepal", "city": "Lumbini", "country": "Nepal", "lat": 27.4833, "lon": 83.2833, "tz": "Asia/Kathmandu"},
    {"name": "Janakpur, Madhesh, Nepal", "city": "Janakpur", "country": "Nepal", "lat": 26.7271, "lon": 85.9238, "tz": "Asia/Kathmandu"},
    {"name": "Biratnagar, Koshi, Nepal", "city": "Biratnagar", "country": "Nepal", "lat": 26.4525, "lon": 87.2718, "tz": "Asia/Kathmandu"},
    {"name": "Chitwan (Bharatpur), Bagmati, Nepal", "city": "Bharatpur", "country": "Nepal", "lat": 27.6833, "lon": 84.4333, "tz": "Asia/Kathmandu"},
    {"name": "Dharana, Koshi, Nepal", "city": "Dharan", "country": "Nepal", "lat": 26.8124, "lon": 87.2835, "tz": "Asia/Kathmandu"},
    {"name": "Butwal, Lumbini, Nepal", "city": "Butwal", "country": "Nepal", "lat": 27.7006, "lon": 83.4484, "tz": "Asia/Kathmandu"},
    {"name": "Nepalgunj, Banke, Nepal", "city": "Nepalgunj", "country": "Nepal", "lat": 28.0500, "lon": 81.6167, "tz": "Asia/Kathmandu"},
    {"name": "Muktinath, Mustang, Nepal", "city": "Muktinath", "country": "Nepal", "lat": 28.8167, "lon": 83.8667, "tz": "Asia/Kathmandu"},

    # India (Spiritual & Metros)
    {"name": "Varanasi (Kashi), Uttar Pradesh, India", "city": "Varanasi", "country": "India", "lat": 25.3176, "lon": 82.9739, "tz": "Asia/Kolkata"},
    {"name": "Ujjain (Mahakaleshwar), Madhya Pradesh, India", "city": "Ujjain", "country": "India", "lat": 23.1765, "lon": 75.7885, "tz": "Asia/Kolkata"},
    {"name": "Haridwar, Uttarakhand, India", "city": "Haridwar", "country": "India", "lat": 29.9457, "lon": 78.1642, "tz": "Asia/Kolkata"},
    {"name": "Rishikesh, Uttarakhand, India", "city": "Rishikesh", "country": "India", "lat": 30.0869, "lon": 78.2676, "tz": "Asia/Kolkata"},
    {"name": "Ayodhya, Uttar Pradesh, India", "city": "Ayodhya", "country": "India", "lat": 26.7922, "lon": 82.1998, "tz": "Asia/Kolkata"},
    {"name": "Mathura, Uttar Pradesh, India", "city": "Mathura", "country": "India", "lat": 27.4924, "lon": 77.6737, "tz": "Asia/Kolkata"},
    {"name": "Vrindavan, Uttar Pradesh, India", "city": "Vrindavan", "country": "India", "lat": 27.5806, "lon": 77.7006, "tz": "Asia/Kolkata"},
    {"name": "Puri (Jagannath), Odisha, India", "city": "Puri", "country": "India", "lat": 19.8135, "lon": 85.8312, "tz": "Asia/Kolkata"},
    {"name": "Tirupati, Andhra Pradesh, India", "city": "Tirupati", "country": "India", "lat": 13.6288, "lon": 79.4192, "tz": "Asia/Kolkata"},
    {"name": "Rameswaram, Tamil Nadu, India", "city": "Rameswaram", "country": "India", "lat": 9.2876, "lon": 79.3129, "tz": "Asia/Kolkata"},
    {"name": "New Delhi, Delhi, India", "city": "New Delhi", "country": "India", "lat": 28.6139, "lon": 77.2090, "tz": "Asia/Kolkata"},
    {"name": "Mumbai, Maharashtra, India", "city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "tz": "Asia/Kolkata"},
    {"name": "Bengaluru (Bangalore), Karnataka, India", "city": "Bengaluru", "country": "India", "lat": 12.9716, "lon": 77.5946, "tz": "Asia/Kolkata"},
    {"name": "Chennai (Madras), Tamil Nadu, India", "city": "Chennai", "country": "India", "lat": 13.0827, "lon": 80.2707, "tz": "Asia/Kolkata"},
    {"name": "Kolkata (Calcutta), West Bengal, India", "city": "Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3639, "tz": "Asia/Kolkata"},
    {"name": "Hyderabad, Telangana, India", "city": "Hyderabad", "country": "India", "lat": 17.3850, "lon": 78.4867, "tz": "Asia/Kolkata"},
    {"name": "Pune, Maharashtra, India", "city": "Pune", "country": "India", "lat": 18.5204, "lon": 73.8567, "tz": "Asia/Kolkata"},
    {"name": "Ahmedabad, Gujarat, India", "city": "Ahmedabad", "country": "India", "lat": 23.0225, "lon": 72.5714, "tz": "Asia/Kolkata"},
    {"name": "Jaipur, Rajasthan, India", "city": "Jaipur", "country": "India", "lat": 26.9124, "lon": 75.7873, "tz": "Asia/Kolkata"},
    {"name": "Lucknow, Uttar Pradesh, India", "city": "Lucknow", "country": "India", "lat": 26.8467, "lon": 80.9462, "tz": "Asia/Kolkata"},

    # Europe
    {"name": "London, England, United Kingdom", "city": "London", "country": "United Kingdom", "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London"},
    {"name": "Berlin, Germany", "city": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050, "tz": "Europe/Berlin"},
    {"name": "Munich, Bavaria, Germany", "city": "Munich", "country": "Germany", "lat": 48.1351, "lon": 11.5820, "tz": "Europe/Berlin"},
    {"name": "Frankfurt, Hesse, Germany", "city": "Frankfurt", "country": "Germany", "lat": 50.1109, "lon": 8.6821, "tz": "Europe/Berlin"},
    {"name": "Paris, Île-de-France, France", "city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "tz": "Europe/Paris"},
    {"name": "Zurich, Switzerland", "city": "Zurich", "country": "Switzerland", "lat": 47.3769, "lon": 8.5417, "tz": "Europe/Zurich"},
    {"name": "Vienna, Austria", "city": "Vienna", "country": "Austria", "lat": 48.2082, "lon": 16.3738, "tz": "Europe/Vienna"},
    {"name": "Rome, Lazio, Italy", "city": "Rome", "country": "Italy", "lat": 41.9028, "lon": 12.4964, "tz": "Europe/Rome"},
    {"name": "Amsterdam, North Holland, Netherlands", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041, "tz": "Europe/Amsterdam"},
    {"name": "Madrid, Spain", "city": "Madrid", "country": "Spain", "lat": 40.4168, "lon": -3.7038, "tz": "Europe/Madrid"},

    # North America
    {"name": "New York City, New York, USA", "city": "New York", "country": "USA", "lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"},
    {"name": "San Francisco, California, USA", "city": "San Francisco", "country": "USA", "lat": 37.7749, "lon": -122.4194, "tz": "America/Los_Angeles"},
    {"name": "Los Angeles, California, USA", "city": "Los Angeles", "country": "USA", "lat": 34.0522, "lon": -118.2437, "tz": "America/Los_Angeles"},
    {"name": "Chicago, Illinois, USA", "city": "Chicago", "country": "USA", "lat": 41.8781, "lon": -87.6298, "tz": "America/Chicago"},
    {"name": "Houston, Texas, USA", "city": "Houston", "country": "USA", "lat": 29.7604, "lon": -95.3698, "tz": "America/Chicago"},
    {"name": "Toronto, Ontario, Canada", "city": "Toronto", "country": "Canada", "lat": 43.6532, "lon": -79.3832, "tz": "America/Toronto"},
    {"name": "Vancouver, British Columbia, Canada", "city": "Vancouver", "country": "Canada", "lat": 49.2827, "lon": -123.1207, "tz": "America/Vancouver"},

    # Asia & Oceania
    {"name": "Tokyo, Japan", "city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "tz": "Asia/Tokyo"},
    {"name": "Singapore, Singapore", "city": "Singapore", "country": "Singapore", "lat": 1.3521, "lon": 103.8198, "tz": "Asia/Singapore"},
    {"name": "Dubai, United Arab Emirates", "city": "Dubai", "country": "United Arab Emirates", "lat": 25.2048, "lon": 55.2708, "tz": "Asia/Dubai"},
    {"name": "Bangkok, Thailand", "city": "Bangkok", "country": "Thailand", "lat": 13.7563, "lon": 100.5018, "tz": "Asia/Bangkok"},
    {"name": "Sydney, New South Wales, Australia", "city": "Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "tz": "Australia/Sydney"},
    {"name": "Melbourne, Victoria, Australia", "city": "Melbourne", "country": "Australia", "lat": -37.8136, "lon": 144.9631, "tz": "Australia/Melbourne"},
]


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
                city = addr.get("city") or addr.get("town") or addr.get("village") or item.get("name", query)
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
