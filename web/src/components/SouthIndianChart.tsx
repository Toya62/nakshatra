"use client";

import React, { useState, useMemo, forwardRef } from "react";
import { ChartData } from "@/lib/types";
import { getVargaAscendant, getVargaMoon } from "@/lib/varga";
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
  Asc: { abbr: "ASC", glyph: "⟐", name: "Ascendant", color: "var(--graha-asc, #fde047)", bg: "rgba(253, 224, 71, 0.18)", border: "rgba(253, 224, 71, 0.55)" },
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

// Fixed South Indian Zodiac Cell coordinates in 4x4 matrix
// Cell size = 130px, Total size = 520px
const SOUTH_INDIAN_SIGN_COORDS: Record<number, { col: number; row: number }> = {
  12: { col: 0, row: 0 }, // Pisces (top-left)
  1:  { col: 1, row: 0 }, // Aries
  2:  { col: 2, row: 0 }, // Taurus
  3:  { col: 3, row: 0 }, // Gemini (top-right)
  4:  { col: 3, row: 1 }, // Cancer
  5:  { col: 3, row: 2 }, // Leo
  6:  { col: 3, row: 3 }, // Virgo (bottom-right)
  7:  { col: 2, row: 3 }, // Libra
  8:  { col: 1, row: 3 }, // Scorpio
  9:  { col: 0, row: 3 }, // Sagittarius (bottom-left)
  10: { col: 0, row: 2 }, // Capricorn
  11: { col: 0, row: 1 }, // Aquarius
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

export const SouthIndianChart = forwardRef<SVGSVGElement, Props>(({ chart, varga = "D1", size = 520 }, ref) => {
  const { t, lang, num } = useLanguage();
  const [hoveredHouse, setHoveredHouse] = useState<number | null>(null);

  const totalSize = 520;
  const cellSize = 130;

  const vKey = varga.toUpperCase();
  const vData = chart.vargas && chart.vargas[vKey];
  const ascSignName = (vData && vKey !== "D1")
    ? (vData["Ascendant"] || chart.ascendant.sign)
    : chart.ascendant.sign;
  const ascSignNum = SIGN_NAMES_TO_NUM[ascSignName] || 1;

  // Map planets to sign numbers
  const signPlanets = useMemo(() => {
    const map: Record<number, PlanetBadgeData[]> = {
      1: [], 2: [], 3: [], 4: [], 5: [], 6: [],
      7: [], 8: [], 9: [], 10: [], 11: [], 12: [],
    };

    if (vData && vKey !== "D1") {
      const ascSign = vData["Ascendant"] || chart.ascendant.sign;
      const ascNum = SIGN_NAMES_TO_NUM[ascSign] || 1;
      map[ascNum]?.push({
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
        map[signNumLocal]?.push({
          key: abbr,
          label: abbr,
          name: p.name,
          isRetro: p.retrograde,
          dignity: getGrahaDignity(p.name, signNumLocal),
        });
      }
    } else {
      map[ascSignNum]?.push({
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
        map[signNumLocal]?.push({
          key: abbr,
          label: abbr,
          name: p.name,
          isRetro: p.retrograde,
          degree: `${p.degree_in_sign.toFixed(1)}°`,
          dignity: getGrahaDignity(p.name, signNumLocal),
        });
      }
    }

    return map;
  }, [chart, vData, vKey, ascSignNum]);

  // House calculation per sign
  const signHouseData = useMemo(() => {
    const res: Record<number, { houseNum: number; isKendra: boolean; isTrikona: boolean; isDusthana: boolean }> = {};
    for (let signNum = 1; signNum <= 12; signNum++) {
      const houseNum = ((signNum - ascSignNum + 12) % 12) + 1;
      const isKendra = [1, 4, 7, 10].includes(houseNum);
      const isTrikona = [1, 5, 9].includes(houseNum);
      const isDusthana = [6, 8, 12].includes(houseNum);
      res[signNum] = { houseNum, isKendra, isTrikona, isDusthana };
    }
    return res;
  }, [ascSignNum]);

  const activeHouseData = hoveredHouse ? BHAVA_METADATA[hoveredHouse] : null;
  const activeSignInfo = hoveredHouse ? ZODIAC_METADATA[((ascSignNum - 1 + (hoveredHouse - 1)) % 12) + 1] : null;

  // Center hub + footer strip follow the selected divisional, like the wheel.
  const vargaAsc = useMemo(() => getVargaAscendant(chart, varga), [chart, varga]);
  const vargaMoon = useMemo(() => getVargaMoon(chart, varga), [chart, varga]);

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: "100%", maxWidth: `${size}px` }}>
      <svg
        ref={ref}
        viewBox={`0 0 ${totalSize} ${totalSize}`}
        style={{
          width: "100%",
          height: "auto",
          maxWidth: `${size}px`,
          aspectRatio: "1/1",
          background: "#0c1222",
          borderRadius: "var(--radius-lg)",
          border: "1px solid rgba(148, 163, 184, 0.2)",
          boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.4)",
          userSelect: "none",
        }}
      >
        <defs>
          <linearGradient id="southKendraGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#c5a059" stopOpacity="0.14" />
            <stop offset="100%" stopColor="#c5a059" stopOpacity="0.04" />
          </linearGradient>
          <linearGradient id="southTrikonaGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.03" />
          </linearGradient>
          <linearGradient id="southDusthanaGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.02" />
          </linearGradient>
          <pattern id="southLagnaHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="8" stroke="#fde047" strokeWidth="1.5" strokeOpacity="0.4" />
          </pattern>
        </defs>

        {/* 12 Outer Sign Boxes */}
        {Object.entries(SOUTH_INDIAN_SIGN_COORDS).map(([sStr, pos]) => {
          const signNum = Number(sStr);
          const x = pos.col * cellSize;
          const y = pos.row * cellSize;
          const { houseNum, isKendra, isTrikona, isDusthana } = signHouseData[signNum];
          const isLagna = houseNum === 1;
          const isHovered = hoveredHouse === houseNum;
          const planets = signPlanets[signNum] || [];
          const meta = ZODIAC_METADATA[signNum];

          let fill = "#0f172a";
          if (isHovered) fill = "rgba(197, 160, 89, 0.22)";
          else if (isLagna) fill = "rgba(253, 224, 71, 0.12)";
          else if (isKendra) fill = "url(#southKendraGrad)";
          else if (isTrikona) fill = "url(#southTrikonaGrad)";
          else if (isDusthana) fill = "url(#southDusthanaGrad)";

          return (
            <g
              key={signNum}
              onClick={() => setHoveredHouse(isHovered ? null : houseNum)}
              onMouseEnter={() => setHoveredHouse(houseNum)}
              onMouseLeave={() => setHoveredHouse(null)}
              style={{ cursor: "pointer", transition: "all 0.15s ease" }}
            >
              {/* Box background */}
              <rect
                x={x}
                y={y}
                width={cellSize}
                height={cellSize}
                fill={fill}
                stroke={isHovered ? "#d8b26e" : isLagna ? "#fde047" : "rgba(148, 163, 184, 0.22)"}
                strokeWidth={isHovered || isLagna ? 1.8 : 1}
              />

              {/* Traditional South Indian Lagna Corner Hatch Indicator */}
              {isLagna && (
                <polygon
                  points={`${x},${y} ${x + 36},${y} ${x},${y + 36}`}
                  fill="url(#southLagnaHatch)"
                  stroke="#fde047"
                  strokeWidth="1"
                  strokeOpacity="0.6"
                />
              )}

              {/* Sign Name & Number Header */}
              <text
                x={x + 8}
                y={y + 16}
                fill={isLagna ? "#fde047" : "rgba(248, 250, 252, 0.85)"}
                fontSize="11"
                fontWeight={700}
                fontFamily="var(--font-sans), sans-serif"
              >
                {lang === "ne" ? meta.sanskrit : meta.english.slice(0, 3)}
              </text>

              <text
                x={x + cellSize - 8}
                y={y + 16}
                textAnchor="end"
                fill={isLagna ? "#fde047" : "rgba(148, 163, 184, 0.7)"}
                fontSize="10"
                fontFamily="var(--font-mono), monospace"
                fontWeight={600}
              >
                {isLagna ? "H1 ⟐" : `H${num(houseNum)}`}
              </text>

              {/* Sub-label: Sanskrit or English element/sign number */}
              <text
                x={x + 8}
                y={y + 27}
                fill="rgba(148, 163, 184, 0.6)"
                fontSize="8.5"
                fontFamily="var(--font-sans), sans-serif"
              >
                {meta.sanskrit} · {num(signNum)}
              </text>

              {/* Planet Badges inside Sign Box */}
              <g transform={`translate(${x + 6}, ${y + 34})`}>
                {planets.map((p, idx) => {
                  const style = GRAHA_STYLES[p.key] || {
                    abbr: p.key,
                    glyph: "●",
                    name: p.name,
                    color: "#f8fafc",
                    bg: "rgba(255, 255, 255, 0.1)",
                    border: "rgba(255, 255, 255, 0.2)",
                  };

                  const badgeY = idx * 18;
                  if (badgeY > cellSize - 40) return null; // Prevent box overflow

                  return (
                    <g key={p.key + idx} transform={`translate(0, ${badgeY})`}>
                      {/* Badge pill */}
                      <rect
                        x={0}
                        y={0}
                        width={cellSize - 12}
                        height={16}
                        rx={3}
                        fill={style.bg}
                        stroke={style.border}
                        strokeWidth="0.8"
                      />

                      {/* Glyph & Abbreviation */}
                      <text
                        x={5}
                        y={11.5}
                        fill={style.color}
                        fontSize="9"
                        fontWeight={700}
                        fontFamily="var(--font-sans), sans-serif"
                      >
                        {style.glyph} {p.label}
                      </text>

                      {/* Dignity & Retrograde */}
                      <text
                        x={46}
                        y={11.5}
                        fill={p.dignity.isExalted ? "#10b981" : p.dignity.isDebilitated ? "#f43f5e" : "#f59e0b"}
                        fontSize="9"
                        fontWeight={700}
                      >
                        {p.dignity.symbol} {p.isRetro ? "(R)" : ""}
                      </text>

                      {/* Degrees */}
                      {p.degree && (
                        <text
                          x={cellSize - 18}
                          y={11.5}
                          textAnchor="end"
                          fill="rgba(248, 250, 252, 0.75)"
                          fontSize="8.5"
                          fontFamily="var(--font-mono), monospace"
                        >
                          {num(p.degree)}
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
            </g>
          );
        })}

        {/* Center 2x2 Cell (Merged Information Hub) */}
        <g transform={`translate(${cellSize}, ${cellSize})`}>
          <rect
            x={0}
            y={0}
            width={cellSize * 2}
            height={cellSize * 2}
            fill="#090d16"
            stroke="rgba(197, 160, 89, 0.35)"
            strokeWidth="1.5"
          />

          {/* Sacred geometry geometric watermark */}
          <circle cx={cellSize} cy={cellSize} r={75} fill="none" stroke="rgba(197, 160, 89, 0.08)" strokeWidth="1" />
          <polygon
            points={`${cellSize},${cellSize - 70} ${cellSize + 60},${cellSize + 35} ${cellSize - 60},${cellSize + 35}`}
            fill="none"
            stroke="rgba(197, 160, 89, 0.08)"
            strokeWidth="1"
          />
          <polygon
            points={`${cellSize},${cellSize + 70} ${cellSize + 60},${cellSize - 35} ${cellSize - 60},${cellSize - 35}`}
            fill="none"
            stroke="rgba(56, 189, 248, 0.08)"
            strokeWidth="1"
          />

          {/* Center Content */}
          <text
            x={cellSize}
            y={48}
            textAnchor="middle"
            fill="#f0d59e"
            fontSize="18"
            fontWeight={700}
            fontFamily="var(--font-serif), Georgia, serif"
            letterSpacing="2"
          >
            {vKey} {vKey === "D1" ? "RASI" : "VARGA"}
          </text>

          <text
            x={cellSize}
            y={70}
            textAnchor="middle"
            fill="#38bdf8"
            fontSize="10"
            fontWeight={600}
            fontFamily="var(--font-sans), sans-serif"
            letterSpacing="1.2"
          >
            {lang === "ne" ? "दक्षिण भारतीय कुण्डली" : "SOUTH INDIAN CHITRA"}
          </text>

          <line
            x1={50}
            y1={86}
            x2={cellSize * 2 - 50}
            y2={86}
            stroke="rgba(148, 163, 184, 0.2)"
            strokeWidth="1"
          />

          {/* Key Ephemeris Details in Center */}
          <g transform={`translate(${cellSize}, 110)`} textAnchor="middle">
            <text fill="rgba(148, 163, 184, 0.8)" fontSize="10" fontFamily="var(--font-sans)">
              {lang === "ne" ? "लग्न" : "Lagna"}:{" "}
              <tspan fill="#fde047" fontWeight={700} fontFamily="var(--font-mono)">
                {vargaAsc.sign} {num(vargaAsc.degreeInSign.toFixed(1))}°
              </tspan>
            </text>

            <text y={24} fill="rgba(148, 163, 184, 0.8)" fontSize="10" fontFamily="var(--font-sans)">
              {lang === "ne" ? "नक्षत्र" : "Nakshatra"}:{" "}
              <tspan fill="#f8fafc" fontWeight={600}>
                {vargaAsc.nakshatra} (P{num(vargaAsc.pada)})
              </tspan>
            </text>

            <text y={48} fill="rgba(148, 163, 184, 0.8)" fontSize="10" fontFamily="var(--font-sans)">
              {lang === "ne" ? "अयनांश" : "Ayanamsa"}:{" "}
              <tspan fill="#d8b26e" fontWeight={600}>
                {chart.ayanamsa?.name || "Lahiri"}
              </tspan>
            </text>

            <text y={80} fill="rgba(148, 163, 184, 0.55)" fontSize="9" fontFamily="var(--font-sans)">
              {lang === "ne" ? "स्थानिक कुण्डली अवलोकन" : "Clockwise Fixed Zodiac Grid"}
            </text>
          </g>
        </g>
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
        {activeHouseData && activeSignInfo ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", gap: "var(--space-2)", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <span style={{ color: "var(--gold-bright)", fontWeight: 700, fontFamily: "var(--font-serif)" }}>
                {activeHouseData.title}
              </span>
              <span style={{ color: "var(--border-subtle)" }}>|</span>
              <span style={{ color: "var(--cyan-vivid)", fontWeight: 600 }}>
                {activeHouseData.sanskrit}
              </span>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", fontSize: "var(--type-micro)", flexWrap: "wrap" }}>
              <span style={{ color: "var(--text-high)", fontWeight: 600 }}>
                {lang === "ne" ? (t.zodiac.signs[activeSignInfo.english as keyof typeof t.zodiac.signs] || activeSignInfo.english) : `${activeSignInfo.english} (${activeSignInfo.sanskrit})`}
              </span>
              <span style={{ color: "var(--border-subtle)" }}>·</span>
              <span style={{ color: "var(--gold-vivid)", fontWeight: 600 }}>
                {lang === "ne" ? `स्वामी: ${t.planets.names[activeSignInfo.lord as keyof typeof t.planets.names] || activeSignInfo.lord}` : `Lord: ${activeSignInfo.lord}`}
              </span>
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", gap: "var(--space-2)", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <span style={{ color: "var(--text-low)", fontSize: "0.82rem" }}>
                {lang === "ne" ? "लग्न" : "Lagna"}: <strong style={{ color: "var(--gold-bright)", fontFamily: "var(--font-mono)" }}>{vargaAsc.sign} {num(vargaAsc.degreeInSign.toFixed(1))}°</strong>
              </span>
              <span style={{ color: "var(--border-subtle)" }}>|</span>
              <span style={{ color: "var(--text-low)", fontSize: "0.82rem" }}>
                {lang === "ne" ? "चन्द्र" : "Moon"}: <strong style={{ color: "var(--text-high)", fontFamily: "var(--font-mono)" }}>{vargaMoon ? `${vargaMoon.sign} ${num(vargaMoon.degreeInSign.toFixed(1))}°` : "Moon"}</strong>
              </span>
            </div>
            <span style={{ color: "var(--text-mid)", fontSize: "0.76rem" }}>
              {lang === "ne" ? "भाव विवरण हेर्न राशि कोठामा छुनुहोस्" : "Tap sign cell to inspect house significations"}
            </span>
          </div>
        )}
      </div>
    </div>
  );
});

SouthIndianChart.displayName = "SouthIndianChart";
