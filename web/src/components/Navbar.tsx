"use client";

import React from "react";
import { Activity, Menu, X } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";

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
            width: "34px",
            height: "34px",
            borderRadius: "8px",
            overflow: "hidden",
            border: "1px solid rgba(223, 177, 91, 0.4)",
            boxShadow: "0 0 12px rgba(223, 177, 91, 0.25)",
            flexShrink: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "#080c16",
          }}
          aria-hidden="true"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/app-icon.jpg"
            alt="Nakshatra Emblem"
            width={34}
            height={34}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
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

      {/* Right — Theme Toggle + API status */}
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
        <ThemeToggle />
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
