"use client";

import React, { useState, useMemo } from "react";
import { ChartData } from "@/lib/types";
import { useLanguage } from "@/context/LanguageContext";

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
  Asc: { abbr: "ASC", glyph: "👑", name: "Ascendant", color: "var(--graha-asc, #fde047)", bg: "rgba(253, 224, 71, 0.18)", border: "rgba(253, 224, 71, 0.55)" },
  Su:  { abbr: "Su",  glyph: "☉",  name: "Sun",       color: "var(--graha-sun, #f59e0b)", bg: "rgba(245, 158, 11, 0.16)", border: "rgba(245, 158, 11, 0.45)" },
  Mo:  { abbr: "Mo",  glyph: "☽",  name: "Moon",      color: "var(--graha-moon, #e2e8f0)", bg: "rgba(148, 163, 184, 0.16)", border: "rgba(148, 163, 184, 0.45)" },
  Ma:  { abbr: "Ma",  glyph: "♂",  name: "Mars",      color: "var(--graha-mars, #f87171)", bg: "rgba(248, 113, 113, 0.16)", border: "rgba(248, 113, 113, 0.45)" },
  Me:  { abbr: "Me",  glyph: "☿",  name: "Mercury",   color: "var(--graha-mercury, #34d399)", bg: "rgba(52, 211, 153, 0.16)", border: "rgba(52, 211, 153, 0.45)" },
  Ju:  { abbr: "Ju",  glyph: "♃",  name: "Jupiter",   color: "var(--graha-jupiter, #fbbf24)", bg: "rgba(251, 191, 36, 0.16)", border: "rgba(251, 191, 36, 0.45)" },
  Ve:  { abbr: "Ve",  glyph: "♀",  name: "Venus",     color: "var(--graha-venus, #f472b6)", bg: "rgba(244, 114, 182, 0.16)", border: "rgba(244, 114, 182, 0.45)" },
  Sa:  { abbr: "Sa",  glyph: "♄",  name: "Saturn",    color: "var(--graha-saturn, #818cf8)", bg: "rgba(129, 140, 248, 0.16)", border: "rgba(129, 140, 248, 0.45)" },
  Ra:  { abbr: "Ra",  glyph: "☊",  name: "Rahu",      color: "var(--graha-rahu, #c084fc)", bg: "rgba(192, 132, 252, 0.16)", border: "rgba(192, 132, 252, 0.45)" },
  Ke:  { abbr: "Ke",  glyph: "☋",  name: "Ketu",      color: "var(--graha-ketu, #94a3b8)", bg: "rgba(148, 163, 184, 0.16)", border: "rgba(148, 163, 184, 0.45)" },
};

