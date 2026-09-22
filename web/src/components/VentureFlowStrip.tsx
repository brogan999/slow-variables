import { ChartSources } from "./ChartSources";
import { Figure, Key } from "./Figure";
import { Marks, RectMark } from "./chart";
import type { VentureDoc } from "@/lib/data";
import { fmt } from "@/lib/format";

const FILL: Record<string, string> = { formd: "var(--s1)", epoch: "var(--s3)" };
const NAME: Record<string, string> = { formd: "Form D filings", epoch: "Epoch's compiled rounds" };

// Quarterly primary-round equity for one sub-layer, stacked by source, on the quarter spine every strip shares, so
// a quarter with no round is a gap. Every place comes from the export; each segment links to its first round's row.
// Form D debt is not drawn into the equity: it is named in the tip and the table.
export function VentureFlowStrip({ doc, name, note = true }: { doc: VentureDoc; name?: string; note?: boolean }) {
  const who = name ?? doc.sublayer_id.replace(/_/g, " ");
  const any = doc.quarters.filter((q) => q.by_source?.length);
  if (!any.length) return <p className="text-sm text-muted">No primary rounds on file for this sub-layer&apos;s entities.</p>;
  const filled = doc.quarters.filter((q) => q.top !== null);
  const sources = ["formd", "epoch"].filter((src) => filled.some((q) => q.by_source?.some((s) => s.kind === "equity" && s.source === src)));
  const last = filled.at(-1);
  return (
    <Figure
      title={`${who}: primary-round equity by quarter`}
      note="each segment links to its first round's record"
      keys={sources.map((s) => <Key key={s} swatch={<span aria-hidden className="inline-block h-2.5 w-4" style={{ background: FILL[s] }} />}>{NAME[s]}</Key>)}
      foot={<>
        {note ? <p>Primary-round equity per calendar quarter: Form D amount sold where the entity files, Epoch&apos;s press-compiled rounds for an entity-quarter with no filing. Amendments replace their originals; SPVs and secondaries are excluded; Form D debt is listed in the table, not drawn.</p> : null}
        <ChartSources cs={doc.chart_sources} />
      </>}
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">quarter</th><th scope="col">source</th><th scope="col">kind</th><th scope="col">dollars</th><th scope="col">record</th></tr></thead>
          <tbody>
            {any.slice().reverse().flatMap((q) => (q.by_source ?? []).map((s) => (
              <tr key={q.as_of + s.source + s.kind}>
                <td className="num whitespace-nowrap">{q.name}</td><td>{NAME[s.source] ?? s.source}</td><td>{s.kind}</td>
                <td className="num">{fmt(s.value, "USD")}</td>
                <td>{s.href ? <a href={s.href} className="underline decoration-grid underline-offset-2 hover:decoration-ink">{s.stamp ?? "record"}</a> : "—"}</td>
              </tr>
            )))}
          </tbody>
        </table>
      }
    >
      <div className="relative mt-5 h-28" role="group" aria-label={`${who}: primary-round equity by quarter; each segment links to its first round's record`}>
        <div className="absolute inset-x-0 bottom-0 h-px bg-grid" aria-hidden />
        <svg className="absolute inset-0 h-full w-full overflow-visible">
          <Marks>
            {doc.quarters.flatMap((q) => (q.by_source ?? []).filter((s) => s.kind === "equity" && s.y !== undefined).map((s) => {
              const debt = q.by_source?.find((d) => d.kind === "debt");
              const tip = `${q.name} · ${NAME[s.source] ?? s.source} · ${fmt(s.value, "USD")}${s.stamp ? ` · ${s.stamp}` : ""}${debt ? ` · plus ${fmt(debt.value, "USD")} Form D debt` : ""}`;
              return <RectMark key={q.as_of + s.source} x={q.x} y={s.y ?? 0} width={q.width} height={s.height ?? 0} fill={FILL[s.source] ?? "var(--s2)"} href={s.href} tip={tip} stop={q === last} edge={1} />;
            }))}
          </Marks>
        </svg>
        {filled.map((q) => q.venture_dollars ? (
          <span key={q.as_of} aria-hidden className={`absolute -translate-x-1/2 -translate-y-full pb-0.5 whitespace-nowrap num text-[10px] text-ink-2 ${q.label_minor ? "max-sm:hidden" : ""}`} style={{ left: `${q.cx}%`, top: `${q.top}%` }}>{fmt(q.venture_dollars.value, "USD")}</span>
        ) : null)}
      </div>
      <div className="relative h-5 pt-1" aria-hidden>
        {doc.quarters.map((q) => <span key={q.as_of} className={`absolute -translate-x-1/2 whitespace-nowrap num text-[10px] text-muted ${q.minor ? "max-sm:hidden" : ""}`} style={{ left: `${q.cx}%` }}>{q.label}</span>)}
      </div>
    </Figure>
  );
}
