"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";
import { LogIn, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(email, password);
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      if (data.user?.role === "superadmin") {
        router.push("/admin");
      } else {
        router.push("/crm");
      }
    } catch (err: any) {
      setError(err.message || "Erro ao fazer login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
      background: "linear-gradient(135deg, #0f0f17 0%, #1a1a2e 50%, #16213e 100%)"
    }}>
      <form onSubmit={handleLogin} className="animate-slide-up" style={{
        width: "100%", maxWidth: "400px", padding: "40px",
        borderRadius: "20px", background: "rgba(26,26,46,0.9)",
        border: "1px solid rgba(139,92,246,0.2)",
        backdropFilter: "blur(20px)",
        boxShadow: "0 8px 32px rgba(0,0,0,0.3)"
      }}>
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <div style={{
            width: "56px", height: "56px", borderRadius: "16px",
            background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
            display: "flex", alignItems: "center", justifyContent: "center",
            margin: "0 auto 16px", fontSize: "28px",
            boxShadow: "0 4px 20px rgba(139,92,246,0.4)"
          }}>✨</div>
          <h1 style={{ fontSize: "24px", fontWeight: 700, marginBottom: "4px" }}>ModAI</h1>
          <p style={{ color: "#94a3b8", fontSize: "14px" }}>Entre no painel de gestão</p>
        </div>

        {error && (
          <div style={{
            padding: "10px 14px", borderRadius: "10px", marginBottom: "16px",
            background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.3)",
            color: "#fca5a5", fontSize: "13px"
          }}>
            {error}
          </div>
        )}

        <div style={{ marginBottom: "16px" }}>
          <label style={{ display: "block", fontSize: "13px", color: "#94a3b8", marginBottom: "6px" }}>
            Email
          </label>
          <input
            type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            placeholder="seu@email.com" required
            style={{
              width: "100%", padding: "12px 14px", borderRadius: "10px",
              background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.2)",
              color: "#f1f5f9", fontSize: "14px", outline: "none"
            }}
          />
        </div>

        <div style={{ marginBottom: "24px" }}>
          <label style={{ display: "block", fontSize: "13px", color: "#94a3b8", marginBottom: "6px" }}>
            Senha
          </label>
          <div style={{ position: "relative" }}>
            <input
              type={showPw ? "text" : "password"} value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••" required
              style={{
                width: "100%", padding: "12px 14px", borderRadius: "10px",
                background: "#1e2a4a", border: "1px solid rgba(139,92,246,0.2)",
                color: "#f1f5f9", fontSize: "14px", outline: "none"
              }}
            />
            <button type="button" onClick={() => setShowPw(!showPw)} style={{
              position: "absolute", right: "12px", top: "50%", transform: "translateY(-50%)",
              background: "none", border: "none", color: "#64748b", cursor: "pointer"
            }}>
              {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        <button type="submit" disabled={loading} style={{
          width: "100%", padding: "12px", borderRadius: "12px",
          background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
          border: "none", color: "white", fontWeight: 600, fontSize: "15px",
          cursor: loading ? "wait" : "pointer", display: "flex",
          alignItems: "center", justifyContent: "center", gap: "8px",
          opacity: loading ? 0.7 : 1, transition: "all 0.2s"
        }}>
          <LogIn size={18} /> {loading ? "Entrando..." : "Entrar"}
        </button>

        <div style={{ marginTop: "20px", textAlign: "center", fontSize: "12px", color: "#64748b" }}>
          <p>Credenciais de teste:</p>
          <p style={{ color: "#94a3b8" }}>Lojista: admin@modaestrela.com / admin123</p>
          <p style={{ color: "#94a3b8" }}>SuperAdmin: superadmin@modai.com / super123</p>
        </div>
      </form>
    </div>
  );
}
