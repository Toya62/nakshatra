"use client";

import React, { useState, useEffect } from "react";
import { PanchangaData } from "@/lib/types";
import { fetchPanchanga } from "@/lib/api";
import { Moon, Sun, AlertTriangle, Calendar, Clock } from "lucide-react";

interface Props {
  defaultLat?: number;
  defaultLon?: number;
  defaultTz?: string;
}

export const PanchangaView: React.FC<Props> = ({
  defaultLat = 27.8667,
  defaultLon = 83.4833,
  defaultTz = "Asia/Kathmandu",
}) => {
  const [date, setDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [time, setTime] = useState("12:00");
  const [lat] = useState(defaultLat);
  const [lon] = useState(defaultLon);
  const [tz] = useState(defaultTz);

  const [data, setData] = useState<PanchangaData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPanchanga = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchPanchanga(date, time, lat, lon, tz);
      setData(res);
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPanchanga();
  }, [date, time, lat, lon, tz]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Top Filter Bar */}
      <div className="glass-panel" style={{ padding: "18px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h3 className="title-serif gold-gradient-text" style={{ fontSize: "1.2rem", display: "flex", alignItems: "center", gap: "8px" }}>
            <Moon size={20} color="#e5b94c" />
            Vedic Panchanga (5 Limbs of Time)
          </h3>
          <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
            Exact solar day boundaries, sunrise markers, and solilunar phases
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Calendar size={14} color="var(--text-muted)" />
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} style={{ width: "auto" }} />
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Clock size={14} color="var(--text-muted)" />
            <input type="time" value={time} onChange={(e) => setTime(e.target.value)} style={{ width: "auto" }} />
          </div>
        </div>
      </div>

      {loading && (
        <div className="glass-panel" style={{ padding: "40px", textAlign: "center", color: "var(--accent-gold)" }}>
          Calculating Panchanga Limbs...
        </div>
      )}

      {error && (
        <div className="glass-panel" style={{ padding: "20px", color: "var(--accent-rose)", borderColor: "var(--accent-rose)" }}>
          Error: {error}
        </div>
      )}

      {data && !loading && (
        <>
          {/* Solar Markers Banner */}
          <div
            className="glass-panel"
            style={{
              padding: "16px 24px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "12px",
              background: "linear-gradient(135deg, rgba(229,185,76,0.08) 0%, rgba(56,189,248,0.06) 100%)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "18px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Sun size={18} color="#f59e0b" />
                <span style={{ fontSize: "0.85rem" }}>
                  Sunrise: <strong style={{ color: "#fbe285" }}>{data.sunrise_time || "N/A"}</strong>
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Moon size={18} color="#38bdf8" />
                <span style={{ fontSize: "0.85rem" }}>
                  Sunset: <strong style={{ color: "#7dd3fc" }}>{data.sunset_time || "N/A"}</strong>
                </span>
              </div>
            </div>

            <div style={{ display: "flex", gap: "12px", fontSize: "0.8rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
              <span>Sun: {data.sun_longitude.toFixed(2)}°</span>
              <span>Moon: {data.moon_longitude.toFixed(2)}°</span>
            </div>
          </div>

          {/* 5 Limbs Cards Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: "16px" }}>
            {/* 1. VARA */}
            <div className="glass-panel" style={{ padding: "20px" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", letterSpacing: "0.06em" }}>1. VARA (DAY)</span>
              <h4 style={{ fontSize: "1.3rem", fontWeight: 700, color: "#fbe285", margin: "8px 0 4px" }}>
                {data.vara.name}
              </h4>
              <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                Lord: <strong style={{ color: "var(--text-main)" }}>{data.vara.lord}</strong>
              </p>
              {data.vara.is_pre_sunrise && (
                <span className="badge badge-rose" style={{ marginTop: "10px" }}>
                  Pre-Sunrise (Previous Vara)
                </span>
              )}
            </div>

            {/* 2. TITHI */}
            <div className="glass-panel" style={{ padding: "20px" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", letterSpacing: "0.06em" }}>2. TITHI (LUNAR DAY)</span>
              <h4 style={{ fontSize: "1.15rem", fontWeight: 700, color: "#7dd3fc", margin: "8px 0 4px" }}>
                {data.tithi.name}
              </h4>
              <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                {data.tithi.paksha} Paksha | Lord: <strong style={{ color: "var(--text-main)" }}>{data.tithi.lord}</strong>
              </p>
              {data.tithi.percentage_left !== undefined && (
                <div style={{ marginTop: "10px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-dim)", marginBottom: "4px" }}>
                    <span>Remaining</span>
                    <span>{data.tithi.percentage_left.toFixed(1)}%</span>
                  </div>
                  <div style={{ height: "4px", background: "rgba(255,255,255,0.1)", borderRadius: "2px" }}>
                    <div style={{ width: `${data.tithi.percentage_left}%`, height: "100%", background: "#38bdf8" }} />
                  </div>
                </div>
              )}
            </div>

            {/* 3. NAKSHATRA */}
            <div className="glass-panel" style={{ padding: "20px" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", letterSpacing: "0.06em" }}>3. NAKSHATRA (STAR)</span>
              <h4 style={{ fontSize: "1.15rem", fontWeight: 700, color: "#fbe285", margin: "8px 0 4px" }}>
                {data.nakshatra.name}
              </h4>
              <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                Pada {data.nakshatra.pada} | Lord: <strong style={{ color: "var(--text-main)" }}>{data.nakshatra.lord}</strong>
              </p>
              {data.nakshatra.percentage_left !== undefined && (
                <div style={{ marginTop: "10px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-dim)", marginBottom: "4px" }}>
                    <span>Remaining</span>
                    <span>{data.nakshatra.percentage_left.toFixed(1)}%</span>
                  </div>
                  <div style={{ height: "4px", background: "rgba(255,255,255,0.1)", borderRadius: "2px" }}>
                    <div style={{ width: `${data.nakshatra.percentage_left}%`, height: "100%", background: "#e5b94c" }} />
                  </div>
                </div>
              )}
            </div>

            {/* 4. YOGA */}
            <div className="glass-panel" style={{ padding: "20px" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", letterSpacing: "0.06em" }}>4. YOGA (ANGULAR)</span>
              <h4 style={{ fontSize: "1.15rem", fontWeight: 700, color: "#c084fc", margin: "8px 0 4px" }}>
                {data.yoga.name}
              </h4>
              <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                Lord: <strong style={{ color: "var(--text-main)" }}>{data.yoga.lord}</strong>
              </p>
              {data.yoga.percentage_left !== undefined && (
                <div style={{ marginTop: "10px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-dim)", marginBottom: "4px" }}>
                    <span>Remaining</span>
                    <span>{data.yoga.percentage_left.toFixed(1)}%</span>
                  </div>
                  <div style={{ height: "4px", background: "rgba(255,255,255,0.1)", borderRadius: "2px" }}>
                    <div style={{ width: `${data.yoga.percentage_left}%`, height: "100%", background: "#a855f7" }} />
                  </div>
                </div>
              )}
            </div>

            {/* 5. KARANA */}
            <div className="glass-panel" style={{ padding: "20px" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", letterSpacing: "0.06em" }}>5. KARANA (HALF-TITHI)</span>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", margin: "8px 0 4px" }}>
                <h4 style={{ fontSize: "1.15rem", fontWeight: 700, color: data.karana.is_vishti_bhadra ? "#f43f5e" : "#6ee7b7" }}>
                  {data.karana.name}
                </h4>
                {data.karana.is_vishti_bhadra && (
                  <span className="badge badge-rose" style={{ gap: "3px" }}>
                    <AlertTriangle size={11} /> BHADRA
                  </span>
                )}
              </div>
              <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                Lord: <strong style={{ color: "var(--text-main)" }}>{data.karana.lord}</strong>
              </p>
              {data.karana.percentage_left !== undefined && (
                <div style={{ marginTop: "10px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-dim)", marginBottom: "4px" }}>
                    <span>Remaining</span>
                    <span>{data.karana.percentage_left.toFixed(1)}%</span>
                  </div>
                  <div style={{ height: "4px", background: "rgba(255,255,255,0.1)", borderRadius: "2px" }}>
                    <div style={{ width: `${data.karana.percentage_left}%`, height: "100%", background: "#10b981" }} />
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
