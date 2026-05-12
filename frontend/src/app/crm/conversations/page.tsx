"use client";

import { useEffect, useState } from "react";
import { getConversations, getMessages } from "@/lib/api";
import { MessageCircle, Bot, User, Clock, Eye } from "lucide-react";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedConv, setSelectedConv] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);

  useEffect(() => {
    getConversations().then(setConversations).catch(() => {});
  }, []);

  const viewMessages = async (conv: any) => {
    setSelectedConv(conv);
    try {
      const msgs = await getMessages(conv.id);
      setMessages(msgs);
    } catch {}
  };

  const stageLabels: Record<string, { label: string; color: string }> = {
    greeting: { label: "Saudação", color: "#8b5cf6" },
    browsing: { label: "Navegando", color: "#f59e0b" },
    ordering: { label: "Pedindo", color: "#6366f1" },
    checkout: { label: "Comprando", color: "#10b981" },
    support: { label: "Suporte", color: "#ef4444" },
    closed: { label: "Encerrado", color: "#6b7280" },
  };

  return (
    <div style={{ display: "flex", gap: "20px", height: "calc(100vh - 80px)" }}>
      {/* List */}
      <div style={{
        width: "380px", flexShrink: 0, overflow: "auto",
        borderRadius: "14px", background: "rgba(26,26,46,0.8)",
        border: "1px solid rgba(139,92,246,0.15)"
      }}>
        <div style={{ padding: "16px", borderBottom: "1px solid rgba(139,92,246,0.1)" }}>
          <h2 style={{ fontSize: "18px", fontWeight: 600 }}>Conversas</h2>
          <p style={{ fontSize: "12px", color: "#64748b" }}>{conversations.length} conversas</p>
        </div>
        {conversations.map((conv) => (
          <button key={conv.id} onClick={() => viewMessages(conv)} style={{
            width: "100%", padding: "14px 16px", textAlign: "left", cursor: "pointer",
            background: selectedConv?.id === conv.id ? "rgba(139,92,246,0.1)" : "transparent",
            border: "none", borderBottom: "1px solid rgba(139,92,246,0.05)",
            color: "#f1f5f9", display: "flex", justifyContent: "space-between", alignItems: "center"
          }}>
            <div>
              <div style={{ fontSize: "14px", fontWeight: 500, marginBottom: "4px" }}>
                Conversa #{conv.id.slice(0, 8)}
              </div>
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                {stageLabels[conv.current_stage] && (
                  <span style={{
                    fontSize: "10px", padding: "2px 6px", borderRadius: "4px",
                    background: `${stageLabels[conv.current_stage].color}20`,
                    color: stageLabels[conv.current_stage].color,
                  }}>
                    {stageLabels[conv.current_stage].label}
                  </span>
                )}
                <span style={{ fontSize: "11px", color: "#64748b" }}>
                  {conv.total_tokens_used} tokens
                </span>
              </div>
            </div>
            <Eye size={16} style={{ color: "#64748b" }} />
          </button>
        ))}
      </div>

      {/* Messages view */}
      <div style={{
        flex: 1, borderRadius: "14px",
        background: "rgba(26,26,46,0.8)", border: "1px solid rgba(139,92,246,0.15)",
        display: "flex", flexDirection: "column"
      }}>
        {selectedConv ? (
          <>
            <div style={{ padding: "16px", borderBottom: "1px solid rgba(139,92,246,0.1)" }}>
              <div style={{ fontSize: "16px", fontWeight: 600 }}>
                Conversa #{selectedConv.id.slice(0, 8)}
              </div>
              <div style={{ fontSize: "12px", color: "#64748b" }}>
                Status: {selectedConv.status} | Tokens: {selectedConv.total_tokens_used}
              </div>
            </div>
            <div style={{ flex: 1, overflow: "auto", padding: "16px" }}>
              {messages.map((msg) => (
                <div key={msg.id} style={{
                  display: "flex", gap: "10px", marginBottom: "12px",
                  flexDirection: msg.role === "user" ? "row-reverse" : "row"
                }}>
                  <div style={{
                    width: "28px", height: "28px", borderRadius: "8px", flexShrink: 0,
                    background: msg.role === "user"
                      ? "linear-gradient(135deg, #3b82f6, #2563eb)"
                      : "linear-gradient(135deg, #8b5cf6, #6366f1)",
                    display: "flex", alignItems: "center", justifyContent: "center"
                  }}>
                    {msg.role === "user" ? <User size={12} /> : <Bot size={12} />}
                  </div>
                  <div style={{
                    maxWidth: "65%", padding: "10px 14px", borderRadius: "12px",
                    background: msg.role === "user" ? "#2563eb" : "#1e2a4a",
                    fontSize: "13px", lineHeight: 1.5, whiteSpace: "pre-wrap"
                  }}>
                    {msg.content}
                    {msg.model_used && (
                      <div style={{ fontSize: "10px", color: "#64748b", marginTop: "4px" }}>
                        {msg.model_used} | {msg.tokens_input + msg.tokens_output} tokens
                        {msg.from_cache && " | cache"}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
            <MessageCircle size={32} style={{ color: "#64748b", marginBottom: "8px" }} />
            <p style={{ color: "#64748b", fontSize: "14px" }}>Selecione uma conversa</p>
          </div>
        )}
      </div>
    </div>
  );
}
