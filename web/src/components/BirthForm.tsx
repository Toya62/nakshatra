"use client";

import React, { useState } from "react";
import { BirthDataInput } from "@/lib/types";
import { MapPin, Calendar, Clock, Settings, Sparkles } from "lucide-react";

interface Props {
  initialData?: BirthDataInput;
  onSubmit: (data: BirthDataInput) => void;
  loading?: boolean;
}

const PRESETS = [
  { name: "Kathmandu, Nepal", lat: 27.8667, lon: 83.4833, tz: "Asia/Kathmandu" },
  { name: "New Delhi, India", lat: 28.6139, lon: 77.2090, tz: "Asia/Kolkata" },
  { name: "Varanasi, India", lat: 25.3176, lon: 82.9739, tz: "Asia/Kolkata" },
  { name: "London, UK", lat: 51.5074, lon: -0.1278, tz: "Europe/London" },
  { name: "New York, USA", lat: 40.7128, lon: -74.0060, tz: "America/New_York" },
  { name: "Tokyo, Japan", lat: 35.6762, lon: 139.6503, tz: "Asia/Tokyo" },
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

  const handlePreset = (p: typeof PRESETS[0]) => {
    setLat(p.lat);
    setLon(p.lon);
    setTz(p.tz);
    setPlace(p.name);
  };

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
    <form onSubmit={handleSubmit} className="glass-panel" style={{ padding: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
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

        {/* Place & Timezone */}
        <div>
          <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "5px", marginBottom: "6px" }}>
            <MapPin size={13} /> Location & IANA Timezone
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: "6px" }}>
            <input type="text" value={place} onChange={(e) => setPlace(e.target.value)} placeholder="City / Country" />
            <input type="text" value={tz} onChange={(e) => setTz(e.target.value)} placeholder="e.g. Asia/Kathmandu" required />
          </div>
        </div>

        {/* Lat / Long */}
        <div>
          <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "5px", marginBottom: "6px" }}>
            Latitude & Longitude
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
            <input type="number" step="any" value={lat} onChange={(e) => setLat(Number(e.target.value))} placeholder="Lat (-90 to 90)" required />
            <input type="number" step="any" value={lon} onChange={(e) => setLon(Number(e.target.value))} placeholder="Lon (-180 to 180)" required />
          </div>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "18px", paddingTop: "14px", borderTop: "1px solid rgba(255,255,255,0.08)" }}>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
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
