"use client";

import { useEffect, useState } from "react";
import { getCatalogs, getProducts, getCustomers, getConversations } from "@/lib/api";
import { ShoppingBag, Package, Users, MessageCircle, TrendingUp } from "lucide-react";

export default function CRMDashboard() {
  const [stats, setStats] = useState({ catalogs: 0, products: 0, customers: 0, conversations: 0 });

  useEffect(() => {
    const token = localStorage.getItem("token") || "";
    Promise.all([
      getCatalogs(token).catch(() => []),
      getProducts(token).catch(() => []),
      getCustomers(token).catch(() => []),
      getConversations().catch(() => []),
    ]).then(([cats, prods, custs, convs]) => {
      setStats({
        catalogs: cats.length,
        products: prods.length,
        customers: custs.length,
        conversations: convs.length,
      });
    });
  }, []);

  const cards = [
    { icon: <ShoppingBag size={22} />, label: "Catálogos", value: stats.catalogs, color: "#8b5cf6" },
    { icon: <Package size={22} />, label: "Produtos", value: stats.products, color: "#3b82f6" },
    { icon: <Users size={22} />, label: "Clientes", value: stats.customers, color: "#10b981" },
    { icon: <MessageCircle size={22} />, label: "Conversas", value: stats.conversations, color: "#f59e0b" },
  ];

  return (
    <div>
      <div style={{ marginBottom: "32px" }}>
        <h1 style={{ fontSize: "28px", fontWeight: 700, marginBottom: "4px" }}>
          Dashboard
        </h1>
        <p style={{ color: "#94a3b8", fontSize: "14px" }}>
          Visão geral da Moda Estrela do Agreste
        </p>
      </div>

      <div style={{
        display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: "16px", marginBottom: "32px"
      }}>
        {cards.map((card, i) => (
          <div key={i} className="animate-fade-in" style={{
            padding: "24px", borderRadius: "16px",
            background: "rgba(26,26,46,0.8)", border: "1px solid rgba(139,92,246,0.15)",
            display: "flex", alignItems: "center", gap: "16px"
          }}>
            <div style={{
              width: "48px", height: "48px", borderRadius: "12px",
              background: `${card.color}20`,
              display: "flex", alignItems: "center", justifyContent: "center",
              color: card.color
            }}>
              {card.icon}
            </div>
            <div>
              <div style={{ fontSize: "28px", fontWeight: 700 }}>{card.value}</div>
              <div style={{ fontSize: "13px", color: "#94a3b8" }}>{card.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{
        padding: "32px", borderRadius: "16px",
        background: "rgba(26,26,46,0.8)", border: "1px solid rgba(139,92,246,0.15)",
        textAlign: "center"
      }}>
        <TrendingUp size={32} style={{ color: "#8b5cf6", marginBottom: "12px" }} />
        <h3 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "8px" }}>
          Painel CRM em funcionamento
        </h3>
        <p style={{ color: "#94a3b8", fontSize: "14px", maxWidth: "500px", margin: "0 auto" }}>
          Use o menu lateral para gerenciar catálogos, produtos, estoque, clientes e
          acompanhar as conversas do chatbot. O Kanban mostra o funil de vendas em tempo real.
        </p>
      </div>
    </div>
  );
}
