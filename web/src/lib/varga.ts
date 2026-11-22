import type { ChartData } from "./types.ts";

/**
 * Divisional (varga) positions for the Kundali view.
 *
 * The backend returns divisional SIGNS in `chart.vargas` (BPHS rules, e.g.
 * Navamsha signs from mayaastrolib) but no divisional degrees, nakshatras
 * or houses. This module derives the rest client-side:
 *
 * - Sign / house: from `chart.vargas` (authoritative) and the varga
 *   Ascendant — never recomputed here.
 * - Degree within the divisional sign: the planet's position inside its
 *   segment of the D1 sign, scaled back to a 0-30 degree arc:
 *   `(degreeInSign * n) % 30`, where n is the division count. This keeps
 *   the degree consistent with the backend's divisional sign, which a
 *   plain `(longitude * n) % 360` would NOT (traditional varga signs do
 *   not follow the harmonic rule for fixed/dual signs).
 * - Nakshatra / pada: from the divisional longitude
 *   (sign index * 30 + divisional degree), mirroring
 *   `nakshatra/core.py::get_nakshatra` exactly (27 nakshatras of 13°20',
 *   pada = quarter of the nakshatra).
 *
 * Retrograde status is the same in every varga (motion is D1-based), so it
 * is carried over unchanged. Yogas and Ashtakavarga are D1-only by
 * definition and are NOT derived here — they are labelled D1 in the UI.
 */

export const ZODIAC_SIGNS = [
  "Aries",
  "Taurus",
  "Gemini",
  "Cancer",
  "Leo",
  "Virgo",
  "Libra",
  "Scorpio",
  "Sagittarius",
  "Capricorn",
  "Aquarius",
  "Pisces",
] as const;

export const SIGN_LORDS: Record<string, string> = {
  Aries: "Mars",
  Taurus: "Venus",
  Gemini: "Mercury",
  Cancer: "Moon",
  Leo: "Sun",
  Virgo: "Mercury",
  Libra: "Venus",
  Scorpio: "Mars",
  Sagittarius: "Jupiter",
  Capricorn: "Saturn",
  Aquarius: "Saturn",
  Pisces: "Jupiter",
};

/** Division count per varga, e.g. D9 -> 9. */
export const VARGA_DIVISORS: Record<string, number> = {
  D1: 1,
  D2: 2,
  D3: 3,
  D4: 4,
  D7: 7,
  D9: 9,
  D10: 10,
  D12: 12,
  D16: 16,
  D20: 20,
  D24: 24,
  D27: 27,
  D30: 30,
  D40: 40,
  D45: 45,
  D60: 60,
};

/** Full display names, e.g. D9 -> "Navamsha (Dharma & Spouse)". */
export const VARGA_NAMES: Record<string, string> = {
  D1: "Rasi (Root)",
  D2: "Hora (Wealth)",
  D3: "Drekkana (Siblings & Courage)",
  D4: "Chaturthamsa (Fortune & Home)",
  D7: "Saptamsa (Children & Lineage)",
  D9: "Navamsha (Dharma & Spouse)",
  D10: "Dasamsa (Career & Stature)",
  D12: "Dwadasamsa (Parents & Ancestry)",
  D16: "Shodasamsa (Vehicles & Happiness)",
  D20: "Vimsamsa (Spiritual Progress)",
  D24: "Chaturvimsamsa (Higher Learning)",
  D27: "Saptavimsamsa (Strengths & Weaknesses)",
  D30: "Trimsamsa (Arishta & Misfortune)",
  D40: "Khavedamsa (Auspicious Effects)",
  D45: "Akshavedamsa (All General Matters)",
  D60: "Shastiamsa (Karma & Past Lives)",
};

