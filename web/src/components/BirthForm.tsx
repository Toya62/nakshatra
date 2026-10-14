"use client";

import React, { useState, useEffect, useRef } from "react";
import { BirthDataInput, PlaceResult, TimezoneOffsetInfo } from "@/lib/types";
import { searchPlaces, fetchTimezoneOffset } from "@/lib/api";
import { MapPin, Calendar, Clock, Settings, Sparkles, Check, Globe } from "lucide-react";

interface Props {
  initialData?: BirthDataInput;
  onSubmit: (data: BirthDataInput) => void;
  loading?: boolean;
}

const PRESETS = [
  { name: "Palpa, Nepal", lat: 27.8667, lon: 83.4833, tz: "Asia/Kathmandu" },
  { name: "Kathmandu, Nepal", lat: 27.7172, lon: 85.3240, tz: "Asia/Kathmandu" },
  { name: "Varanasi, India", lat: 25.3176, lon: 82.9739, tz: "Asia/Kolkata" },
  { name: "New Delhi, India", lat: 28.6139, lon: 77.2090, tz: "Asia/Kolkata" },
  { name: "Berlin, Germany", lat: 52.5200, lon: 13.4050, tz: "Europe/Berlin" },
  { name: "London, UK", lat: 51.5074, lon: -0.1278, tz: "Europe/London" },
  { name: "New York, USA", lat: 40.7128, lon: -74.0060, tz: "America/New_York" },
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

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "var(--space-4)" }}>
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
              placeholder="Type city or spiritual center..."
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
                maxHeight: "220px",
                overflowY: "auto",
                background: "rgba(14, 18, 30, 0.98)",
                border: "1px solid var(--gold-border)",
                boxShadow: "0 12px 28px rgba(0,0,0,0.6)",
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
                    <div style={{ fontWeight: 500, color: "var(--text-high)" }}>
                      {p.city}, <span style={{ color: "var(--text-mid)" }}>{p.country}</span>
                    </div>
                    <div style={{ fontSize: "var(--type-micro)", color: "var(--gold-vivid)" }}>
                      {p.latitude.toFixed(2)}°, {p.longitude.toFixed(2)}° • {p.timezone}
                    </div>
                  </div>
                  {place === p.name && <Check size={14} color="var(--gold-vivid)" />}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Lat / Long & Resolved Timezone */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-1)" }}>
            <label style={{ fontSize: "var(--type-label)", color: "var(--text-mid)" }}>
              Coordinates & Epoch
            </label>
            {tzInfo && (
              <span className={`badge ${tzInfo.is_dst ? "badge-amber" : "badge-cyan"}`}>
                UTC {tzInfo.utc_offset_str} • {tzInfo.tz_abbreviation} {tzInfo.is_dst ? "(DST)" : ""}
              </span>
            )}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1.2fr", gap: "var(--space-1)" }}>
            <input
              type="number"
              step="any"
              value={lat}
              onChange={(e) => setLat(Number(e.target.value))}
              placeholder="Lat"
              aria-label="Latitude coordinate"
              required
            />
            <input
              type="number"
              step="any"
              value={lon}
              onChange={(e) => setLon(Number(e.target.value))}
              placeholder="Lon"
              aria-label="Longitude coordinate"
              required
            />
            <input
              type="text"
              value={tz}
              onChange={(e) => setTz(e.target.value)}
              placeholder="IANA Timezone"
              aria-label="IANA Timezone"
              required
            />
          </div>
        </div>
      </div>

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
