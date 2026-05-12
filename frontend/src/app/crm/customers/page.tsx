"use client";

import { useEffect, useState } from "react";
import { getCustomers } from "@/lib/api";
import { Users, User, Clock } from "lucide-react";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<any[]>([]);

  useEffect(() => {
    const token = localStorage.getItem("token") || "";
    getCustomers(token).then(setCustomers).catch(() => {});
  }, []);

  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <h1 style={{ fontSize: "24px", fontWeight: 700, marginBottom: "4px" }}>Clientes</h1>
        <p style={{ color: "#94a3b8", fontSize: "14px" }}>Todos os clientes atendidos pelo chatbot</p>
      </div>

      <div style={{
        borderRadius: "14px", overflow: "hidden",
        background: "rgba(26,26,46,0.8)", border: "1px solid rgba(139,92,246,0.15)"
      }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid rgba(139,92,246,0.1)" }}>
              {["Cliente", "Contato", "Idade", "Preferências", "Primeiro Contato"].map((h) => (
                <th key={h} style={{ padding: "12px 16px", textAlign: "left", fontSize: "12px", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.id} style={{ borderBottom: "1px solid rgba(139,92,246,0.05)" }}>
                <td style={{ padding: "14px 16px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div style={{
                      width: "32px", height: "32px", borderRadius: "8px",
                      background: "linear-gradient(135deg, #3b82f6, #2563eb)",
                      display: "flex", alignItems: "center", justifyContent: "center"
                    }}>
                      <User size={14} />
                    </div>
                    <span style={{ fontWeight: 500, fontSize: "14px" }}>{c.name || "Anônimo"}</span>
                  </div>
                </td>
                <td style={{ padding: "14px 16px", fontSize: "13px", color: "#94a3b8" }}>
                  {c.phone || c.email || "-"}
                </td>
                <td style={{ padding: "14px 16px", fontSize: "13px", color: "#94a3b8" }}>
                  {c.age || "-"}
                </td>
                <td style={{ padding: "14px 16px", fontSize: "12px", color: "#94a3b8" }}>
                  {c.preferences ? JSON.stringify(c.preferences).slice(0, 60) : "-"}
                </td>
                <td style={{ padding: "14px 16px", fontSize: "12px", color: "#64748b" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <Clock size={12} />
                    {new Date(c.first_contact).toLocaleDateString("pt-BR")}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {customers.length === 0 && (
          <div style={{ padding: "40px", textAlign: "center", color: "#64748b" }}>
            <Users size={32} style={{ marginBottom: "8px", opacity: 0.5 }} />
            <p>Nenhum cliente ainda. Eles aparecerão aqui após interagirem com o chat.</p>
          </div>
        )}
      </div>
    </div>
  );
}
