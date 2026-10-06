import Link from "next/link";
import { StartupMoneyTable } from "./BottleneckMap";
import { Figure, Key } from "./Figure";
import { KIND_LABEL, Swatch } from "./diagrams/kit";
import { BARRIER_FILL, ClaimMark, Flow, ROW_FILL, RowSquares, Square, STATE_GLYPH, UnitRow } from "./diagrams/bottlenecks";
import type { MapCount, MapDoc, OutlookState } from "@/lib/data";
import { CLAIM_WORDS, fmt } from "@/lib/format";

// The figures on /bottlenecks. Every count, share and position is laid out by bottleneck_map.figures in the export;
// this file only places it. Hatching is kept for an expectation, a model's judgement or a score the scorecard itself
// marks as low in confidence; never for a firm reading.
const link = "underline decoration-grid underline-offset-2 hover:decoration-ink";
const SCARCITY: Record<string, string> = { supply: "Short of supply: too little of the thing is made", know_how: "Short of know-how: too few people or firms can do it", money: "Short of money: too little is paid in" };
// A claim's state read beside a row, in the map's own words: "both sides expect this" would read as both expecting the row to bind.
const STATE_WORDS: Record<string, string> = { ...CLAIM_WORDS, both: "tonight's reading fits both sides" };
const FIRM = { chain: "Inputs inside the chain", outside: "Frictions outside the chain", barriers: "Narayanan and Kapoor's barriers" } as const;
const REST = { reading: "rest on a reading", low: "rest on a reading marked low in confidence", plain: "rest only on plain readings with no status", judged: "have only a model's judgement behind them", blank: "rest on neither" } as const;
const SUB = { chain: "on a firm reading", outside: "on an indicator with a status", barriers: "tied to an indicator" } as const;
// A low-confidence reading is hatched over grey, so it reads as a reading held loosely and not as a judgement (hatched over white).
const SEG_GROUND = { reading: "var(--s1)", low: "var(--s3)", plain: "var(--surface)", judged: undefined, blank: "var(--surface-2)" } as const;

