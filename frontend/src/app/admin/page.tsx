"use client";

import { useEffect, useState } from "react";
import { getTokenUsage, getTokenLimits, updateTokenLimit } from "@/lib/api";
import { BarChart3, DollarSign, Cpu, Clock } from "lucide-react";

export default function AdminTokensPage() {
  const [usage, setUsage] = useState<any[]>([]);
  const [limits, setLimits] = useState<any[]>([]);
  const [days, setDays] = useState(30);
  const [editLimit, setEditLimit] = useState<any>(null);

  const token = typeof window !== "undefined" ? localStorage.getItem("token") || "" : "";

  const load = async () => {
    try {
      const [u, l] = await Promise.all([
        getTokenUsage(token, days),
        getTokenLimits(token),
      ]);
      setUsage(u);
      setLimits(l);
    } catch {}
  };

  useEffect(() => { load(); }, [days]);

  const handleUpdateLimit = async () => {
    if (!editLimit) return;
    try {
      await updateTokenLimit(editLimit.id, {
        max_tokens_per_chat: editLimit.max_tokens_per_chat,
        window_hours: editLimit.window_hours,
      }, token);
      setEditLimit(null);
      load();
    } catch {}
  };

  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <h1 style={{ fontSize: "24px", fontWeight: 700, marginBottom: "4px" }}>
          Uso de Tokens por Loja
        </h1>
        <p style={{ color: "#94a3b8", fontSize: "14px" }}>
          Monitore o consumo de tokens de cada cliente da plataforma
        </p>
      </div>

      {/* Period selector */}
      <div style={{ display: "flex", gap: "8px", marginBottom: "24px" }}>
        {[7, 14, 30, 90].map((d) => (
          <button key={d} onClick={() => setDays(d)} style={{
            padding: "8px 16px", borderRadius: "8px",
            background: days === d ? "rgba(239,68,68,0.2)" : "rgba(26,26,46,0.8)",
            border: days === d ? "1px solid rgba(239,68,68,0.4)" : "1px solid rgba(139,92,246,0.1)",
            color: days === d ? "#fca5a5" : "#94a3b8",
            fontSize: "13px", cursor: "pointer"
          }}>
            {d} dias
          </button>
        ))}
      </div>

      {/* Usage table */}
      <div style={{
        borderRadius: "14px", overflow: "hidden", marginBottom: "32px",
        background: "rgba(26,26,46,0.8)", border: "1px solid rgba(139,92,246,0.15)"
      }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid rgba(139,92,246,0.1)" }}>
              {["Loja", "Tokens Input", "Tokens Output", "Total", "Custo Est. (USD)"].map((h) => (
                <th key={h} style={{ padding: "12px 16px", textAlign: "left", fontSize: "12px", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {usage.map((u) => (
              <tr key={u.tenant_id} style={{ borderBottom: "1px solid rgba(139,92,246,0.05)" }}>
                <td style={{ padding: "14px 16px", fontWeight: 500, fontSize: "14px" }}>{u.tenant_name}</td>
                <td style={{ padding: "14px 16px", fontSize: "13px", color: "#94a3b8" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <Cpu size={12} /> {u.total_tokens_input.toLocaleString()}
                  </div>
                </td>
                <td style={{ padding: "14px 16px", fontSize: "13px", color: "#94a3b8" }}>
                  {u.total_tokens_output.toLocaleString()}
                </td>
                <td style={{ padding: "14px 16px", fontSize: "14px", fontWeight: 600, color: "#f59e0b" }}>
                  {(u.total_tokens_input + u.total_tokens_output).toLocaleString()}
                </td>
                <td style={{ padding: "14px 16px", fontSize: "14px", fontWeight: 600, color: "#10b981" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <DollarSign size={14} /> {u.total_cost_usd.toFixed(4)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {usage.length === 0 && (
          <div style={{ padding: "40px", textAlign: "center", color: "#64748b" }}>
            <BarChart3 size={32} style={{ marginBottom: "8px", opacity: 0.5 }} />
            <p>Nenhum uso registrado no período</p>
          </div>
        )}
      </div>

      {/* Limits */}
      <h2 style={{ fontSize: "20px", fontWeight: 600, marginBottom: "16px" }}>Limites de Tokens</h2>
      <div style={{
        borderRadius: "14px", overflow: "hidden",
        background: "rgba(26,26,46,0.8)", border: "1px solid rgba(139,92,246,0.15)"
      }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid rgba(139,92,246,0.1)" }}>
              {["Loja (Tenant)", "Máx Tokens/Chat", "Janela (horas)", "Ativo", "Ações"].map((h) => (
                <th key={h} style={{ padding: "12px 16px", textAlign: "left", fontSize: "12px", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {limits.map((l) => (
              <tr key={l.id} style={{ borderBottom: "1px solid rgba(139,92,246,0.05)" }}>
                <td style={{ padding: "14px 16px", fontSize: "13px" }}>{l.tenant_id.slice(0, 8)}...</td>
                <td style={{ padding: "14px 16px", fontSize: "14px", fontWeight: 600 }}>
                  {editLimit?.id === l.id ? (
                    <input type="number" value={editLimit.max_tokens_per_chat}
                      onChange={(e) => setEditLimit({ ...editLimit, max_tokens_per_chat: parseInt(e.target.value) })}
                      style={{ width: "100px", padding: "6px 8px", borderRadius: "6px", background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.2)", color: "#f1f5f9", fontSize: "13px" }}
                    />
                  ) : l.max_tokens_per_chat.toLocaleString()}
                </td>
                <td style={{ padding: "14px 16px", fontSize: "14px" }}>
                  {editLimit?.id === l.id ? (
                    <input type="number" value={editLimit.window_hours}
                      onChange={(e) => setEditLimit({ ...editLimit, window_hours: parseInt(e.target.value) })}
                      style={{ width: "80px", padding: "6px 8px", borderRadius: "6px", background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.2)", color: "#f1f5f9", fontSize: "13px" }}
                    />
                  ) : (
                    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                      <Clock size={12} /> {l.window_hours}h ({(l.window_hours / 24).toFixed(0)} dias)
                    </div>
                  )}
                </td>
                <td style={{ padding: "14px 16px" }}>
                  <span style={{
                    padding: "2px 8px", borderRadius: "4px", fontSize: "12px",
                    background: l.is_active ? "rgba(16,185,129,0.15)" : "rgba(239,68,68,0.15)",
                    color: l.is_active ? "#10b981" : "#ef4444"
                  }}>
                    {l.is_active ? "Ativo" : "Inativo"}
                  </span>
                </td>
                <td style={{ padding: "14px 16px" }}>
                  {editLimit?.id === l.id ? (
                    <div style={{ display: "flex", gap: "6px" }}>
                      <button onClick={handleUpdateLimit} style={{
                        padding: "6px 12px", borderRadius: "6px", background: "#10b981",
                        border: "none", color: "white", fontSize: "12px", cursor: "pointer"
                      }}>Salvar</button>
                      <button onClick={() => setEditLimit(null)} style={{
                        padding: "6px 12px", borderRadius: "6px", background: "transparent",
                        border: "1px solid rgba(239,68,68,0.3)", color: "#fca5a5",
                        fontSize: "12px", cursor: "pointer"
                      }}>Cancelar</button>
                    </div>
                  ) : (
                    <button onClick={() => setEditLimit({ ...l })} style={{
                      padding: "6px 12px", borderRadius: "6px",
                      background: "rgba(139,92,246,0.15)", border: "1px solid rgba(139,92,246,0.3)",
                      color: "#a78bfa", fontSize: "12px", cursor: "pointer"
                    }}>Editar</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
