"use client";

import React, { useState, useEffect } from "react";
import { BirthDataInput, TransitReport } from "@/lib/types";
import { fetchTransits } from "@/lib/api";
import { Skeleton } from "@/components/Skeleton";
import { EmptyState } from "@/components/EmptyState";
import { Compass, AlertTriangle, ShieldCheck, Sparkles, Calendar } from "lucide-react";

interface Props {
  birth: BirthDataInput;
  onNavigateToChart?: () => void;
}

export const TransitsView: React.FC<Props> = ({ birth, onNavigateToChart }) => {
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
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
      {/* Top Controller */}
      <div className="card" style={{ padding: "var(--space-4) var(--space-5)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "var(--space-3)" }}>
        <div>
          <h2 style={{ fontSize: "var(--type-heading)", fontWeight: 700, display: "flex", alignItems: "center", gap: "var(--space-2)", color: "var(--text-high)" }}>
            <Compass size={18} color="var(--gold-vivid)" aria-hidden="true" />
            Gochar Planetary Transits
          </h2>
          <p style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", marginTop: "2px" }}>
            Computed in real-time against natal Moon and Ascendant
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <label style={{ fontSize: "var(--type-label)", color: "var(--text-mid)", display: "flex", alignItems: "center", gap: "var(--space-1)" }}>
            <Calendar size={13} aria-hidden="true" /> Transit Date:
          </label>
          <input
            type="date"
            value={transitDate}
            onChange={(e) => setTransitDate(e.target.value)}
            style={{ width: "auto" }}
            aria-label="Transit evaluation date"
          />
        </div>
      </div>

      {loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--space-4)" }}>
            <div className="card" style={{ padding: "var(--space-5)", display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
              <Skeleton width="40%" height="16px" />
              <Skeleton width="60%" height="24px" />
              <Skeleton width="90%" height="14px" />
            </div>
            <div className="card" style={{ padding: "var(--space-5)", display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
              <Skeleton width="40%" height="16px" />
              <Skeleton width="60%" height="24px" />
              <Skeleton width="90%" height="14px" />
            </div>
          </div>
          <div className="card" style={{ padding: "var(--space-5)", display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
            <Skeleton width="30%" height="20px" />
            {[1, 2, 3, 4, 5, 6, 7].map((i) => (
              <Skeleton key={i} width="100%" height="32px" />
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="card" style={{ padding: "var(--space-4)", color: "var(--rose)", borderColor: "var(--rose)" }} role="alert">
          Failed to load transits: {error}
        </div>
      )}

      {report && !loading && (
        <>
          {/* Key Indicators Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--space-4)" }}>
            {/* Sade Sati Card */}
            <div className="card" style={{ padding: "var(--space-5)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "var(--space-3)" }}>
                <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", letterSpacing: "0.06em" }}>SATURN TRANSIT (SADE SATI)</span>
                {report.sade_sati.is_active ? (
                  <span className="badge badge-rose" style={{ gap: "4px" }}>
                    <AlertTriangle size={11} aria-hidden="true" /> ACTIVE
                  </span>
                ) : (
                  <span className="badge badge-emerald" style={{ gap: "4px" }}>
                    <ShieldCheck size={11} aria-hidden="true" /> INACTIVE
                  </span>
                )}
              </div>

              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-high)", marginBottom: "var(--space-1)" }}>
                {report.sade_sati.is_active ? report.sade_sati.phase : "No Sade Sati Cycle"}
              </h3>
              <p style={{ fontSize: "var(--type-body)", color: "var(--text-mid)", lineHeight: 1.5 }}>
                Saturn currently in <strong style={{ color: "var(--gold-bright)" }}>{report.sade_sati.saturn_sign}</strong> ({report.sade_sati.house_from_moon}th from Natal Moon in {report.sade_sati.natal_moon_sign}).
              </p>

              {(report.sade_sati.is_ashtama_shani || report.sade_sati.is_kantaka_shani) && (
                <div style={{ marginTop: "var(--space-3)", display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
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
            <div className="card" style={{ padding: "var(--space-5)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "var(--space-3)" }}>
                <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", letterSpacing: "0.06em" }}>DHISHTI / DOUBLE TRANSIT</span>
                <span className="badge badge-gold" style={{ gap: "4px" }}>
                  <Sparkles size={11} aria-hidden="true" /> AUSPICIOUS
                </span>
              </div>

              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--gold-bright)", marginBottom: "var(--space-1)" }}>
                {report.double_transit_houses.length > 0
                  ? `Houses: ${report.double_transit_houses.join(", ")}`
                  : "No Double Transit Active"}
              </h3>
              <p style={{ fontSize: "var(--type-body)", color: "var(--text-mid)", lineHeight: 1.5 }}>
                Houses jointly activated by Saturn and Jupiter aspects. Classical indicator of major life events, karma fruition, and manifestation.
              </p>
            </div>
          </div>

          {/* Planetary Transits Table */}
          <div className="card" style={{ padding: "var(--space-5)" }}>
            <h3 style={{ fontSize: "var(--type-heading)", fontWeight: 700, marginBottom: "var(--space-3)", color: "var(--text-high)" }}>
              Current Planetary Positions in Transit
            </h3>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--type-body)", textAlign: "left" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-mid)", fontSize: "var(--type-micro)" }}>
                    <th style={{ padding: "var(--space-2)" }}>PLANET</th>
                    <th style={{ padding: "var(--space-2)" }}>TRANSIT SIGN</th>
                    <th style={{ padding: "var(--space-2)" }}>DEGREE</th>
                    <th style={{ padding: "var(--space-2)" }}>FROM NATAL LAGNA</th>
                    <th style={{ padding: "var(--space-2)" }}>FROM NATAL MOON</th>
                    <th style={{ padding: "var(--space-2)" }}>MOTION</th>
                  </tr>
                </thead>
                <tbody>
                  {report.planets.map((p, idx) => (
                    <tr
                      key={`${p.name}-${idx}`}
                      style={{
                        borderBottom: "1px solid var(--border-subtle)",
                        background: idx % 2 === 0 ? "transparent" : "var(--bg-subtle)",
                      }}
                    >
                      <td style={{ padding: "var(--space-3) var(--space-2)", fontWeight: 600 }}>{p.name}</td>
                      <td style={{ padding: "var(--space-3) var(--space-2)" }}>
                        <span className="badge badge-cyan">{p.sign}</span>
                      </td>
                      <td style={{ padding: "var(--space-3) var(--space-2)", fontFamily: "var(--font-mono)", fontSize: "var(--type-data)" }}>
                        {p.degree_in_sign.toFixed(2)}°
                      </td>
                      <td style={{ padding: "var(--space-3) var(--space-2)" }}>House {p.house_from_asc}</td>
                      <td style={{ padding: "var(--space-3) var(--space-2)", color: "var(--gold-bright)", fontWeight: 500 }}>House {p.house_from_moon}</td>
                      <td style={{ padding: "var(--space-3) var(--space-2)" }}>
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
