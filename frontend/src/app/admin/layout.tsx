"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { BarChart3, Settings, LogOut, Shield } from "lucide-react";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = localStorage.getItem("token");
    const user = JSON.parse(localStorage.getItem("user") || "{}");
    if (!token || user.role !== "superadmin") {
      router.push("/login");
    }
  }, [router]);

  return (
    <div style={{ display: "flex", height: "100vh", background: "#0f0f17" }}>
      <aside style={{
        width: "240px", background: "#1a1a2e", borderRight: "1px solid rgba(239,68,68,0.15)",
        display: "flex", flexDirection: "column"
      }}>
        <div style={{ padding: "20px", borderBottom: "1px solid rgba(239,68,68,0.1)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{
              width: "36px", height: "36px", borderRadius: "10px",
              background: "linear-gradient(135deg, #ef4444, #dc2626)",
              display: "flex", alignItems: "center", justifyContent: "center"
            }}>
              <Shield size={18} />
            </div>
            <div>
              <div style={{ fontSize: "16px", fontWeight: 700 }}>ModAI</div>
              <div style={{ fontSize: "11px", color: "#fca5a5" }}>Super Admin</div>
            </div>
          </div>
        </div>

        <nav style={{ flex: 1, padding: "8px" }}>
          {[
            { href: "/admin", icon: <BarChart3 size={18} />, label: "Uso de Tokens" },
            { href: "/admin/limits", icon: <Settings size={18} />, label: "Limites" },
          ].map((item) => (
            <Link key={item.href} href={item.href} style={{
              display: "flex", alignItems: "center", gap: "10px",
              padding: "10px 14px", borderRadius: "10px",
              textDecoration: "none", fontSize: "14px",
              color: pathname === item.href ? "#f1f5f9" : "#94a3b8",
              background: pathname === item.href ? "rgba(239,68,68,0.15)" : "transparent",
              marginBottom: "2px"
            }}>
              {item.icon} {item.label}
            </Link>
          ))}
        </nav>

        <div style={{ padding: "12px", borderTop: "1px solid rgba(239,68,68,0.1)" }}>
          <button onClick={() => {
            localStorage.clear();
            router.push("/login");
          }} style={{
            width: "100%", padding: "8px", borderRadius: "8px",
            background: "transparent", border: "1px solid rgba(239,68,68,0.3)",
            color: "#fca5a5", fontSize: "13px", cursor: "pointer",
            display: "flex", alignItems: "center", gap: "6px", justifyContent: "center"
          }}>
            <LogOut size={14} /> Sair
          </button>
        </div>
      </aside>

      <main style={{ flex: 1, overflow: "auto", padding: "24px" }}>
        {children}
      </main>
    </div>
  );
}
