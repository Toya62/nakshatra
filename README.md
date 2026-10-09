# Nakshatra - Vedic Astrology AI Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Built on openephem](https://img.shields.io/badge/ephemeris-JPL%20DE440%2FDE441-green.svg)](https://github.com/NoahChristian/openephem)

**Nakshatra** (नक्षत्र) — modern, MIT-licensed Vedic astrology calculation engine that provides accurate birth charts as JSON via FastAPI REST API or CLI. Built on NASA JPL ephemeris (DE440/DE441) via Skyfield/openephem — no Swiss Ephemeris licensing concerns.

## Features

- **Accurate Calculations**: NASA JPL DE440/DE441 ephemeris via Skyfield (validated to arcseconds)
- **MIT Licensed**: No AGPL/copyleft restrictions — use freely in commercial products
- **Default Lahiri Ayanamsa**: Chitra Paksha (official Indian government standard)
- **Traditional Vedic Defaults**: Whole Sign houses, sidereal zodiac
- **Complete Chart Data**: 9 grahas + Ascendant + Midheaven + Rahu/Ketu with sign, degree, nakshatra, pada, house, dignity, retrograde
- **12 Houses**: Whole Sign from Ascendant
- **Major Aspects**: Conjunction, sextile, square, trine, opposition with orbs
- **Multiple Ayanamsas**: Lahiri, Raman, Krishnamurti (KP), Fagan-Bradley
- **Multiple House Systems**: Whole Sign, Placidus, Koch, Regiomontanus, Campanus, Equal, Porphyry
- **REST API**: FastAPI with interactive Swagger docs at `/docs`
- **CLI**: Command-line tool for quick calculations
- **AI-Ready**: Structured JSON output designed for LLM consumption

## Quick Start

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/nakshatra.git
cd nakshatra

# Install with pip
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### Run API Server

```bash
# Start server
nakshatra-api
# or
uvicorn nakshatra.api:app --reload

# Visit http://localhost:8000/docs for interactive API docs
```

### Calculate Chart via API

```bash
curl -X POST http://localhost:8000/chart \
  -H "Content-Type: application/json" \
  -d '{
    "year": 1990,
    "month": 5,
    "day": 15,
    "hour": 14,
    "minute": 30,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "timezone": "America/New_York",
    "place_name": "New York, NY"
  }'
```

### Calculate Chart via CLI

```bash
# Basic usage
nakshatra --dob 1990-05-15 --time 14:30 --lat 40.7128 --lon -74.0060 --tz America/New_York

# With place name
nakshatra --dob 1990-05-15 --time 14:30 --lat 12.9716 --lon 77.5946 --tz Asia/Kolkata --place "Bangalore, India"

# Different ayanamsa
nakshatra --dob 1990-05-15 --time 14:30 --lat 40.7128 --lon -74.0060 --tz America/New_York --ayanamsa raman

# Save to file
nakshatra --dob 1990-05-15 --time 14:30 --lat 40.7128 --lon -74.0060 --tz America/New_York -o chart.json
```

### Python Library Usage

