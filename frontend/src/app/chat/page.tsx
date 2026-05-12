"use client";

import { useState, useRef, useEffect } from "react";
import { sendMessage } from "@/lib/api";
import { Send, Bot, User, Loader2, Plus, ArrowLeft, Zap, Brain } from "lucide-react";
import Link from "next/link";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  model_used?: string | null;
  from_cache?: boolean;
  tokens_used?: number;
  timestamp: Date;
}

interface ChatSession {
  id: string;
  conversationId?: string;
  customerId?: string;
  messages: ChatMessage[];
  stage: string;
  customerName?: string;
}

export default function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionIdx, setActiveSessionIdx] = useState<number>(-1);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showDebug, setShowDebug] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeSession = activeSessionIdx >= 0 ? sessions[activeSessionIdx] : null;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeSession?.messages]);

  const createNewSession = () => {
    const newSession: ChatSession = {
      id: crypto.randomUUID(),
      messages: [],
      stage: "greeting",
    };
    setSessions((prev) => [...prev, newSession]);
    setActiveSessionIdx(sessions.length);
  };

  const handleSend = async () => {
    if (!input.trim() || !activeSession || isLoading) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    // Update session with user message
    setSessions((prev) =>
      prev.map((s, i) =>
        i === activeSessionIdx ? { ...s, messages: [...s.messages, userMsg] } : s
      )
    );
    setInput("");
    setIsLoading(true);

    try {
      const response = await sendMessage(
        userMsg.content,
        activeSession.conversationId,
        activeSession.customerName
      );

      const aiMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.message,
        model_used: response.model_used,
        from_cache: response.from_cache,
        tokens_used: response.tokens_used,
        timestamp: new Date(),
      };

      setSessions((prev) =>
        prev.map((s, i) =>
          i === activeSessionIdx
            ? {
                ...s,
                messages: [...s.messages, aiMsg],
                conversationId: response.conversation_id,
                customerId: response.customer_id,
                stage: response.stage,
              }
            : s
        )
      );
    } catch (error: any) {
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Erro: ${error.message}. Verifique se o backend está rodando.`,
        timestamp: new Date(),
      };
      setSessions((prev) =>
        prev.map((s, i) =>
          i === activeSessionIdx ? { ...s, messages: [...s.messages, errorMsg] } : s
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const stageLabels: Record<string, { label: string; color: string }> = {
    greeting: { label: "Saudação", color: "#8b5cf6" },
    browsing: { label: "Navegando", color: "#f59e0b" },
    stock_check: { label: "Verificando Estoque", color: "#3b82f6" },
    ordering: { label: "Fazendo Pedido", color: "#6366f1" },
    checkout: { label: "Finalizando", color: "#10b981" },
    support: { label: "Suporte", color: "#ef4444" },
    closed: { label: "Encerrado", color: "#6b7280" },
  };

  const renderMessage = (content: string) => {
    const linkRegex = /\[(.*?)\]\((.*?)\)/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = linkRegex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        parts.push(content.substring(lastIndex, match.index));
      }
      const text = match[1];
      const url = match[2];
      parts.push(
        <a key={match.index} href={url} target="_blank" rel="noreferrer" style={{
          display: "inline-flex", alignItems: "center", gap: "4px", color: "#a78bfa",
          textDecoration: "underline", fontWeight: 500, padding: "2px 4px",
          background: "rgba(139,92,246,0.1)", borderRadius: "4px"
        }}>
          {text}
        </a>
      );
      lastIndex = linkRegex.lastIndex;
    }

    if (lastIndex < content.length) {
      parts.push(content.substring(lastIndex));
    }

    return parts.length > 0 ? parts : content;
  };

  return (
    <div style={{ display: "flex", height: "100vh", background: "#0f0f17" }}>
      {/* Sidebar */}
      <div style={{
        width: "280px", background: "#1a1a2e", borderRight: "1px solid rgba(139,92,246,0.15)",
        display: "flex", flexDirection: "column", flexShrink: 0
      }}>
        {/* Sidebar Header */}
        <div style={{ padding: "20px", borderBottom: "1px solid rgba(139,92,246,0.1)" }}>
          <Link href="/" style={{
            display: "flex", alignItems: "center", gap: "8px",
            textDecoration: "none", color: "#94a3b8", fontSize: "13px", marginBottom: "16px"
          }}>
            <ArrowLeft size={14} /> Voltar
          </Link>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
            <div style={{
              width: "36px", height: "36px", borderRadius: "10px",
              background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px"
            }}>✨</div>
            <span style={{ fontSize: "18px", fontWeight: 700, color: "#f1f5f9" }}>ModAI Chat</span>
          </div>
          <button
            onClick={createNewSession}
            style={{
              width: "100%", padding: "10px", borderRadius: "10px",
              background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
              border: "none", color: "white", fontWeight: 500, fontSize: "14px",
              cursor: "pointer", display: "flex", alignItems: "center",
              justifyContent: "center", gap: "8px",
              transition: "all 0.2s"
            }}
          >
            <Plus size={16} /> Nova Conversa
          </button>
        </div>

        {/* Session List */}
        <div style={{ flex: 1, overflow: "auto", padding: "8px" }}>
          {sessions.map((session, idx) => (
            <button
              key={session.id}
              onClick={() => setActiveSessionIdx(idx)}
              style={{
                width: "100%", padding: "12px", borderRadius: "10px",
                background: idx === activeSessionIdx ? "rgba(139,92,246,0.15)" : "transparent",
                border: idx === activeSessionIdx ? "1px solid rgba(139,92,246,0.3)" : "1px solid transparent",
                color: "#f1f5f9", textAlign: "left", cursor: "pointer",
                marginBottom: "4px", transition: "all 0.2s"
              }}
            >
              <div style={{ fontSize: "14px", fontWeight: 500, marginBottom: "4px" }}>
                {session.customerName || `Cliente ${idx + 1}`}
              </div>
              <div style={{ fontSize: "12px", color: "#64748b" }}>
                {session.messages.length > 0
                  ? session.messages[session.messages.length - 1].content.slice(0, 40) + "..."
                  : "Nova conversa"
                }
              </div>
            </button>
          ))}
          {sessions.length === 0 && (
            <p style={{ textAlign: "center", color: "#64748b", fontSize: "13px", padding: "20px" }}>
              Clique em &quot;Nova Conversa&quot; para começar
            </p>
          )}
        </div>

        {/* Debug toggle */}
        <div style={{ padding: "12px", borderTop: "1px solid rgba(139,92,246,0.1)" }}>
          <button
            onClick={() => setShowDebug(!showDebug)}
            style={{
              width: "100%", padding: "8px", borderRadius: "8px",
              background: showDebug ? "rgba(139,92,246,0.15)" : "transparent",
              border: "1px solid rgba(139,92,246,0.2)",
              color: "#94a3b8", fontSize: "12px", cursor: "pointer",
              display: "flex", alignItems: "center", gap: "6px", justifyContent: "center"
            }}
          >
            <Brain size={14} /> {showDebug ? "Ocultar" : "Mostrar"} Debug IA
          </button>
        </div>
      </div>

      {/* Chat Area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {activeSession ? (
          <>
            {/* Chat Header */}
            <div style={{
              padding: "16px 24px", borderBottom: "1px solid rgba(139,92,246,0.1)",
              display: "flex", alignItems: "center", justifyContent: "space-between"
            }}>
              <div>
                <h2 style={{ fontSize: "16px", fontWeight: 600, margin: 0 }}>
                  Moda Estrela do Agreste
                </h2>
                <p style={{ fontSize: "12px", color: "#64748b", margin: "2px 0 0" }}>
                  Atendimento virtual com IA
                </p>
              </div>
              {activeSession.stage && stageLabels[activeSession.stage] && (
                <span style={{
                  padding: "4px 12px", borderRadius: "12px", fontSize: "12px", fontWeight: 500,
                  background: `${stageLabels[activeSession.stage].color}20`,
                  color: stageLabels[activeSession.stage].color,
                  border: `1px solid ${stageLabels[activeSession.stage].color}40`
                }}>
                  {stageLabels[activeSession.stage].label}
                </span>
              )}
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflow: "auto", padding: "24px" }}>
              {activeSession.messages.length === 0 && (
                <div style={{ textAlign: "center", padding: "60px 20px" }}>
                  <div style={{
                    width: "64px", height: "64px", borderRadius: "16px",
                    background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    margin: "0 auto 16px", fontSize: "28px"
                  }}>👋</div>
                  <h3 style={{ fontSize: "20px", fontWeight: 600, marginBottom: "8px" }}>
                    Bem-vindo à Moda Estrela!
                  </h3>
                  <p style={{ color: "#94a3b8", fontSize: "14px" }}>
                    Digite uma mensagem para começar. Eu sou a ModAI e vou te ajudar!
                  </p>
                </div>
              )}

              {activeSession.messages.map((msg) => (
                <div
                  key={msg.id}
                  className="animate-fade-in"
                  style={{
                    display: "flex", gap: "12px", marginBottom: "16px",
                    flexDirection: msg.role === "user" ? "row-reverse" : "row",
                  }}
                >
                  {/* Avatar */}
                  <div style={{
                    width: "32px", height: "32px", borderRadius: "8px", flexShrink: 0,
                    background: msg.role === "user"
                      ? "linear-gradient(135deg, #3b82f6, #2563eb)"
                      : "linear-gradient(135deg, #8b5cf6, #6366f1)",
                    display: "flex", alignItems: "center", justifyContent: "center"
                  }}>
                    {msg.role === "user" ? <User size={16} /> : <Bot size={16} />}
                  </div>

                  {/* Bubble */}
                  <div style={{ maxWidth: "70%" }}>
                    <div style={{
                      padding: "12px 16px", borderRadius: "14px",
                      background: msg.role === "user"
                        ? "linear-gradient(135deg, #3b82f6, #2563eb)"
                        : "#1e2a4a",
                      fontSize: "14px", lineHeight: 1.6,
                      borderTopRightRadius: msg.role === "user" ? "4px" : "14px",
                      borderTopLeftRadius: msg.role === "user" ? "14px" : "4px",
                      whiteSpace: "pre-wrap",
                    }}>
                      {renderMessage(msg.content)}
                    </div>

                    {/* Debug info */}
                    {showDebug && msg.role === "assistant" && (
                      <div style={{
                        display: "flex", gap: "8px", marginTop: "4px", flexWrap: "wrap"
                      }}>
                        {msg.model_used && (
                          <span style={{
                            fontSize: "10px", padding: "2px 6px", borderRadius: "4px",
                            background: "rgba(139,92,246,0.15)", color: "#a78bfa"
                          }}>
                            <Zap size={10} style={{ display: "inline", verticalAlign: "middle" }} /> {msg.model_used}
                          </span>
                        )}
                        {msg.from_cache && (
                          <span style={{
                            fontSize: "10px", padding: "2px 6px", borderRadius: "4px",
                            background: "rgba(16,185,129,0.15)", color: "#10b981"
                          }}>
                            cache hit
                          </span>
                        )}
                        {msg.tokens_used !== undefined && msg.tokens_used > 0 && (
                          <span style={{
                            fontSize: "10px", padding: "2px 6px", borderRadius: "4px",
                            background: "rgba(245,158,11,0.15)", color: "#f59e0b"
                          }}>
                            {msg.tokens_used} tokens
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="animate-fade-in" style={{ display: "flex", gap: "12px", marginBottom: "16px" }}>
                  <div style={{
                    width: "32px", height: "32px", borderRadius: "8px",
                    background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
                    display: "flex", alignItems: "center", justifyContent: "center"
                  }}>
                    <Bot size={16} />
                  </div>
                  <div style={{
                    padding: "12px 16px", borderRadius: "14px", borderTopLeftRadius: "4px",
                    background: "#1e2a4a", display: "flex", alignItems: "center", gap: "4px"
                  }}>
                    <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#8b5cf6", animation: "typing 1.4s ease-in-out infinite" }} />
                    <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#8b5cf6", animation: "typing 1.4s ease-in-out 0.2s infinite" }} />
                    <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#8b5cf6", animation: "typing 1.4s ease-in-out 0.4s infinite" }} />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div style={{
              padding: "16px 24px", borderTop: "1px solid rgba(139,92,246,0.1)",
              display: "flex", gap: "12px"
            }}>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                placeholder="Digite sua mensagem..."
                style={{
                  flex: 1, padding: "12px 16px", borderRadius: "12px",
                  background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.2)",
                  color: "#f1f5f9", fontSize: "14px", outline: "none",
                  transition: "border-color 0.2s"
                }}
                disabled={isLoading}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                style={{
                  padding: "12px 20px", borderRadius: "12px",
                  background: input.trim()
                    ? "linear-gradient(135deg, #8b5cf6, #6366f1)"
                    : "#1e2a4a",
                  border: "none", color: "white", cursor: input.trim() ? "pointer" : "default",
                  display: "flex", alignItems: "center", gap: "6px",
                  transition: "all 0.2s", opacity: input.trim() ? 1 : 0.5
                }}
              >
                {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
              </button>
            </div>
          </>
        ) : (
          /* No session selected */
          <div style={{
            flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
            flexDirection: "column", gap: "16px"
          }}>
            <div style={{
              width: "80px", height: "80px", borderRadius: "20px",
              background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "36px", boxShadow: "0 8px 30px rgba(139,92,246,0.3)"
            }}>💬</div>
            <h2 style={{ fontSize: "22px", fontWeight: 600 }}>Protótipo ModAI</h2>
            <p style={{ color: "#94a3b8", fontSize: "14px" }}>
              Crie uma nova conversa para simular um atendimento
            </p>
            <button
              onClick={createNewSession}
              style={{
                padding: "12px 28px", borderRadius: "12px",
                background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
                border: "none", color: "white", fontWeight: 500, fontSize: "14px",
                cursor: "pointer", display: "flex", alignItems: "center", gap: "8px"
              }}
            >
              <Plus size={16} /> Nova Conversa
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
