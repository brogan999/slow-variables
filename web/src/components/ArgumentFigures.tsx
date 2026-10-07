import Link from "next/link";
import { Fact } from "@/components/Fact";
import { Figure, Key } from "@/components/Figure";
import { folioId } from "@/components/Essay";
import { StatusChip } from "@/components/StatusChip";
import { CondMark, COND_WORDS, DIRECTION_HUE, DirectionStrip, Dot, RangeStrip, Square, StateChip, ZONE_WORDS, ZoneSwatch } from "@/components/diagrams/argument";
import { KIND_LABEL } from "@/components/diagrams/kit";
import type { ArgumentDoc } from "@/lib/data";
import { fmt, fmtLine, HELD_WORDS, PHASE_WORDS, STATE_WORDS, words } from "@/lib/format";

// The figures added to /argument (Part 45i). Every place and count is the export's (argument.figures); the claims are
// the essay's own headings, the labels the seed's, and the statuses tonight's. Titles describe or ask: the readings
// change nightly, so no title states a result.
const a = "text-ink underline decoration-axis underline-offset-2";
const th = "border-b border-ink py-1 pr-3 text-left font-medium text-ink-2";
const td = "border-b border-grid py-1 pr-3 align-top";
const pair = "grid grid-cols-[minmax(0,1fr)_auto] items-start gap-x-2 text-[13px] leading-tight md:flex md:flex-col md:gap-1";
const side = "grid grid-cols-1 gap-x-5 gap-y-2 sm:grid-cols-[12rem_minmax(0,1fr)]";

// Said wherever a figure draws the labs: the drafter is one of them.
const Drafted = ({ what }: { what: string }) => (
  <p>This figure was drafted by Claude, a model made by Anthropic, and Anthropic is among the labs {what}. Check it against the records it links to.</p>
);

// The three glyphs a test's chip can carry, for the map's key.
const StateChipGlyphs = () => <span aria-hidden className="font-sans text-[12px] leading-none text-ink">● ✕ ◀</span>;

export function ArgumentMap({ doc }: { doc: ArgumentDoc }) {
  const head = "font-mono text-[10px] uppercase tracking-[0.08em] text-muted";
  return (
    <Figure
      id="fig-map"
      title="The argument in one picture: each claim, what it rests on, and the tests that bear on it"
      note={`${KIND_LABEL.model}; the chips are tonight's statuses`}
      keys={<>
        <Key swatch={<span className="inline-block h-3 w-5 rounded-[2px] border border-ink-2" />}>a slow variable&apos;s status tonight, by its published rule; the words are the site&apos;s</Key>
        <Key swatch={<span className="inline-flex gap-1"><StateChipGlyphs /></span>}>a test&apos;s state tonight: met, not met, or running the other way</Key>
        <Key swatch={<span className="inline-block h-3 w-5 rounded-[2px] border border-dashed border-muted" />}>dashed: the test cannot be run yet</Key>
        <Key swatch={<span className="font-sans text-[12px] underline decoration-axis underline-offset-2">name</span>}>a link to the reading&apos;s page, or to the test below</Key>
      </>}
      foot={<><p>A drawing of how the essay&apos;s claims hang together, not a measurement. Each claim is a heading of this essay, each slow variable and each test is named as the site names it, and each chip is the status on record tonight. It does not show how strong any link is; the sections below do that with numbers.</p>
        <p>Which reading and which test sit under which claim is this site&apos;s own arrangement; the essay does not sort them. The tests do not all cut the same way. Two would count against the claim above them if they were met: AI is not an ordinary technology, and Profit moves up to the labs. One would bear its claim out: Users keep most of the value. Two test things the essay does not argue and sit under the nearest claim: AI speeds up its own invention, and Workers stop sharing the gains.</p>
        <p>An ordinary technology is one that spreads over decades, as electricity and computers did. The labs are the companies that build the models. Installation is the first half of a build-out, when money runs ahead of revenue; frenzy is its later phase. Each is explained in the folio it links to.</p><Drafted what="whose profit and whose own claims some of these tests read" /></>}
    >
      <div className="flex flex-col font-sans">
        <div className="hidden gap-x-5 pb-1.5 md:grid md:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)_minmax(0,1.15fr)]" aria-hidden>
          <span className={head}>The claim</span><span className={head}>→ rests on</span><span className={head}>→ tested each night by</span>
        </div>
        {doc.figures.map.map((r) => (
          <div key={r.folio} className="grid gap-x-5 gap-y-3 border-t border-grid py-3.5 md:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)_minmax(0,1.15fr)]">
            <div>
              <a href={`#${folioId(r.label)}`} className="font-mono text-[10px] uppercase tracking-[0.08em] text-muted no-underline hover:underline">{r.label}</a>
              <p className="mt-1 text-[15px] font-semibold leading-snug text-ink">{r.claim}</p>
            </div>
            <div className="flex flex-col gap-2">
              <span className={`${head} md:hidden`}>Rests on</span>
              {r.watches.map((w) => (
                <div key={w.id} className={pair}>
                  <Link href={`/indicators/${w.id}`} className={a}>{w.label}</Link><StatusChip status={w.status} />
                </div>
              ))}
              {r.phase ? (
                <div className={pair}>
                  <a href={`#${folioId(r.label)}`} className={a}>The stage of the build-out</a>
                  <span className="inline-flex items-center rounded-[2px] border border-ink-2 px-1.5 py-0.5 text-xs whitespace-nowrap">{words(doc.phase.half ?? r.phase)}{doc.phase.half && doc.phase.half !== r.phase ? <span className="ml-1 text-muted">· its {PHASE_WORDS[r.phase]} phase</span> : null}</span>
                </div>
              ) : null}
            </div>
            <div className="flex flex-col gap-2">
              <span className={`${head} md:hidden`}>Tested each night by</span>
              {r.exits.map((e) => (
                <div key={e.monitor} className={pair}>
                  <a href="#fig-exits" className={a}>{e.label}</a><StateChip state={e.state} />
                </div>
              ))}
              {r.exits.length ? null : <p className="text-[12.5px] leading-snug text-ink-2">No test of its own in the list. The rule that names the stage is re-run each night, and a change is flagged so the essay can be rewritten.</p>}
            </div>
          </div>
        ))}
      </div>
    </Figure>
  );
}

