# Nakshatra Web Frontend

Modern, high-performance web interface for the **Nakshatra Vedic Astrology AI Engine**, built with **Next.js 16.4**, **React 19**, **TypeScript**, and modern CSS glassmorphism.

---

## Key Features

1. **Precision Birth Input & Geocoding (`BirthForm.tsx`)**:
   - Debounced type-ahead place search over 100+ curated spiritual and global locations with OpenStreetMap Nominatim fallback.
   - Real-time civil UTC offset and historical Daylight Saving Time (DST) resolution with live badge indicator.
   - Ayanamsa selector (Jagannatha Hora Lahiri default, Lahiri, Raman, KP, Fagan-Bradley).
   - House system selector (Whole Sign default, Placidus, Equal, etc.).

2. **Dual Visual Chart Renderers**:
   - **North Indian (`NorthIndianChart.tsx`)**: Traditional diamond chart format with house numbers, retrograde indicators, and planetary dignity badges.
   - **South Indian (`SouthIndianChart.tsx`)**: Fixed zodiac sign grid format with aspect markings.
   - **Varga Switcher**: Instant switching across D1 (Rasi), D9 (Navamsha), D10 (Dasamsha), and D60 (Shastiamsha).

3. **Unified 120-Year Dasha & Gochar Life Timeline (`TimelineView.tsx`)**:
   - Proportional Vimshottari Mahadasha ribbon bar.
   - Click-to-zoom into 9 sub-Antardashas and Pratyantardashas.
   - Seeker's real-time age indicator ("NOW" cursor).
   - Overlaid Saturn Sade Sati 7.5-year windows calibrated to natal Moon.
   - Nepali Bikram Sambat (BS) date display badge.
   - Sanskrit Devanagari nomenclature toggle (सूर्य, चन्द्र, मङ्गल, etc.).

4. **Explainable "Why" Astrological Reason Inspector (`ConsultationView.tsx`)**:
   - Interactive explainability modal breaking down every AI answer into 3 pillars:
     1. **Scriptural Pramana**: Verbatim classical verses, works, chapters, and shlokas.
     2. **Natal Grounding (Yukti)**: Seekers exact degrees, Lagna, operating Dasha, and Gochara transits.
     3. **Ethical / Dharma Guardrail**: Non-fatalistic counseling guidance and licensed boundary disclaimers.

5. **Transits & Daily Panchanga**:
   - Real-time Gochara planetary aspects from Lagna and Moon (`TransitsView.tsx`).
   - Active 5 limbs of Vedic time (`PanchangaView.tsx`): Tithi, Vara, Nakshatra, Yoga, and Karana with Bhadra alert.

6. **36-Point Ashtakoota & Muhurtha Scoring**:
   - Marriage compatibility with Kuja Dosha (Manglik) detection (`CompatibilityView.tsx`).
   - Auspicious timing engine with Horas, Choghadiya, Abhijit Muhurtha, and Rahu Kalam (`MuhurthaView.tsx`).

7. **Trust & Privacy First**:
   - Ephemeral zero-log privacy policy banner.
   - Interactive Legal & Licensing modal disclosing Swiss Ephemeris AGPL-3.0 compliance.

---

## Getting Started

### Prerequisites
- Node.js 18+ or 20+
- Running Nakshatra FastAPI backend on `http://127.0.0.1:8004` (or Hugging Face Space)

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
# Type check and build production bundle with Next.js Turbopack
npm run build

# Start production server
npm start
```

---

## Configuration

The frontend automatically detects local and cloud API endpoints in the following priority:
1. Custom API URL (if set via `window.__NAKSHATRA_API_URL__` or `NEXT_PUBLIC_API_URL`)
2. Local Next.js API route proxy (`/api/py/*`)
3. `http://127.0.0.1:8004` (Local FastAPI backend)
4. `http://localhost:8004`
5. `https://toya62-nakshatra.hf.space` (Hugging Face Space)

---

## License

GNU Affero General Public License v3.0 (AGPL-3.0) — see [LICENSE](../LICENSE).
Swiss Ephemeris is copyright © 1997-2026 Astrodienst AG.
