"use client";

import React, { useState, useEffect } from "react";
import { BirthDataInput, YogaResult } from "@/lib/types";
import { fetchYogas } from "@/lib/api";
import { Award } from "lucide-react";

interface Props {
  birth: BirthDataInput;
}

export const YogasView: React.FC<Props> = ({ birth }) => {
  const [yogas, setYogas] = useState<YogaResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchYogas(birth)
      .then((data) => {
        if (!cancelled) setYogas(data);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError((e as Error).message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [birth]);

  if (loading) {
    return (
      <div className="glass-panel" style={{ padding: "30px", textAlign: "center", color: "var(--accent-gold)" }}>
        Scanning classical Parashara Yogas...
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel" style={{ padding: "20px", color: "var(--accent-rose)" }}>
        Could not load yogas: {error}
      </div>
    );
  }

  if (yogas.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: "30px", textAlign: "center", color: "var(--text-muted)" }}>
        No major classical yogas detected in this chart.
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ padding: "20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h4 className="title-serif gold-gradient-text" style={{ fontSize: "1.1rem", display: "flex", alignItems: "center", gap: "8px" }}>
          <Award size={18} color="#e5b94c" />
          Detected Classical Yogas ({yogas.length})
        </h4>
        <span className="badge badge-gold">Parashara Rules Engine</span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "14px" }}>
        {yogas.map((y, idx) => (
          <div
            key={idx}
            style={{
              background: "rgba(0,0,0,0.25)",
              border: "1px solid rgba(229, 185, 76, 0.2)",
              borderRadius: "10px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "8px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <h5 style={{ fontSize: "1.02rem", fontWeight: 700, color: "#fbe285" }}>
                {y.name}
              </h5>
              <span className="badge badge-cyan" style={{ fontSize: "0.7rem" }}>
                {y.category}
              </span>
            </div>

            <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", lineHeight: 1.45 }}>
              {y.description}
            </p>

            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "auto", paddingTop: "8px" }}>
              {y.planets_involved.map((p, pIdx) => (
                <span key={`${p}-${pIdx}`} className="badge badge-gold" style={{ fontSize: "0.68rem" }}>
                  {p}
                </span>
              ))}
              {y.houses_involved.map((h, hIdx) => (
                <span key={`${h}-${hIdx}`} className="badge badge-emerald" style={{ fontSize: "0.68rem" }}>
                  H{h}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
