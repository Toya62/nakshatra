"use client";

import React, { useEffect, useState } from "react";
import { Sun, ShieldAlert, Clock, Award, Activity } from "lucide-react";
import { BirthDataInput, SpecialLagna, SpecialLagnasInput, SpecialLagnasReport } from "@/lib/types";
import { fetchSpecialLagnas } from "@/lib/api";

interface Props {
  birth?: BirthDataInput;
}

export const SpecialLagnasView: React.FC<Props> = ({ birth }: Props) => {
  const [report, setReport] = useState<SpecialLagnasReport | null>(null);
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

    const payload: SpecialLagnasInput = {
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

    fetchSpecialLagnas(payload)
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
            Special Lagnas (Vishesha Lagna)
          </h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>
            Enter your birth parameters to compute Arudha, Upapada, Indu, Bhrigu, Ghati, Sri and
            Karakamsha lagnas — classical Jaimini/Tajika ascendants for perception, marriage,
            prosperity, karmic triggers, authority, fortune and soul-direction.
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
            Computing Special Lagnas…
          </h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>
            Deriving each vishesha lagna from its classical pada/midpoint rule.
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
          <h3 style={{ color: "var(--rose)", fontSize: "var(--type-body)", fontWeight: 700 }}>Special Lagnas Error</h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>{error || "Unable to compute special lagnas."}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)", maxWidth: "var(--size-container-lg)", margin: "0 auto", width: "100%" }}>
      {/* ── Header Banner ── */}
      <div className="card" style={{ padding: "var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-3)" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <Activity size={24} color="var(--gold-vivid)" />
              <h2 style={{ fontSize: "var(--type-title)", fontWeight: 700, color: "var(--text-high)" }}>
                Special Lagnas — Vishesha Lagna
              </h2>
            </div>
            <p style={{ fontSize: "var(--type-small)", color: "var(--text-mid)", marginTop: "var(--space-1)" }}>
              {report.lagnas.length} classical special ascendants, each with sign, house, lord and degree.
            </p>
          </div>
          <span
            style={{
              fontSize: "var(--type-micro)",
              fontWeight: 700,
              padding: "var(--space-0-5) var(--space-2)",
              borderRadius: "var(--radius-sm)",
              background: "var(--gold-dim)",
              border: "1px solid var(--gold-border)",
              color: "var(--gold-vivid)",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
          >
            {report.lagnas.length} lagnas
          </span>
        </div>
      </div>

      {/* ── Lagna Cards ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "var(--space-4)" }}>
        {report.lagnas.map((l: SpecialLagna, idx: number) => (
          <div
            key={idx}
            className="card"
            style={{ padding: "var(--space-4) var(--space-5)", borderLeft: `4px solid var(--gold-border)`, display: "flex", flexDirection: "column", gap: "var(--space-2)" }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", margin: 0 }}>
                {l.name}
              </h4>
              <span style={{ fontSize: "var(--type-label)", fontWeight: 600, color: "var(--cyan-vivid)", textTransform: "uppercase" }}>
                House {l.house}
              </span>
            </div>
            <div style={{ fontSize: "var(--type-small)", color: "var(--text-high)", fontWeight: 700 }}>
              {l.sign}
            </div>
            <div style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", display: "flex", justifyContent: "space-between", gap: "var(--space-2)" }}>
              <span>
                <span style={{ color: "var(--text-low)" }}>Lord:</span> <span style={{ color: "var(--text-high)", fontWeight: 600 }}>{l.lord}</span>
              </span>
              <span>
                <span style={{ color: "var(--text-low)" }}>Degree:</span> <span style={{ color: "var(--text-high)", fontFamily: "var(--font-mono)" }}>{l.degree_in_sign.toFixed(2)}°</span>
              </span>
            </div>
            <div style={{ fontSize: "var(--type-label)", color: "var(--text-low)", fontStyle: "italic", marginTop: "var(--space-1)" }}>{l.rationale}</div>
          </div>
        ))}
      </div>

      {/* ── Notes ── */}
      {report.notes.length > 0 && (
        <div className="card" style={{ padding: "var(--space-4) var(--space-5)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
            <Clock size={16} color="var(--gold-vivid)" />
            <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", margin: 0 }}>Calculation Notes</h4>
          </div>
          <ul style={{ color: "var(--text-mid)", fontSize: "var(--type-small)", lineHeight: 1.7, paddingLeft: "var(--space-4)", margin: 0 }}>
            {report.notes.map((n, idx) => (
              <li key={idx}>{n}</li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Master Summary ── */}
      <div className="card" style={{ padding: "var(--space-4) var(--space-5)", background: "linear-gradient(135deg, var(--gold-dim) 0%, var(--bg-card) 100%)", border: "1px solid var(--gold-border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)" }}>
          <Award size={16} color="var(--gold-vivid)" />
          <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", margin: 0 }}>Master's Reading</h4>
        </div>
        <div style={{ color: "var(--text-high)", lineHeight: 1.7, fontSize: "var(--type-small)", whiteSpace: "pre-wrap" }}>
          The special lagnas refine the natal reading: {report.lagnas.map((l) => `${l.name} in ${l.sign} (House ${l.house}, lord ${l.lord})`).join("; ")}. Use Arudha for
          public image, Upapada for marriage timing, Indu for wealth flowering, Bhrigu Bindu for karmic event
          triggers, Ghati for authority, Sri for dharma/fortune, and Karakamsha for the soul's direction.
          Transits and dasha operating on these points mature their promise.
        </div>
      </div>
    </div>
  );
};
