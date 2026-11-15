"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { Sidebar, TabId } from "@/components/Sidebar";
import { BirthSummaryPill } from "@/components/BirthSummaryPill";
import { NorthIndianChart } from "@/components/NorthIndianChart";
import { PlanetsTable } from "@/components/PlanetsTable";
import { YogasView } from "@/components/YogasView";
import { TransitsView } from "@/components/TransitsView";
import { DashaView } from "@/components/DashaView";
import { PanchangaView } from "@/components/PanchangaView";
import { CompatibilityView } from "@/components/CompatibilityView";
import { MuhurthaView } from "@/components/MuhurthaView";
import { ConsultationView } from "@/components/ConsultationView";
import { RemediesView } from "@/components/RemediesView";
import { VarshaphalView } from "@/components/VarshaphalView";
import { KalsarpView } from "@/components/KalsarpView";
import { SpecialLagnasView } from "@/components/SpecialLagnasView";
import { ChakraView } from "@/components/ChakraView";
import { RashiFalView } from "@/components/RashiFalView";
import { AshtakavargaView } from "@/components/AshtakavargaView";
import { BirthDataInput, ChartData, getBirthKey } from "@/lib/types";
import { fetchChart, checkApiHealth } from "@/lib/api";
import { Sparkles, Layers } from "lucide-react";
import { DEFAULT_LOCATION, DEFAULT_AYANAMSA, DEFAULT_HOUSE_SYSTEM } from "@/config/defaults";

const VARGAS = [
  "D1", "D2", "D3", "D4", "D7", "D9", "D10",
  "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"
];

const DEFAULT_BIRTH_DATA: BirthDataInput = {
  year: 1997,
  month: 5,
  day: 22,
  hour: 4,
  minute: 53,
  second: 0,
  latitude: DEFAULT_LOCATION.lat || 27.8667,
  longitude: DEFAULT_LOCATION.lon || 83.4833,
  timezone: DEFAULT_LOCATION.tz || "Asia/Kathmandu",
  place_name: DEFAULT_LOCATION.place || "Palpa, Nepal",
  ayanamsa: DEFAULT_AYANAMSA,
  house_system: DEFAULT_HOUSE_SYSTEM,
};

const VALID_TABS: TabId[] = [
  "chart",
  "transits",
  "dasha",
  "panchanga",
  "compatibility",
  "muhurtha",
  "remedies",
  "varshaphal",
  "kalsarp",
  "special-lagnas",
  "chakra",
  "rashi-fal",
  "consult",
];

