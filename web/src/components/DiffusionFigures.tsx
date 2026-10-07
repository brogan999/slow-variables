import Link from "next/link";
import { Figure, Key } from "@/components/Figure";
import { StatusChip } from "@/components/StatusChip";
import { TimePlot } from "@/components/TimeChart";
import { GROUP_WORDS, GaugeLink, Glyph, LineSwatch, Strips } from "@/components/diagrams/diffusion";
import { KIND_LABEL } from "@/components/diagrams/kit";
import type { DiffusionFigs, Doc, GaugeGroup } from "@/lib/data";
import { fmt, words } from "@/lib/format";

// The figures on /diffusion. Every count, place and age is the export's (src/ai_tracker/diffusion_figures.py), read
// off the stage's own indicator cards; the site's mark for an estimate is not used, because nothing here is one.
const u = "text-ink underline decoration-axis underline-offset-2";
const GROUPS: GaugeGroup[] = ["fast", "normal", "slow", "unscored", "other"];
const gaugeKeys = (
  <>
    {GROUPS.map((g) => <Key key={g} swatch={<Glyph group={g} />}>{GROUP_WORDS[g]}</Key>)}
    <Key swatch={<Glyph group="normal" votes={false} />}>outlined: scored, but it shares a source with a gauge already counted, so it casts no vote of its own</Key>
  </>
);
const gauge = <>A gauge is what this site calls an indicator: a published series read against a rule written down in advance.</>;

