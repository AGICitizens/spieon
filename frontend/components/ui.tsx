import type { ReactNode } from "react";
import Link from "next/link";
import clsx from "clsx";

const TONE_CLASS = {
  neutral: "border-[var(--line-strong)] bg-[var(--panel)] text-[var(--muted)]",
  success:
    "border-[color:color-mix(in_srgb,var(--success)_45%,black_10%)] bg-[color:color-mix(in_srgb,var(--success)_10%,white_90%)] text-[color:color-mix(in_srgb,var(--success)_82%,black_18%)]",
  warning:
    "border-[color:color-mix(in_srgb,var(--warning)_45%,black_10%)] bg-[color:color-mix(in_srgb,var(--warning)_10%,white_90%)] text-[color:color-mix(in_srgb,var(--warning)_85%,black_15%)]",
  danger:
    "border-[color:color-mix(in_srgb,var(--danger)_45%,black_10%)] bg-[color:color-mix(in_srgb,var(--danger)_10%,white_90%)] text-[color:color-mix(in_srgb,var(--danger)_85%,black_15%)]",
  info: "border-[color:color-mix(in_srgb,var(--info)_45%,black_10%)] bg-[color:color-mix(in_srgb,var(--info)_10%,white_90%)] text-[color:color-mix(in_srgb,var(--info)_82%,black_18%)]",
  dark: "border-[var(--ink)] bg-[var(--ink)] text-[var(--panel)]",
} as const;

type Tone = keyof typeof TONE_CLASS;

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  aside,
  className,
}: {
  eyebrow: string;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  aside?: ReactNode;
  className?: string;
}) {
  return (
    <header
      className={clsx(
        "grid gap-6 border-b border-[var(--line)] pb-8 lg:grid-cols-[minmax(0,1.2fr)_minmax(18rem,22rem)] lg:gap-8",
        className,
      )}
    >
      <div className="space-y-5">
        <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
          {eyebrow}
        </p>
        <div className="space-y-4">
          <h1 className="max-w-[13ch] font-editorial-sans text-4xl font-bold uppercase leading-[0.94] sm:text-5xl lg:text-[4.2rem]">
            {title}
          </h1>
          {description ? (
            <div className="max-w-3xl font-editorial-mono text-sm leading-7 text-[var(--muted)]">
              {description}
            </div>
          ) : null}
        </div>
        {actions ? <div className="flex flex-col gap-3 sm:flex-row">{actions}</div> : null}
      </div>
      {aside ? <Panel className="h-fit">{aside}</Panel> : null}
    </header>
  );
}

export function Panel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        "editorial-card rounded-none p-5 sm:p-6",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function SectionHeading({
  label,
  title,
  description,
  className,
}: {
  label: string;
  title: string;
  description?: ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx("space-y-2", className)}>
      <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
        {label}
      </p>
      <h2 className="font-editorial-sans text-2xl font-semibold uppercase leading-none">
        {title}
      </h2>
      {description ? (
        <div className="max-w-3xl text-sm leading-6 text-[var(--muted)]">
          {description}
        </div>
      ) : null}
    </div>
  );
}

export function MetricCard({
  label,
  value,
  detail,
  className,
}: {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  className?: string;
}) {
  return (
    <Panel className={clsx("space-y-3 p-4 sm:p-5", className)}>
      <p className="font-editorial-mono text-[0.68rem] uppercase tracking-[0.18em] text-[var(--muted)]">
        {label}
      </p>
      <div className="font-editorial-sans text-3xl font-semibold leading-none text-[var(--ink)]">
        {value}
      </div>
      {detail ? (
        <div className="text-xs leading-5 text-[var(--muted)]">{detail}</div>
      ) : null}
    </Panel>
  );
}

export function StatusPill({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center border px-2.5 py-1 font-editorial-mono text-[0.64rem] font-bold uppercase tracking-[0.18em]",
        TONE_CLASS[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: ReactNode;
  action?: ReactNode;
}) {
  return (
    <Panel className="space-y-3">
      <h3 className="font-editorial-sans text-xl font-semibold uppercase">{title}</h3>
      <div className="max-w-2xl text-sm leading-6 text-[var(--muted)]">{description}</div>
      {action ? <div>{action}</div> : null}
    </Panel>
  );
}

export function ActionCard({
  href,
  label,
  title,
  description,
}: {
  href: string;
  label: string;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="editorial-card group block p-5 transition-transform duration-150 hover:-translate-x-1 hover:-translate-y-1 hover:shadow-[10px_10px_0_rgba(17,17,17,0.08)]"
    >
      <p className="font-editorial-mono text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--muted)]">
        {label}
      </p>
      <h3 className="mt-5 font-editorial-sans text-xl font-semibold uppercase leading-tight">
        {title}
      </h3>
      <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{description}</p>
      <p className="mt-6 font-editorial-mono text-[0.7rem] font-bold uppercase tracking-[0.18em] text-[var(--ink)]">
        Open +
      </p>
    </Link>
  );
}
