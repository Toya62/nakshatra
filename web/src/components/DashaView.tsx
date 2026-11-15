"use client";

import React, { useState } from "react";
import { VimshottariData, BirthDataInput, ChartData } from "@/lib/types";
import { TimelineView } from "@/components/TimelineView";
import { EmptyState } from "@/components/EmptyState";
import { Clock, ChevronDown, ChevronRight, Activity, Calendar } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

interface Props {
  dashas?: VimshottariData;
  birth?: BirthDataInput;
  chart?: ChartData | null;
  onNavigateToChart?: () => void;
}

export const DashaView: React.FC<Props> = ({ dashas, birth, chart, onNavigateToChart }) => {
  const { t, lang, num } = useLanguage();
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const [activeMode, setActiveMode] = useState<"timeline" | "cards">("timeline");

  if (!dashas) {
    return (
      <EmptyState
        icon={Clock}
        title="Vimshottari Dasha Timeline"
        description="Calculate your birth chart to unlock your personalized 120-year planetary dasha periods, current Mahadasha, Antardasha, and sub-cycle progression."
        actionLabel={onNavigateToChart ? "Go to Birth Chart" : undefined}
        onAction={onNavigateToChart}
      />
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
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
      {/* Top View Selector Bar */}
      {birth && (
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "var(--space-2)" }}>
          <button
            onClick={() => setActiveMode("timeline")}
            className={`chip${activeMode === "timeline" ? " active" : ""}`}
            aria-pressed={activeMode === "timeline"}
          >
            <Calendar size={14} aria-hidden="true" />
            {lang === "ne" ? "१२० वर्षे जीवन चक्र र वि.सं. क्यालेन्डर" : "Visual 120-Yr Timeline & BS Calendar"}
          </button>
          <button
            onClick={() => setActiveMode("cards")}
            className={`chip${activeMode === "cards" ? " active" : ""}`}
            aria-pressed={activeMode === "cards"}
          >
            <Activity size={14} aria-hidden="true" />
            {lang === "ne" ? "शास्त्रीय महादशा / अन्तर्दशा तालिका" : "Classical Progress & Tree View"}
          </button>
        </div>
      )}

      {/* Render Mode 1: Rich Interactive 120-Year Life Timeline */}
      {activeMode === "timeline" && birth && (
        <TimelineView birth={birth} chart={chart} />
      )}

      {/* Render Mode 2: Classical Progress & Tree View */}
      {(!birth || activeMode === "cards") && (
        <>
          {/* Header Overview Card */}
          <div className="card" style={{ padding: "var(--space-5)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)", flexWrap: "wrap", gap: "var(--space-2)" }}>
              <div>
                <h3 style={{ fontSize: "var(--type-heading)", fontWeight: 700, display: "flex", alignItems: "center", gap: "var(--space-2)", color: "var(--text-high)" }}>
                  <Clock size={18} color="var(--gold-vivid)" aria-hidden="true" />
                  {t.dasha.title}
                </h3>
                <p style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", marginTop: "2px" }}>
                  {t.dasha.subtitle}
                </p>
              </div>

              <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
                <span className="badge badge-gold">
                  {lang === "ne" ? "जन्म नक्षत्र" : "Birth"}: {dashas.birth_nakshatra} ({dashas.birth_nakshatra_lord})
                </span>
                <span className="badge badge-cyan">
                  {lang === "ne" ? "दशा शेष" : "Balance"}: {dashas.balance_lord} ({num(dashas.balance_years.toFixed(2))} {lang === "ne" ? "वर्ष" : "yrs"})
                </span>
              </div>
            </div>

            {/* Current Periods Progress Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "var(--space-4)" }}>
              {/* MD */}
              {dashas.current_md && (
                <div style={{ background: "var(--bg-subtle)", padding: "var(--space-4)", borderRadius: "var(--radius-sm)", border: "1px solid var(--gold-border)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "var(--space-1)" }}>
                    <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", letterSpacing: "0.05em" }}>MAHADASHA (MD)</span>
                    <span style={{ fontSize: "var(--type-label)", color: "var(--gold-bright)", fontWeight: 700 }}>{mdProgress.toFixed(1)}%</span>
                  </div>
                  <h4 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--gold-bright)", marginBottom: "var(--space-2)" }}>
                    {dashas.current_md.lord}
                  </h4>
                  <div style={{ width: "100%", height: "6px", background: "var(--border-subtle)", borderRadius: "3px", overflow: "hidden", marginBottom: "var(--space-2)" }}>
                    <div style={{ width: `${mdProgress}%`, height: "100%", background: "var(--gold-vivid)" }} />
                  </div>
                  <p style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", fontFamily: "var(--font-mono)" }}>
                    {dashas.current_md.start.slice(0, 10)} → {dashas.current_md.end.slice(0, 10)}
                  </p>
                </div>
              )}

              {/* AD */}
              {dashas.current_ad && (
                <div style={{ background: "var(--bg-subtle)", padding: "var(--space-4)", borderRadius: "var(--radius-sm)", border: "1px solid rgba(56,189,248,0.25)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "var(--space-1)" }}>
                    <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", letterSpacing: "0.05em" }}>ANTARDASHA (AD)</span>
                    <span style={{ fontSize: "var(--type-label)", color: "var(--cyan-vivid)", fontWeight: 700 }}>{adProgress.toFixed(1)}%</span>
                  </div>
                  <h4 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--cyan-vivid)", marginBottom: "var(--space-2)" }}>
                    {dashas.current_ad.lord}
                  </h4>
                  <div style={{ width: "100%", height: "6px", background: "var(--border-subtle)", borderRadius: "3px", overflow: "hidden", marginBottom: "var(--space-2)" }}>
                    <div style={{ width: `${adProgress}%`, height: "100%", background: "var(--cyan-vivid)" }} />
                  </div>
                  <p style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", fontFamily: "var(--font-mono)" }}>
                    {dashas.current_ad.start.slice(0, 10)} → {dashas.current_ad.end.slice(0, 10)}
                  </p>
                </div>
              )}

              {/* PD */}
              {dashas.current_pd && (
                <div style={{ background: "var(--bg-subtle)", padding: "var(--space-4)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "var(--space-1)" }}>
                    <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", letterSpacing: "0.05em" }}>PRATYANTARDASHA (PD)</span>
                    <span style={{ fontSize: "var(--type-label)", color: "var(--text-high)", fontWeight: 700 }}>{pdProgress.toFixed(1)}%</span>
                  </div>
                  <h4 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-high)", marginBottom: "var(--space-2)" }}>
                    {dashas.current_pd.lord}
                  </h4>
                  <div style={{ width: "100%", height: "6px", background: "var(--border-subtle)", borderRadius: "3px", overflow: "hidden", marginBottom: "var(--space-2)" }}>
                    <div style={{ width: `${pdProgress}%`, height: "100%", background: "var(--gold-vivid)" }} />
                  </div>
                  <p style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", fontFamily: "var(--font-mono)" }}>
                    {dashas.current_pd.start.slice(0, 10)} → {dashas.current_pd.end.slice(0, 10)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Mahadasha Timeline Accordion */}
          <div className="card" style={{ padding: "var(--space-5)" }}>
            <h4 style={{ fontSize: "var(--type-heading)", fontWeight: 700, marginBottom: "var(--space-3)", color: "var(--text-high)" }}>
              Lifelong Mahadasha Timeline Tree
            </h4>

            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
              {dashas.mahadashas.map((md, idx) => {
                const itemKey = `${md.lord}-${md.start}-${idx}`;
                const isCurrent = dashas.current_md?.lord === md.lord;
                const isExpanded = expandedKey === itemKey;

                return (
                  <div
                    key={itemKey}
                    style={{
                      background: isCurrent ? "var(--gold-dim)" : "var(--bg-subtle)",
                      border: isCurrent ? "1px solid var(--gold-border)" : "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-sm)",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      onClick={() => setExpandedKey(isExpanded ? null : itemKey)}
                      style={{
                        padding: "var(--space-3) var(--space-4)",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        cursor: "pointer",
                      }}
                      role="button"
                      aria-expanded={isExpanded}
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          setExpandedKey(isExpanded ? null : itemKey);
                        }
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                        {isExpanded ? <ChevronDown size={15} aria-hidden="true" /> : <ChevronRight size={15} aria-hidden="true" />}
                        <span style={{ fontWeight: 600, color: isCurrent ? "var(--gold-bright)" : "var(--text-high)" }}>
                          {md.lord} Mahadasha
                        </span>
                        {isCurrent && <span className="badge badge-gold">Active Now</span>}
                      </div>

                      <span style={{ fontSize: "var(--type-label)", color: "var(--text-mid)", fontFamily: "var(--font-mono)" }}>
                        {md.start.slice(0, 10)} → {md.end.slice(0, 10)} ({md.duration_years ? `${md.duration_years.toFixed(1)} yrs` : ""})
                      </span>
                    </div>

                    {isExpanded && md.subs && (
                      <div style={{ padding: "0 var(--space-4) var(--space-3) var(--space-6)", display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 150px), 1fr))", gap: "var(--space-2)" }}>
                        {md.subs.map((ad, adIdx) => (
                          <div
                            key={`${ad.lord}-${ad.start}-${adIdx}`}
                            style={{
                              background: "var(--bg-input)",
                              padding: "var(--space-2) var(--space-3)",
                              borderRadius: "var(--radius-sm)",
                              border: "1px solid var(--border-subtle)",
                            }}
                          >
                            <div style={{ fontWeight: 600, fontSize: "var(--type-label)", color: "var(--cyan-vivid)" }}>{ad.lord}</div>
                            <div style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", fontFamily: "var(--font-mono)" }}>
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
        </>
      )}
    </div>
  );
};
