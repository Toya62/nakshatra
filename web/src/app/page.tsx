"use client";

import React, { useState, useEffect } from "react";
import { Navbar, TabId } from "@/components/Navbar";
import { BirthForm } from "@/components/BirthForm";
import { SouthIndianChart } from "@/components/SouthIndianChart";
import { NorthIndianChart } from "@/components/NorthIndianChart";
import { PlanetsTable } from "@/components/PlanetsTable";
import { YogasView } from "@/components/YogasView";
import { TransitsView } from "@/components/TransitsView";
import { DashaView } from "@/components/DashaView";
import { PanchangaView } from "@/components/PanchangaView";
import { CompatibilityView } from "@/components/CompatibilityView";
import { MuhurthaView } from "@/components/MuhurthaView";
import { ConsultationView } from "@/components/ConsultationView";
import { BirthDataInput, ChartData } from "@/lib/types";
import { fetchChart, checkApiHealth } from "@/lib/api";
import { Sparkles, Layers } from "lucide-react";

const VARGAS = ["D1", "D9", "D10", "D60"];

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabId>("chart");
  const [apiStatus, setApiStatus] = useState<"connected" | "offline" | "checking">("checking");
  const [selectedVarga, setSelectedVarga] = useState("D1");
  const [chartStyle, setChartStyle] = useState<"north" | "south">("north");
  const [legalModalOpen, setLegalModalOpen] = useState(false);

  const [birthData, setBirthData] = useState<BirthDataInput>({
    year: 1997,
    month: 5,
    day: 22,
    hour: 4,
    minute: 53,
    second: 0,
    latitude: 27.8667,
    longitude: 83.4833,
    timezone: "Asia/Kathmandu",
    place_name: "Palpa, Nepal",
    ayanamsa: "jhora_lahiri",
    house_system: "WholeSign",
  });

  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loadingChart, setLoadingChart] = useState(false);
  const [chartError, setChartError] = useState<string | null>(null);

  // Check API health on mount and calculate initial chart
  useEffect(() => {
    checkApiHealth().then(({ status }) => {
      setApiStatus(status === "connected" ? "connected" : "offline");
    });
  }, []);

  const handleCalculateChart = async (data: BirthDataInput) => {
    setBirthData(data);
    setLoadingChart(true);
    setChartError(null);
    try {
      const chart = await fetchChart(data);
      setChartData(chart);
    } catch (e: unknown) {
      setChartError((e as Error).message);
    } finally {
      setLoadingChart(false);
    }
  };

  // Auto-calculate default chart on first load
  useEffect(() => {
    handleCalculateChart(birthData);
  }, []);

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} apiStatus={apiStatus} />

      <main style={{ flex: 1, padding: "28px 24px", maxWidth: "1380px", margin: "0 auto", width: "100%" }}>
        {/* Tab 1: Birth Chart */}
        {activeTab === "chart" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <BirthForm
              initialData={birthData}
              onSubmit={handleCalculateChart}
              loading={loadingChart}
            />

            {chartError && (
              <div className="glass-panel" style={{ padding: "18px", color: "var(--accent-rose)", borderColor: "var(--accent-rose)" }}>
                Failed to compute chart: {chartError}
              </div>
            )}

            {chartData && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(460px, 1fr))", gap: "24px" }}>
                {/* Visual Chart Card */}
                <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "10px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <Sparkles size={18} color="#e5b94c" />
                      <div style={{ display: "flex", gap: "4px" }}>
                        <button
                          onClick={() => setChartStyle("north")}
                          className={`badge ${chartStyle === "north" ? "badge-gold" : "badge-cyan"}`}
                          style={{
                            cursor: "pointer",
                            fontSize: "0.8rem",
                            padding: "4px 10px",
                            background: chartStyle === "north" ? "rgba(229,185,76,0.3)" : "transparent",
                          }}
                        >
                          North Indian (Diamond)
                        </button>
                        <button
                          onClick={() => setChartStyle("south")}
                          className={`badge ${chartStyle === "south" ? "badge-gold" : "badge-cyan"}`}
                          style={{
                            cursor: "pointer",
                            fontSize: "0.8rem",
                            padding: "4px 10px",
                            background: chartStyle === "south" ? "rgba(229,185,76,0.3)" : "transparent",
                          }}
                        >
                          South Indian (Grid)
                        </button>
                      </div>
                    </div>

                    {/* Varga Switcher */}
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <Layers size={14} color="var(--text-muted)" />
                      {VARGAS.map((v) => (
                        <button
                          key={v}
                          onClick={() => setSelectedVarga(v)}
                          className={`badge ${selectedVarga === v ? "badge-gold" : "badge-cyan"}`}
                          style={{
                            cursor: "pointer",
                            background: selectedVarga === v ? "rgba(229,185,76,0.3)" : "rgba(255,255,255,0.04)",
                          }}
                        >
                          {v}
                        </button>
                      ))}
                    </div>
                  </div>

                  {chartStyle === "north" ? (
                    <NorthIndianChart chart={chartData} varga={selectedVarga} size={480} />
                  ) : (
                    <SouthIndianChart chart={chartData} varga={selectedVarga} size={480} />
                  )}
                </div>

                {/* Planetary Ephemeris & Yogas */}
                <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                  <PlanetsTable chart={chartData} />
                  <YogasView birth={birthData} />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Transits */}
        {activeTab === "transits" && <TransitsView birth={birthData} />}

        {/* Tab 3: Dasha Timeline */}
        {activeTab === "dasha" && (
          <DashaView
            dashas={chartData?.dashas}
            birth={birthData}
            chart={chartData}
          />
        )}

        {/* Tab 4: Panchanga */}
        {activeTab === "panchanga" && (
          <PanchangaView
            defaultLat={birthData.latitude}
            defaultLon={birthData.longitude}
            defaultTz={birthData.timezone}
          />
        )}

        {/* Tab 5: Kundali Matching */}
        {activeTab === "compatibility" && <CompatibilityView defaultBride={birthData} />}

        {/* Tab 6: Muhurtha & Horas */}
        {activeTab === "muhurtha" && (
          <MuhurthaView
            defaultLat={birthData.latitude}
            defaultLon={birthData.longitude}
            defaultTz={birthData.timezone}
          />
        )}

        {/* Tab 7: AI Consultation */}
        {activeTab === "consult" && <ConsultationView birth={chartData ? birthData : undefined} />}
      </main>

      {/* Licensing & Rights Modal */}
      {legalModalOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(7, 9, 14, 0.8)",
            backdropFilter: "blur(8px)",
            zIndex: 100,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
          onClick={() => setLegalModalOpen(false)}
        >
          <div
            className="glass-panel"
            style={{
              maxWidth: "680px",
              width: "100%",
              padding: "28px",
              maxHeight: "85vh",
              overflowY: "auto",
              position: "relative",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 className="title-serif gold-gradient-text" style={{ fontSize: "1.25rem", display: "flex", alignItems: "center", gap: "8px" }}>
                <Sparkles size={20} color="#e5b94c" />
                Legal, Licensing & Classical Rights
              </h3>
              <button
                onClick={() => setLegalModalOpen(false)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  fontSize: "1.3rem",
                  cursor: "pointer",
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "16px", fontSize: "0.86rem", color: "var(--text-main)", lineHeight: 1.6 }}>
              <div style={{ padding: "12px 16px", background: "rgba(229, 185, 76, 0.1)", borderRadius: "8px", border: "1px solid rgba(229, 185, 76, 0.25)" }}>
                <strong style={{ color: "#fbe285" }}>Swiss Ephemeris Dual Licensing (Astrodienst AG / pyswisseph):</strong>
                <p style={{ marginTop: "4px", color: "var(--text-dim)", fontSize: "0.82rem" }}>
                  The astronomical engine uses Swiss Ephemeris (`pyswisseph`), copyright © 1997-2026 Astrodienst AG.
                  Nakshatra is released as open source under GNU AGPL-3.0. Closed-source commercial products incorporating
                  Swiss Ephemeris require a commercial license directly from Astrodienst AG.
                </p>
              </div>

              <div>
                <strong style={{ color: "#7dd3fc" }}>Classical Scripture Attribution:</strong>
                <ul style={{ marginTop: "6px", paddingLeft: "18px", color: "var(--text-dim)", fontSize: "0.82rem" }}>
                  <li><strong>Brihat Parashara Hora Shastra (BPHS):</strong> Root Sanskrit verses in public domain; English commentary (R. Santhanam 1984) referenced for educational study.</li>
                  <li><strong>Saravali & Phaladeepika:</strong> Classical Sanskrit treatises in public domain.</li>
                  <li><strong>Modern Commentaries:</strong> Indexed as fair use research excerpts for scriptural grounding.</li>
                </ul>
              </div>

              <div style={{ padding: "12px 16px", background: "rgba(16, 185, 129, 0.1)", borderRadius: "8px", border: "1px solid rgba(16, 185, 129, 0.25)" }}>
                <strong style={{ color: "#34d399" }}>Zero Data Retention & GDPR Privacy:</strong>
                <p style={{ marginTop: "4px", color: "var(--text-dim)", fontSize: "0.82rem" }}>
                  All calculations run entirely in memory. Exact coordinates, birth times, and questions are never persisted to databases or server logs.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer
        style={{
          padding: "20px 28px",
          borderTop: "1px solid rgba(255,255,255,0.06)",
          textAlign: "center",
          fontSize: "0.8rem",
          color: "var(--text-dim)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          maxWidth: "1380px",
          margin: "0 auto",
          width: "100%",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div>
          Nakshatra Vedic Engine — Swiss Ephemeris (`pyswisseph`) & BPHS Classical RAG
        </div>
        <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
          <span>Ayanamsa: Jagannatha Hora Lahiri</span>
          <button
            onClick={() => setLegalModalOpen(true)}
            style={{
              background: "transparent",
              border: "none",
              color: "#fbe285",
              cursor: "pointer",
              fontSize: "0.8rem",
              textDecoration: "underline",
            }}
          >
            Licensing & Legal Notice
          </button>
        </div>
      </footer>
    </div>
  );
}

