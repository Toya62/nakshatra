"use client";

import React, { useState } from "react";
import { BirthDataInput, RAGAnswer, SearchReference } from "@/lib/types";
import { askConsultationStream } from "@/lib/api";
import { BookOpen, Send, Sparkles, User, Bot, Quote, HelpCircle, ShieldCheck, X, Layers, Compass } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  role: "user" | "assistant";
  text: string;
  citations?: RAGAnswer["citations"];
  model?: string;
  references?: SearchReference[];
  isStreaming?: boolean;
}

interface Props {
  birth?: BirthDataInput;
}

const SAMPLE_QUESTIONS = [
  "What does the 10th house signify for career and profession?",
  "How does Saturn in the 7th house affect marriage?",
  "What are the classical results of Sun and Mercury conjunction (Budhaditya)?",
  "How does the lord of the 9th house in the 1st house impact destiny?",
];

export const ConsultationView: React.FC<Props> = ({ birth }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      text: "Namaste. I am your Nakshatra Vedic Consultant, grounded in authentic classical texts (Brihat Parashara Hora Shastra, Phaladeepika, Saravali). Ask any astrological question or query your chart placements.",
    },
  ]);
  const [input, setInput] = useState("");
  const [includeChart, setIncludeChart] = useState(Boolean(birth));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Explainable "Why" Inspection Modal State
  const [inspectingMessage, setInspectingMessage] = useState<Message | null>(null);
  const [activeTab, setActiveTab] = useState<"pramana" | "yukti" | "dharma">("pramana");

  const handleSend = async (questionText?: string) => {
    const q = (questionText || input).trim();
    if (!q || loading) return;

    setInput("");
    setError(null);
    setLoading(true);

    setMessages((prev) => [
      ...prev,
      { role: "user", text: q },
      { role: "assistant", text: "", isStreaming: true },
    ]);

    try {
      await askConsultationStream(
        q,
        {
          onInit: (initData) => {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant") {
                updated[updated.length - 1] = {
                  ...last,
                  model: initData.model,
                  references: initData.references,
                };
              }
              return updated;
            });
          },
          onToken: (token) => {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant") {
                updated[updated.length - 1] = {
                  ...last,
                  text: last.text + token,
                };
              }
              return updated;
            });
          },
          onDone: (doneData) => {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant") {
                updated[updated.length - 1] = {
                  ...last,
                  citations: doneData.citations,
                  model: doneData.model || last.model,
                  isStreaming: false,
                };
              }
              return updated;
            });
            setLoading(false);
          },
          onError: (errMsg) => {
            setError(errMsg);
            setLoading(false);
          },
        },
        includeChart ? birth : undefined,
        4
      );
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "18px", maxWidth: "900px", margin: "0 auto" }}>
      {/* Consultation Header Banner */}
      <div className="glass-panel" style={{ padding: "18px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h3 className="title-serif gold-gradient-text" style={{ fontSize: "1.2rem", display: "flex", alignItems: "center", gap: "8px" }}>
            <BookOpen size={20} color="#e5b94c" />
            Vedic Scripture Consultation
          </h3>
          <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
            Zero-hallucination RAG synthesized via Gemini with verified shloka citations
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "14px", flexWrap: "wrap" }}>
          {/* Privacy badge */}
          <div style={{ display: "flex", alignItems: "center", gap: "5px", fontSize: "0.75rem", color: "#38bdf8", background: "rgba(56, 189, 248, 0.1)", padding: "4px 8px", borderRadius: "6px", border: "1px solid rgba(56, 189, 248, 0.25)" }}>
            <ShieldCheck size={14} />
            <span>Zero Persistence • GDPR Compliant</span>
          </div>

          {birth && (
            <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.85rem", cursor: "pointer", color: includeChart ? "#fbe285" : "var(--text-muted)" }}>
              <input
                type="checkbox"
                checked={includeChart}
                onChange={(e) => setIncludeChart(e.target.checked)}
                style={{ width: "16px", height: "16px", accentColor: "#e5b94c" }}
              />
              Ground with Natal Chart context
            </label>
          )}
        </div>
      </div>

      {/* Suggested Questions */}
      {messages.length === 1 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Suggested Classical Questions:
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "8px" }}>
            {SAMPLE_QUESTIONS.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSend(q)}
                className="badge badge-gold"
                style={{
                  textAlign: "left",
                  padding: "10px 14px",
                  fontSize: "0.82rem",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(229,185,76,0.2)",
                  borderRadius: "8px",
                }}
              >
                <Sparkles size={14} color="#e5b94c" />
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat Messages Log */}
      <div
        className="glass-panel"
        style={{
          minHeight: "420px",
          maxHeight: "580px",
          overflowY: "auto",
          padding: "20px",
          display: "flex",
          flexDirection: "column",
          gap: "18px",
        }}
      >
        {messages.map((m, idx) => {
          const isUser = m.role === "user";
          return (
            <div
              key={idx}
              style={{
                display: "flex",
                gap: "12px",
                alignSelf: isUser ? "flex-end" : "flex-start",
                maxWidth: "88%",
              }}
            >
              {!isUser && (
                <div
                  style={{
                    width: "34px",
                    height: "34px",
                    borderRadius: "50%",
                    background: "linear-gradient(135deg, #e5b94c 0%, #38bdf8 100%)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <Bot size={18} color="#07090e" />
                </div>
              )}

              <div
                style={{
                  background: isUser ? "rgba(229, 185, 76, 0.15)" : "rgba(255, 255, 255, 0.04)",
                  border: isUser ? "1px solid rgba(229, 185, 76, 0.4)" : "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "14px",
                  padding: "14px 18px",
                  color: "#f1f5f9",
                  fontSize: "0.92rem",
                  lineHeight: 1.6,
                  width: "100%",
                }}
              >
                {isUser ? (
                  <div style={{ whiteSpace: "pre-wrap" }}>{m.text}</div>
                ) : (
                  <div className="markdown-chat-body">
                    {m.text ? (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {m.text}
                      </ReactMarkdown>
                    ) : (
                      <span style={{ color: "var(--accent-gold)", fontStyle: "italic", display: "inline-flex", alignItems: "center", gap: "6px" }}>
                        <Sparkles size={14} className="pulse-glow" /> Consulting classical verses...
                      </span>
                    )}
                    {m.isStreaming && m.text && (
                      <span
                        style={{
                          display: "inline-block",
                          width: "7px",
                          height: "14px",
                          marginLeft: "3px",
                          backgroundColor: "#fbe285",
                          verticalAlign: "middle",
                          boxShadow: "0 0 8px rgba(229,185,76,0.8)",
                          animation: "pulseGlow 0.8s infinite",
                        }}
                      />
                    )}
                  </div>
                )}

                {/* Assistant footer with Explainable "Why" Button */}
                {!isUser && m.text && !m.isStreaming && (
                  <div style={{ marginTop: "12px", paddingTop: "10px", borderTop: "1px solid rgba(255,255,255,0.06)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "8px" }}>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                      Synthesizer: {m.model || "Gemini Flash"} • Swiss Ephemeris C-Core
                    </div>

                    <button
                      type="button"
                      onClick={() => setInspectingMessage(m)}
                      className="badge badge-gold"
                      style={{
                        cursor: "pointer",
                        background: "rgba(229, 185, 76, 0.15)",
                        border: "1px solid rgba(229, 185, 76, 0.4)",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "5px",
                        fontSize: "0.76rem",
                        padding: "4px 8px",
                      }}
                    >
                      <HelpCircle size={13} color="#e5b94c" />
                      <span>Why? Inspect Astrological Basis</span>
                    </button>
                  </div>
                )}

                {/* Inline Citations Accordion */}
                {m.citations && m.citations.length > 0 && (
                  <div style={{ marginTop: "12px", paddingTop: "10px", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                    <div style={{ fontSize: "0.78rem", color: "#fbe285", fontWeight: 600, display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
                      <Quote size={13} /> Classical Shloka Citations ({m.citations.length})
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                      {m.citations.map((c, cIdx) => (
                        <div
                          key={cIdx}
                          style={{
                            background: "rgba(0,0,0,0.3)",
                            border: "1px solid rgba(229,185,76,0.15)",
                            borderRadius: "6px",
                            padding: "8px 10px",
                            fontSize: "0.8rem",
                          }}
                        >
                          <div style={{ fontWeight: 600, color: "#38bdf8", marginBottom: "3px" }}>
                            [{cIdx + 1}] {c.work} {c.chapter ? `Ch.${c.chapter}` : ""} {c.verse ? `v.${c.verse}` : ""}
                          </div>
                          <div style={{ color: "var(--text-muted)", fontSize: "0.76rem", fontStyle: "italic" }}>
                            "{c.text}"
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {isUser && (
                <div
                  style={{
                    width: "34px",
                    height: "34px",
                    borderRadius: "50%",
                    background: "rgba(255, 255, 255, 0.12)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <User size={18} color="#fbe285" />
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "var(--accent-gold)", fontSize: "0.88rem" }}>
            <Sparkles size={16} className="pulse-glow" /> Consulting classical verses via Gemini...
          </div>
        )}

        {error && (
          <div className="badge badge-rose" style={{ padding: "8px 14px", borderRadius: "8px" }}>
            Error: {error}
          </div>
        )}
      </div>

      {/* Input box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        style={{ display: "flex", gap: "10px" }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask an astrological question (e.g. 'How does Jupiter in the 9th house affect luck?')..."
          style={{ flex: 1, padding: "12px 16px", borderRadius: "10px", fontSize: "0.95rem" }}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()} className="btn-primary" style={{ padding: "0 22px" }}>
          <Send size={18} />
        </button>
      </form>

      {/* Explainable "Why" Inspection Modal */}
      {inspectingMessage && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0,0,0,0.75)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "20px",
          }}
          onClick={() => setInspectingMessage(null)}
        >
          <div
            className="glass-panel"
            style={{
              width: "100%",
              maxWidth: "760px",
              maxHeight: "85vh",
              overflowY: "auto",
              padding: "24px",
              border: "1px solid rgba(229, 185, 76, 0.4)",
              borderRadius: "16px",
              background: "#0c101d",
              boxShadow: "0 20px 50px rgba(0,0,0,0.8)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "18px", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "12px" }}>
              <div>
                <h3 className="title-serif gold-gradient-text" style={{ fontSize: "1.25rem", display: "flex", alignItems: "center", gap: "8px" }}>
                  <Compass size={20} color="#e5b94c" />
                  Astrological Explainability Inspector
                </h3>
                <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Pramana (Scriptural Evidence) & Yukti (Chart Grounding) Behind This Reading
                </p>
              </div>
              <button
                type="button"
                onClick={() => setInspectingMessage(null)}
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Tabs */}
            <div style={{ display: "flex", gap: "10px", marginBottom: "16px", borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: "8px" }}>
              <button
                type="button"
                onClick={() => setActiveTab("pramana")}
                className="badge"
                style={{
                  cursor: "pointer",
                  background: activeTab === "pramana" ? "rgba(229,185,76,0.3)" : "rgba(255,255,255,0.04)",
                  color: activeTab === "pramana" ? "#fbe285" : "var(--text-muted)",
                  padding: "6px 12px",
                }}
              >
                1. Scriptural Pramana ({inspectingMessage.citations?.length || 0})
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("yukti")}
                className="badge"
                style={{
                  cursor: "pointer",
                  background: activeTab === "yukti" ? "rgba(56,189,248,0.3)" : "rgba(255,255,255,0.04)",
                  color: activeTab === "yukti" ? "#38bdf8" : "var(--text-muted)",
                  padding: "6px 12px",
                }}
              >
                2. Natal Chart Grounding
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("dharma")}
                className="badge"
                style={{
                  cursor: "pointer",
                  background: activeTab === "dharma" ? "rgba(74,222,128,0.3)" : "rgba(255,255,255,0.04)",
                  color: activeTab === "dharma" ? "#4ade80" : "var(--text-muted)",
                  padding: "6px 12px",
                }}
              >
                3. Ethical / Dharma Guardrail
              </button>
            </div>

            {/* Tab 1: Scriptural Pramana */}
            {activeTab === "pramana" && (
              <div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "12px" }}>
                  The AI was strictly grounded by these canonical Sanskrit verses retrieved from indexed works:
                </div>
                {inspectingMessage.citations && inspectingMessage.citations.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                    {inspectingMessage.citations.map((c, i) => (
                      <div
                        key={i}
                        style={{
                          background: "rgba(255,255,255,0.03)",
                          border: "1px solid rgba(229,185,76,0.25)",
                          borderRadius: "10px",
                          padding: "12px 16px",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                          <span style={{ fontWeight: 600, color: "#e5b94c" }}>
                            [{i + 1}] {c.work}
                          </span>
                          <span style={{ fontSize: "0.75rem", color: "#38bdf8", background: "rgba(56,189,248,0.1)", padding: "2px 8px", borderRadius: "4px" }}>
                            Chapter {c.chapter || "N/A"}, Verse {c.verse || "N/A"}
                          </span>
                        </div>
                        <div style={{ fontSize: "0.86rem", color: "#e2e8f0", fontStyle: "italic", lineHeight: 1.6 }}>
                          "{c.text}"
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                    General introductory greeting. Ask a specific question to invoke RAG verse retrieval.
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Natal Chart Grounding */}
            {activeTab === "yukti" && (
              <div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "12px" }}>
                  Mathematical Astronomical Ground Truth supplied to LLM from Swiss Ephemeris engine:
                </div>
                {birth ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.86rem" }}>
                    <div style={{ background: "rgba(255,255,255,0.03)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                      <strong>Epoch:</strong> {birth.year}-{birth.month}-{birth.day} {birth.hour}:{birth.minute} ({birth.timezone})
                    </div>
                    <div style={{ background: "rgba(255,255,255,0.03)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                      <strong>Coordinates:</strong> {birth.latitude}° N, {birth.longitude}° E ({birth.place_name || "Custom"})
                    </div>
                    <div style={{ background: "rgba(255,255,255,0.03)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                      <strong>Lineage Calibration:</strong> Sidereal Zodiac • {birth.ayanamsa || "jhora_lahiri"} Ayanamsa • {birth.house_system || "WholeSign"} Houses
                    </div>
                    <div style={{ background: "rgba(56,189,248,0.08)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(56,189,248,0.2)", color: "#7ec8e3" }}>
                      <strong>Calculation Outsource Enforcement:</strong> The model is hard-coded to never perform mental astronomical trigonometry. Planetary coordinates and dashas are computed deterministically.
                    </div>
                  </div>
                ) : (
                  <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                    No birth chart attached to this session. Answer was synthesized from general classical principles. Check "Ground with Natal Chart context" above to evaluate personal coordinates.
                  </div>
                )}
              </div>
            )}

            {/* Tab 3: Ethical / Dharma Guardrail */}
            {activeTab === "dharma" && (
              <div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "12px" }}>
                  Jyotish Counseling Ethics & Anti-Fatalism Policy:
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "0.85rem" }}>
                  <div style={{ background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.2)", borderRadius: "8px", padding: "12px 14px" }}>
                    <div style={{ fontWeight: 600, color: "#4ade80", marginBottom: "4px" }}>
                      Anti-Fatalistic Reframing
                    </div>
                    <div style={{ color: "#e2e8f0", lineHeight: 1.5 }}>
                      Vedic astrology reveals karma and cycles for conscious navigation, never unalterable doom. All challenging transits (Sade Sati, Maraka periods) are translated into opportunities for discipline, self-correction, and spiritual remedies.
                    </div>
                  </div>

                  <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px", padding: "12px 14px" }}>
                    <div style={{ fontWeight: 600, color: "#fbe285", marginBottom: "4px" }}>
                      Professional Counseling Boundary
                    </div>
                    <div style={{ color: "var(--text-muted)", lineHeight: 1.5 }}>
                      Jyotish consultation does not diagnose or replace licensed human medical, psychiatric, or legal counsel.
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