export function ReadingsFigure({ doc }: { doc: ArgumentDoc }) {
  const { ranged, directed } = doc.figures.readings;
  const rangeTip = (r: (typeof ranged)[number]) =>
    `${r.label}: ${fmt(r.value, r.unit)} as of ${r.as_of}; ordinary up to ${fmtLine(r.edges[0].at, r.unit)}, faster from ${fmtLine(r.edges[1].at, r.unit)}; status ${words(r.status)}`;
  const dirTip = (r: (typeof directed)[number]) =>
    `${r.label}: ${fmt(r.start.value, r.unit)} on ${r.start.as_of}, ${fmt(r.end.value, r.unit)} on ${r.end.as_of}; status ${words(r.status)}`;
  const name = (r: { href: string; label: string }) => <Link href={r.href} className="text-[14px] font-semibold leading-tight text-ink no-underline hover:underline">{r.label}</Link>;
  return (
    <Figure
      id="fig-readings"
      title="An ordinary technology or a faster one: where the slow variables sit tonight"
      note={`${KIND_LABEL.chart}; the ranges and the bands are this site's published rules`}
      keys={<>
        <Key swatch={<ZoneSwatch zone="normal" />}>the range an ordinary technology would be in by now</Key>
        <Key swatch={<ZoneSwatch zone="between" />}>between the ranges: not scored</Key>
        <Key swatch={<ZoneSwatch zone="fast" />}>the range that would mean something faster</Key>
        <Key swatch={<Dot kind="scored" />}>tonight&apos;s number, scored in the range it sits in</Key>
        {ranged.some((r) => r.lane === "between" || r.lane === "line") ? <Key swatch={<Dot kind="between" />}>tonight&apos;s number, between the ranges or on a line</Key> : null}
        {ranged.some((r) => r.lane === "outside") ? <Key swatch={<Dot kind="held" />}>held: the number falls in a range but is not scored there, so it hangs beneath</Key> : null}
        <Key swatch={<Dot kind="start" />}>where a number stood when the window (the stretch of time its rule compares) opened</Key>
        {directed.some((r) => r.status === "concentrating") ? <Key swatch={<Square hue={DIRECTION_HUE.concentrating} hatched={false} />}>purple here means gathering in one place, not faster</Key> : null}
        <Key swatch={<span className="inline-block h-2.5 w-4 bg-surface-2" />}>a move this small does not count</Key>
        <Key swatch={<Square hue="var(--ink-2)" hatched />}>tonight&apos;s number, hatched where it rests on an estimate</Key>
      </>}
      foot={<>
        <p>Each strip has its own scale, starting at nothing, so compare a mark with its own ranges and not with the row above. The ranges are published in advance, set from how earlier technologies spread and from the long-run trend in output per hour; each variable&apos;s own page gives the reasoning. A number sits inside a range only when the site scores it there.{ranged.some((r) => r.lane === "outside") ? " A number hanging beneath its strip is one the site has not scored: the essay's sentence above reads where the number falls, and the site's own status does not yet confirm it." : ""} The lower rows have no range: the site grades them by whether the number rose or fell over a set window, and a rise can mean the profit gathering in one place or spreading out, never fast or slow.</p>
        <p>It does not show how sure each reading is, how each got here over time, or the fast variables the essay sets these against. The chip makers&apos; share is a share of the gross profit this site can measure, which includes an estimate for OpenAI and Anthropic; the value users keep is one survey&apos;s estimate.</p>
        <Drafted what="whose estimated profit sits inside the total the chip makers' share is measured against" />
      </>}
      table={
        <table className="w-full min-w-[40rem] border-collapse text-xs">
          <thead><tr><th className={th}>Slow variable</th><th className={th}>Tonight</th><th className={th}>As of</th><th className={th}>Graded against</th><th className={th}>Status on record</th><th className={th}>Evidence grade</th></tr></thead>
          <tbody>
            {ranged.map((r) => (
              <tr key={r.id}>
                <td className={td}><Link href={r.href} className={a}>{r.label}</Link></td>
                <td className={`${td} num whitespace-nowrap`}>{fmt(r.value, r.unit)}</td><td className={`${td} num whitespace-nowrap`}>{r.as_of}</td>
                <td className={td}>ordinary up to <span className="num">{fmtLine(r.edges[0].at, r.unit)}</span>; faster from <span className="num">{fmtLine(r.edges[1].at, r.unit)}</span></td>
                <td className={td}>{words(r.status)}{r.held.length ? <>: {r.held.includes("pending") ? "" : "held because "}{r.held.map((h) => HELD_WORDS[h] ?? h).join("; ")}</> : null}</td>
                <td className={td}>{r.grade}</td>
              </tr>
            ))}
            {directed.map((r) => (
              <tr key={r.id}>
                <td className={td}><Link href={r.href} className={a}>{r.label}</Link></td>
                <td className={`${td} num whitespace-nowrap`}>{fmt(r.end.value, r.unit)}</td><td className={`${td} num whitespace-nowrap`}>{r.end.as_of}</td>
                <td className={td}>its own reading of <span className="num">{fmt(r.start.value, r.unit)}</span> on <span className="num">{r.start.as_of}</span>; a move within <span className="num">{fmtLine(r.dead.band, r.unit)}</span>{r.unit === "share" ? " of the whole" : ""} does not count</td>
                <td className={td}>{words(r.status)}</td>
                <td className={td}>{r.grade}{r.estimate ? " (rests on an estimate)" : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      <div className="flex flex-col font-sans">
        <p className="mb-1 font-mono text-[10px] uppercase tracking-[0.08em] text-muted">Graded against a range: how far has it spread, and has output moved?</p>
        {ranged.map((r) => (
          <div key={r.id} className={`${side} border-t border-grid py-3`}>
            <div className="flex flex-col items-start gap-1.5">
              {name(r)}
              <span className="text-[1.25rem] leading-none"><Fact f={{ value: r.value, unit: r.unit, as_of: r.as_of, obs_ids: r.obs_ids, href: r.href, holds: null }} /></span>
              <StatusChip status={r.status} />
            </div>
            <div className="flex flex-col gap-1">
              <RangeStrip r={r} edge={(v) => fmtLine(v, r.unit)} tip={rangeTip(r)} />
              {r.held.length ? <p className="text-[12px] leading-snug text-ink-2">{r.held.includes("pending") ? "Not yet rescored" : "Held, not scored"}: the number falls in the {ZONE_WORDS[r.falls]} range, but {r.held.map((h) => HELD_WORDS[h] ?? h).join("; ")}.</p> : null}
            </div>
          </div>
        ))}
        <p className="mt-4 mb-1 font-mono text-[10px] uppercase tracking-[0.08em] text-muted">Graded by direction: where is the money going?</p>
        {directed.map((r) => (
          <div key={r.id} className={`${side} border-t border-grid py-3`}>
            <div className="flex flex-col items-start gap-1.5">
              {name(r)}
              <span className="text-[1.25rem] leading-none"><Fact f={{ value: r.end.value, unit: r.unit, as_of: r.end.as_of, obs_ids: r.end.obs_ids, href: r.href, holds: null }} /></span>
              <StatusChip status={r.status} />
            </div>
            <div className="flex flex-col gap-1.5 sm:pt-2">
              <DirectionStrip r={r} tip={dirTip(r)} whole={r.unit === "share" ? "the whole of the profit measured" : undefined} />
              <p className="text-[12px] leading-snug text-ink-2">From <span className="num">{fmt(r.start.value, r.unit)}</span> on <span className="num">{r.start.as_of}</span>, the start of the window the rule compares. A rise reads as {r.higher_is}.{r.estimate ? " Rests on an estimate." : ""}</p>
            </div>
          </div>
        ))}
      </div>
    </Figure>
  );
}

export function ExitsFigure({ doc }: { doc: ArgumentDoc }) {
  const x = doc.figures.exits;
  return (
    <Figure
      id="fig-exits"
      title="The tests the argument is held to, and whether each is met tonight"
      note={`${KIND_LABEL.chart} of the nightly test's results`}
      keys={<>
        <Key swatch={<CondMark holds={true} />}>a condition that is met tonight</Key>
        <Key swatch={<CondMark holds={false} />}>not met</Key>
        <Key swatch={<CondMark holds={null} />}>cannot be tested yet; the table says why</Key>
        {x.rows.some((r) => r.state === "contradicted") ? <Key swatch={<CondMark holds={true} counter />}>running the other way: the opposite happened: the chip makers&apos; share rose, so the move up to the labs the site once expected has not come. This is the test the essay says has already failed</Key> : null}
      </>}
      foot={<>
        <p>Each row is a test from the list below, split into the conditions the nightly run checks; the plain wording of each condition is this site&apos;s, and the exact line and tonight&apos;s reading are in the table. Not every test would prove the argument wrong if it were met: the map at the top of the essay says which way each one cuts. A test is met only when all of its conditions are met at once, so a tick on its own decides nothing: output growing, for one, is the usual state of the economy. It does not show how far each reading is from its line (the table gives both), or how likely any test is to be met.</p>
        <Drafted what="whose share of the profit and whose own claims these tests read" />
      </>}
      table={
        <table className="w-full min-w-[40rem] border-collapse text-xs">
          <thead><tr><th className={th}>Test</th><th className={th}>Condition, as the nightly run states it</th><th className={th}>Tonight&apos;s reading</th><th className={th}>Result</th></tr></thead>
          <tbody>
            {x.rows.flatMap((r) => r.conds.map((c, i) => (
              <tr key={`${r.monitor}-${i}`}>
                <td className={td}>{i === 0 ? r.label : ""}</td>
                <td className={td}>{c.counter ? "Opposite test: " : ""}{c.text}</td>
                <td className={`${td} num`}>{c.detail}</td>
                <td className={td}>{COND_WORDS[String(c.holds)]}</td>
              </tr>
            )))}
          </tbody>
        </table>
      }
    >
      <div className="flex flex-col font-sans">
        <p className="pb-3 text-[13px] leading-snug text-ink-2">
          Of <span className="num text-ink">{x.counts.exits}</span> tests tonight: <span className="num text-ink">{x.counts.met}</span> {STATE_WORDS.supported}, <span className="num text-ink">{x.counts.unsupported}</span> {STATE_WORDS.unsupported}, <span className="num text-ink">{x.counts.contradicted}</span> {STATE_WORDS.contradicted}, <span className="num text-ink">{x.counts.untestable}</span> that {STATE_WORDS.untestable}.
        </p>
        {x.rows.map((r) => (
          <div key={r.monitor} className={`${side} border-t border-grid py-3`}>
            <div className="flex flex-col items-start gap-1.5">
              <span className="text-[14px] font-semibold leading-tight text-ink">{r.label}</span>
              <StateChip state={r.state} />
              <span className="text-[12px] leading-snug text-muted">{r.conds.some((c) => c.either) ? "counts only when every condition is met at once, with one of the either-or pair" : "counts only when every condition is met at once"}</span>
            </div>
            <ul className="flex flex-col gap-1.5">
              {r.conds.map((c, i) => (
                <li key={i} className={`flex items-start gap-2 text-[13px] leading-snug ${c.counter ? "mt-1 border-t border-dashed border-grid pt-2" : ""}`}>
                  <CondMark holds={c.holds} counter={c.counter} />
                  <span className="text-ink">{c.either && !r.conds[i - 1]?.either ? <span className="mr-1.5 font-mono text-[10px] uppercase tracking-[0.08em] text-muted">either</span> : null}{c.either && r.conds[i - 1]?.either ? <span className="mr-1.5 font-mono text-[10px] uppercase tracking-[0.08em] text-muted">or</span> : null}{c.label}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Figure>
  );
}
