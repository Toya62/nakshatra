"use client";

import React, { useState, useEffect } from "react";
import { BirthDataInput, RemediesReport } from "@/lib/types";
import { fetchRemedies } from "@/lib/api";
import { EmptyState } from "./EmptyState";
import { useLanguage } from "@/context/LanguageContext";
import {
  ShieldCheck,
  Sparkles,
  AlertTriangle,
  Flame,
  Compass,
} from "lucide-react";

interface Props {
  birth?: BirthDataInput;
  onConsultClick?: (prompt: string) => void;
}

export const RemediesView: React.FC<Props> = ({ birth, onConsultClick }) => {
  const { t, lang, num } = useLanguage();
  const [report, setReport] = useState<RemediesReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "high" | "moderate">("all");
  const [showPrecautions, setShowPrecautions] = useState(true);

  useEffect(() => {
    if (!birth) {
      setReport(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchRemedies(birth)
      .then((data) => {
        if (!cancelled) {
          setReport(data);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError((err as Error).message);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [birth]);

  if (!birth) {
    return (
      <div style={{ maxWidth: "var(--size-container)", margin: "0 auto", width: "100%" }}>
        <EmptyState
          title={t.remedies.emptyTitle}
          description={t.remedies.emptyDesc}
          icon={ShieldCheck}
        />
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ maxWidth: "var(--size-container)", margin: "0 auto", width: "100%", padding: "var(--space-6)" }}>
        <div className="card" style={{ padding: "var(--space-8)", textAlign: "center" }}>
          <Sparkles size={28} color="var(--gold-vivid)" className="spin" style={{ margin: "0 auto var(--space-3)" }} />
          <h3 style={{ fontSize: "var(--type-heading)", color: "var(--gold-vivid)" }}>{t.remedies.synthesizing}</h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)", marginTop: "var(--space-1)" }}>
            {t.remedies.synthesizingDesc}
          </p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div style={{ maxWidth: "var(--size-container)", margin: "0 auto", width: "100%", padding: "var(--space-6)" }}>
        <div className="card" style={{ padding: "var(--space-6)", borderColor: "var(--rose)" }}>
          <AlertTriangle size={24} color="var(--rose)" style={{ marginBottom: "var(--space-2)" }} />
          <h3 style={{ color: "var(--rose)", fontSize: "var(--type-body)", fontWeight: 700 }}>{t.remedies.calculationError}</h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>{error || "Unable to compute remedies."}</p>
        </div>
      </div>
    );
  }

  // Filter planets
  const filteredPlanets = report.afflicted_planets.filter((p) => {
    if (filter === "high") return p.severity === "High";
    if (filter === "moderate") return p.severity === "Moderate";
    return true;
  });

  const highSeverityCount = report.afflicted_planets.filter((p) => p.severity === "High").length;
  const modSeverityCount = report.afflicted_planets.filter((p) => p.severity === "Moderate").length;
  const isSadeSatiActive = report.sade_sati_status.includes("ACTIVE");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)", maxWidth: "var(--size-container-lg)", margin: "0 auto", width: "100%" }}>
      {/* ── Header Banner ── */}
      <div className="card" style={{ padding: "var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-3)" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <ShieldCheck size={22} color="var(--gold-vivid)" aria-hidden="true" />
              <h2 style={{ fontSize: "var(--type-title)", fontWeight: 700, color: "var(--text-high)" }}>
                {t.remedies.title}
              </h2>
            </div>
            <p style={{ fontSize: "var(--type-small)", color: "var(--text-mid)", marginTop: "var(--space-1)" }}>
              {t.remedies.subtitle}
            </p>
          </div>

          {/* Quick status pills */}
          <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap", alignItems: "center" }}>
            <span className="chip" style={{ fontSize: "var(--type-micro)" }}>
              {lang === "ne" ? "लग्न:" : "Lagna:"} <strong style={{ color: "var(--gold-vivid)", marginLeft: "var(--space-0-5)" }}>{report.natal_lagna}</strong>
            </span>
            <span className="chip" style={{ fontSize: "var(--type-micro)" }}>
              {lang === "ne" ? "चन्द्र:" : "Moon:"} <strong style={{ color: "var(--cyan-vivid)", marginLeft: "var(--space-0-5)" }}>{report.natal_moon}</strong>
            </span>
            <span className="chip" style={{ fontSize: "var(--type-micro)" }}>
              {lang === "ne" ? "दशा:" : "Dasha:"} <strong style={{ color: "var(--gold-vivid)", marginLeft: "var(--space-0-5)" }}>{report.active_dasha}</strong>
            </span>
          </div>
        </div>

        {/* Sade Sati Alert Banner */}
        {isSadeSatiActive && (
          <div
            style={{
              marginTop: "var(--space-4)",
              padding: "var(--space-3) var(--space-4)",
              background: "rgba(234, 179, 8, 0.12)",
              border: "1px solid var(--amber)",
              borderRadius: "var(--radius-md)",
              display: "flex",
              alignItems: "center",
              gap: "var(--space-3)",
            }}
          >
            <AlertTriangle size={18} color="var(--amber)" style={{ flexShrink: 0 }} />
            <div style={{ fontSize: "var(--type-small)", color: "var(--text-high)" }}>
              <strong style={{ color: "var(--amber)" }}>{lang === "ne" ? "शनि गोचर सूचना: " : "Saturn Gochar Notice: "}</strong>
              <span>{report.sade_sati_status}. {lang === "ne" ? "विशेष शनिबार छाया दान तथा कालो कुकुरको सेवा सिफारिस गरिएको छ।" : "Special Saturday Chhaya Dāna and black dog seva recommended below."}</span>
            </div>
          </div>
        )}
      </div>

      {/* ── Lal Kitab Golden Rules & Strict Precautions Card ── */}
      <div
        className="card"
        style={{
          padding: "var(--space-4) var(--space-5)",
          background: "linear-gradient(135deg, var(--gold-dim) 0%, var(--bg-card) 100%)",
          border: "1px solid var(--gold-border)",
        }}
      >
        <div
          style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
          onClick={() => setShowPrecautions(!showPrecautions)}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
            <Flame size={17} color="var(--gold-vivid)" />
            <h3 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              {t.remedies.goldenRules}
            </h3>
          </div>
          <button type="button" className="chip" style={{ fontSize: "var(--type-micro)" }}>
            {showPrecautions ? t.remedies.collapse : t.remedies.showRules}
          </button>
        </div>

        {showPrecautions && (
          <div style={{ marginTop: "var(--space-3)", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(var(--size-xl), 1fr))", gap: "var(--space-3)", fontSize: "var(--type-micro)" }}>
            <div style={{ background: "var(--bg-input)", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <strong style={{ color: "var(--gold-vivid)", display: "block", marginBottom: "var(--space-0-5)" }}>{t.remedies.daytimeRuleTitle}</strong>
              <span style={{ color: "var(--text-mid)" }}>{t.remedies.daytimeRuleDesc}</span>
            </div>
            <div style={{ background: "var(--bg-input)", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <strong style={{ color: "var(--gold-vivid)", display: "block", marginBottom: "var(--space-0-5)" }}>{t.remedies.count43Title}</strong>
              <span style={{ color: "var(--text-mid)" }}>{t.remedies.count43Desc}</span>
            </div>
            <div style={{ background: "var(--bg-input)", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <strong style={{ color: "var(--rose)", display: "block", marginBottom: "var(--space-0-5)" }}>{t.remedies.exaltedRuleTitle}</strong>
              <span style={{ color: "var(--text-mid)" }}>{t.remedies.exaltedRuleDesc}</span>
            </div>
            <div style={{ background: "var(--bg-input)", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <strong style={{ color: "var(--cyan-vivid)", display: "block", marginBottom: "var(--space-0-5)" }}>{t.remedies.cleanRooftopsTitle}</strong>
              <span style={{ color: "var(--text-mid)" }}>{t.remedies.cleanRooftopsDesc}</span>
            </div>
          </div>
        )}
      </div>

      {/* ── Filter Switcher ── */}
      <div style={{ display: "flex", gap: "var(--space-2)", overflowX: "auto", paddingBottom: "var(--space-0-5)", scrollbarWidth: "thin" }}>
        <button
          type="button"
          onClick={() => setFilter("all")}
          className={`chip${filter === "all" ? " active" : ""}`}
          style={{ fontSize: "var(--type-micro)" }}
        >
          {`${t.remedies.filterAll} (${num(report.total_afflictions)})`}
        </button>
        <button
          type="button"
          onClick={() => setFilter("high")}
          className={`chip${filter === "high" ? " active" : ""}`}
          style={{ fontSize: "var(--type-micro)" }}
        >
          {`${t.remedies.filterHigh} (${num(highSeverityCount)})`}
        </button>
        <button
          type="button"
          onClick={() => setFilter("moderate")}
          className={`chip${filter === "moderate" ? " active" : ""}`}
          style={{ fontSize: "var(--type-micro)" }}
        >
          {`${t.remedies.filterModerate} (${num(modSeverityCount)})`}
        </button>
      </div>

      {/* ── Afflicted Planets Lal Kitab Upaya Cards ── */}
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        {filteredPlanets.map((p) => {
          const isHigh = p.severity === "High";
          const isMod = p.severity === "Moderate";

          return (
            <div
              key={p.planet}
              className="card"
              style={{
                padding: "var(--space-5)",
                borderLeft: `4px solid ${isHigh ? "var(--rose)" : isMod ? "var(--amber)" : "var(--cyan-vivid)"}`,
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-4)",
              }}
            >
              {/* Card Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-3)" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
                    <h3 style={{ fontSize: "var(--type-heading)", fontWeight: 700, color: "var(--gold-vivid)" }}>
                      {lang === "ne" ? (t.planets.names[p.planet as keyof typeof t.planets.names] || p.planet) : p.planet} {lang === "ne" ? `भाव ${num(p.house)} मा` : `in House ${p.house}`} ({lang === "ne" ? (t.zodiac.signs[p.sign as keyof typeof t.zodiac.signs] || p.sign) : p.sign})
                    </h3>
                    <span
                      style={{
                        fontSize: "var(--type-micro)",
                        padding: "var(--space-1) var(--space-2)",
                        borderRadius: "var(--radius-sm)",
                        fontWeight: 700,
                        background: isHigh ? "var(--rose-dim)" : isMod ? "var(--amber-dim)" : "var(--cyan-dim)",
                        color: isHigh ? "var(--rose)" : isMod ? "var(--amber)" : "var(--cyan-vivid)",
                        border: `1px solid ${isHigh ? "var(--rose)" : isMod ? "var(--amber)" : "var(--cyan-vivid)"}`,
                      }}
                    >
                      {isHigh ? (lang === "ne" ? "उच्च तीव्रता" : "High Severity") : isMod ? (lang === "ne" ? "मध्यम तीव्रता" : "Moderate Severity") : (lang === "ne" ? "सामान्य तीव्रता" : "Low Severity")}
                    </span>
                    <span className="chip" style={{ fontSize: "var(--type-micro)", padding: "0 var(--space-2)" }}>
                      {lang === "ne" ? "स्थिति:" : "Dignity:"} {p.dignity}
                    </span>
                  </div>

                  {/* Affliction reasons */}
                  <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap", marginTop: "var(--space-2)" }}>
                    {p.affliction_reasons.map((r, idx) => (
                      <span
                        key={idx}
                        style={{
                          fontSize: "var(--type-micro)",
                          color: "var(--text-mid)",
                          background: "var(--bg-subtle)",
                          padding: "var(--space-0) var(--space-2)",
                          borderRadius: "var(--radius-sm)",
                          border: "1px solid var(--border-subtle)",
                        }}
                      >
                        • {r}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Consultation trigger button */}
                <button
                  type="button"
                  onClick={() => {
                    const prompt = `Explain the authentic Lal Kitab Upayas and strict precautions (savdhanis) for my afflicted ${p.planet} in House ${p.house} (${p.sign}) based on classical Lal Kitab.`;
                    if (onConsultClick) {
                      onConsultClick(prompt);
                    } else if (typeof window !== "undefined") {
                      window.location.hash = "#consult";
                    }
                  }}
                  className="chip active"
                  style={{ fontSize: "var(--type-micro)", flexShrink: 0 }}
                >
                  <Sparkles size={12} color="var(--gold-vivid)" aria-hidden="true" />
                  <span>{lang === "ne" ? `${t.planets.names[p.planet as keyof typeof t.planets.names] || p.planet} बारे AI परामर्श` : `Consult AI on ${p.planet} Upaya`}</span>
                </button>
              </div>

              {/* ── Lal Kitab 4-Pillar Remedial Architecture ── */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                  gap: "var(--space-3)",
                }}
              >
                {/* 1. Practical Household Remedy (Gharelu Upaya) */}
                <div
                  style={{
                    background: "var(--bg-input)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    padding: "var(--space-3) var(--space-4)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "var(--space-1-5)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                    <ShieldCheck size={16} color="var(--gold-vivid)" />
                    <span style={{ fontSize: "var(--type-micro)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                      {t.remedies.householdRemedy}
                    </span>
                  </div>
                  <p style={{ fontSize: "var(--type-small)", color: "var(--text-high)", lineHeight: 1.5, margin: 0, fontWeight: 500 }}>
                    {p.lal_kitab.household_remedy}
                  </p>
                </div>

                {/* 2. Symbolic Action (Jal Pravah / Earth) */}
                <div
                  style={{
                    background: "var(--bg-input)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    padding: "var(--space-3) var(--space-4)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "var(--space-1-5)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                    <Compass size={16} color="var(--cyan-vivid)" />
                    <span style={{ fontSize: "var(--type-micro)", fontWeight: 700, color: "var(--cyan-vivid)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                      {t.remedies.symbolicAction}
                    </span>
                  </div>
                  <p style={{ fontSize: "var(--type-small)", color: "var(--text-high)", lineHeight: 1.5, margin: 0 }}>
                    {p.lal_kitab.symbolic_action}
                  </p>
                </div>

                {/* 3. Creature & Animal Service (Jeev Seva) */}
                <div
                  style={{
                    background: "var(--bg-input)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    padding: "var(--space-3) var(--space-4)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "var(--space-1-5)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                    <Flame size={16} color="var(--emerald)" />
                    <span style={{ fontSize: "var(--type-micro)", fontWeight: 700, color: "var(--emerald)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                      {t.remedies.creatureService}
                    </span>
                  </div>
                  <p style={{ fontSize: "var(--type-small)", color: "var(--emerald)", lineHeight: 1.5, margin: 0, fontWeight: 500 }}>
                    🐾 {p.lal_kitab.creature_service}
                  </p>
                </div>
              </div>

              {/* 4. Strict Precautions (Savdhanis / Parhez) Alert Banner */}
              <div
                style={{
                  background: "var(--rose-dim)",
                  border: "1px solid var(--rose)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-3) var(--space-4)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-1-5)" }}>
                  <AlertTriangle size={15} color="var(--rose)" />
                  <strong style={{ fontSize: "var(--type-small)", color: "var(--rose)", textTransform: "uppercase", letterSpacing: "0.03em" }}>
                    {t.remedies.strictPrecautions}
                  </strong>
                </div>
                <ul style={{ paddingLeft: "var(--space-4)", margin: 0, fontSize: "var(--type-small)", color: "var(--text-high)", lineHeight: 1.5 }}>
                  {p.lal_kitab.forbidden_actions.map((act, aIdx) => (
                    <li key={aIdx} style={{ marginBottom: "var(--space-0-5)" }}>
                      {act}
                    </li>
                  ))}
                </ul>
              </div>

              {/* 5. Daytime & 43-Day Execution Rule Tag */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "var(--space-2)", borderTop: "1px solid var(--border-subtle)", paddingTop: "var(--space-2)" }}>
                <span className="chip" style={{ fontSize: "var(--type-micro)", color: "var(--gold-vivid)", background: "var(--gold-dim)", borderColor: "var(--gold-border)" }}>
                  ☀️ {t.remedies.daytimeTag}
                </span>
                <span style={{ fontSize: "var(--type-micro)", color: "var(--text-low)" }}>
                  {lang === "ne" ? "४३ दिन नबिराई सम्पन्न गर्नुहोस्" : "Must be performed unbroken for 43 days"}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