function isValidTab(t: string | null | undefined): t is TabId {
  return !!t && (VALID_TABS as string[]).includes(t);
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabId>("chart");
  const [apiStatus, setApiStatus] = useState<"connected" | "offline" | "checking">("checking");
  const [selectedVarga, setSelectedVarga] = useState("D1");
  const [legalModalOpen, setLegalModalOpen] = useState(false);
  const [sidebarSlim, setSidebarSlim] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const [birthData, setBirthData] = useState<BirthDataInput>(DEFAULT_BIRTH_DATA);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loadingChart, setLoadingChart] = useState(false);
  const [chartError, setChartError] = useState<string | null>(null);

  useEffect(() => {
    checkApiHealth().then(({ status }) => {
      setApiStatus(status === "connected" ? "connected" : "offline");
    });
  }, []);

  const handleTabChange = (tab: TabId) => {
    setActiveTab(tab);
    try {
      localStorage.setItem("nakshatra_active_tab", tab);
      if (typeof window !== "undefined") {
        window.history.replaceState(null, "", `#${tab}`);
      }
    } catch {}
  };

  const handleVargaChange = (v: string) => {
    setSelectedVarga(v);
    try {
      localStorage.setItem("nakshatra_selected_varga", v);
    } catch {}
  };

  const handleToggleSlim = () => {
    setSidebarSlim((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("nakshatra_sidebar_slim", String(next));
      } catch {}
      return next;
    });
  };

  const handleCalculateChart = async (data: BirthDataInput) => {
    const oldKey = getBirthKey(birthData);
    const newKey = getBirthKey(data);
    if (oldKey !== newKey) {
      try {
        localStorage.removeItem("nakshatra_consultation_messages");
        localStorage.setItem("nakshatra_consult_chart_key", newKey);
      } catch {}
    }

    setBirthData(data);
    setLoadingChart(true);
    setChartError(null);
    try {
      const chart = await fetchChart(data);
      setChartData(chart);
      try {
        localStorage.setItem("nakshatra_birth_data", JSON.stringify(data));
        localStorage.setItem("nakshatra_chart_data", JSON.stringify(chart));
      } catch {}
    } catch (e: unknown) {
      setChartError((e as Error).message);
    } finally {
      setLoadingChart(false);
    }
  };

  // Client hydration on mount: restore tab from hash/storage, restore preferences and cached chart
  useEffect(() => {
    // 1. Restore tab from hash or localStorage
    const hash = window.location.hash.replace("#", "");
    if (isValidTab(hash)) {
      setActiveTab(hash);
    } else {
      try {
        const savedTab = localStorage.getItem("nakshatra_active_tab");
        if (isValidTab(savedTab)) {
          setActiveTab(savedTab);
          window.history.replaceState(null, "", `#${savedTab}`);
        }
      } catch {}
    }

    const onHashChange = () => {
      const currentHash = window.location.hash.replace("#", "");
      if (isValidTab(currentHash)) {
        setActiveTab(currentHash);
        try {
          localStorage.setItem("nakshatra_active_tab", currentHash);
        } catch {}
      }
    };
    window.addEventListener("hashchange", onHashChange);

    // 2. Restore sidebar & chart viewing preferences
    try {
      const savedSlim = localStorage.getItem("nakshatra_sidebar_slim");
      if (savedSlim !== null) setSidebarSlim(savedSlim === "true");

      const savedVarga = localStorage.getItem("nakshatra_selected_varga");
      if (savedVarga && VARGAS.includes(savedVarga)) setSelectedVarga(savedVarga);
    } catch {}

    // 3. Restore birth data and cached chart
    let activeBirth = DEFAULT_BIRTH_DATA;
    try {
      const savedBirth = localStorage.getItem("nakshatra_birth_data");
      if (savedBirth) {
        const parsedBirth = JSON.parse(savedBirth);
        if (parsedBirth && parsedBirth.year) {
          activeBirth = parsedBirth;
          setBirthData(parsedBirth);
        }
      }
    } catch {}

    let hasCachedChart = false;
    try {
      const savedChart = localStorage.getItem("nakshatra_chart_data");
      if (savedChart) {
        const parsedChart = JSON.parse(savedChart);
        if (parsedChart && parsedChart.planets && parsedChart.houses) {
          setChartData(parsedChart);
          hasCachedChart = true;
        }
      }
    } catch {}

    // Only hit ephemeris calculation API if not already cached
    if (!hasCachedChart) {
      handleCalculateChart(activeBirth);
    }

    return () => {
      window.removeEventListener("hashchange", onHashChange);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      className={`app-shell${sidebarSlim ? " sidebar-slim" : ""}`}
      style={{ position: "relative" }}
    >
      {/* ── Header ── */}
      <Navbar
        apiStatus={apiStatus}
        mobileMenuOpen={mobileMenuOpen}
        onToggleMobile={() => setMobileMenuOpen((v) => !v)}
        onToggleSlim={handleToggleSlim}
        sidebarSlim={sidebarSlim}
      />

      {/* ── Sidebar ── */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        slim={sidebarSlim}
        onToggleSlim={handleToggleSlim}
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* ── Main content ── */}
      <main
        className="app-main fade-up"
        style={{
          padding: "var(--space-6)",
          maxWidth: "1440px",
          width: "100%",
        }}
        key={activeTab} /* remount fade-up per tab switch */
      >
        {/* ═══ Birth Chart ═══════════════════════════════════════════════ */}
        {activeTab === "chart" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
            <BirthSummaryPill
              birthData={birthData}
              hasChart={!!chartData}
              onSubmit={handleCalculateChart}
              loading={loadingChart}
            />

            {chartError && (
              <div
                className="card"
                style={{ padding: "var(--space-4)", color: "var(--rose)", borderColor: "var(--rose)" }}
                role="alert"
              >
                Failed to compute chart: {chartError}
              </div>
            )}

            {chartData && (
              <>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "minmax(0, 1.3fr) minmax(0, 1fr)",
                    gap: "var(--space-6)",
                  }}
                  className="chart-grid"
                >
                  {/* Visual Chart Card */}
                  <div className="card" style={{ padding: "var(--space-5)" }}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "var(--space-4)",
                        flexWrap: "wrap",
                        gap: "var(--space-3)",
                      }}
                    >
                      {/* Section title */}
                      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                        <span className="serif-section" style={{ fontSize: "1.05rem", color: "var(--gold-bright)", letterSpacing: "0.03em" }}>
                          Kundali Chart
                        </span>
                      </div>

                      {/* Varga chips (scrollable row for all 16 Shodashavargas) */}
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "var(--space-1)",
                          overflowX: "auto",
                          maxWidth: "100%",
                          width: "100%",
                          minWidth: 0,
                          paddingBottom: "2px",
                          WebkitOverflowScrolling: "touch",
                          scrollbarWidth: "none",
                        }}
                        tabIndex={0}
                        aria-label="Divisional chart selector"
                      >
                        <Layers size={13} color="var(--text-low)" aria-hidden="true" style={{ flexShrink: 0, marginRight: "2px" }} />
                        {VARGAS.map((v) => (
                          <button
                            key={v}
                            onClick={() => handleVargaChange(v)}
                            className={`chip${selectedVarga === v ? " active" : ""}`}
                            aria-pressed={selectedVarga === v}
                          >
                            {v}
                          </button>
                        ))}
                      </div>
                    </div>

                    <NorthIndianChart chart={chartData} varga={selectedVarga} size={500} />
                  </div>

                  {/* Data Rail */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)" }}>
                    <PlanetsTable chart={chartData} />
                    <YogasView birth={birthData} />
                  </div>
                </div>

                {/* Ashtakavarga Comprehensive System (SAV & BAV) */}
                <AshtakavargaView ashtakavarga={chartData.ashtakavarga} />
              </>
            )}
          </div>
        )}

        {/* ═══ Transits ══════════════════════════════════════════════════ */}
        {activeTab === "transits" && (
          <TransitsView birth={birthData} onNavigateToChart={() => handleTabChange("chart")} />
        )}

        {/* ═══ Dasha ═════════════════════════════════════════════════════ */}
        {activeTab === "dasha" && (
          <DashaView
            dashas={chartData?.dashas}
            birth={birthData}
            chart={chartData}
            onNavigateToChart={() => handleTabChange("chart")}
          />
        )}

        {/* ═══ Panchanga ═════════════════════════════════════════════════ */}
        {activeTab === "panchanga" && (
          <PanchangaView
            defaultLat={birthData.latitude}
            defaultLon={birthData.longitude}
            defaultTz={birthData.timezone}
          />
        )}

        {/* ═══ Compatibility ══════════════════════════════════════════════ */}
        {activeTab === "compatibility" && <CompatibilityView defaultBride={birthData} />}

        {/* ═══ Muhurtha ══════════════════════════════════════════════════ */}
        {activeTab === "muhurtha" && (
          <MuhurthaView
            defaultLat={birthData.latitude}
            defaultLon={birthData.longitude}
            defaultTz={birthData.timezone}
          />
        )}

        {/* ═══ Remedies & Upayas ═══════════════════════════════════════════ */}
        {activeTab === "remedies" && (
          <RemediesView
            birth={chartData ? birthData : undefined}
            onConsultClick={() => {
              handleTabChange("consult");
            }}
          />
        )}

        {/* ═══ Varshaphal / Barsha Fal ═════════════════════════════════════════════════ */}
        {activeTab === "varshaphal" && (
          <VarshaphalView birth={chartData ? birthData : undefined} />
        )}

        {/* ═══ Kalsarp Dosha Analyzer ═══════════════════════════════════════════════════ */}
        {activeTab === "kalsarp" && (
          <KalsarpView birth={chartData ? birthData : undefined} />
        )}

        {/* ═══ Special Lagnas (Vishesha Lagna) ═════════════════════════════════════════════════════ */}
        {activeTab === "special-lagnas" && (
          <SpecialLagnasView birth={chartData ? birthData : undefined} />
        )}

        {/* ═══ Vedic Chakra Systems ════════════════════════════════════════════════════════════════════ */}
        {activeTab === "chakra" && (
          <ChakraView birth={chartData ? birthData : undefined} />
        )}

        {/* ═══ Rashi Fal — Moon-sign Horoscope ════════════════════════════════════════════════════════════════ */}
        {activeTab === "rashi-fal" && (
          <RashiFalView birth={chartData ? birthData : undefined} />
        )}

        {/* ═══ AI Consultation ═══════════════════════════════════════════════════════════════════════════════════════ */}
        {activeTab === "consult" && (
          <ConsultationView
            key={getBirthKey(chartData ? birthData : undefined)}
            birth={chartData ? birthData : undefined}
          />
        )}
      </main>

      {/* ── Legal Modal ── */}
      {legalModalOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "var(--bg-overlay)",
            backdropFilter: "blur(8px)",
            zIndex: 300,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "var(--space-5)",
          }}
          onClick={() => setLegalModalOpen(false)}
        >
          <div
            className="card"
            style={{
              maxWidth: "680px",
              width: "100%",
              padding: "var(--space-8)",
              maxHeight: "85vh",
              overflowY: "auto",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "var(--space-4)",
              }}
            >
              <h3
                className="title-serif gold-gradient-text"
                style={{ fontSize: "1.15rem", display: "flex", alignItems: "center", gap: "var(--space-2)" }}
              >
                <Sparkles size={18} color="var(--gold-vivid)" aria-hidden="true" />
                Legal, Licensing &amp; Classical Rights
              </h3>
              <button
                onClick={() => setLegalModalOpen(false)}
                className="btn-ghost"
                aria-label="Close legal notice"
              >
                ✕
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)", fontSize: "var(--type-label)", color: "var(--text-high)", lineHeight: 1.6 }}>
              <div style={{ padding: "12px 16px", background: "var(--gold-dim)", borderRadius: "var(--radius-sm)", border: "1px solid var(--gold-border)" }}>
                <strong style={{ color: "var(--gold-bright)" }}>Swiss Ephemeris Dual Licensing (Astrodienst AG / pyswisseph):</strong>
                <p style={{ marginTop: "4px", color: "var(--text-mid)", fontSize: "var(--type-micro)" }}>
                  The astronomical engine uses Swiss Ephemeris (`pyswisseph`), copyright © 1997–2026 Astrodienst AG.
                  Nakshatra is released as open source under GNU AGPL-3.0. Closed-source commercial products incorporating
                  Swiss Ephemeris require a commercial license directly from Astrodienst AG.
                </p>
              </div>

              <div>
                <strong style={{ color: "var(--cyan-vivid)" }}>Classical Scripture Attribution:</strong>
                <ul style={{ marginTop: "6px", paddingLeft: "18px", color: "var(--text-mid)", fontSize: "var(--type-micro)" }}>
                  <li><strong>Brihat Parashara Hora Shastra (BPHS):</strong> Root Sanskrit verses in public domain; English commentary (R. Santhanam 1984) referenced for educational study.</li>
                  <li><strong>Saravali &amp; Phaladeepika:</strong> Classical Sanskrit treatises in public domain.</li>
                  <li><strong>Modern Commentaries:</strong> Indexed as fair use research excerpts for scriptural grounding.</li>
                </ul>
              </div>

              <div style={{ padding: "12px 16px", background: "var(--emerald-dim)", borderRadius: "var(--radius-sm)", border: "1px solid rgba(16,185,129,0.25)" }}>
                <strong style={{ color: "var(--emerald)" }}>Zero Data Retention &amp; GDPR Privacy:</strong>
                <p style={{ marginTop: "4px", color: "var(--text-mid)", fontSize: "var(--type-micro)" }}>
                  All calculations run entirely in memory. Exact coordinates, birth times, and questions are never persisted to databases or server logs.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Footer ── */}
      <footer
        style={{
          gridColumn: "1 / -1",
          padding: "16px var(--space-6)",
          borderTop: "1px solid var(--border-subtle)",
          textAlign: "center",
          fontSize: "var(--type-micro)",
          color: "var(--text-low)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "var(--space-3)",
        }}
      >
        <div>Nakshatra — Swiss Ephemeris (pyswisseph) · BPHS Classical RAG</div>
        <div style={{ display: "flex", gap: "var(--space-4)", alignItems: "center" }}>
          <span>Ayanamsa: {(birthData.ayanamsa ?? "").replace("jhora_", "JHora ").replace(/_/g, " ")}</span>
          <span>·</span>
          <span>{birthData.house_system}</span>
          <button
            onClick={() => setLegalModalOpen(true)}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--gold-bright)",
              cursor: "pointer",
              fontSize: "var(--type-micro)",
              textDecoration: "underline",
            }}
          >
            Licensing &amp; Legal
          </button>
        </div>
      </footer>
    </div>
  );
}
