"use client";

import React, { useState, useEffect, useMemo } from "react";
import { BirthDataInput, ChartData, DashaPeriod, VimshottariData, BikramSambatDate, DevanagariNomenclature } from "@/lib/types";
import { fetchBikramSambat, fetchNomenclature } from "@/lib/api";
import { Clock, Calendar, Sparkles, AlertCircle, Compass, Shield, ChevronRight, Eye } from "lucide-react";

interface Props {
  birth: BirthDataInput;
  chart?: ChartData | null;
}

const GRAHA_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  Sun: { bg: "rgba(245, 158, 11, 0.25)", border: "#f59e0b", text: "#fbbf24" },
  Moon: { bg: "rgba(56, 189, 248, 0.25)", border: "#38bdf8", text: "#7dd3fc" },
  Mars: { bg: "rgba(239, 68, 68, 0.25)", border: "#ef4444", text: "#f87171" },
  Mercury: { bg: "rgba(16, 185, 129, 0.25)", border: "#10b981", text: "#34d399" },
  Jupiter: { bg: "rgba(229, 185, 76, 0.28)", border: "#e5b94c", text: "#fbe285" },
  Venus: { bg: "rgba(236, 72, 153, 0.25)", border: "#ec4899", text: "#f472b6" },
  Saturn: { bg: "rgba(99, 102, 241, 0.28)", border: "#6366f1", text: "#818cf8" },
  Rahu: { bg: "rgba(168, 85, 247, 0.25)", border: "#a855f7", text: "#c084fc" },
  Ketu: { bg: "rgba(148, 163, 184, 0.25)", border: "#94a3b8", text: "#cbd5e1" },
};

const ZODIAC_SIGNS = [
  "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
];

