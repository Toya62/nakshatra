"use client";

import React, { useState, useEffect } from "react";
import {
  Sun,
  Moon,
  Clock,
  AlertOctagon,
  Sparkles,
  ShieldAlert,
  Calendar,
  Briefcase,
  Plane,
  Home,
  Heart,
  DollarSign,
  Activity,
} from "lucide-react";
import { BirthDataInput, MuhurthaReport } from "@/lib/types";
import { fetchMuhurtha } from "@/lib/api";

interface Props {
  defaultLat?: number;
  defaultLon?: number;
  defaultTz?: string;
}

export const MuhurthaView: React.FC<Props> = ({
  defaultLat = 28.6139,
  defaultLon = 77.209,
  defaultTz = "Asia/Kolkata",
}) => {
  const [input, setInput] = useState<BirthDataInput>({
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    day: new Date().getDate(),
    hour: new Date().getHours(),
    minute: new Date().getMinutes(),
    second: 0,
    latitude: defaultLat,
    longitude: defaultLon,
    timezone: defaultTz,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<MuhurthaReport | null>(null);
  const [timelineTab, setTimelineTab] = useState<"horas" | "choghadiyas">("horas");

  const loadMuhurtha = async (params: BirthDataInput) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchMuhurtha(params);
      setReport(res);
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMuhurtha(input);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadMuhurtha(input);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Header Banner */}
      <div className="glass-panel" style={{ padding: "24px 28px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "8px" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #e5b94c 0%, #10b981 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Sun size={20} color="#07090e" />
          </div>
          <h2 className="title-serif gold-gradient-text" style={{ fontSize: "1.4rem", fontWeight: 700 }}>
            Vedic Muhurtha & Planetary Election
          </h2>
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", maxWidth: "860px", lineHeight: 1.5 }}>
          Real-time electional astrology calculating 24 Chaldean Planetary Horas, 16 Choghadiyas,
          solar culmination (Abhijit & Brahma Muhurthas), Rahu Kalam afflictions, and classical Siddhi Yogas
          for decision-making and enterprise ventures.
        </p>
      </div>

      {/* Time & Place Form */}
      <form onSubmit={handleSubmit} className="glass-panel" style={{ padding: "20px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "14px", alignItems: "flex-end" }}>
          <div>
            <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
              Date
            </label>
            <input
              type="date"
              value={`${input.year}-${String(input.month).padStart(2, "0")}-${String(input.day).padStart(2, "0")}`}
              onChange={(e) => {
                const [y, m, d] = e.target.value.split("-").map(Number);
                if (y && m && d) setInput({ ...input, year: y, month: m, day: d });
              }}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: "8px",
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "var(--text-bright)",
                fontSize: "0.88rem",
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
              Time
            </label>
            <input
              type="time"
              value={`${String(input.hour).padStart(2, "0")}:${String(input.minute).padStart(2, "0")}`}
              onChange={(e) => {
                const [h, m] = e.target.value.split(":").map(Number);
                setInput({ ...input, hour: h || 0, minute: m || 0 });
              }}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: "8px",
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "var(--text-bright)",
                fontSize: "0.88rem",
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
              Latitude
            </label>
            <input
              type="number"
              step="0.0001"
              value={input.latitude}
              onChange={(e) => setInput({ ...input, latitude: parseFloat(e.target.value) || 0 })}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: "8px",
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "var(--text-bright)",
                fontSize: "0.88rem",
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
              Longitude
            </label>
            <input
              type="number"
              step="0.0001"
              value={input.longitude}
              onChange={(e) => setInput({ ...input, longitude: parseFloat(e.target.value) || 0 })}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: "8px",
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "var(--text-bright)",
                fontSize: "0.88rem",
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
              Timezone
            </label>
            <input
              type="text"
              value={input.timezone}
              onChange={(e) => setInput({ ...input, timezone: e.target.value })}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: "8px",
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "var(--text-bright)",
                fontSize: "0.88rem",
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="badge-gold"
            style={{
              padding: "9px 18px",
              fontWeight: 700,
              cursor: loading ? "wait" : "pointer",
              borderRadius: "8px",
              border: "1px solid rgba(229,185,76,0.6)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              height: "38px",
            }}
          >
            <Calendar size={15} />
            {loading ? "Evaluating..." : "Evaluate"}
          </button>
        </div>
      </form>

      {error && (
        <div className="glass-panel" style={{ padding: "16px", color: "var(--accent-rose)", borderColor: "var(--accent-rose)" }}>
          {error}
        </div>
      )}

      {report && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Main Score & Solar Bounds Card */}
          <div
            className="glass-panel"
            style={{
              padding: "24px 28px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "20px",
              border: `1px solid ${
                report.muhurtha_score >= 70
                  ? "rgba(16, 185, 129, 0.6)"
                  : report.muhurtha_score >= 50
                  ? "rgba(56, 189, 248, 0.6)"
                  : "rgba(244, 63, 94, 0.6)"
              }`,
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "6px" }}>
                <span
                  style={{
                    fontSize: "2.5rem",
                    fontWeight: 900,
                    color:
                      report.muhurtha_score >= 70
                        ? "#10b981"
                        : report.muhurtha_score >= 50
                        ? "#38bdf8"
                        : "#f43f5e",
                  }}
                >
                  {report.muhurtha_score}
                </span>
                <span style={{ fontSize: "1.2rem", color: "var(--text-muted)", fontWeight: 600 }}>/ 100</span>
                <span
                  className={`badge ${
                    report.muhurtha_score >= 70
                      ? "badge-emerald"
                      : report.muhurtha_score >= 50
                      ? "badge-cyan"
                      : "badge-rose"
                  }`}
                  style={{ fontSize: "0.85rem", padding: "4px 12px" }}
                >
                  {report.verdict}
                </span>
              </div>
              <p style={{ color: "var(--text-bright)", fontSize: "0.92rem", fontWeight: 500 }}>
                {report.recommendation}
              </p>
            </div>

            <div style={{ display: "flex", gap: "18px", color: "var(--text-muted)", fontSize: "0.82rem" }}>
              <div>
                <span style={{ color: "#e5b94c", fontWeight: 600 }}>Sunrise:</span> {report.sunrise_time}
              </div>
              <div>
                <span style={{ color: "#ec4899", fontWeight: 600 }}>Sunset:</span> {report.sunset_time}
              </div>
            </div>
          </div>

          {/* Active Hora & Active Choghadiya */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
            <div className="glass-panel" style={{ padding: "20px", borderLeft: "4px solid #e5b94c" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Active Planetary Hora
                </span>
                <span className={`badge ${report.current_hora.nature === "Benefic" ? "badge-emerald" : "badge-rose"}`}>
                  {report.current_hora.nature}
                </span>
              </div>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-bright)", marginBottom: "4px" }}>
                {report.current_hora.ruling_planet} Hora
              </h3>
              <p style={{ fontSize: "0.82rem", color: "#e5b94c", marginBottom: "10px" }}>
                {report.current_hora.start_time} - {report.current_hora.end_time} ({report.current_hora.period_type})
              </p>
              <p style={{ fontSize: "0.84rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                <strong>Recommended:</strong> {report.current_hora.recommended_activities}
              </p>
            </div>

            <div className="glass-panel" style={{ padding: "20px", borderLeft: "4px solid #38bdf8" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Active Choghadiya
                </span>
                <span className={`badge ${report.current_choghadiya.score >= 70 ? "badge-emerald" : "badge-rose"}`}>
                  {report.current_choghadiya.nature}
                </span>
              </div>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-bright)", marginBottom: "4px" }}>
                {report.current_choghadiya.name} Choghadiya
              </h3>
              <p style={{ fontSize: "0.82rem", color: "#38bdf8", marginBottom: "10px" }}>
                {report.current_choghadiya.start_time} - {report.current_choghadiya.end_time} ({report.current_choghadiya.period_type})
              </p>
              <p style={{ fontSize: "0.84rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                Ruler: <strong>{report.current_choghadiya.ruler}</strong> | Quality Score: <strong>{report.current_choghadiya.score}/100</strong>
              </p>
            </div>
          </div>

          {/* Enterprise Suitability Matrix */}
          <div className="glass-panel" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-bright)", marginBottom: "16px" }}>
              Enterprise Suitability Checklist
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px" }}>
              {[
                { label: "Business Contracts", ok: report.suitability.business_contract, icon: Briefcase },
                { label: "Financial Investment", ok: report.suitability.financial_investment, icon: DollarSign },
                { label: "Travel & Relocation", ok: report.suitability.travel, icon: Plane },
                { label: "Marriage Ceremonies", ok: report.suitability.marriage, icon: Heart },
                { label: "Real Estate Acquisition", ok: report.suitability.property_purchase, icon: Home },
                { label: "Medical Treatments", ok: report.suitability.medical_treatment, icon: Activity },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div
                    key={item.label}
                    style={{
                      padding: "12px 14px",
                      borderRadius: "10px",
                      background: item.ok ? "rgba(16,185,129,0.06)" : "rgba(244,63,94,0.06)",
                      border: `1px solid ${item.ok ? "rgba(16,185,129,0.2)" : "rgba(244,63,94,0.2)"}`,
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                    }}
                  >
                    <Icon size={18} color={item.ok ? "#10b981" : "#f43f5e"} />
                    <div>
                      <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-bright)" }}>
                        {item.label}
                      </div>
                      <div style={{ fontSize: "0.72rem", color: item.ok ? "#10b981" : "#f43f5e", fontWeight: 500 }}>
                        {item.ok ? "Favorable" : "Avoid"}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Special Timing Windows & Alerts */}
          <div className="glass-panel" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-bright)", marginBottom: "16px" }}>
              Auspicious & Inauspicious Timing Windows
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "14px" }}>
              {/* Abhijit Muhurtha */}
              <div style={{ padding: "14px", borderRadius: "10px", background: "rgba(229,185,76,0.05)", border: "1px solid rgba(229,185,76,0.2)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <span style={{ fontWeight: 600, color: "#e5b94c", fontSize: "0.88rem" }}>Abhijit Muhurtha</span>
                  {report.abhijit_muhurtha.is_active && <span className="badge badge-emerald">ACTIVE NOW</span>}
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-bright)" }}>
                  {report.abhijit_muhurtha.start_time} - {report.abhijit_muhurtha.end_time}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>
                  {report.abhijit_muhurtha.notes}
                </div>
              </div>

              {/* Brahma Muhurtha */}
              <div style={{ padding: "14px", borderRadius: "10px", background: "rgba(56,189,248,0.05)", border: "1px solid rgba(56,189,248,0.2)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <span style={{ fontWeight: 600, color: "#38bdf8", fontSize: "0.88rem" }}>Brahma Muhurtha</span>
                  {report.brahma_muhurtha.is_active && <span className="badge badge-cyan">ACTIVE NOW</span>}
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-bright)" }}>
                  {report.brahma_muhurtha.start_time} - {report.brahma_muhurtha.end_time}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>
                  {report.brahma_muhurtha.notes}
                </div>
              </div>

              {/* Rahu Kalam */}
              <div style={{ padding: "14px", borderRadius: "10px", background: "rgba(244,63,94,0.05)", border: "1px solid rgba(244,63,94,0.2)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <span style={{ fontWeight: 600, color: "#f43f5e", fontSize: "0.88rem" }}>Rahu Kalam (Avoid)</span>
                  {report.rahu_kalam.is_active && <span className="badge badge-rose">ALERT: ACTIVE</span>}
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-bright)" }}>
                  {report.rahu_kalam.start_time} - {report.rahu_kalam.end_time}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>
                  {report.rahu_kalam.notes}
                </div>
              </div>

              {/* Yamaganda */}
              <div style={{ padding: "14px", borderRadius: "10px", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <span style={{ fontWeight: 600, color: "var(--text-bright)", fontSize: "0.88rem" }}>Yamaganda (Avoid)</span>
                  {report.yamaganda.is_active && <span className="badge badge-rose">ACTIVE</span>}
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-bright)" }}>
                  {report.yamaganda.start_time} - {report.yamaganda.end_time}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>
                  {report.yamaganda.notes}
                </div>
              </div>
            </div>
          </div>

          {/* Timeline Switcher: Horas vs Choghadiyas */}
          <div className="glass-panel" style={{ padding: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-bright)" }}>
                Complete Day Timeline
              </h3>
              <div style={{ display: "flex", gap: "6px" }}>
                <button
                  onClick={() => setTimelineTab("horas")}
                  className={`badge ${timelineTab === "horas" ? "badge-gold" : "badge-cyan"}`}
                  style={{
                    cursor: "pointer",
                    padding: "6px 14px",
                    background: timelineTab === "horas" ? "rgba(229,185,76,0.3)" : "transparent",
                  }}
                >
                  Planetary Horas (24)
                </button>
                <button
                  onClick={() => setTimelineTab("choghadiyas")}
                  className={`badge ${timelineTab === "choghadiyas" ? "badge-gold" : "badge-cyan"}`}
                  style={{
                    cursor: "pointer",
                    padding: "6px 14px",
                    background: timelineTab === "choghadiyas" ? "rgba(229,185,76,0.3)" : "transparent",
                  }}
                >
                  Choghadiya Cycles (16)
                </button>
              </div>
            </div>

            {timelineTab === "horas" && (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", textAlign: "left", color: "var(--text-muted)" }}>
                      <th style={{ padding: "8px 12px" }}>#</th>
                      <th style={{ padding: "8px 12px" }}>Time</th>
                      <th style={{ padding: "8px 12px" }}>Ruling Planet</th>
                      <th style={{ padding: "8px 12px" }}>Nature</th>
                      <th style={{ padding: "8px 12px" }}>Recommended Activities</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...report.day_horas, ...report.night_horas].map((h) => (
                      <tr
                        key={h.hora_index}
                        style={{
                          borderBottom: "1px solid rgba(255,255,255,0.05)",
                          background: h.is_current ? "rgba(229,185,76,0.12)" : "transparent",
                        }}
                      >
                        <td style={{ padding: "10px 12px", fontWeight: 600, color: "var(--text-dim)" }}>
                          {h.hora_index} ({h.period_type})
                        </td>
                        <td style={{ padding: "10px 12px", color: h.is_current ? "#e5b94c" : "var(--text-bright)", fontWeight: h.is_current ? 700 : 400 }}>
                          {h.start_time} - {h.end_time} {h.is_current && "(Active)"}
                        </td>
                        <td style={{ padding: "10px 12px", fontWeight: 600, color: "var(--text-bright)" }}>
                          {h.ruling_planet}
                        </td>
                        <td style={{ padding: "10px 12px" }}>
                          <span className={`badge ${h.nature === "Benefic" ? "badge-emerald" : "badge-rose"}`}>
                            {h.nature}
                          </span>
                        </td>
                        <td style={{ padding: "10px 12px", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                          {h.recommended_activities}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {timelineTab === "choghadiyas" && (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.1)", textAlign: "left", color: "var(--text-muted)" }}>
                      <th style={{ padding: "8px 12px" }}>#</th>
                      <th style={{ padding: "8px 12px" }}>Time</th>
                      <th style={{ padding: "8px 12px" }}>Choghadiya</th>
                      <th style={{ padding: "8px 12px" }}>Nature</th>
                      <th style={{ padding: "8px 12px" }}>Ruling Planet</th>
                      <th style={{ padding: "8px 12px" }}>Quality Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...report.day_choghadiyas, ...report.night_choghadiyas].map((c, idx) => (
                      <tr
                        key={idx}
                        style={{
                          borderBottom: "1px solid rgba(255,255,255,0.05)",
                          background: c.is_current ? "rgba(56,189,248,0.12)" : "transparent",
                        }}
                      >
                        <td style={{ padding: "10px 12px", fontWeight: 600, color: "var(--text-dim)" }}>
                          {c.index} ({c.period_type})
                        </td>
                        <td style={{ padding: "10px 12px", color: c.is_current ? "#38bdf8" : "var(--text-bright)", fontWeight: c.is_current ? 700 : 400 }}>
                          {c.start_time} - {c.end_time} {c.is_current && "(Active)"}
                        </td>
                        <td style={{ padding: "10px 12px", fontWeight: 600, color: "var(--text-bright)" }}>
                          {c.name}
                        </td>
                        <td style={{ padding: "10px 12px" }}>
                          <span className={`badge ${c.score >= 70 ? "badge-emerald" : "badge-rose"}`}>
                            {c.nature}
                          </span>
                        </td>
                        <td style={{ padding: "10px 12px", color: "var(--text-muted)" }}>
                          {c.ruler}
                        </td>
                        <td style={{ padding: "10px 12px", fontWeight: 600, color: c.score >= 70 ? "#10b981" : "#f43f5e" }}>
                          {c.score}/100
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
