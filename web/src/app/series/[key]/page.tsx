import Link from "next/link";
import { Grade } from "@/components/StatusChip";
import { fmt, series, seriesKeys } from "@/lib/data";

export const dynamicParams = false;
export async function generateMetadata({ params }: { params: Promise<{ key: string }> }) {
  const { key } = await params;
  return { title: decodeURIComponent(key) };
}
export function generateStaticParams() { return seriesKeys().map((key) => ({ key })); }

const COLS = ["as_of_date", "published_date", "tier", "audited_vs_reported", "extraction_method", "review_status", "retrieved_at", "http_status", "content_hash", "supersedes_id"] as const;

export default async function SeriesPage({ params }: { params: Promise<{ key: string }> }) {
  const { key } = await params;
  const s = series(decodeURIComponent(key));
  const oneReason = new Set(s.withdrawn.map((o) => o.dispute_text)).size === 1;
  return (
    <div className="flex flex-col gap-4">
      <div>
        <p className="text-xs text-muted"><Link href="/indicators" className="hover:text-ink">Indicators</Link> / series</p>
        <h1 className="num text-xl md:text-2xl break-all">{s.series_key}</h1>
        <p className="text-sm text-ink-2 mt-1">
          {s.source ? <>Source: <a href={s.source.url} className="underline decoration-grid underline-offset-4">{s.source.name}</a> ({s.source.org}) · {s.source.license}</> : "Source unknown"} · <a href={`/data/${s.series_key}.csv`} className="underline decoration-grid underline-offset-4">CSV</a>
        </p>
        {s.source?.attribution ? <p className="text-xs text-muted mt-1">{s.source.attribution}</p> : null}
      </div>
      {s.observations.length === 0 ? <p className="text-sm text-ink-2">No live rows: every row in this series was withdrawn.</p> : null}
      <div className="overflow-x-auto" hidden={s.observations.length === 0}>
        <table className="data w-full text-xs">
          <thead><tr><th scope="col">id</th><th scope="col">{s.observations.every((o) => o.value_numeric === null) ? "text" : "value"}</th><th scope="col">grade</th>{COLS.map((c) => <th scope="col" key={c}>{c.replace(/_/g, " ")}</th>)}<th scope="col">url</th><th scope="col">flags</th></tr></thead>
          <tbody>
            {s.observations.map((o) => (
              <tr key={o.id} id={o.id} className="target:bg-fast/10">
                <td className="font-mono">{o.id}</td>
                <td className={o.value_numeric !== null ? "tabular-nums whitespace-nowrap" : "max-w-md"}>{o.value_numeric !== null ? fmt(o.value_numeric as number, String(o.unit)) : String(o.value_text)}{o.value_low != null ? <span className="text-muted"> ({fmt(o.value_low as number)}–{fmt(o.value_high as number)})</span> : null}</td>
                <td><Grade grade={o.grade} tier={o.tier as number} /></td>
                {COLS.map((c) => <td key={c} className="whitespace-nowrap text-ink-2">{o[c] === null || o[c] === undefined ? "—" : String(o[c]).slice(0, c === "content_hash" ? 12 : 40)}</td>)}
                <td><a href={String(o.url)} className="underline decoration-grid underline-offset-4">source page</a></td>
                <td>{o.disputed ? <span className="text-slow">⚑ disputed: {String(o.dispute_text).slice(0, 120)}</span> : null}{o.run_rate_vs_booked ? <span className="ml-1">{String(o.run_rate_vs_booked)}</span> : null}{o.gross_vs_net ? <span className="ml-1">{String(o.gross_vs_net)}</span> : null}{o.note ? <div className="text-muted">{String(o.note)}</div> : null}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {s.withdrawn.length ? (
        <section aria-labelledby="withdrawn" className="text-xs">
          <h2 id="withdrawn" className="text-sm font-medium">Withdrawn rows</h2>
          <p className="text-ink-2 mt-1">Rows found to be wrong are kept, struck through, with the reason. They feed no number on this site.</p>
          {oneReason ? <p className="text-slow mt-1">{String(s.withdrawn[0].dispute_text)}</p> : null}
          <ul className="mt-2 flex flex-col gap-1">
            {s.withdrawn.map((o) => (
              <li key={o.id} id={o.id} className="target:bg-fast/10">
                <span className="font-mono text-muted">{o.id}</span>{" "}
                <del className="num">{String(o.as_of_date)} · {o.value_numeric !== null ? fmt(o.value_numeric as number, String(o.unit)) : String(o.value_text)}</del>{" "}
                <a href={String(o.url)} className="underline decoration-grid underline-offset-4">source page</a>
                {oneReason ? null : <span className="text-slow"> — {String(o.dispute_text)}</span>}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <details className="text-xs"><summary className="cursor-pointer text-ink-2">Raw snippets and dispute text</summary>
        <ul className="mt-2 flex flex-col gap-2 font-mono">{s.observations.map((o) => <li key={o.id}><span className="text-muted">{o.id}</span> {String(o.raw_snippet)}{o.dispute_text ? <span className="text-slow"> — {String(o.dispute_text)}</span> : null}</li>)}</ul>
      </details>
    </div>
  );
}
