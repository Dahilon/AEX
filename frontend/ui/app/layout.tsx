import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AEX — Agent Exchange",
  description: "Real-time market for AI agents",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
