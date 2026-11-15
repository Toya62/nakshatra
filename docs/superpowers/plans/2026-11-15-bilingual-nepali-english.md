# Bilingual (Nepali & English) Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the Nakshatra Vedic Astrology application into a fully bilingual system (Nepali and English) across the complete user interface, astrological charts, tables, reports, Panchanga, and AI consultation with 100% type-safe dictionary coverage and zero translation gaps.

**Architecture:** A centralized, type-safe React internationalization system (`LanguageContext` + compile-time enforced `TranslationSchema`) powers all frontend components with instant language toggling, number localization (Devanagari ०–९ vs Western 0–9), and calendar synchronization. The backend FastAPI service and AI consultation engine are extended with an explicit `language: "en" | "ne"` parameter, delivering authentic, culturally resonant classical Nepali astrological syntheses or modern English analyses.

**Tech Stack:** Next.js 16 (App Router), React 19, TypeScript 5, Tailwind CSS, Python 3.11, FastAPI, Swiss Ephemeris (`mayaastrolib`).

**Spec:** Bilingual Jyotish Specification for Nakshatra Engine (Nepali / English full-stack localization).

## Global Constraints

- 100% TypeScript compile-time key parity: any missing key in `ne.ts` or `en.ts` must trigger a `TS2741` / `TS2322` build failure.
- Astrological accuracy: Nepali terms must adhere to authentic classical Jyotish standards (Brihat Parashara Hora Shastra, Jaimini Upadesha Sutra, and Nepal Panchanga Nirnayak Samiti conventions).
- No external heavy i18n runtime dependency bloat (use lightweight custom React Context + typed dictionaries).
- Instant, flicker-free client language switching persisted in `localStorage` under `nakshatra_language`.
- Numerals in Nepali mode format dynamically to Devanagari numerals (e.g. `१२° ३४'`) while preserving numerical calculation accuracy in data models.
- Responsive design: all Devanagari labels, badges, and tables must fit without horizontal blowout on 402px mobile viewports (iPhone 16 Pro).

## Review Focus

1. Devanagari line-height and clipping: Devanagari matras (e.g., ी, ु, ू, ै, ौ, ्र) clipping inside constrained buttons or table headers.
2. Number formatting consistency: Mathematical degree computations remaining floats while UI renders formatted Devanagari numerals in Nepali mode.
3. Chart SVG abbreviation fit: 2-character Devanagari Graha glyphs (सू, चं, मं, बु, गु, शु, श, रा, के) rendering clearly inside North Indian chart houses without overlapping boundaries.
4. AI Consultation language boundary: AI model adhering strictly to Nepali when `language="ne"` without leaking random English sentences or broken transliteration.
5. Storage synchronization: Switching calendar (BS/AD) or language (EN/NE) synchronizing seamlessly across components without requiring page reload.

---

### Task 1: Core i18n Type System, Number Formatter & Test Harness

**Files:**
- Create: `web/src/lib/i18n/types.ts`
- Create: `web/src/lib/i18n/formatters.ts`
- Create: `web/src/lib/i18n/formatters.test.ts`
- Modify: `web/package.json`

**Interfaces:**
- Consumes: None
- Produces: `Language = 'en' | 'ne'`, `TranslationSchema`, `toDevanagariDigits(num: number | string): string`, `formatNumber(num: number | string, lang: Language): string`, `formatDegree(deg: number, lang: Language): string`.

- [ ] **Step 1: Write failing unit test for formatters**

```typescript
// web/src/lib/i18n/formatters.test.ts
import { toDevanagariDigits, formatNumber, formatDegree } from "./formatters";

describe("i18n formatters", () => {
  test("converts arabic digits to devanagari", () => {
    expect(toDevanagariDigits("2026")).toBe("२०२६");
    expect(toDevanagariDigits(1997)).toBe("१९९७");
    expect(toDevanagariDigits("0123456789")).toBe("०१२३४५६७८९");
  });

  test("formats numbers by language", () => {
    expect(formatNumber(12.5, "ne")).toBe("१२.५");
    expect(formatNumber(12.5, "en")).toBe("12.5");
  });

  test("formats degrees by language", () => {
    expect(formatDegree(24.385, "ne", 2)).toBe("२४.३९°");
    expect(formatDegree(24.385, "en", 2)).toBe("24.39°");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test web/src/lib/i18n/formatters.test.ts || npx tsx web/src/lib/i18n/formatters.test.ts`
