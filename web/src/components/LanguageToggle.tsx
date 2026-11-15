"use client";

import React from "react";
import { Globe } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

export const LanguageToggle: React.FC = () => {
  const { lang, toggleLang } = useLanguage();

  return (
    <button
      type="button"
      onClick={toggleLang}
      className="btn-icon"
      aria-label={`Switch language, currently ${lang === "en" ? "English" : "Nepali"}`}
      title={lang === "en" ? "नेपाली भाषामा बदल्नुहोस् (Switch to Nepali)" : "Switch to English"}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding: "0 10px",
        height: "36px",
        borderRadius: "var(--radius-md)",
        background: "var(--bg-subtle)",
        border: "1px solid var(--border-subtle)",
        color: "var(--text-high)",
        cursor: "pointer",
        fontSize: "var(--type-label)",
        fontWeight: 600,
        transition: "all 0.18s ease",
        userSelect: "none",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "var(--gold-border)";
        e.currentTarget.style.color = "var(--gold-vivid)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--border-subtle)";
        e.currentTarget.style.color = "var(--text-high)";
      }}
    >
      <Globe size={15} color="var(--gold-vivid)" aria-hidden="true" />
      <span style={{ display: "inline-flex", alignItems: "center", gap: "3px" }}>
        <span
          style={{
            color: lang === "en" ? "var(--gold-vivid)" : "var(--text-low)",
            fontWeight: lang === "en" ? 700 : 500,
          }}
        >
          EN
        </span>
        <span style={{ color: "var(--border-subtle)", fontSize: "11px" }}>|</span>
        <span
          style={{
            color: lang === "ne" ? "var(--gold-vivid)" : "var(--text-low)",
            fontWeight: lang === "ne" ? 700 : 500,
            fontFamily: "var(--font-sans)",
          }}
        >
          ने
        </span>
      </span>
    </button>
  );
};
