import Link from "next/link";
import { MarginPanel } from "@/components/ArticleLayout";
import { ChartSources } from "@/components/ChartSources";
import { Inline } from "@/components/Essay";
import { Fact } from "@/components/Fact";
import { HATCH } from "@/components/MarginStackChart";
import { Grade } from "@/components/StatusChip";
import type { MigrationDoc, TightInput } from "@/lib/data";
import { PREDICTION_WORDS } from "@/lib/format";

// Where the bottleneck has sat, by year. The spans are this site's reading of dated events, each with its reason in the
// table below; only the "now" line is data. Layout only: a span's place on the track is its year, as a share of the axis.
export function StripPlate({ strip }: { strip: MigrationDoc["strip"] }) {
  const pct = (year: number) => `${(((year - strip.from) / (strip.to - strip.from)) * 100).toFixed(2)}%`;
  const width = (a: number, b: number) => `${(((b - a) / (strip.to - strip.from)) * 100).toFixed(2)}%`;
  const ticks = Array.from({ length: Math.floor((strip.to - strip.from) / 2) + 1 }, (_, i) => strip.from + 2 * i);
  const said = strip.rows.filter((r) => r.spans.some((s) => s.running && s.level === "binding")).map((r) => r.label.toLowerCase());
  return (
    <figure className="plate font-sans text-sm">
      <div className="sm:grid sm:grid-cols-[10.5rem_minmax(0,1fr)] sm:gap-x-3">
        <div className="hidden sm:flex flex-col pt-5" aria-hidden>
          {strip.rows.map((r) => <div key={r.id} className="h-8 flex items-center justify-end text-right text-[12.5px] leading-tight text-ink-2">{r.label}</div>)}
        </div>
        <div className="relative pt-5 pb-6" role="img" aria-label={`A chart of which input to AI has been hardest to get in each year from ${strip.from} to today. Binding today: ${said.join(", ")}. The table below lists every span with its reason.`}>
          <div className="absolute top-5 bottom-6 right-0 bg-surface-2/60" style={{ left: pct(strip.now) }} />
          {strip.rows.map((r) => (
            <div key={r.id} className="relative sm:h-8 flex flex-col sm:block">
              <div className="sm:hidden mt-2 mb-0.5 text-[12px] leading-tight text-ink-2">{r.label}</div>
              <div className="relative h-6 sm:h-8">
                <div className="absolute left-0 right-0 top-1/2 h-px bg-grid" />
                {r.spans.map((s, i) => (
                  <div key={i} className={`absolute top-1/2 -translate-y-1/2 rounded-[1px] ${s.level === "binding" ? "h-4 sm:h-[18px] bg-s1" : "h-2 sm:h-[9px] bg-s2"}`} style={{ left: pct(s.from), width: width(s.from, s.to) }} />
                ))}
                {r.predicted ? <div className="absolute top-1/2 -translate-y-1/2 h-4 sm:h-[18px] border border-s1/70 rounded-[1px]" style={{ left: pct(strip.now), right: 0, background: HATCH }} /> : null}
              </div>
            </div>
          ))}
          <div className="absolute top-4 bottom-4 w-px bg-ink" style={{ left: pct(strip.now) }} />
          <div className="absolute top-0 -translate-x-1/2 whitespace-nowrap font-mono text-[10px] uppercase tracking-[0.12em] text-ink-2" style={{ left: pct(strip.now) }}>today</div>
          <div className="absolute bottom-0 left-0 right-0 h-4">
            {ticks.map((y, i) => <span key={y} className={`absolute -translate-x-1/2 whitespace-nowrap font-mono text-[10px] text-muted ${i % 2 ? "hidden sm:block" : ""}`} style={{ left: pct(y) }}>{y}</span>)}
          </div>
        </div>
      </div>
      <ul className="mt-4 flex flex-wrap gap-x-5 gap-y-1.5 text-xs text-ink-2">
        <li className="flex items-center gap-1.5"><span className="inline-block w-5 h-3 bg-s1 rounded-[1px]" aria-hidden /> the bottleneck</li>
        <li className="flex items-center gap-1.5"><span className="inline-block w-5 h-1.5 bg-s2 rounded-[1px]" aria-hidden /> short, but not what held things back</li>
        <li className="flex items-center gap-1.5"><span className="inline-block w-5 h-3 border border-s1/70 rounded-[1px]" style={{ background: HATCH }} aria-hidden /> predicted</li>
      </ul>
      <figcaption className="mt-3 font-serif text-sm text-ink-2 leading-relaxed">The spans are this site&apos;s reading of dated events, not a measurement; each has its reason and source below. Hatched means a prediction, listed at the end of this page with its test or the outcome that would prove it wrong. The right edge is the end of the chart, not a date.</figcaption>
      <details className="mt-2 text-xs text-ink-2">
        <summary className="cursor-pointer text-muted hover:text-ink">Every span, with its reason</summary>
        <div className="overflow-x-auto mt-2">
          <table className="data w-full">
            <thead><tr><th scope="col">Input</th><th scope="col">Years</th><th scope="col">Reading</th><th scope="col">Why</th></tr></thead>
            <tbody>
              {strip.rows.flatMap((r) => r.spans.map((s, i) => (
                <tr key={`${r.id}${i}`}>
                  <td className="whitespace-nowrap">{r.label}</td>
                  <td className="whitespace-nowrap num">{s.from}–{s.running ? "today" : s.to}</td>
                  <td className="whitespace-nowrap">{s.level === "binding" ? "the bottleneck" : "short"}</td>
                  <td className="min-w-[16rem]">{s.because} <a href={s.source} className="underline decoration-grid underline-offset-2 hover:text-ink">source</a></td>
                </tr>
              )))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}

const lower = (name: string) => (/^[A-Z]{2}/.test(name) ? name : name[0].toLowerCase() + name.slice(1)); // "AI chips" keeps its capitals

const WHY: Record<string, string> = {
  no_public_series: "Nobody publishes a series that would measure it",
  not_read_yet: "Published, but this site does not read it yet",
  gauge_unsound: "The gauge available does not measure what it claims",
  stale_or_thin: "Its readings are too old or too few today",
};

function Bar({ i, ticks }: { i: TightInput; ticks: number[] }) {
  return (
    <div className="relative h-2.5 bg-surface-2 rounded-[1px]" aria-hidden>
      <div className="absolute inset-y-0 left-0 rounded-[1px]" style={{ width: `${i.score}%`, background: i.hatched ? HATCH : "var(--s1)", outline: i.hatched ? "1px solid color-mix(in srgb, var(--s1) 70%, transparent)" : undefined }} />
      {ticks.map((t) => <div key={t} className="absolute inset-y-0 w-px bg-background" style={{ left: `${t}%` }} />)}
    </div>
  );
}

// Twenty-three inputs in three groups. A scored row shows a whole number, its word, its confidence and how many gauges
// stand behind it; an input with no usable data is named and explained, never scored.
export function ScorecardPlate({ card }: { card: MigrationDoc["scorecard"] }) {
  const ticks = card.method.words.map(([floor]) => floor).filter((f) => f > 0);
  const scored = card.inputs.filter((i) => i.score !== null);
  return (
    <figure className="plate font-sans text-sm">
      {card.kinds.map((k) => {
        const rows = card.inputs.filter((i) => i.kind === k.id);
        const out = rows.filter((i) => i.score === null);
        return (
          <section key={k.id} className="mt-7 first:mt-0">
            <h3 className="eyebrow">{k.name}</h3>
            <p className="mt-1 font-serif text-[0.95rem] leading-snug text-ink-2 max-w-[58ch]">{k.tight_means}</p>
            <ol className="mt-3 flex flex-col">
              {rows.filter((i) => i.score !== null).map((i) => (
                <li key={i.id} className="py-3 border-t border-grid grid gap-x-4 gap-y-1.5 grid-cols-[minmax(0,1fr)_auto] sm:grid-cols-[minmax(0,13rem)_minmax(0,1fr)_7.5rem] items-center">
                  <div className="text-ink font-medium leading-tight"><span className="num text-muted mr-2 text-xs">{String(i.n).padStart(2, "0")}</span>{i.name}</div>
                  <div className="order-3 sm:order-2 col-span-2 sm:col-span-1"><Bar i={i} ticks={ticks} /></div>
                  <div className="order-2 sm:order-3 text-ink text-right whitespace-nowrap"><span className="num">{i.score}</span> · {i.word}</div>
                  <p className="order-4 col-span-2 sm:col-span-3 text-xs text-ink-2 leading-relaxed">
                    <span className="whitespace-nowrap">confidence <span className="num">{i.confidence}</span>{i.hatched ? " (low)" : ""}</span> · <span className="whitespace-nowrap">{i.used} of {i.defined} gauge{i.defined === 1 ? "" : "s"}</span>
                    {i.gauges.some((g) => g.pinned) ? <> · at the end of its scale</> : null}. {i.reads}
                  </p>
                </li>
              ))}
            </ol>
            {out.length ? (
              <details className="border-t border-grid pt-3 text-xs text-ink-2">
                <summary className="cursor-pointer leading-relaxed"><span className="text-muted">Not scored:</span> {out.map((i) => lower(i.name)).join(", ")}. <span className="underline decoration-grid underline-offset-2">Why not</span></summary>
                <dl className="mt-2 flex flex-col gap-2.5">
                  {Object.keys(WHY).filter((w) => out.some((i) => i.withheld?.kind === w)).map((w) => (
                    <div key={w}>
                      <dt className="text-muted">{WHY[w]}</dt>
                      {out.filter((i) => i.withheld?.kind === w).map((i) => <dd key={i.id} className="mt-1 leading-relaxed"><span className="text-ink">{i.name}.</span> {i.withheld?.because}</dd>)}
                    </div>
                  ))}
                </dl>
              </details>
            ) : null}
          </section>
        );
      })}
      <ul className="mt-6 flex flex-wrap gap-x-5 gap-y-1.5 text-xs text-ink-2">
        <li className="flex items-center gap-1.5"><span className="inline-block w-5 h-2.5 bg-s1 rounded-[1px]" aria-hidden /> tightness, nought to a hundred</li>
        <li className="flex items-center gap-1.5"><span className="inline-block w-5 h-2.5 rounded-[1px]" style={{ background: HATCH }} aria-hidden /> the same, where confidence is under {card.method.hatch_under}</li>
      </ul>
      <figcaption className="mt-3 font-serif text-sm text-ink-2 leading-relaxed">Tightness is this site&apos;s arithmetic on other people&apos;s figures, most of them Epoch AI&apos;s estimates, for which Epoch publishes wide error margins. A gap of under ten points between two inputs means nothing. <Link href="/methodology#tightness" className="underline decoration-axis underline-offset-2 hover:decoration-ink">How the scores are made</Link>.</figcaption>
      <details className="mt-2 text-xs text-ink-2">
        <summary className="cursor-pointer text-muted hover:text-ink">The gauges behind each score</summary>
        <div className="overflow-x-auto mt-2">
          <table className="data w-full">
            <thead><tr><th scope="col">Gauge</th><th scope="col">Reading</th><th scope="col">Points</th><th scope="col">Weight</th><th scope="col">Age, of limit</th><th scope="col">Grade</th></tr></thead>
            {scored.map((i) => (
              <tbody key={i.id}>
                <tr><th scope="rowgroup" colSpan={6} className="text-left font-sans font-medium normal-case tracking-normal text-[12.5px] text-ink pt-3">{i.name} <span className="font-normal text-muted">· evidence fed {i.factors?.coverage}, freshness {i.factors?.freshness}, source {i.factors?.source}</span></th></tr>
                {i.gauges.map((g) => (
                  <tr key={g.id}>
                    <td className="min-w-[11rem]">{g.label}</td>
                    <td className="whitespace-nowrap">{g.reading ? <Fact f={g.reading} /> : <span className="text-muted">{g.unfed ? "no gauge here" : "no reading"}</span>}</td>
                    <td className="num">{g.points ?? "—"}</td>
                    <td className="num">{g.weight}</td>
                    <td className="num whitespace-nowrap">{g.age_days !== null ? `${g.age_days} of ${g.max_age_days} days` : "—"}</td>
                    <td>{g.grade ? <Grade grade={g.grade} /> : "—"}</td>
                  </tr>
                ))}
              </tbody>
            ))}
          </table>
        </div>
      </details>
      <ChartSources cs={card.chart_sources} />
    </figure>
  );
}

const WHEN: Record<string, string> = { now: "Now", next: "Next", watch: "Watch" };

export function Predictions({ doc }: { doc: MigrationDoc }) {
  return (
    <ul className="flex flex-col">
      {doc.predictions.map((p) => (
        <li key={p.id} className="py-5 border-t border-grid grid gap-2 md:grid-cols-[minmax(0,1fr)_12rem] md:gap-8">
          <div className="flex flex-col gap-1.5">
            <p className="font-serif text-[1.125rem] leading-snug text-ink">{p.claim}</p>
            <p className="font-serif text-[1.0625rem] leading-relaxed text-ink-2"><Inline text={p.text} facts={doc.facts} /></p>
          </div>
          <div className="flex flex-col gap-1 md:text-right">
            <span className="eyebrow">{WHEN[p.when]}</span>
            <span className="text-sm text-ink">{PREDICTION_WORDS[p.state]}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}

export function MigrationMargin({ doc }: { doc: MigrationDoc }) {
  const c = doc.scorecard;
  return (
    <>
      <MarginPanel
        title={`Reading · ${doc.as_of}`}
        rows={[
          ["Inputs scored", c.scored.value ? <><Fact f={c.scored} /> of {c.total}</> : `none of ${c.total} today`],
          ["Predictions holding", String(doc.tally.holding)],
          ["Failing their test", String(doc.tally.failing)],
          ["Can't be tested yet", String(doc.tally.untestable)],
        ]}
      />
      <MarginPanel title="Instrument">
        <p>Tightness runs from nought to a hundred and is scored only where a published series supports it. It is a different thing from the speed readings elsewhere on this site and never changes one.</p>
        <p><Link href="/methodology#tightness" className="text-ink underline decoration-axis underline-offset-2">How the scores are made →</Link></p>
        <p>A different list: <Link href="/bottlenecks" className="text-ink underline decoration-axis underline-offset-2">the barriers to adoption</Link> that Arvind Narayanan and Sayash Kapoor describe are about why firms are slow to use AI, not about what is scarce in making it.</p>
        <p>The two tallies of what labs buy are kept on <Link href="/layers/model" className="text-ink underline decoration-axis underline-offset-2">the model layer&apos;s page</Link>.</p>
      </MarginPanel>
    </>
  );
}