export function StageGauges({ f }: { f: DiffusionFigs["gauges"] }) {
  return (
    <Figure
      id="fig-gauges"
      title="Every gauge, stage by stage, and what it reads tonight"
      note={KIND_LABEL.chart}
      keys={gaugeKeys}
      foot={<>
        <p>One mark is one published gauge, and each links to its page. {gauge} A filled mark casts a vote toward its stage&apos;s status; gauges that read the same survey or tracker share a single vote, so the rest of them are outlined.</p>
        <p>Emerging is this site&apos;s word for a gauge that has readings but no verdict yet: its number sits between the ranges or on the line between them, its margin of error reaches across both, it rests on a single source that is not a primary one, or its only evidence is a company describing itself. A mark here does not show how large any reading is; the figure of ranges further down the page does.</p>
      </>}
      table={
        <table className="data">
          <thead><tr><th scope="col">Stage</th><th scope="col">Status</th><th scope="col">Fast</th><th scope="col">Normal</th><th scope="col">Slow</th><th scope="col">Emerging</th><th scope="col">Reads who keeps the money</th><th scope="col">Votes cast</th></tr></thead>
          <tbody>{f.rows.map((r) => (
            <tr key={r.stage}><th scope="row">{r.name}</th><td>{words(r.status)}</td><td>{r.counts.fast}</td><td>{r.counts.normal}</td><td>{r.counts.slow}</td><td>{r.counts.unscored}</td><td>{r.counts.other}</td><td>{r.votes}</td></tr>
          ))}</tbody>
        </table>
      }
    >
      <div role="group" aria-label="Each stage's gauges, one mark each, grouped by what they read" className="flex flex-col gap-4">
        {f.rows.map((r) => (
          <div key={r.stage} className="grid grid-cols-1 gap-1.5 sm:grid-cols-[13rem_minmax(0,1fr)] sm:gap-3">
            <div className="flex flex-col items-start gap-1 text-[13px] leading-tight text-ink"><Link href={`/buckets/${r.stage}`} className="hover:underline">{r.order}. {r.name}</Link><StatusChip status={r.status} /></div>
            <div>
              <div className="flex flex-wrap items-center gap-x-1 gap-y-1.5" data-marks>
                {r.dots.map((d, i) => <GaugeLink key={d.id} d={d} stop={i === 0} tip={`${d.name} · ${words(d.status)}${d.votes ? " · counts toward the stage" : ""}`} className={i && r.dots[i - 1].group !== d.group ? "ml-3" : ""} />)}
              </div>
              <div className="mt-1.5 font-mono text-[11px] text-muted">
                {GROUPS.filter((g) => r.counts[g]).map((g) => `${r.counts[g]} ${GROUP_WORDS[g].replace("reads who keeps the money, not speed", "on who keeps the money")}`).join(" · ")}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Figure>
  );
}

const ZONE_WORDS = { slow: "past normal, away from fast", normal: "inside the normal range", between: "between the two", fast: "inside the fast range", edge_normal: "on the line of the normal range", edge_fast: "on the line of the fast range" } as const;
const HELD_WORDS = { edge: "on the line between ranges", interval: "its margin of error reaches across both ranges", single: "a single source that is not a primary one", tier: "its only evidence is a company describing itself" } as const;
type BandDot = DiffusionFigs["bands"]["rows"][number]["dots"][number];
const where = (d: BandDot) => ZONE_WORDS[d.on_edge ? (`edge_${d.on_edge}` as const) : d.zone];
// why an emerging gauge carries no verdict: the evaluator's own reasons, or simply a number between the ranges
const whyNot = (d: BandDot) => (d.held.length ? d.held.map((h) => HELD_WORDS[h]).join("; ") : d.status === "emerging" && d.zone === "between" ? "its number falls between the ranges" : null);
const ZONE_TINT = { slow: "color-mix(in srgb, var(--slow) 10%, transparent)", normal: "var(--surface-2)", between: "transparent", fast: "color-mix(in srgb, var(--fast) 10%, transparent)" } as const;

export function BandStrips({ f }: { f: DiffusionFigs["bands"] }) {
  const left = f.rows.flatMap((r) => r.left_out.map((x) => ({ ...x, stage: r.name })));
  return (
    <Figure
      id="fig-bands"
      title="Where tonight's number sits between its normal range and its fast range"
      note={KIND_LABEL.chart}
      keys={<>
        {gaugeKeys}
        <Key swatch={<span className="inline-block h-2.5 w-4 bg-surface-2 ring-1 ring-grid" />}>the normal range</Key>
        <Key swatch={<span className="inline-block h-2.5 w-4 bg-fast/10 ring-1 ring-grid" />}>the fast range</Key>
      </>}
      foot={<>
        <p>Each gauge has a normal range and a fast range, fixed before the data came in: the first is what a slow, electricity-like spread would show, the second what a much quicker one would. A mark&apos;s place is the range tonight&apos;s number falls in, before the rule&apos;s checks on its evidence; its shape is the status the site has published. Between the ranges the place is to scale. Inside a range, which has no far edge, the scale is squeezed: a mark deeper in its range is further from the line, counted in widths of that gauge&apos;s own gap between the ranges, but equal steps on the page are not equal steps in the number. Height within a strip means nothing; marks are stacked so they do not overlap.</p>
        <p>A part-filled mark in a shaded range is a gauge whose number falls in that range but which the site has not scored. It is not a reading of fast or of normal. The rule holds a number back when it sits on or very near the line between ranges, when its margin of error reaches across both, when it rests on a single source that is not a primary one, or when its only evidence is a company describing itself. The table beneath says which applies to each gauge. Gauges read by direction instead of by a range are left out and listed in the table.</p>
      </>}
      table={
        <table className="data">
          <thead><tr><th scope="col">Stage</th><th scope="col">Gauge</th><th scope="col">Number the rule reads</th><th scope="col">As of</th><th scope="col">Where it sits</th><th scope="col">Published status</th><th scope="col">Why it is not scored</th></tr></thead>
          <tbody>
            {f.rows.flatMap((r) => r.dots.map((d) => (
              <tr key={d.id}><th scope="row">{r.name}</th><td><Link href={d.href} className={u}>{d.name}</Link></td><td className="num whitespace-nowrap">{fmt(d.value, d.unit)}</td><td className="num whitespace-nowrap">{d.as_of ?? "—"}</td><td>{where(d)}</td><td>{words(d.status)}</td><td>{whyNot(d) ?? "—"}</td></tr>
            )))}
            {left.map((x) => <tr key={x.id}><th scope="row">{x.stage}</th><td><Link href={`/indicators/${x.id}`} className={u}>{x.name}</Link></td><td>—</td><td>—</td><td className="text-muted">not drawn: {x.why}</td><td>—</td><td>—</td></tr>)}
          </tbody>
        </table>
      }
    >
      <Strips
        rows={f.rows} label="Each stage's gauges placed between their own normal and fast ranges"
        zones={f.zones.map((z) => ({ key: z.id, x: z.x, w: z.w, tint: ZONE_TINT[z.id], label: { slow: "slower", normal: "normal range", between: "between", fast: "fast range" }[z.id] }))}
        tip={(d) => `${d.name} · ${fmt(d.value, d.unit)} · ${where(d)} · published as ${words(d.status)}${d.held.length ? ` · not scored: ${whyNot(d)}` : ""}`}
        side={(r) => (r.left_out.length ? <>{r.dots.length} placed · {r.left_out.length} not drawn</> : <>{r.dots.length} placed</>)}
      />
    </Figure>
  );
}

export function HeadlineSeries({ f, docs }: { f: DiffusionFigs["headline"]; docs: Doc[] }) {
  const rows = f.map((h) => ({ h, d: docs.find((x) => x.id === h.id) })).filter((x): x is { h: DiffusionFigs["headline"][number]; d: Doc } => !!x.d?.chart);
  return (
    <Figure
      id="fig-headline"
      title="One gauge from each stage, over time"
      note={KIND_LABEL.chart}
      keys={<>
        <Key swatch={<svg width="10" height="10" aria-hidden><circle cx="5" cy="5" r="3.5" fill="var(--s1)" /></svg>}>a reading, linked to its record</Key>
        <Key swatch={<svg width="10" height="10" aria-hidden><circle cx="5" cy="5" r="3.5" fill="var(--surface)" stroke="var(--s1)" strokeWidth="1.5" /></svg>}>hollow: disputed; its page says why</Key>
        <Key swatch={<span aria-hidden className="inline-block h-3 w-px bg-s1/40" />}>the interval its source gives</Key>
        <Key swatch={<span className="inline-block h-2.5 w-4 bg-surface-2 ring-1 ring-grid" />}>normal range, where the rule reads the series drawn</Key>
        <Key swatch={<span className="inline-block h-2.5 w-4 bg-fast/10 ring-1 ring-grid" />}>fast range</Key>
      </>}
      foot={<>
        <p>For each stage, a single gauge, named above its panel: the one this site is most sure of among those with more than a single reading to draw, chosen from the gauges that count toward the stage&apos;s status where any of those can be drawn. A tie goes to the gauge with more records behind it. Where no gauge counts, the panel says so and the gauge drawn is one the site has not scored. Each panel has its own scale and its own span of dates, so compare shapes within a panel and not heights across panels.</p>
        <p>The shaded ranges appear only where the rule reads the very series plotted. Where it reads a fitted trend, or a single named study among several, the panel shows the readings and no range, and the gauge&apos;s own page shows what the rule reads. A hollow dot is a reading that is disputed; its page says by whom. One gauge does not speak for its stage: each panel&apos;s heading links to the stage&apos;s full list.</p>
      </>}
      table={
        <table className="data">
          <thead><tr><th scope="col">Stage</th><th scope="col">Gauge</th><th scope="col">Latest reading</th><th scope="col">As of</th><th scope="col">Status</th><th scope="col">Readings drawn</th></tr></thead>
          <tbody>{rows.map(({ h, d }) => (
            <tr key={h.id}><th scope="row">{h.name}</th><td><Link href={`/indicators/${d.id}`} className={u}>{d.name}</Link></td><td className="num whitespace-nowrap">{fmt(d.latest?.value, d.unit)}</td><td className="num whitespace-nowrap">{d.latest?.as_of ?? "—"}</td><td>{words(d.status)}</td><td>{d.chart?.n_drawn}</td></tr>
          ))}</tbody>
        </table>
      }
    >
      <div className="grid gap-x-8 gap-y-8 md:grid-cols-2">
        {rows.map(({ h, d }) => (
          <div key={h.id} className="flex min-w-0 flex-col gap-2">
            <div className="flex flex-col gap-1">
              <span className="eyebrow"><Link href={`/buckets/${h.stage}`} className="hover:underline">{h.order}. {h.name}</Link>{h.counts ? "" : " · does not count toward the stage’s status"}</span>
              <span className="flex flex-wrap items-center gap-2 text-[13px] leading-tight"><Link href={`/indicators/${d.id}`} className={`${u} font-medium`}>{d.name}</Link><StatusChip status={d.status} /></span>
              <span className="font-mono text-[11px] text-muted">latest {fmt(d.latest?.value, d.unit)} · {d.latest?.as_of}{d.chart?.y.log ? " · log scale" : ""}</span>
            </div>
            <TimePlot d={d} />
          </div>
        ))}
      </div>
    </Figure>
  );
}

const Num = ({ n, loop = false }: { n: number; loop?: boolean }) => <span className={`inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full font-mono text-[11px] ${loop ? "text-ink ring-1 ring-inset ring-ink" : "bg-ink text-surface"}`}>{n}</span>;

export function LagModel({ f }: { f: DiffusionFigs["model"] }) {
  return (
    <Figure
      id="fig-lag"
      title="Why the stages arrive one after another"
      note={KIND_LABEL.model}
      keys={<>
        <Key swatch={<LineSwatch />}>how far a stage has gone, as time passes</Key>
        <Key swatch={<LineSwatch dashed />}>the lag: the wait between a stage and the next</Key>
        <Key swatch={<span className="inline-block h-2.5 w-2.5 rounded-full bg-ink" />}>a numbered stage, named below</Key>
        <Key swatch={<span className="inline-block h-2.5 w-2.5 rounded-full ring-1 ring-inset ring-ink" />}>the last stage: the loop back to the first, not drawn</Key>
      </>}
      foot={<p>A drawing of the argument made by Arvind Narayanan and Sayash Kapoor, not of any data. The order of the stages and what holds each back are theirs, as this site&apos;s records word them. The even spacing, the gentler slope of each later curve and the equal heights are drawn for the eye and measure nothing: the drawing shows that each stage must wait for the last, not how long the wait is. The figures above and below show what is measured.</p>}
    >
      <div className="grid grid-cols-[1.25rem_minmax(0,1fr)] gap-x-2">
        <div className="relative" aria-hidden><span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-90 whitespace-nowrap font-mono text-[11px] text-muted">how far along →</span></div>
        <div role="img" aria-label="A model: the stages drawn as curves that each start later and rise more slowly than the last" className="relative h-52 border-b border-l border-axis sm:h-64">
          <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 h-full w-full overflow-visible" aria-hidden>
            <line x1={f.curves[0]?.mid.x} x2={f.curves[f.curves.length - 1]?.mid.x} y1="50" y2="50" stroke="var(--axis)" strokeWidth="2" strokeDasharray="4 3" vectorEffect="non-scaling-stroke" />
            {f.curves.map((c) => <path key={c.stage} d={c.d} fill="none" stroke="var(--s2)" strokeWidth="2" vectorEffect="non-scaling-stroke" />)}
          </svg>
          {f.lags.map((l) => <span key={l.x} aria-hidden className="absolute -translate-x-1/2 -translate-y-[1.35rem] bg-surface px-0.5 font-mono text-[11px] text-muted" style={{ left: `${l.x}%`, top: `${l.y}%` }}>lag</span>)}
          {f.curves.map((c) => <span key={c.stage} aria-hidden className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: `${c.mid.x}%`, top: `${c.mid.y}%` }}><Num n={c.order} /></span>)}
        </div>
        <div />
        <div className="pt-1.5 text-right font-mono text-[11px] text-muted" aria-hidden>time →</div>
      </div>
      <ol className="mt-4 grid gap-x-8 gap-y-3 md:grid-cols-2">
        {f.curves.map((c) => (
          <li key={c.stage} className="flex gap-2.5 text-[13px] leading-snug">
            <Num n={c.order} />
            <span><Link href={`/buckets/${c.stage}`} className={`${u} font-medium`}>{c.name}</Link><span className="text-ink-2">: {c.stock}</span><span className="mt-0.5 block text-muted">What holds it back: {c.limit}</span></span>
          </li>
        ))}
        {f.loop ? (
          <li className="flex gap-2.5 text-[13px] leading-snug md:col-span-2">
            <Num n={f.loop.order} loop />
            <span><Link href={`/buckets/${f.loop.stage}`} className={`${u} font-medium`}>{f.loop.name} (feedback into methods)</Link><span className="text-ink-2">: {f.loop.stock}</span><span className="mt-0.5 block text-muted">Not drawn as a curve: it is the loop from the last stage back to the first. What holds it back: {f.loop.limit}</span></span>
          </li>
        ) : null}
      </ol>
    </Figure>
  );
}

export function Freshness({ f }: { f: DiffusionFigs["fresh"] }) {
  return (
    <Figure
      id="fig-fresh"
      title="How old each stage's newest readings are"
      note={KIND_LABEL.chart}
      keys={<>
        {gaugeKeys}
        <Key swatch={<span className="inline-block h-3 w-0.5 bg-ink" />}>the stage&apos;s middle age (between the middle pair where the count is even)</Key>
        <Key swatch={<span className="inline-block h-3 w-3 rounded-[2px] ring-1 ring-ink" />}>framed: flagged stale, past its expected refresh</Key>
        <Key swatch={<span className="inline-block h-3 w-3 rounded-[2px] outline-dashed outline-2 outline-muted" />}>dashed frame: past its expected refresh, excused for a stated reason</Key>
      </>}
      foot={<>
        <p>Each mark is a gauge, placed by the age of its newest reading on {f.today}: fresh on the left, old on the right. The scale stretches recent weeks and squeezes old years, so that both can be read. A stage whose marks sit to the right is being read on old data, however its status reads.</p>
        <p>A gauge is flagged stale, and framed here, once its newest reading is older than two of the gaps its source usually leaves between readings, or one gap and a month where that is longer. A yearly source can therefore be well over a year old, still count toward its stage, and carry no frame: its place on the scale is the only sign. A dashed frame marks a gauge that is past that limit but excused, because it is a one-off study, a count of rare events or a projection that changes only when its source revises it; the reason is in its tip and on its page. Age is counted from the date a reading describes, not the date it was fetched. Height within a strip means nothing; marks are stacked so they do not overlap.</p>
      </>}
      table={
        <table className="data">
          <thead><tr><th scope="col">Stage</th><th scope="col">Gauges dated</th><th scope="col">Newest</th><th scope="col">Middle</th><th scope="col">Oldest</th><th scope="col">Flagged stale</th><th scope="col">Past its refresh, excused</th></tr></thead>
          <tbody>{f.rows.map((r) => (
            <tr key={r.stage}><th scope="row">{r.name}</th><td>{r.dots.length}</td><td className="num">{fmt(r.newest_days, "days")}</td><td className="num">{fmt(r.median_days, "days")}</td><td className="num">{fmt(r.oldest_days, "days")}</td><td>{r.n_stale}</td><td>{r.n_excused}</td></tr>
          ))}</tbody>
        </table>
      }
    >
      <Strips
        rows={f.rows} ticks={f.ticks} label="Each stage's gauges placed by the age of their newest reading"
        tip={(d) => `${d.name} · newest reading ${d.as_of} · ${fmt(d.age_days, "days")} old${d.stale ? " · flagged stale" : ""}${d.excused && d.why ? ` · ${d.why}` : ""}`}
        side={(r) => <><span className="block">middle age {fmt(r.median_days, "days")}</span><span className="block">oldest {fmt(r.oldest_days, "days")}</span></>}
        box={(d) => (d.stale ? "solid" : d.excused ? "dotted" : undefined)}
        extra={(r) => (r.median_x === null ? null : <div aria-hidden className="absolute -inset-y-1 w-0.5 bg-ink" style={{ left: `${r.median_x}%` }} />)}
      />
    </Figure>
  );
}

export function Sureness({ f }: { f: DiffusionFigs["sure"] }) {
  return (
    <Figure
      id="fig-sure"
      title="How sure this site says it is of each reading"
      note={KIND_LABEL.chart}
      keys={<>
        {gaugeKeys}
        {f.zones.map((z) => <Key key={z.lo} swatch={<span className="font-mono text-ink">{z.lo}–{z.hi}</span>}>{z.label}</Key>)}
      </>}
      foot={<>
        <p>Each gauge carries a confidence score set with its status, on the rubric in the key: it grades the evidence behind the reading, not the size of the reading. Marks to the left rest on thin or vague evidence; marks to the right on good evidence. The score is this site&apos;s own grading and is written into the record with a reason each time a status changes.</p>
        <p>A stage whose filled marks sit to the right has a status that rests on firm readings; a stage with only part-filled marks to the left has no firm reading yet. The scale stops short of certainty by rule. A mark on a line between bands belongs to the band on its right. Height within a strip means nothing; marks are stacked so they do not overlap.</p>
      </>}
      table={
        <table className="data">
          <thead><tr><th scope="col">Stage</th><th scope="col">Gauge</th><th scope="col">Confidence</th><th scope="col">Status</th><th scope="col">Casts a vote</th></tr></thead>
          <tbody>{f.rows.flatMap((r) => r.dots.map((d) => (
            <tr key={d.id}><th scope="row">{r.name}</th><td><Link href={d.href} className={u}>{d.name}</Link></td><td className="num">{d.confidence}</td><td>{words(d.status)}</td><td>{d.votes ? "yes" : "no"}</td></tr>
          )))}</tbody>
        </table>
      }
    >
      <Strips
        rows={f.rows} label="Each stage's gauges placed by this site's confidence in them"
        ticks={f.zones.map((z) => ({ x: z.x, label: z.tick }))}
        zones={f.zones.map((z, i) => ({ key: z.tick, x: z.x, w: z.w, tint: i % 2 ? "transparent" : "var(--surface-2)" }))}
        tip={(d) => `${d.name} · confidence ${d.confidence} · ${words(d.status)}`}
        side={(r) => <>{r.dots.length} gauges</>}
      />
    </Figure>
  );
}
