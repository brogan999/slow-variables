import Link from "next/link";
import type { SgMark, SingularityDoc } from "@/lib/data";
import { Figure, Key } from "./Figure";
import { Fact } from "./Fact";
import { WORD, WordChip } from "./StatusChip";

export const ORDER = ["happening", "slower", "too_early"]; // the words a ledger status can take
const ROW = 14; // pixels per stacked row of marks
const glyph = (w: string) => (WORD[w] ?? WORD.too_early).glyph;
const years = (m: SgMark) => m.years ?? "no date";
const Claim = ({ m }: { m: SgMark }) => <>{m.quoted ? <>&ldquo;{m.line}&rdquo;</> : m.line}</>;

function Track({ doc, height, children }: { doc: SingularityDoc; height: number; children: React.ReactNode }) {
  return (
    <div className="relative" style={{ height }}>
      {doc.axis.ticks.map((t) => <div key={t.year} aria-hidden className="absolute inset-y-0 w-px bg-grid" style={{ left: `${t.x}%` }} />)}
      {doc.axis.breaks.map((b) => <div key={b} aria-hidden className="absolute inset-y-0 border-l border-dashed border-axis" style={{ left: `${b}%` }} />)}
      <div aria-hidden className="absolute inset-y-0 right-0 bg-surface-2/60" style={{ left: `${doc.axis.today}%` }} />
      {children}
    </div>
  );
}

export function TimelinePlate({ doc }: { doc: SingularityDoc }) {
  const placed = doc.lanes.flatMap((l) => l.forecasts);
  return (
    <Figure
      title="When each forecaster expected each milestone"
      note="a mark sits at the year forecast, a bar spans a stated range; hover or tap for who said it and when"
      keys={<>
        {ORDER.map((w) => <Key key={w} swatch={<span aria-hidden className="font-mono text-sm leading-none">{glyph(w)}</span>}>{doc.words[w]}</Key>)}
        <Key swatch={<span aria-hidden className="inline-block h-[3px] w-5 bg-s3" />}>the range stated</Key>
        <Key swatch={<span aria-hidden className="font-mono text-sm leading-none text-muted">◇</span>}>set in a story, not a forecast</Key>
      </>}
      foot={<p>The scale is not even: the half century from 1950 and the half century from 2050 are squeezed so the years around now get most of the width (dashed lines mark where it changes). A call that gives odds, or bets against a date, without naming a year is listed under the chart. Shaded: the years still to come.</p>}
      tableLabel="Every forecast placed on the chart"
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">Milestone</th><th scope="col">Who</th><th scope="col">Said</th><th scope="col">Years forecast</th><th scope="col">Tonight</th></tr></thead>
          <tbody>
            {doc.lanes.flatMap((l) => l.forecasts.map((m) => (
              <tr key={m.id}><td>{l.label}</td><td><Link href={m.href} className="hover:underline">{m.who}</Link></td><td className="num whitespace-nowrap">{m.made.slice(0, 4)}</td><td className="num whitespace-nowrap">{years(m)}</td><td>{doc.words[m.word]}</td></tr>
            )))}
          </tbody>
        </table>
      }
    >
      <div className="font-sans text-sm" role="group" aria-label={`${placed.length ? "Forecasts of AI milestones placed by the year forecast, one row per milestone, with an unscored row of fiction below." : ""} Each mark links to the forecast.`}>
        <div className="relative h-5 sm:ml-[calc(11rem+0.75rem)]" aria-hidden>
          <span className="absolute -translate-x-1/2 font-mono text-[10px] uppercase tracking-[0.1em] text-ink" style={{ left: `${doc.axis.today}%` }}>today</span>
        </div>
        {doc.lanes.map((l) => (
          <div key={l.id} className="sm:grid sm:grid-cols-[11rem_minmax(0,1fr)] sm:gap-x-3 border-t border-grid py-1.5">
            <div className="text-[12.5px] leading-tight text-ink-2 pb-1 sm:pb-0 sm:pt-1 sm:text-right">{l.label}</div>
            <Track doc={doc} height={l.slots * ROW + 6}>
              {l.forecasts.map((m) => {
                const tip = `${m.who}, said ${m.made.slice(0, 4)}: ${years(m)}. ${doc.words[m.word]}.`;
                const top = (m.slot ?? 0) * ROW + 3;
                return (
                  <span key={m.id} className="sg-mark" data-made={m.made_year}>
                    {m.span_width !== undefined ? <span aria-hidden className="absolute h-[3px] bg-s3" style={{ top: top + 5, left: `${m.x_low}%`, width: `${m.span_width}%` }} /> : null}
                    <Link href={m.href} prefetch={false} data-tip={tip} aria-label={tip} title={tip}
                      className="absolute -translate-x-1/2 font-mono text-[13px] leading-none text-ink hover:text-ink focus-visible:outline-2" style={{ top, left: `${m.x}%` }}>{glyph(m.word)}</Link>
                  </span>
                );
              })}
            </Track>
          </div>
        ))}
        <div className="sm:grid sm:grid-cols-[11rem_minmax(0,1fr)] sm:gap-x-3 border-t-2 border-double border-axis py-1.5 mt-1">
          <div className="text-[12.5px] leading-tight italic text-ink-2 pb-1 sm:pb-0 sm:pt-1 sm:text-right">Imagined, not forecast</div>
          <Track doc={doc} height={doc.fiction_slots * ROW + 6}>
            {doc.fiction.filter((f) => f.x !== null).map((f) => {
              const tip = `${f.title}, ${f.author} (${f.year_written}), set in ${f.set_in_year}`;
              return <a key={f.anchor} href={`#${f.anchor}`} data-tip={tip} aria-label={tip} title={tip}
                className="absolute -translate-x-1/2 font-mono text-[13px] leading-none text-muted" style={{ top: (f.slot ?? 0) * ROW + 3, left: `${f.x}%` }}>◇</a>;
            })}
          </Track>
        </div>
        <div className="relative h-5 sm:ml-[calc(11rem+0.75rem)]" aria-hidden>
          {doc.axis.ticks.map((t) => <span key={t.year} className={`absolute -translate-x-1/2 font-mono text-[10px] text-muted ${[1970, 2025, 2035, 2045, 2075].includes(t.year) ? "max-sm:hidden" : ""}`} style={{ left: `${t.x}%` }}>{t.year}</span>)}
        </div>
      </div>
    </Figure>
  );
}

