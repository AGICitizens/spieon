"use client";

import Image from "next/image";
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
  { href: "/hackathon", label: "Hackathon" },
  { href: "/about", label: "About" },
];

export default function SiteNav() {
  const pathname = usePathname();

  return (
    <header className="border-b border-[var(--line-strong)] bg-[var(--paper)]">
      <nav className="grid min-h-16 grid-cols-[1fr_auto] items-center gap-4 px-5 py-4 sm:grid-cols-[1fr_auto_1fr] lg:px-8">
        <Link href="/" className="flex items-center gap-3">
          <span
            aria-hidden="true"
            className="flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden"
          >
            <Image
              src="/spieon.svg"
              alt=""
              width={32}
              height={32}
              className="h-8 w-8 scale-[1.18]"
            />
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
