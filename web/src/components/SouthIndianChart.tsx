"use client";

import React, { useMemo } from "react";
import { ChartData } from "@/lib/types";

interface Props {
  chart: ChartData;
  varga?: string;
  size?: number;
}

const SIGN_CELLS: Record<string, { row: number; col: number; num: number }> = {
  Pisces: { row: 0, col: 0, num: 12 },
  Aries: { row: 0, col: 1, num: 1 },
  Taurus: { row: 0, col: 2, num: 2 },
  Gemini: { row: 0, col: 3, num: 3 },
  Cancer: { row: 1, col: 3, num: 4 },
  Leo: { row: 2, col: 3, num: 5 },
  Virgo: { row: 3, col: 3, num: 6 },
  Libra: { row: 3, col: 2, num: 7 },
  Scorpio: { row: 3, col: 1, num: 8 },
  Sagittarius: { row: 3, col: 0, num: 9 },
  Capricorn: { row: 2, col: 0, num: 10 },
  Aquarius: { row: 1, col: 0, num: 11 },
};

export const SouthIndianChart: React.FC<Props> = ({ chart, varga = "D1", size = 520 }) => {
  const cellSize = size / 4;

  const placements = useMemo(() => {
    const map: Record<string, { label: string; isAsc?: boolean; isRetro?: boolean; degree?: string }[]> = {
      Aries: [], Taurus: [], Gemini: [], Cancer: [], Leo: [], Virgo: [],
      Libra: [], Scorpio: [], Sagittarius: [], Capricorn: [], Aquarius: [], Pisces: [],
    };

    const vKey = varga.toUpperCase();
    const vData = chart.vargas && chart.vargas[vKey];

    if (vData && vKey !== "D1") {
      const ascSign = vData["Ascendant"] || chart.ascendant.sign;
      if (map[ascSign]) map[ascSign].push({ label: "Asc", isAsc: true });

      const allPlanets = [...chart.planets, chart.rahu, chart.ketu];
      for (const p of allPlanets) {
        let vName = p.name;
        let abbr = p.name.slice(0, 2);
        if (p.name === "North Node" || p.name === "Rahu") { vName = "North Node"; abbr = "Ra"; }
        else if (p.name === "South Node" || p.name === "Ketu") { vName = "South Node"; abbr = "Ke"; }
        else if (p.name === "Mercury") abbr = "Me";
        else if (p.name === "Jupiter") abbr = "Ju";
        else if (p.name === "Venus") abbr = "Ve";
        else if (p.name === "Saturn") abbr = "Sa";
        else if (p.name === "Sun") abbr = "Su";
        else if (p.name === "Moon") abbr = "Mo";
        else if (p.name === "Mars") abbr = "Ma";

        const pSign = vData[vName] || p.sign;
        if (map[pSign]) {
          map[pSign].push({
            label: abbr,
            isRetro: p.retrograde,
          });
        }
      }
    } else {
      // D1 direct positions
      if (map[chart.ascendant.sign]) {
        map[chart.ascendant.sign].push({
          label: "Asc",
          isAsc: true,
          degree: `${chart.ascendant.degree_in_sign.toFixed(1)}°`,
        });
      }

      const allPlanets = [...chart.planets, chart.rahu, chart.ketu];
      for (const p of allPlanets) {
        let abbr = p.name.slice(0, 2);
        if (p.name.includes("Rahu") || p.name.includes("North")) abbr = "Ra";
        else if (p.name.includes("Ketu") || p.name.includes("South")) abbr = "Ke";
        else if (p.name === "Mercury") abbr = "Me";
        else if (p.name === "Jupiter") abbr = "Ju";
        else if (p.name === "Venus") abbr = "Ve";
        else if (p.name === "Saturn") abbr = "Sa";
        else if (p.name === "Sun") abbr = "Su";
        else if (p.name === "Moon") abbr = "Mo";
        else if (p.name === "Mars") abbr = "Ma";

        if (map[p.sign]) {
          map[p.sign].push({
            label: abbr,
            isRetro: p.retrograde,
            degree: `${p.degree_in_sign.toFixed(1)}°`,
          });
        }
      }
    }

    return map;
  }, [chart, varga]);

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", padding: "10px" }}>
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${size} ${size}`}
        style={{
          maxWidth: `${size}px`,
          filter: "drop-shadow(0 12px 36px rgba(0,0,0,0.6))",
          borderRadius: "16px",
          background: "linear-gradient(145deg, #090c15 0%, #0c1020 100%)",
          border: "2px solid rgba(229, 185, 76, 0.35)",
        }}
      >
        <defs>
          <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(229, 185, 76, 0.12)" />
            <stop offset="100%" stopColor="rgba(12, 16, 32, 0)" />
          </radialGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Outer and Grid Lines */}
        <rect x="0" y="0" width={size} height={size} fill="none" stroke="rgba(229, 185, 76, 0.4)" strokeWidth="2" />

        {/* 4x4 Grid lines */}
        {[1, 2, 3].map((i) => (
          <React.Fragment key={i}>
            <line
              x1={i * cellSize} y1="0"
              x2={i * cellSize} y2={size}
              stroke="rgba(229, 185, 76, 0.25)"
              strokeWidth="1.5"
            />
            <line
              x1="0" y1={i * cellSize}
              x2={size} y2={i * cellSize}
              stroke="rgba(229, 185, 76, 0.25)"
              strokeWidth="1.5"
            />
          </React.Fragment>
        ))}

        {/* Center 2x2 Chamber */}
        <rect
          x={cellSize}
          y={cellSize}
          width={cellSize * 2}
          height={cellSize * 2}
          fill="url(#centerGlow)"
          stroke="rgba(229, 185, 76, 0.5)"
          strokeWidth="1.5"
        />

        {/* Center Astrological Stamp */}
        <g transform={`translate(${size / 2}, ${size / 2})`}>
          <circle r={cellSize * 0.75} fill="none" stroke="rgba(229, 185, 76, 0.15)" strokeDasharray="4 4" />
          <polygon
            points={`0,-${cellSize * 0.5} ${cellSize * 0.43},${cellSize * 0.25} -${cellSize * 0.43},${cellSize * 0.25}`}
            fill="none"
            stroke="rgba(56, 189, 248, 0.2)"
            strokeWidth="1"
          />
          <polygon
            points={`0,${cellSize * 0.5} ${cellSize * 0.43},-${cellSize * 0.25} -${cellSize * 0.43},-${cellSize * 0.25}`}
            fill="none"
            stroke="rgba(229, 185, 76, 0.2)"
            strokeWidth="1"
          />
          <text
            y="-22"
            textAnchor="middle"
            fill="#fbe285"
            fontSize="18"
            fontWeight="700"
            fontFamily="'Cinzel', serif"
            letterSpacing="3"
          >
            NAKSHATRA
          </text>
          <text
            y="2"
            textAnchor="middle"
            fill="#38bdf8"
            fontSize="14"
            fontWeight="600"
            fontFamily="'Outfit', sans-serif"
          >
            {varga.toUpperCase()} {varga === "D1" ? "RASI" : varga === "D9" ? "NAVAMSA" : "VARGA"}
          </text>
          <text
            y="22"
            textAnchor="middle"
            fill="#94a3b8"
            fontSize="11"
            fontFamily="'Outfit', sans-serif"
          >
            Asc: {chart.ascendant.sign} ({chart.ascendant.degree_in_sign.toFixed(1)}°)
          </text>
          <text
            y="38"
            textAnchor="middle"
            fill="#64748b"
            fontSize="9"
            fontFamily="'JetBrains Mono', monospace"
          >
            Lahiri (JHora)
          </text>
        </g>

        {/* Outer 12 Zodiac Houses */}
        {Object.entries(SIGN_CELLS).map(([signName, { row, col, num }]) => {
          const x = col * cellSize;
          const y = row * cellSize;
          const bodies = placements[signName] || [];

          return (
            <g key={signName} transform={`translate(${x}, ${y})`}>
              {/* Sign Header & Index */}
              <text
                x="8"
                y="16"
                fill="#94a3b8"
                fontSize="11"
                fontWeight="600"
                fontFamily="'Outfit', sans-serif"
              >
                {signName.slice(0, 3).toUpperCase()}
              </text>
              <text
                x={cellSize - 8}
                y="16"
                textAnchor="end"
                fill="rgba(229, 185, 76, 0.5)"
                fontSize="10"
                fontFamily="'JetBrains Mono', monospace"
              >
                {num}
              </text>

              {/* Planets in this sign */}
              <g transform="translate(10, 32)">
                {bodies.map((b, idx) => {
                  const lineY = idx * 17;
                  return (
                    <g key={idx} transform={`translate(0, ${lineY})`}>
                      {b.isAsc ? (
                        <rect
                          x="-4"
                          y="-10"
                          width="34"
                          height="15"
                          rx="3"
                          fill="rgba(244, 63, 94, 0.25)"
                          stroke="rgba(244, 63, 94, 0.7)"
                          strokeWidth="0.8"
                        />
                      ) : null}
                      <text
                        x="0"
                        y="0"
                        fill={b.isAsc ? "#fda4af" : b.isRetro ? "#f59e0b" : "#e2e8f0"}
                        fontSize="12"
                        fontWeight={b.isAsc ? "700" : "600"}
                        fontFamily="'Outfit', sans-serif"
                      >
                        {b.label}
                        {b.isRetro ? <tspan fill="#f59e0b" fontSize="9"> (R)</tspan> : null}
                      </text>
                      {b.degree ? (
                        <text
                          x={cellSize - 28}
                          y="0"
                          textAnchor="end"
                          fill="#64748b"
                          fontSize="9.5"
                          fontFamily="'JetBrains Mono', monospace"
                        >
                          {b.degree}
                        </text>
                      ) : null}
                    </g>
                  );
                })}
              </g>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
