import type { Metadata } from "next";
import type { ReactNode } from "react";
import {
  Instrument_Serif,
  JetBrains_Mono,
  Space_Grotesk,
} from "next/font/google";
import SiteNav from "@/components/SiteNav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Spieon",
  description:
    "Autonomous security agent that scans MCP servers and x402 endpoints, attests findings, and rewards probe authors.",
  icons: {
    icon: "/spieon.svg",
    shortcut: "/spieon.svg",
    apple: "/spieon.svg",
  },
};

const editorialSans = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
});

const editorialMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

const editorialSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
  variable: "--font-instrument-serif",
});

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        suppressHydrationWarning
        className={`${editorialSans.variable} ${editorialMono.variable} ${editorialSerif.variable} min-h-screen antialiased`}
      >
        <div className="relative z-10 mx-auto min-h-screen max-w-[1440px] border-x border-[var(--line-strong)] bg-[var(--paper)]">
          <SiteNav />
          <main className="px-5 py-8 sm:px-8 sm:py-10 lg:px-10 lg:py-12">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
