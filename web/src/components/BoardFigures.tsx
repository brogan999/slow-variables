import { Figure, Key } from "@/components/Figure";
import { LEAN_FILL, LeanSplit, MarkRows, WORD_FILL, WordSwatch } from "@/components/diagrams/board";
import { KIND_LABEL, ShareBars, Swatch } from "@/components/diagrams/kit";
import type { BoardDoc, BoardMark, Word } from "@/lib/data";

// The predictions board's figures. Every count and position is the export's (src/ai_tracker/board.py).
const labels = (b: BoardDoc) => Object.fromEntries(b.words.map((w) => [w.id, w.label])) as Record<Word, string>;
const BAR_FILL = { ...WORD_FILL, too_early: "var(--surface-2)" };
const wordKeys = (b: BoardDoc, skip: Word[] = [], bars = false) => b.words.filter((w) => !skip.includes(w.id)).map((w) => <Key key={w.id} swatch={bars ? <Swatch fill={BAR_FILL[w.id]} /> : <WordSwatch word={w.id} />}>{w.label.toLowerCase()}</Key>);
const mark = (m: BoardMark, label: Record<Word, string>) => ({ key: m.key, word: m.word, href: m.href, tip: `${m.who}: ${label[m.word].toLowerCase()}${m.settles ? `, window closes ${m.settles}` : ""}`, framed: m.due });

// The numbers under a chart: one row for each thing drawn, one column for each word.
function Counts({ head, cols, rows }: { head: string; cols: { id: string; label: string }[]; rows: { name: string; counts: Record<string, number>; total?: number }[] }) {
  return (
    <table className="data">
      <thead><tr><th scope="col">{head}</th>{cols.map((c) => <th key={c.id} scope="col">{c.label}</th>)}<th scope="col">All</th></tr></thead>
      <tbody>{rows.map((r) => <tr key={r.name}><th scope="row">{r.name}</th>{cols.map((c) => <td key={c.id}>{r.counts[c.id]}</td>)}<td>{r.total}</td></tr>)}</tbody>
    </table>
  );
}

