import Link from "next/link";
import { MarginPanel } from "@/components/ArticleLayout";
import { ChartSources } from "@/components/ChartSources";
import { Inline } from "@/components/Essay";
import { Fact } from "@/components/Fact";
import { Figure, Key } from "@/components/Figure";
import { Grade } from "@/components/StatusChip";
import type { MigrationDoc, TightInput } from "@/lib/data";
import { PREDICTION_WORDS, WITHHELD_WORDS } from "@/lib/format";

const lower = (name: string) => (/^[A-Z]{2}/.test(name) ? name : name[0].toLowerCase() + name.slice(1)); // "AI chips" keeps its capitals

// Where the bottleneck has sat, by year. The spans are this site's reading of dated events, each with its reason in the
// table; only the "today" line is data. Every place on the track comes from the export; each span links to its row.
export function StripPlate({ strip }: { strip: MigrationDoc["strip"] }) {
  const said = strip.rows.filter((r) => r.spans.some((s) => s.running && s.level === "binding")).map((r) => lower(r.label));
  const next = strip.rows.filter((r) => r.predicted).map((r) => lower(r.label));
  const label = `Which input to AI has been hardest to get in each year from ${strip.from} to today.${said.length ? ` The bottleneck today: ${said.join(", ")}.` : ""}${next.length ? ` Hatched from today on, as this site's predictions: ${next.join(", ")}.` : ""} Each span links to its reason.`;
  const spans = strip.rows.flatMap((r) => r.spans.map((s) => ({ r, s })));
  return (
    <Figure
      title="Where the bottleneck has sat, year by year"
      note="this site's reading of dated events, not a measurement"
      keys={<>
        <Key swatch={<span aria-hidden className="inline-block h-3 w-5 bg-tight-5" />}>the bottleneck</Key>
        <Key swatch={<span aria-hidden className="inline-block h-1.5 w-5 bg-s3" />}>short, but not the bottleneck</Key>
        <Key swatch={<span aria-hidden className="hatch inline-block h-3 w-5 text-s1 ring-1 ring-s1/60" />}>this site&apos;s prediction</Key>
      </>}
      foot={<p>Hatched means a prediction, listed at the end of this page with its test or the outcome that would prove it wrong. The right edge is the end of the chart, not a date.</p>}
      tableLabel="Every span, with its reason"
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">Input</th><th scope="col">Years</th><th scope="col">Reading</th><th scope="col">Why</th></tr></thead>
          <tbody>
            {spans.map(({ r, s }) => (
              <tr key={s.anchor} id={s.anchor} className="scroll-mt-24 target:bg-surface-2">
                <td className="whitespace-nowrap">{r.label}</td>
                <td className="whitespace-nowrap num">{s.from}–{s.running ? "today" : s.to}</td>
                <td className="whitespace-nowrap">{s.level === "binding" ? "the bottleneck" : "short"}</td>
                <td className="min-w-[16rem]">{s.because} <a href={s.source} className="underline decoration-grid underline-offset-2 hover:text-ink">source</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      <div className="sm:grid sm:grid-cols-[10.5rem_minmax(0,1fr)] sm:gap-x-3 font-sans text-sm">
        <div className="hidden sm:flex flex-col pt-6" aria-hidden>
          {strip.rows.map((r) => <div key={r.id} className="h-8 flex items-center justify-end text-right text-[12.5px] leading-tight text-ink-2">{r.label}</div>)}
        </div>
        <div className="relative pt-6 pb-6" role="group" aria-label={label}>
          {strip.ticks.map((t) => <div key={t.x} className="absolute top-6 bottom-6 w-px bg-grid" style={{ left: `${t.x}%` }} aria-hidden />)}
          <div className="absolute top-6 bottom-6 right-0 bg-surface-2/70" style={{ left: `${strip.now_x}%` }} aria-hidden />
          <div data-marks>
            {strip.rows.map((r) => (
              <div key={r.id} className="relative sm:h-8 flex flex-col sm:block">
                <div className="sm:hidden mt-2 mb-0.5 text-[12px] leading-tight text-ink-2" aria-hidden>{r.label}</div>
                <div className="relative h-6 sm:h-8">
                  {r.spans.map((s) => {
                    const tip = `${r.label}: ${s.level === "binding" ? "the bottleneck" : "short"}, ${s.from} to ${s.running ? "today" : s.to}`;
                    return <a key={s.anchor} href={`#${s.anchor}`} data-tip={tip} aria-label={tip} title={tip} tabIndex={0} data-stop={s === spans[0].s || undefined}
                      className={`absolute top-1/2 -translate-y-1/2 ${s.level === "binding" ? "h-4 sm:h-[18px] bg-tight-5" : "h-2 sm:h-[9px] bg-s3"}`} style={{ left: `${s.left}%`, width: `${s.width}%` }} />;
                  })}
                  {r.predicted ? <div aria-hidden className="hatch absolute top-1/2 -translate-y-1/2 h-4 sm:h-[18px] text-s1 ring-1 ring-s1/60" style={{ left: `${strip.now_x}%`, right: 0 }} /> : null}
                </div>
              </div>
            ))}
          </div>
          <div className="absolute top-4 bottom-4 w-px bg-ink" style={{ left: `${strip.now_x}%` }} aria-hidden />
          <div className="sm:hidden absolute top-0 -translate-x-1/2 whitespace-nowrap font-mono text-[10px] uppercase tracking-[0.1em] text-ink-2" style={{ left: `${strip.now_x}%` }} aria-hidden>today</div>
          <div className="hidden sm:block absolute top-0 left-0 pr-1.5 text-right whitespace-nowrap font-mono text-[10px] uppercase tracking-[0.1em] text-ink-2" style={{ width: `${strip.now_x}%` }} aria-hidden>observed</div>
          <div className="hidden sm:block absolute top-0 pl-1.5 whitespace-nowrap font-mono text-[10px] uppercase tracking-[0.1em] text-ink-2" style={{ left: `${strip.now_x}%` }} aria-hidden>predicted</div>
          <div className="absolute bottom-0 left-0 right-0 h-4" aria-hidden>
            {strip.ticks.map((t) => <span key={t.x} className={`absolute -translate-x-1/2 whitespace-nowrap font-mono text-[10px] text-muted ${t.minor ? "max-sm:hidden" : ""}`} style={{ left: `${t.x}%` }}>{t.label}</span>)}
          </div>
        </div>
      </div>
    </Figure>
  );
}

const WHY = WITHHELD_WORDS;
// the five tightness words on the one-hue ramp, slack lightest
const TONE: Record<string, string> = { slack: "var(--tight-1)", easing: "var(--tight-2)", moderate: "var(--tight-3)", tight: "var(--tight-4)", severe: "var(--tight-5)" };

function Bar({ i, floors }: { i: TightInput; floors: number[] }) {
  const tone = TONE[i.word ?? "slack"];
  return (
    <span className="relative block h-2.5 w-full min-w-12 bg-surface-2" aria-hidden>
      <span className={`absolute inset-y-0 left-0 ${i.hatched ? "hatch" : ""}`} style={{ width: `${i.score}%`, color: tone, background: i.hatched ? undefined : tone, boxShadow: i.hatched ? "inset 0 0 0 1px currentColor" : undefined }} />
      {floors.map((f) => <span key={f} className="absolute inset-y-0 w-px bg-surface" style={{ left: `${f}%` }} />)}
    </span>
  );
}

// Twenty-three inputs in three groups, as the prototype's dense table. A scored row shows a whole number and its word
// on a bar ticked at the word lines, its confidence and how many gauges stand behind it; an input with no usable data
// stays in the table with the reason, never scored.
export function ScorecardPlate({ card }: { card: MigrationDoc["scorecard"] }) {
  const floors = card.method.words.map(([floor]) => floor).filter((f) => f > 0);
  const scored = card.inputs.filter((i) => i.score !== null);
  return (
    <Figure
      title="How tight each input to AI is today"
      note="nought slack · a hundred severe · scored only where a published series supports it"
      keys={<>
        {[...card.method.words].reverse().map(([, w]) => <Key key={w} swatch={<span aria-hidden className="inline-block h-2.5 w-4" style={{ background: TONE[w] }} />}>{w}</Key>)}
        {scored.some((i) => i.hatched) ? <Key swatch={<span aria-hidden className="hatch inline-block h-2.5 w-4 text-tight-3 ring-1 ring-tight-3" />}>confidence under {card.method.hatch_under}</Key> : null}
      </>}
      foot={<>
        <p>Tightness is this site&apos;s arithmetic on other people&apos;s figures, most of them Epoch AI&apos;s estimates, for which Epoch publishes wide error margins. A gap of under ten points between two inputs means nothing. <Link href="/methodology#tightness" className="underline decoration-axis underline-offset-2 hover:decoration-ink">How the scores are made</Link>.</p>
        <ChartSources cs={card.chart_sources} />
      </>}
      tableLabel="The gauges behind each score"
      table={scored.length ? (
        <table className="data w-full">
          <thead><tr><th scope="col">Gauge</th><th scope="col">Reading</th><th scope="col">Points</th><th scope="col">Weight</th><th scope="col">Age, of limit</th><th scope="col">Grade</th></tr></thead>
          {scored.map((i) => (
            <tbody key={i.id}>
              <tr><th scope="rowgroup" colSpan={6} className="pt-3!"><span className="block max-w-[19rem] sm:max-w-none font-sans font-medium normal-case tracking-normal text-[12.5px] text-ink">{i.name} <span className="font-normal text-muted">· evidence fed {i.factors?.coverage}, freshness {i.factors?.freshness}, source {i.factors?.source}</span></span></th></tr>
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
      ) : undefined}
    >
      <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Tightness of each input, as a table">
        <table className="data w-full [&_td]:max-sm:px-2 [&_th]:max-sm:px-2">
          <thead><tr><th scope="col">Input</th><th scope="col" className="w-[42%]">Tightness</th><th scope="col" className="max-sm:hidden">Confidence</th><th scope="col" className="max-sm:hidden">Gauges</th></tr></thead>
          {card.kinds.map((k) => (
            <tbody key={k.id}>
              <tr><th scope="rowgroup" colSpan={4} className="pt-4!"><span className="block font-sans text-[12px] text-ink">{k.name}</span><span className="block mt-0.5 font-serif normal-case tracking-normal text-[13px] font-normal text-ink-2">{k.tight_means}</span></th></tr>
              {card.inputs.filter((i) => i.kind === k.id).map((i) => i.score !== null ? (
                <tr key={i.id} id={`input-${i.id}`} className="scroll-mt-24 target:bg-surface-2">
                  <td className="sm:min-w-[9rem]">
                    <span className="text-ink font-medium"><span className="num text-muted mr-1.5 text-[11px]">{String(i.n).padStart(2, "0")}</span>{i.name}</span>
                    <span className="sm:hidden block text-[11px] text-ink-2">confidence <span className="num">{i.confidence}</span>{i.hatched ? " (low)" : ""} · {i.used} of {i.defined} gauge{i.defined === 1 ? "" : "s"}</span>
                    {i.reads ? <span className="block mt-0.5 text-[11px] leading-snug text-ink-2">{i.reads}</span> : null}
                  </td>
                  <td><div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2"><Bar i={i} floors={floors} /><span className="whitespace-nowrap text-ink"><span className="num">{i.score}</span> · {i.word}</span></div>{i.gauges.some((g) => g.pinned) ? <span className="block text-[11px] text-ink-2">at the end of its scale</span> : null}</td>
                  <td className="max-sm:hidden num whitespace-nowrap">{i.confidence}{i.hatched ? " (low)" : ""}</td>
                  <td className="max-sm:hidden num whitespace-nowrap">{i.used} of {i.defined}</td>
                </tr>
              ) : (
                <tr key={i.id} id={`input-${i.id}`} className="scroll-mt-24 target:bg-surface-2">
                  <td colSpan={4} className="text-ink-2">
                    <span className="num text-muted mr-1.5 text-[11px]">{String(i.n).padStart(2, "0")}</span>{i.name}
                    <span className="block text-[12px] leading-snug"><span className="text-muted">Not scored: {i.withheld ? WHY[i.withheld.kind] : "no reading"}.</span> {i.withheld?.because}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          ))}
        </table>
      </div>
    </Figure>
  );
}

const WHEN: Record<string, string> = { now: "Now", next: "Next", watch: "Watch" };

export function Predictions({ doc }: { doc: MigrationDoc }) {
  return (
    <ul className="flex flex-col">
      {doc.predictions.map((p) => (
        <li key={p.id} className="py-5 border-t border-grid grid gap-2 md:grid-cols-[minmax(0,1fr)_12rem] md:gap-8">
          <div className="flex flex-col gap-1.5">
            <p className="font-serif text-[1.125rem] leading-snug text-ink"><Inline text={p.claim} facts={doc.facts} /></p>
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
          ["Inputs scored", c.scored.value !== null && c.scored.as_of !== null ? <><Fact f={{ ...c.scored, value: c.scored.value, as_of: c.scored.as_of }} /> of {c.total}</> : `none of ${c.total} today`],
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
