"use client";

import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from "react";
import type { Language, TranslationSchema } from "@/lib/i18n/types.ts";
import { getTranslation } from "@/lib/i18n/index.ts";
import { formatNumber, formatDegree } from "@/lib/i18n/formatters.ts";

export interface LanguageContextType {
  lang: Language;
  setLang: (l: Language) => void;
  toggleLang: () => void;
  t: TranslationSchema;
  num: (n: number | string) => string;
  deg: (d: number, decimals?: number) => string;
}

const STORAGE_KEY = "nakshatra_language";

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<Language>("en");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "en" || saved === "ne") {
      setLangState(saved);
      document.documentElement.lang = saved;
    }
  }, []);

  const setLang = useCallback((newLang: Language) => {
    setLangState(newLang);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, newLang);
      document.documentElement.lang = newLang;
      window.dispatchEvent(new CustomEvent("languageChanged", { detail: newLang }));
    }
  }, []);

  const toggleLang = useCallback(() => {
    setLang(lang === "en" ? "ne" : "en");
  }, [lang, setLang]);

  const t = useMemo(() => getTranslation(lang), [lang]);

  const num = useCallback((n: number | string) => formatNumber(n, lang), [lang]);
  const deg = useCallback((d: number, decimals: number = 2) => formatDegree(d, lang, decimals), [lang]);

  const value = useMemo(
    () => ({
      lang,
      setLang,
      toggleLang,
      t,
      num,
      deg,
    }),
    [lang, setLang, toggleLang, t, num, deg]
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
};

export function useLanguage(): LanguageContextType {
  const context = useContext(LanguageContext);
  if (!context) {
    // Fallback if rendered outside provider (e.g. testing or static pass)
    return {
      lang: "en",
      setLang: () => {},
      toggleLang: () => {},
      t: getTranslation("en"),
      num: (n: number | string) => String(n),
      deg: (d: number, decimals: number = 2) => `${d.toFixed(decimals)}°`,
    };
  }
  return context;
}
