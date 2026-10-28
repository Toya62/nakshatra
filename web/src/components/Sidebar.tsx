"use client";

import React from "react";
import {
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";
import { NakshatraLogo } from "@/components/NakshatraLogo";
import {
  KundaliIcon,
  GocharIcon,
  DashaIcon,
  PanchangaIcon,
  MatchingIcon,
  MuhurthaIcon,
  RemediesIcon,
  ConsultationIcon,
} from "@/components/VedicIcons";

export type TabId =
  | "chart"
  | "transits"
  | "dasha"
  | "panchanga"
  | "compatibility"
  | "muhurtha"
  | "remedies"
  | "consult";

interface Props {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  slim: boolean;
  onToggleSlim: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

const TABS: {
  id: TabId;
  label: string;
  Icon: React.ElementType;
  accent: {
    color: string;
    bg: string;
    border: string;
  };
  hint?: string;
}[] = [
  {
    id: "chart",
    label: "Birth Chart",
    Icon: KundaliIcon,
    accent: {
      color: "var(--graha-sun, #d97706)",
      bg: "rgba(217, 119, 6, 0.12)",
      border: "rgba(217, 119, 6, 0.28)",
    },
  },
  {
    id: "transits",
    label: "Transits (Gochar)",
    Icon: GocharIcon,
    accent: {
      color: "var(--graha-saturn, #2563eb)",
      bg: "rgba(37, 99, 235, 0.10)",
      border: "rgba(37, 99, 235, 0.25)",
    },
  },
  {
    id: "dasha",
    label: "Vimshottari Dasha",
    Icon: DashaIcon,
    accent: {
      color: "var(--graha-jupiter, #b45309)",
      bg: "rgba(180, 83, 9, 0.10)",
      border: "rgba(180, 83, 9, 0.25)",
    },
  },
  {
    id: "panchanga",
    label: "Daily Panchanga",
    Icon: PanchangaIcon,
    accent: {
      color: "var(--graha-mercury, #059669)",
      bg: "rgba(5, 150, 105, 0.10)",
      border: "rgba(5, 150, 105, 0.25)",
    },
  },
  {
    id: "compatibility",
    label: "Kundali Matching",
    Icon: MatchingIcon,
    accent: {
      color: "var(--graha-venus, #e11d48)",
      bg: "rgba(225, 29, 72, 0.10)",
      border: "rgba(225, 29, 72, 0.25)",
    },
  },
  {
    id: "muhurtha",
    label: "Muhurtha & Horas",
    Icon: MuhurthaIcon,
    accent: {
      color: "var(--graha-sun, #d97706)",
      bg: "rgba(217, 119, 6, 0.10)",
      border: "rgba(217, 119, 6, 0.25)",
    },
  },
  {
    id: "remedies",
    label: "Remedies & Upayas",
    Icon: RemediesIcon,
    accent: {
      color: "var(--graha-rahu, #7c3aed)",
      bg: "rgba(124, 58, 237, 0.10)",
      border: "rgba(124, 58, 237, 0.25)",
    },
    hint: "Parashari & Lal Kitab",
  },
];

const CONSULT = {
  id: "consult" as TabId,
  label: "AI Consultation",
  Icon: ConsultationIcon,
  accent: {
    color: "#6366f1",
    bg: "rgba(99, 102, 241, 0.12)",
    border: "rgba(99, 102, 241, 0.30)",
  },
};

export const Sidebar: React.FC<Props> = ({
  activeTab,
  onTabChange,
  slim,
  onToggleSlim,
  mobileOpen,
  onCloseMobile,
}) => {
  const handleTab = (id: TabId) => {
    onTabChange(id);
    onCloseMobile();
  };

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="sidebar-backdrop"
          style={{ display: "block" }}
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      <aside
        className={`app-sidebar${mobileOpen ? " open" : ""}`}
        aria-label="Primary navigation"
        style={{
          background: "var(--bg-base)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          borderRight: "1px solid var(--border-subtle)",
          display: "flex",
          flexDirection: "column",
          overflowX: "hidden",
          overflowY: "auto",
          transition: "width 0.25s ease",
          width: slim ? "var(--sidebar-w-slim)" : "var(--sidebar-w)",
        }}
      >
        {/* Desktop Sidebar Rail Header: collapse / expand toggle */}
        <div
          className="mobile-hide"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: slim ? "center" : "space-between",
            padding: slim ? "10px 0" : "10px 14px",
            borderBottom: "1px solid var(--border-subtle)",
            minHeight: "44px",
            flexShrink: 0,
          }}
        >
          {!slim && (
            <span
              style={{
                fontSize: "11px",
                fontWeight: 700,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                color: "var(--text-low)",
                fontFamily: "var(--font-sans)",
                userSelect: "none",
              }}
            >
              Navigation
            </span>
          )}
          <button
            type="button"
            onClick={onToggleSlim}
            aria-label={slim ? "Expand sidebar" : "Collapse sidebar"}
            title={slim ? "Expand sidebar" : "Collapse sidebar"}
            className="btn-icon"
            style={{
              background: "var(--bg-subtle)",
              border: "1px solid var(--border-subtle)",
              color: "var(--text-mid)",
              cursor: "pointer",
              width: "28px",
              height: "28px",
              borderRadius: "var(--radius-sm)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 0.18s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--gold-border)";
              e.currentTarget.style.color = "var(--gold-vivid)";
              e.currentTarget.style.background = "var(--bg-input)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--border-subtle)";
              e.currentTarget.style.color = "var(--text-mid)";
              e.currentTarget.style.background = "var(--bg-subtle)";
            }}
          >
            {slim ? <ChevronRight size={15} aria-hidden="true" /> : <ChevronLeft size={15} aria-hidden="true" />}
          </button>
        </div>

        {/* Mobile drawer header with Close [X] */}
        <div
          className="mobile-only"
          style={{
            alignItems: "center",
            justifyContent: "space-between",
            padding: "12px 14px",
            borderBottom: "1px solid var(--border-subtle)",
            minHeight: "44px",
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <NakshatraLogo size={26} />
            <span
              className="serif-display gold-gradient-text"
              style={{ fontSize: "0.95rem", fontWeight: 700, letterSpacing: "0.08em" }}
            >
              NAKSHATRA
            </span>
          </div>
          <button
            type="button"
            onClick={onCloseMobile}
            aria-label="Close navigation drawer"
            title="Close drawer"
            className="btn-icon"
            style={{
              width: "28px",
              height: "28px",
              background: "var(--bg-subtle)",
              border: "1px solid var(--border-subtle)",
              color: "var(--text-high)",
              borderRadius: "var(--radius-sm)",
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <X size={15} aria-hidden="true" />
          </button>
        </div>

        {/* Nav items */}
        <nav
          role="tablist"
          aria-label="App sections"
          style={{
            flex: 1,
            padding: "var(--space-3) var(--space-2)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-1)",
          }}
        >
          {TABS.map(({ id, label, Icon, accent }) => {
            const active = activeTab === id;
            return (
              <button
                key={id}
                role="tab"
                aria-selected={active}
                aria-label={slim ? label : undefined}
                title={slim ? label : undefined}
                onClick={() => handleTab(id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-3)",
                  padding: slim ? "8px 0" : "7px 10px",
                  justifyContent: slim ? "center" : "flex-start",
                  width: "100%",
                  borderRadius: "var(--radius-md)",
                  border: "none",
                  borderLeft: active ? "3px solid var(--gold-vivid)" : "3px solid transparent",
                  background: active ? "linear-gradient(90deg, var(--gold-dim) 0%, transparent 100%)" : "transparent",
                  color: active ? "var(--text-high)" : "var(--text-mid)",
                  fontFamily: "var(--font-sans)",
                  fontSize: "0.875rem",
                  fontWeight: active ? 600 : 500,
                  cursor: "pointer",
                  transition: "all 0.18s ease",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  flexShrink: 0,
                }}
                onMouseEnter={(e) => {
                  if (!active) {
                    e.currentTarget.style.background = "var(--bg-subtle)";
                    e.currentTarget.style.color = "var(--text-high)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!active) {
                    e.currentTarget.style.background = "transparent";
                    e.currentTarget.style.color = "var(--text-mid)";
                  }
                }}
              >
                {/* 32x32px Jewel Icon Tile with Vedic Planetary Accent */}
                <div
                  style={{
                    width: "32px",
                    height: "32px",
                    borderRadius: "8px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    background: active ? accent.bg : "var(--bg-subtle)",
                    border: `1px solid ${active ? accent.border : "var(--border-subtle)"}`,
                    color: active ? accent.color : "var(--text-mid)",
                    boxShadow: active ? `0 0 10px ${accent.bg}` : "none",
                    transition: "all 0.18s ease",
                  }}
                  aria-hidden="true"
                >
                  <Icon size={20} style={{ color: active ? accent.color : "currentColor" }} />
                </div>
                {!slim && (
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", letterSpacing: "0.01em" }}>
                    {label}
                  </span>
                )}
              </button>
            );
          })}

          {/* Divider before AI Consultation */}
          <div
            style={{
              borderTop: "1px solid var(--border-subtle)",
              margin: "var(--space-2) 0",
            }}
            role="separator"
          />

          {/* Consultation — bottom-aligned, third-eye indigo & gold tinted */}
          {(() => {
            const { id, label, Icon, accent } = CONSULT;
            const active = activeTab === id;
            return (
              <button
                role="tab"
                aria-selected={active}
                aria-label={slim ? label : undefined}
                title={slim ? label : undefined}
                onClick={() => handleTab(id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-3)",
                  padding: slim ? "8px 0" : "7px 10px",
                  justifyContent: slim ? "center" : "flex-start",
                  width: "100%",
                  borderRadius: "var(--radius-md)",
                  border: "none",
                  borderLeft: active ? "3px solid var(--gold-vivid)" : "3px solid transparent",
                  background: active
                    ? "linear-gradient(90deg, var(--gold-dim) 0%, transparent 100%)"
                    : "var(--gold-dim)",
                  color: active ? "var(--gold-bright)" : "var(--gold-vivid)",
                  fontFamily: "var(--font-sans)",
                  fontSize: "0.875rem",
                  fontWeight: active ? 600 : 500,
                  cursor: "pointer",
                  transition: "all 0.18s ease",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  flexShrink: 0,
                }}
              >
                <div
                  style={{
                    width: "32px",
                    height: "32px",
                    borderRadius: "8px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    background: active ? accent.bg : "var(--bg-input)",
                    border: `1px solid ${active ? accent.border : "var(--gold-border)"}`,
                    color: active ? accent.color : "var(--gold-vivid)",
                    boxShadow: active ? `0 0 12px ${accent.bg}` : "0 0 6px var(--gold-dim)",
                    transition: "all 0.18s ease",
                  }}
                  aria-hidden="true"
                >
                  <Icon size={20} style={{ color: active ? accent.color : "currentColor" }} />
                </div>
                {!slim && <span style={{ letterSpacing: "0.01em" }}>{label}</span>}
              </button>
            );
          })()}
        </nav>
      </aside>
    </>
  );
};

/** Hamburger button — rendered inside the header on mobile */
export const HamburgerButton: React.FC<{
  open: boolean;
  onToggle: () => void;
}> = ({ open, onToggle }) => (
  <button
    onClick={onToggle}
    aria-label={open ? "Close navigation menu" : "Open navigation menu"}
    aria-expanded={open}
    className="btn-ghost mobile-only"
    style={{ padding: "6px", display: "none" }}
  >
    <Menu size={20} aria-hidden="true" />
  </button>
);
