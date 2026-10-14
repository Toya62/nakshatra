"use client";

import React, { useState, useMemo } from "react";
import { ChartData } from "@/lib/types";

interface Props {
  chart: ChartData;
  varga?: string;
  size?: number;
}

interface DignityInfo {
  isExalted: boolean;
  isDebilitated: boolean;
  isOwnSign: boolean;
  symbol: string;
  label: string;
}

function getGrahaDignity(planetName: string, signNum: number): DignityInfo {
  const norm = planetName.toLowerCase();
  if (norm.includes("sun")) {
    if (signNum === 1) return { isExalted: true, isDebilitated: false, isOwnSign: false, symbol: "↑", label: "Exalted" };
    if (signNum === 7) return { isExalted: false, isDebilitated: true, isOwnSign: false, symbol: "↓", label: "Debilitated" };
    if (signNum === 5) return { isExalted: false, isDebilitated: false, isOwnSign: true, symbol: "★", label: "Own Sign" };
  } else if (norm.includes("moon")) {
    if (signNum === 2) return { isExalted: true, isDebilitated: false, isOwnSign: false, symbol: "↑", label: "Exalted" };
    if (signNum === 8) return { isExalted: false, isDebilitated: true, isOwnSign: false, symbol: "↓", label: "Debilitated" };
    if (signNum === 4) return { isExalted: false, isDebilitated: false, isOwnSign: true, symbol: "★", label: "Own Sign" };
  } else if (norm.includes("mars")) {
    if (signNum === 10) return { isExalted: true, isDebilitated: false, isOwnSign: false, symbol: "↑", label: "Exalted" };
    if (signNum === 4) return { isExalted: false, isDebilitated: true, isOwnSign: false, symbol: "↓", label: "Debilitated" };
    if (signNum === 1 || signNum === 8) return { isExalted: false, isDebilitated: false, isOwnSign: true, symbol: "★", label: "Own Sign" };
  } else if (norm.includes("mercury")) {
    if (signNum === 6) return { isExalted: true, isDebilitated: false, isOwnSign: true, symbol: "↑", label: "Exalted" };
    if (signNum === 12) return { isExalted: false, isDebilitated: true, isOwnSign: false, symbol: "↓", label: "Debilitated" };
    if (signNum === 3) return { isExalted: false, isDebilitated: false, isOwnSign: true, symbol: "★", label: "Own Sign" };
  } else if (norm.includes("jupiter")) {
    if (signNum === 4) return { isExalted: true, isDebilitated: false, isOwnSign: false, symbol: "↑", label: "Exalted" };
    if (signNum === 10) return { isExalted: false, isDebilitated: true, isOwnSign: false, symbol: "↓", label: "Debilitated" };
    if (signNum === 9 || signNum === 12) return { isExalted: false, isDebilitated: false, isOwnSign: true, symbol: "★", label: "Own Sign" };
  } else if (norm.includes("venus")) {
    if (signNum === 12) return { isExalted: true, isDebilitated: false, isOwnSign: false, symbol: "↑", label: "Exalted" };
    if (signNum === 6) return { isExalted: false, isDebilitated: true, isOwnSign: false, symbol: "↓", label: "Debilitated" };
    if (signNum === 2 || signNum === 7) return { isExalted: false, isDebilitated: false, isOwnSign: true, symbol: "★", label: "Own Sign" };
  } else if (norm.includes("saturn")) {
    if (signNum === 7) return { isExalted: true, isDebilitated: false, isOwnSign: false, symbol: "↑", label: "Exalted" };
    if (signNum === 1) return { isExalted: false, isDebilitated: true, isOwnSign: false, symbol: "↓", label: "Debilitated" };
    if (signNum === 10 || signNum === 11) return { isExalted: false, isDebilitated: false, isOwnSign: true, symbol: "★", label: "Own Sign" };
  }
  return { isExalted: false, isDebilitated: false, isOwnSign: false, symbol: "", label: "" };
}

interface GrahaStyle {
  abbr: string;
  glyph: string;
  name: string;
  color: string;
  bg: string;
  border: string;
}

