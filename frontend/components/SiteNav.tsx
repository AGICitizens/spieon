"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/scan", label: "Scan" },
  { href: "/findings", label: "Findings" },
  { href: "/agent", label: "Agent" },
  { href: "/memory", label: "Memory" },
  { href: "/modules", label: "Modules" },
  { href: "/leaderboard", label: "Leaderboard" },
  { href: "/benchmarks", label: "Benchmarks" },
  { href: "/about", label: "About" },
];

export default function SiteNav() {
  const pathname = usePathname();

  return (
    <header className="border-b border-[var(--line-strong)] bg-[var(--paper)]">
      <nav className="grid min-h-16 grid-cols-[1fr_auto] items-center gap-4 px-5 py-4 sm:grid-cols-[1fr_auto_1fr] lg:px-8">
        <Link href="/" className="flex items-center gap-3">
          <span
            aria-hidden
            className="relative h-5 w-5 shrink-0 rounded-full border-[5px] border-[var(--ink)]"
          >
            <span className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--ink)]" />
          </span>
          <span className="font-editorial-sans text-base font-bold uppercase tracking-[0.08em]">
            Spieon
          </span>
        </Link>

        <div className="hidden justify-center sm:flex">
          <span className="border border-[var(--line-strong)] px-3 py-2 font-editorial-mono text-[0.64rem] font-bold uppercase tracking-[0.18em] text-[var(--muted)]">
            Autonomous Security Operations
          </span>
        </div>

        <div className="flex justify-end">
          <Link href="/scan" className="editorial-button editorial-button-dark min-w-[9rem]">
            Launch scan
          </Link>
        </div>

        <ul className="order-4 col-span-2 flex flex-wrap gap-x-5 gap-y-3 border-t border-[var(--line)] pt-4 sm:order-none sm:col-span-3 sm:justify-center sm:border-t-0 sm:pt-0">
          {NAV.map((item) => {
            const active =
              item.href === "/"
                ? pathname === item.href
                : pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={clsx(
                    "font-editorial-mono text-[0.72rem] uppercase tracking-[0.18em] transition-colors",
                    active ? "text-[var(--ink)]" : "text-[var(--muted)] hover:text-[var(--ink)]",
                  )}
                >
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </header>
  );
}
