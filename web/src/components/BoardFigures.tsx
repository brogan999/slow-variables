import Link from "next/link";
import { Inline } from "@/components/Essay";
import { Figure, Key } from "@/components/Figure";
import { LEAN_FILL, LeanSplit, MarkRows, WORD_FILL, WordSwatch } from "@/components/diagrams/board";
import { KIND_LABEL, ShareBars, Swatch } from "@/components/diagrams/kit";
import { type BoardDoc, type BoardMark, outlook, type Word } from "@/lib/data";

// The predictions board's figures. Every count and position is the export's (src/ai_tracker/board.py).
const labels = (b: BoardDoc) => Object.fromEntries(b.words.map((w) => [w.id, w.label])) as Record<Word, string>;
// Too early is hollow wherever it is drawn: in a bar it is the surface with a muted line round it.
const LINE = "linear-gradient(var(--muted) 0 0)";
const HOLLOW = `${LINE} top / 100% 1px no-repeat, ${LINE} bottom / 100% 1px no-repeat, ${LINE} left / 1px 100% no-repeat, ${LINE} right / 1px 100% no-repeat, var(--surface)`;
const BAR_FILL = { ...WORD_FILL, too_early: HOLLOW };
// A key entry for each word the figure draws, and none for a word with no mark in it.
const wordKeys = (b: BoardDoc, drawn: Partial<Record<Word, number>>[], bars = false) => b.words.filter((w) => drawn.some((c) => c[w.id])).map((w) => <Key key={w.id} swatch={bars ? <span className="inline-block h-2.5 w-4" style={{ background: BAR_FILL[w.id] }} /> : <WordSwatch word={w.id} />}>{w.label.toLowerCase()}</Key>);
const mark = (m: BoardMark, label: Record<Word, string>) => ({ key: m.key, word: m.word, href: m.href, tip: `${m.who}: ${label[m.word].toLowerCase()}${m.settles ? `, window closes ${m.settles}` : ""}`, framed: m.due });

// The numbers under a chart: one row for each thing drawn, one column for each word.
function Counts({ head, cols, rows, all = "All" }: { head: string; cols: { id: string; label: string }[]; rows: { name: string; counts: Record<string, number>; total?: number }[]; all?: string }) {
  return (
    <table className="data">
      <thead><tr><th scope="col">{head}</th>{cols.map((c) => <th key={c.id} scope="col">{c.label}</th>)}<th scope="col">{all}</th></tr></thead>
      <tbody>{rows.map((r) => <tr key={r.name}><th scope="row">{r.name}</th>{cols.map((c) => <td key={c.id}>{r.counts[c.id]}</td>)}<td>{r.total}</td></tr>)}</tbody>
    </table>
  );
}

// Which forecast each mark is, in words, so nothing is known only by hovering: the row it sits in, then its line.
function MarkList({ b, groups }: { b: BoardDoc; groups: { name: string; marks: BoardMark[] }[] }) {
  const label = labels(b);
  const row = new Map(b.folios.flatMap((f) => f.rows).map((r) => [`${r.kind}-${r.id}`, r]));
  const o = outlook();
  return (
    <div className="mt-4 flex min-w-[16rem] flex-col gap-3 text-[13px] leading-snug">
      <p className="eyebrow">Which forecast each mark is, in the order drawn</p>
      {groups.map((g) => (
        <div key={g.name}>
          <p className="font-medium text-ink">{g.name}</p>
          <ol className="mt-1 flex flex-col gap-1.5 text-ink-2">
            {g.marks.map((m) => (
              <li key={m.key} className="grid grid-cols-[0.75rem_minmax(0,1fr)] items-baseline gap-x-2">
                <span className="mt-1 flex self-start"><WordSwatch word={m.word} /></span>
                <span>
                  <span className="text-ink"><Inline text={row.get(m.key)?.line ?? ""} facts={o.facts} tests={o.tests} /></span>{" "}
                  <span className="text-muted">{m.who} · {label[m.word].toLowerCase()}{m.settles ? <> · window closes {m.settles}{m.due ? ", already passed" : ""}</> : null} · </span>
                  <Link href={m.href} prefetch={false} className="underline decoration-grid underline-offset-2 hover:text-ink">record</Link>
                </span>
              </li>
            ))}
          </ol>
        </div>
      ))}
    </div>
  );
}

