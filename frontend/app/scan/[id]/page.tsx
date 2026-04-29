import NarrationStream from "./NarrationStream";

type Params = { id: string };

export default async function ScanDetailPage({
  params,
}: {
  params: Promise<Params>;
}) {
  const { id } = await params;

  return (
    <section className="space-y-6">
      <header className="space-y-1">
        <p className="text-xs uppercase tracking-wide text-zinc-500">scan</p>
        <h1 className="font-mono text-xl text-zinc-100">{id}</h1>
      </header>
      <NarrationStream scanId={id} />
    </section>
  );
}
