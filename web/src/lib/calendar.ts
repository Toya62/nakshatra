import { fetchBikramSambat, fetchGregorianDate } from './api';
import { BikramSambatDate, GregorianDate } from './types';

export type CalendarSystem = 'gregorian' | 'bikram';

const CALENDAR_STORAGE_KEY = 'nakshatra_calendar_system';

export function getCalendarSystem(): CalendarSystem {
  if (typeof window === 'undefined') return 'gregorian';
  const stored = localStorage.getItem(CALENDAR_STORAGE_KEY);
  if (stored === 'bikram' || stored === 'gregorian') {
    return stored;
  }
  return 'gregorian';
}

export function setCalendarSystem(system: CalendarSystem): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(CALENDAR_STORAGE_KEY, system);
}

export async function convertAdToBs(year: number, month: number, day: number): Promise<BikramSambatDate | null> {
  try {
    return await fetchBikramSambat(year, month, day);
  } catch (error) {
    console.error('Failed to convert AD to BS:', error);
    return null;
  }
}

export async function convertBsToAd(year: number, month: number, day: number): Promise<GregorianDate | null> {
  try {
    return await fetchGregorianDate(year, month, day);
  } catch (error) {
    console.error('Failed to convert BS to AD:', error);
    return null;
  }
}

export function formatDateDual(
  year: number,
  month: number,
  day: number,
  bsData?: BikramSambatDate | null,
  showBoth: boolean = true
): string {
  const adStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')} AD`;
  if (!showBoth || !bsData) {
    return adStr;
  }
  return `${bsData.formatted_ne || bsData.formatted} BS / ${adStr}`;
}