// The page's summary: the path as a row of equal boxes, with what is scored tight and what is expected to bind
// placed at the stage it acts on. The boxes are equal because nothing here measures how much passes through a stage.
export function BindingPath({ doc }: { doc: MapDoc }) {
  const f = doc.figures;
  const low = f.stages.some((s) => s.now.some((r) => r.low));
  return (
    <Figure
      id="fig-path"
      title="Each stage of AI&apos;s spread: what is scored tight tonight, and what a writer expects to bind"
      note={`${KIND_LABEL.model} · tonight's readings placed on it`}
      keys={<>
        <Key swatch={<span aria-hidden className="inline-block h-1.5 w-5 bg-tight-5" />}>a stage where at least one input is scored tight or severe tonight</Key>
        <Key swatch={<span aria-hidden className="inline-block h-1.5 w-5 bg-s3" />}>a stage where some rows are scored and none is tight</Key>
        <Key swatch={<span aria-hidden className="inline-block h-1.5 w-5 bg-surface ring-1 ring-inset ring-axis" />}>a stage where no row is scored: unmeasured on this scale, which is not the same as free</Key>
        <Key swatch={<Square fill="var(--tight-5)" />}>an input scored tight or severe</Key>
        {low ? <Key swatch={<Square fill="var(--tight-5)" hatched />}>a score this site marks as low in confidence, hatched as on the scorecard</Key> : null}
        <Key swatch={<Square fill="var(--s1)" hatched />}>a row a named writer, or this site, expects to bind at this stage; the name beside it says whose claim it is</Key>
      </>}
      foot={<>
        <p>AI reaches everyday use in stages, each feeding the next: a model is invented, built into products, taken up by people and firms, and then firms and laws change around it. A stage moves no faster than the scarcest thing it needs, which is what binding means. The boxes are the same width on purpose: nothing on this site measures how much passes through a stage, so the drawing marks where something binds and never how narrow the passage is.</p>
        <p>The stage names are the map&apos;s. Tight means the input is short of what is wanted, on this site&apos;s scorecard, which runs from slack to severe. An input is listed as tight where its score there is tight or severe; a row is listed as expected where a claim on file says it will bind at that stage, with the claim&apos;s maker after it, and a claim failing its own test tonight says so. Many rows carry no tightness score at all, and frictions outside the chain never do, so a stage with a grey or an outlined band is not known to be free: most or all of it is not scored. Press a name for the row&apos;s entry.</p>
      </>}
    >
      <div role="group" aria-label="The stages of AI's spread in order, with what binds at each" className="grid grid-cols-1 gap-2 md:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr] md:items-stretch">
        {f.stages.map((s, k) => (
          <div key={s.id} className="contents">
            {k ? <Flow /> : null}
            <section className="flex flex-col bg-surface ring-1 ring-grid">
              <div aria-hidden className={`h-1.5 ${s.now.length ? "bg-tight-5" : s.scored ? "bg-s3" : "bg-surface ring-1 ring-inset ring-axis"}`} />
              <div className="flex flex-col gap-2 p-3">
                <div>
                  <span className="eyebrow">Stage <span className="num">{s.n}</span></span>
                  <h3 className="font-sans font-semibold text-[14px] leading-tight text-ink">{s.label}</h3>
                  <span className="block text-[11px] leading-snug text-muted"><span className="num">{s.total}</span> rows of the map act here; <span className="num">{s.scored}</span> of them carry a tightness score</span>
                </div>
                <div className="text-[12.5px] leading-snug">
                  <span className="block text-[11px] text-ink-2">Scored tight or severe</span>
                  {s.now.length ? <ul className="mt-0.5 flex flex-col gap-0.5">{s.now.map((r) => <li key={r.id} className="flex items-baseline gap-1.5"><span className="translate-y-px"><Square fill="var(--tight-5)" hatched={r.low} /></span><span><a href={r.href} className={link}>{r.name}</a>{r.low ? <span className="text-muted"> · low confidence</span> : null}</span></li>)}</ul> : <span className="text-muted">{s.scored ? "none of the scored rows is tight; the rest are not scored" : "not scored: no row here carries a tightness score, so nothing can show as tight"}</span>}
                </div>
                <div className="text-[12.5px] leading-snug">
                  <span className="block text-[11px] text-ink-2">Expected to bind here</span>
                  {s.expected.length ? <ul className="mt-0.5 flex flex-col gap-0.5">{s.expected.map((x) => <li key={x.id} className="flex items-baseline gap-1.5"><span className="translate-y-px"><Square fill="var(--s1)" hatched /></span><span><a href={x.href} className={link}>{x.name}</a><span className="text-[11.5px] text-muted"> · {x.acts ? null : "placed here by "}{x.writers.map((w, j) => <span key={`${w.who}-${w.state}`}>{j ? " · " : null}{w.who}{w.state === "failing" ? <span className="text-ink"> ({STATE_GLYPH.failing} failing its test)</span> : null}</span>)}{x.acts ? null : "; the map itself does not"}</span></span></li>)}</ul> : <span className="text-muted">no claim on file</span>}
                </div>
              </div>
            </section>
          </div>
        ))}
      </div>
    </Figure>
  );
}

function Panel({ label, children }: { label: string; children: React.ReactNode }) {
  return <section className="flex flex-col gap-2"><h3 className="eyebrow">{label}</h3>{children}</section>;
}

