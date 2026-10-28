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
  onToggleSlim?: () => void;
  sidebarSlim?: boolean;
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
      {/* Left — Brand & Logo (preceded by hamburger toggle on mobile only) */}
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
        {/* Mobile drawer toggle — hidden on desktop (>768px), visible on mobile */}
        <button
          type="button"
          onClick={onToggleMobile}
          aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={mobileMenuOpen}
          aria-controls="app-sidebar"
          title={mobileMenuOpen ? "Close navigation" : "Open navigation"}
          className="btn-icon hamburger-btn mobile-only"
          style={{
            background: "var(--bg-subtle)",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-high)",
            cursor: "pointer",
            width: "36px",
            height: "36px",
            borderRadius: "var(--radius-md)",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.18s ease",
            flexShrink: 0,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = "var(--gold-border)";
            e.currentTarget.style.color = "var(--gold-vivid)";
            e.currentTarget.style.background = "var(--bg-input)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = "var(--border-subtle)";
            e.currentTarget.style.color = "var(--text-high)";
            e.currentTarget.style.background = "var(--bg-subtle)";
          }}
        >
          {mobileMenuOpen
            ? <X size={18} aria-hidden="true" />
            : <Menu size={18} aria-hidden="true" />}
        </button>

        {/* Logo mark */}
        <div
          style={{
            width: "34px",
            height: "34px",
            borderRadius: "8px",
            overflow: "hidden",
            border: "1px solid var(--gold-border)",
            boxShadow: "0 0 12px var(--gold-dim)",
            flexShrink: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "var(--bg-input)",
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
