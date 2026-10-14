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
    <form onSubmit={handleSubmit} className="glass-panel" style={{ padding: "24px", position: "relative" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px", flexWrap: "wrap", gap: "10px" }}>
        <h3 className="title-serif gold-gradient-text" style={{ fontSize: "1.15rem", display: "flex", alignItems: "center", gap: "8px" }}>
          <Sparkles size={18} color="#e5b94c" />
          Birth Coordinates & Epoch
        </h3>

        {/* Preset quick buttons */}
        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
          {PRESETS.map((p) => (
            <button
              key={p.name}
              type="button"
              onClick={() => handlePreset(p)}
              className="badge badge-gold"
              style={{ cursor: "pointer", background: place === p.name ? "rgba(229,185,76,0.3)" : "rgba(255,255,255,0.05)" }}
            >
              {p.name.split(",")[0]}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
        {/* Date */}
        <div>
          <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "5px", marginBottom: "6px" }}>
            <Calendar size={13} /> Date of Birth (YYYY-MM-DD)
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr", gap: "6px" }}>
            <input type="number" min={1900} max={2100} value={year} onChange={(e) => setYear(Number(e.target.value))} placeholder="YYYY" required />
            <input type="number" min={1} max={12} value={month} onChange={(e) => setMonth(Number(e.target.value))} placeholder="MM" required />
            <input type="number" min={1} max={31} value={day} onChange={(e) => setDay(Number(e.target.value))} placeholder="DD" required />
          </div>
        </div>

        {/* Time */}
        <div>
          <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "5px", marginBottom: "6px" }}>
            <Clock size={13} /> Time (24h: HH:MM:SS)
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "6px" }}>
            <input type="number" min={0} max={23} value={hour} onChange={(e) => setHour(Number(e.target.value))} placeholder="HH" required />
            <input type="number" min={0} max={59} value={minute} onChange={(e) => setMinute(Number(e.target.value))} placeholder="MM" required />
            <input type="number" min={0} max={59} value={second} onChange={(e) => setSecond(Number(e.target.value))} placeholder="SS" />
          </div>
        </div>

        {/* Place Search Autocomplete */}
        <div ref={dropdownRef} style={{ position: "relative" }}>
          <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "5px", marginBottom: "6px" }}>
            <MapPin size={13} /> Place of Birth (Auto-Geocoded)
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
              style={{ width: "100%", paddingRight: "30px" }}
            />
            <Globe size={14} color="#e5b94c" style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", pointerEvents: "none", opacity: 0.7 }} />
          </div>

          {/* Autocomplete Suggestions Menu */}
          {showSuggestions && suggestions.length > 0 && (
            <div
              className="glass-panel"
              style={{
                position: "absolute",
                top: "100%",
                left: 0,
                right: 0,
                marginTop: "4px",
                zIndex: 50,
                maxHeight: "220px",
                overflowY: "auto",
                background: "rgba(20, 24, 38, 0.98)",
                border: "1px solid rgba(229, 185, 76, 0.3)",
                borderRadius: "8px",
                boxShadow: "0 12px 28px rgba(0,0,0,0.6)",
              }}
            >
              {suggestions.map((p, idx) => (
                <div
                  key={`${p.name}-${idx}`}
                  onClick={() => handleSelectPlace(p)}
                  style={{
                    padding: "10px 14px",
                    cursor: "pointer",
                    borderBottom: "1px solid rgba(255,255,255,0.05)",
                    fontSize: "0.85rem",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    transition: "background 0.15s ease",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(229,185,76,0.15)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <div>
                    <div style={{ fontWeight: 500, color: "#fff" }}>{p.city}, <span style={{ color: "var(--text-muted)" }}>{p.country}</span></div>
                    <div style={{ fontSize: "0.72rem", color: "#e5b94c" }}>
                      {p.latitude.toFixed(2)}°, {p.longitude.toFixed(2)}° • {p.timezone}
                    </div>
                  </div>
                  {place === p.name && <Check size={14} color="#e5b94c" />}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Lat / Long & Resolved Timezone */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
            <label style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Coordinates & Civil Epoch
            </label>
            {tzInfo && (
              <span style={{ fontSize: "0.72rem", color: tzInfo.is_dst ? "#ff9800" : "#7ec8e3", background: "rgba(255,255,255,0.06)", padding: "2px 6px", borderRadius: "4px" }}>
                UTC {tzInfo.utc_offset_str} • {tzInfo.tz_abbreviation} {tzInfo.is_dst ? "(DST)" : ""}
              </span>
            )}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1.2fr", gap: "6px" }}>
            <input type="number" step="any" value={lat} onChange={(e) => setLat(Number(e.target.value))} placeholder="Lat" required />
            <input type="number" step="any" value={lon} onChange={(e) => setLon(Number(e.target.value))} placeholder="Lon" required />
            <input type="text" value={tz} onChange={(e) => setTz(e.target.value)} placeholder="IANA Timezone" required />
          </div>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "18px", paddingTop: "14px", borderTop: "1px solid rgba(255,255,255,0.08)", flexWrap: "wrap", gap: "10px" }}>
        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <Settings size={15} color="var(--text-muted)" />
          <div style={{ display: "flex", gap: "8px" }}>
            <select value={ayanamsa} onChange={(e) => setAyanamsa(e.target.value)} style={{ width: "auto" }}>
              <option value="jhora_lahiri">JHora Lahiri (Calibrated)</option>
              <option value="lahiri">True Lahiri (Chitrapaksha)</option>
              <option value="raman">B.V. Raman</option>
              <option value="krishnamurti">KP (Krishnamurti)</option>
              <option value="tropical">Sayana (Tropical)</option>
            </select>
            <select value={houseSystem} onChange={(e) => setHouseSystem(e.target.value)} style={{ width: "auto" }}>
              <option value="WholeSign">Whole Sign (Vedic Default)</option>
              <option value="Placidus">Placidus</option>
              <option value="Equal">Equal House</option>
            </select>
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn-primary">
          <Sparkles size={16} />
          {loading ? "Calculating Ephemeris..." : "Calculate Kundali"}
        </button>
      </div>
    </form>
  );
};
