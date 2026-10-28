"use client";

import React, { useState, useEffect } from "react";
import { Calendar } from "lucide-react";
import { CalendarSystem, getCalendarSystem, setCalendarSystem } from "@/lib/calendar";

export const CalendarSwitcher: React.FC = () => {
  const [system, setSystem] = useState<CalendarSystem>("gregorian");

  useEffect(() => {
    setSystem(getCalendarSystem());
    const handleCalChange = (e: Event) => {
      const customEvent = e as CustomEvent<CalendarSystem>;
      if (customEvent.detail) {
        setSystem(customEvent.detail);
      }
    };
    window.addEventListener("calendarSystemChanged", handleCalChange);
    return () => window.removeEventListener("calendarSystemChanged", handleCalChange);
  }, []);

  const toggle = () => {
    const newSystem = system === "gregorian" ? "bikram" : "gregorian";
    setSystem(newSystem);
    setCalendarSystem(newSystem);
    // Trigger a page reload or custom event to notify components
    window.dispatchEvent(new CustomEvent("calendarSystemChanged", { detail: newSystem }));
  };

  return (
    <button
      onClick={toggle}
      className="flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1.5 rounded-lg bg-[var(--surface-raised)] border border-[var(--border-subtle)] hover:border-[var(--gold-vivid)] transition-colors text-xs sm:text-sm min-h-[36px]"
      title="Switch calendar system"
      aria-label={`Switch calendar system, currently ${system === "gregorian" ? "Gregorian AD" : "Bikram Sambat BS"}`}
    >
      <Calendar size={15} />
      <span className="font-medium whitespace-nowrap">
        <span className="hidden sm:inline">
          {system === "gregorian" ? "AD (Gregorian)" : "BS (Bikram Sambat)"}
        </span>
        <span className="inline sm:hidden">
          {system === "gregorian" ? "AD" : "BS"}
        </span>
      </span>
    </button>
  );
};
