# Nakshatra - Vedic Astrology AI Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Engine: Swiss Ephemeris](https://img.shields.io/badge/engine-Swiss%20Ephemeris-blue.svg)](https://www.astro.com/swisseph/)

**Nakshatra** (नक्षत्र) is a high-precision Vedic astrology calculation engine providing birth charts, Vimshottari dashas, divisional charts, Ashtakavarga, and Shadbala as structured JSON via FastAPI REST API, CLI, and Python library. Powered by **Swiss Ephemeris** (`pyswisseph`) through `mayaastrolib` for sub-second, arcsecond-level astronomical accuracy.

---

## Features

- **Accurate Astronomical Engine**: Swiss Ephemeris (`pyswisseph`) backend with true planetary velocities and retrograde indicators.
- **Complete Birth Chart Data**: 9 Grahas (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu) + Ascendant + Midheaven with sign, degree, nakshatra, pada, house, dignity, and retrograde state.
- **Multiple Ayanamsas**:
  - `lahiri`: Astronomical Chitra Paksha (official Indian standard, default).
  - `jhora_lahiri`: Traditional Lahiri calibrated for 100% concordance with Jagannatha Hora.
  - `raman`: B.V. Raman's ayanamsa.
  - `krishnamurti`: K.P. (Krishnamurti Paddhati) ayanamsa.
  - `fagan_bradley`: Western sidereal standard.
- **Multiple House Systems**: Whole Sign (traditional Vedic default), Placidus, Koch, Regiomontanus, Campanus, Equal, Porphyry.
- **Vimshottari Dashas**:
  - Birth balance calculation down to fractional years.
  - Full 120-year sequence of Mahadashas (MD).
  - Nested Antardashas (AD) and Pratyantardashas (PD) down to the exact second (`YYYY-MM-DD HH:MM:SS`).
  - Active current period lookup (`current_md`, `current_ad`, `current_pd`).
- **Shodashavarga (Divisional Charts)**:
  - All 16 vargas: D1 (Rasi), D2 (Hora), D3 (Drekkana), D4 (Chaturthamsa), D7 (Saptamsa), D9 (Navamsa), D10 (Dasamsa), D12 (Dvadasamsa), D16 (Shodasamsa), D20 (Vimsamsa), D24 (Chaturvimsamsa), D27 (Bhamsa), D30 (Trimsamsa), D40 (Khavedamsa), D45 (Akshavedamsa), D60 (Shastiamsa).
- **Ashtakavarga**:
  - Complete Sarvashtakavarga (canonical 337 grand total) and Bhinnashtakavarga for all 7 classical planets across 12 signs.
- **Shadbala (Planetary Strengths)**:
  - 6 classical balas: Sthana, Dig, Kala, Cheshta, Naisargika, and Drik.
  - Total virupas, total rupas, required strength threshold, and sufficiency status.
- **Upagrahas (Shadow Planets)**:
  - Dhuma, Vyatipata, Parivesha, Indrachapa, and Upaketu with exact sidereal degree and house.
- **Major Aspects**: Conjunction, sextile, square, trine, and opposition with orbs.
- **REST API**: FastAPI server with interactive Swagger UI at `/docs`.
- **CLI**: Terminal tool `nakshatra` for quick JSON chart generation.
- **AI-Ready**: Clean Pydantic models designed for LLM prompts and agent workflows.

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Toya62/nakshatra.git
cd nakshatra

# Install in editable mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Run API Server

```bash
# Start server
nakshatra-api
# or
uvicorn nakshatra.api:app --reload

# Interactive docs at http://localhost:8000/docs
```

### Calculate Chart via API

```bash
curl -X POST http://localhost:8000/chart \
  -H "Content-Type: application/json" \
  -d '{
    "year": 1997,
    "month": 5,
    "day": 22,
    "hour": 4,
    "minute": 53,
    "latitude": 27.8667,
    "longitude": 83.4833,
    "timezone": "Asia/Kathmandu",
    "place_name": "Palpa, Nepal",
    "ayanamsa": "jhora_lahiri"
  }'
```

### Calculate Chart via CLI

