"use client";

import React, { useState, useEffect } from "react";
import { BirthDataInput, RemediesReport, PlanetRemedy } from "@/lib/types";
import { fetchRemedies } from "@/lib/api";
import { EmptyState } from "./EmptyState";
import {
  ShieldCheck,
  Sparkles,
  AlertTriangle,
  Flame,
  Clock,
  Compass,
  CheckCircle2,
  Info,
  ExternalLink,
} from "lucide-react";

interface Props {
  birth?: BirthDataInput;
  onConsultClick?: (prompt: string) => void;
}

export const RemediesView: React.FC<Props> = ({ birth, onConsultClick }) => {
  const [report, setReport] = useState<RemediesReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "high" | "parashari" | "lalkitab">("all");
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
      <div style={{ maxWidth: "980px", margin: "0 auto", width: "100%" }}>
        <EmptyState
          title="Remedies & Upayas Calculation"
          description="Enter your birth parameters to calculate tailored Parashari Mantras, Gemstones, Dāna, and authentic Lal Kitab household Upayas."
          icon={ShieldCheck}
        />
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ maxWidth: "980px", margin: "0 auto", width: "100%", padding: "var(--space-6)" }}>
        <div className="card" style={{ padding: "var(--space-8)", textAlign: "center" }}>
          <Sparkles size={28} color="var(--gold-vivid)" className="spin" style={{ margin: "0 auto var(--space-3)" }} />
          <h3 style={{ fontSize: "var(--type-heading)", color: "var(--gold-vivid)" }}>Synthesizing Vedic & Lal Kitab Remedies...</h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)", marginTop: "4px" }}>
            Evaluating afflicted grahas, dusthana placements, operating dasha lords, and Gochar transits.
          </p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div style={{ maxWidth: "980px", margin: "0 auto", width: "100%", padding: "var(--space-6)" }}>
        <div className="card" style={{ padding: "var(--space-6)", borderColor: "rgba(239, 68, 68, 0.3)" }}>
          <AlertTriangle size={24} color="#f87171" style={{ marginBottom: "var(--space-2)" }} />
          <h3 style={{ color: "#f87171", fontSize: "var(--type-body)", fontWeight: 700 }}>Remedies Calculation Error</h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>{error || "Unable to compute remedies."}</p>
        </div>
      </div>
    );
  }

  // Filter planets
  const filteredPlanets = report.afflicted_planets.filter((p) => {
    if (filter === "high") return p.severity === "High";
    return true;
  });

  const highSeverityCount = report.afflicted_planets.filter((p) => p.severity === "High").length;
  const isSadeSatiActive = report.sade_sati_status.includes("ACTIVE");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)", maxWidth: "1000px", margin: "0 auto", width: "100%" }}>
      {/* ── Header Banner ── */}
      <div className="card" style={{ padding: "var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-3)" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <ShieldCheck size={22} color="var(--gold-vivid)" aria-hidden="true" />
              <h2 style={{ fontSize: "var(--type-title)", fontWeight: 700, color: "var(--text-high)" }}>
                Vedic &amp; Lal Kitab Remedies
              </h2>
            </div>
            <p style={{ fontSize: "var(--type-small)", color: "var(--text-mid)", marginTop: "4px" }}>
              Dual-system karmic rectifications: Classical Parashari Mantras, Gemstones, and Dāna paired with Lal Kitab household Upayas and precautions.
            </p>
          </div>

          {/* Quick status pills */}
          <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap", alignItems: "center" }}>
            <span className="chip" style={{ fontSize: "var(--type-micro)" }}>
              Lagna: <strong style={{ color: "var(--gold-vivid)", marginLeft: "3px" }}>{report.natal_lagna}</strong>
            </span>
            <span className="chip" style={{ fontSize: "var(--type-micro)" }}>
              Moon: <strong style={{ color: "var(--cyan-vivid)", marginLeft: "3px" }}>{report.natal_moon}</strong>
            </span>
            <span className="chip" style={{ fontSize: "var(--type-micro)" }}>
              Dasha: <strong style={{ color: "var(--gold-vivid)", marginLeft: "3px" }}>{report.active_dasha}</strong>
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
              border: "1px solid rgba(234, 179, 8, 0.35)",
              borderRadius: "var(--radius-md)",
              display: "flex",
              alignItems: "center",
              gap: "var(--space-3)",
            }}
          >
            <AlertTriangle size={18} color="#eab308" flex-shrink={0} />
            <div style={{ fontSize: "var(--type-small)", color: "var(--text-high)" }}>
              <strong style={{ color: "#eab308" }}>Saturn Gochar Notice: </strong>
              <span>{report.sade_sati_status}. Special Saturday Chhaya Dāna and black dog seva recommended below.</span>
            </div>
          </div>
        )}
      </div>

      {/* ── Lal Kitab Inviolable Precautions (Savdhanis) Card ── */}
      <div
        className="card"
        style={{
          padding: "var(--space-4) var(--space-5)",
          background: "linear-gradient(135deg, rgba(212, 160, 23, 0.08) 0%, rgba(6, 8, 14, 0.85) 100%)",
          border: "1px solid rgba(212, 160, 23, 0.3)",
        }}
      >
        <div
          style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
          onClick={() => setShowPrecautions(!showPrecautions)}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
            <Flame size={17} color="var(--gold-vivid)" />
            <h3 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Lal Kitab Golden Rules &amp; Strict Precautions
            </h3>
          </div>
          <button type="button" className="chip" style={{ fontSize: "var(--type-micro)" }}>
            {showPrecautions ? "Collapse" : "Show Rules"}
          </button>
        </div>

        {showPrecautions && (
          <div style={{ marginTop: "var(--space-3)", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--space-3)", fontSize: "var(--type-micro)" }}>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <strong style={{ color: "var(--gold-vivid)", display: "block", marginBottom: "2px" }}>☀️ Daytime Rule (Surya Prakash):</strong>
              <span style={{ color: "var(--text-mid)" }}>All Lal Kitab Upayas must be performed between sunrise and sunset; night-time remedies are forbidden and can trigger reverse affliction.</span>
            </div>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <strong style={{ color: "var(--gold-vivid)", display: "block", marginBottom: "2px" }}>⏳ 43-Day Uninterrupted Count:</strong>
              <span style={{ color: "var(--text-mid)" }}>Perform only one planetary remedy at a time for 40 to 43 consecutive days without missing a single day. If broken, restart from day 1.</span>
            </div>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <strong style={{ color: "#f87171", display: "block", marginBottom: "2px" }}>🚫 Never Remedy Exalted Grahas:</strong>
              <span style={{ color: "var(--text-mid)" }}>Never perform remedies or donate articles for a planet in its own sign or exalted sign; doing so destroys its auspicious protection.</span>
            </div>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <strong style={{ color: "var(--cyan-vivid)", display: "block", marginBottom: "2px" }}>🧹 Clean Rooftops (Rahu Shanti):</strong>
              <span style={{ color: "var(--text-mid)" }}>Never keep unserviceable electrical scrap, fused bulbs, rusted iron, or broken furniture on the roof or under staircases.</span>
            </div>
          </div>
        )}
      </div>

      {/* ── Filter Switcher ── */}
      <div style={{ display: "flex", gap: "var(--space-2)", overflowX: "auto", paddingBottom: "2px", scrollbarWidth: "thin" }}>
        <button
          type="button"
          onClick={() => setFilter("all")}
          className={`chip${filter === "all" ? " active" : ""}`}
          style={{ fontSize: "var(--type-micro)" }}
        >
          All Afflicted Grahas ({report.total_afflictions})
        </button>
        <button
          type="button"
          onClick={() => setFilter("high")}
          className={`chip${filter === "high" ? " active" : ""}`}
          style={{ fontSize: "var(--type-micro)" }}
        >
          High Severity Priority ({highSeverityCount})
        </button>
        <button
          type="button"
          onClick={() => setFilter("parashari")}
          className={`chip${filter === "parashari" ? " active" : ""}`}
          style={{ fontSize: "var(--type-micro)" }}
        >
          Parashari Focus (Mantras &amp; Gems)
        </button>
        <button
          type="button"
          onClick={() => setFilter("lalkitab")}
          className={`chip${filter === "lalkitab" ? " active" : ""}`}
          style={{ fontSize: "var(--type-micro)" }}
        >
          Lal Kitab Focus (Upayas &amp; Animal Seva)
        </button>
      </div>

      {/* ── Afflicted Planets Remedy Cards ── */}
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
                borderLeft: `4px solid ${isHigh ? "#ef4444" : isMod ? "#eab308" : "var(--cyan-vivid)"}`,
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-4)",
              }}
            >
              {/* Card Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-3)" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                    <h3 style={{ fontSize: "var(--type-heading)", fontWeight: 700, color: "var(--gold-vivid)" }}>
                      {p.planet} in House {p.house} ({p.sign})
                    </h3>
                    <span
                      style={{
                        fontSize: "var(--type-micro)",
                        padding: "3px 9px",
                        borderRadius: "10px",
                        fontWeight: 700,
                        background: isHigh ? "rgba(239, 68, 68, 0.2)" : isMod ? "rgba(234, 179, 8, 0.2)" : "rgba(56, 189, 248, 0.2)",
                        color: isHigh ? "#f87171" : isMod ? "#eab308" : "var(--cyan-vivid)",
                        border: `1px solid ${isHigh ? "#ef4444" : isMod ? "#eab308" : "var(--cyan-vivid)"}`,
                      }}
                    >
                      {p.severity} Severity
                    </span>
                    <span className="chip" style={{ fontSize: "var(--type-micro)", padding: "2px 8px" }}>
                      Dignity: {p.dignity}
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
                          background: "rgba(255,255,255,0.03)",
                          padding: "2px 8px",
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
                    const prompt = `Explain the classical Parashari remedies and Lal Kitab Upayas for my afflicted ${p.planet} in House ${p.house} (${p.sign}) with exact precautions.`;
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
                  <span>Consult AI on {p.planet}</span>
                </button>
              </div>

              {/* ── Two-Column Dual-System Grid ── */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    filter === "parashari"
                      ? "1fr"
                      : filter === "lalkitab"
                      ? "1fr"
                      : "repeat(auto-fit, minmax(340px, 1fr))",
                  gap: "var(--space-4)",
                }}
              >
                {/* 1. Parashari Column */}
                {filter !== "lalkitab" && (
                  <div
                    style={{
                      background: "rgba(212, 160, 23, 0.03)",
                      border: "1px solid rgba(212, 160, 23, 0.2)",
                      borderRadius: "var(--radius-md)",
                      padding: "var(--space-4)",
                      display: "flex",
                      flexDirection: "column",
                      gap: "var(--space-3)",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", borderBottom: "1px solid rgba(212, 160, 23, 0.15)", paddingBottom: "var(--space-2)" }}>
                      <Compass size={15} color="var(--gold-vivid)" />
                      <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                        Classical Parashari Prescription
                      </h4>
                    </div>

                    <div>
                      <span style={{ fontSize: "var(--type-micro)", color: "var(--text-low)", textTransform: "uppercase" }}>Deity &amp; Practice:</span>
                      <p style={{ fontSize: "var(--type-small)", color: "var(--text-high)", fontWeight: 600 }}>{p.parashari.deity}</p>
                      <p style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", marginTop: "2px" }}>{p.parashari.spiritual_practice}</p>
                    </div>

                    <div>
                      <span style={{ fontSize: "var(--type-micro)", color: "var(--text-low)", textTransform: "uppercase" }}>Vedic Beej Mantra:</span>
                      <pre
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: "var(--type-small)",
                          color: "var(--gold-bright)",
                          background: "rgba(0, 0, 0, 0.5)",
                          padding: "8px 10px",
                          borderRadius: "var(--radius-sm)",
                          border: "1px solid rgba(212, 160, 23, 0.2)",
                          marginTop: "3px",
                          whiteSpace: "pre-wrap",
                        }}
                      >
                        {p.parashari.beej_mantra}
                      </pre>
                      <span style={{ fontSize: "var(--type-micro)", color: "var(--text-low)" }}>Prescribed count: {p.parashari.mantra_count}</span>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)", fontSize: "var(--type-small)" }}>
                      <div style={{ background: "rgba(0,0,0,0.25)", padding: "6px 8px", borderRadius: "var(--radius-sm)" }}>
                        <span style={{ color: "var(--cyan-vivid)", display: "block" }}>Gemstone:</span>
                        <strong style={{ color: "var(--text-high)" }}>{p.parashari.gemstone}</strong>
                        <span style={{ color: "var(--text-low)", display: "block", fontSize: "var(--type-micro)" }}>Sub: {p.parashari.substitute_gem}</span>
                      </div>
                      <div style={{ background: "rgba(0,0,0,0.25)", padding: "6px 8px", borderRadius: "var(--radius-sm)" }}>
                        <span style={{ color: "var(--cyan-vivid)", display: "block" }}>Metal &amp; Finger:</span>
                        <strong style={{ color: "var(--text-high)" }}>{p.parashari.metal}</strong>
                        <span style={{ color: "var(--text-low)", display: "block", fontSize: "var(--type-micro)" }}>{p.parashari.gem_finger}</span>
                      </div>
                    </div>

                    {p.parashari.gem_caution && (
                      <div style={{ fontSize: "var(--type-small)", color: "var(--amber)", background: "rgba(234, 179, 8, 0.08)", padding: "6px 10px", borderRadius: "var(--radius-sm)" }}>
                        ⚠️ {p.parashari.gem_caution}
                      </div>
                    )}

                    <div style={{ fontSize: "var(--type-small)", borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: "var(--space-2)" }}>
                      <span style={{ color: "var(--text-low)" }}>Dāna ({p.parashari.charity_day}): </span>
                      <span style={{ color: "var(--text-mid)" }}>{p.parashari.charity_items.join(", ")}</span>
                    </div>
                  </div>
                )}

                {/* 2. Lal Kitab Column */}
                {filter !== "parashari" && (
                  <div
                    style={{
                      background: "rgba(56, 189, 248, 0.03)",
                      border: "1px solid rgba(56, 189, 248, 0.2)",
                      borderRadius: "var(--radius-md)",
                      padding: "var(--space-4)",
                      display: "flex",
                      flexDirection: "column",
                      gap: "var(--space-3)",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", borderBottom: "1px solid rgba(56, 189, 248, 0.15)", paddingBottom: "var(--space-2)" }}>
                      <ShieldCheck size={15} color="var(--cyan-vivid)" />
                      <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--cyan-vivid)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                        Authentic Lal Kitab Upaya
                      </h4>
                    </div>

                    <div>
                      <span style={{ fontSize: "var(--type-micro)", color: "var(--text-low)", textTransform: "uppercase" }}>Practical Household Remedy:</span>
                      <p style={{ fontSize: "var(--type-small)", color: "var(--text-high)", marginTop: "2px", fontWeight: 500 }}>
                        {p.lal_kitab.household_remedy}
                      </p>
                    </div>

                    <div>
                      <span style={{ fontSize: "var(--type-micro)", color: "var(--text-low)", textTransform: "uppercase" }}>Symbolic Action (Jal Pravah / Earth):</span>
                      <p style={{ fontSize: "var(--type-small)", color: "var(--text-mid)", marginTop: "2px" }}>
                        {p.lal_kitab.symbolic_action}
                      </p>
                    </div>

                    <div>
                      <span style={{ fontSize: "var(--type-micro)", color: "var(--text-low)", textTransform: "uppercase" }}>Creature &amp; Animal Seva:</span>
                      <p style={{ fontSize: "var(--type-small)", color: "var(--emerald)", marginTop: "2px", fontWeight: 500 }}>
                        🐾 {p.lal_kitab.creature_service}
                      </p>
                    </div>

                    {/* Strict Precautions (Savdhanis) */}
                    <div
                      style={{
                        background: "rgba(239, 68, 68, 0.08)",
                        border: "1px solid rgba(239, 68, 68, 0.25)",
                        borderRadius: "var(--radius-sm)",
                        padding: "10px 12px",
                        marginTop: "auto",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                        <AlertTriangle size={14} color="#f87171" />
                        <strong style={{ fontSize: "var(--type-small)", color: "#f87171", textTransform: "uppercase" }}>Strict Lal Kitab Precautions (Savdhanis):</strong>
                      </div>
                      <ul style={{ paddingLeft: "18px", margin: 0, fontSize: "var(--type-small)", color: "var(--text-high)", lineHeight: 1.5 }}>
                        {p.lal_kitab.forbidden_actions.map((act, aIdx) => (
                          <li key={aIdx}>{act}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
