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
  Sun: { bg: "var(--amber-dim)", border: "var(--graha-sun)", text: "var(--graha-sun)" },
  Moon: { bg: "var(--cyan-dim)", border: "var(--graha-moon)", text: "var(--graha-moon)" },
  Mars: { bg: "var(--rose-dim)", border: "var(--graha-mars)", text: "var(--graha-mars)" },
  Mercury: { bg: "var(--emerald-dim)", border: "var(--graha-mercury)", text: "var(--graha-mercury)" },
  Jupiter: { bg: "var(--gold-dim)", border: "var(--graha-jupiter)", text: "var(--graha-jupiter)" },
  Venus: { bg: "var(--rose-dim)", border: "var(--graha-venus)", text: "var(--graha-venus)" },
  Saturn: { bg: "rgba(99, 102, 241, 0.15)", border: "var(--graha-saturn)", text: "var(--graha-saturn)" },
  Rahu: { bg: "rgba(168, 85, 247, 0.15)", border: "var(--graha-rahu)", text: "var(--graha-rahu)" },
  "North Node": { bg: "rgba(168, 85, 247, 0.15)", border: "var(--graha-rahu)", text: "var(--graha-rahu)" },
  Ketu: { bg: "var(--bg-subtle)", border: "var(--graha-ketu)", text: "var(--graha-ketu)" },
  "South Node": { bg: "var(--bg-subtle)", border: "var(--graha-ketu)", text: "var(--graha-ketu)" },
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
    const normalized = name === "North Node" ? "Rahu" : name === "South Node" ? "Ketu" : name;
    if (!useDevanagari || !nomenclature?.planets) return normalized;
    return nomenclature.planets[normalized] || nomenclature.planets[name] || normalized;
  };

  const translateSign = (name: string): string => {
    if (!useDevanagari || !nomenclature?.signs) return name;
    return nomenclature.signs[name] || name;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "22px" }}>
      {/* Top Banner & Control Bar */}
      <div className="card" style={{ padding: "20px 24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
              <Clock size={22} color="var(--gold-vivid)" />
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
                  background: "var(--gold-dim)",
                  border: "1px solid var(--gold-border)",
                  fontSize: "0.82rem",
                  color: "var(--gold-bright)",
                  fontWeight: 600,
                }}
              >
                <Calendar size={14} color="var(--gold-vivid)" />
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
                background: useDevanagari ? "var(--gold-dim)" : "var(--bg-subtle)",
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
                background: showSadeSati ? "var(--rose-dim)" : "var(--bg-subtle)",
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
            background: "var(--bg-subtle)",
            border: "1px solid var(--border-subtle)",
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
              Current Age: <strong style={{ color: "var(--gold-bright)" }}>{currentAgeYears.toFixed(2)} years</strong>
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
      <div className="card" style={{ padding: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 className="title-serif" style={{ fontSize: "1.1rem", color: "var(--text-main)", display: "flex", alignItems: "center", gap: "8px" }}>
            <Compass size={18} color="var(--gold-vivid)" />
            Vimshottari 120-Year Macro Timeline (Click any Mahadasha block to inspect)
          </h3>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Proportional Astronomical Duration
          </span>
        </div>

        {/* The Ribbon Bar Wrapper */}
        <div style={{ position: "relative", marginTop: "24px", marginBottom: "8px" }}>
          <div
            style={{
              position: "relative",
              width: "100%",
              height: "76px",
              background: "var(--bg-subtle)",
              borderRadius: "12px",
              overflow: "hidden",
              border: "1px solid var(--border-subtle)",
              display: "flex",
            }}
          >
            {mahadashas.map((md, idx) => {
              const startMs = new Date(md.start.replace("Z", "")).getTime();
              const endMs = new Date(md.end.replace("Z", "")).getTime();
              const widthPct = Math.max(1, ((endMs - startMs) / totalTimelineSpanMs) * 100);
              const style = GRAHA_COLORS[md.lord] || { bg: "var(--bg-subtle)", border: "var(--border-subtle)", text: "var(--text-high)" };
              const isSelected = selectedMd?.lord === md.lord && selectedMd?.start === md.start;

              return (
                <button
                  key={`${md.lord}-${idx}`}
                  onClick={() => {
                    setSelectedMd(md);
                    const activeSub = md.subs?.find(
                      (s) => dashas?.current_md?.lord === md.lord && dashas?.current_ad?.lord === s.lord
                    );
                    setSelectedAd(activeSub || (md.subs && md.subs.length > 0 ? md.subs[0] : null));
                  }}
                  title={`${md.lord} Mahadasha (${md.start.slice(0, 10)} to ${md.end.slice(0, 10)})`}
                  style={{
                    width: `${widthPct}%`,
                    height: "100%",
                    background: isSelected ? style.border : style.bg,
                    borderRight: "1px solid var(--border-subtle)",
                    borderTop: isSelected ? `4px solid var(--text-high)` : "none",
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
                      color: isSelected ? "#ffffff" : style.text,
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
                      color: isSelected ? "rgba(255,255,255,0.9)" : "var(--text-dim)",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {md.start.slice(0, 4)}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Current Age "You Are Here" Marker */}
          {(() => {
            const nowMs = Date.now();
            if (nowMs >= timelineBounds.startMs && nowMs <= timelineBounds.endMs) {
              const leftPct = ((nowMs - timelineBounds.startMs) / totalTimelineSpanMs) * 100;
              return (
                <div
                  style={{
                    position: "absolute",
                    top: "-20px",
                    bottom: 0,
                    left: `${leftPct}%`,
                    width: "2px",
                    background: "var(--gold-bright)",
                    boxShadow: "0 0 8px rgba(251,226,133,0.8)",
                    pointerEvents: "none",
                    zIndex: 20,
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      top: 0,
                      left: "-16px",
                      background: "var(--gold-vivid)",
                      color: "var(--bg-base)",
                      fontSize: "0.62rem",
                      fontWeight: 800,
                      padding: "1px 5px",
                      borderRadius: "4px",
                      whiteSpace: "nowrap",
                      boxShadow: "0 2px 6px rgba(0,0,0,0.5)",
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
            <div style={{ fontSize: "0.78rem", color: "var(--rose)", fontWeight: 700, marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
              <AlertCircle size={14} color="var(--rose)" />
              Transiting Saturn Sade Sati Windows (Age-calibrated 7.5-Year Cycles):
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
              {sadeSatiWindows.map((win, i) => (
                <div
                  key={i}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "8px",
                    background: "var(--rose-dim)",
                    border: "1px solid var(--rose)",
                    fontSize: "0.76rem",
                    color: "var(--rose)",
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
        <div className="card" style={{ padding: "var(--space-6)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)", flexWrap: "wrap", gap: "var(--space-3)" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                <span
                  style={{
                    width: "12px",
                    height: "12px",
                    borderRadius: "50%",
                    background: (GRAHA_COLORS[selectedMd.lord] || GRAHA_COLORS[translateGraha(selectedMd.lord)])?.border || "var(--gold-vivid)",
                  }}
                  aria-hidden="true"
                />
                <h3 style={{ fontSize: "var(--type-heading)", fontWeight: 700, color: "var(--gold-bright)" }}>
                  {translateGraha(selectedMd.lord)} Mahadasha Breakdown
                </h3>
              </div>
              <p style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", marginTop: "2px", fontFamily: "var(--font-mono)" }}>
                Epoch: {selectedMd.start.slice(0, 10)} → {selectedMd.end.slice(0, 10)}
              </p>
            </div>

            <div className="badge badge-gold" style={{ fontSize: "var(--type-micro)" }}>
              9 Sub-Antardasha Cycles (Bhuktis)
            </div>
          </div>

          {/* Antardashas Cards Grid - Balanced responsive cards */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
              gap: "var(--space-3)",
            }}
          >
            {(selectedMd.subs || []).map((ad, idx) => {
              const adName = translateGraha(ad.lord);
              const adStyle = GRAHA_COLORS[ad.lord] || GRAHA_COLORS[adName] || { bg: "var(--bg-subtle)", border: "var(--border-subtle)", text: "var(--text-high)" };
              const isSelectedAd = selectedAd?.lord === ad.lord && selectedAd?.start === ad.start;
              const isCurrent =
                dashas?.current_md?.lord === selectedMd.lord &&
                dashas?.current_ad?.lord === ad.lord;

              return (
                <div
                  key={`${ad.lord}-${idx}`}
                  onClick={() => setSelectedAd(ad)}
                  style={{
                    background: isSelectedAd ? "var(--gold-dim)" : "var(--bg-subtle)",
                    border: isSelectedAd
                      ? "1px solid var(--gold-vivid)"
                      : isCurrent
                      ? "1px solid var(--emerald)"
                      : "1px solid var(--border-subtle)",
                    boxShadow: isSelectedAd
                      ? "0 0 16px rgba(229,185,76,0.18)"
                      : isCurrent
                      ? "0 0 14px rgba(16,185,129,0.18)"
                      : "none",
                    borderRadius: "var(--radius-md)",
                    padding: "var(--space-3) var(--space-4)",
                    cursor: "pointer",
                    position: "relative",
                    transition: "all 0.18s ease",
                  }}
                  role="button"
                  aria-pressed={isSelectedAd}
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setSelectedAd(ad);
                    }
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-2)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                      <span
                        style={{
                          width: "9px",
                          height: "9px",
                          borderRadius: "50%",
                          background: adStyle.border,
                        }}
                        aria-hidden="true"
                      />
                      <strong style={{ fontSize: "var(--type-heading)", color: adStyle.text, fontWeight: 700 }}>
                        {adName}
                      </strong>
                    </div>

                    {isCurrent && (
                      <span className="badge badge-emerald" style={{ fontSize: "0.64rem", padding: "2px 6px" }}>
                        ACTIVE
                      </span>
                    )}
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", fontSize: "var(--type-micro)", color: "var(--text-mid)", fontFamily: "var(--font-mono)", whiteSpace: "nowrap" }}>
                    <span>{ad.start.slice(0, 10)}</span>
                    <span style={{ color: "var(--text-low)" }}>→</span>
                    <span>{ad.end.slice(0, 10)}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Selected Antardasha Pratyantar Inspector */}
          {selectedAd && selectedAd.subs && selectedAd.subs.length > 0 && (
            <div style={{ marginTop: "var(--space-5)", paddingTop: "var(--space-4)", borderTop: "1px solid var(--border-subtle)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)", flexWrap: "wrap", gap: "var(--space-2)" }}>
                <h4 style={{ fontSize: "var(--type-heading)", color: "var(--cyan-vivid)", display: "flex", alignItems: "center", gap: "var(--space-2)", fontWeight: 700 }}>
                  <Eye size={16} aria-hidden="true" />
                  Pratyantardasha (PD) Micro-Periods for {translateGraha(selectedMd.lord)} - {translateGraha(selectedAd.lord)}
                </h4>
                <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)" }}>
                  9 Sub-Sub Cycles (Sookshma)
                </span>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(290px, 1fr))",
                  gap: "var(--space-2)",
                }}
              >
                {selectedAd.subs.map((pd, pidx) => {
                  const pdName = translateGraha(pd.lord);
                  const pdStyle = GRAHA_COLORS[pd.lord] || GRAHA_COLORS[pdName] || { bg: "var(--bg-subtle)", border: "var(--border-subtle)", text: "var(--text-high)" };
                  const isCurrentPd =
                    dashas?.current_md?.lord === selectedMd.lord &&
                    dashas?.current_ad?.lord === selectedAd.lord &&
                    dashas?.current_pd?.lord === pd.lord;

                  return (
                    <div
                      key={`${pd.lord}-${pidx}`}
                      style={{
                        background: isCurrentPd ? "var(--emerald-dim)" : "var(--bg-subtle)",
                        padding: "var(--space-2-5) var(--space-3)",
                        borderRadius: "var(--radius-sm)",
                        border: isCurrentPd ? "1px solid var(--emerald)" : "1px solid var(--border-subtle)",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: "var(--space-1-5)",
                        minWidth: 0,
                        overflow: "hidden",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-1-5)", minWidth: 0, flexShrink: 0 }}>
                        <span
                          style={{
                            width: "7px",
                            height: "7px",
                            borderRadius: "50%",
                            background: pdStyle.border,
                            flexShrink: 0,
                          }}
                          aria-hidden="true"
                        />
                        <span style={{ fontWeight: 600, fontSize: "var(--type-label)", color: "var(--text-high)" }}>
                          {pdName}
                        </span>
                        {isCurrentPd && (
                          <span
                            className="badge badge-emerald"
                            style={{
                              fontSize: "0.58rem",
                              padding: "1px 5px",
                              letterSpacing: "0.04em",
                              fontWeight: 700,
                              lineHeight: 1.2,
                              flexShrink: 0,
                            }}
                          >
                            NOW
                          </span>
                        )}
                      </div>

                      <div
                        style={{
                          fontSize: "0.72rem",
                          color: isCurrentPd ? "var(--emerald)" : "var(--text-mid)",
                          fontFamily: "var(--font-mono)",
                          whiteSpace: "nowrap",
                          letterSpacing: "-0.015em",
                          flexShrink: 0,
                        }}
                      >
                        {pd.start.slice(0, 10)} → {pd.end.slice(0, 10)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
