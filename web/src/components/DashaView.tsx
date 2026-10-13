"use client";

import React from "react";
import { VimshottariData } from "@/lib/types";
import { Clock, ChevronDown, ChevronRight } from "lucide-react";

interface Props {
  dashas?: VimshottariData;
}

export const DashaView: React.FC<Props> = ({ dashas }) => {
  const [expandedKey, setExpandedKey] = React.useState<string | null>(null);

  if (!dashas) {
    return (
      <div className="glass-panel" style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>
        No Dasha information available. Calculate chart first.
      </div>
    );
  }

  const computeProgress = (startStr: string, endStr: string): number => {
    try {
      const start = new Date(startStr.replace("Z", "")).getTime();
      const end = new Date(endStr.replace("Z", "")).getTime();
      const now = Date.now();
      if (now <= start) return 0;
      if (now >= end) return 100;
      return Math.min(100, Math.max(0, ((now - start) / (end - start)) * 100));
    } catch {
      return 0;
    }
  };

  const mdProgress = dashas.current_md ? computeProgress(dashas.current_md.start, dashas.current_md.end) : 0;
  const adProgress = dashas.current_ad ? computeProgress(dashas.current_ad.start, dashas.current_ad.end) : 0;
  const pdProgress = dashas.current_pd ? computeProgress(dashas.current_pd.start, dashas.current_pd.end) : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header Overview Card */}
      <div className="glass-panel" style={{ padding: "20px 24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h3 className="title-serif gold-gradient-text" style={{ fontSize: "1.2rem", display: "flex", alignItems: "center", gap: "8px" }}>
              <Clock size={20} color="#e5b94c" />
              Vimshottari Dasha Engine (120-Year Cycle)
            </h3>
            <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
              Sub-second astronomical precision calibrated against natal Moon
            </p>
          </div>

          <div style={{ display: "flex", gap: "10px" }}>
            <span className="badge badge-gold">
              Birth: {dashas.birth_nakshatra} ({dashas.birth_nakshatra_lord})
            </span>
            <span className="badge badge-cyan">
              Balance: {dashas.balance_lord} ({dashas.balance_years.toFixed(2)} yrs)
            </span>
          </div>
        </div>

        {/* Current Periods Progress Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "16px" }}>
          {/* MD */}
          {dashas.current_md && (
            <div style={{ background: "rgba(0,0,0,0.25)", padding: "16px", borderRadius: "10px", border: "1px solid rgba(229,185,76,0.2)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", letterSpacing: "0.05em" }}>MAHADASHA (MD)</span>
                <span style={{ fontSize: "0.8rem", color: "#fbe285", fontWeight: 700 }}>{mdProgress.toFixed(1)}%</span>
              </div>
              <h4 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#fbe285", marginBottom: "8px" }}>
                {dashas.current_md.lord}
              </h4>
              <div style={{ width: "100%", height: "6px", background: "rgba(255,255,255,0.1)", borderRadius: "3px", overflow: "hidden", marginBottom: "8px" }}>
                <div style={{ width: `${mdProgress}%`, height: "100%", background: "linear-gradient(90deg, #e5b94c, #fbe285)" }} />
              </div>
              <p style={{ fontSize: "0.75rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                {dashas.current_md.start.slice(0, 10)} → {dashas.current_md.end.slice(0, 10)}
              </p>
            </div>
          )}

          {/* AD */}
          {dashas.current_ad && (
            <div style={{ background: "rgba(0,0,0,0.25)", padding: "16px", borderRadius: "10px", border: "1px solid rgba(56,189,248,0.2)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", letterSpacing: "0.05em" }}>ANTARDASHA (AD)</span>
                <span style={{ fontSize: "0.8rem", color: "#7dd3fc", fontWeight: 700 }}>{adProgress.toFixed(1)}%</span>
              </div>
              <h4 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#7dd3fc", marginBottom: "8px" }}>
                {dashas.current_ad.lord}
              </h4>
              <div style={{ width: "100%", height: "6px", background: "rgba(255,255,255,0.1)", borderRadius: "3px", overflow: "hidden", marginBottom: "8px" }}>
                <div style={{ width: `${adProgress}%`, height: "100%", background: "linear-gradient(90deg, #0284c7, #38bdf8)" }} />
              </div>
              <p style={{ fontSize: "0.75rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                {dashas.current_ad.start.slice(0, 10)} → {dashas.current_ad.end.slice(0, 10)}
              </p>
            </div>
          )}

          {/* PD */}
          {dashas.current_pd && (
            <div style={{ background: "rgba(0,0,0,0.25)", padding: "16px", borderRadius: "10px", border: "1px solid rgba(168,85,247,0.2)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", letterSpacing: "0.05em" }}>PRATYANTARDASHA (PD)</span>
                <span style={{ fontSize: "0.8rem", color: "#c084fc", fontWeight: 700 }}>{pdProgress.toFixed(1)}%</span>
              </div>
              <h4 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#c084fc", marginBottom: "8px" }}>
                {dashas.current_pd.lord}
              </h4>
              <div style={{ width: "100%", height: "6px", background: "rgba(255,255,255,0.1)", borderRadius: "3px", overflow: "hidden", marginBottom: "8px" }}>
                <div style={{ width: `${pdProgress}%`, height: "100%", background: "linear-gradient(90deg, #7e22ce, #a855f7)" }} />
              </div>
              <p style={{ fontSize: "0.75rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                {dashas.current_pd.start.slice(0, 10)} → {dashas.current_pd.end.slice(0, 10)}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Mahadasha Timeline Accordion */}
      <div className="glass-panel" style={{ padding: "20px" }}>
        <h4 className="title-serif gold-gradient-text" style={{ fontSize: "1.05rem", marginBottom: "14px" }}>
          Lifelong Mahadasha Timeline
        </h4>

        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {dashas.mahadashas.map((md, idx) => {
            const itemKey = `${md.lord}-${md.start}-${idx}`;
            const isCurrent = dashas.current_md?.lord === md.lord;
            const isExpanded = expandedKey === itemKey;

            return (
              <div
                key={itemKey}
                style={{
                  background: isCurrent ? "rgba(229,185,76,0.08)" : "rgba(255,255,255,0.02)",
                  border: isCurrent ? "1px solid rgba(229,185,76,0.3)" : "1px solid rgba(255,255,255,0.06)",
                  borderRadius: "8px",
                  overflow: "hidden",
                }}
              >
                <div
                  onClick={() => setExpandedKey(isExpanded ? null : itemKey)}
                  style={{
                    padding: "12px 16px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    cursor: "pointer",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    <span style={{ fontWeight: 600, color: isCurrent ? "#fbe285" : "#f1f5f9" }}>
                      {md.lord} Mahadasha
                    </span>
                    {isCurrent && <span className="badge badge-gold" style={{ fontSize: "0.7rem" }}>Active Now</span>}
                  </div>

                  <span style={{ fontSize: "0.82rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                    {md.start.slice(0, 10)} → {md.end.slice(0, 10)} ({md.duration_years ? `${md.duration_years.toFixed(1)} yrs` : ""})
                  </span>
                </div>

                {isExpanded && md.subs && (
                  <div style={{ padding: "0 16px 14px 42px", display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "8px" }}>
                    {md.subs.map((ad, adIdx) => (
                      <div
                        key={`${ad.lord}-${ad.start}-${adIdx}`}
                        style={{
                          background: "rgba(0,0,0,0.3)",
                          padding: "8px 12px",
                          borderRadius: "6px",
                          border: "1px solid rgba(255,255,255,0.04)",
                        }}
                      >
                        <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "#38bdf8" }}>{ad.lord}</div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                          {ad.start.slice(0, 10)} → {ad.end.slice(0, 10)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