// The matrix collapsed three ways: by stage, by part of the chain, and by kind of scarcity. One square is one row.
export function MapCounted({ doc }: { doc: MapDoc }) {
  const f = doc.figures;
  const classes = Object.keys(ROW_FILL).filter((c) => f.tally[c]);
  const low = f.sections.some((s) => s.units.some((u) => u.low));
  const counts = (name: string, p: MapCount) => <tr key={name}><th scope="row">{name}</th>{classes.map((c) => <td key={c} className="num">{p.counts[c] ?? 0}</td>)}<td className="num">{p.total}</td></tr>;
  return (
    <Figure
      id="fig-counted"
      title="The map counted: how many rows act on each stage, and how each reads tonight"
      note={KIND_LABEL.chart}
      keys={<>
        {classes.map((c) => <Key key={c} swatch={<Square {...ROW_FILL[c]} />}>{ROW_FILL[c].label}</Key>)}
        {low ? <Key swatch={<Square fill="var(--tight-5)" hatched />}>a score this site marks as low in confidence, hatched as on the scorecard</Key> : null}
      </>}
      foot={<>
        <p>One square is one row of the map above; press a square for the row&apos;s entry. A row that acts on more than one stage is drawn once at each, so the stage rows add up to more than the map has rows; in the other panels each row is drawn once.</p>
        <p>The chain is the run of inputs AI is made from, chips to applications; a friction outside it is anything else that slows AI&apos;s spread, such as law or habit. An input inside the chain carries this site&apos;s tightness score where published figures support one, and stays an open square where they do not. A friction outside the chain is read by indicators on a different scale, so it is drawn grey and never placed on the orange one: grey does not mean loose. The last panel covers inputs only, because the kind of scarcity is a field of the scorecard that frictions do not have.</p>
      </>}
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">Rows</th>{classes.map((c) => <th key={c} scope="col">{ROW_FILL[c].label}</th>)}<th scope="col">All</th></tr></thead>
          <tbody><tr><th scope="rowgroup" colSpan={classes.length + 2}>By stage</th></tr>{f.stages.map((s) => counts(s.label, s))}</tbody>
          <tbody><tr><th scope="rowgroup" colSpan={classes.length + 2}>By part of the map</th></tr>{f.sections.map((s) => counts(`${s.group}: ${s.name}`, s))}</tbody>
          <tbody><tr><th scope="rowgroup" colSpan={classes.length + 2}>By kind of scarcity</th></tr>{f.kinds.map((k) => counts(SCARCITY[k.id] ?? k.id, k))}</tbody>
        </table>
      }
    >
      <div className="flex flex-col gap-6">
        <Panel label="By stage: what would slow each stage if it ran short">
          {f.stages.map((s) => <UnitRow key={s.id} name={s.label} total={s.total}><RowSquares units={s.units} /></UnitRow>)}
        </Panel>
        <Panel label="By part of the map: where the rows sit">
          {f.sections.map((s) => <UnitRow key={s.id} name={s.name} sub={s.group} total={s.total}><RowSquares units={s.units} /></UnitRow>)}
        </Panel>
        <Panel label="By kind of scarcity, inputs inside the chain only">
          {f.kinds.map((k) => <UnitRow key={k.id} name={SCARCITY[k.id] ?? k.id} total={k.total}><RowSquares units={k.units} /></UnitRow>)}
        </Panel>
      </div>
    </Figure>
  );
}

// How much of the page rests on a reading and how much on a model's judgement (drawn in the judgement's pattern).
export function MapFirmness({ doc }: { doc: MapDoc }) {
  const f = doc.figures;
  const n = (b: (typeof f.firm)[number], key: string) => b.segs.find((s) => s.key === key)?.n;
  const has = (key: string) => f.firm.some((b) => b.segs.some((s) => s.key === key && Boolean(s.n)));
  return (
    <Figure
      id="fig-firm"
      title="How much of this page rests on a reading, and how much has only a model&apos;s judgement behind it"
      note={`${KIND_LABEL.chart} · hatched is a model's judgement, not a reading`}
      keys={<>
        <Key swatch={<Swatch fill="var(--s1)" />}>rests on a reading: for an input, a score built from published figures; for a friction, at least one published indicator with a status</Key>
        {has("low") ? <Key swatch={<span aria-hidden className="inline-block h-2.5 w-4 hatch ring-1 ring-inset ring-current" style={{ color: "var(--s1)", backgroundColor: SEG_GROUND.low }} />}>rests on a reading this site marks as low in confidence</Key> : null}
        {has("plain") ? <Key swatch={<span aria-hidden className="inline-block h-2.5 w-4 ring-[1.5px] ring-inset ring-current" style={{ color: "var(--s1)" }} />}>rests only on plain readings with no status: a figure exists, but nothing here says whether it is fast or slow</Key> : null}
        <Key swatch={<span aria-hidden className="inline-block h-2.5 w-4 hatch ring-1 ring-inset ring-current" style={{ color: "var(--s1)" }} />}>no reading: only a model&apos;s judgement, in words, is on file; it is labelled as one wherever it is printed</Key>
        {has("blank") ? <Key swatch={<span className="inline-block h-2.5 w-4 bg-surface-2 ring-1 ring-inset ring-axis" />}>neither a reading nor a judgement</Key> : null}
      </>}
      foot={<>
        <p>Each bar is the whole of one list. An input counts as read when this site scores it. A friction counts as read when at least one published indicator stands behind its row, and as plainly read when only figures with no status do; neither says the indicator measures the friction well. One of Narayanan and Kapoor&apos;s barriers counts as read when an indicator is tied to that barrier itself. Being read says a figure exists, not that the figure is strong.</p>
        {f.made_by ? <p>The judgements were written by an AI model (Anthropic&apos;s {f.made_by.model}) on {f.made_by.date}. The only review on record is by {f.made_by.reviewed_by}. Put plainly, a model checked a model, and no person has checked every judgement. They are opinions in words and move no score. For an input with no score the judgement is printed on <Link href="/argument/migration" className={link}>the tightness scorecard</Link>, not on the map above; for a barrier it is printed beside the barrier in the folded list at the foot of this page.</p> : null}
      </>}
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">List</th><th scope="col">On a reading</th><th scope="col">On a reading marked low in confidence</th><th scope="col">On plain readings with no status</th><th scope="col">Only a model&apos;s judgement</th><th scope="col">On neither</th><th scope="col">All</th></tr></thead>
          <tbody>{f.firm.map((b) => <tr key={b.id}><th scope="row">{FIRM[b.id]}</th>{b.segs.map((s) => <td key={s.key} className="num">{s.n}</td>)}<td className="num">{b.total}</td></tr>)}</tbody>
        </table>
      }
    >
      <div role="group" aria-label="Each list on this page, split by what stands behind its entries" className="flex flex-col gap-3">
        {f.firm.map((b) => (
          <div key={b.id} className="grid grid-cols-1 gap-1 sm:grid-cols-[14rem_1fr] sm:items-center sm:gap-3">
            <div className="text-[13px] leading-tight text-ink">{FIRM[b.id]}<span className="block font-mono text-[11px] text-muted">{n(b, "reading")} of {b.total} {SUB[b.id]}</span></div>
            <div className="relative h-5 w-full">
              {b.segs.filter((s) => s.n > 0).map((s) => <div key={s.key} title={`${FIRM[b.id]}: ${s.n} ${REST[s.key]}`} className={`absolute inset-y-0 ${s.key === "low" || s.key === "judged" ? "hatch ring-1 ring-inset ring-current" : s.key === "plain" ? "ring-[1.5px] ring-inset ring-current" : s.key === "blank" ? "ring-1 ring-inset ring-axis" : ""}`} style={{ left: `${s.x}%`, width: `${s.w}%`, color: s.key === "blank" ? undefined : "var(--s1)", backgroundColor: SEG_GROUND[s.key] }} />)}
            </div>
          </div>
        ))}
      </div>
    </Figure>
  );
}

