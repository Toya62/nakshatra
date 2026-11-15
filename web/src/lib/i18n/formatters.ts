import type { Language } from "./types";

const DEVANAGARI_DIGITS = ["०", "१", "२", "३", "४", "५", "६", "७", "८", "९"];

/**
 * Converts Western digits 0-9 in any string or number to Devanagari digits ०-९.
 */
export function toDevanagariDigits(input: number | string): string {
  const str = String(input);
  return str.replace(/\d/g, (digit) => DEVANAGARI_DIGITS[parseInt(digit, 10)]);
}

/**
 * Formats a number based on current language:
 * - In "ne" mode: converts digits to Devanagari numerals.
 * - In "en" mode: outputs standard Western digits.
 */
export function formatNumber(input: number | string, lang: Language): string {
  if (lang === "ne") {
    return toDevanagariDigits(input);
  }
  return String(input);
}

/**
 * Formats celestial degrees (e.g. 24.385°) with precision and language formatting.
 */
export function formatDegree(deg: number, lang: Language, decimals: number = 2): string {
  const fixed = deg.toFixed(decimals);
  return `${formatNumber(fixed, lang)}°`;
}

/**
 * Formats Year, Month, Day in YYYY-MM-DD format with localized digits.
 */
export function formatDateByLang(year: number, month: number, day: number, lang: Language): string {
  const m = String(month).padStart(2, "0");
  const d = String(day).padStart(2, "0");
  const raw = `${year}-${m}-${d}`;
  return formatNumber(raw, lang);
}
