"use client";

import React, { useEffect, useState } from "react";
import { Sun, ShieldAlert, Clock, Award, Activity } from "lucide-react";
import {
  BirthDataInput,
  KalsarpInput,
  KalsarpPlanetStatus,
  KalsarpReport,
} from "@/lib/types";
import { fetchKalsarp } from "@/lib/api";

interface Props {
  birth?: BirthDataInput;
}

const CLASSIFICATION_STYLE: Record<string, { color: string; bg: string; border: string }> = {
  Purna: {
    color: "var(--rose)",
    bg: "rgba(239, 68, 68, 0.10)",
    border: "rgba(239, 68, 68, 0.25)",
  },
  Ardh: {
    color: "var(--amber)",
    bg: "rgba(245, 158, 11, 0.10)",
    border: "rgba(245, 158, 11, 0.25)",
  },
  None: {
    color: "var(--emerald)",
    bg: "rgba(16, 185, 129, 0.10)",
    border: "rgba(16, 185, 129, 0.25)",
  },
};

export const KalsarpView: React.FC<Props> = ({ birth }: Props) => {
  const [report, setReport] = useState<KalsarpReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!birth) {
      setReport(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);

    const payload: KalsarpInput = {
      year: birth.year,
      month: birth.month,
      day: birth.day,
      hour: birth.hour,
      minute: birth.minute,
      second: birth.second ?? 0,
      latitude: birth.latitude,
      longitude: birth.longitude,
      timezone: birth.timezone,
      place_name: birth.place_name,
      ayanamsa: birth.ayanamsa || "jhora_lahiri",
      house_system: birth.house_system || "WholeSign",
    };

    fetchKalsarp(payload)
      .then((data) => {
        if (!cancelled) setReport(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError((err as Error).message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [birth]);

  if (!birth) {
    return (
      <div style={{ maxWidth: "var(--size-container)", margin: "0 auto", width: "100%" }}>
        <div className="card" style={{ padding: "var(--space-8)", textAlign: "center" }}>
          <Sun size={32} color="var(--gold-vivid)" style={{ margin: "0 auto var(--space-3)" }} />
          <h3 style={{ fontSize: "var(--type-heading)", color: "var(--gold-vivid)", marginBottom: "var(--space-1)" }}>
            Kalsarp Dosha Analyzer
          </h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>
            Enter your birth parameters to detect whether classical planets are hemmed between Rahu and Ketu,
            and identify the Kalsarp type (Anant, Kulik, Vasuki, Shankhpal, Padma, Mahapadma, Takshak,
            Karkotak, Shankhachur, Ghatak, Vishdhar, Sheshnag).
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ maxWidth: "var(--size-container)", margin: "0 auto", width: "100%", padding: "var(--space-6)" }}>
        <div className="card" style={{ padding: "var(--space-8)", textAlign: "center" }}>
          <Clock size={32} color="var(--gold-vivid)" className="spin" style={{ margin: "0 auto var(--space-3)" }} />
          <h3 style={{ fontSize: "var(--type-heading)", color: "var(--gold-vivid)", marginBottom: "var(--space-1)" }}>
            Analyzing Rahu–Ketu Axis…
          </h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>
            Checking whether all seven classical Grahas fall within the Kalsarp arc.
          </p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div style={{ maxWidth: "var(--size-container)", margin: "0 auto", width: "100%", padding: "var(--space-6)" }}>
        <div className="card" style={{ padding: "var(--space-6)", borderColor: "var(--rose)" }}>
          <ShieldAlert size={24} color="var(--rose)" style={{ marginBottom: "var(--space-2)" }} />
          <h3 style={{ color: "var(--rose)", fontSize: "var(--type-body)", fontWeight: 700 }}>Kalsarp Calculation Error</h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>{error || "Unable to analyze Kalsarp Dosha."}</p>
        </div>
      </div>
    );
  }

  const style = CLASSIFICATION_STYLE[report.classification] ?? CLASSIFICATION_STYLE.None;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)", maxWidth: "var(--size-container-lg)", margin: "0 auto", width: "100%" }}>
      {/* ── Header Banner ── */}
      <div className="card" style={{ padding: "var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-3)" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <Activity size={24} color="var(--gold-vivid)" />
              <h2 style={{ fontSize: "var(--type-title)", fontWeight: 700, color: "var(--text-high)" }}>
                Kalsarp Dosha Analysis
              </h2>
            </div>
            <p style={{ fontSize: "var(--type-small)", color: "var(--text-mid)", marginTop: "var(--space-1)" }}>
              Rahu–Ketu nodal axis diagnostic across the twelve classical types.
            </p>
            <div style={{ marginTop: "var(--space-3)", fontSize: "var(--type-micro)", color: "var(--text-low)", fontFamily: "var(--font-mono)" }}>
              Rahu: {report.rahu_sign} (House {report.rahu_house}) &nbsp;•&nbsp; Ketu: {report.ketu_sign} (House {report.ketu_house}) &nbsp;•&nbsp; Axis arc: {report.axis_arc_degrees?.toFixed(2) ?? "—"}°
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
            <span
              style={{
                fontSize: "var(--type-micro)",
                fontWeight: 700,
                padding: "var(--space-0-5) var(--space-2)",
                borderRadius: "var(--radius-sm)",
                background: style.bg,
                border: `1px solid ${style.border}`,
                color: style.color,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              {report.has_kalsarp ? report.classification + " Kalsarp" : "No Kalsarp"}
            </span>
            {report.has_kalsarp && report.kalsarp_type && (
              <span
                style={{
                  fontSize: "var(--type-micro)",
                  fontWeight: 700,
                  padding: "var(--space-0-5) var(--space-2)",
                  borderRadius: "var(--radius-sm)",
                  background: "var(--gold-dim)",
                  border: "1px solid var(--gold-border)",
                  color: "var(--gold-vivid)",
                }}
              >
                {report.kalsarp_type}
              </span>
            )}
          </div>
        </div>

        <div style={{ marginTop: "var(--space-4)", padding: "var(--space-3) var(--space-4)", background: "var(--bg-subtle)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)", fontSize: "var(--type-small)", color: "var(--text-high)", lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
          {report.summary}
        </div>
      </div>

      {/* ── Type Description ── */}
      {report.has_kalsarp && report.kalsarp_type_description && (
        <div className="card" style={{ padding: "var(--space-4) var(--space-5)", borderLeft: `4px solid ${style.color}` }}>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
            <Award size={16} color={style.color} />
            <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: style.color, textTransform: "uppercase" }}>
              {report.kalsarp_type} — Classical Type
            </h4>
          </div>
          <div style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>{report.kalsarp_type_description}</div>
        </div>
      )}

      {/* ── Classification Stats ── */}
      <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
        <div style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)", padding: "var(--space-3) var(--space-4)", flex: 1, minWidth: 140 }}>
          <div style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textTransform: "uppercase" }}>Planets Within Axis</div>
          <div style={{ fontSize: "var(--type-heading)", fontWeight: 700, color: "var(--gold-vivid)" }}>
            {report.planets_within_axis} / {report.total_classical_planets}
          </div>
        </div>
        <div style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)", padding: "var(--space-3) var(--space-4)", flex: 1, minWidth: 140 }}>
          <div style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textTransform: "uppercase" }}>Classification</div>
          <div style={{ fontSize: "var(--type-heading)", fontWeight: 700, color: style.color }}>{report.classification}</div>
        </div>
      </div>

      {/* ── Planet Status Table ── */}
      <div className="card" style={{ padding: "var(--space-4) var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase" }}>Classical Graha Axis Status</h4>
          <span style={{ fontSize: "var(--type-label)", color: "var(--text-low)" }}>{report.planet_status.length} planets</span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--type-micro)" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border-subtle)" }}>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Graha</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Sign</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Degree</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>House</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Within Axis</th>
              </tr>
            </thead>
            <tbody>
              {report.planet_status.map((p: KalsarpPlanetStatus, idx: number) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: "1px solid var(--border-subtle)",
                    background: p.within_axis ? "rgba(239, 68, 68, 0.04)" : "transparent",
                  }}
                >
                  <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-high)", fontWeight: 600 }}>{p.name}</td>
                  <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)" }}>{p.sign}</td>
                  <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)", fontFamily: "var(--font-mono)" }}>{p.degree_in_sign.toFixed(2)}°</td>
                  <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)" }}>{p.house}</td>
                  <td style={{ padding: "var(--space-1) var(--space-2)" }}>
                    <span
                      style={{
                        fontSize: "var(--type-label)",
                        fontWeight: 600,
                        padding: "1px 6px",
                        borderRadius: "var(--radius-sm)",
                        background: p.within_axis ? "var(--rose-dim)" : "var(--emerald-dim)",
                        color: p.within_axis ? "var(--rose)" : "var(--emerald)",
                        border: `1px solid ${p.within_axis ? "var(--rose)" : "var(--emerald)"}`,
                      }}
                    >
                      {p.within_axis ? "Within" : "Outside"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