// Every claim listed under a row, as one mark in the state the export gives it tonight.
export function ClaimStates({ doc }: { doc: MapDoc }) {
  const c = doc.figures.claims;
  return (
    <Figure
      id="fig-claims"
      title="How each expectation placed on the map is faring tonight"
      note={KIND_LABEL.chart}
      keys={<>
        {c.states.map((s) => <Key key={s} swatch={<span aria-hidden className={`text-[14px] leading-none ${s === "untestable" ? "text-muted" : "text-ink"}`}>{STATE_GLYPH[s]}</span>}>{STATE_WORDS[s]}</Key>)}
        <Key swatch={<span aria-hidden className="inline-block h-3.5 w-3.5 ring-1 ring-inset ring-axis" />}>boxed: this site&apos;s own claim, or its extension of an author&apos;s</Key>
      </>}
      foot={<>
        <p>One mark is one claim listed under a row in the entries below: a statement by a named writer, or by this site, about what will happen on that row, with a test this site runs again each night where a published series allows one. Not every claim says the row will bind; some say it will not. A claim that names more than one row is drawn under each row, so there are more marks than claims; the counts above count each claim once.</p>
        <p>A boxed mark is this site&apos;s own claim, or its extension of a named writer&apos;s, so there the site is marking its own work; an unboxed mark is a named writer&apos;s claim, tested by this site.</p>
        <p>A claim that cannot be tested yet is not a claim that is wrong: no series on file can settle it today. A reading that fits both sides means the claim and its rival both expect what is seen so far. Press a mark for the claim and its test.</p>
      </>}
      tableLabel="The claims, row by row"
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">Row</th><th scope="col">Who</th><th scope="col">Claim</th><th scope="col">Tonight</th></tr></thead>
          <tbody>{c.rows.map((r) => c.states.map((s) => r.cells[s].map((m, k) => (
            <tr key={`${r.id}-${s}-${k}`}><th scope="row">{r.name}</th><td>{m.who}</td><td className="min-w-[16rem]"><Link href={m.href} prefetch={false} className={link}>{m.text}</Link></td><td className="whitespace-nowrap">{STATE_WORDS[s]}</td></tr>
          ))))}</tbody>
        </table>
      }
    >
      <div className="flex flex-col gap-4">
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-4">
          {c.states.map((s) => (
            <div key={s} className="flex flex-col border-l-2 border-grid pl-2.5">
              <dd className="num text-xl leading-none text-ink"><span aria-hidden className={`mr-1.5 text-[15px] ${s === "untestable" ? "text-muted" : ""}`}>{STATE_GLYPH[s]}</span>{c.tally[s]}</dd>
              <dt className="mt-1 text-[11.5px] leading-tight text-ink-2">{STATE_WORDS[s]}</dt>
            </div>
          ))}
        </dl>
        <div role="group" aria-label="Each row that carries a claim, with one mark for each claim" className="flex flex-col gap-1.5 border-t border-grid pt-3">
          {c.rows.map((r) => (
            <div key={r.id} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 sm:grid-cols-[14rem_1fr]">
              <a href={r.href} className="text-[13px] leading-tight text-ink hover:underline decoration-grid underline-offset-2">{r.name}</a>
              <span className="flex flex-wrap items-center gap-0.5 max-sm:justify-end">{c.states.map((s: OutlookState) => r.cells[s].map((m, k) => <ClaimMark key={`${s}-${k}`} m={m} state={s} words={STATE_WORDS[s]} />))}</span>
            </div>
          ))}
        </div>
      </div>
    </Figure>
  );
}

