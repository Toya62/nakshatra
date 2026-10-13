"use client";

import React, { useMemo } from "react";
import { ChartData } from "@/lib/types";

interface Props {
  chart: ChartData;
  varga?: string;
  size?: number;
}

const SIGN_NAMES_TO_NUM: Record<string, number> = {
  Aries: 1, Taurus: 2, Gemini: 3, Cancer: 4, Leo: 5, Virgo: 6,
  Libra: 7, Scorpio: 8, Sagittarius: 9, Capricorn: 10, Aquarius: 11, Pisces: 12,
};

const NUM_TO_SIGN_NAME: Record<number, string> = {
  1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer", 5: "Leo", 6: "Virgo",
  7: "Libra", 8: "Scorpio", 9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces",
};

export const NorthIndianChart: React.FC<Props> = ({ chart, varga = "D1", size = 520 }) => {
  const w = size;
  const h = size;
  const cx = w / 2;
  const cy = h / 2;

  // Determine Ascendant sign
  const vKey = varga.toUpperCase();
  const vData = chart.vargas && chart.vargas[vKey];
  const ascSignName = (vData && vKey !== "D1")
    ? (vData["Ascendant"] || chart.ascendant.sign)
    : chart.ascendant.sign;
  const ascSignNum = SIGN_NAMES_TO_NUM[ascSignName] || 1;

  // Map each house (1 to 12) to its sign number and bodies
  const houseData = useMemo(() => {
    // Map sign name -> array of planet badges
    const signPlanets: Record<string, { label: string; isAsc?: boolean; isRetro?: boolean; degree?: string }[]> = {
      Aries: [], Taurus: [], Gemini: [], Cancer: [], Leo: [], Virgo: [],
      Libra: [], Scorpio: [], Sagittarius: [], Capricorn: [], Aquarius: [], Pisces: [],
    };

    if (vData && vKey !== "D1") {
      signPlanets[ascSignName]?.push({ label: "Asc", isAsc: true });
      const allPlanets = [...chart.planets, chart.rahu, chart.ketu];
      for (const p of allPlanets) {
        let vName = p.name;
        let abbr = p.name.slice(0, 2);
        if (p.name.includes("Rahu") || p.name.includes("North")) { vName = "North Node"; abbr = "Ra"; }
        else if (p.name.includes("Ketu") || p.name.includes("South")) { vName = "South Node"; abbr = "Ke"; }
        else if (p.name === "Mercury") abbr = "Me";
        else if (p.name === "Jupiter") abbr = "Ju";
        else if (p.name === "Venus") abbr = "Ve";
        else if (p.name === "Saturn") abbr = "Sa";
        else if (p.name === "Sun") abbr = "Su";
        else if (p.name === "Moon") abbr = "Mo";
        else if (p.name === "Mars") abbr = "Ma";

        const pSign = vData[vName] || p.sign;
        if (signPlanets[pSign]) {
          signPlanets[pSign].push({
            label: abbr,
            isRetro: p.retrograde,
          });
        }
      }
    } else {
      signPlanets[chart.ascendant.sign]?.push({
        label: "Asc",
        isAsc: true,
        degree: `${chart.ascendant.degree_in_sign.toFixed(1)}°`,
      });

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

        if (signPlanets[p.sign]) {
          signPlanets[p.sign].push({
            label: abbr,
            isRetro: p.retrograde,
            degree: `${p.degree_in_sign.toFixed(1)}°`,
          });
        }
      }
    }

    // Build array for houses 1 to 12
    const houses: { houseNum: number; signNum: number; signName: string; planets: typeof signPlanets[string] }[] = [];
    for (let houseNum = 1; houseNum <= 12; houseNum++) {
      const signNum = ((ascSignNum - 1 + (houseNum - 1)) % 12) + 1;
      const signName = NUM_TO_SIGN_NAME[signNum];
      houses.push({
        houseNum,
        signNum,
        signName,
        planets: signPlanets[signName] || [],
      });
    }
    return houses;
  }, [chart, varga, ascSignName, ascSignNum, vData, vKey]);

  // Chamber geometry definitions (counter-clockwise Vedic house sequence)
  const chambers = [
    // House 1 (Top diamond)
    {
      house: 1,
      polygon: `${cx},0 ${cx / 2},${cy / 2} ${cx},${cy} ${cx * 1.5},${cy / 2}`,
      labelPos: { x: cx, y: 28 },
      contentPos: { x: cx, y: cy * 0.45 },
      signPos: { x: cx, y: cy - 14 },
      isKendra: true,
    },
    // House 2 (Top-left triangle)
    {
      house: 2,
      polygon: `0,0 ${cx},0 ${cx / 2},${cy / 2}`,
      labelPos: { x: cx * 0.35, y: 20 },
      contentPos: { x: cx * 0.42, y: cy * 0.32 },
      signPos: { x: cx * 0.55, y: cy * 0.42 },
      isKendra: false,
    },
    // House 3 (Left-upper triangle)
    {
      house: 3,
      polygon: `0,0 0,${cy} ${cx / 2},${cy / 2}`,
      labelPos: { x: 20, y: cy * 0.35 },
      contentPos: { x: cx * 0.32, y: cy * 0.5 },
      signPos: { x: cx * 0.42, y: cy * 0.6 },
      isKendra: false,
    },
    // House 4 (Left diamond)
    {
      house: 4,
      polygon: `0,${cy} ${cx / 2},${cy / 2} ${cx},${cy} ${cx / 2},${cy * 1.5}`,
      labelPos: { x: 28, y: cy },
      contentPos: { x: cx * 0.45, y: cy },
      signPos: { x: cx - 18, y: cy },
      isKendra: true,
    },
    // House 5 (Left-lower triangle)
    {
      house: 5,
      polygon: `0,${cy} 0,${h} ${cx / 2},${cy * 1.5}`,
      labelPos: { x: 20, y: cy * 1.65 },
      contentPos: { x: cx * 0.32, y: cy * 1.5 },
      signPos: { x: cx * 0.42, y: cy * 1.4 },
      isKendra: false,
    },
    // House 6 (Bottom-left triangle)
    {
      house: 6,
      polygon: `0,${h} ${cx},${h} ${cx / 2},${cy * 1.5}`,
      labelPos: { x: cx * 0.35, y: h - 14 },
      contentPos: { x: cx * 0.42, y: cy * 1.68 },
      signPos: { x: cx * 0.55, y: cy * 1.58 },
      isKendra: false,
    },
    // House 7 (Bottom diamond)
    {
      house: 7,
      polygon: `${cx},${h} ${cx / 2},${cy * 1.5} ${cx},${cy} ${cx * 1.5},${cy * 1.5}`,
      labelPos: { x: cx, y: h - 18 },
      contentPos: { x: cx, y: cy * 1.55 },
      signPos: { x: cx, y: cy + 24 },
      isKendra: true,
    },
    // House 8 (Bottom-right triangle)
    {
      house: 8,
      polygon: `${cx},${h} ${w},${h} ${cx * 1.5},${cy * 1.5}`,
      labelPos: { x: cx * 1.65, y: h - 14 },
      contentPos: { x: cx * 1.58, y: cy * 1.68 },
      signPos: { x: cx * 1.45, y: cy * 1.58 },
      isKendra: false,
    },
    // House 9 (Right-lower triangle)
    {
      house: 9,
      polygon: `${w},${h} ${w},${cy} ${cx * 1.5},${cy * 1.5}`,
      labelPos: { x: w - 20, y: cy * 1.65 },
      contentPos: { x: cx * 1.68, y: cy * 1.5 },
      signPos: { x: cx * 1.58, y: cy * 1.4 },
      isKendra: false,
    },
    // House 10 (Right diamond)
    {
      house: 10,
      polygon: `${w},${cy} ${cx * 1.5},${cy * 1.5} ${cx},${cy} ${cx * 1.5},${cy / 2}`,
      labelPos: { x: w - 28, y: cy },
      contentPos: { x: cx * 1.55, y: cy },
      signPos: { x: cx + 18, y: cy },
      isKendra: true,
    },
    // House 11 (Right-upper triangle)
    {
      house: 11,
      polygon: `${w},${cy} ${w},0 ${cx * 1.5},${cy / 2}`,
      labelPos: { x: w - 20, y: cy * 0.35 },
      contentPos: { x: cx * 1.68, y: cy * 0.5 },
      signPos: { x: cx * 1.58, y: cy * 0.6 },
      isKendra: false,
    },
    // House 12 (Top-right triangle)
    {
      house: 12,
      polygon: `${w},0 ${cx},0 ${cx * 1.5},${cy / 2}`,
      labelPos: { x: cx * 1.65, y: 20 },
      contentPos: { x: cx * 1.58, y: cy * 0.32 },
      signPos: { x: cx * 1.45, y: cy * 0.42 },
      isKendra: false,
    },
  ];

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", padding: "10px" }}>
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${w} ${h}`}
        style={{
          maxWidth: `${size}px`,
          filter: "drop-shadow(0 12px 36px rgba(0,0,0,0.6))",
          borderRadius: "16px",
          background: "linear-gradient(145deg, #090c15 0%, #0c1020 100%)",
          border: "2px solid rgba(229, 185, 76, 0.35)",
        }}
      >
        <defs>
          <radialGradient id="northKendraGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(229, 185, 76, 0.15)" />
            <stop offset="100%" stopColor="rgba(12, 16, 32, 0.02)" />
          </radialGradient>
        </defs>

        {/* Outer Square */}
        <rect x="0" y="0" width={w} height={h} fill="none" stroke="rgba(229, 185, 76, 0.4)" strokeWidth="2" />

        {/* Two Main Cross Diagonals */}
        <line x1="0" y1="0" x2={w} y2={h} stroke="rgba(229, 185, 76, 0.3)" strokeWidth="1.5" />
        <line x1="0" y1={h} x2={w} y2="0" stroke="rgba(229, 185, 76, 0.3)" strokeWidth="1.5" />

        {/* Center Rhombus (Diamond) Lines */}
        <polygon
          points={`${cx},0 ${w},${cy} ${cx},${h} 0,${cy}`}
          fill="none"
          stroke="rgba(229, 185, 76, 0.55)"
          strokeWidth="2"
        />

        {/* Render each chamber */}
        {chambers.map((ch) => {
          const data = houseData[ch.house - 1];
          const planets = data ? data.planets : [];

          return (
            <g key={ch.house}>
              {/* Kendra chamber subtle gold gradient */}
              {ch.isKendra && (
                <polygon
                  points={ch.polygon}
                  fill="url(#northKendraGlow)"
                />
              )}

              {/* Rasi Number (Classical Vedic marker) */}
              <text
                x={ch.signPos.x}
                y={ch.signPos.y}
                textAnchor="middle"
                fill="rgba(229, 185, 76, 0.7)"
                fontSize="13"
                fontWeight="700"
                fontFamily="'Cinzel', serif"
              >
                {data.signNum}
              </text>

              {/* House Title (e.g. H1 / Lagna) */}
              {ch.house === 1 && (
                <text
                  x={ch.labelPos.x}
                  y={ch.labelPos.y}
                  textAnchor="middle"
                  fill="#fbe285"
                  fontSize="12"
                  fontWeight="700"
                  fontFamily="'Cinzel', serif"
                  letterSpacing="1.5"
                >
                  LAGNA
                </text>
              )}

              {/* Planets inside this house */}
              <g transform={`translate(${ch.contentPos.x}, ${ch.contentPos.y})`}>
                {planets.map((p, pIdx) => {
                  const lineY = (pIdx - (planets.length - 1) / 2) * 16;
                  return (
                    <g key={pIdx} transform={`translate(0, ${lineY})`}>
                      {p.isAsc ? (
                        <rect
                          x="-22"
                          y="-10"
                          width="44"
                          height="14"
                          rx="3"
                          fill="rgba(244, 63, 94, 0.25)"
                          stroke="rgba(244, 63, 94, 0.7)"
                          strokeWidth="0.8"
                        />
                      ) : null}
                      <text
                        x="0"
                        y="0"
                        textAnchor="middle"
                        fill={p.isAsc ? "#fda4af" : p.isRetro ? "#f59e0b" : "#f1f5f9"}
                        fontSize="11.5"
                        fontWeight={p.isAsc ? "700" : "600"}
                        fontFamily="'Outfit', sans-serif"
                      >
                        {p.label}
                        {p.isRetro ? <tspan fill="#f59e0b" fontSize="9"> (R)</tspan> : null}
                        {p.degree ? <tspan fill="#94a3b8" fontSize="9"> {p.degree}</tspan> : null}
                      </text>
                    </g>
                  );
                })}
              </g>
            </g>
          );
        })}

        {/* Small Center Label */}
        <circle cx={cx} cy={cy} r="18" fill="#090c15" stroke="rgba(229, 185, 76, 0.4)" strokeWidth="1" />
        <text
          x={cx}
          y={cy + 4}
          textAnchor="middle"
          fill="#fbe285"
          fontSize="10"
          fontWeight="700"
          fontFamily="'Cinzel', serif"
        >
          {varga}
        </text>
      </svg>
    </div>
  );
};