Expected: FAIL with module not found or missing exports.

- [ ] **Step 3: Implement `types.ts` and `formatters.ts`**

Define `TranslationSchema` in `web/src/lib/i18n/types.ts` encompassing all namespaces: `common`, `nav`, `birthForm`, `zodiac`, `planets`, `nakshatras`, `bhavas`, `kundali`, `panchanga`, `dasha`, `ashtakavarga`, `varshaphal`, `kalsarp`, `specialLagnas`, `chakras`, `rashiFal`, `muhurtha`, `compatibility`, `remedies`, `consultation`.
Implement `toDevanagariDigits`, `formatNumber`, and `formatDegree` in `web/src/lib/i18n/formatters.ts` replacing Arabic digits `0-9` with `०-९`.

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test web/src/lib/i18n/formatters.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/lib/i18n/
git commit -m "feat(i18n): add core i18n type schema and devanagari number formatters"
```

---

### Task 2: English & Nepali Master Dictionaries (`en.ts` and `ne.ts`)

**Files:**
- Create: `web/src/lib/i18n/dictionaries/en.ts`
- Create: `web/src/lib/i18n/dictionaries/ne.ts`
- Create: `web/src/lib/i18n/index.ts`
- Create: `web/src/lib/i18n/parity.test.ts`

**Interfaces:**
- Consumes: `TranslationSchema` from `web/src/lib/i18n/types.ts`
- Produces: `dictionaries: Record<Language, TranslationSchema>`, `getTranslation(lang: Language): TranslationSchema`.

- [ ] **Step 1: Write parity unit test**

```typescript
// web/src/lib/i18n/parity.test.ts
import { dictionaries } from "./index";