export function Undated({ doc }: { doc: SingularityDoc }) {
  const lanes = doc.lanes.filter((l) => l.undated.length);
  return (
    <dl className="grid gap-4">
      {lanes.map((l) => (
        <div key={l.id}>
          <dt className="eyebrow mb-1">{l.label}</dt>
          {l.undated.map((m) => (
            <dd key={m.id} className="sg-mark border-t border-grid py-2 grid gap-x-3 sm:grid-cols-[11rem_minmax(0,1fr)] text-[0.95rem]" data-made={m.made_year}>
              <span><WordChip word={m.word} label={doc.words[m.word]} /></span>
              <span><Link href={m.href} className="hover:underline"><Claim m={m} /></Link> <span className="text-xs text-ink-2">· {m.made.slice(0, 4)}</span></span>
            </dd>
          ))}
        </div>
      ))}
    </dl>
  );
}

function Rows({ doc, rows, when }: { doc: SingularityDoc; rows: SgMark[]; when: (m: SgMark) => React.ReactNode }) {
  return (
    <ul>
      {rows.map((m) => (
        <li key={m.id} className="border-t border-grid py-2.5 grid gap-x-4 gap-y-1 sm:grid-cols-[11rem_minmax(0,1fr)]">
          <div><WordChip word={m.word} label={doc.words[m.word]} /></div>
          <div className="min-w-0 text-[0.975rem] leading-snug">
            <Link href={m.href} className="hover:underline"><Claim m={m} /></Link>
            <div className="mt-0.5 text-xs text-ink-2">{when(m)}</div>
          </div>
        </li>
      ))}
    </ul>
  );
}

export function Due({ doc }: { doc: SingularityDoc }) {
  return <Rows doc={doc} rows={doc.due} when={(m) => <>said {m.made.slice(0, 4)} · its time came {m.settles}</>} />;
}

