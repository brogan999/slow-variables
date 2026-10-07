import Link from "next/link";
import { Inline } from "@/components/Essay";
import { Figure, Key } from "@/components/Figure";
import { Mark, Marks, Plot } from "@/components/chart";
import { PlotLine, ScaleBars } from "@/components/diagrams/census";
import { KIND_LABEL } from "@/components/diagrams/kit";
import { LANE_MARK, LaneDot, STATE_GLYPH, YearScale, YearTrack } from "@/components/diagrams/longrun";
import { WORD } from "@/components/StatusChip";
import { type OutlookState, outlook, type SingularityDoc } from "@/lib/data";
import { CLAIM_WORDS, fmt } from "@/lib/format";

// The long-run page's figures. Every count and position is the export's (singularity.figures in src/ai_tracker).
const glyph = (w: string) => (WORD[w] ?? WORD.too_early).glyph;
const link = "underline decoration-grid underline-offset-2 hover:text-ink";
const ROW = "border-t border-grid py-2 first:border-t-0 sm:grid sm:items-center sm:gap-x-3";
const HIDE = [1970, 2025, 2035, 2045, 2075]; // the timeline's own choice of ticks a phone has no room for
const DISCLOSE = "This figure was drafted by a Claude model, made by Anthropic, and the heads of Anthropic and of rival labs are among the forecasters it draws; each is placed by the same rule, from its own record in this site's ledger of forecasts, and no placing was adjusted for anyone.";
const WORLDS_NOTE = `${KIND_LABEL.model}; the glyphs are tonight's readings`;

export function LaneSpread({ doc }: { doc: SingularityDoc }) {
  const f = doc.figures.spread;
  return (
    <Figure
      id="fig-spread"
      title="How far apart the dated forecasts of each milestone are, and how many give no year"
      note={KIND_LABEL.chart}
      keys={<>
        <Key swatch={<span className="inline-block h-3 w-[2px] bg-s2" />}>a forecast, at the year the timeline places it</Key>
        <Key swatch={<span className="inline-block h-px w-5 bg-ink-2" />}>from the earliest year a forecast is placed at to the latest</Key>
        <Key swatch={<span className="inline-block h-3 w-4 bg-surface-2" />}>shaded: the years still to come</Key>
      </>}
      foot={<>
        <p>Each row counts forecasts, not people: a writer with more than one dated forecast on a row is counted for each, and the authors of AI 2027 appear both together and under their own names. A forecast that gives a range is placed, as on the timeline above, at its most likely year or else at the last year of its range, so a row does not show how wide each forecast is, and a row can begin later than the earliest year a forecast names. A step toward a milestone (a forecast of an early sign of it, not of the milestone itself) is left out and counted in the table. Each forecast is named on the timeline above and in the lists under it.</p>
        <p>No middle or average is drawn. The marks on a row are not the same kind of year: some are a deadline (&quot;by&quot; a year), some a most likely year, some the last year of a range, and some a year the forecaster gave only some odds, in a few cases less than even. The forecasters do not all mean the same thing by a milestone, and the rows that are not in the forecaster table further down gather different claims on one theme. So a row shows how far apart the years are, not where opinion settles. The scale is the timeline&apos;s and is not even. {DISCLOSE}</p>
      </>}
      tableLabel="The counts and the years"
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">Milestone</th><th scope="col">Give a year</th><th scope="col">Steps toward it</th><th scope="col">Give no year</th><th scope="col">Earliest placed</th><th scope="col">Latest placed</th></tr></thead>
          <tbody>
            {f.lanes.map((s) => (
              <tr key={s.id}><th scope="row" className="text-left font-normal">{s.label}</th><td className="num">{s.n_dated}</td><td className="num">{s.n_steps}</td><td className="num">{s.n_undated}</td><td className="num">{s.first ?? "·"}</td><td className="num">{s.last ?? "·"}</td></tr>
            ))}
          </tbody>
        </table>
      }
    >
      <div role="group" aria-label="For each milestone, its dated forecasts on one strip of years, with the count that give a year and the count that do not">
        {f.lanes.map((s) => (
          <div key={s.id} className={`${ROW} sm:grid-cols-[12rem_minmax(0,1fr)_11rem]`}>
            <div className="text-[12.5px] leading-tight text-ink sm:text-right">{s.label}
              <span className="mt-0.5 block font-mono text-[11px] text-muted"><span className="num text-ink-2">{s.n_dated}</span> with a year · <span className="num text-ink-2">{s.n_undated}</span> without</span>
            </div>
            <YearTrack ticks={doc.axis.ticks} breaks={doc.axis.breaks} today={doc.axis.today} className="h-6 max-sm:mt-1.5">
              {s.x !== null ? <span aria-hidden className="absolute top-1/2 h-px -translate-y-1/2 bg-ink-2" style={{ left: `${s.x}%`, width: `${s.w}%` }} /> : null}
              {s.marks.map((m) => <span key={m.id} title={`${m.who}, said ${m.made}: ${m.years}`} className="absolute top-1/2 h-3 w-[2px] -translate-x-1/2 -translate-y-1/2 bg-s2" style={{ left: `${m.x}%` }} />)}
            </YearTrack>
            <div className="font-mono text-[11px] leading-snug text-ink-2 max-sm:mt-1">{s.first === null ? null : s.first === s.last ? <span className="num text-ink">{s.first}</span> : <><span className="num text-ink">{s.first}</span> to <span className="num text-ink">{s.last}</span></>}{s.theme ? <span className="block text-muted">different claims on a theme</span> : null}</div>
          </div>
        ))}
        <div className="sm:grid sm:grid-cols-[12rem_minmax(0,1fr)_11rem] sm:gap-x-3"><span className="max-sm:hidden" /><YearScale ticks={doc.axis.ticks} hide={HIDE} /></div>
      </div>
    </Figure>
  );
}