const GRAHA_STYLES: Record<string, GrahaStyle> = {
  Asc: { abbr: "ASC", glyph: "👑", name: "Ascendant", color: "#fde047", bg: "rgba(253, 224, 71, 0.18)", border: "rgba(253, 224, 71, 0.55)" },
  Su:  { abbr: "Su",  glyph: "☉",  name: "Sun",       color: "#f59e0b", bg: "rgba(245, 158, 11, 0.16)", border: "rgba(245, 158, 11, 0.45)" },
  Mo:  { abbr: "Mo",  glyph: "☽",  name: "Moon",      color: "#e2e8f0", bg: "rgba(226, 232, 240, 0.16)", border: "rgba(226, 232, 240, 0.45)" },
  Ma:  { abbr: "Ma",  glyph: "♂",  name: "Mars",      color: "#f87171", bg: "rgba(248, 113, 113, 0.16)", border: "rgba(248, 113, 113, 0.45)" },
  Me:  { abbr: "Me",  glyph: "☿",  name: "Mercury",   color: "#34d399", bg: "rgba(52, 211, 153, 0.16)", border: "rgba(52, 211, 153, 0.45)" },
  Ju:  { abbr: "Ju",  glyph: "♃",  name: "Jupiter",   color: "#fbbf24", bg: "rgba(251, 191, 36, 0.16)", border: "rgba(251, 191, 36, 0.45)" },
  Ve:  { abbr: "Ve",  glyph: "♀",  name: "Venus",     color: "#f472b6", bg: "rgba(244, 114, 182, 0.16)", border: "rgba(244, 114, 182, 0.45)" },
  Sa:  { abbr: "Sa",  glyph: "♄",  name: "Saturn",    color: "#818cf8", bg: "rgba(129, 140, 248, 0.16)", border: "rgba(129, 140, 248, 0.45)" },
  Ra:  { abbr: "Ra",  glyph: "☊",  name: "Rahu",      color: "#c084fc", bg: "rgba(192, 132, 252, 0.16)", border: "rgba(192, 132, 252, 0.45)" },
  Ke:  { abbr: "Ke",  glyph: "☋",  name: "Ketu",      color: "#94a3b8", bg: "rgba(148, 163, 184, 0.16)", border: "rgba(148, 163, 184, 0.45)" },
};

const SIGN_CELLS: Record<string, { row: number; col: number; num: number }> = {
  Pisces:      { row: 0, col: 0, num: 12 },
  Aries:       { row: 0, col: 1, num: 1 },
  Taurus:      { row: 0, col: 2, num: 2 },
  Gemini:      { row: 0, col: 3, num: 3 },
  Cancer:      { row: 1, col: 3, num: 4 },
  Leo:         { row: 2, col: 3, num: 5 },
  Virgo:       { row: 3, col: 3, num: 6 },
  Libra:       { row: 3, col: 2, num: 7 },
  Scorpio:     { row: 3, col: 1, num: 8 },
  Sagittarius: { row: 3, col: 0, num: 9 },
  Capricorn:   { row: 2, col: 0, num: 10 },
  Aquarius:    { row: 1, col: 0, num: 11 },
};

const ZODIAC_METADATA: Record<number, { english: string; sanskrit: string; lord: string; element: string }> = {
  1:  { english: "Aries",       sanskrit: "Mesha",       lord: "Mars",    element: "Fire"  },
  2:  { english: "Taurus",      sanskrit: "Vrishabha",   lord: "Venus",   element: "Earth" },
  3:  { english: "Gemini",      sanskrit: "Mithuna",     lord: "Mercury", element: "Air"   },
  4:  { english: "Cancer",      sanskrit: "Karka",       lord: "Moon",    element: "Water" },
  5:  { english: "Leo",         sanskrit: "Simha",       lord: "Sun",     element: "Fire"  },
  6:  { english: "Virgo",       sanskrit: "Kanya",       lord: "Mercury", element: "Earth" },
  7:  { english: "Libra",       sanskrit: "Tula",        lord: "Venus",   element: "Air"   },
  8:  { english: "Scorpio",     sanskrit: "Vrishchika",  lord: "Mars",    element: "Water" },
  9:  { english: "Sagittarius", sanskrit: "Dhanu",       lord: "Jupiter", element: "Fire"  },
  10: { english: "Capricorn",   sanskrit: "Makara",      lord: "Saturn",  element: "Earth" },
  11: { english: "Aquarius",    sanskrit: "Kumbha",      lord: "Saturn",  element: "Air"   },
  12: { english: "Pisces",      sanskrit: "Meena",       lord: "Jupiter", element: "Water" },
};