// The startup-money table as a picture: one dot per sub-layer on one ratio scale, with the table folded beneath.
export function StartupMoney({ doc }: { doc: MapDoc }) {
  const m = doc.figures.money;
  const lines = m.ticks.map((t) => <span key={t.x} aria-hidden className="absolute inset-y-0 w-px bg-grid" style={{ left: `${t.x}%` }} />);
  return (
    <Figure
      id="fig-money"
      title="Where startup money went, sub-layer by sub-layer"
      note={KIND_LABEL.chart}
      keys={<>
        <Key swatch={<span aria-hidden className="inline-block h-2.5 w-2.5 rounded-full bg-s1" />}>money startups in the sub-layer raised by selling new shares, over the latest year on file{m.as_of ? `, to ${m.as_of}` : ""}</Key>
        <Key swatch={<span aria-hidden className="inline-block h-2.5 w-5 border border-dashed border-axis" />}>no round on file in that year; the sub-layer is left off the scale, which is not the same as nothing raised</Key>
      </>}
      foot={<>
        <p>The scale multiplies as it goes{m.steps === "uneven" ? null : <>: each labelled line is the same multiple of the one before{m.steps === "even_but_last" ? ", apart from the last, which only closes the scale" : null}</>}. Equal distances are therefore equal multiples, not equal amounts, and the gap between the frontier labs and every other sub-layer is far wider than it looks. Each firm is counted once, in its main sub-layer.</p>
        <p>Startup money only. The physical build-out is paid for with big companies&apos; capital spending and debt, which this figure misses; the map&apos;s capital row reads that spending. Money arriving does not show that an input is short, and none arriving does not show that it is plentiful.</p>
      </>}
      tableLabel="The numbers: firms tracked and money raised, by sub-layer"
      table={<StartupMoneyTable doc={doc} />}
    >
      <div role="group" aria-label="Money raised by startups in each sub-layer, on one scale that multiplies as it goes" className="flex flex-col gap-2.5 sm:gap-1.5">
        {m.rows.map((r) => (
          <div key={r.id} className="grid grid-cols-1 gap-1 sm:grid-cols-[17rem_1fr] sm:items-center sm:gap-3">
            <div className="text-[13px] leading-tight text-ink"><Link href={`/stack/${r.id}`} prefetch={false} className="hover:underline decoration-grid underline-offset-2">{r.name}</Link>
              <span className="block text-[11px] text-muted"><span className="num">{r.firms}</span> firms tracked · the map&apos;s inputs here: {r.inputs.join(", ")}</span>
            </div>
            <div className="px-2">
              {r.venture && r.x !== null ? (
                <div className="relative h-6">
                  {lines}
                  <span aria-hidden className="absolute inset-x-0 top-1/2 h-px bg-grid" />
                  <Link href={r.venture.href} prefetch={false} title={`${r.name}: ${fmt(r.venture.value, "USD")} raised in the year to ${r.venture.as_of}`} className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2" style={{ left: `${r.x}%` }}>
                    <span className="block h-2.5 w-2.5 rounded-full bg-s1" />
                    <span className={`num absolute top-1/2 -translate-y-1/2 whitespace-nowrap bg-surface px-0.5 text-[11.5px] text-ink ${r.flip ? "right-full mr-1" : "left-full ml-1"}`}>{fmt(r.venture.value, "USD")}</span>
                  </Link>
                </div>
              ) : <div className="flex h-6 items-center border border-dashed border-axis px-2 text-[11.5px] text-muted">no round on file: not placed on the scale</div>}
            </div>
          </div>
        ))}
        <div aria-hidden className="grid grid-cols-1 sm:grid-cols-[17rem_1fr] sm:gap-3">
          <span className="max-sm:hidden" />
          <div className="px-2"><div className="relative h-4">{m.ticks.map((t, k) => <span key={t.x} className={`num absolute top-0 text-[10.5px] text-muted ${k === 0 ? "" : k === m.ticks.length - 1 ? "-translate-x-full" : "-translate-x-1/2"}`} style={{ left: `${t.x}%` }}>{t.label}</span>)}</div></div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-[17rem_1fr] sm:gap-3">
          <span className="max-sm:hidden" />
          <p className="px-2 text-[10.5px] leading-snug text-muted">money raised in the year, in US dollars; {m.steps === "uneven" ? "equal distances to the right multiply the amount by the same factor" : "each labelled step to the right multiplies the amount by the same factor"}{m.steps === "even_but_last" ? ", except the last line, which only closes the scale" : null}</p>
        </div>
      </div>
    </Figure>
  );
}

