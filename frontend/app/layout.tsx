import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Veridian Trading",
  description: "Your crypto trading bot, tuned to you.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
