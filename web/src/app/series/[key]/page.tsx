import Link from "next/link";
import { Grade } from "@/components/StatusChip";
import { fmt, series, seriesKeys } from "@/lib/data";

export const dynamicParams = false;
export function generateStaticParams() { return seriesKeys().map((key) => ({ key })); }

const COLS = ["as_of_date", "published_date", "tier", "audited_vs_reported", "extraction_method", "review_status", "retrieved_at", "http_status", "content_hash", "supersedes_id"] as const;

export default async function SeriesPage({ params }: { params: Promise<{ key: string }> }) {
  const { key } = await params;
  const s = series(decodeURIComponent(key));
  return (
    <div className="flex flex-col gap-4">
      <div>
        <p className="text-xs text-muted"><Link href="/indicators" className="hover:text-ink">Indicators</Link> / series</p>
        <h1 className="text-xl font-semibold tracking-tight font-mono break-all">{s.series_key}</h1>
        <p className="text-sm text-ink-2 mt-1">
          {s.source ? <>Source: <a href={s.source.url} className="underline decoration-grid underline-offset-4">{s.source.name}</a> ({s.source.org}) · {s.source.license}</> : "Source unknown"} · <a href={`/data/${s.series_key}.csv`} className="underline decoration-grid underline-offset-4">CSV</a>
        </p>
        {s.source?.attribution ? <p className="text-xs text-muted mt-1">{s.source.attribution}</p> : null}
      </div>
      <div className="overflow-x-auto">
        <table className="data w-full text-xs">
          <thead><tr><th>id</th><th>value</th><th>grade</th>{COLS.map((c) => <th key={c}>{c.replace(/_/g, " ")}</th>)}<th>url</th><th>flags</th></tr></thead>
          <tbody>
            {s.observations.map((o) => (
              <tr key={o.id} id={o.id} className="target:bg-fast/10">
                <td className="font-mono">{o.id}</td>
                <td className="tabular-nums whitespace-nowrap">{o.value_numeric !== null ? fmt(o.value_numeric as number, String(o.unit)) : String(o.value_text)}{o.value_low != null ? <span className="text-muted"> ({fmt(o.value_low as number)}–{fmt(o.value_high as number)})</span> : null}</td>
                <td><Grade grade={o.grade} tier={o.tier as number} /></td>
                {COLS.map((c) => <td key={c} className="whitespace-nowrap text-ink-2">{o[c] === null || o[c] === undefined ? "—" : String(o[c]).slice(0, c === "content_hash" ? 12 : 40)}</td>)}
                <td><a href={String(o.url)} className="underline decoration-grid underline-offset-4">link</a></td>
                <td>{o.disputed ? <span className="text-slow" title={String(o.dispute_text)}>⚑ disputed</span> : null}{o.run_rate_vs_booked ? <span className="ml-1">{String(o.run_rate_vs_booked)}</span> : null}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <details className="text-xs"><summary className="cursor-pointer text-ink-2">Raw snippets and dispute text</summary>
        <ul className="mt-2 flex flex-col gap-2 font-mono">{s.observations.map((o) => <li key={o.id}><span className="text-muted">{o.id}</span> {String(o.raw_snippet)}{o.dispute_text ? <span className="text-slow"> — {String(o.dispute_text)}</span> : null}</li>)}</ul>
      </details>
    </div>
  );
}
