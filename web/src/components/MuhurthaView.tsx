"use client";

import React, { useState, useEffect } from "react";
import {
  Sun,
  Calendar,
  Briefcase,
  Plane,
  Home,
  Heart,
  DollarSign,
  Activity,
} from "lucide-react";
import { BirthDataInput, MuhurthaReport } from "@/lib/types";
import { fetchMuhurtha } from "@/lib/api";
import { DEFAULT_LOCATION } from "@/config/defaults";

interface Props {
  defaultLat?: number;
  defaultLon?: number;
  defaultTz?: string;
}

export const MuhurthaView: React.FC<Props> = ({
  defaultLat = DEFAULT_LOCATION.lat || 28.6139,
  defaultLon = DEFAULT_LOCATION.lon || 77.209,
  defaultTz = DEFAULT_LOCATION.tz || "Asia/Kolkata",
}) => {
  const [input, setInput] = useState<BirthDataInput>({
    year: 2026,
    month: 10,
    day: 14,
    hour: 12,
    minute: 0,
    second: 0,
    latitude: defaultLat,
    longitude: defaultLon,
    timezone: defaultTz,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<MuhurthaReport | null>(null);
  const [timelineTab, setTimelineTab] = useState<"horas" | "choghadiyas">("horas");

  const loadMuhurtha = async (params: BirthDataInput) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchMuhurtha(params);
      setReport(res);
    } catch (err: unknown) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const now = new Date();
    const clientInput: BirthDataInput = {
      year: now.getFullYear(),
      month: now.getMonth() + 1,
      day: now.getDate(),
      hour: now.getHours(),
      minute: now.getMinutes(),
      second: 0,
      latitude: defaultLat,
      longitude: defaultLon,
      timezone: defaultTz,
    };
    setInput(clientInput);
    loadMuhurtha(clientInput);
  }, [defaultLat, defaultLon, defaultTz]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadMuhurtha(input);
  };

   return (
     <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
       {/* Header Banner */}
       <div className="card" style={{ padding: "var(--space-5) var(--space-6)" }}>
         <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-1)" }}>
           <div
             style={{
               width: "36px",
               height: "36px",
               borderRadius: "var(--radius-md)",
               background: "linear-gradient(135deg, rgba(229,185,76,0.2) 0%, rgba(16,185,129,0.2) 100%)",
               border: "1px solid rgba(229,185,76,0.35)",
               display: "flex",
               alignItems: "center",
               justifyContent: "center",
               flexShrink: 0,
             }}
           >
             <Sun size={18} color="var(--gold-bright)" />
           </div>
           <h2 className="title-serif gold-gradient-text" style={{ fontSize: "1.4rem", fontWeight: 700 }}>
             Vedic Muhurtha & Planetary Election
           </h2>
         </div>
          <p style={{ color: "var(--text-muted)", fontSize: "var(--type-body)", maxWidth: "860px", lineHeight: 1.5 }}>
           Real-time electional astrology calculating 24 Chaldean Planetary Horas, 16 Choghadiyas,
           solar culmination (Abhijit & Brahma Muhurthas), Rahu Kalam afflictions, and classical Siddhi Yogas
           for decision-making and enterprise ventures.
         </p>
       </div>

       {/* Time & Place Form */}
       <form onSubmit={handleSubmit} className="card" style={{ padding: "var(--space-5)" }}>
         <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "var(--space-3)", alignItems: "flex-end" }}>
            <div>
              <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-0-5)" }}>
                Date
              </label>
              <input
                type="date"
                value={`${input.year}-${String(input.month).padStart(2, "0")}-${String(input.day).padStart(2, "0")}`}
                onChange={(e) => {
                  const [y, m, d] = e.target.value.split("-").map(Number);
                  if (y && m && d) setInput({ ...input, year: y, month: m, day: d });
                }}

              />
            </div>

            <div>
              <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-0-5)" }}>
                Time
              </label>
              <input
                type="time"
                value={`${String(input.hour).padStart(2, "0")}:${String(input.minute).padStart(2, "0")}`}
                onChange={(e) => {
                  const [h, m] = e.target.value.split(":").map(Number);
                  setInput({ ...input, hour: h || 0, minute: m || 0 });
                }}

              />
            </div>

            <div>
              <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-0-5)" }}>
                Latitude
              </label>
              <input
                type="number"
                step="0.0001"
                value={input.latitude}
                onChange={(e) => setInput({ ...input, latitude: parseFloat(e.target.value) || 0 })}

              />
            </div>

            <div>
              <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-0-5)" }}>
                Longitude
              </label>
              <input
                type="number"
                step="0.0001"
                value={input.longitude}
                onChange={(e) => setInput({ ...input, longitude: parseFloat(e.target.value) || 0 })}

              />
            </div>

            <div>
              <label style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block", marginBottom: "var(--space-0-5)" }}>
                Timezone
              </label>
              <input
                type="text"
                value={input.timezone}
                onChange={(e) => setInput({ ...input, timezone: e.target.value })}

              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary"
              style={{
                height: "40px",
                padding: "0 var(--space-4)",
                whiteSpace: "nowrap",
              }}
            >
              <Calendar size={15} />
              {loading ? "Evaluating..." : "Evaluate"}
            </button>
        </div>
      </form>

       {error && (
         <div className="card" style={{ padding: "var(--space-3)", color: "var(--rose)", borderColor: "var(--rose)" }} role="alert">
           {error}
         </div>
       )}

       {report && (
         <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
           {/* Main Score & Solar Bounds Card */}
           <div
              className="card"
              style={{
                padding: "var(--space-5) var(--space-6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: "var(--space-5)",
                border: `var(--border-width) solid ${
                  report.muhurtha_score >= 70
                    ? "rgba(16, 185, 129, 0.6)"
                    : report.muhurtha_score >= 50
                    ? "rgba(56, 189, 248, 0.6)"
                    : "rgba(244, 63, 94, 0.6)"
                }`,
              }}
           >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-1-5)" }}>
                <span
                  style={{
                    fontSize: "2.5rem",
                    fontWeight: 900,
                     color:
                       report.muhurtha_score >= 70
                         ? "var(--emerald)"
                         : report.muhurtha_score >= 50
                         ? "var(--cyan-vivid)"
                         : "var(--rose)",
                  }}
                >
                  {report.muhurtha_score}
                </span>
                <span style={{ fontSize: "1.2rem", color: "var(--text-muted)", fontWeight: 600 }}>/ 100</span>
                 <span
                   className={`badge ${
                     report.muhurtha_score >= 70
                       ? "badge-emerald"
                       : report.muhurtha_score >= 50
                       ? "badge-cyan"
                       : "badge-rose"
                   }`}
                   style={{ fontSize: "0.85rem", padding: "var(--space-0-5) var(--space-2)" }}
                 >
                  {report.verdict}
                </span>
              </div>
              <p style={{ color: "var(--text-bright)", fontSize: "0.92rem", fontWeight: 500 }}>
                {report.recommendation}
              </p>
            </div>

             <div style={{ display: "flex", gap: "var(--space-4-5)", color: "var(--text-muted)", fontSize: "0.82rem" }}>
              <div>
                 <span style={{ color: "var(--amber)", fontWeight: 600 }}>Sunrise:</span> {report.sunrise_time}
              </div>
              <div>
                <span style={{ color: "var(--rose)", fontWeight: 600 }}>Sunset:</span> {report.sunset_time}
              </div>
            </div>
          </div>

           {/* Active Hora & Active Choghadiya */}
           <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-5)" }}>
             <div className="card" style={{ padding: "var(--space-5)", borderLeft: "var(--border-width-4) solid var(--amber)" }}>
               <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-2)" }}>
                 <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                   Active Planetary Hora
                 </span>
                 <span className={`badge ${report.current_hora.nature === "Benefic" ? "badge-emerald" : "badge-rose"}`}>
                   {report.current_hora.nature}
                 </span>
               </div>
               <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-bright)", marginBottom: "var(--space-0-5)" }}>
                 {report.current_hora.ruling_planet} Hora
               </h3>
               <p style={{ fontSize: "0.82rem", color: "var(--amber)", marginBottom: "var(--space-2-5)" }}>
                 {report.current_hora.start_time} - {report.current_hora.end_time} ({report.current_hora.period_type})
               </p>
              <p style={{ fontSize: "0.84rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                <strong>Recommended:</strong> {report.current_hora.recommended_activities}
              </p>
            </div>

             <div className="card" style={{ padding: "var(--space-5)", borderLeft: "var(--border-width-4) solid var(--cyan-vivid)" }}>
               <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-2)" }}>
                 <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                   Active Choghadiya
                 </span>
                 <span className={`badge ${report.current_choghadiya.score >= 70 ? "badge-emerald" : "badge-rose"}`}>
                   {report.current_choghadiya.nature}
                 </span>
               </div>
               <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-bright)", marginBottom: "var(--space-0-5)" }}>
                 {report.current_choghadiya.name} Choghadiya
               </h3>
               <p style={{ fontSize: "0.82rem", color: "var(--cyan-vivid)", marginBottom: "var(--space-2-5)" }}>
                 {report.current_choghadiya.start_time} - {report.current_choghadiya.end_time} ({report.current_choghadiya.period_type})
               </p>
              <p style={{ fontSize: "0.84rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                Ruler: <strong>{report.current_choghadiya.ruler}</strong> | Quality Score: <strong>{report.current_choghadiya.score}/100</strong>
              </p>
            </div>
          </div>

           {/* Enterprise Suitability Matrix */}
           <div className="card" style={{ padding: "var(--space-5)" }}>
             <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-bright)", marginBottom: "var(--space-4)" }}>
               Enterprise Suitability Checklist
             </h3>
             <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "var(--space-2)" }}>
              {[
                { label: "Business Contracts", ok: report.suitability.business_contract, icon: Briefcase },
                { label: "Financial Investment", ok: report.suitability.financial_investment, icon: DollarSign },
                { label: "Travel & Relocation", ok: report.suitability.travel, icon: Plane },
                { label: "Marriage Ceremonies", ok: report.suitability.marriage, icon: Heart },
                { label: "Real Estate Acquisition", ok: report.suitability.property_purchase, icon: Home },
                { label: "Medical Treatments", ok: report.suitability.medical_treatment, icon: Activity },
              ].map((item) => {
                const Icon = item.icon;
                 return (
                   <div
                     key={item.label}
                     style={{
                       padding: "var(--space-1-5) var(--space-3-5)",
                       borderRadius: "var(--radius-md)",
                       background: item.ok ? "rgba(16,185,129,0.06)" : "rgba(244,63,94,0.06)",
                       border: `var(--border-width) solid ${item.ok ? "rgba(16,185,129,0.2)" : "rgba(244,63,94,0.2)"}`,
                       display: "flex",
                       alignItems: "center",
                       gap: "var(--space-2-5)",
                     }}
                   >
                     <Icon size={18} color={item.ok ? "var(--emerald)" : "var(--rose)"} />
                    <div>
                      <div style={{ fontSize: "var(--type-body)", fontWeight: 600, color: "var(--text-bright)" }}>
                        {item.label}
                      </div>
                       <div style={{ fontSize: "var(--type-micro)", color: item.ok ? "var(--emerald)" : "var(--rose)", fontWeight: 600 }}>
                         {item.ok ? "Favorable" : "Avoid"}
                       </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

           {/* Special Timing Windows & Alerts */}
           <div className="card" style={{ padding: "var(--space-5)" }}>
             <h3 style={{ fontSize: "var(--type-section)", fontWeight: 700, color: "var(--text-bright)", marginBottom: "var(--space-4)" }}>
               Auspicious &amp; Inauspicious Timing Windows
             </h3>
             <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "var(--space-3-5)" }}>
               {/* Abhijit Muhurtha */}
               <div style={{ padding: "var(--space-3-5)", borderRadius: "var(--radius-md)", background: "rgba(229,185,76,0.05)", border: "var(--border-width) solid rgba(229,185,76,0.2)" }}>
                 <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-0-5)" }}>
                    <span style={{ fontWeight: 600, color: "var(--amber)", fontSize: "var(--type-body)" }}>Abhijit Muhurtha</span>
                   {report.abhijit_muhurtha.is_active && <span className="badge badge-emerald">ACTIVE NOW</span>}
                 </div>
                <div style={{ fontSize: "var(--type-small)", color: "var(--text-bright)" }}>
                  {report.abhijit_muhurtha.start_time} - {report.abhijit_muhurtha.end_time}
                </div>
                 <div style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", marginTop: "var(--space-0-5)" }}>
                   {report.abhijit_muhurtha.notes}
                 </div>
              </div>

               {/* Brahma Muhurtha */}
               <div style={{ padding: "var(--space-3-5)", borderRadius: "var(--radius-md)", background: "rgba(56,189,248,0.05)", border: "var(--border-width) solid rgba(56,189,248,0.2)" }}>
                 <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-0-5)" }}>
                    <span style={{ fontWeight: 600, color: "var(--cyan-vivid)", fontSize: "var(--type-body)" }}>Brahma Muhurtha</span>
                   {report.brahma_muhurtha.is_active && <span className="badge badge-cyan">ACTIVE NOW</span>}
                 </div>
                <div style={{ fontSize: "var(--type-small)", color: "var(--text-bright)" }}>
                  {report.brahma_muhurtha.start_time} - {report.brahma_muhurtha.end_time}
                </div>
                 <div style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", marginTop: "var(--space-0-5)" }}>
                   {report.brahma_muhurtha.notes}
                 </div>
              </div>

               {/* Rahu Kalam */}
               <div style={{ padding: "var(--space-3-5)", borderRadius: "var(--radius-md)", background: "rgba(244,63,94,0.05)", border: "var(--border-width) solid rgba(244,63,94,0.2)" }}>
                 <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-0-5)" }}>
                    <span style={{ fontWeight: 600, color: "var(--rose)", fontSize: "var(--type-body)" }}>Rahu Kalam (Avoid)</span>
                   {report.rahu_kalam.is_active && <span className="badge badge-rose">ALERT: ACTIVE</span>}
                 </div>
                <div style={{ fontSize: "var(--type-small)", color: "var(--text-bright)" }}>
                  {report.rahu_kalam.start_time} - {report.rahu_kalam.end_time}
                </div>
                 <div style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", marginTop: "var(--space-0-5)" }}>
                   {report.rahu_kalam.notes}
                 </div>
              </div>

               {/* Yamaganda */}
               <div style={{ padding: "var(--space-3-5)", borderRadius: "var(--radius-md)", background: "var(--bg-subtle)", border: "var(--border-width) solid var(--border-subtle)" }}>
                 <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-0-5)" }}>
                   <span style={{ fontWeight: 600, color: "var(--text-bright)", fontSize: "var(--type-body)" }}>Yamaganda (Avoid)</span>
                   {report.yamaganda.is_active && <span className="badge badge-rose">ACTIVE</span>}
                 </div>
                <div style={{ fontSize: "var(--type-small)", color: "var(--text-bright)" }}>
                  {report.yamaganda.start_time} - {report.yamaganda.end_time}
                </div>
                 <div style={{ fontSize: "var(--type-micro)", color: "var(--text-muted)", marginTop: "var(--space-0-5)" }}>
                   {report.yamaganda.notes}
                 </div>
              </div>
            </div>
          </div>

           {/* Timeline Switcher: Horas vs Choghadiyas */}
           <div className="card" style={{ padding: "var(--space-5)" }}>
             <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-4)" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-bright)" }}>
                Complete Day Timeline
              </h3>
               <div style={{ display: "flex", gap: "var(--space-1-5)" }}>
                 <button
                   onClick={() => setTimelineTab("horas")}
                   className={`badge ${timelineTab === "horas" ? "badge-gold" : "badge-cyan"}`}
                   style={{
                     cursor: "pointer",
                     padding: "var(--space-1-5) var(--space-3-5)",
                     background: timelineTab === "horas" ? "var(--gold-dim)" : "transparent",
                   }}
                >
                  Planetary Horas (24)
                </button>
                 <button
                   onClick={() => setTimelineTab("choghadiyas")}
                   className={`badge ${timelineTab === "choghadiyas" ? "badge-gold" : "badge-cyan"}`}
                   style={{
                     cursor: "pointer",
                     padding: "var(--space-1-5) var(--space-3-5)",
                     background: timelineTab === "choghadiyas" ? "var(--gold-dim)" : "transparent",
                   }}
                >
                  Choghadiya Cycles (16)
                </button>
              </div>
            </div>

             {timelineTab === "horas" && (
               <div style={{ overflowX: "auto" }}>
                 <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                   <thead>
                     <tr style={{ borderBottom: "var(--border-width) solid var(--border-subtle)", textAlign: "left", color: "var(--text-muted)" }}>
                       <th style={{ padding: "var(--space-2) var(--space-3)" }}>#</th>
                       <th style={{ padding: "var(--space-2) var(--space-3)" }}>Time</th>
                       <th style={{ padding: "var(--space-2) var(--space-3)" }}>Ruling Planet</th>
                       <th style={{ padding: "var(--space-2) var(--space-3)" }}>Nature</th>
                       <th style={{ padding: "var(--space-2) var(--space-3)" }}>Recommended Activities</th>
                     </tr>
                   </thead>
                   <tbody>
                     {[...report.day_horas, ...report.night_horas].map((h) => (
                       <tr
                         key={h.hora_index}
                         style={{
                           borderBottom: "var(--border-width) solid var(--border-subtle)",
                           background: h.is_current ? "var(--gold-dim)" : "transparent",
                         }}
                       >
                         <td style={{ padding: "var(--space-2-5) var(--space-3)", fontWeight: 600, color: "var(--text-dim)" }}>
                           {h.hora_index} ({h.period_type})
                         </td>
                          <td style={{ padding: "var(--space-2-5) var(--space-3)", color: h.is_current ? "var(--amber)" : "var(--text-bright)", fontWeight: h.is_current ? 700 : 400 }}>
                           {h.start_time} - {h.end_time} {h.is_current && "(Active)"}
                         </td>
                         <td style={{ padding: "var(--space-2-5) var(--space-3)", fontWeight: 600, color: "var(--text-bright)" }}>
                           {h.ruling_planet}
                         </td>
                         <td style={{ padding: "var(--space-2-5) var(--space-3)" }}>
                           <span className={`badge ${h.nature === "Benefic" ? "badge-emerald" : "badge-rose"}`}>
                             {h.nature}
                           </span>
                         </td>
                         <td style={{ padding: "var(--space-2-5) var(--space-3)", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                           {h.recommended_activities}
                         </td>
                       </tr>
                     ))}
                   </tbody>
                </table>
              </div>
            )}

             {timelineTab === "choghadiyas" && (
               <div style={{ overflowX: "auto" }}>
                 <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                   <thead>
                     <tr style={{ borderBottom: "var(--border-width) solid var(--border-subtle)", textAlign: "left", color: "var(--text-muted)" }}>
                       <th style={{ padding: "var(--space-2) var(--space-3)" }}>#</th>
                       <th style={{ padding: "var(--space-2) var(--space-3)" }}>Time</th>
                       <th style={{ padding: "var(--space-2) var(--space-3)" }}>Choghadiya</th>
                       <th style={{ padding: "var(--space-2) var(--space-3)" }}>Nature</th>
                       <th style={{ padding: "var(--space-2) var(--space-3)" }}>Ruling Planet</th>
                       <th style={{ padding: "var(--space-2) var(--space-3)" }}>Quality Score</th>
                     </tr>
                   </thead>
                   <tbody>
                     {[...report.day_choghadiyas, ...report.night_choghadiyas].map((c, idx) => (
                       <tr
                         key={idx}
                         style={{
                           borderBottom: "var(--border-width) solid var(--border-subtle)",
                           background: c.is_current ? "var(--cyan-dim)" : "transparent",
                         }}
                       >
                         <td style={{ padding: "var(--space-2-5) var(--space-3)", fontWeight: 600, color: "var(--text-dim)" }}>
                           {c.index} ({c.period_type})
                         </td>
                          <td style={{ padding: "var(--space-2-5) var(--space-3)", color: c.is_current ? "var(--cyan-vivid)" : "var(--text-bright)", fontWeight: c.is_current ? 700 : 400 }}>
                           {c.start_time} - {c.end_time} {c.is_current && "(Active)"}
                         </td>
                         <td style={{ padding: "var(--space-2-5) var(--space-3)", fontWeight: 600, color: "var(--text-bright)" }}>
                           {c.name}
                         </td>
                         <td style={{ padding: "var(--space-2-5) var(--space-3)" }}>
                           <span className={`badge ${c.score >= 70 ? "badge-emerald" : "badge-rose"}`}>
                             {c.nature}
                           </span>
                         </td>
                         <td style={{ padding: "var(--space-2-5) var(--space-3)", color: "var(--text-muted)" }}>
                           {c.ruler}
                         </td>
                         <td style={{ padding: "var(--space-2-5) var(--space-3)", fontWeight: 600, color: c.score >= 70 ? "var(--emerald)" : "var(--rose)" }}>
                           {c.score}/100
                         </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
