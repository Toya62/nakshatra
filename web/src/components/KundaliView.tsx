"use client";

import React, { useState, useEffect, useRef } from "react";
import { ChartData } from "@/lib/types";
import { NorthIndianChart } from "@/components/NorthIndianChart";
import { SouthIndianChart } from "@/components/SouthIndianChart";
import { exportPngToFile, exportSvgToFile } from "@/lib/chartExport";
import { useLanguage } from "@/context/LanguageContext";
import { Download, Layers, Sparkles, Check, Image as ImageIcon } from "lucide-react";

interface Props {
  chart: ChartData;
  selectedVarga: string;
  onVargaChange: (varga: string) => void;
  size?: number;
}

const VARGAS = [
  "D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12",
  "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60",
];

export const KundaliView: React.FC<Props> = ({
  chart,
  selectedVarga,
  onVargaChange,
  size = 520,
}) => {
  const { t, lang } = useLanguage();
  const [chartStyle, setChartStyle] = useState<"north" | "south">("north");
  const [exporting, setExporting] = useState<"png" | "svg" | null>(null);
  const [exportSuccess, setExportSuccess] = useState(false);
  const svgRef = useRef<SVGSVGElement | null>(null);

  // Hydrate preference from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem("nakshatra_chart_style");
      if (saved === "north" || saved === "south") {
        setChartStyle(saved);
      }
    } catch {
      // Ignore storage restrictions
    }
  }, []);

  const handleStyleChange = (style: "north" | "south") => {
    setChartStyle(style);
    try {
      localStorage.setItem("nakshatra_chart_style", style);
    } catch {
      // Ignore storage restrictions
    }
  };

  const handleExport = async (format: "png" | "svg") => {
    if (!svgRef.current) return;
    setExporting(format);
    const filename = `nakshatra_${selectedVarga.toLowerCase()}_${chartStyle}_chart`;

    try {
      if (format === "png") {
        await exportPngToFile(svgRef.current, filename, 2);
      } else {
        exportSvgToFile(svgRef.current, filename);
      }
      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 2000);
    } catch (err) {
      console.error("Failed to export chart:", err);
    } finally {
      setExporting(null);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)", width: "100%", maxWidth: `${size}px` }}>
      {/* Top Chart Toolbar: Style Toggle & Export Action */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "var(--space-2)",
          flexWrap: "wrap",
          padding: "var(--space-2) var(--space-3)",
          background: "var(--bg-card)",
          border: "1px solid var(--border-card)",
          borderRadius: "var(--radius-md)",
        }}
      >
        {/* Chart Style Switcher */}
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-1)" }}>
          <span style={{ fontSize: "var(--type-micro)", color: "var(--text-low)", marginRight: "var(--space-1)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            {lang === "ne" ? "शैली" : "Style"}:
          </span>
          <button
            type="button"
            onClick={() => handleStyleChange("north")}
            className={`chip${chartStyle === "north" ? " active" : ""}`}
            style={{ fontSize: "var(--type-micro)", padding: "3px 8px" }}
            title="North Indian diamond format"
          >
            ⟐ {lang === "ne" ? "उत्तर" : "North"}
          </button>
          <button
            type="button"
            onClick={() => handleStyleChange("south")}
            className={`chip${chartStyle === "south" ? " active" : ""}`}
            style={{ fontSize: "var(--type-micro)", padding: "3px 8px" }}
            title="South Indian square grid format"
          >
            ⊞ {lang === "ne" ? "दक्षिण" : "South"}
          </button>
        </div>

        {/* Quick Export Actions */}
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-1)" }}>
          <button
            type="button"
            onClick={() => handleExport("png")}
            disabled={exporting !== null}
            className="btn-ghost"
            style={{
              fontSize: "var(--type-micro)",
              padding: "4px 8px",
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              borderRadius: "var(--radius-sm)",
            }}
            title="Export high-resolution PNG"
          >
            {exportSuccess ? (
              <Check size={12} color="var(--emerald)" />
            ) : (
              <ImageIcon size={12} color="var(--gold-vivid)" />
            )}
            {exporting === "png" ? "Saving..." : "PNG"}
          </button>

          <button
            type="button"
            onClick={() => handleExport("svg")}
            disabled={exporting !== null}
            className="btn-ghost"
            style={{
              fontSize: "var(--type-micro)",
              padding: "4px 8px",
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              borderRadius: "var(--radius-sm)",
            }}
            title="Export vector SVG"
          >
            <Download size={12} color="var(--cyan-vivid)" />
            {exporting === "svg" ? "Saving..." : "SVG"}
          </button>
        </div>
      </div>

      {/* Varga Selector Strip — wraps to a second row so all 16 divisionals
          stay visible; the previous horizontal scroll hid D30/D40/D45/D60
          behind an invisible scrollbar. */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "var(--space-1)",
          maxWidth: "100%",
          width: "100%",
          padding: "4px 2px",
        }}
        aria-label="Divisional chart selector"
      >
        <Layers size={13} color="var(--text-low)" aria-hidden="true" style={{ flexShrink: 0, marginRight: "4px" }} />
        {VARGAS.map((v) => (
          <button
            key={v}
            onClick={() => onVargaChange(v)}
            className={`chip${selectedVarga === v ? " active" : ""}`}
            style={{ flexShrink: 0, padding: "3px 8px", fontSize: "var(--type-micro)" }}
            aria-pressed={selectedVarga === v}
          >
            {v}
          </button>
        ))}
      </div>

      {/* Render Chart Format */}
      {chartStyle === "north" ? (
        <NorthIndianChart ref={svgRef} chart={chart} varga={selectedVarga} size={size} />
      ) : (
        <SouthIndianChart ref={svgRef} chart={chart} varga={selectedVarga} size={size} />
      )}
    </div>
  );
};
