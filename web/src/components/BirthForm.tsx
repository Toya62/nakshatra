"use client";

import React, { useState, useEffect, useRef } from "react";
import { BirthDataInput, BikramSambatDate, PlaceResult, TimezoneOffsetInfo } from "@/lib/types";
import { searchPlaces, fetchTimezoneOffset } from "@/lib/api";
import { MapPin, Calendar, Clock, Settings, Sparkles, Check, Globe, Compass, Sliders } from "lucide-react";
import { DEFAULT_LOCATION } from "@/config/defaults";
import { CalendarSwitcher } from "./CalendarSwitcher";
import { getCalendarSystem, setCalendarSystem, convertAdToBs, convertBsToAd, CalendarSystem } from "@/lib/calendar";

export const NEPALI_MONTHS = [
  { index: 1, name_en: "Baishakh", name_ne: "वैशाख" },
  { index: 2, name_en: "Jestha", name_ne: "जेठ" },
  { index: 3, name_en: "Ashadh", name_ne: "असार" },
  { index: 4, name_en: "Shrawan", name_ne: "साउन" },
  { index: 5, name_en: "Bhadra", name_ne: "भदौ" },
  { index: 6, name_en: "Ashwin", name_ne: "असोज" },
  { index: 7, name_en: "Kartik", name_ne: "कात्तिक" },
  { index: 8, name_en: "Mangsir", name_ne: "मंसिर" },
  { index: 9, name_en: "Poush", name_ne: "पुस" },
  { index: 10, name_en: "Magh", name_ne: "माघ" },
  { index: 11, name_en: "Falgun", name_ne: "फागुन" },
  { index: 12, name_en: "Chaitra", name_ne: "चैत" },
];

interface Props {
  initialData?: BirthDataInput;
  onSubmit: (data: BirthDataInput) => void;
  loading?: boolean;
}

const PRESETS = [
  { name: "Palpa, Nepal", lat: 27.8667, lon: 83.4833, tz: "Asia/Kathmandu" },
  { name: "Kathmandu, Nepal", lat: 27.7172, lon: 85.3240, tz: "Asia/Kathmandu" },
  { name: "Yangon, Myanmar", lat: 16.8661, lon: 96.1951, tz: "Asia/Yangon" },
  { name: "Varanasi, India", lat: 25.3176, lon: 82.9739, tz: "Asia/Kolkata" },
  { name: "New Delhi, India", lat: 28.6139, lon: 77.2090, tz: "Asia/Kolkata" },
  { name: "London, UK", lat: 51.5074, lon: -0.1278, tz: "Europe/London" },
  { name: "New York, USA", lat: 40.7128, lon: -74.0060, tz: "America/New_York" },
];

const COMMON_TIMEZONES = [
  { value: "Asia/Yangon", label: "Asia/Yangon (UTC +06:30) • Myanmar / Burma" },
  { value: "Asia/Kathmandu", label: "Asia/Kathmandu (UTC +05:45) • Nepal" },
  { value: "Asia/Kolkata", label: "Asia/Kolkata (UTC +05:30) • India, Sri Lanka" },
  { value: "Asia/Dhaka", label: "Asia/Dhaka (UTC +06:00) • Bangladesh" },
  { value: "Asia/Bangkok", label: "Asia/Bangkok (UTC +07:00) • Thailand, Vietnam, Cambodia" },
  { value: "Asia/Singapore", label: "Asia/Singapore (UTC +08:00) • Singapore, Malaysia" },
  { value: "Asia/Hong_Kong", label: "Asia/Hong_Kong (UTC +08:00) • Hong Kong" },
  { value: "Asia/Tokyo", label: "Asia/Tokyo (UTC +09:00) • Japan" },
  { value: "Asia/Dubai", label: "Asia/Dubai (UTC +04:00) • UAE, Gulf" },
  { value: "Europe/London", label: "Europe/London (UTC +00:00) • UK" },
  { value: "Europe/Paris", label: "Europe/Paris (UTC +01:00) • France, Germany" },
  { value: "Europe/Berlin", label: "Europe/Berlin (UTC +01:00) • Central Europe" },
  { value: "America/New_York", label: "America/New_York (UTC -05:00) • US Eastern" },
  { value: "America/Chicago", label: "America/Chicago (UTC -06:00) • US Central" },
  { value: "America/Denver", label: "America/Denver (UTC -07:00) • US Mountain" },
  { value: "America/Los_Angeles", label: "America/Los_Angeles (UTC -08:00) • US Pacific" },
  { value: "Australia/Sydney", label: "Australia/Sydney (UTC +10:00) • Australia" },
  { value: "UTC", label: "UTC (UTC +00:00) • Universal Time" },
];