/** Short names for badges, e.g. D9 -> "Navamsha". */
export const VARGA_SHORT_NAMES: Record<string, string> = {
  D1: "Rasi",
  D2: "Hora",
  D3: "Drekkana",
  D4: "Chaturthamsa",
  D7: "Saptamsa",
  D9: "Navamsha",
  D10: "Dasamsa",
  D12: "Dwadasamsa",
  D16: "Shodasamsa",
  D20: "Vimsamsa",
  D24: "Chaturvimsamsa",
  D27: "Saptavimsamsa",
  D30: "Trimsamsa",
  D40: "Khavedamsa",
  D45: "Akshavedamsa",
  D60: "Shastiamsa",
};

/** (Nakshatra name, lord) in order — mirrors nakshatra/core.py NAKSHATRAS. */
export const NAKSHATRAS: ReadonlyArray<readonly [string, string]> = [
  ["Ashwini", "Ketu"],
  ["Bharani", "Venus"],
  ["Krittika", "Sun"],
  ["Rohini", "Moon"],
  ["Mrigashira", "Mars"],
  ["Ardra", "Rahu"],
  ["Punarvasu", "Jupiter"],
  ["Pushya", "Saturn"],
  ["Ashlesha", "Mercury"],
  ["Magha", "Ketu"],
  ["Purva Phalguni", "Venus"],
  ["Uttara Phalguni", "Sun"],
  ["Hasta", "Moon"],
  ["Chitra", "Mars"],
  ["Swati", "Rahu"],
  ["Vishakha", "Jupiter"],
  ["Anuradha", "Saturn"],
  ["Jyeshtha", "Mercury"],
  ["Mula", "Ketu"],
  ["Purva Ashadha", "Venus"],
  ["Uttara Ashadha", "Sun"],
  ["Shravana", "Moon"],
  ["Dhanishta", "Mars"],
  ["Shatabhisha", "Rahu"],
  ["Purva Bhadrapada", "Jupiter"],
  ["Uttara Bhadrapada", "Saturn"],
  ["Revati", "Mercury"],
];

const NAKSHATRA_SPAN = 360 / 27;

/** Nakshatra, lord and pada from an absolute sidereal longitude. */
export function getNakshatra(longitude: number): {
  nakshatra: string;
  lord: string;
  pada: number;
} {
  const lon = ((longitude % 360) + 360) % 360;
  const idx = Math.floor(lon / NAKSHATRA_SPAN) % 27;
  const [nakshatra, lord] = NAKSHATRAS[idx];
  const degInNak = lon % NAKSHATRA_SPAN;
  const pada = Math.min(Math.floor(degInNak / (NAKSHATRA_SPAN / 4)) + 1, 4);
  return { nakshatra, lord, pada };
}

/** Degree within the divisional sign for a D1 degree-in-sign. */
export function vargaDegree(degreeInSign: number, varga: string): number {
  const n = VARGA_DIVISORS[varga.toUpperCase()] ?? 1;
  if (n <= 1) return degreeInSign;
  // Floating-point guard: 29.9999999 -> 30 would flip the sign.
  const d = (degreeInSign * n) % 30;
  return d >= 29.999999 ? 0 : d;
}

function signIndex(sign: string): number {
  const i = ZODIAC_SIGNS.indexOf(sign as (typeof ZODIAC_SIGNS)[number]);
  return i === -1 ? 0 : i;
}

export interface VargaBody {
  name: string;
  sign: string;
  degreeInSign: number;
  nakshatra: string;
  nakshatraLord: string;
  pada: number;
  house: number;
  signLord: string;
  retrograde: boolean;
  isAsc: boolean;
}

interface D1Body {
  name: string;
  sign: string;
  degreeInSign: number;
  nakshatra: string;
  nakshatraLord: string;
  pada: number;
  house: number;
  retrograde: boolean;
  isAsc: boolean;
}

/** Backend varga map keys for the bodies the frontend renders. */
function vargaKeyFor(name: string): string {
  if (name.startsWith("Ascendant")) return "Ascendant";
  if (name === "Rahu") return "North Node";
  if (name === "Ketu") return "South Node";
  return name;
}