export function TallyBars({ b }: { b: BoardDoc }) {
  const label = labels(b);
  return (
    <Figure
      id="fig-tally"
      title="How many forecasts in each section are happening, not happening, or still too early to tell"
      note={KIND_LABEL.chart}
      keys={wordKeys(b, [b.tally], true)}
      foot={<p>Each bar is every forecast in that section, split by tonight&apos;s word; the count beside a name is how many forecasts the bar holds. A bar shows shares, so a short section and a long one look alike: read the counts in the table. The words are this site&apos;s reading on {b.as_of}, not a final verdict.</p>}
      table={<Counts head="Section" cols={b.words} rows={b.figures.sections.map((s) => ({ name: s.label, counts: s.counts, total: s.n }))} />}
    >
      <ShareBars
        label="Each section's forecasts, split by tonight's word"
        rows={b.figures.sections.map((s) => ({
          name: s.label, note: `${s.n}`,
          segs: s.bar.map((x) => ({ key: x.word, x: x.x, w: x.w, fill: BAR_FILL[x.word], tip: `${s.label}: ${x.n} ${label[x.word].toLowerCase()}` })),
        }))}
      />
    </Figure>
  );
}

const step = "flex flex-col gap-1 border border-axis bg-surface-2 p-3";
const arrow = "self-center text-center font-mono text-muted";

// How a forecast moves through the board. The steps are this site's method; the counts are tonight's.
export function BoardFlow({ b }: { b: BoardDoc }) {
  const f = b.figures.flow;
  return (
    <Figure
      id="fig-flow"
      title="How a forecast gets its word"
      note="A drawing of the method, not a measurement, with tonight's counts"
      foot={<p>The boxes draw the steps this site follows, not a measurement; the counts in them are the board&apos;s on {b.as_of}. A forecast moves right when it is scored and can move back if what it was scored on goes stale. A model&apos;s lean sits beside a forecast that is too early to tell and never changes its word.</p>}
    >
      <ol className="grid gap-2 md:grid-cols-[minmax(0,1fr)_1.5rem_minmax(0,1fr)_1.5rem_minmax(0,1.6fr)] md:items-center">
        <li className={step}>
          <span className="eyebrow">Stated</span>
          <span className="num text-2xl leading-none text-ink">{f.stated}</span>
          <span className="text-[13px] leading-snug text-ink-2">Someone writes a forecast down: a lab, a named writer, or this site.</span>
        </li>
        <li aria-hidden className={arrow}><span className="md:hidden">↓</span><span className="max-md:hidden">→</span></li>
        <li className={step}>
          <span className="eyebrow">What would settle it</span>
          <span className="text-[13px] leading-snug text-ink-2">This site says what would settle it: a reading it takes itself, or, for someone else&apos;s dated claim, an outside check.</span>
        </li>
        <li aria-hidden className={arrow}><span className="md:hidden">↓</span><span className="max-md:hidden">→</span></li>
        <li className="grid gap-2">
          <div className="flex flex-col gap-1.5 border border-ink bg-surface p-3">
            <span className="eyebrow">Scored</span>
            <span className="num text-2xl leading-none text-ink">{f.tested}</span>
            <ul className="flex flex-col gap-1 text-[13px] leading-snug text-ink-2">
              {b.words.filter((w) => w.id !== "too_early").map((w) => (
                <li key={w.id} className="grid grid-cols-[0.75rem_minmax(0,1fr)] items-baseline gap-x-2"><span className="mt-1 flex self-start"><WordSwatch word={w.id} /></span><span><span className="text-ink">{w.label}.</span> {w.meaning}</span></li>
              ))}
            </ul>
          </div>
          <div className="flex flex-col gap-1.5 border border-dashed border-axis p-3">
            <span className="eyebrow">Not scored yet</span>
            <span className="num text-2xl leading-none text-ink">{f.too_early}</span>
            <span className="grid grid-cols-[0.75rem_minmax(0,1fr)] items-baseline gap-x-2 text-[13px] leading-snug text-ink-2"><span className="mt-1 flex self-start"><WordSwatch word="too_early" /></span><span><span className="text-ink">{b.words.find((w) => w.id === "too_early")?.label}.</span> {b.words.find((w) => w.id === "too_early")?.meaning}</span></span>
            {b.judged ? <span className="grid grid-cols-[0.75rem_minmax(0,1fr)] items-baseline gap-x-2 text-[13px] leading-snug text-ink-2"><span className="hatch mt-1 h-3 w-3 self-start text-s1" style={{ boxShadow: "inset 0 0 0 1px currentColor" }} /><span>A model&apos;s judgement, not a reading: it leans one way or the other on <span className="num text-ink">{f.leaned}</span> of these, and on <span className="num text-ink">{f.unleaned}</span> it gives none.</span></span> : null}
          </div>
        </li>
      </ol>
    </Figure>
  );
}

