"use client";

import React, { useState, useEffect, useRef } from "react";
import { BirthDataInput, PlaceResult, TimezoneOffsetInfo } from "@/lib/types";
import { searchPlaces, fetchTimezoneOffset } from "@/lib/api";
import { MapPin, Calendar, Clock, Settings, Sparkles, Check, Globe, Compass, Sliders } from "lucide-react";

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
  const [year, setYear] = useState(initialData?.year || 1997);
  const [month, setMonth] = useState(initialData?.month || 5);
  const [day, setDay] = useState(initialData?.day || 22);
  const [hour, setHour] = useState(initialData?.hour || 4);
  const [minute, setMinute] = useState(initialData?.minute || 53);
  const [second, setSecond] = useState(initialData?.second || 0);

  const [lat, setLat] = useState(initialData?.latitude || 27.8667);
  const [lon, setLon] = useState(initialData?.longitude || 83.4833);
  const [tz, setTz] = useState(initialData?.timezone || "Asia/Kathmandu");
  const [place, setPlace] = useState(initialData?.place_name || "Palpa, Nepal");

  const [ayanamsa, setAyanamsa] = useState(initialData?.ayanamsa || "jhora_lahiri");
  const [houseSystem, setHouseSystem] = useState(initialData?.house_system || "WholeSign");

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
    setYear(initialData.year);
    setMonth(initialData.month);
    setDay(initialData.day);
    setHour(initialData.hour);
    setMinute(initialData.minute);
    setSecond(initialData.second ?? 0);
    setLat(initialData.latitude);
    setLon(initialData.longitude);
    setTz(initialData.timezone);
    setPlace(initialData.place_name || "");
    setQuery(initialData.place_name || "");
    if (initialData.ayanamsa) setAyanamsa(initialData.ayanamsa);
    if (initialData.house_system) setHouseSystem(initialData.house_system);
  }, [initialData]);

  // Auto-resolve timezone offset whenever date or timezone changes
  useEffect(() => {
    let active = true;
    fetchTimezoneOffset(tz, year, month, day, hour, minute)
      .then((info) => {
        if (active && info) setTzInfo(info);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [tz, year, month, day, hour, minute]);

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
    setLat(p.latitude);
    setLon(p.longitude);
    setTz(p.timezone);
    setShowSuggestions(false);
  };

  const handlePreset = (p: typeof PRESETS[0]) => {
    setLat(p.lat);
    setLon(p.lon);
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      year,
      month,
      day,
      hour,
      minute,
      second,
      latitude: lat,
      longitude: lon,
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
          <label style={{ fontSize: "var(--type-label)", color: "var(--text-mid)", display: "flex", alignItems: "center", gap: "var(--space-1)", marginBottom: "var(--space-1)" }}>
            <Calendar size={13} aria-hidden="true" /> Date of Birth (YYYY-MM-DD)
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr", gap: "var(--space-1)" }}>
            <input
              type="number"
              min={1900}
              max={2100}
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              placeholder="YYYY"
              aria-label="Birth year"
              required
            />
            <input
              type="number"
              min={1}
              max={12}
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
              placeholder="MM"
              aria-label="Birth month"
              required
            />
            <input
              type="number"
              min={1}
              max={31}
              value={day}
              onChange={(e) => setDay(Number(e.target.value))}
              placeholder="DD"
              aria-label="Birth day"
              required
            />
          </div>
        </div>

        {/* Time */}
        <div>
          <label style={{ fontSize: "var(--type-label)", color: "var(--text-mid)", display: "flex", alignItems: "center", gap: "var(--space-1)", marginBottom: "var(--space-1)" }}>
            <Clock size={13} aria-hidden="true" /> Time (24h: HH:MM:SS)
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "var(--space-1)" }}>
            <input
              type="number"
              min={0}
              max={23}
              value={hour}
              onChange={(e) => setHour(Number(e.target.value))}
              placeholder="HH"
              aria-label="Birth hour"
              required
            />
            <input
              type="number"
              min={0}
              max={59}
              value={minute}
              onChange={(e) => setMinute(Number(e.target.value))}
              placeholder="MM"
              aria-label="Birth minute"
              required
            />
            <input
              type="number"
              min={0}
              max={59}
              value={second}
              onChange={(e) => setSecond(Number(e.target.value))}
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
            {lat >= 0 ? `${lat.toFixed(4)}°N` : `${Math.abs(lat).toFixed(4)}°S`},{" "}
            {lon >= 0 ? `${lon.toFixed(4)}°E` : `${Math.abs(lon).toFixed(4)}°W`}
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
              type="number"
              step="any"
              value={lat}
              onChange={(e) => setLat(Number(e.target.value))}
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
              type="number"
              step="any"
              value={lon}
              onChange={(e) => setLon(Number(e.target.value))}
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
          <div style={{ display: "flex", gap: "var(--space-2)" }}>
            <select
              value={ayanamsa}
              onChange={(e) => setAyanamsa(e.target.value)}
              style={{ width: "auto" }}
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
              style={{ width: "auto" }}
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