// Narayanan and Kapoor's barriers, one square each: read by an indicator, or judged by a model, family by family.
export function BarrierFamilies({ doc }: { doc: MapDoc }) {
  const f = doc.figures;
  return (
    <Figure
      id="fig-families"
      title="Narayanan and Kapoor&apos;s barriers by family: which an indicator reads, and what a model judges of the rest"
      note={`${KIND_LABEL.chart} · hatched is a model's judgement, not a reading`}
      keys={<>
        <Key swatch={<Square {...BARRIER_FILL.read} />}>a barrier that an indicator on this site is tied to</Key>
        {f.judged_words.map((w) => <Key key={w.id} swatch={<Square {...(BARRIER_FILL[w.id] ?? BARRIER_FILL.blank)} />}>no indicator; a model&apos;s judgement: {w.label}</Key>)}
      </>}
      foot={<>
        <p>One square is one barrier named in Narayanan and Kapoor&apos;s essays, grouped by the family the map gives a row to; press a square for the barrier in the folded list below. A dark square says an indicator is tied to that barrier, not what the indicator reads; its status is beside the barrier in the list.</p>
        {f.made_by ? <p>Every hatched square is one AI model&apos;s opinion, not evidence{f.judged_mostly ? ": most of this figure is hatched" : null}{f.judged_mostly && f.judged_top_mostly ? <>, and most of the hatching says &lsquo;{f.judged_words[0].label}&rsquo;, which is that model&apos;s view and has not been checked against any series</> : null}. A hatched square is a judgement, not a reading, and its grey says which word the model chose, never how tight anything measures. The model (Anthropic&apos;s {f.made_by.model}) wrote each in words on {f.made_by.date}, from this site&apos;s readings where it had any and otherwise from its own general knowledge. The only review on record is by {f.made_by.reviewed_by}. Put plainly, a model checked a model, and no person has checked every judgement.</p> : null}
        <p>A family&apos;s row on the map can also be read by an indicator, or by a plain figure with no status, that is tied to the family as a whole and to none of its barriers; so a family with no dark square here can still show as measured on the map.</p>
      </>}
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">Family</th><th scope="col">Tied to an indicator</th>{f.judged_words.map((w) => <th key={w.id} scope="col">A model judges: {w.label}</th>)}<th scope="col">All</th></tr></thead>
          <tbody>{f.families.map((x) => <tr key={x.id}><th scope="row">{x.name}</th><td className="num">{x.counts.read ?? 0}</td>{f.judged_words.map((w) => <td key={w.id} className="num">{x.counts[w.id] ?? 0}</td>)}<td className="num">{x.total}</td></tr>)}</tbody>
        </table>
      }
    >
      <div className="flex flex-col gap-2.5">
        {f.families.map((x) => (
          <UnitRow key={x.id} name={<a href={x.href} className="hover:underline decoration-grid underline-offset-2">{x.name}</a>} total={x.total}>
            {x.units.map((u) => <a key={u.id} href={u.href} title={u.label ? `${u.title}. A model's judgement: ${u.label}` : `${u.title}. Tied to an indicator`} className="flex hover:opacity-70"><Square {...(BARRIER_FILL[u.cls] ?? BARRIER_FILL.blank)} /><span className="sr-only">{u.title}: {u.label ? `a model's judgement, ${u.label}` : "tied to an indicator"}</span></a>)}
          </UnitRow>
        ))}
      </div>
    </Figure>
  );
}
