"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import {
  LayoutDashboard, ShoppingBag, Package, Users, Columns3,
  MessageCircle, LogOut, Settings
} from "lucide-react";

const navItems = [
  { href: "/crm", icon: <LayoutDashboard size={18} />, label: "Dashboard" },
  { href: "/crm/catalogs", icon: <ShoppingBag size={18} />, label: "Catálogos" },
  { href: "/crm/products", icon: <Package size={18} />, label: "Produtos" },
  { href: "/crm/customers", icon: <Users size={18} />, label: "Clientes" },
  { href: "/crm/kanban", icon: <Columns3 size={18} />, label: "Kanban" },
  { href: "/crm/conversations", icon: <MessageCircle size={18} />, label: "Conversas" },
];

export default function CRMLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const userData = localStorage.getItem("user");
    if (!token) {
      router.push("/login");
      return;
    }
    if (userData) setUser(JSON.parse(userData));
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    router.push("/login");
  };

  return (
    <div style={{ display: "flex", height: "100vh", background: "#0f0f17" }}>
      {/* Sidebar */}
      <aside style={{
        width: "240px", background: "#1a1a2e", borderRight: "1px solid rgba(139,92,246,0.15)",
        display: "flex", flexDirection: "column", flexShrink: 0
      }}>
        <div style={{ padding: "20px", borderBottom: "1px solid rgba(139,92,246,0.1)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{
              width: "36px", height: "36px", borderRadius: "10px",
              background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px"
            }}>✨</div>
            <div>
              <div style={{ fontSize: "16px", fontWeight: 700, color: "#f1f5f9" }}>ModAI</div>
              <div style={{ fontSize: "11px", color: "#64748b" }}>CRM</div>
            </div>
          </div>
        </div>

        <nav style={{ flex: 1, padding: "8px" }}>
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} style={{
                display: "flex", alignItems: "center", gap: "10px",
                padding: "10px 14px", borderRadius: "10px",
                textDecoration: "none", fontSize: "14px", fontWeight: 500,
                color: isActive ? "#f1f5f9" : "#94a3b8",
                background: isActive ? "rgba(139,92,246,0.15)" : "transparent",
                border: isActive ? "1px solid rgba(139,92,246,0.3)" : "1px solid transparent",
                marginBottom: "2px", transition: "all 0.2s"
              }}>
                {item.icon} {item.label}
              </Link>
            );
          })}
        </nav>

        <div style={{ padding: "12px", borderTop: "1px solid rgba(139,92,246,0.1)" }}>
          {user && (
            <div style={{ padding: "8px 12px", fontSize: "12px", color: "#94a3b8", marginBottom: "8px" }}>
              {user.name}
            </div>
          )}
          <button onClick={handleLogout} style={{
            width: "100%", padding: "8px 12px", borderRadius: "8px",
            background: "transparent", border: "1px solid rgba(239,68,68,0.3)",
            color: "#fca5a5", fontSize: "13px", cursor: "pointer",
            display: "flex", alignItems: "center", gap: "6px", justifyContent: "center"
          }}>
            <LogOut size={14} /> Sair
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, overflow: "auto", padding: "24px" }}>
        {children}
      </main>
    </div>
  );
}
