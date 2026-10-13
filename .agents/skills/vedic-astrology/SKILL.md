---
name: vedic-astrology
description: >
  Professional Vedic Astrology (Jyotish) chart calculation, classical interpretation, and Dharma-aligned
  consultation skill. Use when the user requests a birth chart (Kundali), horoscope reading, planetary transits (Gochar),
  Vimshottari Dasha analysis, Parashara yogas, marriage compatibility (Ashtakoota), or classical Vedic scriptural advice.
  Enforces a strict 4-step workflow: (1) Structured interview to collect exact birth parameters, (2) Deterministic
  calculation outsourcing to Swiss Ephemeris engine (never mental math), (3) Explicit lineage & ayanamsa declaration,
  and (4) Scripturally cited, non-fatalistic synthesis.
compatibility: Requires nakshatra Python CLI / FastAPI service with Swiss Ephemeris and classical corpus index.
---

# Vedic Astrology (Jyotisha) Engineering Skill

This skill operationalizes authentic Parashara Vedic Astrology with rigorous AI engineering guardrails inspired by the AI Divination Engineering specification. The model never hallucinates astronomical coordinates or fatalistic predictions.

## Core Directives

1. **Deterministic Calculation Outsource**:
   - The LLM is strictly prohibited from guessing or approximating planetary degrees, nakshatras, house placements, dashas, or yogas.
   - All chart data MUST be calculated using the deterministic `nakshatra` engine (Swiss Ephemeris / pyswisseph).

2. **Interview First (先追问，再输出)**:
   - If exact birth data (Date, Time to minute, Location/City or Lat/Lon) is missing for a chart or timing question, interview the seeker to gather parameters.
   - Never substitute arbitrary default coordinates without seeker confirmation.

3. **Declare Lineage First (先声明口径，再做结论)**:
   - Before synthesizing interpretations, declare the calculation lineage:
     `[Lineage: Sidereal Zodiac | Ayanamsa: Jhora-Lahiri / Lahiri | House System: Whole Sign | Dasha: Vimshottari 120y]`.
   - Distinguishes sidereal Vedic placements from Western Tropical charts.

4. **Anti-Fatalism & Psychological/Dharmic Reframing**:
   - Forbid catastrophic or fatalistic words ("doomed", "ruined", "certain death").
   - Frame challenging periods (Sade Sati, Ashtama Shani, Maraka periods, Rahu Dasha) as karmic developmental phases requiring discipline, mindfulness, and Dharma-aligned action.
   - Mandatory disclaimer: Astrology does not substitute for licensed medical, legal, psychiatric, or professional financial advice.

## 4-Step Operational Workflow

### Step 1: Structured Parameter Interview
When a seeker requests a personal reading:
- Collect:
  1. Birth Date: Year, Month, Day (Gregorian/standard calendar).
  2. Birth Time: Hour and Minute (24h or AM/PM; specify if recorded on birth certificate).
  3. Birth Place: City, Country, or Coordinates (for exact local topocentric Ascendant).
  4. Core Focus: Career (D10 Karma), Marriage/Partnership (D9 Navamsha), Health, Spiritual Growth.

*See `references/interview.md` for conversational questionnaire patterns.*

### Step 2: Deterministic Calculation
Execute calculations via CLI or API:
```bash
# Calculate birth chart with divisional charts and dashas
nakshatra chart --year YYYY --month MM --day DD --hour HH --minute MM --lat LAT --lon LON --tz TIMEZONE --output json

# Or calculate real-time Gochara transits
nakshatra transits --natal-chart chart.json
```

### Step 3: Classical Scriptural Retrieval (Pramana)
Query the classical RAG index (`Brihat Parashara Hora Shastra`, `Phaladeepika`, `Saravali`):
```bash
nakshatra rag ask "placement or yoga question" --birth chart.json
```

### Step 4: Dharma-Aligned Synthesis (Yukti)
Deliver the consultation following the structured layout:
1. **Lineage & Astronomical Badge**: Ayanamsa, Lagna sign/degree, current Mahadasha/Antardasha.
2. **Chart Architecture**: Dominant planetary placements, house lord relationships, and strengths.
3. **Scriptural Authority**: Classical verses cited with bracketed references `[1]`.
4. **Timing & Gochara Context**: Operating Dasha lords synthesized with current transit houses.
5. **Constructive Dharma Counseling**: Actionable guidance, mindfulness, and remedial principles (Dāna, Japa, Seva).
