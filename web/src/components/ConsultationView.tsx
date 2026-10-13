"use client";

import React, { useState } from "react";
import { BirthDataInput, RAGAnswer, SearchReference } from "@/lib/types";
import { askConsultationStream } from "@/lib/api";
import { BookOpen, Send, Sparkles, User, Bot, Quote } from "lucide-react";
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
            Zero-hallucination RAG synthesized via Gemini 3.8 Flash with verified shloka citations
          </p>
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

      {/* Suggested Questions Pills */}
      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
        {SAMPLE_QUESTIONS.map((sq, i) => (
          <button
            key={i}
            onClick={() => handleSend(sq)}
            className="badge badge-gold"
            style={{ cursor: "pointer", padding: "6px 12px", background: "rgba(229,185,76,0.08)", fontSize: "0.8rem", textAlign: "left" }}
          >
            {sq}
          </button>
        ))}
      </div>

      {/* Chat Messages Log */}
      <div className="glass-panel" style={{ padding: "24px", minHeight: "420px", display: "flex", flexDirection: "column", gap: "20px" }}>
        {messages.map((m, idx) => {
          const isUser = m.role === "user";
          return (
            <div
              key={idx}
              style={{
                display: "flex",
                gap: "14px",
                alignItems: "flex-start",
                alignSelf: isUser ? "flex-end" : "flex-start",
                maxWidth: "85%",
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

                {/* Model tag */}
                {m.model && (
                  <div style={{ marginTop: "8px", fontSize: "0.72rem", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                    Synthesizer: {m.model}
                  </div>
                )}

                {/* Classical Citations Accordion */}
                {m.citations && m.citations.length > 0 && (
                  <div style={{ marginTop: "14px", paddingTop: "12px", borderTop: "1px solid rgba(255,255,255,0.08)" }}>
                    <div style={{ fontSize: "0.8rem", color: "#fbe285", fontWeight: 600, display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
                      <Quote size={14} /> Classical References Cited ({m.citations.length})
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
    </div>
  );
};
