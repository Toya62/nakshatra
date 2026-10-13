"use client";

import React, { useState, useEffect } from "react";
import { BirthDataInput, TransitReport } from "@/lib/types";
import { fetchTransits } from "@/lib/api";
import { Compass, AlertTriangle, ShieldCheck, Sparkles, Calendar } from "lucide-react";

interface Props {
  birth: BirthDataInput;
}

export const TransitsView: React.FC<Props> = ({ birth }) => {
  const [transitDate, setTransitDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [report, setReport] = useState<TransitReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTransits = async (dateStr?: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTransits(birth, dateStr || transitDate);
      setReport(data);
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTransits(transitDate);
  }, [birth, transitDate]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Top Controller */}
      <div className="glass-panel" style={{ padding: "18px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h3 className="title-serif gold-gradient-text" style={{ fontSize: "1.2rem", display: "flex", alignItems: "center", gap: "8px" }}>
            <Compass size={20} color="#e5b94c" />
            Gochar Planetary Transits
          </h3>
          <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
            Computed in real-time against natal Moon and Ascendant
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <label style={{ fontSize: "0.85rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "6px" }}>
            <Calendar size={14} /> Transit Date:
          </label>
          <input
            type="date"
            value={transitDate}
            onChange={(e) => setTransitDate(e.target.value)}
            style={{ width: "auto" }}
          />
        </div>
      </div>

      {loading && (
        <div className="glass-panel" style={{ padding: "40px", textAlign: "center", color: "var(--accent-gold)" }}>
          Calculating Gochar Ephemeris...
        </div>
      )}

      {error && (
        <div className="glass-panel" style={{ padding: "20px", color: "var(--accent-rose)", borderColor: "var(--accent-rose)" }}>
          Error: {error}
        </div>
      )}

      {report && !loading && (
        <>
          {/* Key Indicators Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "18px" }}>
            {/* Sade Sati Card */}
            <div className="glass-panel" style={{ padding: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", letterSpacing: "0.06em" }}>SATURN TRANSIT (SADE SATI)</span>
                {report.sade_sati.is_active ? (
                  <span className="badge badge-rose" style={{ gap: "4px" }}>
                    <AlertTriangle size={12} /> ACTIVE
                  </span>
                ) : (
                  <span className="badge badge-emerald" style={{ gap: "4px" }}>
                    <ShieldCheck size={12} /> INACTIVE
                  </span>
                )}
              </div>

              <h4 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#f8fafc", marginBottom: "6px" }}>
                {report.sade_sati.is_active ? report.sade_sati.phase : "No Sade Sati Cycle"}
              </h4>
              <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                Saturn currently in <strong style={{ color: "#fbe285" }}>{report.sade_sati.saturn_sign}</strong> ({report.sade_sati.house_from_moon}th from Natal Moon in {report.sade_sati.natal_moon_sign}).
              </p>

              {(report.sade_sati.is_ashtama_shani || report.sade_sati.is_kantaka_shani) && (
                <div style={{ marginTop: "12px", display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  {report.sade_sati.is_ashtama_shani && (
                    <span className="badge badge-rose">Ashtama Shani (8th House)</span>
                  )}
                  {report.sade_sati.is_kantaka_shani && (
                    <span className="badge badge-rose">Kantaka Shani (4th/10th)</span>
                  )}
                </div>
              )}
            </div>

            {/* Double Transit Card */}
            <div className="glass-panel" style={{ padding: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", letterSpacing: "0.06em" }}>DHISHTI / DOUBLE TRANSIT</span>
                <span className="badge badge-gold" style={{ gap: "4px" }}>
                  <Sparkles size={12} /> AUSPICIOUS
                </span>
              </div>

              <h4 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#fbe285", marginBottom: "6px" }}>
                {report.double_transit_houses.length > 0
                  ? `Houses: ${report.double_transit_houses.join(", ")}`
                  : "No Double Transit Active"}
              </h4>
              <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                Houses jointly activated by Saturn and Jupiter aspects. Classical indicator of major life events, karma fruition, and manifestation.
              </p>
            </div>
          </div>

          {/* Planetary Transits Table */}
          <div className="glass-panel" style={{ padding: "20px" }}>
            <h4 className="title-serif gold-gradient-text" style={{ fontSize: "1.05rem", marginBottom: "14px" }}>
              Current Planetary Positions in Transit
            </h4>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", textAlign: "left" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid rgba(229, 185, 76, 0.2)", color: "var(--text-muted)", fontSize: "0.78rem" }}>
                    <th style={{ padding: "8px" }}>PLANET</th>
                    <th style={{ padding: "8px" }}>TRANSIT SIGN</th>
                    <th style={{ padding: "8px" }}>DEGREE</th>
                    <th style={{ padding: "8px" }}>FROM NATAL LAGNA</th>
                    <th style={{ padding: "8px" }}>FROM NATAL MOON</th>
                    <th style={{ padding: "8px" }}>MOTION</th>
                  </tr>
                </thead>
                <tbody>
                  {report.planets.map((p, idx) => (
                    <tr key={`${p.name}-${idx}`} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                      <td style={{ padding: "10px 8px", fontWeight: 600 }}>{p.name}</td>
                      <td style={{ padding: "10px 8px" }}>
                        <span className="badge badge-cyan">{p.sign}</span>
                      </td>
                      <td style={{ padding: "10px 8px", fontFamily: "var(--font-mono)" }}>
                        {p.degree_in_sign.toFixed(2)}°
                      </td>
                      <td style={{ padding: "10px 8px" }}>House {p.house_from_asc}</td>
                      <td style={{ padding: "10px 8px", color: "var(--accent-gold)" }}>House {p.house_from_moon}</td>
                      <td style={{ padding: "10px 8px" }}>
                        {p.retrograde ? (
                          <span className="badge badge-rose">Retrograde</span>
                        ) : (
                          <span className="badge badge-emerald">Direct</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
