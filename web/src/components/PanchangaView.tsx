"use client";

import React, { useState, useEffect } from "react";
import { PanchangaData } from "@/lib/types";
import { fetchPanchanga } from "@/lib/api";
import { Skeleton } from "@/components/Skeleton";
import { Moon, Sun, AlertTriangle, Calendar, Clock } from "lucide-react";
import { DEFAULT_LOCATION } from "@/config/defaults";
import { useLanguage } from "@/context/LanguageContext";

interface Props {
  defaultLat?: number;
  defaultLon?: number;
  defaultTz?: string;
}

export const PanchangaView: React.FC<Props> = ({
  defaultLat = DEFAULT_LOCATION.lat || 27.8667,
  defaultLon = DEFAULT_LOCATION.lon || 83.4833,
  defaultTz = DEFAULT_LOCATION.tz || "Asia/Kathmandu",
}) => {
  const { t, lang, num } = useLanguage();
  const [date, setDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [time, setTime] = useState("12:00");
  const [lat] = useState(defaultLat);
  const [lon] = useState(defaultLon);
  const [tz] = useState(defaultTz);

  const [data, setData] = useState<PanchangaData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPanchanga = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchPanchanga(date, time, lat, lon, tz);
      setData(res);
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPanchanga();
  }, [date, time, lat, lon, tz]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
      {/* Top Filter Bar */}
      <div className="card" style={{ padding: "var(--space-4) var(--space-5)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "var(--space-3)" }}>
        <div>
          <h2 style={{ fontSize: "var(--type-heading)", fontWeight: 700, display: "flex", alignItems: "center", gap: "var(--space-2)", color: "var(--text-high)" }}>
            <Moon size={18} color="var(--gold-vivid)" aria-hidden="true" />
            {t.panchanga.title}
          </h2>
          <p style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", marginTop: "2px" }}>
            {t.panchanga.subtitle}
          </p>
        </div>

        <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-1)" }}>
            <Calendar size={13} color="var(--text-mid)" aria-hidden="true" />
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              style={{ width: "auto" }}
              aria-label="Panchanga calculation date"
            />
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-1)" }}>
            <Clock size={13} color="var(--text-mid)" aria-hidden="true" />
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              style={{ width: "auto" }}
              aria-label="Panchanga calculation time"
            />
          </div>
        </div>
      </div>

      {loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          <div className="card" style={{ padding: "var(--space-4) var(--space-5)" }}>
            <Skeleton width="60%" height="24px" />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: "var(--space-4)" }}>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="card" style={{ padding: "var(--space-5)", display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
                <Skeleton width="40%" height="14px" />
                <Skeleton width="70%" height="24px" />
                <Skeleton width="90%" height="14px" />
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="card" style={{ padding: "var(--space-4)", color: "var(--rose)", borderColor: "var(--rose)" }} role="alert">
          Failed to load Panchanga: {error}
        </div>
      )}

      {data && !loading && (
        <>
          {/* Solar Markers Banner */}
          <div
            className="card"
            style={{
              padding: "var(--space-4) var(--space-5)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "var(--space-3)",
              background: "linear-gradient(135deg, rgba(229,185,76,0.06) 0%, rgba(56,189,248,0.05) 100%)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-5)", flexWrap: "wrap" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                <Sun size={17} color="var(--amber)" aria-hidden="true" />
                <span style={{ fontSize: "var(--type-body)" }}>
                  {t.panchanga.sunrise}: <strong style={{ color: "var(--gold-bright)" }}>{data.sunrise_time || "N/A"}</strong>
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                <Moon size={17} color="var(--cyan-vivid)" aria-hidden="true" />
                <span style={{ fontSize: "var(--type-body)" }}>
                  {t.panchanga.sunset}: <strong style={{ color: "var(--cyan-vivid)" }}>{data.sunset_time || "N/A"}</strong>
                </span>
              </div>
            </div>

            <div style={{ display: "flex", gap: "var(--space-3)", fontSize: "var(--type-micro)", color: "var(--text-mid)", fontFamily: "var(--font-mono)" }}>
              <span>Sun: {data.sun_longitude.toFixed(2)}°</span>
              <span>Moon: {data.moon_longitude.toFixed(2)}°</span>
            </div>
          </div>

          {/* 5 Limbs Cards Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 160px), 1fr))", gap: "var(--space-4)" }}>
            {/* 1. VARA */}
            <div className="card" style={{ padding: "var(--space-5)" }}>
              <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", letterSpacing: "0.06em" }}>1. {t.panchanga.vara.toUpperCase()}</span>
              <h3 style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--gold-bright)", margin: "8px 0 4px" }}>
                {data.vara.name}
              </h3>
              <p style={{ fontSize: "var(--type-body)", color: "var(--text-mid)" }}>
                {lang === "ne" ? "स्वामी" : "Lord"}: <strong style={{ color: "var(--text-high)" }}>{data.vara.lord}</strong>
              </p>
              {data.vara.is_pre_sunrise && (
                <span className="badge badge-rose" style={{ marginTop: "var(--space-2)" }}>
                  {lang === "ne" ? "सूर्योदय अगाडि (अघिल्लो वार)" : "Pre-Sunrise (Previous Vara)"}
                </span>
              )}
            </div>

            {/* 2. TITHI */}
            <div className="card" style={{ padding: "var(--space-5)" }}>
              <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", letterSpacing: "0.06em" }}>2. {t.panchanga.tithi.toUpperCase()}</span>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--cyan-vivid)", margin: "8px 0 4px" }}>
                {data.tithi.name}
              </h3>
              <p style={{ fontSize: "var(--type-body)", color: "var(--text-mid)" }}>
                {data.tithi.paksha} {lang === "ne" ? "पक्ष" : "Paksha"} | {lang === "ne" ? "स्वामी" : "Lord"}: <strong style={{ color: "var(--text-high)" }}>{data.tithi.lord}</strong>
              </p>
              {data.tithi.percentage_left !== undefined && (
                <div style={{ marginTop: "var(--space-2)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--type-micro)", color: "var(--text-low)", marginBottom: "4px" }}>
                    <span>{lang === "ne" ? "बाँकी" : "Remaining"}</span>
                    <span>{num(data.tithi.percentage_left.toFixed(1))}%</span>
                  </div>
                  <div style={{ height: "4px", background: "var(--border-subtle)", borderRadius: "2px" }}>
                    <div style={{ width: `${data.tithi.percentage_left}%`, height: "100%", background: "var(--cyan-vivid)", borderRadius: "2px" }} />
                  </div>
                </div>
              )}
            </div>

            {/* 3. NAKSHATRA */}
            <div className="card" style={{ padding: "var(--space-5)" }}>
              <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", letterSpacing: "0.06em" }}>3. {t.panchanga.nakshatra.toUpperCase()}</span>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--gold-bright)", margin: "8px 0 4px" }}>
                {data.nakshatra.name}
              </h3>
              <p style={{ fontSize: "var(--type-body)", color: "var(--text-mid)" }}>
                {lang === "ne" ? `चरण ${num(data.nakshatra.pada ?? "")}` : `Pada ${data.nakshatra.pada ?? ""}`} | {lang === "ne" ? "स्वामी" : "Lord"}: <strong style={{ color: "var(--text-high)" }}>{data.nakshatra.lord}</strong>
              </p>
              {data.nakshatra.percentage_left !== undefined && (
                <div style={{ marginTop: "var(--space-2)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--type-micro)", color: "var(--text-low)", marginBottom: "4px" }}>
                    <span>{lang === "ne" ? "बाँकी" : "Remaining"}</span>
                    <span>{num(data.nakshatra.percentage_left.toFixed(1))}%</span>
                  </div>
                  <div style={{ height: "4px", background: "var(--border-subtle)", borderRadius: "2px" }}>
                    <div style={{ width: `${data.nakshatra.percentage_left}%`, height: "100%", background: "var(--gold-vivid)", borderRadius: "2px" }} />
                  </div>
                </div>
              )}
            </div>

            {/* 4. YOGA */}
            <div className="card" style={{ padding: "var(--space-5)" }}>
              <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", letterSpacing: "0.06em" }}>4. {t.panchanga.yoga.toUpperCase()}</span>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--graha-rahu)", margin: "8px 0 4px" }}>
                {data.yoga.name}
              </h3>
              <p style={{ fontSize: "var(--type-body)", color: "var(--text-mid)" }}>
                {lang === "ne" ? "स्वामी" : "Lord"}: <strong style={{ color: "var(--text-high)" }}>{data.yoga.lord}</strong>
              </p>
              {data.yoga.percentage_left !== undefined && (
                <div style={{ marginTop: "var(--space-2)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--type-micro)", color: "var(--text-low)", marginBottom: "4px" }}>
                    <span>{lang === "ne" ? "बाँकी" : "Remaining"}</span>
                    <span>{num(data.yoga.percentage_left.toFixed(1))}%</span>
                  </div>
                  <div style={{ height: "4px", background: "var(--border-subtle)", borderRadius: "2px" }}>
                    <div style={{ width: `${data.yoga.percentage_left}%`, height: "100%", background: "var(--graha-rahu)", borderRadius: "2px" }} />
                  </div>
                </div>
              )}
            </div>

            {/* 5. KARANA */}
            <div className="card" style={{ padding: "var(--space-5)" }}>
              <span style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", letterSpacing: "0.06em" }}>5. {t.panchanga.karana.toUpperCase()}</span>
              <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", margin: "8px 0 4px" }}>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: data.karana.is_vishti_bhadra ? "var(--rose)" : "var(--emerald)" }}>
                  {data.karana.name}
                </h3>
                {data.karana.is_vishti_bhadra && (
                  <span className="badge badge-rose" style={{ gap: "3px" }}>
                    <AlertTriangle size={11} aria-hidden="true" /> {lang === "ne" ? "भद्रा (विष्टि)" : "BHADRA"}
                  </span>
                )}
              </div>
              <p style={{ fontSize: "var(--type-body)", color: "var(--text-mid)" }}>
                {lang === "ne" ? "स्वामी" : "Lord"}: <strong style={{ color: "var(--text-high)" }}>{data.karana.lord}</strong>
              </p>
              {data.karana.percentage_left !== undefined && (
                <div style={{ marginTop: "var(--space-2)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--type-micro)", color: "var(--text-low)", marginBottom: "4px" }}>
                    <span>{lang === "ne" ? "बाँकी" : "Remaining"}</span>
                    <span>{num(data.karana.percentage_left.toFixed(1))}%</span>
                  </div>
                  <div style={{ height: "4px", background: "var(--border-subtle)", borderRadius: "2px" }}>
                    <div style={{ width: `${data.karana.percentage_left}%`, height: "100%", background: "var(--emerald)", borderRadius: "2px" }} />
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
