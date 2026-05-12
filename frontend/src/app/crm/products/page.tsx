"use client";

import { useEffect, useState } from "react";
import { getProducts, getCatalogs, createProduct, getStock, updateStockItem, createStockItem } from "@/lib/api";
import { Plus, Package, Boxes } from "lucide-react";

export default function ProductsPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [catalogs, setCatalogs] = useState<any[]>([]);
  const [selectedCatalog, setSelectedCatalog] = useState<string>("");
  const [showForm, setShowForm] = useState(false);
  const [showStock, setShowStock] = useState<string | null>(null);
  const [stock, setStock] = useState<any[]>([]);
  const [form, setForm] = useState({ name: "", description: "", price: "", catalog_id: "" });

  const token = typeof window !== "undefined" ? localStorage.getItem("token") || "" : "";

  const loadProducts = async () => {
    try {
      const data = await getProducts(token, selectedCatalog || undefined);
      setProducts(data);
    } catch {}
  };

  useEffect(() => {
    getCatalogs(token).then(setCatalogs).catch(() => {});
  }, []);

  useEffect(() => { loadProducts(); }, [selectedCatalog]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createProduct({
        ...form,
        price: parseFloat(form.price),
      }, token);
      setForm({ name: "", description: "", price: "", catalog_id: "" });
      setShowForm(false);
      loadProducts();
    } catch {}
  };

  const loadStock = async (productId: string) => {
    try {
      const data = await getStock(productId, token);
      setStock(data);
      setShowStock(productId);
    } catch {}
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 style={{ fontSize: "24px", fontWeight: 700, marginBottom: "4px" }}>Produtos</h1>
          <p style={{ color: "#94a3b8", fontSize: "14px" }}>Gerencie os produtos e estoque</p>
        </div>
        <div style={{ display: "flex", gap: "12px" }}>
          <select
            value={selectedCatalog}
            onChange={(e) => setSelectedCatalog(e.target.value)}
            style={{
              padding: "10px 14px", borderRadius: "10px",
              background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.2)",
              color: "#f1f5f9", fontSize: "14px"
            }}
          >
            <option value="">Todos os catálogos</option>
            {catalogs.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <button onClick={() => setShowForm(!showForm)} style={{
            padding: "10px 20px", borderRadius: "10px",
            background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
            border: "none", color: "white", fontWeight: 500, fontSize: "14px",
            cursor: "pointer", display: "flex", alignItems: "center", gap: "6px"
          }}>
            <Plus size={16} /> Novo Produto
          </button>
        </div>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="animate-fade-in" style={{
          padding: "20px", borderRadius: "14px",
          background: "rgba(26,26,46,0.8)", border: "1px solid rgba(139,92,246,0.2)",
          marginBottom: "20px", display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr auto",
          gap: "12px", alignItems: "end"
        }}>
          <div>
            <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>Catálogo</label>
            <select value={form.catalog_id} onChange={(e) => setForm({ ...form, catalog_id: e.target.value })} required
              style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.2)", color: "#f1f5f9", fontSize: "14px" }}>
              <option value="">Selecione...</option>
              {catalogs.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>Nome</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required
              style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.2)", color: "#f1f5f9", fontSize: "14px", outline: "none" }} />
          </div>
          <div>
            <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>Descrição</label>
            <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.2)", color: "#f1f5f9", fontSize: "14px", outline: "none" }} />
          </div>
          <div>
            <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>Preço (R$)</label>
            <input type="number" step="0.01" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} required
              style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.2)", color: "#f1f5f9", fontSize: "14px", outline: "none" }} />
          </div>
          <button type="submit" style={{
            padding: "10px 20px", borderRadius: "8px", background: "#10b981",
            border: "none", color: "white", fontWeight: 500, cursor: "pointer"
          }}>Salvar</button>
        </form>
      )}

      {/* Products table */}
      <div style={{
        borderRadius: "14px", overflow: "hidden",
        background: "rgba(26,26,46,0.8)", border: "1px solid rgba(139,92,246,0.15)"
      }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid rgba(139,92,246,0.1)" }}>
              {["Produto", "Catálogo", "Preço", "Estoque"].map((h) => (
                <th key={h} style={{ padding: "12px 16px", textAlign: "left", fontSize: "12px", color: "#64748b", fontWeight: 600, textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id} style={{ borderBottom: "1px solid rgba(139,92,246,0.05)" }}>
                <td style={{ padding: "14px 16px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <Package size={16} style={{ color: "#8b5cf6" }} />
                    <div>
                      <div style={{ fontWeight: 500, fontSize: "14px" }}>{p.name}</div>
                      <div style={{ fontSize: "12px", color: "#64748b" }}>{p.description}</div>
                    </div>
                  </div>
                </td>
                <td style={{ padding: "14px 16px", fontSize: "13px", color: "#94a3b8" }}>
                  {catalogs.find((c) => c.id === p.catalog_id)?.name || "-"}
                </td>
                <td style={{ padding: "14px 16px", fontSize: "14px", fontWeight: 600, color: "#10b981" }}>
                  R$ {parseFloat(p.price).toFixed(2)}
                </td>
                <td style={{ padding: "14px 16px" }}>
                  <button onClick={() => loadStock(p.id)} style={{
                    padding: "6px 12px", borderRadius: "6px",
                    background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.3)",
                    color: "#a5b4fc", fontSize: "12px", cursor: "pointer",
                    display: "flex", alignItems: "center", gap: "4px"
                  }}>
                    <Boxes size={14} /> Ver estoque
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Stock Modal */}
      {showStock && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
          display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50
        }} onClick={() => setShowStock(null)}>
          <div onClick={(e) => e.stopPropagation()} className="animate-slide-up" style={{
            width: "500px", maxHeight: "80vh", overflow: "auto",
            borderRadius: "16px", background: "#1a1a2e",
            border: "1px solid rgba(139,92,246,0.2)", padding: "24px"
          }}>
            <h3 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px" }}>
              Estoque do Produto
            </h3>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {["Tamanho", "Cor", "Qtd"].map((h) => (
                    <th key={h} style={{ padding: "8px", textAlign: "left", fontSize: "12px", color: "#64748b", borderBottom: "1px solid rgba(139,92,246,0.1)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {stock.map((s) => (
                  <tr key={s.id}>
                    <td style={{ padding: "8px", fontSize: "13px" }}>{s.size}</td>
                    <td style={{ padding: "8px", fontSize: "13px" }}>{s.color}</td>
                    <td style={{
                      padding: "8px", fontSize: "13px", fontWeight: 600,
                      color: s.quantity > 0 ? "#10b981" : "#ef4444"
                    }}>
                      {s.quantity}
                    </td>
                  </tr>
                ))}
                {stock.length === 0 && (
                  <tr>
                    <td colSpan={3} style={{ padding: "20px", textAlign: "center", color: "#64748b" }}>
                      Sem itens de estoque
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
