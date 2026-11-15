"use client";

import React, { useEffect, useState } from "react";
import { Sun, Award, ShieldAlert, Layers, Clock } from "lucide-react";
import {
  BirthDataInput,
  SahamInfo,
  MonthPrediction,
  VarshaphalReport,
  VarshaphalInput,
} from "@/lib/types";
import { fetchVarshaphal } from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";

interface Props {
  birth?: BirthDataInput;
}

const CURRENT_YEAR = new Date().getFullYear();

const DIGNITY_COLOR: Record<string, string> = {
  exalted: "var(--emerald)",
  own_sign: "var(--cyan-vivid)",
  neutral: "var(--text-mid)",
  debilitated: "var(--rose)",
};

export const VarshaphalView: React.FC<Props> = ({ birth }: Props) => {
  const { t, lang, num } = useLanguage();
  const [report, setReport] = useState<VarshaphalReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [targetYear, setTargetYear] = useState(CURRENT_YEAR);

  useEffect(() => {
    if (!birth) {
      setReport(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);

    const payload: VarshaphalInput = {
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
      target_year: targetYear,
      ayanamsa: birth.ayanamsa || "jhora_lahiri",
      house_system: birth.house_system || "WholeSign",
    };

    fetchVarshaphal(payload)
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
  }, [birth, targetYear]);

  if (!birth) {
    return (
      <div style={{ maxWidth: "var(--size-container)", margin: "0 auto", width: "100%" }}>
        <div className="card" style={{ padding: "var(--space-8)", textAlign: "center" }}>
          <Sun size={32} color="var(--gold-vivid)" style={{ margin: "0 auto var(--space-3)" }} />
          <h3 style={{ fontSize: "var(--type-heading)", color: "var(--gold-vivid)", marginBottom: "var(--space-1)" }}>
            Varshaphal (Barsha Fal) - Annual Horoscope
          </h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>
            Enter your birth parameters to compute the Tajik solar-return chart, Muntha, Year Lord, Sahams and month-wise forecast.
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
            Casting Solar Return Chart...
          </h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>
            Locating the exact moment the transiting Sun returns to its natal longitude.
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
          <h3 style={{ color: "var(--rose)", fontSize: "var(--type-body)", fontWeight: 700 }}>{t.varshaphal.calculationError}</h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>{error || "Unable to compute annual horoscope."}</p>
        </div>
      </div>
    );
  }

  const m = report.muntha;
  const v = report.varsheshwara;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)", maxWidth: "var(--size-container-lg)", margin: "0 auto", width: "100%" }}>
      <div className="card" style={{ padding: "var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-3)" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <Sun size={24} color="var(--gold-vivid)" />
              <h2 style={{ fontSize: "var(--type-title)", fontWeight: 700, color: "var(--text-high)" }}>
                {t.varshaphal.title} - {num(report.target_year)}
              </h2>
            </div>
            <p style={{ fontSize: "var(--type-small)", color: "var(--text-mid)", marginTop: "var(--space-1)" }}>
              {t.varshaphal.subtitle}. {lang === "ne" ? `उमेर ${num(report.completed_years)}` : `Age ${report.completed_years}`}.
            </p>
            <div style={{ marginTop: "var(--space-3)", fontSize: "var(--type-micro)", color: "var(--text-low)", fontFamily: "var(--font-mono)" }}>
              {t.varshaphal.solarReturn} (local): {report.solar_return_local} • UTC: {report.solar_return_utc}
            </div>
          </div>
          <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "flex-start" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-1)" }}>
              <label style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textTransform: "uppercase" }}>{t.varshaphal.targetYear}</label>
              <input
                type="number"
                min="1"
                max="3000"
                value={targetYear}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTargetYear(parseInt(e.target.value, 10) || CURRENT_YEAR)}
                style={{ width: "90px", padding: "6px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)", background: "var(--bg-input)", color: "var(--text-high)", fontSize: "var(--type-small)" }}
              />
            </div>
          </div>
        </div>
        <div style={{ marginTop: "var(--space-4)", padding: "var(--space-3) var(--space-4)", background: "var(--gold-dim)", border: "1px solid var(--gold-border)", borderRadius: "var(--radius-md)", display: "flex", alignItems: "center", gap: "var(--space-3)", flexWrap: "wrap" }}>
          <Award size={16} color="var(--gold-vivid)" />
          <div style={{ fontSize: "var(--type-small)", color: "var(--text-high)" }}>
            <strong style={{ color: "var(--gold-vivid)" }}>{t.varshaphal.varsheshwara}:</strong> <span style={{ color: "var(--text-mid)", fontWeight: 600 }}>{lang === "ne" ? (t.planets.names[v.planet as keyof typeof t.planets.names] || v.planet) : v.planet}</span>
          </div>
          <div style={{ fontSize: "var(--type-small)", color: "var(--text-high)" }}>
            <strong style={{ color: "var(--cyan-vivid)" }}>{t.varshaphal.muntha}:</strong> <span style={{ color: "var(--text-mid)", fontWeight: 600 }}>{lang === "ne" ? (t.zodiac.signs[m.sign as keyof typeof t.zodiac.signs] || m.sign) : m.sign} ({lang === "ne" ? `भाव ${num(m.house)}` : `House ${m.house}`})</span>
          </div>
          <div style={{ fontSize: "var(--type-small)", color: "var(--text-high)" }}>
            <strong style={{ color: "var(--cyan-vivid)" }}>{t.varshaphal.munthaLord}:</strong> <span style={{ color: "var(--text-mid)", fontWeight: 600 }}>{lang === "ne" ? (t.planets.names[m.lord as keyof typeof t.planets.names] || m.lord) : m.lord}</span>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--space-4)" }}>
        <div className="card" style={{ padding: "var(--space-4) var(--space-5)", borderLeft: "4px solid var(--graha-mercury, #059669)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
            <Award size={16} color="var(--gold-vivid)" />
            <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase" }}>{t.varshaphal.yearLordTitle}</h4>
          </div>
          <div style={{ fontSize: "var(--type-small)", color: "var(--text-mid)", marginBottom: "var(--space-2)" }}>{v.rationale}</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)", fontSize: "var(--type-micro)" }}>
            <div style={{ background: "var(--bg-subtle)", padding: "var(--space-1) var(--space-2)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <span style={{ color: "var(--text-low)", display: "block", textTransform: "uppercase", fontSize: "var(--type-label)" }}>{t.transits.tablePlanet}</span>
              <span style={{ color: "var(--text-high)", fontWeight: 600 }}>{lang === "ne" ? (t.planets.names[v.planet as keyof typeof t.planets.names] || v.planet) : v.planet}</span>
            </div>
            <div style={{ background: "var(--bg-subtle)", padding: "var(--space-1) var(--space-2)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <span style={{ color: "var(--text-low)", display: "block", textTransform: "uppercase", fontSize: "var(--type-label)" }}>{t.varshaphal.dignity}</span>
              <span style={{ color: DIGNITY_COLOR[v.dignity] || "var(--text-mid)", fontWeight: 600 }}>{v.dignity}</span>
            </div>
            <div style={{ background: "var(--bg-subtle)", padding: "var(--space-1) var(--space-2)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <span style={{ color: "var(--text-low)", display: "block", textTransform: "uppercase", fontSize: "var(--type-label)" }}>{t.common.sign}</span>
              <span style={{ color: "var(--text-high)" }}>{lang === "ne" ? (t.zodiac.signs[v.sign as keyof typeof t.zodiac.signs] || v.sign) : v.sign}</span>
            </div>
            <div style={{ background: "var(--bg-subtle)", padding: "var(--space-1) var(--space-2)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <span style={{ color: "var(--text-low)", display: "block", textTransform: "uppercase", fontSize: "var(--type-label)" }}>{t.common.house}</span>
              <span style={{ color: "var(--text-high)", fontWeight: 600 }}>{num(v.house)}</span>
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: "var(--space-4) var(--space-5)", borderLeft: "4px solid var(--graha-moon, #0f766e)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
            <Layers size={16} color="var(--cyan-vivid)" />
            <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--cyan-vivid)", textTransform: "uppercase" }}>{t.varshaphal.munthaTitle}</h4>
          </div>
          <div style={{ fontSize: "var(--type-small)", color: "var(--text-mid)", marginBottom: "var(--space-2)" }}>
            {t.varshaphal.munthaDesc} <strong>{num(m.completed_years)}</strong>.
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)", fontSize: "var(--type-micro)" }}>
            <div style={{ background: "var(--bg-subtle)", padding: "var(--space-1) var(--space-2)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <span style={{ color: "var(--text-low)", display: "block", textTransform: "uppercase", fontSize: "var(--type-label)" }}>{t.common.sign}</span>
              <span style={{ color: "var(--text-high)", fontWeight: 600 }}>{lang === "ne" ? (t.zodiac.signs[m.sign as keyof typeof t.zodiac.signs] || m.sign) : m.sign}</span>
            </div>
            <div style={{ background: "var(--bg-subtle)", padding: "var(--space-1) var(--space-2)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <span style={{ color: "var(--text-low)", display: "block", textTransform: "uppercase", fontSize: "var(--type-label)" }}>{t.varshaphal.degreeInSign}</span>
              <span style={{ color: "var(--text-high)" }}>{num(m.degree_in_sign.toFixed(2))}°</span>
            </div>
            <div style={{ background: "var(--bg-subtle)", padding: "var(--space-1) var(--space-2)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <span style={{ color: "var(--text-low)", display: "block", textTransform: "uppercase", fontSize: "var(--type-label)" }}>{t.common.house}</span>
              <span style={{ color: "var(--text-high)", fontWeight: 600 }}>{num(m.house)}</span>
            </div>
            <div style={{ background: "var(--bg-subtle)", padding: "var(--space-1) var(--space-2)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
              <span style={{ color: "var(--text-low)", display: "block", textTransform: "uppercase", fontSize: "var(--type-label)" }}>{t.common.lord}</span>
              <span style={{ color: "var(--text-high)", fontWeight: 600 }}>{lang === "ne" ? (t.planets.names[m.lord as keyof typeof t.planets.names] || m.lord) : m.lord}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="card" style={{ padding: "var(--space-4) var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase" }}>{t.varshaphal.sahams}</h4>
          <span style={{ fontSize: "var(--type-label)", color: "var(--text-low)" }}>{num(report.sahams.length)} {lang === "ne" ? "सहमहरू" : "calculated"}</span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "var(--space-2)" }}>
          {report.sahams.map((s: SahamInfo, idx: number) => (
            <div
              key={idx}
              style={{ background: "var(--bg-subtle)", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)", fontSize: "var(--type-micro)" }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 600, color: "var(--gold-vivid)", marginBottom: "var(--space-0-5)" }}>
                <span>{s.name}</span>
                <span>{lang === "ne" ? (t.zodiac.signs[s.sign as keyof typeof t.zodiac.signs] || s.sign) : s.sign}</span>
              </div>
              <div style={{ color: "var(--text-mid)", fontSize: "var(--type-label)" }}>{num(s.degree_in_sign.toFixed(2))}° • {lang === "ne" ? `भाव ${num(s.house)}` : `House ${s.house}`}</div>
              <div style={{ color: "var(--text-low)", fontSize: "var(--type-label)", marginTop: "var(--space-0-5)" }}>{s.formula}</div>
              <div style={{ color: "var(--text-mid)", fontSize: "var(--type-label)", marginTop: "var(--space-0-5)", fontStyle: "italic" }}>{s.meaning}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ padding: "var(--space-4) var(--space-5)" }}>
        <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", marginBottom: "var(--space-3)" }}>{t.varshaphal.monthLords}</h4>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "var(--space-2)" }}>
          {report.month_lords.map((mo: MonthPrediction, idx: number) => (
            <div
              key={idx}
              style={{ background: "var(--bg-subtle)", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)", fontSize: "var(--type-micro)" }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 600, color: "var(--cyan-vivid)", marginBottom: "var(--space-0-5)" }}>
                <span>{lang === "ne" ? `महिना ${num(mo.month)}` : `Month ${mo.month}`}</span>
                <span>{mo.weekday}</span>
              </div>
              <div style={{ color: "var(--text-high)", fontWeight: 600 }}>{lang === "ne" ? (t.planets.names[mo.lord as keyof typeof t.planets.names] || mo.lord) : mo.lord}</div>
              <div style={{ color: "var(--text-mid)", fontSize: "var(--type-label)", marginTop: "var(--space-0-5)" }}>{mo.theme}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ padding: "var(--space-4) var(--space-5)", background: "linear-gradient(135deg, var(--gold-dim) 0%, var(--bg-card) 100%)", border: "1px solid var(--gold-border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
          <Clock size={16} color="var(--gold-vivid)" />
          <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase" }}>{t.varshaphal.annualReading}</h4>
        </div>
        <div style={{ color: "var(--text-high)", lineHeight: 1.7, fontSize: "var(--type-small)", whiteSpace: "pre-wrap" }}>{report.summary}</div>
      </div>

      <div className="card" style={{ padding: "var(--space-4) var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase" }}>{t.varshaphal.chartSnapshot}</h4>
          <span style={{ fontSize: "var(--type-label)", color: "var(--text-low)" }}>{report.varshaphal_chart.ascendant} Asc</span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: "var(--space-1)", fontSize: "var(--type-label)" }}>
          {report.varshaphal_chart.planets.map((p, idx) => (
            <div
              key={idx}
              style={{ background: "var(--bg-subtle)", padding: "var(--space-1) var(--space-2)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)", display: "flex", justifyContent: "space-between", alignItems: "center" }}
            >
              <span style={{ color: "var(--text-mid)", fontSize: "var(--type-micro)" }}>{p.name}</span>
              <span style={{ color: "var(--text-high)", fontWeight: 600 }}>{p.sign} {p.degree.toFixed(1)}°</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
