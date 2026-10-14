"use client";

import React from "react";
import { Activity, Menu, X } from "lucide-react";

// Re-export TabId from Sidebar so existing imports still work
export type { TabId } from "@/components/Sidebar";

interface Props {
  apiStatus: "connected" | "offline" | "checking";
  mobileMenuOpen: boolean;
  onToggleMobile: () => void;
}

export const Navbar: React.FC<Props> = ({
  apiStatus,
  mobileMenuOpen,
  onToggleMobile,
}) => {
  return (
    <header
      className="app-header"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 var(--space-6)",
        background: "var(--bg-base)",
        borderBottom: "1px solid var(--border-subtle)",
        position: "sticky",
        top: 0,
        zIndex: 100,
        backdropFilter: "blur(18px)",
        WebkitBackdropFilter: "blur(18px)",
        gap: "var(--space-3)",
      }}
    >
      {/* Left — hamburger (mobile) + wordmark */}
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
        {/* Hamburger — visible only on mobile via CSS */}
        <button
          onClick={onToggleMobile}
          aria-label={mobileMenuOpen ? "Close navigation" : "Open navigation"}
          aria-expanded={mobileMenuOpen}
          aria-controls="app-sidebar"
          style={{
            background: "transparent",
            border: "none",
            color: "var(--text-mid)",
            cursor: "pointer",
            padding: "6px",
            borderRadius: "var(--radius-sm)",
            display: "none", /* shown via media query below */
          }}
          className="hamburger-btn"
        >
          {mobileMenuOpen
            ? <X size={20} aria-hidden="true" />
            : <Menu size={20} aria-hidden="true" />}
        </button>

        {/* Logo mark */}
        <div
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "9px",
            background: "linear-gradient(135deg, #e5b94c 0%, #7c3aed 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            boxShadow: "var(--gold-glow)",
          }}
          aria-hidden="true"
        >
          {/* Nakshatra glyph — ✦ */}
          <span
            style={{
              color: "#fff",
              fontSize: "14px",
              fontWeight: 700,
              lineHeight: 1,
              fontFamily: "var(--font-serif)",
            }}
          >
            ✦
          </span>
        </div>

        <div>
          <h1
            className="serif-display gold-gradient-text"
            style={{ fontSize: "1.2rem", fontWeight: 700, lineHeight: 1, letterSpacing: "0.1em" }}
          >
            NAKSHATRA
          </h1>
          <p
            style={{
              fontSize: "var(--type-micro)",
              color: "var(--text-low)",
              letterSpacing: "0.09em",
              marginTop: "2px",
            }}
          >
            VEDIC ASTROLOGY ENGINE
          </p>
        </div>
      </div>

      {/* Right — API status */}
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
        <div
          className={`badge ${
            apiStatus === "connected"
              ? "badge-emerald"
              : apiStatus === "checking"
              ? "badge-cyan"
              : "badge-rose"
          }`}
          style={{ gap: "5px", fontSize: "var(--type-micro)" }}
          title={`Backend API: ${apiStatus}`}
        >
          <Activity size={11} aria-hidden="true" />
          <span>{apiStatus === "checking" ? "connecting…" : apiStatus}</span>
        </div>
      </div>
    </header>
  );
};
