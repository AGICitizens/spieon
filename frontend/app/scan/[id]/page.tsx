type Params = { id: string };

export default async function ScanDetailPage({
  params,
}: {
  params: Promise<Params>;
}) {
  const { id } = await params;
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Scan {id}</h1>
      <p className="text-zinc-400">
        Live narration stream, probe runs, and attested findings will render
        here.
      </p>
    </section>
  );
}
