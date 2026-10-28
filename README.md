---
title: Nakshatra
emoji: 🪐
colorFrom: indigo
colorTo: yellow
sdk: gradio
sdk_version: 6.30.0
app_file: app.py
pinned: false
license: agpl-3.0
---

# Nakshatra - Vedic Astrology AI Engine

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 16.4](https://img.shields.io/badge/Next.js-16.4_Turbopack-black.svg)](https://nextjs.org/)
[![Engine: Swiss Ephemeris](https://img.shields.io/badge/engine-Swiss%20Ephemeris-blue.svg)](https://www.astro.com/swisseph/)
[![Hugging Face Space](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Space%20Live-yellow)](https://toya62-nakshatra.hf.space)

**Nakshatra** (नक्षत्र) is a high-precision, production-grade Vedic astrology calculation and AI consultation engine. Powered by **Swiss Ephemeris** (`pyswisseph`) through `mayaastrolib` for sub-second, arcsecond-level astronomical accuracy, it provides birth charts (Kundali), Vimshottari dashas, divisional charts (Shodashavarga), Ashtakavarga, Shadbala, and Gochar transits as structured JSON via FastAPI REST API, Next.js web application, Gradio UI, Model Context Protocol (MCP) server, CLI, and Python library.

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
- **Vimshottari Dashas & 120-Year Visual Timeline**:
  - Birth balance calculation down to fractional years.
  - Full 120-year sequence of Mahadashas (MD), Antardashas (AD), and Pratyantardashas (PD) down to the exact second (`YYYY-MM-DD HH:MM:SS`).
  - Interactive horizontal life ribbon with real-time age indicator ("NOW" cursor) and active period lookup.
  - Overlaid Saturn Sade Sati 7.5-year windows calibrated to natal Moon.
- **Nepali Bikram Sambat (BS) Calendar & Sanskrit Devanagari**:
  - Bidirectional Gregorian (AD) ↔ Nepali Bikram Sambat (BS) date conversion via authentic Panchanga ephemeris tables (`nepali-datetime`).
  - Canonical Sanskrit Devanagari nomenclature toggle across Grahas (सूर्य, चन्द्र, मङ्गल, etc.), Rasis (मेष, वृष, etc.), and Nakshatras (अश्विनी ... रेवती).
- **Geocoding & Historical Timezone/DST Resolver**:
  - Offline curated registry of 100+ global and spiritual centers (Kathmandu, Varanasi, Ujjain, Lumbini, Tirupati, etc.) with OpenStreetMap Nominatim fallback.
  - Historical Civil UTC offset and Daylight Saving Time (DST) calculation via IANA / `zoneinfo`.
- **Explainable "Why" Astrological Reason Inspector**:
  - Transparent 3-pillar breakdown for AI consultations:
    1. *Scriptural Pramana*: Full classical verses, works, chapters, and shloka citations.
    2. *Natal Grounding (Yukti)*: Seekers exact planetary degrees, operating Mahadasha/Antardasha, Lagna, and Gochar transits.
    3. *Ethical / Dharma Guardrail*: Anti-fatalistic counseling reframing and professional boundary guidance.
- **GDPR Zero-Log Ephemeral Privacy Policy**:
  - Strict in-memory processing: zero persistence of seeker names, questions, or exact birth coordinates.
  - Automatic scrubbing of latitude, longitude, and personal identifiers from application logs (`PrivacySanitizerFilter`).
  - Automatic injection of `X-Data-Policy: ephemeral-zero-retention` header.
- **Shodashavarga (Divisional Charts)**:
  - All 16 vargas: D1 (Rasi), D2 (Hora), D3 (Drekkana), D4 (Chaturthamsa), D7 (Saptamsa), D9 (Navamsa), D10 (Dasamsa), D12 (Dvadasamsa), D16 (Shodasamsa), D20 (Vimsamsa), D24 (Chaturvimsamsa), D27 (Bhamsa), D30 (Trimsamsa), D40 (Khavedamsa), D45 (Akshavedamsa), D60 (Shastiamsa).
- **Ashtakavarga**:
  - Complete Sarvashtakavarga (canonical 337 grand total) and Bhinnashtakavarga for all 7 classical planets across 12 signs.
- **Shadbala (Planetary Strengths)**:
  - 6 classical balas: Sthana, Dig, Kala, Cheshta, Naisargika, and Drik.
  - Total virupas, total rupas, required strength threshold, and sufficiency status.
- **Upagrahas (Shadow Planets)**:
  - Dhuma, Vyatipata, Parivesha, Indrachapa, and Upaketu with exact sidereal degree and house.
- **Transits (Gochar)**:
  - Current or user-specified transit date against natal chart.
  - Transit houses from natal Lagna and natal Moon (Chandra Lagna).
  - Sade Sati (rising / peak / setting), Ashtama Shani, and Kantaka Shani detection.
  - Jupiter Gochar with Phaladeepika favorable-house evaluation.
  - Double Transit detection (houses simultaneously aspected by Jupiter and Saturn).
  - Sarvashtakavarga (SAV) and Bhinnashtakavarga (BAV) bindus per transit sign.
- **Panchanga Engine**:
  - 5 limbs of Vedic time: Tithi (lunar phase & percentage left), Vara (Vedic weekday from sunrise), Nakshatra (lunar mansion & percentage left), Yoga (solilunar angular sum & percentage left), and Karana (half-tithi & movable/fixed tracking with Bhadra alert).
  - Swiss Ephemeris sunrise and sunset calculations with pre-sunrise solar day rollback.
- **Parashari Graha Drishti (Vedic House Aspects)**:
  - Exact house-to-house aspect engine:
    - All Grahas cast full 7th house aspect.
    - Special classical Graha Drishti: Saturn (3rd & 10th houses), Mars (4th & 8th houses), Jupiter (5th & 9th houses), Rahu/Ketu (5th & 9th houses).
    - Computed directly on `ChartData.vedic_aspects` and injected into deterministic engine and AI consultation prompts.
- **Classical Yoga Detection & Parivartana Engine**:
  - Rule-based deterministic detection engine over `ChartData`:
    - **Parivartana Yogas**: Mutual sign exchanges classified classically into **Maha Yoga** (exchanges between Kendra/Trikona auspicious lords), **Kahala Yoga** (3rd lord exchanges), and **Dainya Yoga** (6th, 8th, or 12th Dusthana lord exchanges).
    - **Pancha Mahapurusha**: Ruchaka (Mars), Bhadra (Mercury), Hamsa (Jupiter), Malavya (Venus), Sasa (Saturn).
    - **Gaja Kesari**: Jupiter in Kendra from Moon.
    - **Kemadruma & Bhanga**: Moon flanking checks with Kendra cancellations.
    - **Strict Neechabhanga Rules**: Classical Phaladeepika criteria (dispositor in Kendra, planet exalted in sign in Kendra, dispositor aspect) with Dusthana friction evaluation; solitary Kendra placement does not falsely cancel debility.
    - **Chandra Yogas**: Sunapha, Anapha, Dhurdhura, Chandra Mangala, Chandradhi Yoga.
    - **Surya Yogas**: Budhaditya, Vesi, Vasi, Ubhayachari.
    - **Viparita Raja Yogas**: Harsha, Sarala, Vimala.
    - **Raja & Dhana Yogas**: Amala Yoga, Kendra-Trikona conjunctions, wealth axis combinations.
- **30-Day Transit Window Scanner & Chandrashtama Radar**:
  - Continuous 3-hour precision window scanner (`scan_transit_window`):
    - Planetary Ingresses (e.g. Sun into Libra, Mars into Cancer).
    - Planetary Stations (Mercury/Venus retrograde and direct turning points).
    - **Chandrashtama Periods**: Exact 54-hour lunar transit through the 8th house from natal Moon, flagging heightened emotional vulnerability and trading/travel friction.
- **Dual-System Karmic Rectifications & Remedies**:
  - `POST /remedies` dual-system prescription engine:
    - **Classical Parashari**: Exact Vedic Beej Mantra count, gemstone prescription with weight (ratti), metal, finger, and contraindications, plus day-specific Dāna (charity items).
    - **Authentic Lal Kitab**: Practical household Upayas, symbolic acts (*Jal Pravah*), creature/animal seva (cows, crows, black dogs), and inviolable golden rules (daytime *Surya Prakash* rule, 43-day continuous count, strict prohibition against remedying exalted planets).
- **Deterministic Hierarchical Prediction Engine**:
  - Three-tier synthesis across 5 life domains (Career, Finance, Marriage, Health, Spirituality):
    1. *Natal Promise*: Planetary yogas, house lords, and SAV bindus evaluated into Purna (Full), Madhyama (Moderate), or Alpa (Weak).
    2. *Vimshottari Dasha Timing*: Checks whether operating Mahadasha and Antardasha lords activate the required bhava.
    3. *Gochara Transits*: Real-time transit friction and double transit support.
- **OCR-Purged BPHS & Classical Corpus Vector RAG**:
  - Multi-tier chunker over Brihat Parashara Hora Shastra (BPHS), Saravali, and Phaladeepika.
  - Purged legacy 1980s Indian font glyph noise (`amfwnwTTsirm`, caret clusters, broken hyphens).
  - Fixed verse range chapter-shift parsing (preserves context on ranges like `1-4. Maitreya said...`).
  - Modern allegorical translation filter reframing archaic curses into actionable psychological counsel.
- **Model Context Protocol (MCP) Server**:
  - Exposes 7 registered tools for Claude Desktop, Cursor, and agentic workflows:
    - `calculate_birth_chart`
    - `get_daily_panchanga`
    - `match_kundali_compatibility`
    - `get_muhurtha_election`
    - `get_transits_gochar`
    - `detect_vedic_yogas`
    - `consult_scripture_rag`
- **Multi-Format Outputs**: High-legibility North Indian diamond chart, ASCII tables, Markdown, CSV, and JSON.
- **Dual-Theme Design System & Responsive Navigation**:
  - Full Light Mode and Dark Mode support with seamless toggle, system detection, and localStorage persistence.
  - Light mode calibrated for high-contrast WCAG AA/AAA legibility across all 8 feature tabs.
  - Responsive collapsible sidebar with desktop 56px slim icon mode and mobile slide-out navigation drawer.
- **REST API**: FastAPI server with interactive Swagger UI at `/docs` and OpenAPI 3.0 spec.

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Toya62/nakshatra.git
cd nakshatra

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .

# Or with dev and AI extras
pip install -e ".[dev,ai]"
```

### Run API Server

```bash
# Start FastAPI backend on port 8004
uvicorn nakshatra.api:app --reload --port 8004
```

### Run Frontend Web App

```bash
cd web
npm install
npm run dev
# Open http://localhost:3000
```

### Run MCP Server (Claude Desktop / Cursor)

```bash
# Launch MCP stdio server
python -m nakshatra.mcp_server
```

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "nakshatra": {
      "command": "/path/to/nakshatra/.venv/bin/python",
      "args": ["-m", "nakshatra.mcp_server"]
    }
  }
}
```

---

## REST API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/chart` | `POST` | Calculate Vedic chart, planets, houses, dashas, vargas, and Ashtakavarga |
| `/transits` | `POST` | Calculate Gochara transits, Sade Sati status, and double transits |
| `/transits/window` | `POST` | Scan 30-day transit window for ingresses, stations, and Chandrashtama periods |
| `/predict` | `POST` | Classical hierarchical predictions across Career, Finance, Marriage, Health, Spirituality |
| `/remedies` | `POST` | Dual-system remedies: Classical Parashari (Mantra, Gem, Dana) & Lal Kitab Upayas |
| `/panchanga` | `POST` | Compute 5 limbs of Vedic time (Tithi, Vara, Nakshatra, Yoga, Karana) |
| `/yogas` | `POST` | Detect classical Parashara Raja, Dhana, Mahapurusha, and Parivartana yogas |
| `/match/compatibility` | `POST` | 36-point Ashtakoota and Kuja Dosha (Manglik) analysis |
| `/muhurtha` | `POST` | Planetary Horas, Choghadiya, Abhijit, and Rahu Kalam election scoring |
| `/geocode/search` | `GET` | Autocomplete and resolve cities/coordinates (`?q=Kathmandu`) |
| `/geocode/timezone` | `GET` | Resolve historical UTC/DST offset (`?tz=Asia/Kathmandu&year=1997...`) |
| `/calendar/bs` | `GET` | Convert Gregorian (AD) to Nepali Bikram Sambat (BS) |
| `/calendar/ad` | `GET` | Convert Nepali Bikram Sambat (BS) to Gregorian (AD) |
| `/calendar/nomenclature` | `GET` | Canonical Sanskrit Devanagari terms for Grahas, Rasis, and Nakshatras |
| `/rag/ask` | `POST` | Scripture-grounded consultation with shloka citations |
| `/privacy` | `GET` | GDPR ephemeral zero-retention guarantee |
| `/legal/licensing` | `GET` | Swiss Ephemeris AGPL-3.0 and classical corpus attribution notice |
| `/health` | `GET` | System health check |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             NAKSHATRA PLATFORM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [FRONTEND APPS]                                                            │
│  ├─ Next.js 16.4 Web App (North Indian Kundali, 120-Yr Timeline, Remedies) │
│  ├─ Dual-Theme UI (Cosmic Obsidian Slate #080b14 / Warm Alabaster Cream)   │
│  ├─ Responsive Collapsible Sidebar (Desktop Slim 56px / Mobile Drawer)      │
│  └─ Hugging Face Space Gradio 6.30 (ZeroGPU keepalive)                      │
│                                                                             │
│  [API & PROTOCOLS]                                                          │
│  ├─ FastAPI REST API (CORS, Ephemeral Privacy Middleware, Rate Limits)       │
│  └─ Model Context Protocol (MCP) Server (7 Astrological Tools)              │
│                                                                             │
│  [ASTRONOMICAL CORE & EPHEMERIS]                                            │
│  ├─ Swiss Ephemeris Engine (pyswisseph / mayaastrolib)                     │
│  ├─ Jagannatha Hora Concordance (jhora_lahiri Ayanamsa)                     │
│  ├─ Vimshottari Dasha Engine (120-year cycle down to second)                │
│  ├─ Parashari Graha Drishti Engine (Full 7th, Special 3/10, 4/8, 5/9)       │
│  ├─ 30-Day Transit Window Scanner (Ingresses, Stations, Chandrashtama)      │
│  └─ Shodashavarga (D1 - D60), Ashtakavarga (337 SAV), Shadbala (6 Balas)     │
│                                                                             │
│  [ANALYTICAL & PRESCRIPTIVE ENGINES]                                        │
│  ├─ Classical Yogas: Parivartana (Maha, Kahala, Dainya) & Neechabhanga      │
│  ├─ Dual-System Remedies (Parashari Mantras/Gems/Dana + Lal Kitab Upayas)   │
│  ├─ Deterministic Predictor (Natal Promise x Dasha Timing x Transits)       │
│  ├─ 36-Point Ashtakoota Compatibility & Muhurtha Election                   │
│  └─ Geocoding & Historical Timezone/DST Resolver (zoneinfo + Nominatim)     │
│                                                                             │
│  [CLASSICAL RAG & SYNTHESIS]                                                │
│  ├─ OCR-Purged Verse Chunker (BPHS, Saravali, Phaladeepika, Lal Kitab)      │
│  ├─ Hybrid Vector Store (NumPy Cosine + BM25, RRF Fusion)                   │
│  ├─ Modern Allegorical Translation Layer (Archaic Curses -> Behavioral Psy) │
│  └─ Cited LLM Synthesis (OpenAI / Gemini 3.8 / Verbatim Fallback)           │
│                                                                             │
│  [TRUST & SAFETY GUARDRAILS]                                                │
│  ├─ Explainable Reason Inspector (Pramana, Yukti, Dharma)                   │
│  ├─ Anti-Fatalistic Psychological/Dharma Reframing                          │
│  └─ GDPR Ephemeral Zero-Log Filter                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Roadmap

- [x] **Swiss Ephemeris Core**: Sub-second astronomical chart generation with `pyswisseph`.
- [x] **Vimshottari Engine**: Exact MD, AD, and PD timestamps down to the second.
- [x] **Divisional Charts (Shodashavarga)**: D1 through D60 support.
- [x] **Ashtakavarga & Shadbala**: 337 SAV bindus and 6 classical strength balas.
- [x] **Parashari Graha Drishti**: Complete house aspect engine with special planetary aspects.
- [x] **Parivartana Yogas**: Classical Maha, Kahala, and Dainya mutual exchange detection.
- [x] **Strict Neechabhanga Rules**: Phaladeepika dispositor/exaltation Kendra criteria with Dusthana friction.
- [x] **30-Day Transit Window Scanner**: 3-hour precision window scanner for ingresses, stations, and Chandrashtama.
- [x] **Dual-System Remedies**: Parashari mantras, gemstones, and charity paired with Lal Kitab Upayas and strict precautions.
- [x] **Deterministic Prediction Engine**: Natal Promise $\times$ Dasha Timing $\times$ Transit synthesis.
- [x] **Jagannatha Hora Calibration**: `jhora_lahiri` ayanamsa for 100% concordance.
- [x] **Panchanga Engine**: Exact 5 limbs (Tithi, Vara, Nakshatra, Yoga, Karana) with solar day tracking.
- [x] **OCR-Purged Corpus RAG**: Purged legacy font noise and preserved verse range chapter mapping.
- [x] **Modern Allegorical Translation**: Ethical, non-fatalistic psychological framing.
- [x] **Interactive Frontend**: Next.js 16.4 production application with dual-theme cosmic UI.
- [x] **Dual-Theme & Responsive Navigation**: Light/Dark mode with WCAG AA/AAA tokens and collapsible sidebar.
- [x] **Offline Geocoding & Historical Timezone Resolver**: 100+ global centers with DST resolution.
- [x] **Explainable Astrological Reason Inspector**: Direct shloka citations (Pramana) and natal grounding (Yukti).
- [x] **120-Year Life Timeline UI**: Proportional Vimshottari ribbon bar and Sade Sati overlays.
- [x] **Model Context Protocol (MCP) Server**: 7 registered tools for Claude Desktop, Cursor, and agents.

> [!TIP]
> **Looking for upcoming product expansion plans?**  
> See [ROADMAP.md](ROADMAP.md) for our detailed future roadmap covering the **Astrology Knowledge Hub**, **KP & Western Astrology**, and **10 Specialized Diagnostic Report Modules** (Mangal Dosha, Kalsarp, Pitra Dosha, Videsh Yoga, Gemstones, Raj Yoga).

---

## Validation & Jagannatha Hora Concordance

Tested against reference charts exported from Jagannatha Hora:
- **Planetary Positions**: Mean difference $< 1$ arcsecond on Moon and Nodes with `jhora_lahiri`.
- **Rasi & Navamsa (D9)**: 100% exact match across all 10 bodies.
- **Nakshatras & Padas**: 100% exact match across all bodies.
- **Ashtakavarga**: 100% exact match for Sun, Mars, Mercury, Jupiter, and Saturn; canonical 337 grand total.
- **Vimshottari Dasha**: Mahadashas, Antardashas, and Pratyantardashas align to sub-day accuracy.
- **Test Suite**: 256 automated tests passing across Python 3.10, 3.11, and 3.12.

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

## License & Attribution

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** — see [LICENSE](LICENSE) for details.

### Special Notice Regarding Swiss Ephemeris (`pyswisseph`)
The Swiss Ephemeris portion of this software is copyright © 1997-2026 by **Astrodienst AG**, Switzerland. It is dual-licensed under the **GNU AGPL v3** or a **commercial license** directly from Astrodienst AG ([astro.com/swisseph](https://www.astro.com/swisseph/)).
- **Open-source & Free Software**: Permitted under GNU AGPL-3.0 copyleft terms.
- **Proprietary Commercial SaaS / Closed-Source**: Requires purchasing a commercial Swiss Ephemeris license from Astrodienst AG.

### Classical Corpus Attribution
- **Brihat Parashara Hora Shastra (BPHS)**: Sanskrit verses in public domain; English commentary (R. Santhanam, 1984) referenced for educational study.
- **Saravali & Phaladeepika**: Classical Sanskrit astrological treatises in the public domain.
- **Modern Syntheses**: Referenced as fair use research excerpts for scriptural grounding.