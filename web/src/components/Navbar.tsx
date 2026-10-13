"use client";

import React from "react";
import { Sparkles, Moon, Compass, Clock, BookOpen, Activity } from "lucide-react";

export type TabId = "chart" | "transits" | "dasha" | "panchanga" | "consult";

interface Props {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  apiStatus: "connected" | "offline" | "checking";
}

export const Navbar: React.FC<Props> = ({ activeTab, onTabChange, apiStatus }) => {
  const tabs = [
    { id: "chart" as TabId, label: "Birth Chart", icon: Sparkles },
    { id: "transits" as TabId, label: "Transits (Gochar)", icon: Compass },
    { id: "dasha" as TabId, label: "Vimshottari Dasha", icon: Clock },
    { id: "panchanga" as TabId, label: "Daily Panchanga", icon: Moon },
    { id: "consult" as TabId, label: "AI Consultation", icon: BookOpen },
  ];

  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "16px 28px",
        background: "rgba(10, 13, 24, 0.8)",
        backdropFilter: "blur(18px)",
        borderBottom: "1px solid rgba(229, 185, 76, 0.18)",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div
          style={{
            width: "36px",
            height: "36px",
            borderRadius: "10px",
            background: "linear-gradient(135deg, #e5b94c 0%, #a855f7 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 15px rgba(229, 185, 76, 0.4)",
          }}
        >
          <Sparkles size={20} color="#07090e" />
        </div>
        <div>
          <h1 className="title-serif gold-gradient-text" style={{ fontSize: "1.3rem", fontWeight: "800", lineHeight: 1.1 }}>
            NAKSHATRA
          </h1>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", letterSpacing: "0.08em" }}>
            VEDIC ASTROLOGY AI ENGINE
          </p>
        </div>
      </div>

      <nav style={{ display: "flex", gap: "6px" }}>
        {tabs.map((t) => {
          const Icon = t.icon;
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => onTabChange(t.id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 16px",
                borderRadius: "10px",
                border: isActive ? "1px solid rgba(229, 185, 76, 0.5)" : "1px solid transparent",
                background: isActive ? "rgba(229, 185, 76, 0.12)" : "transparent",
                color: isActive ? "#fbe285" : "var(--text-muted)",
                cursor: "pointer",
                fontWeight: isActive ? 600 : 500,
                fontSize: "0.88rem",
                transition: "all 0.2s ease",
              }}
            >
              <Icon size={16} color={isActive ? "#e5b94c" : "currentColor"} />
              {t.label}
            </button>
          );
        })}
      </nav>

      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div
          className={`badge ${apiStatus === "connected" ? "badge-emerald" : apiStatus === "checking" ? "badge-cyan" : "badge-rose"}`}
          style={{ gap: "6px" }}
        >
          <Activity size={12} />
          <span>API: {apiStatus}</span>
        </div>
      </div>
    </header>
  );
};
