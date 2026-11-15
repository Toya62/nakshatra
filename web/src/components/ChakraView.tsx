"use client";

import React, { useEffect, useState } from "react";
import { ShieldAlert, Clock, Activity } from "lucide-react";
import {
  BirthDataInput,
  ChakraInput,
  ChakraReport,
  CompoundPair,
  GhatiHouse,
  NavataraEntry,
} from "@/lib/types";
import { fetchChakra } from "@/lib/api";

interface Props {
  birth?: BirthDataInput;
}

const TARA_STYLE: Record<string, { color: string; bg: string }> = {
  good: { color: "var(--emerald)", bg: "rgba(16, 185, 129, 0.12)" },
  bad: { color: "var(--rose)", bg: "rgba(239, 68, 68, 0.12)" },
  neutral: { color: "var(--text-mid)", bg: "rgba(107, 114, 128, 0.08)" },
};

const COMPOUND_STYLE: Record<string, { color: string; bg: string }> = {
  intimate_friend: { color: "var(--emerald)", bg: "rgba(16, 185, 129, 0.14)" },
  friend: { color: "var(--cyan-vivid)", bg: "rgba(6, 182, 212, 0.10)" },
  neutral: { color: "var(--text-mid)", bg: "rgba(107, 114, 128, 0.08)" },
  enemy: { color: "var(--amber)", bg: "rgba(245, 158, 11, 0.10)" },
  bitter_enemy: { color: "var(--rose)", bg: "rgba(239, 68, 68, 0.14)" },
};