export function SaidAgainstGiven({ doc }: { doc: SingularityDoc }) {
  const f = doc.figures.said;
  const lane = Object.fromEntries(f.lanes.map((l) => [l.id, l.label]));
  return (
    <Figure
      id="fig-said"
      title="When each forecast was made, against the year it gave"
      note={KIND_LABEL.chart}
      keys={<>
        {f.lanes.map((l) => <Key key={l.id} swatch={<LaneDot lane={l.id} />}>{l.label}</Key>)}
        <Key swatch={<span className="inline-block h-4 w-[1.5px] bg-s2" />}>the range of years stated</Key>
        <Key swatch={<span className="inline-block h-px w-5 bg-s2" />}>a mark set aside, tied back to the date it was made</Key>
        <Key swatch={<span className="inline-block w-5 border-t border-dashed border-ink-2" />}>the year the forecast was made</Key>
        <Key swatch={<span className="inline-block h-px w-5 bg-ink" />}>this year</Key>
      </>}
      foot={<>
        <p>One mark is one dated forecast of the milestones in the forecaster table: <span className="num">{f.n}</span> in all, each linked to its record. The dashed steps are the year a forecast was made, so a mark higher above them looked further ahead. Because the scale up the side is not even, equal heights are not equal numbers of years: the table gives each forecast&apos;s years. A mark under the line marked this year names a year that has already passed; a mark on it names this year, which is not over. Neither scale is even: the years before 2020 are squeezed along the bottom, and the years before 2020 and after 2040 up the side (dashed lines mark where each scale changes).</p>
        <p>Where one mark would cover another, the later is set beside it, to the right or the left, and tied back by a short line to the date it was made: <span className="num">{f.n_moved}</span> marks are set aside this way, some by several months, and no mark is set right of today. Read such a mark&apos;s date from the far end of its line, or from the table. No mark is named in the drawing: the table lists every forecast in the order drawn, left to right, with its writer. Not drawn: <span className="num">{f.left_out.steps}</span> steps toward a milestone and <span className="num">{f.left_out.undated}</span> forecasts that give odds or doubt a date without naming a year.</p>
        <p>The marks fall toward the lower right because this site&apos;s list holds different people making different claims in different years, not because anyone here changed a date: no forecaster&apos;s earlier and later date for the same claim is on record, so the figure cannot show a forecast being brought forward and is not evidence that forecasts are converging. Where one writer has more than one mark on a milestone they are different claims, at different odds or on different conditions; each links to its record. A mark is the year the timeline places a forecast at, which may be a deadline, a most likely year or a year given only some odds, and a range bar may be a spread of odds or a plain &quot;give or take&quot;. No trend line is fitted. {DISCLOSE}</p>
      </>}
      tableLabel="Every forecast drawn"
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">Made</th><th scope="col">Who</th><th scope="col">Milestone</th><th scope="col">Years forecast</th><th scope="col">Tonight</th></tr></thead>
          <tbody>
            {f.marks.map((m) => (
              <tr key={m.id}><td className="num whitespace-nowrap">{m.made.slice(0, 7)}</td><td><Link href={m.href} prefetch={false} className="hover:underline">{m.who}</Link></td><td>{lane[m.lane]}</td><td className="num whitespace-nowrap">{m.years}</td><td className="whitespace-nowrap"><span aria-hidden className="mr-1">{glyph(m.word)}</span>{doc.words[m.word]}</td></tr>
            ))}
          </tbody>
        </table>
      }
    >
      <div className="overflow-x-auto"><div className="min-w-[40rem]">
        <Plot x={f.x_ticks} y={{ ticks: f.y_ticks, unit: "the year forecast ↑", chars: 4 }} tall label="Dated forecasts placed by the year each was made, across, and the year it gave, up. Use the arrow keys to move between marks; each opens its forecast.">
          <line x1={`${f.break}%`} x2={`${f.break}%`} y1="0" y2="100%" stroke="var(--axis)" strokeDasharray="3 3" />
          {f.y_breaks.map((y) => <line key={y} x1="0" x2="100%" y1={`${y}%`} y2={`${y}%`} stroke="var(--axis)" strokeDasharray="3 3" />)}
          <PlotLine points={f.said_line} />
          <line x1="0" x2="100%" y1={`${f.this_year}%`} y2={`${f.this_year}%`} stroke="var(--ink)" />
          <text x={`${f.break}%`} dx="6" y={`${f.this_year}%`} dy="12" fontSize="10" fill="var(--ink)" className="font-mono uppercase">this year</text>
          {f.marks.map((m) => m.y_low !== null ? <line key={m.id} x1={`${m.x}%`} x2={`${m.x}%`} y1={`${m.y_high}%`} y2={`${m.y_low}%`} stroke="var(--s2)" strokeWidth="1.5" /> : null)}
          {f.marks.map((m) => m.moved ? <line key={`tie-${m.id}`} x1={`${m.x_made}%`} x2={`${m.x}%`} y1={`${m.y}%`} y2={`${m.y}%`} stroke="var(--s2)" /> : null)}
          <Marks>
            {f.marks.map((m, i) => (
              <Mark key={m.id} p={m} stop={i === 0} {...LANE_MARK[m.lane]}
                tip={`${m.who}, said ${m.made.slice(0, 4)}: ${lane[m.lane]}, ${m.years}. ${doc.words[m.word]}.${m.moved ? " Set aside: made at the far end of its line." : ""}`} />
            ))}
          </Marks>
        </Plot>
      </div></div>
      <p className="mt-1 text-right font-mono text-[11px] text-muted" aria-hidden>the year the forecast was made →</p>
    </Figure>
  );
}

