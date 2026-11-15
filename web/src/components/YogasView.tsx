"use client";

import React, { useState, useEffect } from "react";
import { BirthDataInput, YogaResult } from "@/lib/types";
import { fetchYogas } from "@/lib/api";
import { Award, ChevronDown, ChevronUp } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

interface Props {
  birth: BirthDataInput;
}

function YogaCard({ yoga }: { yoga: YogaResult }) {
  const { t, lang, num } = useLanguage();
  const [open, setOpen] = useState(false);

  return (
    <div
      style={{
        background: "var(--bg-subtle)",
        border: "1px solid var(--border-card)",
        borderRadius: "var(--radius-md)",
        overflow: "hidden",
        transition: "border-color 0.18s",
      }}
    >
      {/* Accordion trigger */}
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "var(--space-3) var(--space-4)",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          gap: "var(--space-3)",
          textAlign: "left",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", minWidth: 0 }}>
          <span
            style={{
              fontWeight: 700,
              fontSize: "var(--type-body)",
              color: "var(--gold-bright)",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {yoga.name}
          </span>
          <span className="badge badge-cyan" style={{ fontSize: "var(--type-micro)", flexShrink: 0 }}>
            {t.yogas.categories[yoga.category] || yoga.category}
          </span>
        </div>
        {open
          ? <ChevronUp size={14} color="var(--text-low)" aria-hidden="true" />
          : <ChevronDown size={14} color="var(--text-low)" aria-hidden="true" />}
      </button>

      {/* Expanded body */}
      {open && (
        <div
          style={{
            padding: "0 var(--space-4) var(--space-4)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-2)",
          }}
        >
          <p
            style={{
              fontSize: "var(--type-label)",
              color: "var(--text-mid)",
              lineHeight: 1.55,
            }}
          >
            {yoga.description}
          </p>

          {(yoga.planets_involved.length > 0 || yoga.houses_involved.length > 0) && (
            <div style={{ display: "flex", gap: "var(--space-1)", flexWrap: "wrap", paddingTop: "var(--space-1)" }}>
              {yoga.planets_involved.map((p, i) => (
                <span key={`p-${i}`} className="badge badge-gold" style={{ fontSize: "var(--type-micro)" }}>
                  {lang === "ne" ? (t.planets.names[p as keyof typeof t.planets.names] || p) : p}
                </span>
              ))}
              {yoga.houses_involved.map((h, i) => (
                <span key={`h-${i}`} className="badge badge-emerald" style={{ fontSize: "var(--type-micro)" }}>
                  {lang === "ne" ? `भाव ${num(h)}` : `H${h}`}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export const YogasView: React.FC<Props> = ({ birth }) => {
  const { t, num } = useLanguage();
  const [yogas, setYogas] = useState<YogaResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchYogas(birth)
      .then((data) => { if (!cancelled) setYogas(data); })
      .catch((e: unknown) => { if (!cancelled) setError((e as Error).message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [birth]);

  return (
    <div className="card" style={{ padding: "var(--space-5)" }}>
      {/* Header */}
      <div className="section-header">
        <h4 className="section-title" style={{ fontSize: "var(--type-heading)" }}>
          <Award size={15} color="var(--gold-vivid)" aria-hidden="true" />
          {t.nav.yogas}
          {!loading && yogas.length > 0 && (
            <span className="badge badge-gold" style={{ fontSize: "var(--type-micro)", marginLeft: "var(--space-2)" }}>
              {num(yogas.length)} {t.yogas.found}
            </span>
          )}
        </h4>
        <span className="badge badge-cyan" style={{ fontSize: "var(--type-micro)" }}>
          {t.yogas.parasharaEngine}
        </span>
      </div>

      {/* Loading skeleton */}
      {loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton" style={{ height: "44px", borderRadius: "var(--radius-md)" }} />
          ))}
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <p style={{ fontSize: "var(--type-label)", color: "var(--rose)" }}>
          {t.yogas.loadError}: {error}
        </p>
      )}

      {/* Empty */}
      {!loading && !error && yogas.length === 0 && (
        <p style={{ fontSize: "var(--type-label)", color: "var(--text-low)", textAlign: "center", padding: "var(--space-6) 0" }}>
          {t.yogas.noYogas}
        </p>
      )}

      {/* Yoga list — accordion */}
      {!loading && !error && yogas.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
          {yogas.map((y, idx) => (
            <YogaCard key={`${y.name}-${idx}`} yoga={y} />
          ))}
        </div>
      )}
    </div>
  );
};
