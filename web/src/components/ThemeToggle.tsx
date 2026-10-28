"use client";

import React, { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

export const ThemeToggle: React.FC = () => {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const current = document.documentElement.getAttribute("data-theme") as "dark" | "light" | null;
    if (current === "light" || current === "dark") {
      setTheme(current);
    } else {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      setTheme(prefersDark ? "dark" : "light");
    }

    const observer = new MutationObserver(() => {
      const attr = document.documentElement.getAttribute("data-theme") as "dark" | "light" | null;
      if (attr === "light" || attr === "dark") {
        setTheme(attr);
      }
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });

    return () => observer.disconnect();
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);

    document.documentElement.classList.add("theme-transitioning");
    document.documentElement.setAttribute("data-theme", nextTheme);
    try {
      localStorage.setItem("nakshatra_theme", nextTheme);
    } catch {}

    window.setTimeout(() => {
      document.documentElement.classList.remove("theme-transitioning");
    }, 320);
  };

  if (!mounted) {
    return (
      <button
        type="button"
        className="btn-icon theme-toggle-btn"
        aria-label="Theme toggle"
        disabled
        style={{ opacity: 0.6 }}
      >
        <Moon size={16} aria-hidden="true" />
      </button>
    );
  }

  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="btn-icon theme-toggle-btn"
      aria-label={isDark ? "Switch to light mode (Sacred Dawn)" : "Switch to dark mode (Celestial Obsidian)"}
      title={isDark ? "Switch to light mode (Sacred Dawn)" : "Switch to dark mode (Celestial Obsidian)"}
      style={{
        position: "relative",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: "36px",
        height: "36px",
        borderRadius: "var(--radius-md)",
        background: "var(--bg-subtle)",
        border: "1px solid var(--border-subtle)",
        color: "var(--gold-vivid)",
        cursor: "pointer",
        transition: "all 0.22s cubic-bezier(0.16, 1, 0.3, 1)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transform: isDark ? "rotate(0deg) scale(1)" : "rotate(180deg) scale(0)",
          transition: "transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease",
          opacity: isDark ? 1 : 0,
          position: "absolute",
        }}
      >
        <Moon size={17} aria-hidden="true" />
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transform: !isDark ? "rotate(0deg) scale(1)" : "rotate(-180deg) scale(0)",
          transition: "transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease",
          opacity: !isDark ? 1 : 0,
          position: "absolute",
        }}
      >
        <Sun size={17} aria-hidden="true" />
      </div>
    </button>
  );
};

