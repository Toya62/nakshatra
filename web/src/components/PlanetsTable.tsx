"use client";

import React from "react";
import { ChartData } from "@/lib/types";
import { Download, Table } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

interface Props {
  chart: ChartData;
}

// Classical benefic / malefic classification
const BENEFICS  = new Set(["Jupiter", "Venus", "Moon", "Mercury"]);
const MALEFICS  = new Set(["Sun", "Mars", "Saturn", "Rahu", "Ketu"]);

function planetColor(name: string, isAsc: boolean): string {
  if (isAsc) return "var(--graha-asc, var(--gold-bright))";
  if (BENEFICS.has(name))  return "var(--emerald, #6ee7b7)";
  if (MALEFICS.has(name))  return "var(--rose, #fda4af)";
  return "var(--text-high)";
}

export const PlanetsTable: React.FC<Props> = ({ chart }) => {
  const { t, lang, num } = useLanguage();
  const bodies = [
    {
      name: "Ascendant (Lagna)",
      sign: chart.ascendant.sign,
      degree: chart.ascendant.degree_in_sign,
      nakshatra: chart.ascendant.nakshatra,
      pada: chart.ascendant.pada,
      lord: chart.ascendant.nakshatra_lord,
      house: 1,
      retrograde: false,
      isAsc: true,
    },
    ...chart.planets.map((p) => ({
      name: p.name,
      sign: p.sign,
      degree: p.degree_in_sign,
      nakshatra: p.nakshatra,
      pada: p.pada,
      lord: p.nakshatra_lord,
      house: p.house,
      retrograde: p.retrograde,
      isAsc: false,
    })),
    {
      name: "Rahu",
      sign: chart.rahu.sign,
      degree: chart.rahu.degree_in_sign,
      nakshatra: chart.rahu.nakshatra,
      pada: chart.rahu.pada,
      lord: chart.rahu.nakshatra_lord,
      house: chart.rahu.house,
      retrograde: true,
      isAsc: false,
    },
    {
      name: "Ketu",
      sign: chart.ketu.sign,
      degree: chart.ketu.degree_in_sign,
      nakshatra: chart.ketu.nakshatra,
      pada: chart.ketu.pada,
      lord: chart.ketu.nakshatra_lord,
      house: chart.ketu.house,
      retrograde: true,
      isAsc: false,
    },
  ];

  const handleDownloadJSON = () => {
    const blob = new Blob([JSON.stringify(chart, null, 2)], { type: "application/json" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url;
    a.download = "nakshatra_chart.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="card" style={{ padding: "var(--space-5)" }}>
      {/* Header */}
      <div className="section-header">
        <h4 className="section-title" style={{ fontSize: "var(--type-heading)" }}>
          <Table size={15} color="var(--gold-vivid)" aria-hidden="true" />
          {lang === "ne" ? "ग्रह स्थिति तालिका" : "Planetary Ephemeris"}
          <span
            className="badge badge-gold"
            style={{ fontSize: "var(--type-micro)", marginLeft: "var(--space-2)" }}
          >
            {lang === "ne" ? "निरयण" : "Nirayana"}
          </span>
        </h4>
        <button
          onClick={handleDownloadJSON}
          className="btn-ghost"
          style={{ fontSize: "var(--type-label)", padding: "5px 10px" }}
          title="Download chart as JSON"
        >
          <Download size={13} aria-hidden="true" />
          JSON
        </button>
      </div>

      {/* Table */}
      <div style={{ overflowX: "auto", WebkitOverflowScrolling: "touch" }}>
        <table
          style={{
            width: "100%",
            minWidth: "500px",
            borderCollapse: "collapse",
            fontSize: "var(--type-label)",
            textAlign: "left",
          }}
          aria-label="Planetary positions"
        >
          <thead>
            <tr
              style={{
                borderBottom: "1px solid var(--gold-border)",
                color: "var(--text-low)",
                fontSize: "var(--type-micro)",
                letterSpacing: "0.06em",
                textTransform: "uppercase",
              }}
            >
              {(lang === "ne"
                ? ["ग्रह", "राशि", "अंश", "भाव", "नक्षत्र", "पाद", "स्वामी", "गति"]
                : ["Graha", "Rasi", "Degree", "Bhava", "Nakshatra", "Pada", "Lord", "Motion"]
              ).map((h) => (
                <th key={h} style={{ padding: "8px 8px 10px", fontWeight: 600 }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {bodies.map((b, idx) => {
              const even = idx % 2 === 0;
              return (
                <tr
                  key={`${b.name}-${idx}`}
                  style={{
                    borderBottom: "1px solid var(--border-subtle)",
                    background: b.isAsc
                      ? "linear-gradient(90deg, var(--gold-dim) 0%, transparent 100%)"
                      : even
                      ? "var(--bg-subtle)"
                      : "transparent",
                    transition: "background 0.15s",
                  }}
                >
                  {/* Graha */}
                  <td
                    style={{
                      padding: "9px 8px",
                      fontWeight: 600,
                      color: planetColor(b.name, b.isAsc),
                      whiteSpace: "nowrap",
                    }}
                  >
                    {lang === "ne" ? (t.planets.names[b.name.replace(/ \(.*\)/, "") as keyof typeof t.planets.names] || b.name) : b.name}
                  </td>

                  {/* Sign */}
                  <td style={{ padding: "9px 8px" }}>
                    <span
                      className="chip"
                      style={{
                        fontSize: "var(--type-micro)",
                        padding: "2px 8px",
                        background: "var(--bg-subtle)",
                        borderColor: "var(--border-subtle)",
                        color: "var(--text-high)",
                        cursor: "default",
                      }}
                    >
                      {lang === "ne" ? (t.zodiac.signs[b.sign as keyof typeof t.zodiac.signs] || b.sign) : b.sign}
                    </span>
                  </td>

                  {/* Degree */}
                  <td
                    className="data-mono"
                    style={{ padding: "9px 8px", color: "var(--text-mid)" }}
                  >
                    {num(b.degree.toFixed(2))}°
                  </td>

                  {/* House */}
                  <td
                    style={{
                      padding: "9px 8px",
                      fontWeight: 600,
                      color: "var(--text-high)",
                      fontFamily: "var(--font-mono)",
                      fontSize: "var(--type-data)",
                    }}
                  >
                    {lang === "ne" ? `भाव ${num(b.house)}` : `H${b.house}`}
                  </td>

                  {/* Nakshatra */}
                  <td style={{ padding: "9px 8px", color: "var(--text-high)", whiteSpace: "nowrap" }}>
                    {b.nakshatra}
                  </td>

                  {/* Pada */}
                  <td
                    className="data-mono"
                    style={{ padding: "9px 8px", color: "var(--text-mid)" }}
                  >
                    {num(b.pada)}
                  </td>

                  {/* Lord */}
                  <td style={{ padding: "9px 8px", color: "var(--text-mid)" }}>
                    {lang === "ne" ? (t.planets.names[b.lord as keyof typeof t.planets.names] || b.lord) : b.lord}
                  </td>

                  {/* Motion */}
                  <td style={{ padding: "9px 8px" }}>
                    {b.retrograde ? (
                      <span className="badge badge-rose">{lang === "ne" ? "℞ वक्री" : "℞ Retro"}</span>
                    ) : (
                      <span className="badge badge-emerald">{lang === "ne" ? "मार्गी" : "Direct"}</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
