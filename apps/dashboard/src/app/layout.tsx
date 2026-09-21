import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "CRouter Gateway — Observability & Control Center",
  description: "Resilient, OpenAI-compatible AI gateway dashboard for routing, quota governance, and live inference.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0b0f19] text-slate-100 antialiased selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