describe("i18n dictionary parity", () => {
  test("en and ne have identical keys across all namespaces", () => {
    const en = dictionaries.en;
    const ne = dictionaries.ne;
    expect(Object.keys(en).sort()).toEqual(Object.keys(ne).sort());
    for (const namespace of Object.keys(en) as (keyof typeof en)[]) {
      const enKeys = Object.keys(en[namespace]).sort();
      const neKeys = Object.keys(ne[namespace]).sort();
      expect(neKeys).toEqual(enKeys);
    }
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test web/src/lib/i18n/parity.test.ts`
Expected: FAIL with module not found.

- [ ] **Step 3: Implement `en.ts`, `ne.ts`, and `index.ts`**

Populate complete translations:
- Rashis: Mesha/मेष to Meena/मीन
- Grahas: Surya/सूर्य, Chandra/चन्द्र, Mangala/मङ्गल, Budha/बुध, Guru/गुरु, Shukra/शुक्र, Shani/शनि, Rahu/राहु, Ketu/केतु
- Bhavas 1-12: Tanu/तनु to Vyaya/व्यय
- 27 Nakshatras + Abhijit
- Navatara, Tajik Sahams, Ashtakoota, Ashtakavarga, Panchanga, Muhurtha, Remedies, Consultation.
Enforce `export const en: TranslationSchema = { ... }` and `export const ne: TranslationSchema = { ... }` ensuring TypeScript validates completeness at compile time.

- [ ] **Step 4: Run parity test to verify it passes**

Run: `node --test web/src/lib/i18n/parity.test.ts && cd web && npx tsc --noEmit`
Expected: PASS with 0 errors.

- [ ] **Step 5: Commit**

```bash
git add web/src/lib/i18n/
git commit -m "feat(i18n): create complete english and nepali dictionaries with key parity"
```

---

### Task 3: Global Language Context & Persistence Hook

**Files:**
- Create: `web/src/context/LanguageContext.tsx`
- Modify: `web/src/app/layout.tsx`
- Modify: `web/src/app/globals.css`

**Interfaces:**
- Consumes: `dictionaries`, `formatNumber`, `toDevanagariDigits` from `web/src/lib/i18n`
- Produces: `LanguageProvider`, `useLanguage(): { lang: Language, setLang: (l: Language) => void, t: TranslationSchema, num: (n: number | string) => string, deg: (d: number) => string }`

- [ ] **Step 1: Write component integration test**

```tsx
// web/src/context/LanguageContext.test.tsx
import { renderHook, act } from "@testing-library/react";
import { LanguageProvider, useLanguage } from "./LanguageContext";

test("defaults to en and toggles to ne with number formatting", () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <LanguageProvider>{children}</LanguageProvider>
  );
  const { result } = renderHook(() => useLanguage(), { wrapper });
  expect(result.current.lang).toBe("en");
  expect(result.current.num(2026)).toBe("2026");

  act(() => {
    result.current.setLang("ne");
  });
  expect(result.current.lang).toBe("ne");
  expect(result.current.num(2026)).toBe("२०२६");
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test web/src/context/LanguageContext.test.tsx`
Expected: FAIL

- [ ] **Step 3: Implement `LanguageContext.tsx` and integrate in `layout.tsx`**

- Create `LanguageContext.tsx` storing `nakshatra_language` in `localStorage`, dispatching custom event `languageChanged`.
- Add Google Fonts for `Mukta` and `Noto Sans Devanagari` in `web/src/app/layout.tsx` with `font-sans` CSS variable fallback.
- Wrap `children` inside `<LanguageProvider>`.

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test web/src/context/LanguageContext.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/context/LanguageContext.tsx web/src/app/layout.tsx web/src/app/globals.css
git commit -m "feat(i18n): implement LanguageProvider and Devanagari font typography"
```

---

### Task 4: Navigation, Header Language Toggle & Sidebar Localization

**Files:**
- Create: `web/src/components/LanguageToggle.tsx`
- Modify: `web/src/components/Navbar.tsx:85-125`
- Modify: `web/src/components/Sidebar.tsx:1-200`

**Interfaces:**
- Consumes: `useLanguage()`
- Produces: Visual language toggle button in Navbar, localized sidebar navigation tabs and section labels.

- [ ] **Step 1: Write test for LanguageToggle**

```tsx
// web/src/components/LanguageToggle.test.tsx
import { render, fireEvent } from "@testing-library/react";
import { LanguageToggle } from "./LanguageToggle";
import { LanguageProvider } from "@/context/LanguageContext";

test("LanguageToggle switches language on click", () => {
  const { getByRole } = render(
    <LanguageProvider>
      <LanguageToggle />
    </LanguageProvider>
  );
  const btn = getByRole("button");
  expect(btn.textContent).toContain("ने");
  fireEvent.click(btn);
  expect(btn.textContent).toContain("EN");
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test web/src/components/LanguageToggle.test.tsx`
Expected: FAIL with `LanguageToggle` not found.

- [ ] **Step 3: Implement `LanguageToggle.tsx`, update `Navbar.tsx` and `Sidebar.tsx`**

- In `LanguageToggle.tsx`, render toggle button `[EN | ने]` with gold border highlight on active state.
- In `Navbar.tsx`, mount `<LanguageToggle />` next to `<ThemeToggle />`.
- In `Sidebar.tsx`, update `NAV_ITEMS` and category titles to read dynamically from `t.nav[item.id]`.

- [ ] **Step 4: Run test and typecheck**

Run: `cd web && npx tsc --noEmit`
Expected: PASS with 0 errors.

- [ ] **Step 5: Commit**

```bash
git add web/src/components/LanguageToggle.tsx web/src/components/Navbar.tsx web/src/components/Sidebar.tsx
git commit -m "feat(i18n): mount LanguageToggle in Navbar and localize Sidebar items"
```

---

### Task 5: Birth Input Form & Calendar Localization

**Files:**
- Modify: `web/src/components/BirthForm.tsx:1-350`
- Modify: `web/src/components/CalendarSwitcher.tsx:1-48`
- Modify: `web/src/components/BirthSummaryPill.tsx:1-120`

**Interfaces:**
- Consumes: `useLanguage()`, `formatNumber`
- Produces: Fully translated birth parameters form (English / Nepali labels, placeholders, errors, BS/AD helper text, Ayanamsa options).

- [ ] **Step 1: Write verification test for BirthForm labels**

Verify that all labels in `BirthForm` use `t.birthForm.*` keys without hardcoded English strings.

- [ ] **Step 2: Verify existing hardcoded strings in BirthForm**

Run: `grep -E "Date of Birth|Birth Time|Latitude|Longitude|Calculate" web/src/components/BirthForm.tsx`
Expected: Lists hardcoded strings needing localization.

- [ ] **Step 3: Refactor `BirthForm.tsx`, `CalendarSwitcher.tsx`, and `BirthSummaryPill.tsx`**

- Replace hardcoded text with `t.birthForm.dob`, `t.birthForm.tob`, `t.birthForm.place`, `t.birthForm.ayanamsa`, `t.birthForm.calculateBtn`, etc.
- In `CalendarSwitcher.tsx`, show `वि.सं.` / `ई.सं.` when `lang === 'ne'` and `BS` / `AD` when `lang === 'en'`.
- Format dates in `BirthSummaryPill.tsx` with Devanagari numerals when in Nepali mode.

- [ ] **Step 4: Typecheck and lint**

Run: `cd web && npx tsc --noEmit && npm run lint`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/components/BirthForm.tsx web/src/components/CalendarSwitcher.tsx web/src/components/BirthSummaryPill.tsx
git commit -m "feat(i18n): localize BirthForm, CalendarSwitcher, and BirthSummaryPill"
```

---

### Task 6: North Indian Kundali & Planets Table Localization

**Files:**
- Modify: `web/src/components/NorthIndianChart.tsx:1-350`
- Modify: `web/src/components/PlanetsTable.tsx:1-250`

**Interfaces:**
- Consumes: `useLanguage()`, `t.zodiac`, `t.planets`, `t.bhavas`, `num`
- Produces: Bilingual SVG Kundali chart (Devanagari house numbers & Graha glyphs when in Nepali mode; English abbreviations when in English mode), translated Planets data table with localized dignities and degrees.

- [ ] **Step 1: Write test for chart glyph selection**

Verify helper `getGrahaGlyph(planet: string, lang: Language)` returns `सू` for Sun in `ne`, and `Su` in `en`.

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/chart_glyph.test.ts`
Expected: FAIL

- [ ] **Step 3: Implement bilingual rendering in `NorthIndianChart.tsx` and `PlanetsTable.tsx`**

- In `NorthIndianChart.tsx`:
  - When `lang === "ne"`, render Devanagari numerals for house numbers (`num(h.signNum)`) and Devanagari Graha abbreviations (`सू, चं, मं, बु, गु, शु, श, रा, के`).
  - When `lang === "en"`, render standard Arabic numbers (`1..12`) and English abbreviations (`Su, Mo, Ma, Me, Ju, Ve, Sa, Ra, Ke`).
  - Localize house popup hover card with Sanskrit/Nepali bhava significations.
- In `PlanetsTable.tsx`:
  - Translate table headers: Graha, Rashi, Degree, Nakshatra, Pada, Dignity, House.
  - Dignities: `Exalted` -> `उच्च`, `Debilitated` -> `नीच`, `Own Sign` -> `स्वक्षेत्र`, `Moolatrikona` -> `मूलत्रिकोण`, `Friendly` -> `मित्र`, `Enemy` -> `शत्रु`.
  - Format degrees as `num(deg)` + `°`.

- [ ] **Step 4: Typecheck and build**

Run: `cd web && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/components/NorthIndianChart.tsx web/src/components/PlanetsTable.tsx
git commit -m "feat(i18n): localize NorthIndianChart SVG glyphs and PlanetsTable"
```

---

### Task 7: Panchanga, Dasha & Classical Views Localization

**Files:**
- Modify: `web/src/components/PanchangaView.tsx:1-300`
- Modify: `web/src/components/DashaView.tsx:1-300`
- Modify: `web/src/components/YogasView.tsx:1-200`
- Modify: `web/src/components/AshtakavargaView.tsx:1-250`

**Interfaces:**
- Consumes: `useLanguage()`, `t.panchanga`, `t.dasha`, `t.yogas`, `num`
- Produces: Localized daily Panchanga dashboard, Vimshottari Dasha period trees, Yogas catalogue, and Ashtakavarga charts.

- [ ] **Step 1: Audit hardcoded strings in PanchangaView and DashaView**

Run: `grep -E "Tithi|Nakshatra|Sunrise|Sunset|Rahu Kalam|Mahadasha|Antardasha" web/src/components/PanchangaView.tsx web/src/components/DashaView.tsx`
Expected: Lists keys to map into `t.panchanga` and `t.dasha`.

- [ ] **Step 2: Update `PanchangaView.tsx`**

- Map Tithi, Vara, Nakshatra, Yoga, Karana, Sunrise/Sunset, Rahu Kaal, Yamaghanta to `t.panchanga.*`.
- Render solar/lunar month and paksha (शुक्ल / कृष्ण पक्ष).

- [ ] **Step 3: Update `DashaView.tsx`, `YogasView.tsx`, and `AshtakavargaView.tsx`**

- Localize Dasha headers, planet names, dates (formatted in Devanagari when `ne`).
- Localize Yoga classifications (Benefic/शुभ, Malefic/अशुभ) and descriptions.
- Localize Sarvashtakavarga table headers and score ratings.

- [ ] **Step 4: Typecheck**

Run: `cd web && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/components/PanchangaView.tsx web/src/components/DashaView.tsx web/src/components/YogasView.tsx web/src/components/AshtakavargaView.tsx
git commit -m "feat(i18n): localize Panchanga, Dasha, Yogas, and Ashtakavarga views"
```

---

### Task 8: Phase 2 Feature Views Localization (`Varshaphal`, `Kalsarp`, `Special Lagnas`, `Chakras`, `Rashi Fal`)

**Files:**
- Modify: `web/src/components/VarshaphalView.tsx`
- Modify: `web/src/components/KalsarpView.tsx`
- Modify: `web/src/components/SpecialLagnasView.tsx`
- Modify: `web/src/components/ChakraView.tsx`
- Modify: `web/src/components/RashiFalView.tsx`

**Interfaces:**
- Consumes: `useLanguage()`, `t.varshaphal`, `t.kalsarp`, `t.specialLagnas`, `t.chakras`, `t.rashiFal`, `num`
- Produces: Localized Phase 2 views with translated titles, cards, tables, badges, and summaries.

- [ ] **Step 1: Map all Phase 2 view labels to typed dictionary**

Verify `t.varshaphal`, `t.kalsarp`, `t.specialLagnas`, `t.chakras`, and `t.rashiFal` include all table headers, badge titles, and card sections.

- [ ] **Step 2: Update `VarshaphalView.tsx` and `KalsarpView.tsx`**

- Varshaphal: Year Lord (वर्षेश्वर), Muntha (मुन्था), Sahams (सहम), Month Lords (मासपति).
- Kalsarp: 12 Kalsarp types (अनन्त, कुलिक...), Full/Partial badges (पूर्ण / आंशिक), Graha axis table.

- [ ] **Step 3: Update `SpecialLagnasView.tsx`, `ChakraView.tsx`, and `RashiFalView.tsx`**

- Special Lagnas: Arudha, Upapada, Indu, Bhrigu Bindu, Ghati, Sri, Karakamsha.
- Chakras: Navatara (९ तारा), Panchadha Maitri (५ मैत्री - अधिमित्र, मित्र, सम, शत्रु, अधिशत्रु), Ghatchakra (घटचक्र).
- Rashi Fal: Chandra Lagna, Sade Sati phases (आद्य, मध्य, अन्त्य चरण), Period controls (दैनिक, साप्ताहिक, मासिक, वार्षिक).

- [ ] **Step 4: Typecheck and lint**

Run: `cd web && npx tsc --noEmit && npm run lint`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/components/VarshaphalView.tsx web/src/components/KalsarpView.tsx web/src/components/SpecialLagnasView.tsx web/src/components/ChakraView.tsx web/src/components/RashiFalView.tsx
git commit -m "feat(i18n): localize all Phase 2 views (Varshaphal, Kalsarp, Lagnas, Chakras, RashiFal)"
```

---

### Task 9: Compatibility, Muhurtha & Remedies Localization

**Files:**
- Modify: `web/src/components/CompatibilityView.tsx`
- Modify: `web/src/components/MuhurthaView.tsx`
- Modify: `web/src/components/RemediesView.tsx`

**Interfaces:**
- Consumes: `useLanguage()`, `t.compatibility`, `t.muhurtha`, `t.remedies`, `num`
- Produces: Localized Ashtakoota Milan (36 Gunas), Vivaha/Griha Pravesh Muhurthas, and Graha Remedies.

- [ ] **Step 1: Check Ashtakoota Gunas translation keys**

Ensure 8 Kootas: Varna (वर्ण), Vashya (वश्य), Tara (तारा), Yoni (योनि), Graha Maitri (ग्रहमैत्री), Gana (गण), Bhakoot (भकूट), Nadi (नाड़ी) are defined in dictionary.

- [ ] **Step 2: Update `CompatibilityView.tsx`**

- Localize groom/bride birth parameter inputs, Ashtakoota 36 points table, Manglik dosha analysis and cancellation verdicts.

- [ ] **Step 3: Update `MuhurthaView.tsx` and `RemediesView.tsx`**

- Muhurtha: Shuba activities (विवाह, व्रतबन्ध, गृहप्रवेश, नामकरण, व्यापार प्रारम्भ), quality badges (उत्तम, मध्यम, त्याज्य).
- Remedies: Ratna (रत्न), Mantra (मन्त्र जप), Daan (दान), Rudraksha (रुद्राक्ष).

- [ ] **Step 4: Typecheck**

Run: `cd web && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/components/CompatibilityView.tsx web/src/components/MuhurthaView.tsx web/src/components/RemediesView.tsx
git commit -m "feat(i18n): localize Compatibility, Muhurtha, and Remedies views"
```

---

### Task 10: Backend & AI Consultation Bilingual Engine

**Files:**
- Modify: `nakshatra/ai/service.py:1-250`
- Modify: `nakshatra/api.py:1-400`
- Modify: `web/src/components/ConsultationView.tsx:1-400`
- Test: `tests/test_bilingual_ai.py`

**Interfaces:**
- Consumes: Request `language: Literal["en", "ne"] = "en"` in `/api/py/chat` and `/api/py/consultation`
- Produces: Backend AI prompt routing in classical Nepali or modern English; translated Consultation UI.

- [ ] **Step 1: Write backend test for bilingual prompt construction**

```python
# tests/test_bilingual_ai.py
from nakshatra.ai.service import build_astrologer_system_prompt

def test_system_prompt_language():
    prompt_en = build_astrologer_system_prompt(language="en")
    assert "Vedic Astrologer" in prompt_en
    assert "English" in prompt_en

    prompt_ne = build_astrologer_system_prompt(language="ne")
    assert "तपाईं एक सिद्ध, विद्वान तथा धर्मनिष्ठ वैदिक ज्योतिषाचार्य हुनुहुन्छ" in prompt_ne
    assert "नेपाली" in prompt_ne
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_bilingual_ai.py`
Expected: FAIL (argument `language` unexpected or prompt function missing).

- [ ] **Step 3: Implement bilingual prompt logic in `service.py` and `api.py`**

- In `nakshatra/ai/service.py`: add `language: Literal["en", "ne"] = "en"` to `ConsultationEngine` / prompt generator. For `ne`, load sacred Nepali astrologer persona with classical Sanskrit-rooted Nepali vocabulary and respectful honorifics (तपाईं, हजुर, ग्रह शान्ति).
- In `nakshatra/api.py`: accept `language: Optional[str] = "en"` in `ChatRequest` schema and forward to AI service.
- In `web/src/components/ConsultationView.tsx`: translate UI strings, sample query pills (e.g., "मेरो करियर र आर्थिक स्थिति कस्तो रहनेछ?", "साढे सातीको प्रभाव र उपाय के हो?"), and include current `lang` in request body.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_bilingual_ai.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add nakshatra/ai/service.py nakshatra/api.py web/src/components/ConsultationView.tsx tests/test_bilingual_ai.py
git commit -m "feat(ai): support bilingual Nepali and English AI consultation"
```

---

### Task 11: End-to-End Build, Parity Verification & Mobile Responsiveness Check

**Files:**
- Modify: `web/package.json` (add `test:i18n` script)
- Test: `web/src/lib/i18n/parity.test.ts`
- Test: Full TypeScript check & Next.js production build

**Interfaces:**
- Consumes: All modules
- Produces: Clean zero-error production build with 100% bilingual parity.

- [ ] **Step 1: Run complete i18n parity test**

Run: `npm run test:i18n` in `web/`
Expected: PASS (0 missing keys across all 20 namespaces).

- [ ] **Step 2: Run complete TypeScript build check**

Run: `cd web && npx tsc --noEmit && npm run build`
Expected: PASS with 0 errors.

- [ ] **Step 3: Run Python test suite**

Run: `.venv/bin/pytest tests/`
Expected: All 267+ tests PASS.

- [ ] **Step 4: Commit and tag**

```bash
git add web/package.json
git commit -m "chore(i18n): finalize bilingual build scripts and test verification"
```