export const TimelineView: React.FC<Props> = ({ birth, chart }) => {
  const [useDevanagari, setUseDevanagari] = useState<boolean>(false);
  const [bsDate, setBsDate] = useState<BikramSambatDate | null>(null);
  const [nomenclature, setNomenclature] = useState<DevanagariNomenclature | null>(null);
  const [selectedMd, setSelectedMd] = useState<DashaPeriod | null>(null);
  const [selectedAd, setSelectedAd] = useState<DashaPeriod | null>(null);
  const [showSadeSati, setShowSadeSati] = useState<boolean>(true);

  // Load Bikram Sambat date and Devanagari dictionary
  useEffect(() => {
    fetchBikramSambat(birth.year, birth.month, birth.day).then(setBsDate);
    fetchNomenclature().then(setNomenclature);
  }, [birth.year, birth.month, birth.day]);

  const dashas = chart?.dashas;
  const mahadashas = dashas?.mahadashas || [];

  // Default selected Mahadasha to current active one or first
  useEffect(() => {
    if (dashas?.current_md) {
      setSelectedMd(dashas.current_md);
      if (dashas.current_ad) {
        setSelectedAd(dashas.current_ad);
      }
    } else if (mahadashas.length > 0) {
      setSelectedMd(mahadashas[0]);
    }
  }, [dashas]);

  // Seeker's birth timestamp & current age
  const birthEpochMs = useMemo(() => {
    return new Date(Date.UTC(birth.year, birth.month - 1, birth.day, birth.hour, birth.minute)).getTime();
  }, [birth]);

  const currentAgeYears = useMemo(() => {
    const now = Date.now();
    const diffYears = (now - birthEpochMs) / (365.25 * 86400 * 1000);
    return Math.max(0, diffYears);
  }, [birthEpochMs]);

  // Total timeline span (from first MD start to last MD end)
  const timelineBounds = useMemo(() => {
    if (mahadashas.length === 0) return { startMs: birthEpochMs, endMs: birthEpochMs + 120 * 365.25 * 86400 * 1000 };
    const firstStart = new Date(mahadashas[0].start.replace("Z", "")).getTime();
    const lastEnd = new Date(mahadashas[mahadashas.length - 1].end.replace("Z", "")).getTime();
    return { startMs: firstStart, endMs: lastEnd };
  }, [mahadashas, birthEpochMs]);

  const totalTimelineSpanMs = Math.max(1, timelineBounds.endMs - timelineBounds.startMs);

  // Approximate Sade Sati windows across seeker's 100 years
  // Natal Moon sign index (0 = Aries ... 11 = Pisces)
  const sadeSatiWindows = useMemo(() => {
    if (!chart) return [];
    const moon = chart.planets.find((p) => p.name === "Moon");
    if (!moon) return [];
    const moonSignIdx = ZODIAC_SIGNS.indexOf(moon.sign);
    if (moonSignIdx === -1) return [];

    // Saturn takes ~29.45 years per zodiac revolution (~2.45 years per sign)
    // Find approximate historical and future Sade Sati windows (Moon - 1, Moon, Moon + 1)
    // Anchor: Saturn entered Pisces (sign index 11) ~March 2025
    const anchorYear = 2025.2;
    const anchorSaturnSign = 11; // Pisces

    const windows: Array<{ startAge: number; endAge: number; phaseName: string; approxYear: number }> = [];

    // Check cycles within age 0 to 100
    for (let cycle = -2; cycle <= 4; cycle++) {
      // Saturn reaches moonSignIdx - 1 (12th from Moon)
      const signDiff = (moonSignIdx - 1 - anchorSaturnSign + 12) % 12;
      const startYear = anchorYear + (cycle * 29.45) + (signDiff * 2.45);
      const endYear = startYear + 7.5; // 3 signs * 2.5 years

      const startAge = startYear - birth.year;
      const endAge = endYear - birth.year;

      if (endAge > 0 && startAge < 100) {
        windows.push({
          startAge: Math.max(0, startAge),
          endAge: Math.min(105, endAge),
          phaseName: "Saturn Sade Sati (7.5-Yr Karmic Realignment)",
          approxYear: Math.round(startYear),
        });
      }
    }
    return windows;
  }, [chart, birth.year]);

  const translateGraha = (name: string): string => {
    if (!useDevanagari || !nomenclature?.planets) return name;
    return nomenclature.planets[name] || name;
  };

  const translateSign = (name: string): string => {
    if (!useDevanagari || !nomenclature?.signs) return name;
    return nomenclature.signs[name] || name;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "22px" }}>
      {/* Top Banner & Control Bar */}
      <div className="glass-panel" style={{ padding: "20px 24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
              <Clock size={22} color="#e5b94c" />
              <h2 className="title-serif gold-gradient-text" style={{ fontSize: "1.35rem", fontWeight: 700 }}>
                Unified 120-Year Dasha & Gochar Life Timeline
              </h2>
            </div>
            <p style={{ fontSize: "0.84rem", color: "var(--text-muted)" }}>
              Astronomical Vimshottari progression mapped onto Gregorian & Nepali Bikram Sambat (BS) epochs.
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
            {/* Bikram Sambat Badge */}
            {bsDate && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "6px 14px",
                  borderRadius: "20px",
                  background: "rgba(229, 185, 76, 0.12)",
                  border: "1px solid rgba(229, 185, 76, 0.4)",
                  fontSize: "0.82rem",
                  color: "#fbe285",
                  fontWeight: 600,
                }}
              >
                <Calendar size={14} color="#e5b94c" />
                <span>BS: {useDevanagari ? bsDate.formatted_ne : bsDate.formatted}</span>
              </div>
            )}

            {/* Devanagari Sanskrit Toggle */}
            <button
              onClick={() => setUseDevanagari((prev) => !prev)}
              className={`badge ${useDevanagari ? "badge-gold" : "badge-cyan"}`}
              style={{
                cursor: "pointer",
                padding: "7px 14px",
                fontSize: "0.82rem",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                background: useDevanagari ? "rgba(229,185,76,0.3)" : "rgba(255,255,255,0.05)",
                fontWeight: 600,
              }}
            >
              <Sparkles size={14} />
              {useDevanagari ? "संस्कृत (Devanagari)" : "English / IAST"}
            </button>

            {/* Sade Sati Toggle */}
            <button
              onClick={() => setShowSadeSati((prev) => !prev)}
              className={`badge ${showSadeSati ? "badge-rose" : "badge-cyan"}`}
              style={{
                cursor: "pointer",
                padding: "7px 14px",
                fontSize: "0.82rem",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                background: showSadeSati ? "rgba(244,63,94,0.2)" : "rgba(255,255,255,0.05)",
                fontWeight: 600,
              }}
            >
              <Compass size={14} />
              {showSadeSati ? "Sade Sati: Visible" : "Sade Sati: Hidden"}
            </button>
          </div>
        </div>

        {/* Current Seeker Age Status Ribbon */}
        <div
          style={{
            marginTop: "18px",
            padding: "12px 18px",
            borderRadius: "10px",
            background: "rgba(0, 0, 0, 0.35)",
            border: "1px solid rgba(255,255,255,0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span
              style={{
                display: "inline-block",
                width: "10px",
                height: "10px",
                borderRadius: "50%",
                background: "#10b981",
                boxShadow: "0 0 10px #10b981",
              }}
            />
            <span style={{ fontSize: "0.85rem", color: "var(--text-main)", fontWeight: 600 }}>
              Current Age: <strong style={{ color: "#fbe285" }}>{currentAgeYears.toFixed(2)} years</strong>
            </span>
          </div>

          {dashas?.current_md && (
            <div style={{ display: "flex", gap: "10px", fontSize: "0.82rem" }}>
              <span className="badge badge-gold">
                Mahadasha: {translateGraha(dashas.current_md.lord)}
              </span>
              {dashas.current_ad && (
                <span className="badge badge-cyan">
                  Antardasha: {translateGraha(dashas.current_ad.lord)}
                </span>
              )}
              {dashas.current_pd && (
                <span className="badge badge-emerald">
                  Pratyantar: {translateGraha(dashas.current_pd.lord)}
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 120-Year Interactive Horizontal Life Timeline */}
      <div className="glass-panel" style={{ padding: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 className="title-serif" style={{ fontSize: "1.1rem", color: "var(--text-main)", display: "flex", alignItems: "center", gap: "8px" }}>
            <Compass size={18} color="#e5b94c" />
            Vimshottari 120-Year Macro Timeline (Click any Mahadasha block to inspect)
          </h3>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Proportional Astronomical Duration
          </span>
        </div>

        {/* The Ribbon Bar */}
        <div
          style={{
            position: "relative",
            width: "100%",
            height: "76px",
            background: "rgba(0,0,0,0.45)",
            borderRadius: "12px",
            overflow: "hidden",
            border: "1px solid rgba(255,255,255,0.12)",
            display: "flex",
          }}
        >
          {mahadashas.map((md, idx) => {
            const startMs = new Date(md.start.replace("Z", "")).getTime();
            const endMs = new Date(md.end.replace("Z", "")).getTime();
            const widthPct = Math.max(1, ((endMs - startMs) / totalTimelineSpanMs) * 100);
            const style = GRAHA_COLORS[md.lord] || { bg: "rgba(255,255,255,0.1)", border: "#fff", text: "#fff" };
            const isSelected = selectedMd?.lord === md.lord && selectedMd?.start === md.start;

            return (
              <button
                key={`${md.lord}-${idx}`}
                onClick={() => {
                  setSelectedMd(md);
                  setSelectedAd(md.subs && md.subs.length > 0 ? md.subs[0] : null);
                }}
                title={`${md.lord} Mahadasha (${md.start.slice(0, 10)} to ${md.end.slice(0, 10)})`}
                style={{
                  width: `${widthPct}%`,
                  height: "100%",
                  background: isSelected ? style.border : style.bg,
                  borderRight: "1px solid rgba(0,0,0,0.5)",
                  borderTop: isSelected ? `4px solid #fff` : "none",
                  cursor: "pointer",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: "4px",
                  transition: "all 0.15s ease",
                  outline: "none",
                }}
              >
                <span
                  style={{
                    fontSize: "0.82rem",
                    fontWeight: 700,
                    color: isSelected ? "#07090e" : style.text,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {translateGraha(md.lord)}
                </span>
                <span
                  style={{
                    fontSize: "0.68rem",
                    color: isSelected ? "#07090e" : "var(--text-dim)",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {md.start.slice(0, 4)}
                </span>
              </button>
            );
          })}

          {/* Current Age "You Are Here" Marker */}
          {(() => {
            const nowMs = Date.now();
            if (nowMs >= timelineBounds.startMs && nowMs <= timelineBounds.endMs) {
              const leftPct = ((nowMs - timelineBounds.startMs) / totalTimelineSpanMs) * 100;
              return (
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    bottom: 0,
                    left: `${leftPct}%`,
                    width: "3px",
                    background: "#ffffff",
                    boxShadow: "0 0 12px #ffffff, 0 0 20px #e5b94c",
                    pointerEvents: "none",
                    zIndex: 10,
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      top: "-18px",
                      left: "-22px",
                      background: "#e5b94c",
                      color: "#07090e",
                      fontSize: "0.62rem",
                      fontWeight: 800,
                      padding: "1px 5px",
                      borderRadius: "4px",
                      whiteSpace: "nowrap",
                    }}
                  >
                    NOW
                  </div>
                </div>
              );
            }
            return null;
          })()}
        </div>

        {/* Sade Sati Historical & Future Windows Overlay */}
        {showSadeSati && sadeSatiWindows.length > 0 && (
          <div style={{ marginTop: "16px" }}>
            <div style={{ fontSize: "0.78rem", color: "#f87171", fontWeight: 700, marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
              <AlertCircle size={14} color="#f87171" />
              Transiting Saturn Sade Sati Windows (Age-calibrated 7.5-Year Cycles):
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
              {sadeSatiWindows.map((win, i) => (
                <div
                  key={i}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "8px",
                    background: "rgba(239, 68, 68, 0.12)",
                    border: "1px solid rgba(239, 68, 68, 0.35)",
                    fontSize: "0.76rem",
                    color: "#fca5a5",
                  }}
                >
                  <strong>Age {win.startAge.toFixed(1)} – {win.endAge.toFixed(1)}</strong> (~{win.approxYear} AD)
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Selected Mahadasha Deep Dive: Antardashas Grid */}
      {selectedMd && (
        <div className="glass-panel" style={{ padding: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px", flexWrap: "wrap", gap: "10px" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span
                  style={{
                    width: "12px",
                    height: "12px",
                    borderRadius: "50%",
                    background: GRAHA_COLORS[selectedMd.lord]?.border || "#e5b94c",
                  }}
                />
                <h3 className="title-serif" style={{ fontSize: "1.2rem", color: "#fbe285" }}>
                  {translateGraha(selectedMd.lord)} Mahadasha Breakdown
                </h3>
              </div>
              <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "2px" }}>
                Epoch: {selectedMd.start.slice(0, 10)} → {selectedMd.end.slice(0, 10)}
              </p>
            </div>

            <div className="badge badge-gold" style={{ fontSize: "0.8rem" }}>
              9 Sub-Antardasha Cycles (Bhuktis)
            </div>
          </div>

          {/* Antardashas Cards Grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "12px",
            }}
          >
            {(selectedMd.subs || []).map((ad, idx) => {
              const adStyle = GRAHA_COLORS[ad.lord] || { bg: "rgba(255,255,255,0.05)", border: "#fff", text: "#fff" };
              const isSelectedAd = selectedAd?.lord === ad.lord && selectedAd?.start === ad.start;
              const isCurrent =
                dashas?.current_md?.lord === selectedMd.lord &&
                dashas?.current_ad?.lord === ad.lord;

              return (
                <div
                  key={`${ad.lord}-${idx}`}
                  onClick={() => setSelectedAd(ad)}
                  style={{
                    background: isSelectedAd ? "rgba(229,185,76,0.18)" : "rgba(0,0,0,0.3)",
                    border: isCurrent
                      ? "1px solid #10b981"
                      : isSelectedAd
                      ? "1px solid #e5b94c"
                      : "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "10px",
                    padding: "14px",
                    cursor: "pointer",
                    position: "relative",
                    transition: "all 0.15s ease",
                  }}
                >
                  {isCurrent && (
                    <span
                      style={{
                        position: "absolute",
                        top: "8px",
                        right: "8px",
                        background: "#10b981",
                        color: "#07090e",
                        fontSize: "0.62rem",
                        fontWeight: 800,
                        padding: "2px 6px",
                        borderRadius: "10px",
                      }}
                    >
                      ACTIVE
                    </span>
                  )}

                  <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                    <span
                      style={{
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        background: adStyle.border,
                      }}
                    />
                    <strong style={{ fontSize: "0.95rem", color: adStyle.text }}>
                      {translateGraha(ad.lord)}
                    </strong>
                  </div>

                  <div style={{ fontSize: "0.74rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                    {ad.start.slice(0, 10)}
                  </div>
                  <div style={{ fontSize: "0.74rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                    ↓ {ad.end.slice(0, 10)}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Selected Antardasha Pratyantar Inspector */}
          {selectedAd && selectedAd.subs && selectedAd.subs.length > 0 && (
            <div style={{ marginTop: "24px", paddingTop: "18px", borderTop: "1px solid rgba(255,255,255,0.08)" }}>
              <h4 style={{ fontSize: "0.95rem", color: "#7dd3fc", marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
                <Eye size={16} />
                Pratyantardasha (PD) Micro-Periods for {translateGraha(selectedMd.lord)} - {translateGraha(selectedAd.lord)}:
              </h4>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
                  gap: "10px",
                }}
              >
                {selectedAd.subs.map((pd, pidx) => (
                  <div
                    key={`${pd.lord}-${pidx}`}
                    style={{
                      background: "rgba(0,0,0,0.25)",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      border: "1px solid rgba(255,255,255,0.06)",
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text-main)" }}>
                      {translateGraha(pd.lord)}
                    </div>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                      {pd.start.slice(0, 10)} → {pd.end.slice(0, 10)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