const SIGN_NAMES_TO_NUM: Record<string, number> = {
  Aries: 1, Taurus: 2, Gemini: 3, Cancer: 4, Leo: 5, Virgo: 6,
  Libra: 7, Scorpio: 8, Sagittarius: 9, Capricorn: 10, Aquarius: 11, Pisces: 12,
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

export const NorthIndianChart: React.FC<Props> = ({ chart, varga = "D1", size = 520 }) => {
  const { t, lang, num } = useLanguage();
  const [hoveredHouse, setHoveredHouse] = useState<number | null>(null);

  const w = 520;
  const h = 520;
  const cx = 260;
  const cy = 260;

  const vKey = varga.toUpperCase();
  const vData = chart.vargas && chart.vargas[vKey];
  const ascSignName = (vData && vKey !== "D1")
    ? (vData["Ascendant"] || chart.ascendant.sign)
    : chart.ascendant.sign;
  const ascSignNum = SIGN_NAMES_TO_NUM[ascSignName] || 1;

  // Map each house (1 to 12) to sign and formatted planet badges
  const houseData = useMemo(() => {
    const signPlanets: Record<string, PlanetBadgeData[]> = {
      Aries: [], Taurus: [], Gemini: [], Cancer: [], Leo: [], Virgo: [],
      Libra: [], Scorpio: [], Sagittarius: [], Capricorn: [], Aquarius: [], Pisces: [],
    };

    if (vData && vKey !== "D1") {
      const ascSign = vData["Ascendant"] || chart.ascendant.sign;
      const ascSignNumLocal = SIGN_NAMES_TO_NUM[ascSign] || 1;
      signPlanets[ascSign]?.push({
        key: "Asc",
        label: "ASC",
        name: "Ascendant",
        isAsc: true,
        dignity: { isExalted: false, isDebilitated: false, isOwnSign: false, symbol: "", label: "" },
      });

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
        const signNumLocal = SIGN_NAMES_TO_NUM[pSign] || 1;
        if (signPlanets[pSign]) {
          signPlanets[pSign].push({
            key: abbr,
            label: abbr,
            name: p.name,
            isRetro: p.retrograde,
            dignity: getGrahaDignity(p.name, signNumLocal),
          });
        }
      }
    } else {
      signPlanets[chart.ascendant.sign]?.push({
        key: "Asc",
        label: "ASC",
        name: "Ascendant",
        isAsc: true,
        degree: `${chart.ascendant.degree_in_sign.toFixed(1)}°`,
        dignity: { isExalted: false, isDebilitated: false, isOwnSign: false, symbol: "", label: "" },
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

        const signNumLocal = SIGN_NAMES_TO_NUM[p.sign] || 1;
        if (signPlanets[p.sign]) {
          signPlanets[p.sign].push({
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

    const houses = [];
    for (let houseNum = 1; houseNum <= 12; houseNum++) {
      const signNum = ((ascSignNum - 1 + (houseNum - 1)) % 12) + 1;
      const meta = ZODIAC_METADATA[signNum];
      houses.push({
        houseNum,
        signNum,
        signName: meta.english,
        signSanskrit: meta.sanskrit,
        lord: meta.lord,
        element: meta.element,
        planets: signPlanets[meta.english] || [],
      });
    }
    return houses;
  }, [chart, varga, ascSignName, ascSignNum, vData, vKey]);

  // Chamber geometry definitions with dedicated corner Rashi positions (NO collisions)
  const chambers = [
    // House 1 (Top diamond — Kendra & Trikona)
    {
      house: 1,
      polygon: `${cx},0 130,130 ${cx},${cy} 390,130`,
      contentPos: { x: cx, y: 138 },
      signPos: { x: 175, y: 140 },
      type: "kendra-trikona" as const,
    },
    // House 2 (Top-left triangle)
    {
      house: 2,
      polygon: `0,0 ${cx},0 130,130`,
      contentPos: { x: 130, y: 58 },
      signPos: { x: 215, y: 26 },
      type: "regular" as const,
    },
    // House 3 (Left-upper triangle — Upachaya)
    {
      house: 3,
      polygon: `0,0 0,${cy} 130,130`,
      contentPos: { x: 58, y: 130 },
      signPos: { x: 26, y: 215 },
      type: "upachaya" as const,
    },
    // House 4 (Left diamond — Kendra)
    {
      house: 4,
      polygon: `0,${cy} 130,130 ${cx},${cy} 130,390`,
      contentPos: { x: 130, y: 260 },
      signPos: { x: 130, y: 180 },
      type: "kendra" as const,
    },
    // House 5 (Left-lower triangle — Trikona)
    {
      house: 5,
      polygon: `0,${cy} 0,${h} 130,390`,
      contentPos: { x: 58, y: 390 },
      signPos: { x: 26, y: 315 },
      type: "trikona" as const,
    },
    // House 6 (Bottom-left triangle — Dusthana)
    {
      house: 6,
      polygon: `0,${h} ${cx},${h} 130,390`,
      contentPos: { x: 130, y: 462 },
      signPos: { x: 215, y: 494 },
      type: "dusthana" as const,
    },
    // House 7 (Bottom diamond — Kendra)
    {
      house: 7,
      polygon: `${cx},${h} 130,390 ${cx},${cy} 390,390`,
      contentPos: { x: cx, y: 390 },
      signPos: { x: 180, y: 390 },
      type: "kendra" as const,
    },
    // House 8 (Bottom-right triangle — Dusthana)
    {
      house: 8,
      polygon: `${cx},${h} ${w},${h} 390,390`,
      contentPos: { x: 390, y: 462 },
      signPos: { x: 305, y: 494 },
      type: "dusthana" as const,
    },
    // House 9 (Right-lower triangle — Trikona)
    {
      house: 9,
      polygon: `${w},${cy} ${w},${h} 390,390`,
      contentPos: { x: 462, y: 390 },
      signPos: { x: 494, y: 305 },
      type: "trikona" as const,
    },
    // House 10 (Right diamond — Kendra)
    {
      house: 10,
      polygon: `${w},${cy} 390,130 ${cx},${cy} 390,390`,
      contentPos: { x: 390, y: 260 },
      signPos: { x: 390, y: 180 },
      type: "kendra" as const,
    },
    // House 11 (Right-upper triangle — Upachaya)
    {
      house: 11,
      polygon: `${w},${cy} ${w},0 390,130`,
      contentPos: { x: 462, y: 130 },
      signPos: { x: 494, y: 215 },
      type: "upachaya" as const,
    },
    // House 12 (Top-right triangle — Dusthana)
    {
      house: 12,
      polygon: `260,0 ${w},0 390,130`,
      contentPos: { x: 390, y: 58 },
      signPos: { x: 305, y: 26 },
      type: "dusthana" as const,
    },
  ];

  const activeHouseData = hoveredHouse ? houseData[hoveredHouse - 1] : null;
  const activeBhavaMeta = hoveredHouse ? BHAVA_METADATA[hoveredHouse] : null;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: "100%" }}>
      {/* SVG Container */}
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${w} ${h}`}
        role="img"
        aria-label={`North Indian ${varga} Kundali chart`}
        style={{
          width: "100%",
          maxWidth: `${size}px`,
          aspectRatio: "1 / 1",
          height: "auto",
          filter: "var(--chart-drop-shadow)",
          borderRadius: "var(--radius-lg)",
          background: "var(--chart-bg)",
          border: "1px solid var(--chart-border)",
          userSelect: "none",
          touchAction: "manipulation",
        }}
      >
        <title>{`North Indian ${varga} Kundali Chart`}</title>
        <defs>
          {/* Kendra Auspicious Radial Warmth */}
          <radialGradient id="kendraGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(223, 177, 91, 0.15)" />
            <stop offset="70%" stopColor="rgba(223, 177, 91, 0.04)" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>

          {/* Trikona Grace Indigo/Cyan Tint */}
          <radialGradient id="trikonaGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(56, 189, 248, 0.12)" />
            <stop offset="70%" stopColor="rgba(56, 189, 248, 0.03)" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>

          {/* Hover highlight illumination */}
          <radialGradient id="hoverGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(252, 237, 190, 0.22)" />
            <stop offset="100%" stopColor="rgba(223, 177, 91, 0.08)" />
          </radialGradient>

          {/* Elevated pill card shadow for crisp separation */}
          <filter id="pillShadow" x="-10%" y="-15%" width="120%" height="135%">
            <feDropShadow dx="0" dy="1.5" stdDeviation="1.5" floodColor="rgba(0, 0, 0, 0.08)" />
          </filter>
        </defs>

        {/* Double Engraved Frame */}
        <rect x="1" y="1" width={w - 2} height={h - 2} rx="16" fill="none" stroke="var(--gold-border)" strokeWidth="2.5" />
        <rect x="7" y="7" width={w - 14} height={h - 14} rx="12" fill="none" stroke="var(--border-subtle)" strokeWidth="1" strokeDasharray="6 3" />

        {/* 4 Corner Rosette Accents */}
        {[[10, 10], [w - 10, 10], [10, h - 10], [w - 10, h - 10]].map(([rx, ry], idx) => (
          <g key={idx} transform={`translate(${rx}, ${ry})`}>
            <circle r="3.5" fill="var(--gold-vivid)" />
            <circle r="1.5" fill="var(--bg-void)" />
          </g>
        ))}

        {/* 1. Chamber Background Highlights & Hover Targets */}
        {chambers.map((ch) => {
          const isHovered = hoveredHouse === ch.house;
          let chamberFill = "transparent";
          if (isHovered) chamberFill = "url(#hoverGlow)";
          else if (ch.type === "kendra-trikona" || ch.type === "kendra") chamberFill = "url(#kendraGlow)";
          else if (ch.type === "trikona") chamberFill = "url(#trikonaGlow)";
          else if (ch.type === "dusthana") chamberFill = "var(--bg-subtle)";

          return (
            <polygon
              key={`bg-${ch.house}`}
              points={ch.polygon}
              fill={chamberFill}
              stroke={isHovered ? "var(--gold-vivid)" : "none"}
              strokeWidth={isHovered ? "2.5" : "0"}
              onMouseEnter={() => setHoveredHouse(ch.house)}
              onMouseLeave={() => setHoveredHouse(null)}
              onClick={() => setHoveredHouse((prev) => prev === ch.house ? null : ch.house)}
              style={{ cursor: "pointer", transition: "all 0.2s ease" }}
              pointerEvents="all"
            />
          );
        })}

        {/* 2. Structural Kundali Lines (Background Grid — Never Slices Across Planets) */}
        {/* Two Main Cross Diagonals */}
        <line x1="0" y1="0" x2={w} y2={h} stroke="var(--gold-border)" strokeWidth="1.6" pointerEvents="none" />
        <line x1="0" y1={h} x2={w} y2="0" stroke="var(--gold-border)" strokeWidth="1.6" pointerEvents="none" />

        {/* Center Rhombus (Diamond) Lines */}
        <polygon
          points={`${cx},0 ${w},${cy} ${cx},${h} 0,${cy}`}
          fill="none"
          stroke="var(--chart-grid-stroke)"
          strokeWidth="2"
          pointerEvents="none"
        />

        {/* 3. Center Ashtalakshmi / Yantra Astrolabe Emblem */}
        <g transform={`translate(${cx}, ${cy})`} pointerEvents="none">
          <circle r="30" fill="none" stroke="var(--gold-border)" strokeWidth="1" strokeDasharray="3 3" />
          <rect x="-24" y="-24" width="48" height="48" rx="8" fill="var(--chart-center-bg)" stroke="var(--chart-center-stroke)" strokeWidth="1.4" />
          <rect x="-24" y="-24" width="48" height="48" rx="8" fill="none" stroke="var(--cyan-border)" strokeWidth="1" transform="rotate(45)" />
          <text
            y="-4"
            textAnchor="middle"
            fill="var(--gold-bright)"
            fontSize="12.5"
            fontWeight="700"
            fontFamily="'Cinzel', serif"
            letterSpacing="1"
          >
            {vKey}
          </text>
          <text
            y="10"
            textAnchor="middle"
            fill="var(--text-mid)"
            fontSize="7.5"
            fontWeight="600"
            fontFamily="'Outfit', sans-serif"
            letterSpacing="1"
          >
            {vKey === "D1" ? "RASI" : vKey === "D9" ? "NAVAMSA" : "VARGA"}
          </text>
        </g>

        {/* 4. Foreground: Rashi Seals, LAGNA Header & Planet Pills (Rendered on Top of Lines) */}
        {chambers.map((ch) => {
          const data = houseData[ch.house - 1];
          const planets = data ? data.planets : [];
          const isHovered = hoveredHouse === ch.house;

          return (
            <g
              key={`content-${ch.house}`}
              onMouseEnter={() => setHoveredHouse(ch.house)}
              onMouseLeave={() => setHoveredHouse(null)}
              onClick={() => setHoveredHouse((prev) => prev === ch.house ? null : ch.house)}
              style={{ cursor: "pointer", pointerEvents: "all" }}
            >
              {/* Rashi Zodiac Number (Clean classical numeral, no white ball) */}
              <g transform={`translate(${ch.signPos.x}, ${ch.signPos.y})`}>
                {isHovered && (
                  <circle
                    r="11"
                    fill="var(--gold-dim)"
                    stroke="var(--gold-vivid)"
                    strokeWidth="1.2"
                  />
                )}
                <text
                  x="0"
                  y="4.5"
                  textAnchor="middle"
                  fill={isHovered ? "var(--gold-bright)" : "var(--chart-badge-text)"}
                  fontSize="13"
                  fontWeight="800"
                  fontFamily="'Cinzel', 'Outfit', serif"
                >
                  {num(data.signNum)}
                </text>
              </g>

              {/* House 1 LAGNA Title Badge inside House 1 */}
              {ch.house === 1 && (
                <g transform={`translate(${cx}, 52)`}>
                  <rect
                    x="-34"
                    y="-10"
                    width="68"
                    height="20"
                    rx="10"
                    fill="var(--gold-dim)"
                    stroke="var(--gold-border)"
                    strokeWidth="1"
                  />
                  <text
                    x="0"
                    y="3.5"
                    textAnchor="middle"
                    fill="var(--gold-bright)"
                    fontSize="11"
                    fontWeight="800"
                    fontFamily="'Outfit', sans-serif"
                    letterSpacing="1.8"
                  >
                    {lang === "ne" ? "लग्न" : "LAGNA"}
                  </text>
                </g>
              )}

              {/* Formatted Planet Micro-Pills */}
              <g transform={`translate(${ch.contentPos.x}, ${ch.contentPos.y})`}>
                {(() => {
                  const n = planets.length;
                  if (n === 0) return null;

                  // 1 to 3 planets: vertical neat stack with 96px cards (completely inside chambers)
                  if (n <= 3) {
                    const stepY = 28;
                    const pillW = 96;
                    const pillH = 24;
                    const halfW = pillW / 2; // 48

                    return planets.map((p, pIdx) => {
                      const posY = (pIdx - (n - 1) / 2) * stepY;
                      const style = GRAHA_STYLES[p.key] || {
                        abbr: p.label, glyph: "•", name: p.name, color: "var(--text-high)", bg: "var(--bg-subtle)", border: "var(--border-subtle)"
                      };

                      const hasRetro = !!p.isRetro;
                      const hasDignity = !!p.dignity?.symbol;

                      return (
                        <g key={pIdx} transform={`translate(0, ${posY})`}>
                          {/* Solid Base Card for sharp contrast against chart */}
                          <rect
                            className="graha-pill"
                            x={-halfW}
                            y={-pillH / 2}
                            width={pillW}
                            height={pillH}
                            rx="5"
                            fill="var(--chart-pill-bg)"
                            stroke={style.color}
                            strokeOpacity="0.38"
                            strokeWidth="1.2"
                            filter="url(#pillShadow)"
                          />
                          {/* Subtle Graha Tint Overlay */}
                          <rect
                            x={-halfW}
                            y={-pillH / 2}
                            width={pillW}
                            height={pillH}
                            rx="5"
                            fill={style.color}
                            opacity="0.08"
                            pointerEvents="none"
                          />

                          {/* Graha Glyph + Abbreviation */}
                          <text
                            x={-halfW + 7}
                            y="3.5"
                            fill={style.color}
                            fontSize="11.5"
                            fontWeight="700"
                            fontFamily="'Outfit', sans-serif"
                          >
                            {p.isAsc ? (lang === "ne" ? "ल" : "ASC") : `${style.glyph} ${lang === "ne" ? (t.planets.glyphs[p.name as keyof typeof t.planets.glyphs] || p.label) : p.label}`}
                          </text>

                          {/* Retrograde & Dignity Markers (Positioned in center, safe from degree) */}
                          {hasRetro && hasDignity ? (
                            <g>
                              <text
                                x="-5"
                                y="3.5"
                                textAnchor="middle"
                                fill="var(--amber)"
                                fontSize="9.5"
                                fontWeight="800"
                                fontFamily="'JetBrains Mono', monospace"
                              >
                                ℞
                              </text>
                              <text
                                x="5"
                                y="3.5"
                                textAnchor="middle"
                                fill={p.dignity.isExalted ? "var(--emerald)" : p.dignity.isDebilitated ? "var(--rose)" : "var(--gold-vivid)"}
                                fontSize="10"
                                fontWeight="800"
                              >
                                {p.dignity.symbol}
                              </text>
                            </g>
                          ) : hasRetro ? (
                            <text
                              x="-2"
                              y="3.5"
                              textAnchor="middle"
                              fill="var(--amber)"
                              fontSize="9.5"
                              fontWeight="800"
                              fontFamily="'JetBrains Mono', monospace"
                            >
                              ℞
                            </text>
                          ) : hasDignity ? (
                            <text
                              x="-2"
                              y="3.5"
                              textAnchor="middle"
                              fill={p.dignity.isExalted ? "var(--emerald)" : p.dignity.isDebilitated ? "var(--rose)" : "var(--gold-vivid)"}
                              fontSize="10"
                              fontWeight="800"
                            >
                              {p.dignity.symbol}
                            </text>
                          ) : null}

                          {/* Degrees */}
                          {p.degree && (
                            <text
                              x={halfW - 6}
                              y="3.5"
                              textAnchor="end"
                              fill="var(--text-mid)"
                              fontSize="10"
                              fontWeight="600"
                              fontFamily="'JetBrains Mono', monospace"
                            >
                              {num(p.degree)}
                            </text>
                          )}
                        </g>
                      );
                    });
                  }

                  // 4+ planets: compact 2-column grid
                  const half = Math.ceil(n / 2);
                  const stepY = 24;
                  const pillW = 82;
                  const pillH = 22;
                  const halfW = pillW / 2;

                  return planets.map((p, pIdx) => {
                    const col = pIdx < half ? 0 : 1;
                    const row = pIdx < half ? pIdx : pIdx - half;
                    const posX = col === 0 ? -44 : 44;
                    const posY = (row - (half - 1) / 2) * stepY;
                    const style = GRAHA_STYLES[p.key] || {
                      abbr: p.label, glyph: "•", name: p.name, color: "var(--text-high)", bg: "var(--bg-subtle)", border: "var(--border-subtle)"
                    };

                    return (
                      <g key={pIdx} transform={`translate(${posX}, ${posY})`}>
                        <rect
                          className="graha-pill"
                          x={-halfW}
                          y={-pillH / 2}
                          width={pillW}
                          height={pillH}
                          rx="4"
                          fill="var(--chart-pill-bg)"
                          stroke={style.color}
                          strokeOpacity="0.35"
                          strokeWidth="1.1"
                          filter="url(#pillShadow)"
                        />
                        <rect
                          x={-halfW}
                          y={-pillH / 2}
                          width={pillW}
                          height={pillH}
                          rx="4"
                          fill={style.color}
                          opacity="0.08"
                          pointerEvents="none"
                        />
                        <text
                          x={-halfW + 5}
                          y="3"
                          fill={style.color}
                          fontSize="10.5"
                          fontWeight="700"
                          fontFamily="'Outfit', sans-serif"
                        >
                          {p.isAsc ? (lang === "ne" ? "ल" : "ASC") : (lang === "ne" ? (t.planets.glyphs[p.name as keyof typeof t.planets.glyphs] || p.label) : p.label)}
                        </text>
                        {p.isRetro ? (
                          <text x="-2" y="3" textAnchor="middle" fill="var(--amber)" fontSize="9" fontWeight="800">
                            ℞
                          </text>
                        ) : p.dignity?.symbol ? (
                          <text
                            x="-2"
                            y="3"
                            textAnchor="middle"
                            fill={p.dignity.isExalted ? "var(--emerald)" : p.dignity.isDebilitated ? "var(--rose)" : "var(--gold-vivid)"}
                            fontSize="9"
                            fontWeight="800"
                          >
                            {p.dignity.symbol}
                          </text>
                        ) : null}
                        {p.degree && (
                          <text
                            x={halfW - 5}
                            y="3"
                            textAnchor="end"
                            fill="var(--text-mid)"
                            fontSize="9.5"
                            fontWeight="600"
                            fontFamily="'JetBrains Mono', monospace"
                          >
                            {p.degree}
                          </text>
                        )}
                      </g>
                    );
                  });
                })()}
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
          padding: "var(--space-2-5) var(--space-4)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "var(--space-3)",
          fontSize: "var(--type-label)",
          background: "var(--bg-card)",
          border: "1px solid var(--border-card)",
          borderRadius: "var(--radius-md)",
          width: "100%",
          maxWidth: `${size}px`,
          minHeight: "46px",
          transition: "all 0.2s ease",
        }}
      >
        {activeHouseData && activeBhavaMeta ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", gap: "var(--space-2)", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <span style={{ color: "var(--gold-bright)", fontWeight: 700, fontFamily: "var(--font-serif)" }}>
                {activeBhavaMeta.title}
              </span>
              <span style={{ color: "var(--border-subtle)" }}>|</span>
              <span style={{ color: "var(--cyan-vivid)", fontWeight: 600 }}>
                {activeBhavaMeta.sanskrit}
              </span>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", fontSize: "var(--type-micro)", flexWrap: "wrap" }}>
              <span style={{ color: "var(--text-high)", fontWeight: 600 }}>
                {lang === "ne" ? (t.zodiac.signs[activeHouseData.signName as keyof typeof t.zodiac.signs] || activeHouseData.signName) : `${activeHouseData.signName} (${activeHouseData.signSanskrit})`}
              </span>
              <span style={{ color: "var(--border-subtle)" }}>·</span>
              <span style={{ color: "var(--gold-vivid)", fontWeight: 600 }}>{lang === "ne" ? `स्वामी: ${t.planets.names[activeHouseData.lord as keyof typeof t.planets.names] || activeHouseData.lord}` : `Lord: ${activeHouseData.lord}`}</span>
              <span style={{ color: "var(--border-subtle)" }}>·</span>
              <span style={{ color: "var(--text-mid)" }}>
                {activeHouseData.planets.length > 0
                  ? activeHouseData.planets.map((p) => lang === "ne" ? (t.planets.names[p.name as keyof typeof t.planets.names] || p.name) : p.name).join(", ")
                  : (lang === "ne" ? "ग्रह छैन" : "No grahas")}
              </span>
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", gap: "var(--space-2)", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <span style={{ color: "var(--text-low)", fontSize: "0.82rem" }}>
                {lang === "ne" ? "लग्न" : "Lagna"}: <strong style={{ color: "var(--gold-bright)", fontFamily: "var(--font-mono)" }}>{lang === "ne" ? (t.zodiac.signs[chart.ascendant.sign as keyof typeof t.zodiac.signs] || chart.ascendant.sign) : chart.ascendant.sign} {num(chart.ascendant.degree_in_sign.toFixed(1))}°</strong>
              </span>
              <span style={{ color: "var(--border-subtle)" }}>|</span>
              {(() => {
                const moon = chart.planets.find(p => p.name === "Moon");
                return (
                  <span style={{ color: "var(--text-low)", fontSize: "0.82rem" }}>
                    {lang === "ne" ? "चन्द्र" : "Moon"}: <strong style={{ color: "var(--text-high)", fontFamily: "var(--font-mono)" }}>{moon ? `${lang === "ne" ? (t.zodiac.signs[moon.sign as keyof typeof t.zodiac.signs] || moon.sign) : moon.sign} ${num(moon.degree_in_sign.toFixed(1))}°` : "Moon"}</strong>
                  </span>
                );
              })()}
            </div>
            <span style={{ color: "var(--text-mid)", fontSize: "0.76rem" }}>
              {lang === "ne" ? "भाव विवरण हेर्न कुण्डलीमा छुनुहोस्" : "Tap or hover house chamber to inspect"}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
