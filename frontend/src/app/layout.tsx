import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ModAI — Chatbot de Vendas Inteligente",
  description: "Chatbot de vendas com IA para lojas de confecção do polo têxtil do Agreste Pernambucano",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
