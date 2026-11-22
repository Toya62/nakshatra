import { BirthDataInput } from "./types";
import { DEFAULT_AYANAMSA, DEFAULT_HOUSE_SYSTEM } from "@/config/defaults";

export interface GeoPreset {
  name: string;
  lat: number;
  lon: number;
  tz: string;
}

export const RANDOM_LOCATIONS: GeoPreset[] = [
  { name: "Kathmandu, Nepal", lat: 27.7172, lon: 85.324, tz: "Asia/Kathmandu" },
  { name: "Ujjain, India", lat: 23.1765, lon: 75.7885, tz: "Asia/Kolkata" },
  { name: "Varanasi, India", lat: 25.3176, lon: 82.9739, tz: "Asia/Kolkata" },
  { name: "New Delhi, India", lat: 28.6139, lon: 77.209, tz: "Asia/Kolkata" },
  { name: "Pokhara, Nepal", lat: 28.2096, lon: 83.9856, tz: "Asia/Kathmandu" },
  { name: "Tokyo, Japan", lat: 35.6762, lon: 139.6503, tz: "Asia/Tokyo" },
  { name: "London, UK", lat: 51.5074, lon: -0.1278, tz: "Europe/London" },
  { name: "New York, USA", lat: 40.7128, lon: -74.006, tz: "America/New_York" },
  { name: "Sydney, Australia", lat: -33.8688, lon: 151.2093, tz: "Australia/Sydney" },
  { name: "Cairo, Egypt", lat: 30.0444, lon: 31.2357, tz: "Africa/Cairo" },
  { name: "Yangon, Myanmar", lat: 16.8661, lon: 96.1951, tz: "Asia/Yangon" },
  { name: "Singapore", lat: 1.3521, lon: 103.8198, tz: "Asia/Singapore" },
  { name: "Dubai, UAE", lat: 25.2048, lon: 55.2708, tz: "Asia/Dubai" },
  { name: "Paris, France", lat: 48.8566, lon: 2.3522, tz: "Europe/Paris" },
];

export const NEUTRAL_SSR_BIRTH_DATA: BirthDataInput = {
  year: 2000,
  month: 1,
  day: 1,
  hour: 12,
  minute: 0,
  second: 0,
  latitude: 23.1765,
  longitude: 75.7885,
  timezone: "Asia/Kolkata",
  place_name: "Ujjain, India",
  ayanamsa: DEFAULT_AYANAMSA || "jhora_lahiri",
  house_system: DEFAULT_HOUSE_SYSTEM || "WholeSign",
};

/**
 * Generate a randomized realistic birth data profile
 */
export function getRandomBirthData(excludeLocationName?: string): BirthDataInput {
  const eligibleLocations = excludeLocationName
    ? RANDOM_LOCATIONS.filter((l) => l.name !== excludeLocationName)
    : RANDOM_LOCATIONS;

  const loc = eligibleLocations[Math.floor(Math.random() * eligibleLocations.length)] || RANDOM_LOCATIONS[0];
  
  // Year: between 1970 and 2012
  const year = 1970 + Math.floor(Math.random() * 42);
  // Month: 1 to 12
  const month = 1 + Math.floor(Math.random() * 12);
  // Day: 1 to 28 (safe across all months and leap years)
  const day = 1 + Math.floor(Math.random() * 28);
  // Hour: 0 to 23
  const hour = Math.floor(Math.random() * 24);
  // Minute: 0 to 59
  const minute = Math.floor(Math.random() * 60);

  return {
    year,
    month,
    day,
    hour,
    minute,
    second: 0,
    latitude: loc.lat,
    longitude: loc.lon,
    timezone: loc.tz,
    place_name: loc.name,
    ayanamsa: DEFAULT_AYANAMSA || "jhora_lahiri",
    house_system: DEFAULT_HOUSE_SYSTEM || "WholeSign",
  };
}

/**
 * Check if a given birth data matches the specific personal DOB (May 22, 1997 / Palpa)
 * to ensure it is purged and replaced with a random profile.
 */
export function isPersonalDob(data: Partial<BirthDataInput> | null | undefined): boolean {
  if (!data) return false;
  if (data.year === 1997 && data.month === 5 && data.day === 22) return true;
  if (data.place_name && data.place_name.toLowerCase().includes("palpa")) return true;
  return false;
}
