# Nakshatra Web Frontend

Modern, high-performance web interface for the **Nakshatra Vedic Astrology AI Engine**, built with **Next.js 16.4**, **React 19**, **TypeScript**, and modern CSS glassmorphism.

---

## Key Features

1. **Precision Birth Input & Geocoding (`BirthForm.tsx`)**:
   - Debounced type-ahead place search over 100+ curated spiritual and global locations with OpenStreetMap Nominatim fallback.
   - Real-time civil UTC offset and historical Daylight Saving Time (DST) resolution with live badge indicator.
   - Ayanamsa selector (Jagannatha Hora Lahiri default, Lahiri, Raman, KP, Fagan-Bradley).
   - House system selector (Whole Sign default, Placidus, Equal, etc.).

2. **High-Legibility North Indian Kundali (`NorthIndianChart.tsx`)**:
   - Traditional diamond chart format with enlarged `13px` Graha names, `11px` degrees, and bold `13.5px` Rashi number seals.
   - Centered `LAGNA` header in House 1 (1st Bhava diamond).
   - Instant 16-Varga divisional chart selector across D1 (Rasi), D9 (Navamsha), D10 (Dasamsha), up to D60 (Shastiamsha).
   - Interactive house inspection with Vedic Bhava significations and Graha dignities (exalted, debilitated, own sign).

3. **Dual-System Remedies & Karmic Rectifications (`RemediesView.tsx`)**:
   - Classical Parashari prescriptions: Vedic Beej Mantras, gemstones with weight (ratti), metal, finger, and day-specific Dāna (charity).
   - Authentic Lal Kitab Upayas: practical household remedies, symbolic actions (*Jal Pravah*), creature seva (cows, crows, black dogs).
   - Lal Kitab golden rules & strict precautions: daytime *Surya Prakash* rule, 43-day continuous count, and prohibition against remedying exalted planets.
   - Saturn Sade Sati Gochar notice banner and severity filtering.

4. **Transits, 30-Day Scanner & Daily Panchanga**:
   - 30-day transit window scanner (`TransitsView.tsx`) tracking planetary ingresses, retrograde/direct stations, and 54-hour Chandrashtama periods.
   - Real-time Gochara planetary aspects from Lagna and Moon.
   - Active 5 limbs of Vedic time (`PanchangaView.tsx`): Tithi, Vara, Nakshatra, Yoga, and Karana with Bhadra alert.

5. **Unified 120-Year Dasha & Gochar Life Timeline (`TimelineView.tsx`)**:
   - Proportional Vimshottari Mahadasha ribbon bar.
   - Click-to-zoom into 9 sub-Antardashas and Pratyantardashas.
   - Seeker's real-time age indicator ("NOW" cursor).
   - Overlaid Saturn Sade Sati 7.5-year windows calibrated to natal Moon.
   - Nepali Bikram Sambat (BS) date display badge.
   - Sanskrit Devanagari nomenclature toggle (सूर्य, चन्द्र, मङ्गल, etc.).

6. **Explainable "Why" Astrological Reason Inspector (`ConsultationView.tsx`)**:
   - Interactive explainability modal breaking down every AI answer into 3 pillars:
     1. **Scriptural Pramana**: Verbatim classical verses, works, chapters, and shlokas.
     2. **Natal Grounding (Yukti)**: Seekers exact degrees, Lagna, operating Dasha, and Gochara transits.
     3. **Ethical / Dharma Guardrail**: Non-fatalistic counseling guidance and licensed boundary disclaimers.

7. **36-Point Ashtakoota & Muhurtha Scoring**:
   - Marriage compatibility with Kuja Dosha (Manglik) detection (`CompatibilityView.tsx`).
   - Auspicious timing engine with Horas, Choghadiya, Abhijit Muhurtha, and Rahu Kalam (`MuhurthaView.tsx`).

8. **Dual-Theme Cosmic Glassmorphism & Responsive Layout**:
   - **Light & Dark Mode**: Persistent theme toggle supporting system preference, Dark Mode (cosmic obsidian canvas `#080b14` with champagne gold specular rims), and Light Mode (warm alabaster cream canvas `#f8f6f0`, cedar charcoal `#1c1917` / `#44403c` with WCAG AA/AAA contrast, and rich amber-gold borders).
   - **Collapsible Responsive Sidebar**: Header 3-lines hamburger button toggling slim 56px icon mode on desktop (`>768px`) and slide-out navigation drawer on mobile viewports.
   - Multi-layer specular glass cards (`backdrop-filter: blur(20px)`), refined duotone gradients, and tokenized typography.

9. **Trust & Privacy First**:
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
