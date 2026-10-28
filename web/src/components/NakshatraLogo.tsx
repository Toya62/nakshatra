"use client";

import React from "react";

interface Props {
  size?: number;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * NakshatraLogo — Sacred Vedic 8-Pointed Ashtadala Celestial Emblem
 * Dual-theme aware vector emblem featuring:
 * 1. 12-Rashi celestial coordinate outer ring with 12 cardinal ticks
 * 2. 8-Pointed Star of Lakshmi / Navagraha Yantra (interlocking Ashtakona)
 * 3. Central Surya bindu core with radiating cosmic cardinal rays
 */
export const NakshatraLogo: React.FC<Props> = ({ size = 38, className, style }) => {
  return (
    <div
      className={className}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: "10px",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg-input)",
        border: "1px solid var(--gold-border)",
        boxShadow: "0 2px 10px var(--gold-dim), inset 0 1px 0 rgba(255, 255, 255, 0.12)",
        flexShrink: 0,
        position: "relative",
        overflow: "hidden",
        ...style,
      }}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 40 40"
        width={size - 4}
        height={size - 4}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ display: "block" }}
      >
        <defs>
          {/* Dual-theme celestial gold gradients */}
          <linearGradient id="nakshatra-gold-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffd875" />
            <stop offset="50%" stopColor="#dfb15b" />
            <stop offset="100%" stopColor="#9a6e1a" />
          </linearGradient>

          <linearGradient id="nakshatra-core-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.9" />
            <stop offset="40%" stopColor="#ffd875" />
            <stop offset="100%" stopColor="#b45309" />
          </linearGradient>

          <radialGradient id="nakshatra-ambient-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#dfb15b" stopOpacity="0.32" />
            <stop offset="70%" stopColor="#b45309" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#000000" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Ambient radial center glow */}
        <circle cx="20" cy="20" r="18" fill="url(#nakshatra-ambient-glow)" />

        {/* Outer 12-Rashi Zodiac Coordinate Ring */}
        <circle
          cx="20"
          cy="20"
          r="17"
          stroke="url(#nakshatra-gold-grad)"
          strokeWidth="1.2"
          strokeOpacity="0.75"
        />
        <circle
          cx="20"
          cy="20"
          r="14.5"
          stroke="url(#nakshatra-gold-grad)"
          strokeWidth="0.75"
          strokeDasharray="1.2 2.6"
          strokeOpacity="0.6"
        />

        {/* 12 Rashi Ticks around perimeter */}
        {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((deg) => {
          const isCardinal = deg % 90 === 0;
          return (
            <line
              key={deg}
              x1="20"
              y1={isCardinal ? "3.2" : "4.4"}
              x2="20"
              y2={isCardinal ? "6.8" : "5.8"}
              stroke="url(#nakshatra-gold-grad)"
              strokeWidth={isCardinal ? "1.4" : "0.8"}
              strokeLinecap="round"
              transform={`rotate(${deg} 20 20)`}
              strokeOpacity={isCardinal ? "0.9" : "0.5"}
            />
          );
        })}

        {/* Sacred Ashtakona (8-pointed interlocking Yantra stars) */}
        {/* Square 1: cardinal */}
        <rect
          x="10"
          y="10"
          width="20"
          height="20"
          rx="1"
          stroke="url(#nakshatra-gold-grad)"
          strokeWidth="1.3"
          strokeOpacity="0.85"
        />
        {/* Square 2: 45 degree rotation */}
        <rect
          x="10"
          y="10"
          width="20"
          height="20"
          rx="1"
          transform="rotate(45 20 20)"
          stroke="url(#nakshatra-gold-grad)"
          strokeWidth="1.3"
          strokeOpacity="0.85"
        />

        {/* Inner Diamond Sanctum */}
        <polygon
          points="20,11.5 28.5,20 20,28.5 11.5,20"
          stroke="url(#nakshatra-gold-grad)"
          strokeWidth="0.9"
          strokeOpacity="0.6"
          fill="none"
        />

        {/* Cardinal Cross Axis Rays */}
        <line x1="20" y1="9" x2="20" y2="31" stroke="url(#nakshatra-gold-grad)" strokeWidth="0.8" strokeOpacity="0.5" />
        <line x1="9" y1="20" x2="31" y2="20" stroke="url(#nakshatra-gold-grad)" strokeWidth="0.8" strokeOpacity="0.5" />

        {/* Central Navagraha Surya Bindu Core */}
        <circle
          cx="20"
          cy="20"
          r="4.2"
          fill="url(#nakshatra-core-grad)"
          stroke="url(#nakshatra-gold-grad)"
          strokeWidth="1.2"
        />
        <circle cx="20" cy="20" r="1.6" fill="#ffffff" />
      </svg>
    </div>
  );
};
