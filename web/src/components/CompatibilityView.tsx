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

interface Props {
  defaultBride?: BirthDataInput;
  defaultGroom?: BirthDataInput;
}

export const CompatibilityView: React.FC<Props> = ({ defaultBride, defaultGroom }) => {
  const [brideData, setBrideData] = useState<BirthDataInput>(
    defaultBride || {
      year: 1997,
      month: 5,
      day: 22,
      hour: 4,
      minute: 53,
      second: 0,
      latitude: DEFAULT_LOCATION.lat || 27.8667,
      longitude: DEFAULT_LOCATION.lon || 83.4833,
      timezone: DEFAULT_LOCATION.tz || "Asia/Kathmandu",
      place_name: "Palpa, Nepal",
      ayanamsa: "jhora_lahiri",
      house_system: "WholeSign",
    }
  );

  const [groomData, setGroomData] = useState<BirthDataInput>(
    defaultGroom || {
      year: 1995,
      month: 11,
      day: 28,
      hour: 8,
      minute: 30,
      second: 0,
      latitude: 28.6139,
      longitude: 77.209,
      timezone: "Asia/Kolkata",
      place_name: "Delhi, India",
      ayanamsa: "jhora_lahiri",
      house_system: "WholeSign",
    }
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
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Header Banner */}
      <div className="card" style={{ padding: "24px 28px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "8px" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, var(--gold-vivid) 0%, var(--rose) 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Heart size={20} color="#ffffff" />
          </div>
          <h2 className="title-serif gold-gradient-text" style={{ fontSize: "1.4rem", fontWeight: 700 }}>
            Ashtakoota Kundali Matching & Kuja Dosha
          </h2>
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", maxWidth: "860px", lineHeight: 1.5 }}>
          Deterministic 36-point relationship compatibility engine based on Brihat Parashara Hora Shastra,
          Muhurtha Chintamani, and VedAstro canons. Computes all 8 Kutas, dosha cancellations, extended Rajju/Vedha pairs,
          and Mars afflictions from Lagna, Moon, and Venus.
        </p>
      </div>

      {/* Input Form Cards */}
      <form onSubmit={handleCalculate} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))", gap: "20px" }}>
          {/* Bride Card */}
          <div className="card" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "1.05rem", color: "var(--rose)", fontWeight: 700, marginBottom: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>Bride&apos;s Profile (Kanya)</span>
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div style={{ gridColumn: "span 2" }}>
                <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  Name
                </label>
                <input
                  type="text"
                  value={brideName}
                  onChange={(e) => setBrideName(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "8px", fontSize: "0.88rem" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  Date of Birth
                </label>
                <input
                  type="date"
                  value={`${brideData.year}-${String(brideData.month).padStart(2, "0")}-${String(brideData.day).padStart(2, "0")}`}
                  onChange={(e) => {
                    const [y, m, d] = e.target.value.split("-").map(Number);
                    if (y && m && d) setBrideData({ ...brideData, year: y, month: m, day: d });
                  }}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "8px", fontSize: "0.88rem" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  Time of Birth
                </label>
                <input
                  type="time"
                  step="1"
                  value={`${String(brideData.hour).padStart(2, "0")}:${String(brideData.minute).padStart(2, "0")}:${String(brideData.second ?? 0).padStart(2, "0")}`}
                  onChange={(e) => {
                    const parts = e.target.value.split(":").map(Number);
                    setBrideData({ ...brideData, hour: parts[0] || 0, minute: parts[1] || 0, second: parts[2] || 0 });
                  }}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "8px", fontSize: "0.88rem" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  Latitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={brideData.latitude}
                  onChange={(e) => setBrideData({ ...brideData, latitude: parseFloat(e.target.value) || 0 })}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "8px", fontSize: "0.88rem" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  Longitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={brideData.longitude}
                  onChange={(e) => setBrideData({ ...brideData, longitude: parseFloat(e.target.value) || 0 })}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "8px", fontSize: "0.88rem" }}
                />
              </div>
              <div style={{ gridColumn: "span 2" }}>
                <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  Timezone (IANA)
                </label>
                <input
                  type="text"
                  value={brideData.timezone}
                  onChange={(e) => setBrideData({ ...brideData, timezone: e.target.value })}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "8px", fontSize: "0.88rem" }}
                />
              </div>
            </div>
          </div>

          {/* Groom Card */}
          <div className="card" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "1.05rem", color: "var(--cyan-vivid)", fontWeight: 700, marginBottom: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>Groom&apos;s Profile (Vara)</span>
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div style={{ gridColumn: "span 2" }}>
                <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  Name
                </label>
                <input
                  type="text"
                  value={groomName}
                  onChange={(e) => setGroomName(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "8px", fontSize: "0.88rem" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  Date of Birth
                </label>
                <input
                  type="date"
                  value={`${groomData.year}-${String(groomData.month).padStart(2, "0")}-${String(groomData.day).padStart(2, "0")}`}
                  onChange={(e) => {
                    const [y, m, d] = e.target.value.split("-").map(Number);
                    if (y && m && d) setGroomData({ ...groomData, year: y, month: m, day: d });
                  }}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "8px", fontSize: "0.88rem" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  Time of Birth
                </label>
                <input
                  type="time"
                  step="1"
                  value={`${String(groomData.hour).padStart(2, "0")}:${String(groomData.minute).padStart(2, "0")}:${String(groomData.second ?? 0).padStart(2, "0")}`}
                  onChange={(e) => {
                    const parts = e.target.value.split(":").map(Number);
                    setGroomData({ ...groomData, hour: parts[0] || 0, minute: parts[1] || 0, second: parts[2] || 0 });
                  }}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "8px", fontSize: "0.88rem" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  Latitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={groomData.latitude}
                  onChange={(e) => setGroomData({ ...groomData, latitude: parseFloat(e.target.value) || 0 })}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "8px", fontSize: "0.88rem" }}
                />
              </div>
              <div>
                <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  Longitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={groomData.longitude}
                  onChange={(e) => setGroomData({ ...groomData, longitude: parseFloat(e.target.value) || 0 })}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "8px", fontSize: "0.88rem" }}
                />
              </div>
              <div style={{ gridColumn: "span 2" }}>
                <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                  Timezone (IANA)
                </label>
                <input
                  type="text"
                  value={groomData.timezone}
                  onChange={(e) => setGroomData({ ...groomData, timezone: e.target.value })}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "8px", fontSize: "0.88rem" }}
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
            padding: "14px 28px",
            fontSize: "0.95rem",
            fontWeight: 700,
            cursor: loading ? "wait" : "pointer",
            borderRadius: "12px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "10px",
          }}
        >
          <Sparkles size={18} />
          {loading ? "Calculating Match..." : "Calculate Ashtakoota Match"}
        </button>
      </form>

      {error && (
        <div className="card" style={{ padding: "16px", color: "var(--accent-rose)", borderColor: "var(--accent-rose)" }}>
          {error}
        </div>
      )}

      {/* Results Dashboard */}
      {report && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Main Score Banner */}
          <div
            className="card"
            style={{
              padding: "24px 28px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "20px",
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
              <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "6px" }}>
                <span
                  style={{
                    fontSize: "2.4rem",
                    fontWeight: 900,
                    color:
                      report.ashtakoota.verdict === "Uttama"
                        ? "var(--gold-vivid)"
                        : report.ashtakoota.verdict === "Madhyama"
                        ? "var(--cyan-vivid)"
                        : "var(--rose)",
                  }}
                >
                  {report.ashtakoota.total_score}
                </span>
                <span style={{ fontSize: "1.2rem", color: "var(--text-muted)", fontWeight: 600 }}>/ 36.0 Gunas</span>
                <span
                  className={`badge ${
                    report.ashtakoota.verdict === "Uttama"
                      ? "badge-gold"
                      : report.ashtakoota.verdict === "Madhyama"
                      ? "badge-cyan"
                      : "badge-rose"
                  }`}
                  style={{ fontSize: "0.85rem", padding: "4px 12px" }}
                >
                  {report.ashtakoota.verdict} ({report.ashtakoota.percentage}%)
                </span>
              </div>
              <p style={{ color: "var(--text-bright)", fontSize: "0.92rem", fontWeight: 500 }}>
                {report.ashtakoota.summary}
              </p>
            </div>

            <div style={{ display: "flex", gap: "10px" }}>
              <button
                onClick={handleCopy}
                className="btn-secondary"
                style={{ fontSize: "0.85rem" }}
              >
                <Copy size={14} />
                {copied ? "Copied!" : "Copy Report"}
              </button>
            </div>
          </div>

          {/* Couple Moon Sign / Nakshatra Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "18px" }}>
            <div className="card" style={{ padding: "18px" }}>
              <h4 style={{ color: "var(--rose)", fontSize: "0.95rem", fontWeight: 700, marginBottom: "8px" }}>
                {report.bride_name} (Bride)
              </h4>
              <p style={{ fontSize: "0.88rem", color: "var(--text-bright)" }}>
                Moon in <strong>{report.bride_moon_sign}</strong> | Nakshatra: <strong>{report.bride_nakshatra}</strong> (Pada {report.bride_pada})
              </p>
            </div>

            <div className="card" style={{ padding: "18px" }}>
              <h4 style={{ color: "var(--cyan-vivid)", fontSize: "0.95rem", fontWeight: 700, marginBottom: "8px" }}>
                {report.groom_name} (Groom)
              </h4>
              <p style={{ fontSize: "0.88rem", color: "var(--text-bright)" }}>
                Moon in <strong>{report.groom_moon_sign}</strong> | Nakshatra: <strong>{report.groom_nakshatra}</strong> (Pada {report.groom_pada})
              </p>
            </div>
          </div>

          {/* 8 Ashtakoota Breakdown Table */}
          <div className="card" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "16px", color: "var(--text-bright)" }}>
              Ashtakoota Factor Breakdown (8 Pillars)
            </h3>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.88rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)", textAlign: "left", color: "var(--text-muted)" }}>
                    <th style={{ padding: "10px 12px" }}>Koota</th>
                    <th style={{ padding: "10px 12px" }}>Points</th>
                    <th style={{ padding: "10px 12px" }}>Bride Value</th>
                    <th style={{ padding: "10px 12px" }}>Groom Value</th>
                    <th style={{ padding: "10px 12px" }}>Status</th>
                    <th style={{ padding: "10px 12px" }}>Analysis</th>
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
                      <td style={{ padding: "12px", fontWeight: 600, color: "var(--text-bright)" }}>{k.name}</td>
                      <td style={{ padding: "12px" }}>
                        <span style={{ fontWeight: 700, color: k.obtained_score > 0 ? "var(--gold-vivid)" : "var(--rose)" }}>
                          {k.obtained_score}
                        </span>
                        <span style={{ color: "var(--text-dim)", fontSize: "0.8rem" }}> / {k.max_score}</span>
                      </td>
                      <td style={{ padding: "12px", color: "var(--rose)", fontWeight: 500 }}>{k.bride_val}</td>
                      <td style={{ padding: "12px", color: "var(--cyan-vivid)", fontWeight: 500 }}>{k.groom_val}</td>
                      <td style={{ padding: "12px" }}>
                        {k.is_favorable ? (
                          <span className="badge badge-emerald" style={{ gap: "4px" }}>
                            <CheckCircle2 size={12} /> Pass
                          </span>
                        ) : k.cancelled ? (
                          <span className="badge badge-gold" style={{ gap: "4px" }}>
                            <ShieldCheck size={12} /> Cancelled
                          </span>
                        ) : (
                          <span className="badge badge-rose" style={{ gap: "4px" }}>
                            <XCircle size={12} /> Afflicted
                          </span>
                        )}
                      </td>
                      <td style={{ padding: "12px", color: "var(--text-muted)", fontSize: "0.82rem" }}>{k.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Kuja Dosha (Manglik) Analysis */}
          <div className="card" style={{ padding: "22px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-bright)", display: "flex", alignItems: "center", gap: "8px" }}>
                <ShieldCheck size={18} color="var(--gold-vivid)" />
                <span>Kuja Dosha (Manglik) Evaluation</span>
              </h3>
              <span
                className={`badge ${
                  report.kuja_dosha.is_compatible ? "badge-emerald" : "badge-rose"
                }`}
                style={{ fontSize: "0.85rem", padding: "4px 12px" }}
              >
                {report.kuja_dosha.verdict}
              </span>
            </div>
            <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", marginBottom: "16px" }}>
              {report.kuja_dosha.notes}
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div style={{ padding: "14px", borderRadius: "10px", background: "var(--rose-dim)", border: "1px solid var(--border-subtle)" }}>
                <div style={{ fontWeight: 600, color: "var(--rose)", marginBottom: "4px" }}>Bride Kuja Dosha</div>
                <div style={{ fontSize: "0.88rem", color: "var(--text-bright)" }}>
                  Severity: <strong>{report.kuja_dosha.bride.severity}</strong> (Cancelled: {report.kuja_dosha.bride.is_cancelled ? "Yes" : "No"})
                </div>
                {report.kuja_dosha.bride.cancellations.length > 0 && (
                  <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "6px" }}>
                    Cancellations: {report.kuja_dosha.bride.cancellations.join(", ")}
                  </div>
                )}
              </div>

              <div style={{ padding: "14px", borderRadius: "10px", background: "var(--cyan-dim)", border: "1px solid var(--cyan-border)" }}>
                <div style={{ fontWeight: 600, color: "var(--cyan-vivid)", marginBottom: "4px" }}>Groom Kuja Dosha</div>
                <div style={{ fontSize: "0.88rem", color: "var(--text-bright)" }}>
                  Severity: <strong>{report.kuja_dosha.groom.severity}</strong> (Cancelled: {report.kuja_dosha.groom.is_cancelled ? "Yes" : "No"})
                </div>
                {report.kuja_dosha.groom.cancellations.length > 0 && (
                  <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "6px" }}>
                    Cancellations: {report.kuja_dosha.groom.cancellations.join(", ")}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Extended Kutas (Collapsible) */}
          <div className="card" style={{ padding: "18px" }}>
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
                fontSize: "0.95rem",
              }}
            >
              <span>Extended Classical Kutas (Mahendra, Stree Deergha, Rajju, Vedha)</span>
              {showExtended ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>

            {showExtended && (
              <div style={{ marginTop: "16px", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "12px" }}>
                {[
                  report.extended_kutas.mahendra,
                  report.extended_kutas.stree_deergha,
                  report.extended_kutas.rajju,
                  report.extended_kutas.vedha,
                ].map((k) => (
                  <div
                    key={k.name}
                    style={{
                      padding: "12px",
                      borderRadius: "8px",
                      background: "var(--bg-subtle)",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                      <span style={{ fontWeight: 600, color: "var(--text-bright)" }}>{k.name}</span>
                      {k.is_favorable ? (
                        <CheckCircle2 size={14} color="var(--emerald)" />
                      ) : (
                        <AlertTriangle size={14} color="var(--rose)" />
                      )}
                    </div>
                    <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>{k.notes}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Final Verdict Banner */}
          <div
            className="card"
            style={{
              padding: "20px 24px",
              background: "var(--gold-dim)",
              border: "1px solid var(--gold-border)",
              display: "flex",
              alignItems: "center",
              gap: "14px",
            }}
          >
            <Sparkles size={24} color="var(--gold-vivid)" />
            <div>
              <div style={{ fontWeight: 700, color: "var(--gold-vivid)", fontSize: "0.98rem", marginBottom: "2px" }}>
                Final Astrological Recommendation
              </div>
              <div style={{ fontSize: "0.9rem", color: "var(--text-bright)" }}>
                {report.recommendation}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