```bash
# Output as formatted ASCII table (default)
nakshatra --dob 1997-05-22 --time 04:53 --lat 27.8667 --lon 83.4833 --tz Asia/Kathmandu --ayanamsa jhora_lahiri

# Output as South Indian ASCII box chart diagram
nakshatra --dob 1997-05-22 --time 04:53 --lat 27.8667 --lon 83.4833 --tz Asia/Kathmandu --format diagram

# Output as Markdown report or CSV
nakshatra --dob 1997-05-22 --time 04:53 --lat 27.8667 --lon 83.4833 --tz Asia/Kathmandu --format markdown
nakshatra --dob 1997-05-22 --time 04:53 --lat 27.8667 --lon 83.4833 --tz Asia/Kathmandu --format csv

# Output as pretty JSON
nakshatra --dob 1997-05-22 --time 04:53 --lat 27.8667 --lon 83.4833 --tz Asia/Kathmandu --format json -p

# Save output to specific file
nakshatra --dob 1997-05-22 --time 04:53 --lat 27.8667 --lon 83.4833 --tz Asia/Kathmandu --format json -p -o chart.json

# Auto-save to timestamped file (chart_YYYYMMDD_HHMMSS.<ext>)
nakshatra --dob 1997-05-22 --time 04:53 --lat 27.8667 --lon 83.4833 --tz Asia/Kathmandu --format json -p -s
nakshatra --dob 1997-05-22 --time 04:53 --lat 27.8667 --lon 83.4833 --tz Asia/Kathmandu --format markdown -s
```

### Python Library Usage

```python
from nakshatra import BirthData, calculate_chart, Ayanamsa, HouseSystem

birth = BirthData(
    year=1997, month=5, day=22, hour=4, minute=53,
    latitude=27.8667, longitude=83.4833,
    timezone="Asia/Kathmandu",
    place_name="Palpa, Nepal"
)

# Calculate chart with JHora Lahiri calibration
chart = calculate_chart(
    birth=birth,
    ayanamsa=Ayanamsa.JHORA_LAHIRI,
    house_system=HouseSystem.WHOLE_SIGN
)

# Save directly to file (format inferred from file extension)
chart.save("my_chart.json")      # JSON
chart.save("my_chart.md")        # Markdown report
chart.save("my_chart.csv")       # Planetary CSV
chart.save("my_chart.txt")       # Formatted ASCII tables

# Or get in-memory strings
table_str = chart.to_table()      # Human-readable ASCII tables
diagram_str = chart.to_diagram()  # South Indian ASCII chart box
md_str = chart.to_markdown()      # GitHub-flavored Markdown
csv_str = chart.to_csv()          # Planetary CSV
json_str = chart.to_json()        # Formatted JSON
dict_data = chart.to_dict()       # Python dictionary
```

---

## System Architecture

The complete Nakshatra architecture integrates high-precision astronomical computation with classical shloka retrieval and generative AI synthesis:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER (Browser)                                 │
│                       Streamlit / Next.js Frontend                          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (FastAPI / Streamlit)                       │
│                                                                             │
│   ┌────────────────────┐  ┌─────────────────────┐  ┌────────────────────┐   │
│   │    Chart Layer     │  │      RAG Layer      │  │     LLM Layer      │   │
│   ├────────────────────┤  ├─────────────────────┤  ├────────────────────┤   │
│   │ MayaAstroLib       │  │ FAISS Index         │  │ Gemini 3 / 2.5     │   │
│   │ (Swiss Ephemeris)  │  │ + all-MiniLM-L6-v2  │  │ Flash (Primary)    │   │
│   │                    │  │ (Local embeddings)  │  │                    │   │
│   │ • D1–D60 Vargas    │  │                     │  │ OpenRouter         │   │
│   │ • Vimshottari      │  │ Classical Corpus:   │  │ (Fallback)         │   │
│   │   (MD/AD/PD)       │  │ • BPHS              │  │                    │   │
│   │ • Ashtakavarga     │  │ • Phaladeepika      │  │ Temp: 0.3          │   │
│   │ • Shadbala         │  │ • Brihat Jataka     │  │ Max tokens: 4096   │   │
│   │ • Upagrahas        │  │ • Saravali          │  │                    │   │
│   │ • Yogas & Transits │  │ • Crux (Rath)       │  │                    │   │
│   └─────────┬──────────┘  └──────────┬──────────┘  └─────────┬──────────┘   │
│             │                        │                       │              │
│             └────────────────────────┼───────────────────────┘              │
│                                      ▼                                      │
│                        ┌───────────────────────────┐                        │
│                        │   PROMPT ASSEMBLY LAYER   │                        │
│                        │ (System + Context + Data) │                        │
│                        └───────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Layer Breakdown

