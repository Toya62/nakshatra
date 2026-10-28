/**
 * Frontend configuration for Nakshatra
 * Centralized configuration for defaults, API endpoints, etc.
 */

export const DEFAULT_LOCATION = {
  lat: parseFloat(process.env.NEXT_PUBLIC_DEFAULT_LAT || "0"),
  lon: parseFloat(process.env.NEXT_PUBLIC_DEFAULT_LON || "0"),
  tz: process.env.NEXT_PUBLIC_DEFAULT_TZ || "UTC",
  place: process.env.NEXT_PUBLIC_DEFAULT_PLACE || "",
};

export const DEFAULT_AYANAMSA = process.env.NEXT_PUBLIC_DEFAULT_AYANAMSA || "jhora_lahiri";
export const DEFAULT_HOUSE_SYSTEM = process.env.NEXT_PUBLIC_DEFAULT_HOUSE_SYSTEM || "WholeSign";

export const DEFAULT_CALENDAR_SYSTEM = (process.env.NEXT_PUBLIC_DEFAULT_CALENDAR || "gregorian") as "gregorian" | "bikram";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/py";
