import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Spieon",
  description: "Autonomous security agent for the agent economy.",
};

const NAV = [
  { href: "/", label: "Home" },
  { href: "/scan", label: "Scan" },
  { href: "/agent", label: "Agent" },
  { href: "/findings", label: "Findings" },
  { href: "/memory", label: "Memory" },
  { href: "/modules", label: "Modules" },
  { href: "/leaderboard", label: "Leaderboard" },
  { href: "/benchmarks", label: "Benchmarks" },
  { href: "/about", label: "About" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <header className="border-b border-zinc-800/80">
          <nav className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-4 text-sm">
            <Link href="/" className="font-semibold tracking-tight text-zinc-100">
              spieon
            </Link>
            <ul className="flex flex-wrap gap-4 text-zinc-400">
              {NAV.slice(1).map((item) => (
                <li key={item.href}>
                  <Link href={item.href} className="hover:text-zinc-100">
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
