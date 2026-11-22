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
import { useLanguage } from "@/context/LanguageContext";

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
  const { t, lang, num, deg } = useLanguage();
  const [report, setReport] = useState<RashiFalReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState("daily");
  // The picker must show the date actually being read. It used to start
  // empty ("mm/dd/yyyy") while the header already showed the backend's
  // reference date, so initialise it to local today and keep it in sync
  // with the date the report was cast for.
  const todayStr = () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  };
  const [referenceDate, setReferenceDate] = useState(todayStr);

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
        if (!cancelled) {
          setReport(data);
          // Keep the picker on the date the report was actually cast for.
          // Same value is a no-op, so this cannot loop the effect.
          if (data.reference_date && data.reference_date !== referenceDate) {
            setReferenceDate(data.reference_date);
          }
        }
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
          <h3 style={{ color: "var(--rose)", fontSize: "var(--type-body)", fontWeight: 700 }}>{t.rashiFal.calculationError}</h3>
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
                {t.rashiFal.title} — {report.period_label}
              </h2>
            </div>
            <p style={{ fontSize: "var(--type-small)", color: "var(--text-mid)", marginTop: "var(--space-1)" }}>
              {t.rashiFal.chandraLagna}: {lang === "ne" ? (t.zodiac.signs[report.moon_sign as keyof typeof t.zodiac.signs] || report.moon_sign) : report.moon_sign} {report.moon_nakshatra ? `(${report.moon_nakshatra})` : ""}. {t.rashiFal.referenceDate}: {report.reference_date}.
            </p>
          </div>
          <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-1)" }}>
              <label style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textTransform: "uppercase" }}>{t.rashiFal.period}</label>
              <div style={{ display: "flex", gap: "var(--space-1)" }}>
                {PERIODS.map((p) => {
                  const label = p.id === "daily" ? t.rashiFal.periods.daily : p.id === "monthly" ? t.rashiFal.periods.monthly : p.id === "yearly" ? t.rashiFal.periods.yearly : p.label;
                  return (
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
                      {label}
                    </button>
                  );
                })}
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-1)" }}>
              <label style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textTransform: "uppercase" }}>{t.rashiFal.referenceDate}</label>
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
          <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)" }}>{lang === "ne" ? `अङ्क ${num(report.overall_score)} / +५` : `Score ${report.overall_score} / +5`}</span>
          {report.sade_sati_active && (
            <span style={{ fontSize: "var(--type-micro)", color: "var(--rose)", fontWeight: 600 }}>
              {t.rashiFal.sadeSati}: {report.sade_sati_phase}
            </span>
          )}
          {report.double_transit_houses.length > 0 && (
            <span style={{ fontSize: "var(--type-micro)", color: "var(--gold-vivid)", fontWeight: 600 }}>
              {t.rashiFal.doubleTransit}: {lang === "ne" ? `भाव ${report.double_transit_houses.map(num).join(", ")}` : `House ${report.double_transit_houses.join(", ")}`}
            </span>
          )}
        </div>
      </div>

      {/* ── Master Synthesis ── */}
      <div className="card" style={{ padding: "var(--space-4) var(--space-5)", background: "linear-gradient(135deg, var(--gold-dim) 0%, var(--bg-card) 100%)", border: "1px solid var(--gold-border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
          <Calendar size={16} color="var(--gold-vivid)" />
          <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", margin: 0 }}>{t.rashiFal.mastersSynthesis}</h4>
        </div>
        <div style={{ color: "var(--text-high)", lineHeight: 1.7, fontSize: "var(--type-small)", whiteSpace: "pre-wrap" }}>{report.master_synthesis}</div>
      </div>

      {/* ── Graha Results ── */}
      <div className="card" style={{ padding: "var(--space-4) var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", margin: 0 }}>{t.rashiFal.grahaResults}</h4>
          <span style={{ fontSize: "var(--type-label)", color: "var(--text-low)" }}>{num(report.graha_results.length)} {lang === "ne" ? "ग्रहहरू" : "planets"}</span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--type-micro)" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border-subtle)" }}>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>{lang === "ne" ? "ग्रह" : "Graha"}</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>{lang === "ne" ? "राशि" : "Sign"}</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>{lang === "ne" ? "चन्द्रबाट भाव" : "House from Moon"}</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>{lang === "ne" ? "अंश" : "Degree"}</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>{lang === "ne" ? "स्थिति" : "Status"}</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>{lang === "ne" ? "फल/निर्णय" : "Verdict"}</th>
              </tr>
            </thead>
            <tbody>
              {report.graha_results.map((g: GrahaResult, idx: number) => {
                // Badge on the verdict class, not a binary favourable flag:
                // "Mixed" is not "Testing", and "Difficult" is worse than
                // "Challenging". Fall back to the old binary mapping for
                // payloads from before verdict_key existed.
                const s =
                  VERDICT_STYLE[g.verdict_key] ??
                  (g.favourable ? VERDICT_STYLE.good : VERDICT_STYLE.challenging);
                const statusLabel =
                  g.verdict_key === "excellent" || g.verdict_key === "good"
                    ? t.rashiFal.statusFavourable
                    : g.verdict_key === "mixed"
                      ? t.rashiFal.statusMixed
                      : g.verdict_key === "difficult"
                        ? t.rashiFal.statusDifficult
                        : t.rashiFal.statusChallenging;
                return (
                  <tr key={idx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-high)", fontWeight: 600 }}>
                      {lang === "ne" ? (t.planets.names[g.planet as keyof typeof t.planets.names] || g.planet) : g.planet}
                    </td>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)" }}>
                      {lang === "ne" ? (t.zodiac.signs[g.sign as keyof typeof t.zodiac.signs] || g.sign) : g.sign}
                    </td>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)", fontFamily: "var(--font-mono)" }}>
                      {lang === "ne" ? `भाव ${num(g.house_from_moon)}` : `H${g.house_from_moon}`}
                    </td>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)", fontFamily: "var(--font-mono)" }}>
                      {deg(g.degree_in_sign)}
                    </td>
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
                        {statusLabel}
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
              <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--emerald)", textTransform: "uppercase", margin: 0 }}>
                {t.rashiFal.supportiveTransits}
              </h4>
            </div>
            <div style={{ color: "var(--text-mid)", fontSize: "var(--type-small)", lineHeight: 1.6 }}>
              {favourable
                .map((g) => `${lang === "ne" ? (t.planets.names[g.planet as keyof typeof t.planets.names] || g.planet) : g.planet} (${lang === "ne" ? "भाव" : "House"} ${num(g.house_from_moon)})`)
                .join("; ")}{" "}
              — {lang === "ne" ? "यस अवधिमा यी क्षेत्रहरू उन्नतिशील रहनेछन्।" : "these areas flower this period."}
            </div>
          </div>
        )}
        {challenging.length > 0 && (
          <div className="card" style={{ padding: "var(--space-4) var(--space-5)", borderLeft: "4px solid var(--rose)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
              <Sun size={16} color="var(--rose)" />
              <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--rose)", textTransform: "uppercase", margin: 0 }}>
                {t.rashiFal.watchfulTransits}
              </h4>
            </div>
            <div style={{ color: "var(--text-mid)", fontSize: "var(--type-small)", lineHeight: 1.6 }}>
              {challenging
                .map((g) => `${lang === "ne" ? (t.planets.names[g.planet as keyof typeof t.planets.names] || g.planet) : g.planet} (${lang === "ne" ? "भाव" : "House"} ${num(g.house_from_moon)})`)
                .join("; ")}{" "}
              — {lang === "ne" ? "यी क्षेत्रहरूमा संयमता र सतर्कता अपनाउनुहोस्।" : "exercise restraint here."}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