export function TallyBars({ b }: { b: BoardDoc }) {
  const label = labels(b);
  return (
    <Figure
      id="fig-tally"
      title="How many forecasts in each section are happening, not happening, or still too early to tell"
      note={KIND_LABEL.chart}
      keys={wordKeys(b, [], true)}
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
      note="A model of the method, with tonight's counts"
      foot={<p>The boxes draw the steps this site follows, not a measurement; the counts in them are the board&apos;s on {b.as_of}. A forecast moves right when a reading arrives and can move back if the reading goes stale. A model&apos;s lean sits beside a forecast that is too early to tell and never changes its word.</p>}
    >
      <ol className="grid gap-2 md:grid-cols-[minmax(0,1fr)_1.5rem_minmax(0,1fr)_1.5rem_minmax(0,1.6fr)] md:items-center">
        <li className={step}>
          <span className="eyebrow">Stated</span>
          <span className="num text-2xl leading-none text-ink">{f.stated}</span>
          <span className="text-[13px] leading-snug text-ink-2">Someone writes a forecast down: a lab, a named writer, or this site.</span>
        </li>
        <li aria-hidden className={arrow}><span className="md:hidden">↓</span><span className="max-md:hidden">→</span></li>
        <li className={step}>
          <span className="eyebrow">Given a test</span>
          <span className="text-[13px] leading-snug text-ink-2">This site says which reading would settle it, and what that reading would have to show.</span>
        </li>
        <li aria-hidden className={arrow}><span className="md:hidden">↓</span><span className="max-md:hidden">→</span></li>
        <li className="grid gap-2">
          <div className="flex flex-col gap-1.5 border border-ink bg-surface p-3">
            <span className="eyebrow">A reading arrives</span>
            <span className="num text-2xl leading-none text-ink">{f.tested}</span>
            <ul className="flex flex-col gap-1 text-[13px] leading-snug text-ink-2">
              {b.words.filter((w) => w.id !== "too_early").map((w) => (
                <li key={w.id} className="grid grid-cols-[0.75rem_1.75rem_minmax(0,1fr)] items-baseline gap-x-2"><span className="mt-1 flex self-start"><WordSwatch word={w.id} /></span><span className="num text-right text-ink">{b.tally[w.id]}</span><span><span className="text-ink">{w.label}.</span> {w.meaning}</span></li>
              ))}
            </ul>
          </div>
          <div className="flex flex-col gap-1.5 border border-dashed border-axis p-3">
            <span className="eyebrow">No reading yet</span>
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
  return (
    <Figure
      id="fig-sources"
      title="Who is right so far, by where the forecast came from"
      note={KIND_LABEL.chart}
      keys={wordKeys(b, ["too_early"])}
      foot={<p>One mark is one forecast that a reading has tested; follow a mark to its record. Forecasts still too early to tell are counted at the end of each row, not drawn. The rows are not a ranking and no rate is drawn, because the counts are small and the families are scored differently: a dated claim by someone else is scored as on track or behind, so it can read slower than said but never not happening, while a claim tested nightly can fail its test.</p>}
      table={<Counts head="Where it came from" cols={b.words} rows={b.figures.sources.map((s) => ({ name: s.label, counts: { ...s.counts, too_early: s.too_early }, total: s.n }))} />}
    >
      <MarkRows
        wide
        label="Tested forecasts, one mark each, by the family the forecast came from"
        rows={b.figures.sources.map((s) => ({ key: s.id, name: s.label, marks: s.marks.map((m) => mark(m, label)), tail: <>and {s.too_early} too early to tell</> }))}
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
      note="Chart of a model's judgements, not of readings"
      keys={<>{b.leans.map((w) => <Key key={w.id} swatch={<span style={{ color: LEAN_FILL[w.id], boxShadow: "inset 0 0 0 1px currentColor" }} className="flex"><Swatch fill={LEAN_FILL[w.id]} hatched /></span>}>{w.label}</Key>)}<Key swatch={<span className="inline-block h-3 w-px bg-ink" />}>the centre: true to its left, false to its right</Key></>}
      foot={<p>Every bar here is hatched because it draws a model&apos;s judgement, not a reading: {b.judged.model} gave each lean on {b.judged.date}, and no person reviewed each one. A bar is the shares of that section&apos;s leaned-on forecasts, so sections of different sizes compare; the numbers at its ends count the forecasts leaning true and leaning false, and the count beside a name is how many the bar holds. A lean changes no word above. The model is made by Anthropic, and some of these forecasts are about Anthropic and its rivals. Forecasts with no lean are in the table, not drawn.</p>}
      table={<Counts head="Section" cols={[...b.leans, { id: "none", label: "no lean given" }]} rows={fig.rows.map((r) => ({ name: r.label, counts: { ...r.counts, none: r.unjudged }, total: r.n }))} />}
      tableLabel="The numbers (the last column counts the forecasts with a lean)"
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
      title="When the dated forecasts fall due, and what each one reads today"
      note={KIND_LABEL.chart}
      keys={<>{wordKeys(b)}<Key swatch={<span className="inline-block h-3 w-3 outline outline-1 outline-offset-2 outline-ink" style={{ background: WORD_FILL.slower }} />}>framed: its date has already passed</Key></>}
      foot={<p>One mark is one forecast that names a date, placed in the year its window closes; follow a mark to its record. Later years are grouped, so the rows are not an even scale. <span className="num">{cal.undated}</span> forecasts name no date, only what would settle them, and are not drawn. A date that has passed does not by itself settle a forecast: the word still comes from a reading.</p>}
      table={<Counts head="Window closes" cols={b.words} rows={cal.bins.map((x) => ({ name: x.label, counts: x.counts, total: x.n }))} />}
    >
      <MarkRows
        label="Dated forecasts, one mark each, by the year the window closes"
        rows={cal.bins.map((x) => ({ key: x.id, name: x.label, note: `${x.n}`, marks: x.marks.map((m) => mark(m, label)) }))}
      />
    </Figure>
  );
}

export function ForecasterMarks({ b }: { b: BoardDoc }) {
  const label = labels(b);
  return (
    <Figure
      id="fig-forecasters"
      title="Every forecaster with a forecast that a reading has tested"
      note={KIND_LABEL.chart}
      keys={wordKeys(b)}
      foot={<p>One mark is one forecast, and a hollow mark is one a reading cannot test yet. The names are in alphabetical order, not ranked: most have only a mark or two, which is too few to say who is a better forecaster. A name is as the source credits it, so writers who made a forecast together have a row of their own. Forecasters whose forecasts are all too early to tell are left out, as are this site&apos;s own, which are in the figure by source. A dated claim by someone else can read slower than said but never not happening.</p>}
      table={<Counts head="Forecaster" cols={b.words} rows={b.figures.forecasters.map((f) => ({ name: f.who, counts: f.counts, total: f.n }))} />}
    >
      <MarkRows
        wide
        columns
        label="Forecasters with a tested forecast, one mark for each of their forecasts"
        rows={b.figures.forecasters.map((f) => ({ key: f.who, name: f.who, marks: f.marks.map((m) => mark(m, label)) }))}
      />
    </Figure>
  );
}