const BHAVA_METADATA: Record<number, { title: string; sanskrit: string; classification: string; significations: string }> = {
  1:  { title: "1st House", sanskrit: "Tanu Bhava",    classification: "Kendra & Trikona (Dharma)", significations: "Self, physical vitality, constitution & character" },
  2:  { title: "2nd House", sanskrit: "Dhana Bhava",   classification: "Maraka & Panaphara (Artha)", significations: "Wealth, family heritage, speech & resources" },
  3:  { title: "3rd House", sanskrit: "Sahaja Bhava",  classification: "Upachaya & Apoklima (Kama)", significations: "Courage, initiative, siblings & willpower" },
  4:  { title: "4th House", sanskrit: "Sukha Bhava",   classification: "Kendra (Moksha)", significations: "Mother, peace of mind, home, land & heart" },
  5:  { title: "5th House", sanskrit: "Putra Bhava",   classification: "Trikona (Dharma)", significations: "Intellect, past-life merit (Purva Punya) & creativity" },
  6:  { title: "6th House", sanskrit: "Ari/Roga Bhava", classification: "Dusthana & Upachaya (Artha)", significations: "Service, debt, competitors & health resilience" },
  7:  { title: "7th House", sanskrit: "Kalatra Bhava", classification: "Kendra & Maraka (Kama)", significations: "Spouse, partnership, contracts & public dealings" },
  8:  { title: "8th House", sanskrit: "Randhra Bhava", classification: "Dusthana (Moksha)", significations: "Longevity, transformation, mysteries & unearned wealth" },
  9:  { title: "9th House", sanskrit: "Dharma Bhava",  classification: "Trikona (Dharma)", significations: "Destiny, higher philosophy, guru, father & divine grace" },
  10: { title: "10th House", sanskrit: "Karma Bhava",  classification: "Kendra & Upachaya (Artha)", significations: "Career, public stature, authority & life work" },
  11: { title: "11th House", sanskrit: "Labha Bhava",  classification: "Upachaya (Kama)", significations: "Gains, fulfillment of hopes, elder peers & networks" },
  12: { title: "12th House", sanskrit: "Vyaya Bhava",  classification: "Dusthana (Moksha)", significations: "Moksha, foreign lands, sleep, solitude & spiritual liberation" },
};

interface PlanetBadgeData {
  key: string;
  label: string;
  name: string;
  isAsc?: boolean;
  isRetro?: boolean;
  degree?: string;
  dignity: DignityInfo;
}

