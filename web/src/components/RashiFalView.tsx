"use client";

import React, { useEffect, useState } from "react";
import { Sun, ShieldAlert, Clock, Activity, Calendar } from "lucide-react";
import {
  BirthDataInput,
  GrahaResult,
  RashiFalInput,
  RashiFalReport,
} from "@/lib/types";
import { fetchRashiFal } from "@/lib/api";

interface Props {
  birth?: BirthDataInput;
}

const PERIODS: { id: string; label: string }[] = [
  { id: "daily", label: "Daily" },
  { id: "monthly", label: "Monthly" },
  { id: "yearly", label: "Yearly" },
];

const VERDICT_STYLE: Record<string, { color: string; bg: string; border: string }> = {
  excellent: { color: "var(--emerald)", bg: "rgba(16, 185, 129, 0.10)", border: "rgba(16, 185, 129, 0.25)" },
  good: { color: "var(--cyan-vivid)", bg: "rgba(6, 182, 212, 0.10)", border: "rgba(6, 182, 212, 0.25)" },
  mixed: { color: "var(--amber)", bg: "rgba(245, 158, 11, 0.10)", border: "rgba(245, 158, 11, 0.25)" },
  challenging: { color: "var(--rose)", bg: "rgba(239, 68, 68, 0.10)", border: "rgba(239, 68, 68, 0.25)" },
  difficult: { color: "var(--rose)", bg: "rgba(239, 68, 68, 0.14)", border: "rgba(239, 68, 68, 0.30)" },
};

