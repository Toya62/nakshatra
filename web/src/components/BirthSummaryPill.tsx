"use client";

import React, { useState, useEffect } from "react";
import { BirthDataInput, BikramSambatDate } from "@/lib/types";
import { MapPin, Calendar, Clock, ChevronDown, ChevronUp, Edit2 } from "lucide-react";
import { BirthForm } from "@/components/BirthForm";
import { CalendarSystem, getCalendarSystem, convertAdToBs } from "@/lib/calendar";

interface Props {
  birthData: BirthDataInput;
  hasChart: boolean;
  onSubmit: (data: BirthDataInput) => void;
  loading: boolean;
}

function padZ(n: number) {
  return String(n).padStart(2, "0");
}

function formatAyanamsa(a: string | undefined) {
  if (!a) return "";
  return (a ?? "")
    .replace("jhora_", "JHora ")
    .replace("lahiri", "Lahiri")
    .replace("krishnamurti", "KP")
    .replace("raman", "Raman")
    .replace("tropical", "Tropical")
    .replace(/_/g, " ");
}

export const BirthSummaryPill: React.FC<Props> = ({
  birthData,
  hasChart,
  onSubmit,
  loading,
}) => {
  const [expanded, setExpanded] = useState(!hasChart);
  const [calendarSystem, setCalendarSystem] = useState<CalendarSystem>("gregorian");
  const [bsData, setBsData] = useState<BikramSambatDate | null>(null);

  useEffect(() => {
    setCalendarSystem(getCalendarSystem());
    const handleCalChange = (e: Event) => {
      const customEvent = e as CustomEvent<CalendarSystem>;
      if (customEvent.detail) setCalendarSystem(customEvent.detail);
    };
    window.addEventListener("calendarSystemChanged", handleCalChange);
    return () => window.removeEventListener("calendarSystemChanged", handleCalChange);
  }, []);

  useEffect(() => {
    if (birthData.year && birthData.month && birthData.day) {
      convertAdToBs(birthData.year, birthData.month, birthData.day).then(setBsData);
    }
  }, [birthData.year, birthData.month, birthData.day]);

  // Collapsed pill — shown when a chart has been calculated
  if (hasChart && !expanded) {
    return (
      <div
        className="card"
        style={{
          padding: "var(--space-3) var(--space-5)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "var(--space-4)",
          flexWrap: "wrap",
          cursor: "default",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-4)",
            flexWrap: "wrap",
            fontSize: "var(--type-label)",
            color: "var(--text-mid)",
          }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: "var(--space-1)" }}>
            <Calendar size={12} aria-hidden="true" />
            <span style={{ color: "var(--text-high)", fontWeight: 600 }}>
              {calendarSystem === "bikram" && bsData
                ? `${bsData.formatted_ne || bsData.formatted} BS`
                : `${birthData.day} ${["", "Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][birthData.month]} ${birthData.year}`}
            </span>
            {calendarSystem !== "bikram" && bsData?.formatted_ne && (
              <span style={{ color: "var(--gold-bright)", fontSize: "var(--type-micro)", marginLeft: "4px" }}>
                ({bsData.formatted_ne} BS)
              </span>
            )}
            {calendarSystem === "bikram" && (
              <span style={{ color: "var(--text-low)", fontSize: "var(--type-micro)", marginLeft: "4px" }}>
                ({birthData.year}-{padZ(birthData.month)}-{padZ(birthData.day)} AD)
              </span>
            )}
          </span>

          <span style={{ color: "var(--text-low)" }}>·</span>

          <span style={{ display: "flex", alignItems: "center", gap: "var(--space-1)" }}>
            <Clock size={12} aria-hidden="true" />
            {padZ(birthData.hour)}:{padZ(birthData.minute)}
            {(birthData.second ?? 0) > 0 ? `:${padZ(birthData.second!)}` : ""}
          </span>

          <span style={{ color: "var(--text-low)" }}>·</span>

          <span style={{ display: "flex", alignItems: "center", gap: "var(--space-1)" }}>
            <MapPin size={12} aria-hidden="true" />
            {birthData.place_name || `${birthData.latitude.toFixed(2)}°, ${birthData.longitude.toFixed(2)}°`}
          </span>

          <span style={{ color: "var(--text-low)" }}>·</span>

          <span
            className="badge badge-gold"
            style={{ fontSize: "var(--type-micro)" }}
          >
            {formatAyanamsa(birthData.ayanamsa)}
          </span>

          <span
            className="badge badge-cyan"
            style={{ fontSize: "var(--type-micro)" }}
          >
            {birthData.house_system}
          </span>
        </div>

        <button
          onClick={() => setExpanded(true)}
          className="btn-ghost"
          aria-label="Edit birth details"
          aria-expanded={false}
          style={{ gap: "var(--space-1)", padding: "5px 10px", fontSize: "var(--type-label)" }}
        >
          <Edit2 size={13} aria-hidden="true" />
          Edit
          <ChevronDown size={13} aria-hidden="true" />
        </button>
      </div>
    );
  }

  // Expanded — show the full form
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {hasChart && (
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            marginBottom: "var(--space-2)",
          }}
        >
          <button
            onClick={() => setExpanded(false)}
            className="btn-ghost"
            aria-label="Collapse birth form"
            aria-expanded={true}
            style={{ fontSize: "var(--type-label)", gap: "var(--space-1)" }}
          >
            <ChevronUp size={13} aria-hidden="true" />
            Collapse
          </button>
        </div>
      )}
      <BirthForm
        initialData={birthData}
        onSubmit={(data) => {
          onSubmit(data);
          setExpanded(false);
        }}
        loading={loading}
      />
    </div>
  );
};
