import { api, type Finding } from "@/lib/api";
import NarrationStream from "./NarrationStream";
import PayoutButton from "./PayoutButton";

const SEVERITY_STYLE: Record<Finding["severity"], string> = {
  low: "border-zinc-700 text-zinc-300",
  medium: "border-amber-700 text-amber-200",
  high: "border-orange-700 text-orange-200",
  critical: "border-red-700 text-red-200",
};

type Params = { id: string };

export default async function ScanDetailPage({
  params,
}: {
  params: Promise<Params>;
}) {
  const { id } = await params;

  let findings: Finding[] = [];
  let scanError: string | null = null;
  try {
    findings = await api.listFindings({ scanId: id });
  } catch (err) {
    scanError = (err as Error).message;
  }

  return (
    <section className="space-y-8">
      <header className="space-y-1">
        <p className="text-xs uppercase tracking-wide text-zinc-500">scan</p>
        <h1 className="font-mono text-xl text-zinc-100">{id}</h1>
      </header>

      <NarrationStream scanId={id} />

      <section className="space-y-3">
        <h2 className="text-sm uppercase tracking-wide text-zinc-500">
          Findings ({findings.length})
        </h2>
        {scanError ? (
          <p className="text-sm text-red-400">backend unreachable: {scanError}</p>
        ) : findings.length === 0 ? (
          <p className="text-sm text-zinc-500">
            None yet. Findings appear here as the agent verifies and attests them.
          </p>
        ) : (
          <ul className="space-y-2">
            {findings.map((f) => (
              <li
                key={f.id}
                className={`rounded-md border bg-zinc-950/40 p-3 text-sm ${SEVERITY_STYLE[f.severity]}`}
              >
                <div className="flex items-baseline justify-between gap-3">
                  <span className="font-medium text-zinc-100">{f.title}</span>
                  <span className="text-xs uppercase tracking-wide opacity-80">
                    {f.severity}
                  </span>
                </div>
                <p className="mt-1 text-sm text-zinc-300">{f.summary}</p>
                <p className="mt-2 text-xs text-zinc-500">
                  {f.owasp_id ? (
                    <>
                      owasp <span className="text-zinc-300">{f.owasp_id}</span>{" "}
                    </>
                  ) : null}
                  {f.atlas_technique_id ? (
                    <>
                      · atlas{" "}
                      <span className="text-zinc-300">
                        {f.atlas_technique_id}
                      </span>{" "}
                    </>
                  ) : null}
                  {f.eas_attestation_uid ? (
                    <>
                      · attestation{" "}
                      <span className="font-mono text-zinc-300">
                        {f.eas_attestation_uid.slice(0, 10)}…
                      </span>
                    </>
                  ) : null}
                </p>
                <PayoutButton finding={f} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  );
}
