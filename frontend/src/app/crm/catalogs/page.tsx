"use client";

import { useEffect, useState, useRef } from "react";
import { getCatalogs, createCatalog, deleteCatalog, uploadCatalogPdf } from "@/lib/api";
import { Plus, Trash2, FolderOpen, FileText, Upload } from "lucide-react";

export default function CatalogsPage() {
  const [catalogs, setCatalogs] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadingId, setUploadingId] = useState<string | null>(null);

  const token = typeof window !== "undefined" ? localStorage.getItem("token") || "" : "";

  const load = async () => {
    try {
      const data = await getCatalogs(token);
      setCatalogs(data);
    } catch {}
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createCatalog({ name, description }, token);
      setName(""); setDescription(""); setShowForm(false);
      load();
    } catch {}
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Remover este catálogo e todos os seus produtos?")) return;
    try {
      await deleteCatalog(id, token);
      load();
    } catch {}
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, id: string) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingId(id);
    try {
      await uploadCatalogPdf(id, file, token);
      load();
    } catch (err) {
      alert("Erro ao enviar o PDF");
    } finally {
      setUploadingId(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 style={{ fontSize: "24px", fontWeight: 700, marginBottom: "4px" }}>Catálogos</h1>
          <p style={{ color: "#94a3b8", fontSize: "14px" }}>Gerencie as categorias de produtos da loja</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} style={{
          padding: "10px 20px", borderRadius: "10px",
          background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
          border: "none", color: "white", fontWeight: 500, fontSize: "14px",
          cursor: "pointer", display: "flex", alignItems: "center", gap: "6px"
        }}>
          <Plus size={16} /> Novo Catálogo
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="animate-fade-in" style={{
          padding: "20px", borderRadius: "14px",
          background: "rgba(26,26,46,0.8)", border: "1px solid rgba(139,92,246,0.2)",
          marginBottom: "20px", display: "flex", gap: "12px", alignItems: "end"
        }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>Nome</label>
            <input value={name} onChange={(e) => setName(e.target.value)} required
              placeholder="Ex: Calças, Blusas, Vestidos..."
              style={{
                width: "100%", padding: "10px 12px", borderRadius: "8px",
                background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.2)",
                color: "#f1f5f9", fontSize: "14px", outline: "none"
              }} />
          </div>
          <div style={{ flex: 2 }}>
            <label style={{ display: "block", fontSize: "12px", color: "#94a3b8", marginBottom: "4px" }}>Descrição</label>
            <input value={description} onChange={(e) => setDescription(e.target.value)}
              placeholder="Descrição opcional..."
              style={{
                width: "100%", padding: "10px 12px", borderRadius: "8px",
                background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.2)",
                color: "#f1f5f9", fontSize: "14px", outline: "none"
              }} />
          </div>
          <button type="submit" style={{
            padding: "10px 20px", borderRadius: "8px",
            background: "#10b981", border: "none", color: "white",
            fontWeight: 500, fontSize: "14px", cursor: "pointer", whiteSpace: "nowrap"
          }}>Salvar</button>
        </form>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "16px" }}>
        {catalogs.map((cat) => (
          <div key={cat.id} className="animate-fade-in" style={{
            padding: "20px", borderRadius: "14px",
            background: "rgba(26,26,46,0.8)", border: "1px solid rgba(139,92,246,0.15)",
            display: "grid", gridTemplateColumns: "1fr auto", alignItems: "start"
          }}>
            <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
              <div style={{
                width: "40px", height: "40px", borderRadius: "10px",
                background: "rgba(139,92,246,0.15)",
                display: "flex", alignItems: "center", justifyContent: "center",
                color: "#8b5cf6"
              }}>
                <FolderOpen size={18} />
              </div>
              <div>
                <div style={{ fontSize: "16px", fontWeight: 600 }}>{cat.name}</div>
                <div style={{ fontSize: "13px", color: "#94a3b8" }}>{cat.description || "Sem descrição"}</div>
              </div>
            </div>
            <button onClick={() => handleDelete(cat.id)} style={{
              background: "none", border: "none", color: "#ef4444", cursor: "pointer",
              padding: "6px", borderRadius: "6px"
            }}>
              <Trash2 size={16} />
            </button>
            <div style={{ marginTop: "12px", borderTop: "1px solid rgba(139,92,246,0.1)", paddingTop: "12px", width: "100%", gridColumn: "1 / -1" }}>
              <div style={{ display: "flex", gap: "8px" }}>
                {cat.pdf_url ? (
                  <a href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${cat.pdf_url}`} target="_blank" rel="noreferrer" style={{
                    display: "flex", alignItems: "center", gap: "6px", fontSize: "13px",
                    color: "#8b5cf6", textDecoration: "none", fontWeight: 500,
                    padding: "6px 12px", borderRadius: "6px", background: "rgba(139,92,246,0.1)"
                  }}>
                    <FileText size={14} /> Ver PDF Atual
                  </a>
                ) : (
                  <span style={{ fontSize: "13px", color: "#64748b", padding: "6px 0" }}>Nenhum PDF associado</span>
                )}
                
                <label style={{
                  display: "flex", alignItems: "center", gap: "6px", fontSize: "13px",
                  color: "#f1f5f9", cursor: uploadingId === cat.id ? "not-allowed" : "pointer", fontWeight: 500,
                  padding: "6px 12px", borderRadius: "6px", background: "rgba(255,255,255,0.05)",
                  border: "1px dashed rgba(255,255,255,0.2)"
                }}>
                  <Upload size={14} /> {uploadingId === cat.id ? "Enviando..." : (cat.pdf_url ? "Substituir PDF" : "Enviar PDF")}
                  <input type="file" accept=".pdf" style={{ display: "none" }}
                    disabled={uploadingId === cat.id}
                    onChange={(e) => handleFileUpload(e, cat.id)} />
                </label>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
