"use client";

import React, { useState, useRef, useEffect } from "react";
import { BirthDataInput, RAGAnswer, SearchReference, DomainPrediction, getBirthKey } from "@/lib/types";
import { askConsultationStream, fetchPredictions } from "@/lib/api";
import { useLanguage } from "@/context/LanguageContext";
import { BookOpen, Send, Sparkles, User, Bot, Quote, HelpCircle, ShieldCheck, X, Compass, Square, ArrowDown } from "lucide-react";
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
  "What are classical results of Sun and Mercury conjunction (Budhaditya)?",
  "How does lord of 9th house in 1st house impact destiny and luck?",
  "What are the classical remedies for Sade Sati according to Parashara?",
];

const INITIAL_MESSAGE: Message = {
  role: "assistant",
  text: "Namaste. I am your Nakshatra Vedic Consultant, grounded in authentic classical treatises (Brihat Parashara Hora Shastra, Phaladeepika, Saravali). Ask any astrological question or query your chart placements.",
};

export const ConsultationView: React.FC<Props> = ({ birth }) => {
  const { t, lang } = useLanguage();
  const currentChartKey = getBirthKey(birth);
  const initialText = lang === "ne"
    ? "नमस्ते। म तपाईंको नक्षत्र वैदिक ज्योतिष परामर्शदाता हुँ, जो प्रामाणिक शास्त्रीय ग्रन्थहरू (वृहत् पराशर होरा शास्त्र, फलदीपिका, सारावली) मा आधारित छ। आफ्नो कुण्डली वा ज्योतिष सम्बन्धी कुनै पनि जिज्ञासा सोध्नुहोस्।"
    : "Namaste. I am your Nakshatra Vedic Consultant, grounded in authentic classical treatises (Brihat Parashara Hora Shastra, Phaladeepika, Saravali). Ask any astrological question or query your chart placements.";
  const [messages, setMessages] = useState<Message[]>([{ role: "assistant", text: initialText }]);
  const [input, setInput] = useState("");
  const [includeChart, setIncludeChart] = useState(Boolean(birth));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync includeChart when birth changes
  useEffect(() => {
    setIncludeChart(Boolean(birth));
  }, [birth]);

  // Hierarchical Domain Prediction State
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [predictions, setPredictions] = useState<Record<string, DomainPrediction> | null>(null);
  const [predictLoading, setPredictLoading] = useState(false);

  useEffect(() => {
    setSelectedDomain(null);
    if (!birth) {
      setPredictions(null);
      return;
    }
    let cancelled = false;
    setPredictLoading(true);
    fetchPredictions(birth)
      .then((data) => {
        if (!cancelled) setPredictions(data);
      })
      .catch((err) => {
        console.warn("Predictions fetch failed:", err);
      })
      .finally(() => {
        if (!cancelled) setPredictLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [birth]);

  // Explainable "Why" Inspection Modal State
  const [inspectingMessage, setInspectingMessage] = useState<Message | null>(null);
  const [activeTab, setActiveTab] = useState<"pramana" | "yukti" | "dharma">("pramana");

  // Auto-scroll & streaming abort refs
  const threadEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const userScrolledUpRef = useRef(false);
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  // Restore messages from localStorage on client mount or reset if chart changed
  const isHydratedRef = useRef(false);

  useEffect(() => {
    try {
      const savedChartKey = localStorage.getItem("nakshatra_consult_chart_key");
      if (savedChartKey && savedChartKey !== currentChartKey) {
        // Chart changed: reset consultation chat and remove previous messages
        localStorage.removeItem("nakshatra_consultation_messages");
        localStorage.setItem("nakshatra_consult_chart_key", currentChartKey);
        setMessages([INITIAL_MESSAGE]);
        setInput("");
        setError(null);
        setSelectedDomain(null);
      } else {
        localStorage.setItem("nakshatra_consult_chart_key", currentChartKey);
        const saved = localStorage.getItem("nakshatra_consultation_messages");
        if (saved) {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed) && parsed.length > 0) {
            setMessages(parsed.map((m: Message) => ({ ...m, isStreaming: false })));
          }
        }
      }
    } catch {}
    // Delay enabling persistence until state update has rendered
    const timer = setTimeout(() => {
      isHydratedRef.current = true;
    }, 50);
    return () => clearTimeout(timer);
  }, [currentChartKey]);

  // Persist messages to localStorage when streaming finishes
  useEffect(() => {
    if (!isHydratedRef.current) return;
    const isOnlyInitial = messages.length === 1 && messages[0].text === INITIAL_MESSAGE.text;
    const hasStreaming = messages.some((m) => m.isStreaming);
    if (!hasStreaming) {
      if (isOnlyInitial) {
        try {
          localStorage.removeItem("nakshatra_consultation_messages");
        } catch {}
      } else if (messages.length > 0) {
        try {
          localStorage.setItem("nakshatra_consultation_messages", JSON.stringify(messages));
          localStorage.setItem("nakshatra_consult_chart_key", currentChartKey);
        } catch {}
      }
    }
  }, [messages, currentChartKey]);

  const handleClearChat = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
    setMessages([INITIAL_MESSAGE]);
    setInput("");
    setError(null);
    try {
      localStorage.removeItem("nakshatra_consultation_messages");
    } catch {}
  };

  const handleScroll = () => {
    const el = chatContainerRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    const isUp = distanceFromBottom > 60;
    userScrolledUpRef.current = isUp;
    setShowScrollBottom(isUp);
  };

  const scrollToBottom = (force = false) => {
    const el = chatContainerRef.current;
    if (!el) return;
    if (force || !userScrolledUpRef.current) {
      el.scrollTop = el.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom(false);
  }, [messages]);

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
    setMessages((prev) => {
      const updated = [...prev];
      const last = updated[updated.length - 1];
      if (last && last.role === "assistant") {
        updated[updated.length - 1] = {
          ...last,
          isStreaming: false,
          text: last.text ? last.text + "\n\n*[Consultation response stopped by user]*" : "*[Consultation response stopped by user]*",
        };
      }
      return updated;
    });
  };

  const handleSend = async (questionText?: string) => {
    const q = (questionText || input).trim();
    if (!q || loading) return;

    setInput("");
    setError(null);
    setLoading(true);
    userScrolledUpRef.current = false;
    setShowScrollBottom(false);

    setMessages((prev) => [
      ...prev,
      { role: "user", text: q },
      { role: "assistant", text: "", isStreaming: true },
    ]);

    setTimeout(() => scrollToBottom(true), 50);

    const controller = new AbortController();
    abortControllerRef.current = controller;

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
            abortControllerRef.current = null;
          },
          onError: (errMsg) => {
            if (!controller.signal.aborted) {
              setError(errMsg);
            }
            setLoading(false);
            abortControllerRef.current = null;
          },
        },
        includeChart ? birth : undefined,
        4,
        controller.signal,
        lang
      );
    } catch (e: unknown) {
      const err = e as Error;
      if (err.name !== "AbortError" && !controller.signal.aborted) {
        setError(err.message);
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)", maxWidth: "960px", margin: "0 auto", width: "100%", minWidth: 0 }}>
      {/* Consultation Header Banner */}
      <div className="card" style={{ padding: "var(--space-4) var(--space-5)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "var(--space-3)" }}>
        <div>
          <h2 style={{ fontSize: "var(--type-heading)", fontWeight: 700, display: "flex", alignItems: "center", gap: "var(--space-2)", color: "var(--text-high)" }}>
            <BookOpen size={18} color="var(--gold-vivid)" aria-hidden="true" />
            {t.consultation.title}
          </h2>
          <p style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", marginTop: "2px" }}>
            {t.consultation.subtitle}
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", flexWrap: "wrap" }}>
          {/* Privacy badge */}
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-1)", fontSize: "var(--type-micro)", color: "var(--cyan-vivid)", background: "var(--cyan-dim)", padding: "3px 8px", borderRadius: "var(--radius-sm)", border: "1px solid rgba(56, 189, 248, 0.25)" }}>
            <ShieldCheck size={13} aria-hidden="true" />
            <span>{lang === "ne" ? "शून्य भण्डारण • स्मृतिमा मात्र" : "Zero Persistence • In-Memory"}</span>
          </div>

          {messages.length > 1 && (
            <button
              type="button"
              onClick={handleClearChat}
              className="chip"
              style={{ fontSize: "var(--type-micro)" }}
              aria-label="Reset consultation chat history"
            >
              {lang === "ne" ? "नयाँ कुराकानी" : "Reset Chat"}
            </button>
          )}

          {birth && (
            <button
              type="button"
              onClick={() => setIncludeChart(!includeChart)}
              className={`chip${includeChart ? " active" : ""}`}
              aria-pressed={includeChart}
              aria-label="Toggle Natal Chart context grounding"
            >
              <Sparkles size={13} color={includeChart ? "var(--gold-vivid)" : "var(--text-mid)"} aria-hidden="true" />
              <span>{lang === "ne" ? `कुण्डली सन्दर्भ: ${includeChart ? "सक्रिय" : "बन्द"}` : `Chart Context: ${includeChart ? "Active" : "Off"}`}</span>
            </button>
          )}
        </div>
      </div>

      {/* 5-Step Hierarchical Prediction Domain Selector */}
      {birth && (
        <div className="card" style={{ padding: "var(--space-3) var(--space-4)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-2)", flexWrap: "wrap", gap: "var(--space-2)" }}>
            <span style={{ fontSize: "var(--type-micro)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "uppercase", letterSpacing: "0.06em", display: "flex", alignItems: "center", gap: "6px" }}>
              <Compass size={13} aria-hidden="true" />
              {lang === "ne" ? "शास्त्रीय वैदिक फलादेश (स्वीस एफिमरिस आधार)" : "Hierarchical Vedic Predictions (Deterministic Ground Truth)"}
            </span>
            {predictLoading && (
              <span style={{ fontSize: "var(--type-micro)", color: "var(--text-low)" }}>{lang === "ne" ? "योग तथा गोचर गणना गरिँदैछ..." : "Calculating yogas & transits..."}</span>
            )}
          </div>
          <div style={{ display: "flex", gap: "var(--space-2)", overflowX: "auto", paddingBottom: "2px", scrollbarWidth: "thin", maxWidth: "100%", width: "100%", minWidth: 0, WebkitOverflowScrolling: "touch" }}>
            {[
              { id: "all", label: lang === "ne" ? "समग्र सारांश" : "Overview", icon: "🌌" },
              { id: "career", label: lang === "ne" ? "करियर तथा पदप्रतिष्ठा" : "Career & Status", icon: "👑" },
              { id: "relationship", label: lang === "ne" ? "विवाह तथा सम्बन्ध" : "Marriage & Love", icon: "💍" },
              { id: "wealth", label: lang === "ne" ? "धन तथा आर्थिक स्थिति" : "Wealth & Dhana", icon: "💎" },
              { id: "spiritual_dharma", label: lang === "ne" ? "आध्यात्म तथा धर्म" : "Spiritual Dharma", icon: "🪷" },
              { id: "health", label: lang === "ne" ? "आरोग्य तथा आयु" : "Vitality & Ayur", icon: "🌿" },
            ].map((d) => {
              const isActive = selectedDomain === (d.id === "all" ? null : d.id);
              const pred = predictions && d.id !== "all" ? predictions[d.id] : null;
              return (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => setSelectedDomain(d.id === "all" ? null : d.id)}
                  className={`chip${isActive ? " active" : ""}`}
                  style={{
                    fontSize: "var(--type-micro)",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    flexShrink: 0,
                  }}
                >
                  <span>{d.icon}</span>
                  <span>{d.label}</span>
                  {pred && (
                    <span
                      style={{
                        fontSize: "var(--type-micro)",
                        padding: "2px 6px",
                        borderRadius: "8px",
                        fontWeight: 600,
                        background:
                          pred.promise_tier === "Exceptional" || pred.promise_tier === "Favorable"
                            ? "var(--emerald-dim)"
                            : pred.promise_tier === "Mixed"
                            ? "var(--amber-dim)"
                            : "var(--rose-dim)",
                        color:
                          pred.promise_tier === "Exceptional" || pred.promise_tier === "Favorable"
                            ? "var(--emerald)"
                            : pred.promise_tier === "Mixed"
                            ? "var(--amber)"
                            : "var(--rose)",
                      }}
                    >
                      {pred.promise_tier}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Active Domain Detailed Prediction Card */}
          {selectedDomain && predictions && predictions[selectedDomain] && (
            <div
              style={{
                marginTop: "var(--space-3)",
                padding: "var(--space-4)",
                background: "var(--bg-input)",
                border: "1px solid var(--gold-border)",
                borderRadius: "var(--radius-md)",
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-3)",
              }}
            >
              {/* Verdict header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "var(--space-2)" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                    <h3 style={{ fontSize: "var(--type-body)", fontWeight: 700, color: "var(--gold-vivid)", textTransform: "capitalize" }}>
                      {predictions[selectedDomain].domain.replace("_", " ")} {t.consultation.domainVerdict}
                    </h3>
                    <span
                      className="chip"
                      style={{
                        fontSize: "var(--type-micro)",
                        padding: "2px 8px",
                        fontWeight: 700,
                        borderColor: "var(--gold-vivid)",
                        color: "var(--gold-vivid)",
                      }}
                    >
                      {t.consultation.tier}: {predictions[selectedDomain].promise_tier}
                    </span>
                  </div>
                  <p style={{ fontSize: "var(--type-small)", color: "var(--text-high)", marginTop: "4px", fontStyle: "italic", borderLeft: "2px solid var(--gold-vivid)", paddingLeft: "8px" }}>
                    &ldquo;{predictions[selectedDomain].key_verdict}&rdquo;
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => handleSend(
                    lang === "ne"
                      ? `${t.consultation.askDomainPrompt} ${predictions[selectedDomain].domain.replace("_", " ")} योग र दशा समयबारे फलादेश गर्नुहोस्।`
                      : `Based on Maharishi Parashara's classical rules, synthesize my ${predictions[selectedDomain].domain.replace("_", " ")} promise and operating dasha timing.`
                  )}
                  className="chip active"
                  style={{ fontSize: "var(--type-micro)", flexShrink: 0 }}
                >
                  <Sparkles size={12} color="var(--gold-vivid)" aria-hidden="true" />
                  <span>{lang === "ne" ? "यसबारे AI ज्योतिषीसँग परामर्श गर्नुहोस्" : "Consult AI Astrologer on this"}</span>
                </button>
              </div>

              {/* 5-Step breakdown grid */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                  gap: "var(--space-3)",
                  fontSize: "var(--type-micro)",
                }}
              >
                <div style={{ background: "var(--bg-subtle)", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                  <strong style={{ color: "var(--cyan-vivid)", display: "block", marginBottom: "2px" }}>{t.consultation.natalPromise}</strong>
                  <span style={{ color: "var(--text-mid)" }}>{predictions[selectedDomain].promise_summary}</span>
                </div>
                <div style={{ background: "var(--bg-subtle)", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                  <strong style={{ color: "var(--cyan-vivid)", display: "block", marginBottom: "2px" }}>{t.consultation.vargaConfirmation}</strong>
                  <span style={{ color: "var(--text-mid)" }}>{predictions[selectedDomain].varga_confirmation}</span>
                </div>
                <div style={{ background: "var(--bg-subtle)", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                  <strong style={{ color: "var(--gold-vivid)", display: "block", marginBottom: "2px" }}>{t.consultation.dashaTrigger}</strong>
                  <span style={{ color: "var(--text-mid)" }}>{predictions[selectedDomain].dasha_timing}</span>
                </div>
                <div style={{ background: "var(--bg-subtle)", padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                  <strong style={{ color: "var(--gold-vivid)", display: "block", marginBottom: "2px" }}>{t.consultation.gocharTransits}</strong>
                  <span style={{ color: "var(--text-mid)" }}>{predictions[selectedDomain].active_transits.join(" ")}</span>
                </div>
              </div>

              {/* Citations & Remedies strip */}
              <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "var(--space-2)", borderTop: "1px solid var(--border-subtle)", paddingTop: "var(--space-2)", fontSize: "var(--type-micro)" }}>
                <div>
                  <span style={{ color: "var(--text-low)", textTransform: "uppercase", fontWeight: 600 }}>{t.consultation.scripturalAuthorities} </span>
                  <span style={{ color: "var(--text-mid)" }}>{predictions[selectedDomain].classical_citations.join(" • ")}</span>
                </div>
                <div>
                  <span style={{ color: "var(--text-low)", textTransform: "uppercase", fontWeight: 600 }}>{t.consultation.recommendedRemedies} </span>
                  <span style={{ color: "var(--text-mid)" }}>{predictions[selectedDomain].remedies.join(" • ")}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Suggested Questions Carousel / Horizontal Scroll */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-2)",
          overflowX: "auto",
          paddingBottom: "var(--space-1)",
          scrollbarWidth: "thin",
          maxWidth: "100%",
          width: "100%",
          minWidth: 0,
          WebkitOverflowScrolling: "touch",
        }}
        tabIndex={0}
        aria-label="Suggested classical questions"
      >
        <span style={{ fontSize: "var(--type-micro)", color: "var(--text-low)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap", display: "flex", alignItems: "center", gap: "4px" }}>
          <Sparkles size={11} color="var(--gold-vivid)" aria-hidden="true" /> {t.consultation.sampleQueriesTitle}:
        </span>
        {(t.consultation.samples && t.consultation.samples.length > 0 ? t.consultation.samples : SAMPLE_QUESTIONS).map((q, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleSend(q)}
            disabled={loading}
            className="chip"
            style={{ fontSize: "var(--type-micro)", flexShrink: 0 }}
            aria-label={`Ask question: ${q}`}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Chat Messages Log */}
      <div
        ref={chatContainerRef}
        onScroll={handleScroll}
        className="card"
        style={{
          position: "relative",
          minHeight: "280px",
          maxHeight: "min(60vh, 620px)",
          overflowY: "auto",
          padding: "var(--space-5)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-4)",
        }}
        role="log"
        aria-live="polite"
        aria-label="Consultation conversation"
      >
        {messages.map((m, idx) => {
          const isUser = m.role === "user";
          return (
            <div
              key={idx}
              style={{
                display: "flex",
                gap: "var(--space-3)",
                alignSelf: isUser ? "flex-end" : "flex-start",
                maxWidth: isUser ? "85%" : "92%",
              }}
            >
              {!isUser && (
                <div
                  style={{
                    width: "32px",
                    height: "32px",
                    borderRadius: "50%",
                    background: "linear-gradient(135deg, var(--gold-vivid) 0%, var(--cyan-vivid) 100%)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    boxShadow: "0 2px 10px rgba(0,0,0,0.4)",
                  }}
                  aria-hidden="true"
                >
                  <Bot size={17} color="var(--bg-base)" />
                </div>
              )}

              <div
                style={{
                  background: isUser ? "var(--gold-dim)" : "var(--bg-subtle)",
                  border: isUser ? "1px solid var(--gold-border)" : "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-4)",
                  color: "var(--text-high)",
                  fontSize: "var(--type-body)",
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
                      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
                        <div className="skeleton" style={{ height: "14px", width: "70%" }} />
                        <div className="skeleton" style={{ height: "14px", width: "90%" }} />
                        <div className="skeleton" style={{ height: "14px", width: "40%" }} />
                      </div>
                    )}
                    {m.isStreaming && m.text && (
                      <span
                        style={{
                          display: "inline-block",
                          width: "6px",
                          height: "14px",
                          marginLeft: "4px",
                          backgroundColor: "var(--gold-bright)",
                          verticalAlign: "middle",
                          boxShadow: "0 0 8px rgba(229,185,76,0.8)",
                          animation: "shimmer 1.5s infinite linear",
                        }}
                        aria-hidden="true"
                      />
                    )}
                  </div>
                )}

                {/* Assistant footer with Explainable "Why" Button */}
                {!isUser && m.text && !m.isStreaming && (
                  <div
                    style={{
                      marginTop: "var(--space-3)",
                      paddingTop: "var(--space-2)",
                      borderTop: "1px solid var(--border-subtle)",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      flexWrap: "wrap",
                      gap: "var(--space-2)",
                    }}
                  >
                    <div style={{ fontSize: "var(--type-micro)", color: "var(--text-low)", fontFamily: "var(--font-mono)" }}>
                      Synthesizer: {m.model || "Gemini"} • Swiss Ephemeris C-Core
                    </div>

                    <button
                      type="button"
                      onClick={() => {
                        setInspectingMessage(m);
                        setActiveTab("pramana");
                      }}
                      className="chip active"
                      style={{
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "var(--space-1)",
                        fontSize: "var(--type-micro)",
                        padding: "3px 9px",
                      }}
                      aria-label="Inspect scriptural pramana and astrological basis"
                    >
                      <HelpCircle size={12} color="var(--gold-vivid)" aria-hidden="true" />
                      <span>Why? Inspect Astrological Basis</span>
                    </button>
                  </div>
                )}

                {/* Inline Citations Accordion */}
                {m.citations && m.citations.length > 0 && (
                  <div style={{ marginTop: "var(--space-3)", paddingTop: "var(--space-2)", borderTop: "1px solid var(--border-subtle)" }}>
                    <div style={{ fontSize: "var(--type-label)", color: "var(--gold-bright)", fontWeight: 600, display: "flex", alignItems: "center", gap: "var(--space-1)", marginBottom: "var(--space-2)" }}>
                      <Quote size={12} aria-hidden="true" /> Classical Shloka Citations ({m.citations.length})
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
                      {m.citations.map((c, cIdx) => (
                        <div
                          key={cIdx}
                          style={{
                            background: "var(--bg-subtle)",
                            border: "1px solid var(--gold-border)",
                            borderRadius: "var(--radius-sm)",
                            padding: "var(--space-2) var(--space-3)",
                            fontSize: "var(--type-label)",
                          }}
                        >
                          <div style={{ fontWeight: 600, color: "var(--cyan-vivid)", marginBottom: "2px" }}>
                            [{cIdx + 1}] {c.work} {c.chapter ? `Ch.${c.chapter}` : ""} {c.verse ? `v.${c.verse}` : ""}
                          </div>
                          <div style={{ color: "var(--text-mid)", fontSize: "var(--type-micro)", fontStyle: "italic" }}>
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
                    width: "32px",
                    height: "32px",
                    borderRadius: "50%",
                    background: "var(--gold-dim)",
                    border: "1px solid var(--gold-border)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                  aria-hidden="true"
                >
                  <User size={16} color="var(--gold-bright)" />
                </div>
              )}
            </div>
          );
        })}

        {loading && !messages[messages.length - 1]?.text && (
          <div style={{ display: "flex", gap: "var(--space-3)", maxWidth: "80%" }}>
            <div className="skeleton" style={{ width: 32, height: 32, borderRadius: "50%", flexShrink: 0 }} />
            <div className="card skeleton" style={{ width: 320, height: 72, padding: "var(--space-4)" }} />
          </div>
        )}

        {error && (
          <div className="card" style={{ padding: "var(--space-3)", color: "var(--rose)", borderColor: "var(--rose)" }} role="alert">
            Error: {error}
          </div>
        )}

        {/* Anchor for auto-scroll */}
        <div ref={threadEndRef} />

        {/* Floating Scroll to Bottom pill when user scrolled up */}
        {showScrollBottom && (
          <button
            type="button"
            onClick={() => {
              userScrolledUpRef.current = false;
              setShowScrollBottom(false);
              scrollToBottom(true);
            }}
            className="chip"
            style={{
              position: "sticky",
              bottom: "var(--space-2)",
              alignSelf: "center",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 14px",
              borderRadius: "9999px",
              background: "var(--bg-elevated)",
              border: "1px solid var(--gold-border)",
              color: "var(--gold-vivid)",
              boxShadow: "0 4px 14px rgba(0,0,0,0.35)",
              fontSize: "var(--type-micro)",
              fontWeight: 600,
              zIndex: 10,
              cursor: "pointer",
            }}
            aria-label="Scroll to bottom"
          >
            <ArrowDown size={13} aria-hidden="true" />
            <span>{lang === "ne" ? "तल जानुहोस्" : "Scroll to bottom"}</span>
          </button>
        )}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        style={{ display: "flex", gap: "var(--space-2)", width: "100%", maxWidth: "100%", minWidth: 0 }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t.consultation.inputPlaceholder}
          style={{ flex: 1, padding: "12px 16px", borderRadius: "var(--radius-md)", fontSize: "var(--type-body)", minWidth: 0 }}
          disabled={loading}
          aria-label="Astrological consultation question"
        />
        {loading ? (
          <button
            type="button"
            onClick={handleStop}
            className="btn-danger"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "0 18px",
              height: "44px",
              borderRadius: "var(--radius-md)",
              background: "rgba(239, 68, 68, 0.15)",
              border: "1px solid rgba(239, 68, 68, 0.4)",
              color: "var(--rose, #f87171)",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "var(--type-small)",
              flexShrink: 0,
            }}
            aria-label={t.consultation.stopBtn}
            title={t.consultation.stopBtn}
          >
            <Square size={13} fill="currentColor" aria-hidden="true" />
            <span>{t.consultation.stopBtn}</span>
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim()}
            className="btn-primary"
            style={{ height: "44px", padding: "0 18px", flexShrink: 0 }}
            aria-label={t.consultation.sendBtn}
          >
            <Send size={16} aria-hidden="true" />
          </button>
        )}
      </form>

      {/* Explainable "Why" Inspection Modal / Bottom Sheet */}
      {inspectingMessage && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "var(--bg-overlay)",
            backdropFilter: "blur(8px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 300,
            padding: "var(--space-4)",
          }}
          onClick={() => setInspectingMessage(null)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="inspector-modal-title"
        >
          <div
            className="card"
            style={{
              width: "100%",
              maxWidth: "760px",
              maxHeight: "85vh",
              overflowY: "auto",
              padding: "var(--space-6)",
              border: "1px solid var(--gold-border)",
              boxShadow: "var(--card-shadow-hover)",
              background: "var(--bg-elevated, var(--bg-card))",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "var(--space-4)", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "var(--space-3)" }}>
              <div>
                <h3 id="inspector-modal-title" style={{ fontSize: "var(--type-heading)", fontWeight: 700, display: "flex", alignItems: "center", gap: "var(--space-2)", color: "var(--text-high)" }}>
                  <Compass size={18} color="var(--gold-vivid)" aria-hidden="true" />
                  Astrological Explainability Inspector
                </h3>
                <p style={{ fontSize: "var(--type-micro)", color: "var(--text-mid)", marginTop: "2px" }}>
                  Pramana (Scriptural Evidence) &amp; Yukti (Chart Grounding) Behind This Reading
                </p>
              </div>
              <button
                type="button"
                onClick={() => setInspectingMessage(null)}
                style={{ background: "transparent", border: "none", color: "var(--text-mid)", cursor: "pointer", padding: "4px" }}
                aria-label="Close explainability inspector"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Tabs */}
            <div style={{ display: "flex", gap: "var(--space-2)", marginBottom: "var(--space-4)", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "var(--space-2)", flexWrap: "wrap" }} role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === "pramana"}
                onClick={() => setActiveTab("pramana")}
                className={`chip${activeTab === "pramana" ? " active" : ""}`}
              >
                1. Scriptural Pramana ({inspectingMessage.citations?.length || 0})
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === "yukti"}
                onClick={() => setActiveTab("yukti")}
                className={`chip${activeTab === "yukti" ? " active" : ""}`}
              >
                2. Natal Chart Grounding
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === "dharma"}
                onClick={() => setActiveTab("dharma")}
                className={`chip${activeTab === "dharma" ? " active" : ""}`}
              >
                3. Ethical / Dharma Guardrail
              </button>
            </div>

            {/* Tab 1: Scriptural Pramana */}
            {activeTab === "pramana" && (
              <div role="tabpanel">
                <div style={{ fontSize: "var(--type-label)", color: "var(--text-mid)", marginBottom: "var(--space-3)" }}>
                  The AI was strictly grounded by these canonical Sanskrit verses retrieved from indexed works:
                </div>
                {inspectingMessage.citations && inspectingMessage.citations.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
                    {inspectingMessage.citations.map((c, i) => (
                      <div
                        key={i}
                        style={{
                          background: "var(--bg-subtle)",
                          border: "1px solid var(--gold-border)",
                          borderRadius: "var(--radius-sm)",
                          padding: "var(--space-3) var(--space-4)",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-1)", flexWrap: "wrap", gap: "var(--space-2)" }}>
                          <span style={{ fontWeight: 600, color: "var(--gold-vivid)", fontSize: "var(--type-body)" }}>
                            [{i + 1}] {c.work}
                          </span>
                          <span className="badge badge-cyan">
                            Chapter {c.chapter || "N/A"}, Verse {c.verse || "N/A"}
                          </span>
                        </div>
                        <div style={{ fontSize: "var(--type-label)", color: "var(--text-high)", fontStyle: "italic", lineHeight: 1.6 }}>
                          "{c.text}"
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: "var(--text-mid)", fontSize: "var(--type-body)" }}>
                    General introductory greeting. Ask a specific question to invoke RAG verse retrieval.
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Natal Chart Grounding */}
            {activeTab === "yukti" && (
              <div role="tabpanel">
                <div style={{ fontSize: "var(--type-label)", color: "var(--text-mid)", marginBottom: "var(--space-3)" }}>
                  Mathematical Astronomical Ground Truth supplied to LLM from Swiss Ephemeris engine:
                </div>
                {birth ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)", fontSize: "var(--type-label)" }}>
                    <div style={{ background: "var(--bg-subtle)", padding: "var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                      <strong style={{ color: "var(--gold-bright)" }}>Epoch:</strong> {birth.year}-{birth.month}-{birth.day} {birth.hour}:{birth.minute} ({birth.timezone})
                    </div>
                    <div style={{ background: "var(--bg-subtle)", padding: "var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                      <strong style={{ color: "var(--gold-bright)" }}>Coordinates:</strong> {birth.latitude}° N, {birth.longitude}° E ({birth.place_name || "Custom"})
                    </div>
                    <div style={{ background: "var(--bg-subtle)", padding: "var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
                      <strong style={{ color: "var(--gold-bright)" }}>Lineage Calibration:</strong> Sidereal Zodiac • {birth.ayanamsa || "jhora_lahiri"} Ayanamsa • {birth.house_system || "WholeSign"} Houses
                    </div>
                    <div style={{ background: "var(--cyan-dim)", padding: "var(--space-3)", borderRadius: "var(--radius-sm)", border: "1px solid rgba(56,189,248,0.2)", color: "var(--cyan-vivid)" }}>
                      <strong>Calculation Outsource Enforcement:</strong> The model is hard-coded to never perform mental astronomical trigonometry. Planetary coordinates and dashas are computed deterministically.
                    </div>
                  </div>
                ) : (
                  <div style={{ color: "var(--text-mid)", fontSize: "var(--type-body)" }}>
                    No birth chart attached to this session. Answer was synthesized from general classical principles. Toggle "Chart Context: Active" above to evaluate personal coordinates.
                  </div>
                )}
              </div>
            )}

            {/* Tab 3: Ethical / Dharma Guardrail */}
            {activeTab === "dharma" && (
              <div role="tabpanel">
                <div style={{ fontSize: "var(--type-label)", color: "var(--text-mid)", marginBottom: "var(--space-3)" }}>
                  Jyotish Counseling Ethics &amp; Anti-Fatalism Policy:
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)", fontSize: "var(--type-body)" }}>
                  <div style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.25)", borderRadius: "var(--radius-sm)", padding: "var(--space-3) var(--space-4)" }}>
                    <div style={{ fontWeight: 600, color: "var(--emerald)", marginBottom: "var(--space-1)" }}>
                      Anti-Fatalistic Reframing
                    </div>
                    <div style={{ color: "var(--text-high)", lineHeight: 1.5, fontSize: "var(--type-label)" }}>
                      Vedic astrology reveals karma and cycles for conscious navigation, never unalterable doom. All challenging transits (Sade Sati, Maraka periods) are translated into opportunities for discipline, self-correction, and spiritual remedies.
                    </div>
                  </div>

                  <div style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)", padding: "var(--space-3) var(--space-4)" }}>
                    <div style={{ fontWeight: 600, color: "var(--gold-bright)", marginBottom: "var(--space-1)" }}>
                      Professional Counseling Boundary
                    </div>
                    <div style={{ color: "var(--text-mid)", lineHeight: 1.5, fontSize: "var(--type-label)" }}>
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