/** D1 rows straight from the chart payload. */
function d1Bodies(chart: ChartData): D1Body[] {
  const rows: D1Body[] = [
    {
      name: "Ascendant (Lagna)",
      sign: chart.ascendant.sign,
      degreeInSign: chart.ascendant.degree_in_sign,
      nakshatra: chart.ascendant.nakshatra,
      nakshatraLord: chart.ascendant.nakshatra_lord,
      pada: chart.ascendant.pada,
      house: 1,
      retrograde: false,
      isAsc: true,
    },
    ...chart.planets.map((p) => ({
      name: p.name,
      sign: p.sign,
      degreeInSign: p.degree_in_sign,
      nakshatra: p.nakshatra,
      nakshatraLord: p.nakshatra_lord,
      pada: p.pada,
      house: p.house,
      retrograde: p.retrograde,
      isAsc: false,
    })),
    {
      name: "Rahu",
      sign: chart.rahu.sign,
      degreeInSign: chart.rahu.degree_in_sign,
      nakshatra: chart.rahu.nakshatra,
      nakshatraLord: chart.rahu.nakshatra_lord,
      pada: chart.rahu.pada,
      house: chart.rahu.house,
      retrograde: true,
      isAsc: false,
    },
    {
      name: "Ketu",
      sign: chart.ketu.sign,
      degreeInSign: chart.ketu.degree_in_sign,
      nakshatra: chart.ketu.nakshatra,
      nakshatraLord: chart.ketu.nakshatra_lord,
      pada: chart.ketu.pada,
      house: chart.ketu.house,
      retrograde: true,
      isAsc: false,
    },
  ];
  return rows;
}

/**
 * Ephemeris rows for the selected varga. For D1 (or when the backend sent
 * no varga data) this is the D1 table unchanged. For any other varga the
 * sign/house come from `chart.vargas` and the degree/nakshatra/pada are
 * derived as documented above.
 */
export function getVargaPositions(chart: ChartData, varga: string): VargaBody[] {
  const vKey = varga.toUpperCase();
  const d1 = d1Bodies(chart);
  const vData = chart.vargas?.[vKey];
  if (vKey === "D1" || !vData) {
    return d1.map((b) => ({ ...b, signLord: SIGN_LORDS[b.sign] ?? "" }));
  }

  const ascSign = vData["Ascendant"] || chart.ascendant.sign;
  const ascIdx = signIndex(ascSign);
  return d1.map((b) => {
    const sign = vData[vargaKeyFor(b.name)] || b.sign;
    const sIdx = signIndex(sign);
    const degree = vargaDegree(b.degreeInSign, vKey);
    const divLon = sIdx * 30 + degree;
    const { nakshatra, lord, pada } = getNakshatra(divLon);
    return {
      name: b.name,
      sign,
      degreeInSign: degree,
      nakshatra,
      nakshatraLord: lord,
      pada,
      house: ((sIdx - ascIdx) % 12 + 12) % 12 + 1,
      signLord: SIGN_LORDS[sign] ?? "",
      retrograde: b.retrograde,
      isAsc: b.isAsc,
    };
  });
}

/** Ascendant (sign, degree, nakshatra, pada) in the selected varga. */
export function getVargaAscendant(
  chart: ChartData,
  varga: string,
): { sign: string; degreeInSign: number; nakshatra: string; pada: number } {
  const rows = getVargaPositions(chart, varga);
  const asc = rows.find((r) => r.isAsc) ?? rows[0];
  return {
    sign: asc.sign,
    degreeInSign: asc.degreeInSign,
    nakshatra: asc.nakshatra,
    pada: asc.pada,
  };
}

/** Moon (sign, degree) in the selected varga, or null when absent. */
export function getVargaMoon(
  chart: ChartData,
  varga: string,
): { sign: string; degreeInSign: number } | null {
  const rows = getVargaPositions(chart, varga);
  const moon = rows.find((r) => r.name === "Moon");
  return moon ? { sign: moon.sign, degreeInSign: moon.degreeInSign } : null;
}