1. **Chart Calculation Layer (`nakshatra.core`)**:
   - High-precision astronomical positions via Swiss Ephemeris (`mayaastrolib` / `pyswisseph`).
   - True velocities, retrograde flags, dignities, and whole-sign house placements.
   - Comprehensive divisional charts ($D1$ through $D60$).
   - Vimshottari Dasha timeline with exact timestamp transitions down to Pratyantardasha (PD).
   - Ashtakavarga (337 bindu grand total) and 6-fold Shadbala planetary strength metrics.

2. **RAG Layer (Classical Vedic Shloka Retrieval)**:
   - Local dense retrieval using `all-MiniLM-L6-v2` embeddings and FAISS vector index.
   - Authoritative classical corpus:
     - *Brihat Parashara Hora Shastra* (BPHS)
     - *Phaladeepika* (Mantreswara)
     - *Brihat Jataka* (Varahamihira)
     - *Saravali* (Kalyana Varma)
     - *The Crux of Vedic Astrology* (Pt. Sanjay Rath)
   - Context-aware retrieval triggered by active graha positions, house lords, and dasha rulers.

3. **LLM & Prompt Assembly Layer**:
   - Synthesizes exact astrological facts with classical shloka evidence.
   - **Primary Model**: Google Gemini Flash (via `google-genai` SDK, temp: 0.3, max tokens: 4096).
   - **Fallback Model**: OpenRouter endpoint for redundancy.
   - Prevents AI hallucinations by strictly grounding predictions in retrieved classical rules and calculated chart positions.

4. **Frontend Layer**:
   - Interactive UI (Streamlit for rapid experimentation / Next.js for production SaaS).
   - South Indian and North Indian chart layouts with transit overlays and interactive Dasha timeline.

---

## Roadmap

- [x] **Swiss Ephemeris Core**: Sub-second astronomical chart generation with `pyswisseph`.
- [x] **Vimshottari Engine**: Exact MD, AD, and PD timestamps down to the second.
- [x] **Divisional Charts (Shodashavarga)**: D1 through D60 support.
- [x] **Ashtakavarga & Shadbala**: 337 SAV bindus and 6 classical strength balas.
- [x] **Multi-format Outputs**: ASCII tables, South Indian diagram, Markdown, CSV, and JSON.
- [x] **Jagannatha Hora Calibration**: `jhora_lahiri` ayanamsa for 100% concordance.
- [ ] **Classical Yoga Detection**: Raja, Dhana, Pancha Mahapurusha, Gaja Kesari, Kemadruma, Neechabhanga.
- [ ] **Gochar (Transit) Engine**: Natal-to-transit planetary aspect and house activations.
- [ ] **RAG Corpus Ingestion**: Parsing and chunking of BPHS, Phaladeepika, Saravali, and Crux.
- [ ] **FAISS Vector Store**: Local embeddings via `sentence-transformers` (`all-MiniLM-L6-v2`).
- [ ] **LLM Integration**: Gemini Flash + OpenRouter prompt synthesis agent.
- [ ] **Interactive Frontend**: Streamlit / Next.js web application.

---

## Validation & Jagannatha Hora Concordance

Tested against reference charts exported from Jagannatha Hora:
- **Planetary Positions**: Mean difference $< 1$ arcsecond on Moon and Nodes with `jhora_lahiri`.
- **Rasi & Navamsa (D9)**: 100% exact match across all 10 bodies.
- **Nakshatras & Padas**: 100% exact match across all bodies.
- **Ashtakavarga**: 100% exact match for Sun, Mars, Mercury, Jupiter, and Saturn; canonical 337 grand total.
- **Vimshottari Dasha**: Mahadashas, Antardashas, and Pratyantardashas align to sub-day accuracy.

---

## Development

```bash
# Run test suite
pytest

# Code linting
ruff check .

# Type checking
mypy nakshatra
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.
Ephemeris engine powered by Swiss Ephemeris (`pyswisseph`).