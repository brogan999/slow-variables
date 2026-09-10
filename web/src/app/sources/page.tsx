import { sources } from "@/lib/data";

export const metadata = { title: "Sources" };

export default function SourcesPage() {
  const rows = sources();
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold tracking-tight">Sources</h1>
      <p className="text-sm text-ink-2 max-w-3xl">Only sources with a working connector or a fetched manual row are listed. Health comes from the fetch log, never from a hand-edited field; a source is stale when its last success is older than twice its cadence.</p>
      <div className="overflow-x-auto">
        <table className="data w-full text-sm">
          <thead><tr><th scope="col">Source</th><th scope="col">Org</th><th scope="col">Kind</th><th scope="col">Default tier</th><th scope="col">Cadence</th><th scope="col">Lens</th><th scope="col">Health</th><th scope="col">Last success</th><th scope="col">Items</th><th scope="col">Runs</th><th scope="col">Attribution and licence</th></tr></thead>
          <tbody>
            {rows.map((s) => (
              <tr key={s.id}>
                <td><a href={s.url} className="font-medium underline decoration-grid underline-offset-4">{s.name}</a>{s.last_error ? <div className="text-xs text-slow">last run failed: {s.last_error}</div> : null}</td>
                <td className="text-ink-2">{s.org}</td><td>{s.kind}</td><td className="tabular-nums">{s.default_tier}</td><td>{s.cadence.replace(/_/g, " ")}</td><td>{s.lens}</td>
                <td><Health h={s.health} /></td>
                <td className="whitespace-nowrap tabular-nums">{s.last_success_at ? s.last_success_at.slice(0, 16).replace("T", " ") : "never"}</td>
                <td className="tabular-nums">{s.items_found}</td><td className="tabular-nums">{s.runs || "—"}</td><td className="text-xs text-ink-2">{s.attribution}{s.license ? <span className="text-muted"> · {s.license}</span> : null}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Health({ h }: { h: string }) {
  const label = h === "ok" ? "● fresh" : h === "stale" ? "◐ stale" : "○ never run";
  return <span className={`text-xs whitespace-nowrap ${h === "stale" ? "text-slow" : h === "ok" ? "text-ink" : "text-muted"}`}>{label}</span>;
}