export function Latest({ doc }: { doc: SingularityDoc }) {
  const t = doc.table;
  return (
    <div className="overflow-x-auto">
      <table className="data w-full">
        <thead><tr><th scope="col">Forecaster</th>{t.cols.map((c) => <th key={c.id} scope="col">{c.label}</th>)}</tr></thead>
        <tbody>
          {t.rows.map((r) => (
            <tr key={r.who}>
              <th scope="row" className="font-normal text-left whitespace-nowrap">{r.who}</th>
              {t.cols.map((c) => {
                const v = r.cells[c.id];
                return <td key={c.id} className="num whitespace-nowrap">{v ? <Link href={v.href} className="hover:underline" title={`said ${v.made}; ${doc.words[v.word]}`}><span aria-hidden className="mr-1">{glyph(v.word)}</span>{v.text}</Link> : <span className="text-muted">·</span>}</td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Questions({ doc }: { doc: SingularityDoc }) {
  return (
    <ol className="grid gap-0">
      {doc.questions.map((q, i) => (
        <li key={q.id} className="border-t border-grid py-3 grid gap-x-4 gap-y-1.5 sm:grid-cols-[2rem_minmax(0,1fr)_12rem]">
          <span className="font-serif text-lg text-gild-ink" aria-hidden>{["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][i]}</span>
          <div className="min-w-0">
            <p className="font-serif text-[1.05rem] leading-snug text-ink">{q.question}</p>
            <p className="mt-1 text-sm text-ink-2"><span className="text-muted">Fast:</span> {q.fast} <span className="text-muted">Slow:</span> {q.slow}</p>
          </div>
          <div className="text-sm sm:text-right">{q.reading ? <><span className="text-muted text-xs block">Tonight</span><Fact f={q.reading} /></> : <span className="text-muted">No public series yet</span>}</div>
        </li>
      ))}
    </ol>
  );
}

export function Worlds({ doc }: { doc: SingularityDoc }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {doc.worlds.map((w) => (
        <section key={w.id} aria-labelledby={`world-${w.id}`} className="panel p-5 flex flex-col gap-2">
          <h3 id={`world-${w.id}`} className="display text-xl leading-tight">{w.label}</h3>
          <p className="font-serif text-[1rem] leading-relaxed">{w.text}</p>
          <p className="text-xs text-ink-2">Argued by {w.argued_by.join("; ")}.</p>
          <p className="text-xs"><span className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-2">{w.consistent ? "Consistent with tonight's readings" : "A signpost fails tonight"}</span> · <Link href="/outlook#scenarios" className="underline decoration-axis underline-offset-2 hover:decoration-ink">its cells in the scenario grid</Link></p>
        </section>
      ))}
    </div>
  );
}

export function Fiction({ doc }: { doc: SingularityDoc }) {
  return (
    <ul className="grid gap-x-8 sm:grid-cols-2">
      {doc.fiction.map((f) => (
        <li key={f.anchor} id={f.anchor} className="border-t border-grid py-2.5 scroll-mt-24 target:bg-surface-2">
          <p className="font-serif text-[1rem]"><a href={f.url ?? undefined} className="italic underline decoration-axis underline-offset-2 hover:decoration-ink">{f.title}</a> <span className="text-ink-2">· {f.author}, {f.year_written}</span></p>
          <p className="text-sm text-ink-2 mt-0.5">{f.line} <span className="text-muted">Set {f.set_in_year ? `in ${f.set_in_year}` : f.set_in_words}.</span></p>
        </li>
      ))}
    </ul>
  );
}

export function Sources({ doc }: { doc: SingularityDoc }) {
  return (
    <ol className="flex flex-col gap-3 font-serif text-[1rem] leading-relaxed">
      {doc.sources.map((s) => (
        <li key={s.id}>{s.who}, {s.field}. <a href={s.url} className="italic underline decoration-axis underline-offset-2 hover:decoration-ink">{s.work}</a>, {s.year}.{s.quote ? <> <span className="text-ink-2">&ldquo;{s.quote}&rdquo;</span></> : null}</li>
      ))}
    </ol>
  );
}