export const SouthIndianChart: React.FC<Props> = ({ chart, varga = "D1", size = 520 }) => {
  const [hoveredSign, setHoveredSign] = useState<string | null>(null);

  const baseSize = 520;
  const cellSize = baseSize / 4;

  const vKey = varga.toUpperCase();
  const vData = chart.vargas && chart.vargas[vKey];
  const ascSignName = (vData && vKey !== "D1")
    ? (vData["Ascendant"] || chart.ascendant.sign)
    : chart.ascendant.sign;
  const ascSignNum = SIGN_CELLS[ascSignName]?.num || 1;

  const placements = useMemo(() => {
    const map: Record<string, PlanetBadgeData[]> = {
      Aries: [], Taurus: [], Gemini: [], Cancer: [], Leo: [], Virgo: [],
      Libra: [], Scorpio: [], Sagittarius: [], Capricorn: [], Aquarius: [], Pisces: [],
    };

    if (vData && vKey !== "D1") {
      const ascSign = vData["Ascendant"] || chart.ascendant.sign;
      if (map[ascSign]) {
        map[ascSign].push({
          key: "Asc",
          label: "ASC",
          name: "Ascendant",
          isAsc: true,
          dignity: { isExalted: false, isDebilitated: false, isOwnSign: false, symbol: "", label: "" },
        });
      }

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
        const signNumLocal = SIGN_CELLS[pSign]?.num || 1;
        if (map[pSign]) {
          map[pSign].push({
            key: abbr,
            label: abbr,
            name: p.name,
            isRetro: p.retrograde,
            dignity: getGrahaDignity(p.name, signNumLocal),
          });
        }
      }
    } else {
      if (map[chart.ascendant.sign]) {
        map[chart.ascendant.sign].push({
          key: "Asc",
          label: "ASC",
          name: "Ascendant",
          isAsc: true,
          degree: `${chart.ascendant.degree_in_sign.toFixed(1)}°`,
          dignity: { isExalted: false, isDebilitated: false, isOwnSign: false, symbol: "", label: "" },
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

        const signNumLocal = SIGN_CELLS[p.sign]?.num || 1;
        if (map[p.sign]) {
          map[p.sign].push({
            key: abbr,
            label: abbr,
            name: p.name,
            isRetro: p.retrograde,
            degree: `${p.degree_in_sign.toFixed(1)}°`,
            dignity: getGrahaDignity(p.name, signNumLocal),
          });
        }
      }
    }

    return map;
  }, [chart, varga, vData, vKey]);

  // Derive House index for each hovered sign
  const hoveredInfo = useMemo(() => {
    if (!hoveredSign) return null;
    const signMeta = SIGN_CELLS[hoveredSign];
    if (!signMeta) return null;
    const houseNum = ((signMeta.num - ascSignNum + 12) % 12) + 1;
    const bhava = BHAVA_METADATA[houseNum];
    const zodiac = ZODIAC_METADATA[signMeta.num];
    const planets = placements[hoveredSign] || [];
    return {
      houseNum,
      signName: hoveredSign,
      signNum: signMeta.num,
      bhava,
      zodiac,
      planets,
    };
  }, [hoveredSign, ascSignNum, placements]);

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: "100%" }}>
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${baseSize} ${baseSize}`}
        role="img"
        aria-label={`South Indian ${varga} Kundali chart`}
        style={{
          width: "100%",
          maxWidth: `${size}px`,
          aspectRatio: "1 / 1",
          height: "auto",
          filter: "drop-shadow(0 16px 40px rgba(0,0,0,0.65))",
          borderRadius: "var(--radius-lg)",
          background: "linear-gradient(145deg, #07090e 0%, #0c101c 100%)",
          userSelect: "none",
        }}
      >
        <title>{`South Indian ${varga} Kundali Chart`}</title>
        <defs>
          <radialGradient id="southCenterGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(229, 185, 76, 0.16)" />
            <stop offset="60%" stopColor="rgba(229, 185, 76, 0.04)" />
            <stop offset="100%" stopColor="rgba(12, 16, 28, 0)" />
          </radialGradient>
        </defs>

        {/* Double Engraved Outer Frame */}
        <rect x="1" y="1" width={baseSize - 2} height={baseSize - 2} rx="16" fill="none" stroke="rgba(229, 185, 76, 0.45)" strokeWidth="2.5" />
        <rect x="7" y="7" width={baseSize - 14} height={baseSize - 14} rx="12" fill="none" stroke="rgba(229, 185, 76, 0.22)" strokeWidth="1" strokeDasharray="6 3" />

        {/* Grid lines */}
        {[1, 2, 3].map((i) => (
          <React.Fragment key={i}>
            <line
              x1={i * cellSize} y1="0"
              x2={i * cellSize} y2={baseSize}
              stroke="rgba(229, 185, 76, 0.35)"
              strokeWidth="1.4"
            />
            <line
              x1="0" y1={i * cellSize}
              x2={baseSize} y2={i * cellSize}
              stroke="rgba(229, 185, 76, 0.35)"
              strokeWidth="1.4"
            />
          </React.Fragment>
        ))}

        {/* Center 2x2 Sacred Chamber */}
        <rect
          x={cellSize}
          y={cellSize}
          width={cellSize * 2}
          height={cellSize * 2}
          fill="url(#southCenterGlow)"
          stroke="rgba(229, 185, 76, 0.6)"
          strokeWidth="1.8"
        />

        {/* Center Yantra Astrolabe Seal */}
        <g transform={`translate(${baseSize / 2}, ${baseSize / 2})`} pointerEvents="none">
          <circle r={cellSize * 0.72} fill="none" stroke="rgba(229, 185, 76, 0.22)" strokeWidth="1" strokeDasharray="4 4" />
          <polygon
            points={`0,-${cellSize * 0.46} ${cellSize * 0.4},${cellSize * 0.23} -${cellSize * 0.4},${cellSize * 0.23}`}
            fill="none"
            stroke="rgba(56, 189, 248, 0.28)"
            strokeWidth="1.2"
          />
          <polygon
            points={`0,${cellSize * 0.46} ${cellSize * 0.4},-${cellSize * 0.23} -${cellSize * 0.4},-${cellSize * 0.23}`}
            fill="none"
            stroke="rgba(229, 185, 76, 0.3)"
            strokeWidth="1.2"
          />
          <text
            y="-20"
            textAnchor="middle"
            fill="#fbe285"
            fontSize="16"
            fontWeight="700"
            fontFamily="'Cinzel', serif"
            letterSpacing="3"
          >
            NAKSHATRA
          </text>
          <text
            y="4"
            textAnchor="middle"
            fill="#38bdf8"
            fontSize="12.5"
            fontWeight="600"
            fontFamily="'Outfit', sans-serif"
            letterSpacing="1.5"
          >
            {vKey} {vKey === "D1" ? "RASI" : vKey === "D9" ? "NAVAMSA" : "VARGA"}
          </text>
          <text
            y="24"
            textAnchor="middle"
            fill="#cbd5e1"
            fontSize="10.5"
            fontFamily="'Outfit', sans-serif"
          >
            Lagna: {ascSignName} ({chart.ascendant.degree_in_sign.toFixed(1)}°)
          </text>
          <text
            y="40"
            textAnchor="middle"
            fill="#64748b"
            fontSize="9"
            fontFamily="'JetBrains Mono', monospace"
          >
            Lahiri (JHora)
          </text>
        </g>

        {/* 12 Perimeter Zodiac Cells */}
        {Object.entries(SIGN_CELLS).map(([signName, { row, col, num }]) => {
          const x = col * cellSize;
          const y = row * cellSize;
          const bodies = placements[signName] || [];
          const isLagnaSign = signName === ascSignName;
          const isHovered = hoveredSign === signName;
          const houseNum = ((num - ascSignNum + 12) % 12) + 1;

          return (
            <g
              key={signName}
              transform={`translate(${x}, ${y})`}
              onMouseEnter={() => setHoveredSign(signName)}
              onMouseLeave={() => setHoveredSign(null)}
              onClick={() => setHoveredSign((prev) => prev === signName ? null : signName)}
              style={{ cursor: "pointer", pointerEvents: "all" }}
            >
              {/* Cell Fill on Hover / Lagna */}
              <rect
                x="1"
                y="1"
                width={cellSize - 2}
                height={cellSize - 2}
                fill={isHovered ? "rgba(251, 226, 133, 0.16)" : isLagnaSign ? "rgba(229, 185, 76, 0.08)" : "transparent"}
                stroke={isHovered ? "#fbe285" : "none"}
                strokeWidth={isHovered ? "2" : "0"}
                pointerEvents="all"
              />

              {/* Sign Header & Index */}
              <text
                x="8"
                y="16"
                fill={isHovered ? "#ffffff" : isLagnaSign ? "#fbe285" : "#cbd5e1"}
                fontSize="10.5"
                fontWeight="700"
                fontFamily="'Outfit', sans-serif"
              >
                {signName.slice(0, 3).toUpperCase()}
                <tspan fill="rgba(229, 185, 76, 0.6)" fontSize="9"> (H{houseNum})</tspan>
              </text>
              <text
                x={cellSize - 8}
                y="16"
                textAnchor="end"
                fill="rgba(229, 185, 76, 0.7)"
                fontSize="9.5"
                fontFamily="'Cinzel', serif"
                fontWeight="700"
              >
                {num}
              </text>

              {/* Formatted Planet Micro-Pills */}
              <g transform="translate(8, 25)">
                {bodies.map((b, idx) => {
                  const lineY = idx * 21;
                  const style = GRAHA_STYLES[b.key] || {
                    abbr: b.label, glyph: "•", name: b.name, color: "#f1f5f9", bg: "rgba(255,255,255,0.1)", border: "rgba(255,255,255,0.3)"
                  };

                  return (
                    <g key={idx} transform={`translate(0, ${lineY})`}>
                      <rect
                        x="0"
                        y="0"
                        width={cellSize - 16}
                        height="18"
                        rx="3.5"
                        fill={style.bg}
                        stroke={style.border}
                        strokeWidth="0.8"
                      />
                      <text
                        x="6"
                        y="12.5"
                        fill={style.color}
                        fontSize="9.5"
                        fontWeight="700"
                        fontFamily="'Outfit', sans-serif"
                      >
                        {style.glyph} {b.label}
                      </text>
                      {b.isRetro && (
                        <text x="32" y="12" fill="#f59e0b" fontSize="8" fontWeight="800">
                          ℞
                        </text>
                      )}
                      {b.dignity.symbol && (
                        <text
                          x={b.isRetro ? "40" : "32"}
                          y="12"
                          fill={b.dignity.isExalted ? "#34d399" : b.dignity.isDebilitated ? "#f87171" : "#fbe285"}
                          fontSize="8"
                          fontWeight="800"
                        >
                          {b.dignity.symbol}
                        </text>
                      )}
                      {b.degree && (
                        <text
                          x={cellSize - 22}
                          y="12.5"
                          textAnchor="end"
                          fill="#94a3b8"
                          fontSize="8.5"
                          fontFamily="'JetBrains Mono', monospace"
                        >
                          {b.degree}
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
            </g>
          );
        })}
      </svg>

      {/* Interactive Bhava Inspector Strip */}
      <div
        className="card"
        style={{
          marginTop: "var(--space-3)",
          padding: "var(--space-2) var(--space-4)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "var(--space-3)",
          fontSize: "var(--type-label)",
          background: "rgba(10, 14, 25, 0.88)",
          border: "1px solid rgba(229, 185, 76, 0.22)",
          borderRadius: "var(--radius-md)",
          width: "100%",
          maxWidth: `${size}px`,
          minHeight: "44px",
          transition: "all 0.2s ease",
        }}
      >
        {hoveredInfo ? (
          <>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <span style={{ color: "var(--gold-bright)", fontWeight: 700, fontFamily: "var(--font-serif)" }}>
                H{hoveredInfo.houseNum} · {hoveredInfo.bhava.title}
              </span>
              <span style={{ color: "var(--text-low)" }}>·</span>
              <span style={{ color: "var(--cyan-vivid)", fontWeight: 600 }}>
                {hoveredInfo.bhava.sanskrit}
              </span>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", fontSize: "var(--type-micro)" }}>
              <span style={{ color: "var(--text-high)", fontWeight: 600 }}>
                {hoveredInfo.signName} ({hoveredInfo.zodiac.sanskrit})
              </span>
              <span style={{ color: "var(--text-low)" }}>·</span>
              <span style={{ color: "var(--gold-vivid)" }}>Lord: {hoveredInfo.zodiac.lord}</span>
              <span style={{ color: "var(--text-low)" }}>·</span>
              <span style={{ color: "var(--text-mid)" }}>
                {hoveredInfo.planets.length > 0
                  ? hoveredInfo.planets.map((p) => p.name).join(", ")
                  : "No grahas"}
              </span>
            </div>
          </>
        ) : (
          <div style={{ color: "var(--text-low)", fontSize: "var(--type-micro)", display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%" }}>
            <span>Lagna: <strong style={{ color: "var(--gold-bright)" }}>{chart.ascendant.sign} {chart.ascendant.degree_in_sign.toFixed(1)}°</strong></span>
            <span>·</span>
            <span>Moon: <strong style={{ color: "var(--text-high)" }}>{chart.planets.find(p => p.name === "Moon")?.sign || "Moon"}</strong></span>
            <span>·</span>
            <span style={{ color: "var(--text-mid)" }}>Hover any zodiac cell to inspect Bhava significations</span>
          </div>
        )}
      </div>
    </div>
  );
};
