"use client";

import React, { useState, useEffect } from "react";
import { BirthDataInput, TransitReport } from "@/lib/types";
import { fetchTransits } from "@/lib/api";
import { Skeleton } from "@/components/Skeleton";
import { Compass, AlertTriangle, ShieldCheck, Sparkles, Calendar } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

interface Props {
  birth: BirthDataInput;
  onNavigateToChart?: () => void;
}

export const TransitsView: React.FC<Props> = ({ birth }) => {
  const { t, lang, num, deg } = useLanguage();
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
            {t.transits.title}
          </h2>
          <p style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", marginTop: "2px" }}>
            {t.transits.subtitle}
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <label style={{ fontSize: "var(--type-label)", color: "var(--text-mid)", display: "flex", alignItems: "center", gap: "var(--space-1)" }}>
            <Calendar size={13} aria-hidden="true" /> {t.transits.transitDate}
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
          {t.transits.loadError}: {error}
        </div>
      )}

      {report && !loading && (
        <>
          {/* Key Indicators Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "var(--space-4)" }}>
            {/* Sade Sati Card */}
            <div className="card" style={{ padding: "var(--space-5)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "var(--space-3)" }}>
                <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", letterSpacing: "0.06em" }}>{t.transits.saturnTransit}</span>
                {report.sade_sati.is_active ? (
                  <span className="badge badge-rose" style={{ gap: "4px" }}>
                    <AlertTriangle size={11} aria-hidden="true" /> {t.transits.active}
                  </span>
                ) : (
                  <span className="badge badge-emerald" style={{ gap: "4px" }}>
                    <ShieldCheck size={11} aria-hidden="true" /> {t.transits.inactive}
                  </span>
                )}
              </div>

              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-high)", marginBottom: "var(--space-1)" }}>
                {report.sade_sati.is_active ? report.sade_sati.phase : t.transits.noCycle}
              </h3>
              <p style={{ fontSize: "var(--type-body)", color: "var(--text-mid)", lineHeight: 1.5 }}>
                {lang === "ne" ? (
                  <>
                    {t.transits.currentlyIn} <strong style={{ color: "var(--gold-bright)" }}>{t.zodiac.signs[report.sade_sati.saturn_sign as keyof typeof t.zodiac.signs] || report.sade_sati.saturn_sign}</strong> राशिमा ({t.zodiac.signs[report.sade_sati.natal_moon_sign as keyof typeof t.zodiac.signs] || report.sade_sati.natal_moon_sign} स्थित जन्म चन्द्रमाबाट भाव {num(report.sade_sati.house_from_moon)})।
                  </>
                ) : (
                  <>
                    Saturn currently in <strong style={{ color: "var(--gold-bright)" }}>{report.sade_sati.saturn_sign}</strong> ({report.sade_sati.house_from_moon}th from Natal Moon in {report.sade_sati.natal_moon_sign}).
                  </>
                )}
              </p>

              {(report.sade_sati.is_ashtama_shani || report.sade_sati.is_kantaka_shani) && (
                <div style={{ marginTop: "var(--space-3)", display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
                  {report.sade_sati.is_ashtama_shani && (
                    <span className="badge badge-rose">{t.transits.ashtamaShani}</span>
                  )}
                  {report.sade_sati.is_kantaka_shani && (
                    <span className="badge badge-rose">{t.transits.kantakaShani}</span>
                  )}
                </div>
              )}
            </div>

            {/* Double Transit Card */}
            <div className="card" style={{ padding: "var(--space-5)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "var(--space-3)" }}>
                <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", letterSpacing: "0.06em" }}>{t.transits.doubleTransit}</span>
                <span className="badge badge-gold" style={{ gap: "4px" }}>
                  <Sparkles size={11} aria-hidden="true" /> {t.transits.auspicious}
                </span>
              </div>

              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--gold-bright)", marginBottom: "var(--space-1)" }}>
                {report.double_transit_houses.length > 0
                  ? `${t.transits.doubleTransitHouses} ${report.double_transit_houses.map((h) => num(h)).join(", ")}`
                  : t.transits.noDoubleTransit}
              </h3>
              <p style={{ fontSize: "var(--type-body)", color: "var(--text-mid)", lineHeight: 1.5 }}>
                {t.transits.doubleTransitDesc}
              </p>
            </div>
          </div>

          {/* Planetary Transits Table */}
          <div className="card" style={{ padding: "var(--space-5)" }}>
            <h3 style={{ fontSize: "var(--type-heading)", fontWeight: 700, marginBottom: "var(--space-3)", color: "var(--text-high)" }}>
              {t.transits.currentPositions}
            </h3>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--type-body)", textAlign: "left" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-mid)", fontSize: "var(--type-micro)" }}>
                    <th style={{ padding: "var(--space-2)" }}>{t.transits.tablePlanet}</th>
                    <th style={{ padding: "var(--space-2)" }}>{t.transits.tableTransitSign}</th>
                    <th style={{ padding: "var(--space-2)" }}>{t.transits.tableDegree}</th>
                    <th style={{ padding: "var(--space-2)" }}>{t.transits.tableFromLagna}</th>
                    <th style={{ padding: "var(--space-2)" }}>{t.transits.tableFromMoon}</th>
                    <th style={{ padding: "var(--space-2)" }}>{t.transits.tableMotion}</th>
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
                      <td style={{ padding: "var(--space-3) var(--space-2)", fontWeight: 600 }}>
                        {lang === "ne" ? (t.planets.names[p.name as keyof typeof t.planets.names] || p.name) : p.name}
                      </td>
                      <td style={{ padding: "var(--space-3) var(--space-2)" }}>
                        <span className="badge badge-cyan">
                          {lang === "ne" ? (t.zodiac.signs[p.sign as keyof typeof t.zodiac.signs] || p.sign) : p.sign}
                        </span>
                      </td>
                      <td style={{ padding: "var(--space-3) var(--space-2)", fontFamily: "var(--font-mono)", fontSize: "var(--type-data)" }}>
                        {deg(p.degree_in_sign)}
                      </td>
                      <td style={{ padding: "var(--space-3) var(--space-2)" }}>
                        {lang === "ne" ? `भाव ${num(p.house_from_asc)}` : `House ${p.house_from_asc}`}
                      </td>
                      <td style={{ padding: "var(--space-3) var(--space-2)", color: "var(--gold-bright)", fontWeight: 500 }}>
                        {lang === "ne" ? `भाव ${num(p.house_from_moon)}` : `House ${p.house_from_moon}`}
                      </td>
                      <td style={{ padding: "var(--space-3) var(--space-2)" }}>
                        {p.retrograde ? (
                          <span className="badge badge-rose">{t.transits.retrograde}</span>
                        ) : (
                          <span className="badge badge-emerald">{t.transits.direct}</span>
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
