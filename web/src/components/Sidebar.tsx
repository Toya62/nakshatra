"use client";

import React from "react";
import {
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";
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

const TABS: { id: TabId; label: string; Icon: React.ElementType; hint?: string }[] = [
  { id: "chart",         label: "Birth Chart",        Icon: KundaliIcon },
  { id: "transits",      label: "Transits (Gochar)",  Icon: GocharIcon  },
  { id: "dasha",         label: "Vimshottari Dasha",  Icon: DashaIcon   },
  { id: "panchanga",     label: "Daily Panchanga",    Icon: PanchangaIcon },
  { id: "compatibility", label: "Kundali Matching",   Icon: MatchingIcon },
  { id: "muhurtha",      label: "Muhurtha & Horas",   Icon: MuhurthaIcon },
  { id: "remedies",      label: "Remedies & Upayas",  Icon: RemediesIcon, hint: "Parashari & Lal Kitab" },
];

const CONSULT = { id: "consult" as TabId, label: "AI Consultation", Icon: ConsultationIcon };

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
                fontSize: "10.5px",
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
          <span
            className="serif-display gold-gradient-text"
            style={{ fontSize: "0.95rem", fontWeight: 700, letterSpacing: "0.08em" }}
          >
            NAKSHATRA
          </span>
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
          {TABS.map(({ id, label, Icon }) => {
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
                  padding: slim ? "10px 0" : "10px 12px",
                  justifyContent: slim ? "center" : "flex-start",
                  width: "100%",
                  borderRadius: "var(--radius-md)",
                  border: "none",
                  borderLeft: active ? "3px solid var(--gold-vivid)" : "3px solid transparent",
                  background: active ? "linear-gradient(90deg, var(--gold-dim) 0%, transparent 100%)" : "transparent",
                  color: active ? "var(--gold-bright)" : "var(--text-mid)",
                  fontFamily: "var(--font-sans)",
                  fontSize: "var(--type-label)",
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
                <Icon
                  size={18}
                  style={{ flexShrink: 0, color: active ? "var(--gold-vivid)" : "currentColor" }}
                  aria-hidden="true"
                />
                {!slim && (
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
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

          {/* Consultation — bottom-aligned, gold-tinted */}
          {(() => {
            const { id, label, Icon } = CONSULT;
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
                  padding: slim ? "10px 0" : "10px 12px",
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
                  fontSize: "var(--type-label)",
                  fontWeight: active ? 600 : 500,
                  cursor: "pointer",
                  transition: "all 0.18s ease",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  flexShrink: 0,
                }}
              >
                <Icon size={18} style={{ flexShrink: 0 }} aria-hidden="true" />
                {!slim && <span>{label}</span>}
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
