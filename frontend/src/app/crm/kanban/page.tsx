"use client";

import { useEffect, useState } from "react";
import { getKanbanColumns, moveKanbanCard, createKanbanColumn } from "@/lib/api";
import { Plus, GripVertical, User } from "lucide-react";

export default function KanbanPage() {
  const [columns, setColumns] = useState<any[]>([]);
  const [newColName, setNewColName] = useState("");
  const [draggedCard, setDraggedCard] = useState<any>(null);

  const token = typeof window !== "undefined" ? localStorage.getItem("token") || "" : "";

  const load = async () => {
    try {
      const data = await getKanbanColumns(token);
      setColumns(data);
    } catch {}
  };

  useEffect(() => { load(); }, []);

  const handleDragStart = (e: React.DragEvent, card: any) => {
    setDraggedCard(card);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };

  const handleDrop = async (e: React.DragEvent, columnId: string) => {
    e.preventDefault();
    if (!draggedCard || draggedCard.column_id === columnId) return;
    try {
      await moveKanbanCard(draggedCard.id, { column_id: columnId, position: 0 }, token);
      load();
    } catch {}
    setDraggedCard(null);
  };

  const handleAddColumn = async () => {
    if (!newColName.trim()) return;
    try {
      await createKanbanColumn({ name: newColName, color: "#8b5cf6" }, token);
      setNewColName("");
      load();
    } catch {}
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 style={{ fontSize: "24px", fontWeight: 700, marginBottom: "4px" }}>Kanban de Clientes</h1>
          <p style={{ color: "#94a3b8", fontSize: "14px" }}>Acompanhe o funil de vendas dos clientes</p>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <input
            value={newColName} onChange={(e) => setNewColName(e.target.value)}
            placeholder="Nome da coluna..."
            onKeyDown={(e) => e.key === "Enter" && handleAddColumn()}
            style={{
              padding: "8px 12px", borderRadius: "8px",
              background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.2)",
              color: "#f1f5f9", fontSize: "13px", outline: "none", width: "180px"
            }}
          />
          <button onClick={handleAddColumn} style={{
            padding: "8px 16px", borderRadius: "8px",
            background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
            border: "none", color: "white", fontSize: "13px", cursor: "pointer",
            display: "flex", alignItems: "center", gap: "4px"
          }}>
            <Plus size={14} /> Coluna
          </button>
        </div>
      </div>

      <div style={{
        display: "flex", gap: "16px", overflowX: "auto",
        paddingBottom: "16px", minHeight: "calc(100vh - 180px)"
      }}>
        {columns.map((col) => (
          <div
            key={col.id}
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, col.id)}
            style={{
              minWidth: "280px", maxWidth: "280px",
              background: "rgba(26,26,46,0.6)", borderRadius: "14px",
              border: "1px solid rgba(139,92,246,0.1)",
              display: "flex", flexDirection: "column"
            }}
          >
            {/* Column Header */}
            <div style={{
              padding: "14px 16px", borderBottom: "1px solid rgba(139,92,246,0.1)",
              display: "flex", alignItems: "center", justifyContent: "space-between"
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <div style={{
                  width: "8px", height: "8px", borderRadius: "50%",
                  background: col.color || "#8b5cf6"
                }} />
                <span style={{ fontSize: "14px", fontWeight: 600 }}>{col.name}</span>
              </div>
              <span style={{
                fontSize: "12px", padding: "2px 8px", borderRadius: "8px",
                background: "rgba(139,92,246,0.15)", color: "#a78bfa"
              }}>
                {col.cards?.length || 0}
              </span>
            </div>

            {/* Cards */}
            <div style={{ flex: 1, padding: "8px", overflow: "auto" }}>
              {col.cards?.map((card: any) => (
                <div
                  key={card.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, card)}
                  className="animate-fade-in"
                  style={{
                    padding: "12px", borderRadius: "10px",
                    background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.1)",
                    marginBottom: "8px", cursor: "grab",
                    transition: "all 0.2s"
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <GripVertical size={14} style={{ color: "#64748b" }} />
                    <div style={{
                      width: "28px", height: "28px", borderRadius: "8px",
                      background: "linear-gradient(135deg, #3b82f6, #2563eb)",
                      display: "flex", alignItems: "center", justifyContent: "center"
                    }}>
                      <User size={14} />
                    </div>
                    <div>
                      <div style={{ fontSize: "13px", fontWeight: 500 }}>
                        {card.customer?.name || "Cliente anônimo"}
                      </div>
                      <div style={{ fontSize: "11px", color: "#64748b" }}>
                        {card.customer?.phone || card.customer?.email || "Sem contato"}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              {(!col.cards || col.cards.length === 0) && (
                <div style={{
                  padding: "20px", textAlign: "center",
                  color: "#64748b", fontSize: "12px",
                  border: "2px dashed rgba(139,92,246,0.1)", borderRadius: "10px"
                }}>
                  Arraste clientes aqui
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
