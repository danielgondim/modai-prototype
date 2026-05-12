"use client";

import Link from "next/link";
import { MessageCircle, BarChart3, ShoppingBag, Users, Sparkles, Shield } from "lucide-react";

export default function HomePage() {
  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(135deg, #0f0f17 0%, #1a1a2e 50%, #16213e 100%)" }}>
      {/* Header */}
      <header style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "20px 40px", borderBottom: "1px solid rgba(139,92,246,0.15)"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{
            width: "40px", height: "40px", borderRadius: "12px",
            background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "20px"
          }}>✨</div>
          <span style={{ fontSize: "24px", fontWeight: 700, background: "linear-gradient(90deg, #8b5cf6, #a78bfa)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            ModAI
          </span>
        </div>
        <div style={{ display: "flex", gap: "12px" }}>
          <Link href="/chat" style={{
            padding: "10px 24px", borderRadius: "10px", background: "transparent",
            border: "1px solid rgba(139,92,246,0.4)", color: "#a78bfa",
            textDecoration: "none", fontWeight: 500, fontSize: "14px",
            transition: "all 0.2s"
          }}>
            Testar Chat
          </Link>
          <Link href="/login" style={{
            padding: "10px 24px", borderRadius: "10px",
            background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
            color: "white", textDecoration: "none", fontWeight: 500, fontSize: "14px",
            transition: "all 0.2s"
          }}>
            Entrar no CRM
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section style={{
        textAlign: "center", padding: "100px 40px 60px",
        maxWidth: "900px", margin: "0 auto"
      }}>
        <div className="animate-fade-in" style={{
          display: "inline-flex", alignItems: "center", gap: "8px",
          padding: "6px 16px", borderRadius: "20px",
          background: "rgba(139,92,246,0.15)", border: "1px solid rgba(139,92,246,0.3)",
          fontSize: "13px", color: "#a78bfa", marginBottom: "24px"
        }}>
          <Sparkles size={14} /> Protótipo de Validação
        </div>
        <h1 className="animate-slide-up" style={{
          fontSize: "clamp(36px, 5vw, 64px)", fontWeight: 700,
          lineHeight: 1.1, marginBottom: "24px"
        }}>
          Vendedor virtual com{" "}
          <span style={{ background: "linear-gradient(90deg, #8b5cf6, #ec4899)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            Inteligência Artificial
          </span>
        </h1>
        <p className="animate-slide-up" style={{
          fontSize: "18px", color: "#94a3b8", maxWidth: "600px",
          margin: "0 auto 40px", lineHeight: 1.6
        }}>
          Chatbot inteligente para lojas de confecção do polo têxtil do Agreste Pernambucano.
          Atendimento humanizado, 24/7, com controle total de custos.
        </p>
        <div className="animate-slide-up" style={{ display: "flex", gap: "16px", justifyContent: "center" }}>
          <Link href="/chat" style={{
            padding: "14px 32px", borderRadius: "12px",
            background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
            color: "white", textDecoration: "none", fontWeight: 600, fontSize: "16px",
            boxShadow: "0 4px 20px rgba(139,92,246,0.4)",
            display: "flex", alignItems: "center", gap: "8px"
          }}>
            <MessageCircle size={18} /> Experimentar o Chat
          </Link>
        </div>
      </section>

      {/* Features */}
      <section style={{
        display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
        gap: "20px", padding: "40px", maxWidth: "1200px", margin: "0 auto"
      }}>
        {[
          { icon: <MessageCircle size={24} />, title: "Chat Inteligente", desc: "Bot que entende o cliente e vende como um atendente real, com empatia e conhecimento do catálogo.", color: "#8b5cf6" },
          { icon: <ShoppingBag size={24} />, title: "Catálogo & Estoque", desc: "Gerenciamento completo de catálogos, produtos e estoque em tempo real, integrado ao bot.", color: "#3b82f6" },
          { icon: <Users size={24} />, title: "Kanban de Clientes", desc: "Visualize cada cliente no funil de vendas. Movimentação automática baseada na conversa.", color: "#10b981" },
          { icon: <BarChart3 size={24} />, title: "Controle de Custos", desc: "Roteamento inteligente de modelos, cache semântico e limites de tokens para economizar até 85%.", color: "#f59e0b" },
          { icon: <Shield size={24} />, title: "Human-in-the-Loop", desc: "Quando o limite de tokens é atingido, o lojista assume a conversa sem o cliente perceber.", color: "#ef4444" },
          { icon: <Sparkles size={24} />, title: "Multi-Modelo", desc: "Suporte a GPT-4o, GPT-4o-mini e Gemini 2.5 Flash. Roteamento automático por complexidade.", color: "#ec4899" },
        ].map((f, i) => (
          <div key={i} className="animate-fade-in" style={{
            padding: "28px", borderRadius: "16px",
            background: "rgba(26,26,46,0.8)", border: "1px solid rgba(139,92,246,0.15)",
            backdropFilter: "blur(10px)",
            transition: "all 0.3s", cursor: "default",
            animationDelay: `${i * 0.1}s`
          }}>
            <div style={{
              width: "44px", height: "44px", borderRadius: "10px",
              background: `${f.color}20`, display: "flex",
              alignItems: "center", justifyContent: "center",
              color: f.color, marginBottom: "16px"
            }}>
              {f.icon}
            </div>
            <h3 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "8px" }}>{f.title}</h3>
            <p style={{ fontSize: "14px", color: "#94a3b8", lineHeight: 1.6 }}>{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Footer */}
      <footer style={{
        textAlign: "center", padding: "40px",
        color: "#64748b", fontSize: "13px",
        borderTop: "1px solid rgba(139,92,246,0.1)", marginTop: "40px"
      }}>
        ModAI © 2026 — Protótipo de Validação
      </footer>
    </div>
  );
}