export function SourceMarks({ b }: { b: BoardDoc }) {
  const label = labels(b);
  const rows = b.figures.sources;
  const writers = rows.find((s) => s.id === "writers");
  return (
    <Figure
      id="fig-sources"
      title="How the scored forecasts read, by where each came from"
      note={KIND_LABEL.chart}
      keys={wordKeys(b, rows.map((s) => s.counts))}
      foot={<p>One mark is one forecast that has been scored; follow a mark to its record. Forecasts still too early to tell are counted at the end of each row, not drawn. Read this before comparing rows: the families are scored by different rules. A dated claim by someone else is scored on track or behind, so the worst it can read is slower than said, even when its date passed long ago; it has no word for wrong. A claim tested nightly can fail its test and read not happening, whoever made it{writers && !writers.counts.not_happening ? "; tonight none of the named writers' does" : ""}. A warning sign is the reverse of a forecast: not happening there means the thing that would prove this site&apos;s argument wrong has not shown up. So the rows are not a ranking and no rate is drawn. Each mark is named in the table below.</p>}
      table={<><Counts head="Where it came from" cols={b.words} rows={rows.map((s) => ({ name: s.label, counts: { ...s.counts, too_early: s.too_early }, total: s.n }))} /><MarkList b={b} groups={rows.map((s) => ({ name: s.label, marks: s.marks }))} /></>}
      tableLabel="The numbers, and which forecast each mark is"
    >
      <MarkRows
        wide
        label="Scored forecasts, one mark each, by the family the forecast came from"
        rows={rows.map((s) => ({ key: s.id, name: s.label, marks: s.marks.map((m) => mark(m, label)), tail: <>and {s.too_early} too early to tell{s.id === "ledger" ? "; this family has no word for wrong" : ""}</> }))}
      />
    </Figure>
  );
}

export function LeanBars({ b }: { b: BoardDoc }) {
  const fig = b.figures.leans;
  if (!fig || !b.leans || !b.judged) return null;
  const name = Object.fromEntries(b.leans.map((w) => [w.id, w.label]));
  return (
    <Figure
      id="fig-leans"
      title="Which way a model leans on the forecasts that are too early to tell"
      note="A model's judgements, not readings; the model is Anthropic's"
      keys={<>{b.leans.map((w) => <Key key={w.id} swatch={<span style={{ color: LEAN_FILL[w.id], boxShadow: "inset 0 0 0 1px currentColor" }} className="flex"><Swatch fill={LEAN_FILL[w.id]} hatched /></span>}>{w.label}</Key>)}<Key swatch={<span className="inline-block h-3 w-px bg-ink" />}>the centre: true to its left, false to its right</Key></>}
      foot={<p>Every bar here is hatched because it draws a judgement, not a reading. The judge is {b.judged.model}, a model made by Anthropic; some of these forecasts are about Anthropic and its rivals, and no person reviewed each lean, so treat the leans on those forecasts with extra care. It gave each lean on {b.judged.date}, and a lean changes no word above. A bar is the shares of that section&apos;s leaned-on forecasts; the numbers at its ends count the forecasts leaning true and leaning false, and the count beside a name is how many the bar holds. Bars are shares, so a section with few leans can draw the longest bar: read the counts. Forecasts with no lean are in the table, not drawn.</p>}
      table={<Counts head="Section" all="with a lean" cols={[...b.leans, { id: "none", label: "no lean given" }]} rows={fig.rows.map((r) => ({ name: r.label, counts: { ...r.counts, none: r.unjudged }, total: r.n }))} />}
    >
      <LeanSplit
        centre={fig.centre}
        ends={["leaning true", "leaning false"]}
        label="A model's leans on forecasts that are too early to tell, by section"
        rows={fig.rows.map((r) => ({
          key: r.id, name: r.label, note: `${r.n}`, left: r.true, right: r.false,
          segs: r.bar.map((s) => ({ key: s.lean, x: s.x, w: s.w, tip: `${r.label}: a model's judgement is ${name[s.lean]} on ${s.n}` })),
        }))}
      />
    </Figure>
  );
}