export const RashiFalView: React.FC<Props> = ({ birth }: Props) => {
  const [report, setReport] = useState<RashiFalReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState("daily");
  const [referenceDate, setReferenceDate] = useState("");

  useEffect(() => {
    if (!birth) {
      setReport(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);

    const payload: RashiFalInput = {
      year: birth.year,
      month: birth.month,
      day: birth.day,
      hour: birth.hour,
      minute: birth.minute,
      second: birth.second ?? 0,
      latitude: birth.latitude,
      longitude: birth.longitude,
      timezone: birth.timezone,
      place_name: birth.place_name,
      period,
      reference_date: referenceDate || undefined,
      ayanamsa: birth.ayanamsa || "jhora_lahiri",
      house_system: birth.house_system || "WholeSign",
    };

    fetchRashiFal(payload)
      .then((data) => {
        if (!cancelled) setReport(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError((err as Error).message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [birth, period, referenceDate]);

  if (!birth) {
    return (
      <div style={{ maxWidth: "var(--size-container)", margin: "0 auto", width: "100%" }}>
        <div className="card" style={{ padding: "var(--space-8)", textAlign: "center" }}>
          <Sun size={32} color="var(--gold-vivid)" style={{ margin: "0 auto var(--space-3)" }} />
          <h3 style={{ fontSize: "var(--type-heading)", color: "var(--gold-vivid)", marginBottom: "var(--space-1)" }}>
            Rashi Fal — Moon-sign Horoscope
          </h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>
            Enter your birth parameters to read daily, monthly or yearly transits from your natal Moon sign
            (Chandra Lagna), with graha-wise results, Double Transit and Sade Sati status.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ maxWidth: "var(--size-container)", margin: "0 auto", width: "100%", padding: "var(--space-6)" }}>
        <div className="card" style={{ padding: "var(--space-8)", textAlign: "center" }}>
          <Clock size={32} color="var(--gold-vivid)" className="spin" style={{ margin: "0 auto var(--space-3)" }} />
          <h3 style={{ fontSize: "var(--type-heading)", color: "var(--gold-vivid)", marginBottom: "var(--space-1)" }}>
            Casting Rashi Fal…
          </h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>
            Reading transits from Chandra Lagna.
          </p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div style={{ maxWidth: "var(--size-container)", margin: "0 auto", width: "100%", padding: "var(--space-6)" }}>
        <div className="card" style={{ padding: "var(--space-6)", borderColor: "var(--rose)" }}>
          <ShieldAlert size={24} color="var(--rose)" style={{ marginBottom: "var(--space-2)" }} />
          <h3 style={{ color: "var(--rose)", fontSize: "var(--type-body)", fontWeight: 700 }}>Rashi Fal Error</h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>{error || "Unable to compute Rashi Fal."}</p>
        </div>
      </div>
    );
  }

  const style = VERDICT_STYLE[report.overall_verdict.split(" ")[0].toLowerCase()] ?? VERDICT_STYLE.mixed;
  const favourable = report.graha_results.filter((g) => g.favourable);
  const challenging = report.graha_results.filter((g) => !g.favourable);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)", maxWidth: "var(--size-container-lg)", margin: "0 auto", width: "100%" }}>
      {/* ── Header Banner ── */}
      <div className="card" style={{ padding: "var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-3)" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <Activity size={24} color="var(--gold-vivid)" />
              <h2 style={{ fontSize: "var(--type-title)", fontWeight: 700, color: "var(--text-high)" }}>
                Rashi Fal — {report.period_label}
              </h2>
            </div>
            <p style={{ fontSize: "var(--type-small)", color: "var(--text-mid)", marginTop: "var(--space-1)" }}>
              Chandra Lagna: {report.moon_sign} {report.moon_nakshatra ? `(${report.moon_nakshatra})` : ""}. Reference: {report.reference_date}.
            </p>
          </div>
          <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-1)" }}>
              <label style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textTransform: "uppercase" }}>Period</label>
              <div style={{ display: "flex", gap: "var(--space-1)" }}>
                {PERIODS.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setPeriod(p.id)}
                    style={{
                      padding: "4px 10px",
                      borderRadius: "var(--radius-sm)",
                      border: `1px solid ${period === p.id ? "var(--gold-border)" : "var(--border-subtle)"}`,
                      background: period === p.id ? "var(--gold-dim)" : "var(--bg-subtle)",
                      color: period === p.id ? "var(--gold-vivid)" : "var(--text-mid)",
                      fontSize: "var(--type-micro)",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-1)" }}>
              <label style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textTransform: "uppercase" }}>Reference Date</label>
              <input
                type="date"
                value={referenceDate}
                onChange={(e) => setReferenceDate(e.target.value)}
                style={{ padding: "6px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)", background: "var(--bg-input)", color: "var(--text-high)", fontSize: "var(--type-small)" }}
              />
            </div>
          </div>
        </div>

        <div style={{ marginTop: "var(--space-4)", padding: "var(--space-3) var(--space-4)", background: "var(--gold-dim)", border: "1px solid var(--gold-border)", borderRadius: "var(--radius-md)", display: "flex", alignItems: "center", gap: "var(--space-3)", flexWrap: "wrap" }}>
          <span
            style={{
              fontSize: "var(--type-micro)",
              fontWeight: 700,
              padding: "var(--space-0-5) var(--space-2)",
              borderRadius: "var(--radius-sm)",
              background: style.bg,
              border: `1px solid ${style.border}`,
              color: style.color,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            {report.overall_verdict}
          </span>
          <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)" }}>Score {report.overall_score} / +5</span>
          {report.sade_sati_active && (
            <span style={{ fontSize: "var(--type-micro)", color: "var(--rose)", fontWeight: 600 }}>
              Sade Sati: {report.sade_sati_phase}
            </span>
          )}
          {report.double_transit_houses.length > 0 && (
            <span style={{ fontSize: "var(--type-micro)", color: "var(--gold-vivid)", fontWeight: 600 }}>
              Double Transit: House {report.double_transit_houses.join(", ")}
            </span>
          )}
        </div>
      </div>

      {/* ── Master Synthesis ── */}
      <div className="card" style={{ padding: "var(--space-4) var(--space-5)", background: "linear-gradient(135deg, var(--gold-dim) 0%, var(--bg-card) 100%)", border: "1px solid var(--gold-border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
          <Calendar size={16} color="var(--gold-vivid)" />
          <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", margin: 0 }}>Master's {report.period_label}</h4>
        </div>
        <div style={{ color: "var(--text-high)", lineHeight: 1.7, fontSize: "var(--type-small)", whiteSpace: "pre-wrap" }}>{report.master_synthesis}</div>
      </div>

      {/* ── Graha Results ── */}
      <div className="card" style={{ padding: "var(--space-4) var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", margin: 0 }}>Graha-wise Results from Chandra Lagna</h4>
          <span style={{ fontSize: "var(--type-label)", color: "var(--text-low)" }}>{report.graha_results.length} planets</span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--type-micro)" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border-subtle)" }}>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Graha</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Sign</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>House from Moon</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Degree</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Status</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Verdict</th>
              </tr>
            </thead>
            <tbody>
              {report.graha_results.map((g: GrahaResult, idx: number) => {
                const s = g.favourable ? VERDICT_STYLE.good : VERDICT_STYLE.challenging;
                return (
                  <tr key={idx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-high)", fontWeight: 600 }}>{g.planet}</td>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)" }}>{g.sign}</td>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)", fontFamily: "var(--font-mono)" }}>H{g.house_from_moon}</td>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)", fontFamily: "var(--font-mono)" }}>{g.degree_in_sign.toFixed(2)}°</td>
                    <td style={{ padding: "var(--space-1) var(--space-2)" }}>
                      <span
                        style={{
                          fontSize: "var(--type-label)",
                          fontWeight: 600,
                          padding: "1px 6px",
                          borderRadius: "var(--radius-sm)",
                          background: s.bg,
                          color: s.color,
                          border: `1px solid ${s.border}`,
                          textTransform: "uppercase",
                        }}
                      >
                        {g.favourable ? "Favourable" : "Testing"}
                      </span>
                    </td>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)" }}>{g.verdict}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Supportive & Watchful ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "var(--space-4)" }}>
        {favourable.length > 0 && (
          <div className="card" style={{ padding: "var(--space-4) var(--space-5)", borderLeft: "4px solid var(--emerald)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
              <Sun size={16} color="var(--emerald)" />
              <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--emerald)", textTransform: "uppercase", margin: 0 }}>Supportive Transits</h4>
            </div>
            <div style={{ color: "var(--text-mid)", fontSize: "var(--type-small)", lineHeight: 1.6 }}>
              {favourable.map((g) => `${g.planet} (House ${g.house_from_moon})`).join("; ")} — these areas flower this period.
            </div>
          </div>
        )}
        {challenging.length > 0 && (
          <div className="card" style={{ padding: "var(--space-4) var(--space-5)", borderLeft: "4px solid var(--rose)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
              <Sun size={16} color="var(--rose)" />
              <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--rose)", textTransform: "uppercase", margin: 0 }}>Watchful Transits</h4>
            </div>
            <div style={{ color: "var(--text-mid)", fontSize: "var(--type-small)", lineHeight: 1.6 }}>
              {challenging.map((g) => `${g.planet} (House ${g.house_from_moon})`).join("; ")} — exercise restraint here.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
