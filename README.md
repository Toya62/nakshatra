# Nakshatra - Vedic Astrology AI Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Engine: Swiss Ephemeris](https://img.shields.io/badge/engine-Swiss%20Ephemeris-blue.svg)](https://www.astro.com/swisseph/)

**Nakshatra** (नक्षत्र) is a high-precision Vedic astrology calculation engine providing birth charts, Vimshottari dashas, divisional charts, Ashtakavarga, and Shadbala as structured JSON via FastAPI REST API, CLI, and Python library. Powered by **Swiss Ephemeris** (`pyswisseph`) through `mayaastrolib` for sub-second, arcsecond-level astronomical accuracy.

---

## Features

- **Accurate Astronomical Engine**: Swiss Ephemeris (`pyswisseph`) backend with true planetary velocities and retrograde indicators.
- **Complete Birth Chart Data**: 7 classical Grahas (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn) + Rahu/Ketu lunar nodes + Ascendant + Midheaven with sign, degree, nakshatra, pada, house, dignity, and retrograde state.
- **Multiple Ayanamsas**:
  - `jhora_lahiri`: Traditional Lahiri calibrated for 100% concordance with Jagannatha Hora (**default**).
  - `lahiri`: Astronomical Chitra Paksha (official Indian standard).
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
- **Transits (Gochar)**:
  - Current or user-specified transit date against the natal chart.
  - Transit houses from natal Lagna and natal Moon (Chandra Lagna).
  - Sade Sati (rising / peak / setting), Ashtama Shani, and Kantaka Shani detection.
  - Jupiter Gochar with Phaladeepika favorable-house evaluation.
  - Double Transit detection (houses simultaneously aspected by Jupiter and Saturn).
  - Sarvashtakavarga (SAV) and Bhinnashtakavarga (BAV) bindus per transit sign.
- **Panchanga Engine**:
  - The 5 limbs of Vedic time: Tithi (lunar phase & percentage left), Vara (Vedic weekday from sunrise), Nakshatra (lunar mansion & percentage left), Yoga (solilunar angular sum & percentage left), and Karana (half-tithi & movable/fixed tracking with Bhadra alert).
  - Swiss Ephemeris sunrise and sunset calculations with pre-sunrise solar day rollback.
  - Standalone API (`GET /panchanga`, `POST /panchanga`) and CLI `--panchanga`.
- **Classical Yoga Detection**:
  - Rule-based detection engine over `ChartData`:
    - **Pancha Mahapurusha**: Ruchaka (Mars), Bhadra (Mercury), Hamsa (Jupiter), Malavya (Venus), Sasa (Saturn).
    - **Gaja Kesari**: Jupiter in Kendra from Moon.
    - **Kemadruma & Bhanga**: Moon flanking checks with Kendra cancellations.
    - **Neechabhanga Raja Yoga**: Multi-condition cancellation of planetary debility.
    - **Chandra Yogas**: Sunapha, Anapha, Dhurdhura, Chandra Mangala, Chandradhi Yoga.
    - **Surya Yogas**: Budhaditya, Vesi, Vasi, Ubhayachari.
    - **Viparita Raja Yogas**: Harsha, Sarala, Vimala.
    - **Raja & Dhana Yogas**: Amala Yoga, Kendra-Trikona conjunctions, wealth axis combinations.
  - Standalone API (`GET /yogas`, `POST /yogas`) and CLI `--yogas`.
- **Multi-Format Outputs**: ASCII tables, South Indian chart diagram (any varga), Markdown, CSV, and JSON.
- **REST API**: FastAPI server with interactive Swagger UI at `/docs`.
- **CLI**: Terminal tool `nakshatra` for quick chart, transit, panchanga, and yoga generation.
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

# Calculate planetary transits (Gochar) for the current date
nakshatra --dob 1997-05-22 --time 04:53 --lat 27.8667 --lon 83.4833 --tz Asia/Kathmandu --transit

# Calculate transits for a specific date (table or JSON output)
nakshatra --dob 1997-05-22 --time 04:53 --lat 27.8667 --lon 83.4833 --tz Asia/Kathmandu --transit 2026-12-25
nakshatra --dob 1997-05-22 --time 04:53 --lat 27.8667 --lon 83.4833 --tz Asia/Kathmandu --transit 2026-12-25 --format json -p
```

### RAG Consultation

```bash
# Ingest a classical corpus into a searchable index
# Layout: corpus/<work>/meta.json (work, translator, license) + .txt/.md files
nakshatra ingest-corpus --dir corpus --out index

# Ask a question (API)
curl -X POST http://localhost:8000/rag/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What does my chart say about career?", "top_k": 5}'
```

Retrieval fuses BM25 lexical ranking with `all-MiniLM-L6-v2` dense
embeddings (Reciprocal Rank Fusion) and expands queries via a Bhava/Karaka
concept map (e.g., "marriage" → House 7, Venus, Jupiter, D9 Navamsa).
Install the optional AI extras for semantic embeddings and LLM synthesis:

```bash
pip install 'nakshatra[ai]'   # sentence-transformers, google-genai, openai
```

Without the extras, the engine runs in zero-dependency BM25-only mode with
verbatim cited references.

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

# Calculate transits (Gochar) for a specific date
from datetime import datetime
report = chart.get_transits(datetime(2026, 12, 25))
print(report.to_table())          # Sade Sati, Jupiter Gochar, Double Transit
report_json = report.model_dump_json()
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
   - Hybrid retrieval: BM25 lexical ranking fused with `all-MiniLM-L6-v2` dense embeddings (NumPy cosine store) via Reciprocal Rank Fusion.
   - Bhava/Karaka concept map expands queries (e.g., "marriage" → House 7, Venus, Jupiter, D9 Navamsa).
   - Zero-dependency BM25-only fallback when sentence-transformers is unavailable.
   - Authoritative classical corpus:
     - *Brihat Parashara Hora Shastra* (BPHS)
     - *Phaladeepika* (Mantreswara)
     - *Brihat Jataka* (Varahamihira)
     - *Saravali* (Kalyana Varma)
     - *The Crux of Vedic Astrology* (Pt. Sanjay Rath)
   - Context-aware retrieval triggered by active graha positions, house lords, and dasha rulers.

3. **LLM & Prompt Assembly Layer**:
   - Synthesizes exact astrological facts with classical shloka evidence.
   - **Providers**: OpenAI (`gpt-4o-mini`) and Google Gemini via `google-genai`, selected by API key.
   - Deterministic fallback: verbatim cited references when no LLM is configured.
   - Prevents hallucinations by requiring bracketed `[n]` citations grounded in retrieved chunks.

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
- [x] **Gochar (Transit) Engine**: Natal-to-transit planetary aspects, Sade Sati, Jupiter Gochar, Double Transit.
- [x] **Panchanga Engine**: Exact 5 limbs (Tithi, Vara, Nakshatra, Yoga, Karana) with solar day tracking.
- [x] **Classical Yoga Detection**: Raja, Dhana, Pancha Mahapurusha, Gaja Kesari, Kemadruma (+ Bhanga), Neechabhanga (+ Raja Yoga).
- [x] **RAG Corpus Ingestion**: Two-tier verse/paragraph chunker with license-gated works (BPHS, Phaladeepika, Saravali, Crux).
- [x] **Hybrid Vector Store**: NumPy cosine store + BM25, RRF-fused, with Bhava/Karaka concept expansion.
- [x] **LLM Integration**: OpenAI + Gemini cited synthesis with deterministic verbatim-reference fallback.
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