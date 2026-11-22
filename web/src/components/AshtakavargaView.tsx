"use client";

import React, { useState } from "react";
import { AshtakavargaData } from "@/lib/types";
import { useLanguage } from "@/context/LanguageContext";
import { Sparkles, Grid3X3, Layers } from "lucide-react";

interface Props {
  ashtakavarga?: AshtakavargaData | null;
}

const ZODIAC_SIGNS = [
  "Aries",
  "Taurus",
  "Gemini",
  "Cancer",
  "Leo",
  "Virgo",
  "Libra",
  "Scorpio",
  "Sagittarius",
  "Capricorn",
  "Aquarius",
  "Pisces",
];

const PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"];

export const AshtakavargaView: React.FC<Props> = ({ ashtakavarga }) => {
  const { t, lang, num } = useLanguage();
  const [activeTab, setActiveTab] = useState<"sav" | "bav">("sav");

  // Normalize SAV array (12 elements corresponding to Aries..Pisces)
  const savList: number[] = React.useMemo(() => {
    if (!ashtakavarga) return [];
    if (ashtakavarga.sarvashtakavarga && ashtakavarga.sarvashtakavarga.length === 12) {
      return ashtakavarga.sarvashtakavarga;
    }
    if (ashtakavarga.sav) {
      return ZODIAC_SIGNS.map((sign) => ashtakavarga.sav?.[sign] ?? 0);
    }
    return [];
  }, [ashtakavarga]);

  // Normalize BAV map (Planet -> 12 numbers)
  const bavMap: Record<string, number[]> = React.useMemo(() => {
    const result: Record<string, number[]> = {};
    if (!ashtakavarga) return result;
    if (ashtakavarga.bhinnashtakavarga) {
      for (const [p, vals] of Object.entries(ashtakavarga.bhinnashtakavarga)) {
        result[p] = vals;
      }
    } else if (ashtakavarga.bav) {
      for (const [p, signObj] of Object.entries(ashtakavarga.bav)) {
        result[p] = ZODIAC_SIGNS.map((s) => signObj[s] ?? 0);
      }
    }
    return result;
  }, [ashtakavarga]);

  if (!ashtakavarga) {
    return null;
  }

  const grandTotal = ashtakavarga.grand_total || savList.reduce((acc, v) => acc + v, 0);

  const getStrengthBadge = (score: number) => {
    if (score >= 30) {
      return (
        <span className="badge badge-emerald" style={{ fontSize: "var(--type-micro)" }}>
          {t.ashtakavarga.strengthHigh}
        </span>
      );
    }
    if (score >= 25) {
      return (
        <span className="badge badge-gold" style={{ fontSize: "var(--type-micro)" }}>
          {t.ashtakavarga.strengthMedium}
        </span>
      );
    }
    return (
      <span className="badge badge-rose" style={{ fontSize: "var(--type-micro)" }}>
        {t.ashtakavarga.strengthLow}
      </span>
    );
  };

  return (
    <div className="card" style={{ padding: "var(--space-5)" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "var(--space-3)",
          marginBottom: "var(--space-4)",
        }}
      >
        <div>
          <h3
            style={{
              fontSize: "var(--type-heading)",
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              gap: "var(--space-2)",
              color: "var(--text-high)",
            }}
          >
            <Grid3X3 size={18} color="var(--gold-vivid)" aria-hidden="true" />
            {t.ashtakavarga.title}
          </h3>
          <p style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", marginTop: "2px" }}>
            {t.ashtakavarga.subtitle}
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <button
            type="button"
            onClick={() => setActiveTab("sav")}
            className={`chip${activeTab === "sav" ? " active" : ""}`}
            aria-pressed={activeTab === "sav"}
          >
            <Grid3X3 size={13} aria-hidden="true" />
            {t.ashtakavarga.sarvashtakavarga}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("bav")}
            className={`chip${activeTab === "bav" ? " active" : ""}`}
            aria-pressed={activeTab === "bav"}
          >
            <Layers size={13} aria-hidden="true" />
            {t.ashtakavarga.bhinnashtakavarga}
          </button>
          <span className="badge badge-gold" style={{ fontSize: "var(--type-micro)", marginLeft: "var(--space-1)" }}>
            {t.ashtakavarga.total}: {num(grandTotal)}
          </span>
        </div>
      </div>

      {/* Tab 1: Sarvashtakavarga Grid (12 Signs) */}
      {activeTab === "sav" && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 150px), 1fr))",
            gap: "var(--space-3)",
          }}
        >
          {ZODIAC_SIGNS.map((sign, idx) => {
            const score = savList[idx] ?? 0;
            const signLabel = lang === "ne" ? (t.zodiac.signs[sign as keyof typeof t.zodiac.signs] || sign) : sign;

            return (
              <div
                key={sign}
                style={{
                  background: "var(--bg-subtle)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-3)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "var(--space-1)",
                  textAlign: "center",
                }}
              >
                <div style={{ fontSize: "var(--type-label)", color: "var(--text-mid)", fontWeight: 600 }}>
                  {signLabel}
                </div>
                <div
                  style={{
                    fontSize: "1.45rem",
                    fontWeight: 700,
                    fontFamily: "var(--font-mono)",
                    color: score >= 30 ? "var(--emerald)" : score >= 25 ? "var(--gold-bright)" : "var(--rose)",
                  }}
                >
                  {num(score)}
                </div>
                <div style={{ marginTop: "auto" }}>
                  {getStrengthBadge(score)}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Tab 2: Bhinnashtakavarga Matrix Table */}
      {activeTab === "bav" && (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--type-micro)", textAlign: "center" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-mid)" }}>
                <th style={{ padding: "var(--space-2)", textAlign: "left" }}>{t.transits.tablePlanet}</th>
                {ZODIAC_SIGNS.map((sign) => (
                  <th key={sign} style={{ padding: "var(--space-2)" }}>
                    {lang === "ne" ? (t.zodiac.signs[sign as keyof typeof t.zodiac.signs] || sign).slice(0, 3) : sign.slice(0, 3)}
                  </th>
                ))}
                <th style={{ padding: "var(--space-2)", fontWeight: 700, color: "var(--gold-bright)" }}>
                  {t.ashtakavarga.total}
                </th>
              </tr>
            </thead>
            <tbody>
              {PLANETS.map((planet, pIdx) => {
                const planetName = lang === "ne" ? (t.planets.names[planet as keyof typeof t.planets.names] || planet) : planet;
                const points = bavMap[planet] || [];
                const planetTotal = points.reduce((acc, v) => acc + v, 0);

                return (
                  <tr
                    key={planet}
                    style={{
                      borderBottom: "1px solid var(--border-subtle)",
                      background: pIdx % 2 === 0 ? "transparent" : "var(--bg-subtle)",
                    }}
                  >
                    <td style={{ padding: "var(--space-2)", textAlign: "left", fontWeight: 600, color: "var(--text-high)" }}>
                      {planetName}
                    </td>
                    {ZODIAC_SIGNS.map((_, sIdx) => {
                      const bindu = points[sIdx] ?? 0;
                      return (
                        <td
                          key={sIdx}
                          style={{
                            padding: "var(--space-2)",
                            fontFamily: "var(--font-mono)",
                            color: bindu >= 4 ? "var(--emerald)" : "var(--rose)",
                            fontWeight: bindu >= 5 ? 700 : 400,
                          }}
                        >
                          {num(bindu)}
                        </td>
                      );
                    })}
                    <td style={{ padding: "var(--space-2)", fontWeight: 700, color: "var(--gold-bright)", fontFamily: "var(--font-mono)" }}>
                      {num(planetTotal)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr style={{ borderTop: "2px solid var(--border-subtle)", fontWeight: 700, background: "var(--gold-dim)" }}>
                <td style={{ padding: "var(--space-2)", textAlign: "left", color: "var(--gold-bright)" }}>
                  {t.ashtakavarga.sarvashtakavarga}
                </td>
                {ZODIAC_SIGNS.map((_, sIdx) => {
                  const sav = savList[sIdx] ?? 0;
                  return (
                    <td
                      key={sIdx}
                      style={{
                        padding: "var(--space-2)",
                        fontFamily: "var(--font-mono)",
                        color: sav >= 30 ? "var(--emerald)" : sav >= 25 ? "var(--gold-bright)" : "var(--rose)",
                      }}
                    >
                      {num(sav)}
                    </td>
                  );
                })}
                <td style={{ padding: "var(--space-2)", color: "var(--gold-bright)", fontFamily: "var(--font-mono)" }}>
                  {num(grandTotal)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
};
