"use client";

import React from "react";
import { ChartData } from "@/lib/types";
import { Download, Table } from "lucide-react";

interface Props {
  chart: ChartData;
}

export const PlanetsTable: React.FC<Props> = ({ chart }) => {
  const bodies = [
    {
      name: "Ascendant (Lagna)",
      sign: chart.ascendant.sign,
      degree: chart.ascendant.degree_in_sign,
      longitude: chart.ascendant.longitude,
      nakshatra: chart.ascendant.nakshatra,
      pada: chart.ascendant.pada,
      lord: chart.ascendant.nakshatra_lord,
      house: 1,
      retrograde: false,
      speed: 0,
      isAsc: true,
    },
    ...chart.planets.map((p) => ({
      name: p.name,
      sign: p.sign,
      degree: p.degree_in_sign,
      longitude: p.longitude,
      nakshatra: p.nakshatra,
      pada: p.pada,
      lord: p.nakshatra_lord,
      house: p.house,
      retrograde: p.retrograde,
      speed: p.speed,
      isAsc: false,
    })),
    {
      name: "Rahu (North Node)",
      sign: chart.rahu.sign,
      degree: chart.rahu.degree_in_sign,
      longitude: chart.rahu.longitude,
      nakshatra: chart.rahu.nakshatra,
      pada: chart.rahu.pada,
      lord: chart.rahu.nakshatra_lord,
      house: chart.rahu.house,
      retrograde: true,
      speed: chart.rahu.speed,
      isAsc: false,
    },
    {
      name: "Ketu (South Node)",
      sign: chart.ketu.sign,
      degree: chart.ketu.degree_in_sign,
      longitude: chart.ketu.longitude,
      nakshatra: chart.ketu.nakshatra,
      pada: chart.ketu.pada,
      lord: chart.ketu.nakshatra_lord,
      house: chart.ketu.house,
      retrograde: true,
      speed: chart.ketu.speed,
      isAsc: false,
    },
  ];

  const downloadFile = (content: string, fileName: string, type: string) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadJSON = () => {
    downloadFile(JSON.stringify(chart, null, 2), "nakshatra_chart.json", "application/json");
  };

  return (
    <div className="glass-panel" style={{ padding: "20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h4 className="title-serif gold-gradient-text" style={{ fontSize: "1.05rem", display: "flex", alignItems: "center", gap: "8px" }}>
          <Table size={16} /> Planetary Ephemeris (Nirayana)
        </h4>

        <div style={{ display: "flex", gap: "8px" }}>
          <button onClick={handleDownloadJSON} className="btn-secondary" style={{ fontSize: "0.8rem", padding: "6px 12px" }}>
            <Download size={13} /> JSON
          </button>
        </div>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", textAlign: "left" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid rgba(229, 185, 76, 0.2)", color: "var(--text-muted)", fontSize: "0.78rem", letterSpacing: "0.05em" }}>
              <th style={{ padding: "10px 8px" }}>GRAHA</th>
              <th style={{ padding: "10px 8px" }}>RASI (SIGN)</th>
              <th style={{ padding: "10px 8px" }}>DEGREE</th>
              <th style={{ padding: "10px 8px" }}>BHAVA</th>
              <th style={{ padding: "10px 8px" }}>NAKSHATRA</th>
              <th style={{ padding: "10px 8px" }}>PADA</th>
              <th style={{ padding: "10px 8px" }}>LORD</th>
              <th style={{ padding: "10px 8px" }}>MOTION</th>
            </tr>
          </thead>
          <tbody>
            {bodies.map((b, idx) => (
              <tr
                key={`${b.name}-${idx}`}
                style={{
                  borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                  background: b.isAsc ? "rgba(229, 185, 76, 0.05)" : "transparent",
                }}
              >
                <td style={{ padding: "10px 8px", fontWeight: 600, color: b.isAsc ? "#fbe285" : "var(--text-main)" }}>
                  {b.name}
                </td>
                <td style={{ padding: "10px 8px" }}>
                  <span className="badge badge-cyan">{b.sign}</span>
                </td>
                <td style={{ padding: "10px 8px", fontFamily: "var(--font-mono)" }}>
                  {b.degree.toFixed(2)}°
                </td>
                <td style={{ padding: "10px 8px", fontWeight: 600 }}>
                  House {b.house}
                </td>
                <td style={{ padding: "10px 8px", color: "#f1f5f9" }}>
                  {b.nakshatra}
                </td>
                <td style={{ padding: "10px 8px", fontFamily: "var(--font-mono)" }}>
                  {b.pada}
                </td>
                <td style={{ padding: "10px 8px", color: "var(--text-muted)" }}>
                  {b.lord}
                </td>
                <td style={{ padding: "10px 8px" }}>
                  {b.retrograde ? (
                    <span className="badge badge-rose">Retrograde (R)</span>
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
  );
};