export const BirthForm: React.FC<Props> = ({ initialData, onSubmit, loading }) => {
  // Store values as editable strings so users can clear inputs without getting trapped on "0"
  const [year, setYear] = useState(String(initialData?.year ?? 1997));
  const [month, setMonth] = useState(String(initialData?.month ?? 5));
  const [day, setDay] = useState(String(initialData?.day ?? 22));
  const [hour, setHour] = useState(String(initialData?.hour ?? 4));
  const [minute, setMinute] = useState(String(initialData?.minute ?? 53));
  const [second, setSecond] = useState(String(initialData?.second ?? 0));

  const [lat, setLat] = useState(String(initialData?.latitude ?? (DEFAULT_LOCATION.lat || 27.8667)));
  const [lon, setLon] = useState(String(initialData?.longitude ?? (DEFAULT_LOCATION.lon || 83.4833)));
  const [tz, setTz] = useState(initialData?.timezone || DEFAULT_LOCATION.tz || "Asia/Kathmandu");
  const [place, setPlace] = useState(initialData?.place_name || DEFAULT_LOCATION.place || "");

  const [ayanamsa, setAyanamsa] = useState(initialData?.ayanamsa || "jhora_lahiri");
  const [houseSystem, setHouseSystem] = useState(initialData?.house_system || "WholeSign");

  // Calendar System state (Gregorian AD or Bikram Sambat BS)
  const [calendarSystem, setCalendarSystemState] = useState<CalendarSystem>("gregorian");
  const [bsYear, setBsYear] = useState("2054");
  const [bsMonth, setBsMonth] = useState("2");
  const [bsDay, setBsDay] = useState("9");
  const [bsDateInfo, setBsDateInfo] = useState<BikramSambatDate | null>(null);

  // Sync calendar system on mount and on custom event
  useEffect(() => {
    setCalendarSystemState(getCalendarSystem());
    const handleCalChange = (e: Event) => {
      const customEvent = e as CustomEvent<CalendarSystem>;
      if (customEvent.detail) {
        setCalendarSystemState(customEvent.detail);
      }
    };
    window.addEventListener("calendarSystemChanged", handleCalChange);
    return () => window.removeEventListener("calendarSystemChanged", handleCalChange);
  }, []);

  // Sync AD -> BS date conversion
  useEffect(() => {
    let active = true;
    const y = parseInt(year, 10);
    const m = parseInt(month, 10);
    const d = parseInt(day, 10);
    if (!isNaN(y) && !isNaN(m) && !isNaN(d) && y >= 1900 && m >= 1 && m <= 12 && d >= 1 && d <= 31) {
      convertAdToBs(y, m, d).then((res) => {
        if (active && res) {
          setBsDateInfo(res);
          if (calendarSystem === "gregorian") {
            setBsYear(String(res.year));
            setBsMonth(String(res.month));
            setBsDay(String(res.day));
          }
        }
      });
    }
    return () => {
      active = false;
    };
  }, [year, month, day, calendarSystem]);

  const syncBsToAd = async (yStr: string, mStr: string, dStr: string) => {
    const y = parseInt(yStr, 10);
    const m = parseInt(mStr, 10);
    const d = parseInt(dStr, 10);
    if (!isNaN(y) && !isNaN(m) && !isNaN(d) && y >= 1970 && y <= 2100 && m >= 1 && m <= 12 && d >= 1 && d <= 32) {
      const ad = await convertBsToAd(y, m, d);
      if (ad) {
        setYear(String(ad.year));
        setMonth(String(ad.month));
        setDay(String(ad.day));
      }
    }
  };

  const handleBsYearChange = (val: string) => {
    const cleaned = val.replace(/[^0-9]/g, "").slice(0, 4);
    setBsYear(cleaned);
    syncBsToAd(cleaned, bsMonth, bsDay);
  };

  const handleBsYearBlur = () => {
    if (!bsYear) {
      setBsYear("2054");
      syncBsToAd("2054", bsMonth, bsDay);
      return;
    }
    const y = parseInt(bsYear, 10);
    if (y < 1970) {
      setBsYear("1970");
      syncBsToAd("1970", bsMonth, bsDay);
    } else if (y > 2100) {
      setBsYear("2100");
      syncBsToAd("2100", bsMonth, bsDay);
    }
  };

  const handleBsMonthChange = (val: string) => {
    setBsMonth(val);
    syncBsToAd(bsYear, val, bsDay);
  };

  const handleBsDayChange = (val: string) => {
    const cleaned = val.replace(/[^0-9]/g, "").slice(0, 2);
    setBsDay(cleaned);
    syncBsToAd(bsYear, bsMonth, cleaned);
  };

  const handleBsDayBlur = () => {
    if (!bsDay) {
      setBsDay("1");
      syncBsToAd(bsYear, bsMonth, "1");
      return;
    }
    const d = parseInt(bsDay, 10);
    if (d < 1) {
      setBsDay("1");
      syncBsToAd(bsYear, bsMonth, "1");
    } else if (d > 32) {
      setBsDay("32");
      syncBsToAd(bsYear, bsMonth, "32");
    }
  };

  // Geocoding live search state
  const [query, setQuery] = useState(place);
  const [suggestions, setSuggestions] = useState<PlaceResult[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showManualCoords, setShowManualCoords] = useState(false);
  const [tzInfo, setTzInfo] = useState<TimezoneOffsetInfo | null>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Sync internal state when initialData prop changes
  useEffect(() => {
    if (!initialData) return;
    setYear(String(initialData.year));
    setMonth(String(initialData.month));
    setDay(String(initialData.day));
    setHour(String(initialData.hour));
    setMinute(String(initialData.minute));
    setSecond(String(initialData.second ?? 0));
    setLat(String(initialData.latitude));
    setLon(String(initialData.longitude));
    setTz(initialData.timezone);
    setPlace(initialData.place_name || "");
    setQuery(initialData.place_name || "");
    if (initialData.ayanamsa) setAyanamsa(initialData.ayanamsa);
    if (initialData.house_system) setHouseSystem(initialData.house_system);
  }, [initialData]);

  // Auto-resolve timezone offset whenever date or timezone changes
  useEffect(() => {
    let active = true;
    const y = parseInt(year, 10);
    const m = parseInt(month, 10);
    const d = parseInt(day, 10);
    const h = parseInt(hour, 10);
    const min = parseInt(minute, 10);

    if (!isNaN(y) && !isNaN(m) && !isNaN(d) && y > 1000 && m >= 1 && m <= 12 && d >= 1 && d <= 31) {
      fetchTimezoneOffset(tz, y, m, d, isNaN(h) ? 0 : h, isNaN(min) ? 0 : min)
        .then((info) => {
          if (active && info) setTzInfo(info);
        })
        .catch(() => {});
    }
    return () => {
      active = false;
    };
  }, [tz, year, month, day, hour, minute]);

  // Handlers for date / time fields allowing free clearing & typing
  const handleYearChange = (val: string) => {
    setYear(val.replace(/[^0-9]/g, "").slice(0, 4));
  };
  const handleYearBlur = () => {
    if (!year) {
      setYear("1997");
      return;
    }
    const y = parseInt(year, 10);
    if (y < 1000) setYear("1997");
    else if (y > 2100) setYear("2100");
  };

  const handleMonthChange = (val: string) => {
    setMonth(val.replace(/[^0-9]/g, "").slice(0, 2));
  };
  const handleMonthBlur = () => {
    if (!month) {
      setMonth("1");
      return;
    }
    const m = parseInt(month, 10);
    if (m < 1) setMonth("1");
    else if (m > 12) setMonth("12");
  };

  const handleDayChange = (val: string) => {
    setDay(val.replace(/[^0-9]/g, "").slice(0, 2));
  };
  const handleDayBlur = () => {
    if (!day) {
      setDay("1");
      return;
    }
    const d = parseInt(day, 10);
    if (d < 1) setDay("1");
    else if (d > 31) setDay("31");
  };

  const handleHourChange = (val: string) => {
    setHour(val.replace(/[^0-9]/g, "").slice(0, 2));
  };
  const handleHourBlur = () => {
    if (!hour) {
      setHour("0");
      return;
    }
    const h = parseInt(hour, 10);
    if (h < 0) setHour("0");
    else if (h > 23) setHour("23");
  };

  const handleMinuteChange = (val: string) => {
    setMinute(val.replace(/[^0-9]/g, "").slice(0, 2));
  };
  const handleMinuteBlur = () => {
    if (!minute) {
      setMinute("0");
      return;
    }
    const min = parseInt(minute, 10);
    if (min < 0) setMinute("0");
    else if (min > 59) setMinute("59");
  };

  const handleSecondChange = (val: string) => {
    setSecond(val.replace(/[^0-9]/g, "").slice(0, 2));
  };
  const handleSecondBlur = () => {
    if (!second) {
      setSecond("0");
      return;
    }
    const s = parseInt(second, 10);
    if (s < 0) setSecond("0");
    else if (s > 59) setSecond("59");
  };

  const handleLatChange = (val: string) => {
    if (/^-?[0-9]*\.?[0-9]*$/.test(val)) setLat(val);
  };
  const handleLatBlur = () => {
    if (lat === "" || lat === "-") setLat("0");
  };

  const handleLonChange = (val: string) => {
    if (/^-?[0-9]*\.?[0-9]*$/.test(val)) setLon(val);
  };
  const handleLonBlur = () => {
    if (lon === "" || lon === "-") setLon("0");
  };

  // Handle location search debouncing
  const handlePlaceChange = (val: string) => {
    setQuery(val);
    setPlace(val);
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    if (!val.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const results = await searchPlaces(val, 6);
        setSuggestions(results);
        setShowSuggestions(results.length > 0);
      } catch {
        setSuggestions([]);
      }
    }, 200);
  };

  const handleSelectPlace = (p: PlaceResult) => {
    setPlace(p.name);
    setQuery(p.name);
    setLat(String(p.latitude));
    setLon(String(p.longitude));
    setTz(p.timezone);
    setShowSuggestions(false);
  };

  const handlePreset = (p: typeof PRESETS[0]) => {
    setLat(String(p.lat));
    setLon(String(p.lon));
    setTz(p.tz);
    setPlace(p.name);
    setQuery(p.name);
    setShowSuggestions(false);
  };

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    let currentY = year;
    let currentM = month;
    let currentD = day;

    if (calendarSystem === "bikram") {
      const by = parseInt(bsYear, 10);
      const bm = parseInt(bsMonth, 10);
      const bd = parseInt(bsDay, 10);
      if (!isNaN(by) && !isNaN(bm) && !isNaN(bd) && by >= 1970 && by <= 2100 && bm >= 1 && bm <= 12 && bd >= 1 && bd <= 32) {
        const ad = await convertBsToAd(by, bm, bd);
        if (ad) {
          currentY = String(ad.year);
          currentM = String(ad.month);
          currentD = String(ad.day);
          setYear(currentY);
          setMonth(currentM);
          setDay(currentD);
        }
      }
    }

    const y = parseInt(currentY, 10) || 1997;
    const m = Math.min(12, Math.max(1, parseInt(currentM, 10) || 1));
    const d = Math.min(31, Math.max(1, parseInt(currentD, 10) || 1));
    const h = Math.min(23, Math.max(0, parseInt(hour, 10) || 0));
    const min = Math.min(59, Math.max(0, parseInt(minute, 10) || 0));
    const s = Math.min(59, Math.max(0, parseInt(second, 10) || 0));
    const latitude = parseFloat(lat) || 0;
    const longitude = parseFloat(lon) || 0;

    onSubmit({
      year: y,
      month: m,
      day: d,
      hour: h,
      minute: min,
      second: s,
      latitude,
      longitude,
      timezone: tz,
      place_name: place,
      ayanamsa,
      house_system: houseSystem,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="card" style={{ padding: "var(--space-6)", position: "relative" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)", flexWrap: "wrap", gap: "var(--space-3)" }}>
        <h3 style={{ fontSize: "var(--type-heading)", fontWeight: 700, display: "flex", alignItems: "center", gap: "var(--space-2)", color: "var(--text-high)" }}>
          <Sparkles size={16} color="var(--gold-vivid)" aria-hidden="true" />
          Birth Coordinates & Epoch
        </h3>

        {/* Preset quick buttons */}
        <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
          {PRESETS.map((p) => (
            <button
              key={p.name}
              type="button"
              onClick={() => handlePreset(p)}
              className={`chip${place === p.name ? " active" : ""}`}
              aria-label={`Preset location ${p.name.split(",")[0]}`}
            >
              {p.name.split(",")[0]}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "var(--space-4)" }}>
        {/* Date */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "var(--space-1)" }}>
            <label style={{ fontSize: "var(--type-label)", color: "var(--text-mid)", display: "flex", alignItems: "center", gap: "var(--space-1)", margin: 0 }}>
              <Calendar size={13} aria-hidden="true" />
              {calendarSystem === "bikram" ? "Date of Birth (BS - Bikram Sambat)" : "Date of Birth (AD - Gregorian)"}
            </label>
            <div style={{ display: "flex", gap: "2px", background: "var(--surface-sunken)", padding: "2px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <button
                type="button"
                onClick={() => {
                  setCalendarSystemState("gregorian");
                  setCalendarSystem("gregorian");
                  window.dispatchEvent(new CustomEvent("calendarSystemChanged", { detail: "gregorian" }));
                }}
                className={`chip${calendarSystem === "gregorian" ? " active" : ""}`}
                style={{ fontSize: "11px", padding: "1px 6px", height: "auto", lineHeight: "16px" }}
              >
                AD
              </button>
              <button
                type="button"
                onClick={() => {
                  setCalendarSystemState("bikram");
                  setCalendarSystem("bikram");
                  window.dispatchEvent(new CustomEvent("calendarSystemChanged", { detail: "bikram" }));
                }}
                className={`chip${calendarSystem === "bikram" ? " active" : ""}`}
                style={{ fontSize: "11px", padding: "1px 6px", height: "auto", lineHeight: "16px" }}
              >
                BS (वि.सं.)
              </button>
            </div>
          </div>

          {calendarSystem === "gregorian" ? (
            <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr", gap: "var(--space-1)" }}>
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={year}
                onChange={(e) => handleYearChange(e.target.value)}
                onBlur={handleYearBlur}
                placeholder="YYYY"
                aria-label="Birth year"
                required
              />
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={month}
                onChange={(e) => handleMonthChange(e.target.value)}
                onBlur={handleMonthBlur}
                placeholder="MM"
                aria-label="Birth month"
                required
              />
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={day}
                onChange={(e) => handleDayChange(e.target.value)}
                onBlur={handleDayBlur}
                placeholder="DD"
                aria-label="Birth day"
                required
              />
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 2fr 1fr", gap: "var(--space-1)" }}>
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={bsYear}
                onChange={(e) => handleBsYearChange(e.target.value)}
                onBlur={handleBsYearBlur}
                placeholder="वर्ष (YYYY)"
                aria-label="Bikram Sambat birth year"
                required
              />
              <select
                value={bsMonth}
                onChange={(e) => handleBsMonthChange(e.target.value)}
                style={{ padding: "var(--space-2)", background: "var(--surface-raised)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)", color: "var(--text-high)", fontSize: "var(--type-body)" }}
                aria-label="Bikram Sambat birth month"
              >
                {NEPALI_MONTHS.map((m) => (
                  <option key={m.index} value={String(m.index)}>
                    {m.index < 10 ? `0${m.index}` : m.index} - {m.name_ne} ({m.name_en})
                  </option>
                ))}
              </select>
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={bsDay}
                onChange={(e) => handleBsDayChange(e.target.value)}
                onBlur={handleBsDayBlur}
                placeholder="गते (DD)"
                aria-label="Bikram Sambat birth gate/day"
                required
              />
            </div>
          )}

          {/* Dual Calendar Conversion Indicator Badge */}
          <div style={{ marginTop: "var(--space-1)", fontSize: "var(--type-micro)", color: "var(--text-mid)", display: "flex", alignItems: "center", gap: "var(--space-1)" }}>
            {calendarSystem === "bikram" ? (
              <span>
                Equivalent AD: <strong style={{ color: "var(--gold-bright)" }}>{year}-{String(month).padStart(2, "0")}-{String(day).padStart(2, "0")}</strong>
              </span>
            ) : (
              bsDateInfo && (
                <span>
                  Equivalent BS: <strong style={{ color: "var(--gold-bright)" }}>{bsDateInfo.formatted_ne || bsDateInfo.formatted}</strong>
                </span>
              )
            )}
          </div>
        </div>

        {/* Time */}
        <div>
          <label style={{ fontSize: "var(--type-label)", color: "var(--text-mid)", display: "flex", alignItems: "center", gap: "var(--space-1)", marginBottom: "var(--space-1)" }}>
            <Clock size={13} aria-hidden="true" /> Time (24h: HH:MM:SS)
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "var(--space-1)" }}>
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={hour}
              onChange={(e) => handleHourChange(e.target.value)}
              onBlur={handleHourBlur}
              placeholder="HH"
              aria-label="Birth hour"
              required
            />
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={minute}
              onChange={(e) => handleMinuteChange(e.target.value)}
              onBlur={handleMinuteBlur}
              placeholder="MM"
              aria-label="Birth minute"
              required
            />
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={second}
              onChange={(e) => handleSecondChange(e.target.value)}
              onBlur={handleSecondBlur}
              placeholder="SS"
              aria-label="Birth second"
            />
          </div>
        </div>

        {/* Place Search Autocomplete */}
        <div ref={dropdownRef} style={{ position: "relative" }}>
          <label style={{ fontSize: "var(--type-label)", color: "var(--text-mid)", display: "flex", alignItems: "center", gap: "var(--space-1)", marginBottom: "var(--space-1)" }}>
            <MapPin size={13} aria-hidden="true" /> Place of Birth (Auto-Geocoded)
          </label>
          <div style={{ position: "relative" }}>
            <input
              type="text"
              value={query}
              onChange={(e) => handlePlaceChange(e.target.value)}
              onFocus={() => {
                if (suggestions.length > 0) setShowSuggestions(true);
              }}
              placeholder="Type city (e.g. Yangon, Kathmandu, London)..."
              aria-label="Place of birth search"
              style={{ width: "100%", paddingRight: "32px" }}
            />
            <Globe size={14} color="var(--gold-vivid)" style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none", opacity: 0.8 }} aria-hidden="true" />
          </div>

          {/* Autocomplete Suggestions Menu */}
          {showSuggestions && suggestions.length > 0 && (
            <div
              className="card"
              style={{
                position: "absolute",
                top: "100%",
                left: 0,
                right: 0,
                marginTop: "4px",
                zIndex: 50,
                maxHeight: "240px",
                overflowY: "auto",
                background: "var(--bg-elevated, var(--bg-card))",
                border: "1px solid var(--gold-border)",
                boxShadow: "var(--card-shadow-hover)",
                padding: "var(--space-1)",
              }}
            >
              {suggestions.map((p, idx) => (
                <div
                  key={`${p.name}-${idx}`}
                  onClick={() => handleSelectPlace(p)}
                  style={{
                    padding: "var(--space-2) var(--space-3)",
                    cursor: "pointer",
                    borderRadius: "var(--radius-sm)",
                    fontSize: "var(--type-body)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    transition: "background 0.15s ease",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "var(--gold-dim)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <div>
                    <div style={{ fontWeight: 600, color: "var(--text-high)" }}>
                      {p.city}, <span style={{ color: "var(--text-mid)" }}>{p.country}</span>
                    </div>
                    <div style={{ fontSize: "var(--type-micro)", color: "var(--gold-vivid)", display: "flex", gap: "var(--space-2)", marginTop: "2px" }}>
                      <span>{p.latitude >= 0 ? `${p.latitude.toFixed(2)}°N` : `${Math.abs(p.latitude).toFixed(2)}°S`}, {p.longitude >= 0 ? `${p.longitude.toFixed(2)}°E` : `${Math.abs(p.longitude).toFixed(2)}°W`}</span>
                      <span>•</span>
                      <span>{p.timezone}</span>
                    </div>
                  </div>
                  {place === p.name && <Check size={14} color="var(--gold-vivid)" />}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Resolved Location & Timezone Summary Bar */}
      <div
        style={{
          marginTop: "var(--space-3)",
          padding: "var(--space-2-5) var(--space-3)",
          background: "var(--bg-subtle)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-md)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "var(--space-2)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Compass size={14} color="var(--gold-vivid)" aria-hidden="true" />
            <span style={{ fontSize: "0.86rem", fontWeight: 600, color: "var(--text-high)" }}>
              {place || "Custom Location"}
            </span>
          </div>
          <span style={{ color: "var(--border-subtle)" }}>•</span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.82rem", color: "var(--text-mid)" }}>
            {(() => {
              const numLat = parseFloat(lat) || 0;
              const numLon = parseFloat(lon) || 0;
              return `${numLat >= 0 ? `${numLat.toFixed(4)}°N` : `${Math.abs(numLat).toFixed(4)}°S`}, ${numLon >= 0 ? `${numLon.toFixed(4)}°E` : `${Math.abs(numLon).toFixed(4)}°W`}`;
            })()}
          </span>
          <span style={{ color: "var(--border-subtle)" }}>•</span>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.82rem", color: "var(--gold-bright)", fontWeight: 600 }}>
            {tz}
          </span>
          {tzInfo && (
            <span className={`badge ${tzInfo.is_dst ? "badge-amber" : "badge-cyan"}`} style={{ fontSize: "0.74rem" }}>
              UTC {tzInfo.utc_offset_str} • {tzInfo.tz_abbreviation} {tzInfo.is_dst ? "(DST)" : ""}
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={() => setShowManualCoords(!showManualCoords)}
          className="btn-ghost"
          style={{
            fontSize: "0.78rem",
            padding: "4px 8px",
            color: "var(--gold-vivid)",
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            cursor: "pointer",
          }}
          aria-expanded={showManualCoords}
        >
          <Sliders size={12} aria-hidden="true" />
          {showManualCoords ? "Hide Coordinates & Timezone" : "Edit Coordinates / Timezone"}
        </button>
      </div>

      {/* Manual Coordinates & Timezone Drawer */}
      {showManualCoords && (
        <div
          style={{
            marginTop: "var(--space-2)",
            padding: "var(--space-3) var(--space-4)",
            background: "var(--bg-card)",
            border: "1px dashed var(--gold-border)",
            borderRadius: "var(--radius-md)",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
            gap: "var(--space-3)",
            alignItems: "flex-end",
          }}
        >
          <div>
            <label style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", display: "block", marginBottom: "4px", fontWeight: 600 }}>
              Latitude (Decimal °)
            </label>
            <input
              type="text"
              inputMode="decimal"
              value={lat}
              onChange={(e) => handleLatChange(e.target.value)}
              onBlur={handleLatBlur}
              placeholder="e.g. 16.8661"
              required
              style={{ width: "100%" }}
            />
          </div>

          <div>
            <label style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", display: "block", marginBottom: "4px", fontWeight: 600 }}>
              Longitude (Decimal °)
            </label>
            <input
              type="text"
              inputMode="decimal"
              value={lon}
              onChange={(e) => handleLonChange(e.target.value)}
              onBlur={handleLonBlur}
              placeholder="e.g. 96.1951"
              required
              style={{ width: "100%" }}
            />
          </div>

          <div>
            <label style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", display: "block", marginBottom: "4px", fontWeight: 600 }}>
              Timezone (Standard Preset)
            </label>
            <select
              value={COMMON_TIMEZONES.some(t => t.value === tz) ? tz : "custom"}
              onChange={(e) => {
                if (e.target.value !== "custom") {
                  setTz(e.target.value);
                }
              }}
              style={{ width: "100%" }}
            >
              {COMMON_TIMEZONES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
              {!COMMON_TIMEZONES.some(t => t.value === tz) && (
                <option value="custom">Custom: {tz}</option>
              )}
            </select>
          </div>

          <div>
            <label style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", display: "block", marginBottom: "4px", fontWeight: 600 }}>
              Custom IANA Timezone String
            </label>
            <input
              type="text"
              value={tz}
              onChange={(e) => setTz(e.target.value)}
              placeholder="e.g. Asia/Yangon"
              required
              style={{ width: "100%", fontFamily: "var(--font-mono)" }}
            />
          </div>
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "var(--space-4)", paddingTop: "var(--space-4)", borderTop: "1px solid var(--border-subtle)", flexWrap: "wrap", gap: "var(--space-3)" }}>
        <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "center", flexWrap: "wrap" }}>
          <Settings size={15} color="var(--text-mid)" aria-hidden="true" />
          <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap", width: "100%", maxWidth: "100%", minWidth: 0 }}>
            <select
              value={ayanamsa}
              onChange={(e) => setAyanamsa(e.target.value)}
              style={{ width: "auto", maxWidth: "100%", minWidth: 0, flex: "1 1 180px" }}
              aria-label="Ayanamsa calculation system"
            >
              <option value="jhora_lahiri">JHora Lahiri (Calibrated)</option>
              <option value="lahiri">True Lahiri (Chitrapaksha)</option>
              <option value="raman">B.V. Raman</option>
              <option value="krishnamurti">KP (Krishnamurti)</option>
              <option value="tropical">Sayana (Tropical)</option>
            </select>
            <select
              value={houseSystem}
              onChange={(e) => setHouseSystem(e.target.value)}
              style={{ width: "auto", maxWidth: "100%", minWidth: 0, flex: "1 1 180px" }}
              aria-label="House division system"
            >
              <option value="WholeSign">Whole Sign (Vedic Default)</option>
              <option value="Placidus">Placidus</option>
              <option value="Equal">Equal House</option>
            </select>
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn-primary" aria-label="Calculate birth chart">
          <Sparkles size={16} aria-hidden="true" />
          {loading ? "Calculating Ephemeris..." : "Calculate Kundali"}
        </button>
      </div>
    </form>
  );
};
