import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Baja — Inspeção de Pintura",
  description:
    "Detecção automática de defeitos de pintura em chassis BAJA via IA.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