export function DueLines({ doc }: { doc: SingularityDoc }) {
  const f = doc.figures.due;
  const drawn = Object.keys(doc.words).filter((w) => f.counts[w]);
  return (
    <Figure
      id="fig-due"
      title="Each forecast whose closing date has passed, from the year it was made to the year it fell due"
      note={KIND_LABEL.chart}
      keys={<>
        {drawn.map((w) => <Key key={w} swatch={<span aria-hidden className="font-mono text-sm leading-none">{glyph(w)}</span>}>{doc.words[w].toLowerCase()}, at the year it fell due</Key>)}
        <Key swatch={<span className="inline-block h-3 w-[2px] bg-s2" />}>the year it was made</Key>
        <Key swatch={<span className="inline-block h-[2px] w-5 bg-s2" />}>the wait</Key>
        <Key swatch={<span className="inline-block h-[6px] w-5 bg-s3" />}>the range of years stated</Key>
      </>}
      foot={<>
        <p>One line is one forecast, on an even scale of years. <span className="num">{f.n}</span> forecasts have a closing date (the day this site set for checking it) that has passed: far too few to say how often such forecasts come true, so the figure counts and gives no rate. Slower than said means the date passed without the milestone. This site&apos;s ledger of forecasts has no word for wrong: a forecast that reads slower can still come true late, and one scored on a step says nothing final about the milestone itself. Where a forecast fell due within a year of being made, its marks touch.</p>
        <p>A forecast with no closing date on this site&apos;s record is not on this calendar, even where the year it names has passed: there {f.unclosed.length === 1 ? "is" : "are"} <span className="num">{f.unclosed.length}</span> of those on the timeline, named in the table. The words are this site&apos;s reading on {doc.as_of}.</p>
      </>}
      tableLabel="The forecasts drawn, and those not on this calendar"
      table={<>
        <table className="data w-full">
          <thead><tr><th scope="col">Who</th><th scope="col">Milestone</th><th scope="col">Made</th><th scope="col">Years forecast</th><th scope="col">Fell due</th><th scope="col">Tonight</th></tr></thead>
          <tbody>
            {f.rows.map((r) => (
              <tr key={r.id}><td><Link href={r.href} prefetch={false} className="hover:underline">{r.who}</Link></td><td>{r.lane}{r.step ? " (a step toward it)" : ""}</td><td className="num">{r.made}</td><td className="num whitespace-nowrap">{r.years}</td><td className="num whitespace-nowrap">{r.settles}</td><td className="whitespace-nowrap">{doc.words[r.word]}</td></tr>
            ))}
          </tbody>
        </table>
        {f.unclosed.length ? (
          <table className="data mt-4 w-full">
            <thead><tr><th scope="col">Not on this calendar: no closing date on record</th><th scope="col">Milestone</th><th scope="col">Made</th><th scope="col">Year named</th><th scope="col">Tonight</th></tr></thead>
            <tbody>
              {f.unclosed.map((r) => (
                <tr key={r.id}><td><Link href={r.href} prefetch={false} className="hover:underline">{r.who}</Link></td><td>{r.lane}</td><td className="num">{r.made}</td><td className="num whitespace-nowrap">{r.years}</td><td className="whitespace-nowrap">{doc.words[r.word]}</td></tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </>}
    >
      <div role="group" aria-label="Forecasts whose closing date has passed, each drawn as a line from the year it was made to the year it fell due">
        {f.rows.map((r) => {
          const tip = `${r.who}, said ${r.made}: ${r.years}. Fell due ${r.settles}. ${doc.words[r.word]}.`;
          return (
            <div key={r.id} className={`${ROW} sm:grid-cols-[15rem_minmax(0,1fr)]`}>
              <div className="text-[13px] leading-tight text-ink">{r.who}
                <span className="mt-0.5 block text-[11.5px] leading-snug text-ink-2">{r.lane}{r.step ? ": a step toward it" : ""}</span>
                <span className="mt-0.5 block font-mono text-[11px] text-muted">said {r.made} · fell due {r.due}</span>
                <span className="mt-0.5 block font-mono text-[11px] text-ink"><span aria-hidden className="mr-1">{glyph(r.word)}</span>{doc.words[r.word].toLowerCase()}</span>
              </div>
              <YearTrack ticks={f.ticks} className="h-7 max-sm:mt-1.5">
                <span aria-hidden className="absolute top-1/2 h-[2px] -translate-y-1/2 bg-s2" style={{ left: `${r.x_made}%`, width: `${r.w}%` }} />
                {r.x_low !== null ? <span aria-hidden className="absolute top-1/2 h-[6px] -translate-y-1/2 bg-s3" style={{ left: `${r.x_low}%`, width: `${r.w_low}%` }} /> : null}
                <span aria-hidden className="absolute top-1/2 h-3 w-[2px] -translate-x-1/2 -translate-y-1/2 bg-s2" style={{ left: `${r.x_made}%` }} />
                <Link href={r.href} prefetch={false} title={tip} aria-label={tip} className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 bg-surface p-0.5 font-mono text-[15px] leading-none text-ink hover:opacity-70" style={{ left: `${r.x_due}%` }}>{glyph(r.word)}</Link>
              </YearTrack>
            </div>
          );
        })}
        <div className="sm:grid sm:grid-cols-[15rem_minmax(0,1fr)] sm:gap-x-3"><span className="max-sm:hidden" /><YearScale ticks={f.ticks} /></div>
      </div>
    </Figure>
  );
}

export function WorldsGrid({ doc }: { doc: SingularityDoc }) {
  const f = doc.figures.worlds;
  const o = outlook();
  const world = Object.fromEntries(f.worlds.map((w) => [w.id, w]));
  const states = (Object.keys(STATE_GLYPH) as OutlookState[]).filter((s) => f.states[s]);
  const name = (list: { id: string; label: string }[], id: string) => list.find((x) => x.id === id)?.label ?? id;
  return (
    <Figure
      id="fig-worlds"
      title="Where each world sits on the scenario grid, and how its signposts read tonight"
      note={WORLDS_NOTE}
      keys={<>
        <Key swatch={<span className="inline-block h-3 w-4 border-l-4 border-s2 bg-surface-2" />}>a cell a world is drawn over, named in the cell</Key>
        {states.map((s) => <Key key={s} swatch={<span aria-hidden className="font-mono text-sm leading-none">{STATE_GLYPH[s]}</span>}>a signpost: {CLAIM_WORDS[s]}</Key>)}
        <Key swatch={<span className="inline-block h-3 w-4 border border-dashed border-axis" />}>no source on the outlook argues this cell</Key>
      </>}
      foot={<>
        <p>The grid is the <Link href="/outlook#scenarios" className={link}>outlook page&apos;s</Link>: how far capability goes, down, and how the rules settle, across. Each world is drawn over the cells this site gives it; the placing is this site&apos;s, a drawing of an idea, and no world is crowned. A glyph is one signpost: a claim the outlook tests each night, listed in the table.</p>
        <p>A world reads consistent until a signpost in one of its cells fails. On {doc.as_of}, of the signposts on the grid, counting one that sits in more than one cell each time, <span className="num">{f.states.both}</span> are expected by both sides of the argument, <span className="num">{f.states.untestable}</span> cannot be tested yet, <span className="num">{f.states.holding}</span> hold and <span className="num">{f.states.failing}</span> fail, and <span className="num">{f.bare}</span> cells have no signpost at all. So consistent here means not ruled out: it is no evidence that a world is on its way.</p>
      </>}
      tableLabel="Each world's count, and every signpost"
      table={<>
        <table className="data w-full">
          <thead><tr><th scope="col">World</th><th scope="col">Cells</th><th scope="col">Still open</th>{(Object.keys(STATE_GLYPH) as OutlookState[]).map((s) => <th key={s} scope="col">Signposts: {CLAIM_WORDS[s]}</th>)}<th scope="col">Cells with no signpost</th><th scope="col">The page&apos;s word</th></tr></thead>
          <tbody>
            {f.worlds.map((w) => (
              <tr key={w.id}><th scope="row" className="text-left font-normal">{w.label}</th><td className="num">{w.n_cells}</td><td className="num">{w.open}</td>{(Object.keys(STATE_GLYPH) as OutlookState[]).map((s) => <td key={s} className="num">{w.states[s]}</td>)}<td className="num">{w.bare}</td><td>{w.consistent ? "consistent" : "a signpost fails"}</td></tr>
            ))}
          </tbody>
        </table>
        <ul className="mt-4 flex min-w-[16rem] flex-col gap-2 text-[13px] leading-snug text-ink-2">
          {f.cells.filter((c) => c.argued).map((c) => (
            <li key={`${c.progress}-${c.rules}`}>
              <span className="text-ink">{name(f.progress, c.progress)} · {name(f.rules, c.rules)}</span> ({c.worlds.map((id) => world[id]?.label ?? id).join(", ") || "no world"})
              {c.signs.length ? (
                <ul className="mt-1 flex flex-col gap-1">
                  {c.signs.map((g) => <li key={g.claim} className="grid grid-cols-[1rem_minmax(0,1fr)] items-baseline gap-x-1"><span aria-hidden>{STATE_GLYPH[g.state]}</span><span><Inline text={o.claims.find((k) => k.id === g.claim)?.text ?? g.claim} facts={o.facts} tests={o.tests} /> <span className="text-muted">({CLAIM_WORDS[g.state]})</span></span></li>)}
                </ul>
              ) : <span className="text-muted">: no signpost yet</span>}
            </li>
          ))}
        </ul>
      </>}
    >
      <div role="group" aria-label="The scenario grid, with each world drawn over the cells this site gives it and one glyph for each signpost" className="grid grid-cols-3 gap-1 sm:grid-cols-[9.5rem_repeat(3,minmax(0,1fr))]">
        <span className="max-sm:hidden" />
        {f.rules.map((r) => <div key={r.id} className="self-end pb-1 pr-2 font-mono text-[10.5px] leading-tight text-muted">{r.label}</div>)}
        {f.progress.map((p) => (
          <div key={p.id} className="contents">
            <div className="col-span-3 pt-1.5 text-[12.5px] leading-tight text-ink sm:col-span-1 sm:self-center sm:pt-0 sm:text-right">{p.label}</div>
            {f.rules.map((r) => {
              const c = f.cells.find((k) => k.progress === p.id && k.rules === r.id);
              if (!c?.argued) return <div key={r.id} className="min-h-12 border border-dashed border-axis" title="No source on the outlook argues this cell" />;
              const ws = c.worlds.map((id) => world[id]).filter(Boolean);
              return (
                <div key={r.id} className="flex min-h-12 flex-col gap-1 border-l-4 border-s2 bg-surface-2 p-1.5">
                  <span className="text-[11.5px] font-medium leading-tight text-ink">{ws.map((w) => w.short).join(", ") || "no world"}</span>
                  {c.signs.length
                    ? <span className="flex flex-wrap gap-x-1 font-mono text-[13px] leading-none text-ink">{c.signs.map((g) => <span key={g.claim} title={CLAIM_WORDS[g.state]}>{STATE_GLYPH[g.state]}<span className="sr-only"> {CLAIM_WORDS[g.state]}</span></span>)}</span>
                    : <span className="font-mono text-[10.5px] leading-tight text-muted">no signpost</span>}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </Figure>
  );
}

export function FictionLag({ doc, credits }: { doc: SingularityDoc; credits: { name: string; url: string }[] }) {
  const f = doc.figures.lag;
  return (
    <Figure
      id="fig-lag"
      title="Ideas from fiction that were later built: how many decades passed between the story and the thing"
      note={KIND_LABEL.chart}
      keys={<>
        <Key swatch={<span className="inline-block h-2.5 w-5 bg-s1" />}>ideas the idea bank marks as built, by the decades between</Key>
        <Key swatch={<span className="font-semibold text-ink">Aa</span>}>in heavier type: the row the middle built idea falls in</Key>
      </>}
      foot={<>
        <p>This is the fiction lane: stories, not forecasts, and not evidence for any date on this page. It draws a different list from the works above: the <Link href="/futures" className={link}>Futures idea bank</Link>, <span className="num">{fmt(f.ideas, "count")}</span> inventions from novels and stories ({credits.map((c, i) => <span key={c.url}>{i ? "; " : ""}<a href={c.url} className={link}>{c.name}</a></span>)}). Whether and when an idea was built is the bank&apos;s own mark, not this site&apos;s finding.</p>
        <p><span className="num">{f.n}</span> ideas are marked built with a date and are drawn. <span className="num">{fmt(f.not_built, "count")}</span> are not marked built and have no bar, so the figure shows how long the built ones took, not how long an idea takes: the ones still waiting would stretch it. Nor is it a guide to how long a story written today will wait. An idea from a recent story can only be here if it was built quickly, most ideas in the bank are not marked built at all, and nothing in the count says which of today&apos;s will be. The heavier row is where the middle of the built ideas falls, not a typical wait. Also left out: <span className="num">{f.undated}</span> built at a date the bank does not give, and <span className="num">{f.existed}</span> that existed before the story. Most of the bank&apos;s dates are decades, so the wait is counted in calendar decades, and an idea built a year after its story can fall in the next one.</p>
      </>}
      table={
        <table className="data">
          <thead><tr><th scope="col">Built</th><th scope="col">Ideas</th></tr></thead>
          <tbody>
            {f.bins.map((b) => <tr key={b.key}><th scope="row" className="text-left font-normal">{b.label}</th><td className="num">{b.n}</td></tr>)}
            <tr><th scope="row" className="text-left font-normal">All drawn</th><td className="num">{f.n}</td></tr>
          </tbody>
        </table>
      }
    >
      <ScaleBars
        nameWidth="13rem" valueWidth="9rem"
        label="Ideas from fiction marked as built, counted by the decades between the story and the thing"
        rows={f.bins.map((b) => ({
          key: b.key, name: b.label, w: b.w, strong: b.key === f.middle_key, tip: `${b.label}: ${b.n} ideas`,
          value: <>{b.n}{b.key === f.middle_key ? <span className="text-muted"> · the middle of the built ideas</span> : null}</>,
        }))}
      />
    </Figure>
  );
}
