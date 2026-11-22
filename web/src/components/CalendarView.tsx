"use client";

import React, { useCallback, useEffect, useState } from "react";
import { BikramSambatDate, PanchangaData } from "@/lib/types";
import { fetchBsMonth, fetchPanchanga } from "@/lib/api";
import { Skeleton } from "@/components/Skeleton";
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight } from "lucide-react";
import { DEFAULT_LOCATION } from "@/config/defaults";
import { useLanguage } from "@/context/LanguageContext";

interface Props {
  defaultLat?: number;
  defaultLon?: number;
  defaultTz?: string;
}

/** Month grid in AD with the Bikram Sambat date on every day.
 *  One /calendar/bs/month call per month; tapping a day loads that day's
 *  panchanga through the existing single-day endpoint. */
export const CalendarView: React.FC<Props> = ({
  defaultLat = DEFAULT_LOCATION.lat || 27.8667,
  defaultLon = DEFAULT_LOCATION.lon || 83.4833,
  defaultTz = DEFAULT_LOCATION.tz || "Asia/Kathmandu",
}) => {
  const { t, lang, num } = useLanguage();
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth()); // 0-based
  const [bsDays, setBsDays] = useState<BikramSambatDate[] | null>(null);
  const [loadingMonth, setLoadingMonth] = useState(false);
  const [selectedDay, setSelectedDay] = useState(today.getDate());
  const [dayData, setDayData] = useState<PanchangaData | null>(null);
  const [loadingDay, setLoadingDay] = useState(false);

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstWeekday = new Date(year, month, 1).getDay(); // 0 = Sunday
  const isCurrentMonth = year === today.getFullYear() && month === today.getMonth();
  const locale = lang === "ne" ? "ne-NP" : "en-GB";
  const monthName = new Intl.DateTimeFormat(locale, { month: "long" }).format(new Date(year, month, 1));
  const weekdays = Array.from({ length: 7 }, (_, i) =>
    new Intl.DateTimeFormat(locale, { weekday: "short" }).format(new Date(2026, 9, 4 + i))
  );

  // BS months spanned by this AD month, e.g. "Kartik – Mangsir 2083".
  const bsSpan = (() => {
    if (!bsDays || bsDays.length === 0) return "";
    const first = bsDays[0];
    const last = bsDays[bsDays.length - 1];
    const firstName = lang === "ne" ? first.month_name_ne : first.month_name_en;
    const lastName = lang === "ne" ? last.month_name_ne : last.month_name_en;
    const yearSpan =
      first.year === last.year
        ? (lang === "ne" ? num(first.year) : String(first.year))
        : (lang === "ne" ? `${num(first.year)}–${num(last.year)}` : `${first.year}–${last.year}`);
    if (first.month === last.month) {
      return `${firstName} ${yearSpan}`;
    }
    return `${firstName} – ${lastName} ${yearSpan}`;
  })();

  const loadDay = useCallback(
    async (day: number) => {
      setSelectedDay(day);
      setLoadingDay(true);
      try {
        const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
        const res = await fetchPanchanga(dateStr, "12:00", defaultLat, defaultLon, defaultTz);
        setDayData(res);
      } catch {
        setDayData(null);
      } finally {
        setLoadingDay(false);
      }
    },
    [year, month, defaultLat, defaultLon, defaultTz]
  );

  useEffect(() => {
    let cancelled = false;
    setLoadingMonth(true);
    fetchBsMonth(year, month + 1)
      .then((days) => {
        if (!cancelled) setBsDays(days);
      })
      .catch(() => {
        if (!cancelled) setBsDays(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingMonth(false);
      });
    return () => {
      cancelled = true;
    };
  }, [year, month]);

  useEffect(() => {
    loadDay(isCurrentMonth ? today.getDate() : 1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year, month]);

  const shiftMonth = (delta: number) => {
    const d = new Date(year, month + delta, 1);
    setYear(d.getFullYear());
    setMonth(d.getMonth());
  };

  const goToday = () => {
    setYear(today.getFullYear());
    setMonth(today.getMonth());
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)", maxWidth: "960px", margin: "0 auto", width: "100%", minWidth: 0 }}>
      {/* Header */}
      <div className="card" style={{ padding: "var(--space-4) var(--space-5)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "var(--space-3)" }}>
        <div>
          <h2 style={{ fontSize: "var(--type-heading)", fontWeight: 700, display: "flex", alignItems: "center", gap: "var(--space-2)", color: "var(--text-high)" }}>
            <CalendarIcon size={18} color="var(--gold-vivid)" aria-hidden="true" />
            {t.calendar.title}
          </h2>
          <p style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", marginTop: "2px" }}>
            {t.calendar.subtitle}
          </p>
        </div>
        <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center" }}>
          <button type="button" onClick={() => shiftMonth(-1)} className="btn-icon" aria-label={lang === "ne" ? "अघिल्लो महिना" : "Previous month"}>
            <ChevronLeft size={16} aria-hidden="true" />
          </button>
          <button type="button" onClick={goToday} className="chip" style={{ fontSize: "var(--type-micro)" }}>
            {t.calendar.today}
          </button>
          <button type="button" onClick={() => shiftMonth(1)} className="btn-icon" aria-label={lang === "ne" ? "अर्को महिना" : "Next month"}>
            <ChevronRight size={16} aria-hidden="true" />
          </button>
        </div>
      </div>

      {/* Month title */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "var(--space-2)", padding: "0 var(--space-1)" }}>
        <h3 style={{ fontSize: "var(--type-title)", fontWeight: 700, color: "var(--gold-bright)" }}>
          {monthName} {num(year)}
        </h3>
        <span style={{ fontSize: "var(--type-body)", color: "var(--text-mid)" }}>{bsSpan}</span>
      </div>

      {/* Grid */}
      <div className="card" style={{ padding: "var(--space-4)" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "var(--space-1-5)" }}>
          {weekdays.map((w) => (
            <div key={w} style={{ textAlign: "center", fontSize: "var(--type-label)", fontWeight: 700, color: "var(--text-low)", textTransform: "uppercase", paddingBottom: "var(--space-1)" }}>
              {w}
            </div>
          ))}
          {Array.from({ length: firstWeekday }, (_, i) => (
            <div key={`blank-${i}`} aria-hidden="true" />
          ))}
          {Array.from({ length: daysInMonth }, (_, i) => {
            const day = i + 1;
            const bs = bsDays?.[i] ?? null;
            const isToday = isCurrentMonth && day === today.getDate();
            const isSelected = day === selectedDay;
            return (
              <button
                key={day}
                type="button"
                onClick={() => loadDay(day)}
                aria-pressed={isSelected}
                aria-label={`${monthName} ${day}, ${bs ? bs.formatted : ""}`}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "1px",
                  padding: "var(--space-2) var(--space-1)",
                  borderRadius: "var(--radius-sm)",
                  border: isSelected
                    ? "1px solid var(--gold-vivid)"
                    : isToday
                    ? "1px solid var(--gold-border)"
                    : "1px solid transparent",
                  background: isSelected ? "var(--gold-dim)" : isToday ? "var(--bg-subtle)" : "transparent",
                  color: "var(--text-high)",
                  cursor: "pointer",
                  minWidth: 0,
                }}
              >
                <span style={{ fontSize: "var(--type-body)", fontWeight: isToday || isSelected ? 700 : 500 }}>
                  {num(day)}
                </span>
                <span style={{ fontSize: "var(--type-label)", color: "var(--gold-vivid)" }}>
                  {loadingMonth ? "…" : bs ? num(bs.day) : ""}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected day panchanga */}
      {loadingDay ? (
        <div className="card" style={{ padding: "var(--space-5)" }}>
          <Skeleton width="40%" height="20px" />
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)", marginTop: "var(--space-3)" }}>
            <Skeleton width="80%" height="14px" />
            <Skeleton width="60%" height="14px" />
          </div>
        </div>
      ) : dayData ? (
        <div className="card" style={{ padding: "var(--space-4) var(--space-5)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "var(--space-2)", marginBottom: "var(--space-3)" }}>
            <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase" }}>
              {t.calendar.dayPanchanga}
            </h4>
            <span style={{ fontSize: "var(--type-label)", color: "var(--text-low)", fontFamily: "var(--font-mono)" }}>
              {dayData.date}
              {bsDays?.[selectedDay - 1] ? ` • ${lang === "ne" ? bsDays[selectedDay - 1].formatted_ne : bsDays[selectedDay - 1].formatted}` : ""}
            </span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "var(--space-3)" }}>
            <div>
              <div style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textTransform: "uppercase" }}>{t.panchanga.tithi}</div>
              <div style={{ fontSize: "var(--type-body)", fontWeight: 600, color: "var(--text-high)" }}>{dayData.tithi.name}</div>
            </div>
            <div>
              <div style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textTransform: "uppercase" }}>{t.panchanga.nakshatra}</div>
              <div style={{ fontSize: "var(--type-body)", fontWeight: 600, color: "var(--text-high)" }}>{dayData.nakshatra.name}</div>
            </div>
            <div>
              <div style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textTransform: "uppercase" }}>{t.panchanga.yoga}</div>
              <div style={{ fontSize: "var(--type-body)", fontWeight: 600, color: "var(--text-high)" }}>{dayData.yoga.name}</div>
            </div>
            <div>
              <div style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textTransform: "uppercase" }}>{t.panchanga.karana}</div>
              <div style={{ fontSize: "var(--type-body)", fontWeight: 600, color: "var(--text-high)" }}>{dayData.karana.name}</div>
            </div>
            <div>
              <div style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textTransform: "uppercase" }}>{t.panchanga.sunrise}</div>
              <div style={{ fontSize: "var(--type-body)", fontWeight: 600, color: "var(--text-high)" }}>{dayData.sunrise_time || "—"}</div>
            </div>
            <div>
              <div style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textTransform: "uppercase" }}>{t.panchanga.sunset}</div>
              <div style={{ fontSize: "var(--type-body)", fontWeight: 600, color: "var(--text-high)" }}>{dayData.sunset_time || "—"}</div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