```python
from nakshatra import BirthData, calculate_chart, Ayanamsa, HouseSystem

birth = BirthData(
    year=1990, month=5, day=15, hour=14, minute=30,
    latitude=40.7128, longitude=-74.0060,
    timezone="America/New_York",
    place_name="New York, NY"
)

chart = calculate_chart(
    birth=birth,
    ayanamsa=Ayanamsa.LAHIRI,      # Default
    house_system=HouseSystem.WHOLE_SIGN  # Default
)

# Get JSON
json_output = chart.to_json()
print(json_output)

# Or as dict
chart_dict = chart.to_dict()
print(chart_dict["planets"][0]["name"])  # "Sun"
print(chart_dict["planets"][0]["nakshatra"])  # "Krittika"
print(chart_dict["ascendant"]["sign"])  # "Leo"
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info and links |
| GET | `/health` | Health check |
| POST | `/chart` | Calculate chart (JSON body) |
| GET | `/chart` | Calculate chart (query params) |
| GET | `/docs` | Interactive Swagger UI |

## Chart Output Structure

```json
{
  "birth_data": {...},
  "calculation_time": "2026-01-15T10:30:00Z",
  "zodiac": "sidereal",
  "ayanamsa": "lahiri",
  "house_system": "whole_sign",
  "planets": [
    {
      "name": "Sun",
      "longitude": 30.123456,
      "latitude": 0.0,
      "distance": 1.000123,
      "speed": 0.987654,
      "sign": "Taurus",
      "sign_lord": "Venus",
      "degree_in_sign": 0.123456,
      "nakshatra": "Krittika",
      "nakshatra_lord": "Sun",
      "pada": 1,
      "house": 2,
      "retrograde": false,
      "dignity": "neutral"
    }
    // ... Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu
  ],
  "houses": [
    {"house": 1, "longitude": 120.0, "sign": "Leo", "degree_in_sign": 0.0},
    // ... 12 houses
  ],
  "aspects": [
    {"planet1": "Sun", "planet2": "Moon", "aspect_type": "trine", "orb": 1.23, "applying": true, "exact_degree": 120.0}
  ],
  "ascendant": {...},
  "midheaven": {...},
  "rahu": {...},
  "ketu": {...}
}
```

## Ayanamsa Options

| Ayanamsa | Description |
|----------|-------------|
| `lahiri` | **Default** - Chitra Paksha (Spica-based), official Indian standard |
| `raman` | B.V. Raman's ayanamsa |
| `krishnamurti` | K.P. (Krishnamurti Paddhati) ayanamsa |
| `fagan-bradley` | Western sidereal standard |

## House System Options

| System | Description |
|--------|-------------|
| `whole_sign` | **Default** - Traditional Vedic, each sign = one house |
| `placidus` | Popular Western system |
| `koch` | Koch houses |
| `regiomontanus` | Regiomontanus houses |
| `campanus` | Campanus houses |
| `equal` | Equal houses from Ascendant |
| `porphyry` | Porphyry houses |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Nakshatra API                          │
│  FastAPI → nakshatra.core.calculate_chart() → ChartData    │
├─────────────────────────────────────────────────────────────┤
│  openephem (MIT)                                            │
│    ├─ Skyfield (MIT) → JPL DE440/DE441 (NASA public domain)│
│    ├─ IAU 2006/2000A precession/nutation (ERFA)           │
│    └─ IANA timezone database (public domain)               │
└─────────────────────────────────────────────────────────────┘
```

## Why Nakshatra?

| Factor | Swiss Ephemeris libs | Nakshatra (openephem) |
|--------|---------------------|----------------------|
| License | AGPL (viral) / Commercial | **MIT (permissive)** |
| Ephemeris | VSOP87/JPL (proprietary files) | **JPL DE440/441 (NASA public domain)** |
| Deployment | Requires `.se1` file management | **Auto-downloads & caches** |
| AI/ML Integration | Manual JSON conversion | **Built-in Pydantic models** |
| Commercial SaaS | Requires source disclosure | **No restrictions** |

## Development

```bash
# Run tests
pytest

# Lint
ruff check .

# Type check
mypy nakshatra

# Format
ruff format .
```

## Roadmap

- [ ] Dasha systems (Vimshottari, Yogini, Ashtottari)
- [ ] Divisional charts (D2–D60 / Shodashavarga)
- [ ] Yoga detection (Pancha Mahapurusha, Raja, Dhana, etc.)
- [ ] Ashtakavarga & Shadbala calculations
- [ ] Transit calculations
- [ ] Muhurta / electional astrology
- [ ] Panchanga (tithi, nakshatra, yoga, karana, vara)
- [ ] SVG chart rendering
- [ ] AI interpretation layer (LLM prompt templates)

## License

MIT License — see [LICENSE](LICENSE) for details.

**Ephemeris Data**: JPL DE440/DE441 (NASA public domain), IAU standards (ERFA/IAU SOFA), IANA tzdata (public domain). No Swiss Ephemeris code or data included.

## Acknowledgments

- [openephem](https://github.com/NoahChristian/openephem) — permissive ephemeris engine validated against Swiss Ephemeris
- [Skyfield](https://rhodesmill.org/skyfield/) — elegant astronomy for Python
- [JPL](https://ssd.jpl.nasa.gov/) — NASA Jet Propulsion Laboratory ephemerides
- [ERFA](https://github.com/liberfa/erfa) — Essential Routines for Fundamental Astronomy