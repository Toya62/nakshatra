"use client";

import React, { useState } from "react";
import {
  Heart,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Copy,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { BirthDataInput, CompatibilityReport } from "@/lib/types";
import { fetchCompatibility } from "@/lib/api";
import { DEFAULT_LOCATION } from "@/config/defaults";
import { useLanguage } from "@/context/LanguageContext";
import { getRandomBirthData } from "@/lib/randomBirth";

interface Props {
  defaultBride?: BirthDataInput;
  defaultGroom?: BirthDataInput;
}

export const CompatibilityView: React.FC<Props> = ({ defaultBride, defaultGroom }) => {
  const { t, lang, num } = useLanguage();
  const [brideData, setBrideData] = useState<BirthDataInput>(() =>
    defaultBride || getRandomBirthData()
  );

  const [groomData, setGroomData] = useState<BirthDataInput>(() =>
    defaultGroom || getRandomBirthData(brideData.place_name)
  );

  const [brideName, setBrideName] = useState("Bride");
  const [groomName, setGroomName] = useState("Groom");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<CompatibilityReport | null>(null);
  const [copied, setCopied] = useState(false);
  const [showExtended, setShowExtended] = useState(false);

  const handleCalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetchCompatibility(brideData, groomData, brideName, groomName);
      setReport(res);
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!report) return;
    const txt = `
VEDIC ASHTAKOOTA MATCH REPORT: ${report.bride_name} & ${report.groom_name}
Score: ${report.ashtakoota.total_score} / 36 (${report.ashtakoota.percentage}%) - ${report.ashtakoota.verdict}
Kuja Dosha: ${report.kuja_dosha.verdict}
Recommendation: ${report.recommendation}
    `.trim();
    navigator.clipboard.writeText(txt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
      {/* Header Banner */}
      <div className="card" style={{ padding: "var(--space-6) var(--space-6)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", marginBottom: "var(--space-2)" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "var(--radius-md)",
              background: "linear-gradient(135deg, var(--gold-vivid) 0%, var(--rose) 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Heart size={20} color="#ffffff" />
          </div>
          <h2 className="title-serif gold-gradient-text" style={{ fontSize: "var(--type-title)", fontWeight: 700 }}>
            {t.compatibility.title}
          </h2>
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: "var(--type-small)", maxWidth: "860px", lineHeight: 1.5 }}>
          {t.compatibility.subtitle}
        </p>
      </div>

      {/* Input Form Cards */}
      <form onSubmit={handleCalculate} style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 340px), 1fr))", gap: "var(--space-5)" }}>
          {/* Bride Card */}
          <div className="card" style={{ padding: "var(--space-5)" }}>
            <h3 style={{ fontSize: "var(--type-heading)", color: "var(--rose)", fontWeight: 700, marginBottom: "var(--space-3-5)", display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <span>{t.compatibility.bride}</span>
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-3)" }}>
              <div style={{ gridColumn: "span 2" }}>
                <label style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-1)" }}>
                  {lang === "ne" ? "नाम" : "Name"}
                </label>
                <input
                  type="text"
                  value={brideName}
                  onChange={(e) => setBrideName(e.target.value)}
                  style={{ width: "100%", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", fontSize: "var(--type-small)" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-1)" }}>
                  {t.birthForm.dob}
                </label>
                <input
                  type="date"
                  value={`${brideData.year}-${String(brideData.month).padStart(2, "0")}-${String(brideData.day).padStart(2, "0")}`}
                  onChange={(e) => {
                    const [y, m, d] = e.target.value.split("-").map(Number);
                    if (y && m && d) setBrideData({ ...brideData, year: y, month: m, day: d });
                  }}
                  style={{ width: "100%", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", fontSize: "var(--type-small)" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-1)" }}>
                  {t.birthForm.tob}
                </label>
                <input
                  type="time"
                  step="1"
                  value={`${String(brideData.hour).padStart(2, "0")}:${String(brideData.minute).padStart(2, "0")}:${String(brideData.second ?? 0).padStart(2, "0")}`}
                  onChange={(e) => {
                    const parts = e.target.value.split(":").map(Number);
                    setBrideData({ ...brideData, hour: parts[0] || 0, minute: parts[1] || 0, second: parts[2] || 0 });
                  }}
                  style={{ width: "100%", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", fontSize: "var(--type-small)" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-1)" }}>
                  {t.birthForm.latitude}
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={brideData.latitude}
                  onChange={(e) => setBrideData({ ...brideData, latitude: parseFloat(e.target.value) || 0 })}
                  style={{ width: "100%", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", fontSize: "var(--type-small)" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-1)" }}>
                  {t.birthForm.longitude}
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={brideData.longitude}
                  onChange={(e) => setBrideData({ ...brideData, longitude: parseFloat(e.target.value) || 0 })}
                  style={{ width: "100%", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", fontSize: "var(--type-small)" }}
                />
              </div>
              <div style={{ gridColumn: "span 2" }}>
                <label style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-1)" }}>
                  {t.birthForm.timezone}
                </label>
                <input
                  type="text"
                  value={brideData.timezone}
                  onChange={(e) => setBrideData({ ...brideData, timezone: e.target.value })}
                  style={{ width: "100%", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", fontSize: "var(--type-small)" }}
                />
              </div>
            </div>
          </div>

          {/* Groom Card */}
          <div className="card" style={{ padding: "var(--space-5)" }}>
            <h3 style={{ fontSize: "var(--type-heading)", color: "var(--cyan-vivid)", fontWeight: 700, marginBottom: "var(--space-3-5)", display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <span>{t.compatibility.groom}</span>
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-3)" }}>
              <div style={{ gridColumn: "span 2" }}>
                <label style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-1)" }}>
                  {lang === "ne" ? "नाम" : "Name"}
                </label>
                <input
                  type="text"
                  value={groomName}
                  onChange={(e) => setGroomName(e.target.value)}
                  style={{ width: "100%", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", fontSize: "var(--type-small)" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-1)" }}>
                  {t.birthForm.dob}
                </label>
                <input
                  type="date"
                  value={`${groomData.year}-${String(groomData.month).padStart(2, "0")}-${String(groomData.day).padStart(2, "0")}`}
                  onChange={(e) => {
                    const [y, m, d] = e.target.value.split("-").map(Number);
                    if (y && m && d) setGroomData({ ...groomData, year: y, month: m, day: d });
                  }}
                  style={{ width: "100%", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", fontSize: "var(--type-small)" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-1)" }}>
                  {t.birthForm.tob}
                </label>
                <input
                  type="time"
                  step="1"
                  value={`${String(groomData.hour).padStart(2, "0")}:${String(groomData.minute).padStart(2, "0")}:${String(groomData.second ?? 0).padStart(2, "0")}`}
                  onChange={(e) => {
                    const parts = e.target.value.split(":").map(Number);
                    setGroomData({ ...groomData, hour: parts[0] || 0, minute: parts[1] || 0, second: parts[2] || 0 });
                  }}
                  style={{ width: "100%", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", fontSize: "var(--type-small)" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-1)" }}>
                  {t.birthForm.latitude}
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={groomData.latitude}
                  onChange={(e) => setGroomData({ ...groomData, latitude: parseFloat(e.target.value) || 0 })}
                  style={{ width: "100%", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", fontSize: "var(--type-small)" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-1)" }}>
                  {t.birthForm.longitude}
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={groomData.longitude}
                  onChange={(e) => setGroomData({ ...groomData, longitude: parseFloat(e.target.value) || 0 })}
                  style={{ width: "100%", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", fontSize: "var(--type-small)" }}
                />
              </div>
              <div style={{ gridColumn: "span 2" }}>
                <label style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-1)" }}>
                  {t.birthForm.timezone}
                </label>
                <input
                  type="text"
                  value={groomData.timezone}
                  onChange={(e) => setGroomData({ ...groomData, timezone: e.target.value })}
                  style={{ width: "100%", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", fontSize: "var(--type-small)" }}
                />
              </div>
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-primary"
          style={{
            padding: "var(--space-3-5) var(--space-6)",
            fontSize: "var(--type-data)",
            fontWeight: 700,
            cursor: loading ? "wait" : "pointer",
            borderRadius: "var(--radius-md)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "var(--space-2-5)",
          }}
        >
          <Heart size={18} aria-hidden="true" />
          {loading ? (lang === "ne" ? "गणना गरिँदैछ..." : "Calculating Match...") : (lang === "ne" ? "अष्टकूट गुण मिलान गणना गर्नुहोस्" : "Calculate Ashtakoota Match")}
        </button>
      </form>

      {/* Empty state — what the report will contain once both charts are
          cast. No score is shown or implied before calculation. */}
      {!report && !loading && !error && (
        <div className="card" style={{ padding: "var(--space-5)" }}>
          <h3 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", marginBottom: "var(--space-2)" }}>
            {t.compatibility.emptyTitle}
          </h3>
          <p style={{ fontSize: "var(--type-small)", color: "var(--text-mid)", lineHeight: 1.6, marginBottom: "var(--space-3)" }}>
            {t.compatibility.emptyDesc}
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "var(--space-2)" }}>
            {Object.values(t.compatibility.kootas).map((label) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", fontSize: "var(--type-small)", color: "var(--text-high)" }}>
                <Heart size={12} color="var(--gold-vivid)" aria-hidden="true" />
                {label}
              </div>
            ))}
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", fontSize: "var(--type-small)", color: "var(--text-high)" }}>
              <Heart size={12} color="var(--gold-vivid)" aria-hidden="true" />
              {t.compatibility.manglikCheck}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", fontSize: "var(--type-small)", color: "var(--text-high)" }}>
              <Heart size={12} color="var(--gold-vivid)" aria-hidden="true" />
              {t.compatibility.verdictTitle}
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="card" style={{ padding: "var(--space-4)", color: "var(--accent-rose)", borderColor: "var(--accent-rose)" }}>
          {error}
        </div>
      )}

      {/* Results Dashboard */}
      {report && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
          {/* Main Score Banner */}
          <div
            className="card"
            style={{
              padding: "var(--space-6) var(--space-6)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "var(--space-5)",
              border: `1px solid ${
                report.ashtakoota.verdict === "Uttama"
                  ? "rgba(229, 185, 76, 0.6)"
                  : report.ashtakoota.verdict === "Madhyama"
                  ? "rgba(56, 189, 248, 0.6)"
                  : "rgba(244, 63, 94, 0.6)"
              }`,
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", marginBottom: "var(--space-1-5)" }}>
                <span
                  style={{
                    fontSize: "var(--type-display)",
                    fontWeight: 900,
                    color:
                      report.ashtakoota.verdict === "Uttama"
                        ? "var(--gold-vivid)"
                        : report.ashtakoota.verdict === "Madhyama"
                        ? "var(--cyan-vivid)"
                        : "var(--rose)",
                  }}
                >
                  {num(report.ashtakoota.total_score)}
                </span>
                <span style={{ fontSize: "var(--type-section)", color: "var(--text-muted)", fontWeight: 600 }}>
                  / {num(36.0)} {lang === "ne" ? "गुण" : "Gunas"}
                </span>
                <span
                  className={`badge ${
                    report.ashtakoota.verdict === "Uttama"
                      ? "badge-gold"
                      : report.ashtakoota.verdict === "Madhyama"
                      ? "badge-cyan"
                      : "badge-rose"
                  }`}
                  style={{ fontSize: "var(--type-small)", padding: "var(--space-1) var(--space-3)" }}
                >
                  {lang === "ne"
                    ? (report.ashtakoota.verdict === "Uttama" ? "उत्तम" : report.ashtakoota.verdict === "Madhyama" ? "मध्यम" : "अधम")
                    : report.ashtakoota.verdict} ({num(report.ashtakoota.percentage)}%)
                </span>
              </div>
              <p style={{ color: "var(--text-bright)", fontSize: "var(--type-data)", fontWeight: 500 }}>
                {report.ashtakoota.summary}
              </p>
            </div>

            <div style={{ display: "flex", gap: "var(--space-2-5)" }}>
              <button
                onClick={handleCopy}
                className="btn-secondary"
                style={{ fontSize: "var(--type-small)" }}
              >
                <Copy size={14} />
                {copied ? (lang === "ne" ? "कपी भयो!" : "Copied!") : (lang === "ne" ? "विवरण कपी" : "Copy Report")}
              </button>
            </div>
          </div>

          {/* Couple Moon Sign / Nakshatra Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 280px), 1fr))", gap: "var(--space-4-5)" }}>
            <div className="card" style={{ padding: "var(--space-4-5)" }}>
              <h4 style={{ color: "var(--rose)", fontSize: "var(--type-data)", fontWeight: 700, marginBottom: "var(--space-2)" }}>
                {report.bride_name} ({t.compatibility.bride})
              </h4>
              <p style={{ fontSize: "var(--type-small)", color: "var(--text-bright)" }}>
                {lang === "ne" ? "चन्द्र राशि:" : "Moon in"} <strong>{lang === "ne" ? (t.zodiac.signs[report.bride_moon_sign as keyof typeof t.zodiac.signs] || report.bride_moon_sign) : report.bride_moon_sign}</strong> | {lang === "ne" ? "नक्षत्र:" : "Nakshatra:"} <strong>{report.bride_nakshatra}</strong> ({lang === "ne" ? "पाद" : "Pada"} {num(report.bride_pada)})
              </p>
            </div>

            <div className="card" style={{ padding: "var(--space-4-5)" }}>
              <h4 style={{ color: "var(--cyan-vivid)", fontSize: "var(--type-data)", fontWeight: 700, marginBottom: "var(--space-2)" }}>
                {report.groom_name} ({t.compatibility.groom})
              </h4>
              <p style={{ fontSize: "var(--type-small)", color: "var(--text-bright)" }}>
                {lang === "ne" ? "चन्द्र राशि:" : "Moon in"} <strong>{lang === "ne" ? (t.zodiac.signs[report.groom_moon_sign as keyof typeof t.zodiac.signs] || report.groom_moon_sign) : report.groom_moon_sign}</strong> | {lang === "ne" ? "नक्षत्र:" : "Nakshatra:"} <strong>{report.groom_nakshatra}</strong> ({lang === "ne" ? "पाद" : "Pada"} {num(report.groom_pada)})
              </p>
            </div>
          </div>

          {/* 8 Ashtakoota Breakdown Table */}
          <div className="card" style={{ padding: "var(--space-5)" }}>
            <h3 style={{ fontSize: "var(--type-heading)", fontWeight: 700, marginBottom: "var(--space-4)", color: "var(--text-bright)" }}>
              {t.compatibility.ashtakootaMilan}
            </h3>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--type-small)" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)", textAlign: "left", color: "var(--text-muted)" }}>
                    <th style={{ padding: "var(--space-2-5) var(--space-3)" }}>{lang === "ne" ? "कूट" : "Koota"}</th>
                    <th style={{ padding: "var(--space-2-5) var(--space-3)" }}>{lang === "ne" ? "प्राप्ताङ्क" : "Points"}</th>
                    <th style={{ padding: "var(--space-2-5) var(--space-3)" }}>{lang === "ne" ? "वधू मान" : "Bride Value"}</th>
                    <th style={{ padding: "var(--space-2-5) var(--space-3)" }}>{lang === "ne" ? "वर मान" : "Groom Value"}</th>
                    <th style={{ padding: "var(--space-2-5) var(--space-3)" }}>{lang === "ne" ? "स्थिति" : "Status"}</th>
                    <th style={{ padding: "var(--space-2-5) var(--space-3)" }}>{lang === "ne" ? "व्याख्या" : "Analysis"}</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    report.ashtakoota.varna,
                    report.ashtakoota.vashya,
                    report.ashtakoota.tara,
                    report.ashtakoota.yoni,
                    report.ashtakoota.graha_maitri,
                    report.ashtakoota.gana,
                    report.ashtakoota.bhakoot,
                    report.ashtakoota.nadi,
                  ].map((k) => (
                    <tr key={k.name} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                      <td style={{ padding: "var(--space-3)", fontWeight: 600, color: "var(--text-bright)" }}>{k.name}</td>
                      <td style={{ padding: "var(--space-3)" }}>
                        <span style={{ fontWeight: 700, color: k.obtained_score > 0 ? "var(--gold-vivid)" : "var(--rose)" }}>
                          {num(k.obtained_score)}
                        </span>
                        <span style={{ color: "var(--text-dim)", fontSize: "var(--type-micro)" }}> / {num(k.max_score)}</span>
                      </td>
                      <td style={{ padding: "var(--space-3)", color: "var(--rose)", fontWeight: 500 }}>{k.bride_val}</td>
                      <td style={{ padding: "var(--space-3)", color: "var(--cyan-vivid)", fontWeight: 500 }}>{k.groom_val}</td>
                      <td style={{ padding: "var(--space-3)" }}>
                        {k.is_favorable ? (
                          <span className="badge badge-emerald" style={{ gap: "var(--space-1)" }}>
                            <CheckCircle2 size={12} /> {lang === "ne" ? "शुभ (पास)" : "Pass"}
                          </span>
                        ) : k.cancelled ? (
                          <span className="badge badge-gold" style={{ gap: "var(--space-1)" }}>
                            <ShieldCheck size={12} /> {lang === "ne" ? "दोष परिहार" : "Cancelled"}
                          </span>
                        ) : (
                          <span className="badge badge-rose" style={{ gap: "var(--space-1)" }}>
                            <XCircle size={12} /> {lang === "ne" ? "दोषयुक्त" : "Afflicted"}
                          </span>
                        )}
                      </td>
                      <td style={{ padding: "var(--space-3)", color: "var(--text-muted)", fontSize: "var(--type-micro)" }}>{k.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Kuja Dosha (Manglik) Analysis */}
          <div className="card" style={{ padding: "var(--space-6)" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "var(--space-3-5)" }}>
              <h3 style={{ fontSize: "var(--type-heading)", fontWeight: 700, color: "var(--text-bright)", display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                <ShieldCheck size={18} color="var(--gold-vivid)" />
                <span>{t.compatibility.manglikCheck}</span>
              </h3>
              <span
                className={`badge ${
                  report.kuja_dosha.is_compatible ? "badge-emerald" : "badge-rose"
                }`}
                style={{ fontSize: "var(--type-small)", padding: "var(--space-1) var(--space-3)" }}
              >
                {report.kuja_dosha.verdict}
              </span>
            </div>
            <p style={{ color: "var(--text-muted)", fontSize: "var(--type-small)", marginBottom: "var(--space-4)" }}>
              {report.kuja_dosha.notes}
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 280px), 1fr))", gap: "var(--space-4)" }}>
              <div style={{ padding: "var(--space-3-5)", borderRadius: "var(--radius-md)", background: "var(--rose-dim)", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontWeight: 600, color: "var(--rose)", marginBottom: "var(--space-1)" }}>
                  {lang === "ne" ? "वधू माङ्गलिक विचार" : "Bride Kuja Dosha"}
                </div>
                <div style={{ fontSize: "var(--type-small)", color: "var(--text-bright)" }}>
                  {lang === "ne" ? "तीव्रता:" : "Severity:"} <strong>{report.kuja_dosha.bride.severity}</strong> ({lang === "ne" ? "परिहार:" : "Cancelled:"} {report.kuja_dosha.bride.is_cancelled ? (lang === "ne" ? "भएको" : "Yes") : (lang === "ne" ? "नभएको" : "No")})
                </div>
                {report.kuja_dosha.bride.cancellations.length > 0 && (
                  <div style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", marginTop: "var(--space-1-5)" }}>
                    {lang === "ne" ? "परिहार सूत्र:" : "Cancellations:"} {report.kuja_dosha.bride.cancellations.join(", ")}
                  </div>
                )}
              </div>

              <div style={{ padding: "var(--space-3-5)", borderRadius: "var(--radius-md)", background: "var(--cyan-dim)", border: "1px solid var(--cyan-border)" }}>
                <div style={{ fontWeight: 600, color: "var(--cyan-vivid)", marginBottom: "var(--space-1)" }}>
                  {lang === "ne" ? "वर माङ्गलिक विचार" : "Groom Kuja Dosha"}
                </div>
                <div style={{ fontSize: "var(--type-small)", color: "var(--text-bright)" }}>
                  {lang === "ne" ? "तीव्रता:" : "Severity:"} <strong>{report.kuja_dosha.groom.severity}</strong> ({lang === "ne" ? "परिहार:" : "Cancelled:"} {report.kuja_dosha.groom.is_cancelled ? (lang === "ne" ? "भएको" : "Yes") : (lang === "ne" ? "नभएको" : "No")})
                </div>
                {report.kuja_dosha.groom.cancellations.length > 0 && (
                  <div style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", marginTop: "var(--space-1-5)" }}>
                    {lang === "ne" ? "परिहार सूत्र:" : "Cancellations:"} {report.kuja_dosha.groom.cancellations.join(", ")}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Extended Kutas (Collapsible) */}
          <div className="card" style={{ padding: "var(--space-4-5)" }}>
            <button
              onClick={() => setShowExtended(!showExtended)}
              style={{
                width: "100%",
                background: "transparent",
                border: "none",
                color: "var(--text-bright)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                cursor: "pointer",
                fontWeight: 600,
                fontSize: "var(--type-data)",
              }}
            >
              <span>{lang === "ne" ? "थप शास्त्रीय कूटहरू (महेन्द्र, स्त्री दीर्घ, रज्जु, वेध)" : "Extended Classical Kutas (Mahendra, Stree Deergha, Rajju, Vedha)"}</span>
              {showExtended ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>

            {showExtended && (
              <div style={{ marginTop: "var(--space-4)", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "var(--space-3)" }}>
                {[
                  report.extended_kutas.mahendra,
                  report.extended_kutas.stree_deergha,
                  report.extended_kutas.rajju,
                  report.extended_kutas.vedha,
                ].map((k) => (
                  <div
                    key={k.name}
                    style={{
                      padding: "var(--space-3)",
                      borderRadius: "var(--radius-sm)",
                      background: "var(--bg-subtle)",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-1-5)" }}>
                      <span style={{ fontWeight: 600, color: "var(--text-bright)" }}>{k.name}</span>
                      {k.is_favorable ? (
                        <CheckCircle2 size={14} color="var(--emerald)" />
                      ) : (
                        <AlertTriangle size={14} color="var(--rose)" />
                      )}
                    </div>
                    <p style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)" }}>{k.notes}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Final Verdict Banner */}
          <div
            className="card"
            style={{
              padding: "var(--space-5) var(--space-6)",
              background: "var(--gold-dim)",
              border: "1px solid var(--gold-border)",
              display: "flex",
              alignItems: "center",
              gap: "var(--space-3-5)",
            }}
          >
            <Sparkles size={24} color="var(--gold-vivid)" />
            <div>
              <div style={{ fontWeight: 700, color: "var(--gold-vivid)", fontSize: "var(--type-body)", marginBottom: "var(--space-0-5)" }}>
                {t.compatibility.verdictTitle}
              </div>
              <div style={{ fontSize: "var(--type-small)", color: "var(--text-bright)" }}>
                {report.recommendation}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