export function DueCalendar({ b }: { b: BoardDoc }) {
  const label = labels(b);
  const cal = b.figures.calendar;
  return (
    <Figure
      id="fig-calendar"
      title="When the forecasts with a closing date on record fall due, and what each reads today"
      note={KIND_LABEL.chart}
      keys={<>{wordKeys(b, cal.bins.map((x) => x.counts))}{cal.bins.some((x) => x.marks.some((m) => m.due)) ? <Key swatch={<span className="m-0.5 inline-block h-3 w-3 outline outline-1 outline-ink" />}>framed: its date has already passed</Key> : null}</>}
      foot={<p>One mark is one forecast whose closing date is on this site&apos;s record, placed in the year its window closes; follow a mark to its record. Later years are grouped, so the rows are not an even scale. <span className="num">{cal.undated}</span> forecasts are not drawn: this site&apos;s record gives them no closing date, though some name a year in their own words. A date that has passed does not by itself settle a forecast: the word still comes from how it is scored. Each mark is named in the table below.</p>}
      table={<><Counts head="Window closes" cols={b.words} rows={cal.bins.map((x) => ({ name: x.label, counts: x.counts, total: x.n }))} /><MarkList b={b} groups={cal.bins.map((x) => ({ name: x.label, marks: x.marks }))} /></>}
      tableLabel="The numbers, and which forecast each mark is"
    >
      <MarkRows
        label="Forecasts with a closing date on record, one mark each, by the year the window closes"
        rows={cal.bins.map((x) => ({ key: x.id, name: x.label, note: `${x.n}`, marks: x.marks.map((m) => mark(m, label)) }))}
      />
    </Figure>
  );
}

export function ForecasterMarks({ b }: { b: BoardDoc }) {
  const label = labels(b);
  const rows = b.figures.forecasters;
  const out = b.figures.forecasters_left_out;
  return (
    <Figure
      id="fig-forecasters"
      title="Every forecaster with a scored forecast"
      note={KIND_LABEL.chart}
      keys={wordKeys(b, rows.map((f) => f.counts))}
      foot={<p>One mark is one forecast, and a hollow mark is one that cannot be scored yet. The names are in alphabetical order, not ranked: many have only a mark or two, far too few to say who forecasts better. Writers who made a forecast together have a row of their own. <span className="num">{out.n}</span> more forecasters are not drawn because every forecast of theirs is still too early to tell, among them heads of other labs; they are listed in the table. This site&apos;s own forecasts are in the figure by source. The words are not scored alike: a dated claim by someone else can read slower than said but has no word for wrong, while a claim this site tests nightly can read not happening. This page is drafted by a model made by Anthropic, and Anthropic&apos;s chief executive is among the names; his marks are scored by the same rules as the rest, on the records linked from each mark, and the mark of his that reads happening rests on revenue run-rates reported in the press, not on audited accounts.</p>}
      table={
        <>
          <Counts head="Forecaster" cols={b.words} rows={rows.map((f) => ({ name: f.who, counts: f.counts, total: f.n }))} />
          <table className="data mt-4">
            <thead><tr><th scope="col">Not drawn: every forecast still too early to tell</th><th scope="col">Forecasts</th></tr></thead>
            <tbody>{out.names.map((f) => <tr key={f.who}><th scope="row">{f.who}</th><td>{f.n}</td></tr>)}</tbody>
          </table>
          <MarkList b={b} groups={rows.map((f) => ({ name: f.who, marks: f.marks }))} />
        </>
      }
      tableLabel="The numbers, who is left out, and which forecast each mark is"
    >
      <MarkRows
        wide
        columns
        label="Forecasters with a scored forecast, one mark for each of their forecasts"
        rows={rows.map((f) => ({ key: f.who, name: f.who, marks: f.marks.map((m) => mark(m, label)) }))}
      />
    </Figure>
  );
}
