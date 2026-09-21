import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "CRouter Gateway: Observability & Control Center",
  description: "Resilient, OpenAI-compatible AI gateway dashboard for routing, quota governance, and live inference.",
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
      { url: "/favicon.svg", type: "image/svg+xml" },
    ],
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-zinc-50 text-zinc-900 antialiased selection:bg-zinc-200 selection:text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}