export const ChakraView: React.FC<Props> = ({ birth }: Props) => {
  const [report, setReport] = useState<ChakraReport | null>(null);
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

    const payload: ChakraInput = {
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

    fetchChakra(payload)
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
          <Activity size={32} color="var(--gold-vivid)" style={{ margin: "0 auto var(--space-3)" }} />
          <h3 style={{ fontSize: "var(--type-heading)", color: "var(--gold-vivid)", marginBottom: "var(--space-1)" }}>
            Vedic Chakra Systems
          </h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>
            Enter your birth parameters to compute Navatara (9 tara), Compound (Panchadha Maitri)
            relationships and the Ghatchakra wheel.
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
            Building Chakras…
          </h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>
            Deriving tara, planetary relationships and the ghati wheel.
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
          <h3 style={{ color: "var(--rose)", fontSize: "var(--type-body)", fontWeight: 700 }}>Chakra Calculation Error</h3>
          <p style={{ color: "var(--text-mid)", fontSize: "var(--type-small)" }}>{error || "Unable to compute chakra systems."}</p>
        </div>
      </div>
    );
  }

  const good = report.navatara.filter((n) => n.nature === "good").length;
  const bad = report.navatara.filter((n) => n.nature === "bad").length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)", maxWidth: "var(--size-container-lg)", margin: "0 auto", width: "100%" }}>
      {/* ── Header Banner ── */}
      <div className="card" style={{ padding: "var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-3)" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
              <Activity size={24} color="var(--gold-vivid)" />
              <h2 style={{ fontSize: "var(--type-title)", fontWeight: 700, color: "var(--text-high)" }}>
                Vedic Chakra Systems
              </h2>
            </div>
            <p style={{ fontSize: "var(--type-small)", color: "var(--text-mid)", marginTop: "var(--space-1)" }}>
              Janma Nakshatra: <strong>{report.janma_nakshatra}</strong>. {good} good / {bad} bad tara positions.
            </p>
          </div>
          <div style={{ display: "flex", gap: "var(--space-2)" }}>
            <span style={{ fontSize: "var(--type-micro)", fontWeight: 700, padding: "var(--space-0-5) var(--space-2)", borderRadius: "var(--radius-sm)", background: "var(--emerald-dim)", border: "1px solid var(--emerald)", color: "var(--emerald)" }}>{good} Good Tara</span>
            <span style={{ fontSize: "var(--type-micro)", fontWeight: 700, padding: "var(--space-0-5) var(--space-2)", borderRadius: "var(--radius-sm)", background: "var(--rose-dim)", border: "1px solid var(--rose)", color: "var(--rose)" }}>{bad} Bad Tara</span>
          </div>
        </div>

        <div style={{ marginTop: "var(--space-4)", padding: "var(--space-3) var(--space-4)", background: "var(--bg-subtle)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)", fontSize: "var(--type-small)", color: "var(--text-high)", lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
          {report.summary}
        </div>
      </div>

      {/* ── Navatara Chakra ── */}
      <div className="card" style={{ padding: "var(--space-4) var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", margin: 0 }}>Navatara Chakra (9 Tara)</h4>
          <span style={{ fontSize: "var(--type-label)", color: "var(--text-low)" }}>{report.navatara.length} planets</span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--type-micro)" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border-subtle)" }}>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Graha</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Nakshatra</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Count from Janma</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Tara</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Nature</th>
              </tr>
            </thead>
            <tbody>
              {report.navatara.map((n: NavataraEntry, idx: number) => {
                const s = TARA_STYLE[n.nature];
                return (
                  <tr key={idx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-high)", fontWeight: 600 }}>{n.planet}</td>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)" }}>{n.nakshatra}</td>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)", fontFamily: "var(--font-mono)" }}>{n.count_from_janma}</td>
                    <td style={{ padding: "var(--space-1) var(--space-2)", fontWeight: 600, color: s.color }}>{n.tara}</td>
                    <td style={{ padding: "var(--space-1) var(--space-2)" }}>
                      <span style={{ fontSize: "var(--type-label)", fontWeight: 600, padding: "1px 6px", borderRadius: "var(--radius-sm)", background: s.bg, color: s.color, border: `1px solid ${s.color}` }}>{n.nature}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p style={{ fontSize: "var(--type-label)", color: "var(--text-low)", marginTop: "var(--space-2)", fontStyle: "italic" }}>
          Good: Sampat, Kshema, Sadhaka, Mitra, Ati-Mitra &nbsp;•&nbsp; Bad: Janma, Vipat, Pratyari, Vadha.
        </p>
      </div>

      {/* ── Compound Relationship ── */}
      <div className="card" style={{ padding: "var(--space-4) var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", margin: 0 }}>Compound Relationship (Panchadha Maitri)</h4>
          <span style={{ fontSize: "var(--type-label)", color: "var(--text-low)" }}>{report.compound_relationships.length} pairs</span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--type-micro)" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border-subtle)" }}>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Planet A</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Planet B</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Natural</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Temporary</th>
                <th style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-low)", fontSize: "var(--type-label)" }}>Compound</th>
              </tr>
            </thead>
            <tbody>
              {report.compound_relationships.map((c: CompoundPair, idx: number) => {
                const s = COMPOUND_STYLE[c.compound];
                return (
                  <tr key={idx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-high)", fontWeight: 600 }}>{c.planet_a}</td>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)" }}>{c.planet_b}</td>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)" }}>{c.natural}</td>
                    <td style={{ padding: "var(--space-1) var(--space-2)", color: "var(--text-mid)" }}>{c.temporary}</td>
                    <td style={{ padding: "var(--space-1) var(--space-2)" }}>
                      <span style={{ fontSize: "var(--type-label)", fontWeight: 600, padding: "1px 6px", borderRadius: "var(--radius-sm)", background: s.bg, color: s.color, border: `1px solid ${s.color}` }}>{c.compound.replace(/_/g, " ").replace(/\b\w/g, (ch) => ch.toUpperCase())}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p style={{ fontSize: "var(--type-label)", color: "var(--text-low)", marginTop: "var(--space-2)", fontStyle: "italic" }}>
          Intimate Friend = natural friend + temporary friend &nbsp;•&nbsp; Bitter Enemy = natural enemy + temporary enemy.
        </p>
      </div>

      {/* ── Ghatchakra ── */}
      <div className="card" style={{ padding: "var(--space-4) var(--space-5)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", margin: 0 }}>Ghatchakra Wheel</h4>
          <span style={{ fontSize: "var(--type-label)", color: "var(--text-low)" }}>{report.ghatchakra.length} houses</span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "var(--space-2)" }}>
          {report.ghatchakra.map((g: GhatiHouse, idx: number) => (
            <div
              key={idx}
              style={{ background: "var(--bg-subtle)", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)", textAlign: "center", fontSize: "var(--type-micro)" }}
            >
              <div style={{ fontWeight: 600, color: "var(--text-low)", fontSize: "var(--type-label)", textTransform: "uppercase" }}>House {g.house}</div>
              <div style={{ color: "var(--gold-vivid)", fontWeight: 700 }}>{g.sign}</div>
              <div style={{ color: "var(--text-mid)", fontSize: "var(--type-label)" }}>Ruler: {g.ruler}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
