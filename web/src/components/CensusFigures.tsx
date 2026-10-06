import { Mark, Marks, Plot } from "@/components/chart";
import { AllThreeMark, Dot, DotRows, PlotLine, ScaleBars, VoteMark } from "@/components/diagrams/census";
import { KIND_LABEL, ShareBars, Swatch } from "@/components/diagrams/kit";
import { Figure, Key } from "@/components/Figure";
import { CUT } from "@/components/FirmParts";
import type { CensusIndex, CensusRollupPlot } from "@/lib/data";
import { fmt } from "@/lib/format";

// The census page's figures (plan Part 45b). Every sum, share, width and position is the export's; a figure only
// places it. Each states its kind, keys every mark, and folds its numbers beneath as a table.

type Extra = { table?: React.ReactNode };
type Part = keyof typeof CUT;
const PARTS = Object.keys(CUT) as Part[];
const usd = (v: number | null | undefined) => (v === 0 ? "$0" : fmt(v, "USD"));
const pct = (v: number) => fmt(v, "share");
const SCREEN = <>a screen scored by three AI models, not a claim about what AI can do and not a forecast</>;
const th = "border-b border-ink py-2 pr-4 align-bottom font-medium text-ink-2";
const td = "py-2 pr-4 text-ink-2 tabular-nums";
const rowTh = "py-2 pr-4 font-medium text-ink";
const tbl = "w-full min-w-[34rem] border-collapse text-left text-[13px] leading-snug";
const TickKey = () => <Key swatch={<span className="inline-block h-3 w-0.5 bg-surface outline outline-1 outline-ink" />}>to its left, all three models pass</Key>;
const CutKeys = () => <>{PARTS.map((p) => <Key key={p} swatch={<Swatch fill={CUT[p][0]} />}>{CUT[p][1]}</Key>)}<TickKey /></>;
const Head = ({ cols }: { cols: string[] }) => <thead><tr>{cols.map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr></thead>;
const Both = ({ passes, agreed3 }: { passes: number; agreed3: number | null }) => <>{usd(passes)} <span className="text-muted">· all three {agreed3 === null ? "—" : usd(agreed3)}</span></>;
const both = (name: string, passes: number, agreed3: number | null) => `${name}: ${usd(passes)} passes; all three models pass ${agreed3 === null ? "—" : usd(agreed3)}`;

const QUESTION: Record<string, string> = {
  hours: "Can it be told within hours whether the work was done right?",
  check: "Does a check that already exists settle it?",
  stakes: "Is a single failure cheap?",
};
const GATE: Record<string, string> = { physical: "Needs a body", accountable: "A sign-off a person answers for" };

// The screen itself: what is left out, what each of the three questions holds back, and what is left.
export function ScreenFigure({ c }: { c: CensusIndex }) {
  const s = c.figures.screen;
  const step = "eyebrow mb-2";
  const share = (m: { usd: number; share: number }) => <>{usd(m.usd)} <span className="text-muted">· {pct(m.share)}</span></>;
  return (
    <Figure
      id="fig-screen"
      title="For most work that fails the screen, the reason given most often is that no existing check settles it"
      note={KIND_LABEL.chart}
      keys={<><Key swatch={<Swatch fill={CUT.physical[0]} />}>left out before the vote</Key><Key swatch={<Swatch fill={CUT.rest[0]} />}>the reason the models that voted no gave most often</Key><Key swatch={<Swatch fill={CUT.passes[0]} />}>{CUT.passes[1]}</Key><TickKey /></>}
      foot={<p>Every bar is a share of the {usd(s.payroll)} of knowledge payroll scored. From the census ({c.version}), {SCREEN}. Each task that fails carries the reason the models that voted no gave most often, set by the census&apos;s own code; where reasons tie, the task counts under each, so the middle bars overlap and do not add up. A question a task also fails, but less often, is not counted, so each bar is a floor for that question.</p>}
      table={
        <table className={tbl}>
          <Head cols={["Step", "Payroll", "Share of knowledge payroll"]} />
          <tbody title={s.ref}>
            {s.gates.map((g) => <tr key={g.id} className="border-b border-grid"><th scope="row" className={rowTh}>Left out: {GATE[g.id]}</th><td className={td}>{usd(g.usd)}</td><td className={td}>{pct(g.share)}</td></tr>)}
            <tr className="border-b border-grid"><th scope="row" className={rowTh}>Goes to the vote</th><td className={td}>{usd(s.voted.usd)}</td><td className={td}>{pct(s.voted.share)}</td></tr>
            {s.questions.map((q) => <tr key={q.id} className="border-b border-grid"><th scope="row" className={rowTh}>Most often given: {QUESTION[q.id]}</th><td className={td}>{usd(q.usd)}</td><td className={td}>{pct(q.share)}</td></tr>)}
            <tr className="border-b border-grid"><th scope="row" className={rowTh}>Passes the screen</th><td className={td}>{usd(s.passes)}</td><td className={td}>{pct(s.share_passes)}</td></tr>
            <tr className="border-b border-grid"><th scope="row" className={rowTh}>All three models pass</th><td className={td}>{usd(s.agreed3)}</td><td className={td}>{pct(s.share_agreed3)}</td></tr>
          </tbody>
        </table>
      }
    >
      <div className="flex flex-col gap-5">
        <div>
          <div className={step}>First, left out whatever the vote would say</div>
          <ScaleBars label="Payroll left out before the vote" valueWidth="15rem" nameWidth="13rem" rows={s.gates.map((g) => ({ key: g.id, name: GATE[g.id], w: g.w, fill: CUT.physical[0], value: share(g), tip: `${GATE[g.id]}: ${usd(g.usd)}, ${pct(g.share)} of knowledge payroll` }))} />
        </div>
        <div>
          <div className={step}>Then the vote on the other {usd(s.voted.usd)}: the reason given most often for the payroll that fails, as a share of all knowledge payroll</div>
          <ScaleBars label="Payroll that fails, by the reason given most often" valueWidth="15rem" nameWidth="13rem" rows={s.questions.map((q) => ({ key: q.id, name: QUESTION[q.id], w: q.w, fill: CUT.rest[0], value: share(q), tip: `Most often given, "${QUESTION[q.id]}": ${usd(q.usd)}, ${pct(q.share)} of knowledge payroll` }))} />
        </div>
        <div>
          <div className={step}>What is left passes</div>
          <ScaleBars label="Payroll that passes the screen" valueWidth="15rem" nameWidth="13rem" rows={[{ key: "passes", name: "Yes to all three questions, by two of the three models", strong: true, w: s.passes_w, tick: s.agreed3_x, tickTip: `All three models pass ${usd(s.agreed3)}`, value: <>{usd(s.passes)} <span className="text-muted">· {pct(s.share_passes)} · all three {usd(s.agreed3)}</span></>, tip: both("Passes the screen", s.passes, s.agreed3) }]} />
        </div>
      </div>
    </Figure>
  );
}

// The whole knowledge payroll as one strip, so the size of the part that passes is felt.
export function WholeFigure({ c }: { c: CensusIndex }) {
  const w = c.figures.whole;
  return (
    <Figure
      id="fig-whole"
      title="A small part of the knowledge payroll passes the screen"
      note={KIND_LABEL.chart}
      keys={<TickKey />}
      foot={<p>The strip is the whole {usd(w.payroll)} of knowledge payroll scored. From the census ({c.version}), {SCREEN}. All three models pass {usd(w.agreed3)}, which is {pct(w.share_agreed3)} of the whole. The last part is everything else: mostly work with no existing check that is also slow to judge or costly when wrong; work whose most-given reason is a missing check but on which the models split over whether anything else holds it; and a small part that is a sign-off a person answers for.</p>}
      table={
        <table className={tbl}>
          <Head cols={["Part of the knowledge payroll", "Payroll", "Share"]} />
          <tbody title={w.ref}>
            {w.parts.map((p) => <tr key={p.part} className="border-b border-grid"><th scope="row" className={`${rowTh} first-letter:uppercase`}>{CUT[p.part][1]}</th><td className={td}>{usd(p.usd)}</td><td className={td}>{pct(p.share)}</td></tr>)}
            <tr className="border-b border-grid"><th scope="row" className={rowTh}>Of what passes, all three models pass</th><td className={td}>{usd(w.agreed3)}</td><td className={td}>{pct(w.share_agreed3)}</td></tr>
          </tbody>
        </table>
      }
    >
      <div className="flex flex-col gap-4">
        <div role="img" aria-label={w.parts.map((p) => `${CUT[p.part][1]} ${pct(p.share)}`).join(", ")} className="relative h-10 w-full">
          {w.parts.map((p) => <div key={p.part} title={`${usd(p.usd)} ${CUT[p.part][1]}: ${pct(p.share)}`} className="absolute inset-y-0" style={{ left: `${p.x}%`, width: `${p.w}%`, background: CUT[p.part][0], boxShadow: "inset -1px 0 0 var(--surface)" }} />)}
          <div title={`All three models pass ${usd(w.agreed3)}`} className="absolute -inset-y-1 w-0.5 bg-surface" style={{ left: `${w.agreed3_x}%` }} />
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-3 md:grid-cols-4">
          {w.parts.map((p) => (
            <div key={p.part} className="border-t-4 pt-1.5" style={{ borderColor: CUT[p.part][0] }}>
              <div className="num text-[1.35rem] leading-none text-ink">{pct(p.share)}</div>
              <div className="mt-1 text-[12.5px] leading-snug text-ink-2">{CUT[p.part][1]}</div>
              <div className="mt-0.5 font-mono text-[11px] text-muted">{usd(p.usd)}{p.part === "passes" ? <> · all three {usd(w.agreed3)}</> : null}</div>
            </div>
          ))}
        </div>
      </div>
    </Figure>
  );
}

const JUDGE_FILL = (id: string) => (id === "rule" ? "var(--s1)" : id === "agreed3" ? "var(--s2)" : "var(--s3)");

// Who judges: the vote, the part all three pass, and each model alone, on one dollar axis.
export function JudgesFigure({ c }: { c: CensusIndex }) {
  const f = c.figure;
  if (!f) return null;
  return (
    <Figure
      id="fig-judges"
      title="The payroll that passes depends on which model judges it"
      note={KIND_LABEL.chart}
      keys={<><Key swatch={<Swatch fill="var(--s1)" />}>the rule: two of the three models pass</Key><Key swatch={<Swatch fill="var(--s2)" />}>all three models pass</Key><Key swatch={<Swatch fill="var(--s3)" />}>one model alone</Key></>}
      foot={<p>Of {usd(c.headline.payroll)} of knowledge payroll scored. From the census ({c.version}), {SCREEN}. The census&apos;s rule counts a task when at least two of the three models pass it. Each model alone would pass a different amount, which is why the part all three pass is shown beside every total.</p>}
      table={
        <table className={tbl}>
          <Head cols={["Who judges", "Payroll that passes"]} />
          <tbody title={f.ref}>{f.bars.map((b) => <tr key={b.id} className="border-b border-grid"><th scope="row" className={rowTh}>{b.label}</th><td className={td}>{usd(b.usd)}</td></tr>)}</tbody>
        </table>
      }
    >
      <ScaleBars label="Payroll that passes, by who judges it" ticks={f.ticks} valueWidth="4rem" nameWidth="17rem"
        rows={f.bars.map((b) => ({ key: b.id, name: b.label, strong: b.id === "rule", w: b.width, fill: JUDGE_FILL(b.id), value: usd(b.usd), tip: `${b.label}: ${usd(b.usd)}` }))} />
    </Figure>
  );
}

// The dial: each step of the rule, strictest first, on one dollar axis.
export function DialFigure({ c, table }: { c: CensusIndex } & Extra) {
  const d = c.figures.dial;
  return (
    <Figure
      id="fig-dial"
      title="Each looser step passes more payroll, and the biggest jump comes from letting a person&apos;s judgement count as the check"
      note={KIND_LABEL.chart}
      keys={<><Key swatch={<Swatch fill="var(--s1)" />}>passes at that step of the rule</Key><TickKey /></>}
      foot={<p>Steps run from the strictest rule to the loosest; the step in bold is the rule the census uses. From the census ({c.version}), {SCREEN}. At every step the models vote again, and the part all three pass is marked inside the bar.</p>}
      table={table}
    >
      <ScaleBars label="Payroll that passes at each step of the rule" ticks={d.ticks} nameWidth="19rem"
        rows={d.rows.map((r) => ({
          key: r.rule, title: r.ref, strong: r.headline, w: r.w, tick: r.agreed3_x, tickTip: `All three models pass ${usd(r.agreed3)}`,
          name: <>{r.rule}{r.label ? <span className={`block text-[12px] font-normal ${r.headline ? "text-ink" : "text-muted"}`}>{r.label}</span> : null}</>,
          value: <Both passes={r.passes} agreed3={r.agreed3} />, tip: both(r.rule, r.passes, r.agreed3),
        }))} />
    </Figure>
  );
}

type Shares = { share_passes: number; share_agreed3: number; share_waits_on_check: number; share_physical: number; share_rest: number };
const shareOf = (g: Shares, p: Part) => ({ passes: g.share_passes, waits_on_check: g.share_waits_on_check, physical: g.share_physical, rest: g.share_rest })[p];
const CUT_COLS = ["Passes the screen", "All three models pass", "Waits only on a check", "Needs a body", "Held for more than a missing check"];

type CutRow = Shares & { ref: string; bar: { part: Part; x: number; w: number }[]; agreed3_x: number };

// The firm page's four-way cut, for any grouping of the payroll: one stacked bar per row, and the same rows as a table.
function CutBars<T extends CutRow>({ rows, name, label }: { rows: T[]; name: (r: T) => string; label: string }) {
  return (
    <ShareBars label={label} rows={rows.map((r) => ({
      name: name(r), note: pct(r.share_passes),
      segs: r.bar.map((s) => ({ key: s.part, x: s.x, w: s.w, fill: CUT[s.part][0], tip: `${name(r)}: ${pct(shareOf(r, s.part))} ${CUT[s.part][1]}` })),
      tick: { x: r.agreed3_x, tip: `${name(r)}: all three models pass ${pct(r.share_agreed3)}` },
    }))} />
  );
}
function CutTable<T extends CutRow>({ rows, name, first }: { rows: T[]; name: (r: T) => string; first: string }) {
  return (
    <table className={`${tbl} min-w-[40rem]`}>
      <Head cols={[first, ...CUT_COLS]} />
      <tbody>{rows.map((r) => (
        <tr key={name(r)} className="border-b border-grid align-top" title={r.ref}>
          <th scope="row" className={rowTh}>{name(r)}</th>
          {[r.share_passes, r.share_agreed3, r.share_waits_on_check, r.share_physical, r.share_rest].map((v, i) => <td key={i} className={td}>{pct(v)}</td>)}
        </tr>
      ))}</tbody>
    </table>
  );
}

export function KindsFigure({ c }: { c: CensusIndex }) {
  const rows = c.kinds.groups;
  if (!rows?.length) return null;
  return (
    <Figure
      id="fig-kinds"
      title="What the screen says of each kind of job, best paid first"
      note={KIND_LABEL.chart}
      keys={<CutKeys />}
      foot={<p>Shares of each group&apos;s payroll; the figure beside a name is the share that passes. From the census ({c.version}), {SCREEN}. Groups are the occupation code&apos;s major groups, ordered by average pay; the census has no field for seniority, so this reads kinds of job, not rungs within one. A task passes when at least two of the three models pass it, and the tick marks the part all three pass.</p>}
      table={<CutTable rows={rows} name={(g) => g.name} first="Kind of job" />}
    >
      <CutBars rows={rows} name={(g) => g.name} label="Each kind of job's payroll, split by what the census screen says of it" />
    </Figure>
  );
}

export function FunctionsFigure({ c, table }: { c: CensusIndex } & Extra) {
  const rows = c.figures.functions;
  return (
    <Figure
      id="fig-functions"
      title="In most functions, more work waits on a check than passes"
      note={KIND_LABEL.chart}
      keys={<CutKeys />}
      foot={<p>Shares of each function&apos;s knowledge payroll, ordered by the share that passes, which is printed beside the name. From the census ({c.version}), {SCREEN}. The tick marks the part all three models pass. Work waiting only on a check is work at least two of the three models find quick to judge and cheap to get wrong, with no existing check to settle it.</p>}
      table={<div className="flex flex-col gap-6"><CutTable rows={rows} name={(f) => f.function} first="Function" />{table}</div>}
    >
      <CutBars rows={rows} name={(f) => f.function} label="Each function's knowledge payroll, split by what the census screen says of it" />
    </Figure>
  );
}

// Each model's own share, function by function, beside the vote and the part all three pass.
export function ScorersFigure({ c }: { c: CensusIndex }) {
  const s = c.figures.scorers;
  const who = (k: string) => c.scorer_names[k] ?? k;
  const name = (r: (typeof s.rows)[number]) => r.function ?? "All knowledge work";
  return (
    <Figure
      id="fig-scorers"
      title="In most functions the three models are far apart, and the same model is usually the highest"
      note={KIND_LABEL.chart}
      keys={<>{c.scorers.map((k, i) => <Key key={k} swatch={<Dot i={i} />}>{who(k)} alone</Key>)}<Key swatch={<VoteMark />}>the rule: two of the three pass</Key><Key swatch={<AllThreeMark />}>all three models pass</Key></>}
      foot={<p>Each mark is a share of the function&apos;s knowledge payroll; the line spans the lowest and the highest model. From the census ({c.version}), {SCREEN}. Each model&apos;s own share is its verdict under the same rule and the same exclusions. The same model re-scoring the same tasks also changed some verdicts, so small gaps between rows are noise. Where a function&apos;s marks would sit on top of one another, the rule&apos;s share and the share all three pass are printed in type instead of drawn. Where nothing passes, the marks sit together at zero.</p>}
      table={
        <table className={`${tbl} min-w-[40rem]`}>
          <Head cols={["Function", ...c.scorers.map((k) => `${who(k)} alone`), "The rule: two of the three", "All three models pass"]} />
          <tbody>{s.rows.map((r) => (
            <tr key={name(r)} className="border-b border-grid" title={r.ref}>
              <th scope="row" className={rowTh}>{name(r)}</th>
              {c.scorers.map((k) => <td key={k} className={td}>{pct(r.by_scorer[k].share)}</td>)}
              <td className={td}>{pct(r.share_passes)}</td><td className={td}>{pct(r.share_agreed3)}</td>
            </tr>
          ))}</tbody>
        </table>
      }
    >
      <DotRows label="Share of each function's knowledge payroll that passes, by who judges it" ticks={s.ticks}
        rows={s.rows.map((r) => ({
          key: name(r), name: name(r), strong: r.function === null, title: r.ref, lo: r.lo_x, spread: r.spread_w,
          dots: c.scorers.map((k) => ({ x: r.by_scorer[k].x, tip: `${name(r)}: ${who(k)} alone passes ${pct(r.by_scorer[k].share)}` })),
          vote: r.tight ? undefined : { x: r.vote_x, tip: `${name(r)}: the rule passes ${pct(r.share_passes)}` },
          allThree: r.tight ? undefined : { x: r.agreed3_x, tip: `${name(r)}: all three models pass ${pct(r.share_agreed3)}` },
          note: r.note_x === null ? undefined : { x: r.note_x, text: <>rule {pct(r.share_passes)} · all three {pct(r.share_agreed3)}</> },
        }))} />
    </Figure>
  );
}

// The places a rank label may take around its dot, in pixels; the export picks one (census.LABEL_SIDES, same names).
// A place in the further ring is tied back to its dot by a short line (`lead`, where the line ends).
// The export picks a place twice, for the plot's size on a phone and on a desk, and the page shows the one that fits.
type Side = { dx: number; dy: number; textAnchor: "start" | "middle" | "end"; lead?: [number, number] };
const SIDE: Record<string, Side> = {
  r: { dx: 8, dy: 4, textAnchor: "start" }, l: { dx: -8, dy: 4, textAnchor: "end" }, t: { dx: 0, dy: -8, textAnchor: "middle" }, b: { dx: 0, dy: 15, textAnchor: "middle" },
  tr: { dx: 7, dy: -5, textAnchor: "start" }, tl: { dx: -7, dy: -5, textAnchor: "end" }, br: { dx: 7, dy: 13, textAnchor: "start" }, bl: { dx: -7, dy: 13, textAnchor: "end" },
  r2: { dx: 18, dy: 4, textAnchor: "start", lead: [15, 0] }, l2: { dx: -18, dy: 4, textAnchor: "end", lead: [-15, 0] },
  t2: { dx: 0, dy: -19, textAnchor: "middle", lead: [0, -17] }, b2: { dx: 0, dy: 26, textAnchor: "middle", lead: [0, 15] },
  tr2: { dx: 14, dy: -12, textAnchor: "start", lead: [12, -11] }, tl2: { dx: -14, dy: -12, textAnchor: "end", lead: [-12, -11] },
  br2: { dx: 14, dy: 20, textAnchor: "start", lead: [12, 11] }, bl2: { dx: -14, dy: 20, textAnchor: "end", lead: [-12, 11] },
};

// Where a roll-up could start: every industry the list considers, by its two ingredients, with the list's cut drawn.
export function RollupFigure({ plot, version, table }: { plot: CensusRollupPlot; version: string } & Extra) {
  if (!plot.points?.length) return null;
  const tip = (p: CensusRollupPlot["points"][number]) => `${p.listed ? `${p.rank}. ` : ""}${p.title}: ${pct(p.share_total)} of payroll passes (${usd(p.passes)}; all three ${p.agreed3 === null ? "—" : usd(p.agreed3)}); ${pct(p.small_share)} of employment in small firms`;
  const listed = plot.points.filter((p) => p.listed);
  return (
    <Figure
      id="fig-rollup"
      title="The list is the industries where work that passes and small firms to buy multiply highest"
      note={KIND_LABEL.chart}
      keys={<><Key swatch={<span className="inline-block h-2.5 w-2.5 rounded-full bg-ink" />}>on the list, with its rank</Key><Key swatch={<span className="inline-block h-2.5 w-2.5 rounded-full border-[1.5px] border-s3 bg-surface" />}>considered, below the cut</Key><Key swatch={<span className="inline-block w-5 border-t-[1.5px] border-dashed border-ink-2" />}>the cut: the score of the last industry listed</Key></>}
      foot={<p>Up is more of an industry&apos;s payroll passing; right is more of its employment in small firms; the score is one times the other, so the dashed line is where the list ends. The share that passes is from the census ({version}), {SCREEN}; the part all three models pass is in the table beneath. Employment in small firms is from the Census Bureau&apos;s Statistics of US Businesses. Only industries that clear the list&apos;s floors are drawn. Industries just either side of the line are not meaningfully apart.</p>}
      tableLabel="The numbers, and every industry drawn"
      table={
        <div className="flex flex-col gap-6">
          {table}
          <table className={`${tbl} min-w-[40rem]`}>
            <Head cols={["Rank by score", "Industry", "Share of payroll that passes", "Passes the screen", "All three models pass", "Employment in small firms"]} />
            <tbody>{plot.points.map((p) => (
              <tr key={p.naics} className="border-b border-grid" title={p.ref}>
                <td className={td}>{p.rank}</td><th scope="row" className={rowTh}>{p.title}</th><td className={td}>{pct(p.share_total)}</td><td className={td}>{usd(p.passes)}</td><td className={td}>{p.agreed3 === null ? "—" : usd(p.agreed3)}</td><td className={td}>{pct(p.small_share)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      }
    >
      <Plot x={plot.x.ticks} y={{ ...plot.y, unit: "Share of payroll that passes the screen" }} label="Industries by the share of payroll that passes and the share of employment in small firms" tall>
        <PlotLine points={plot.cut_points} />
        <Marks>
          {plot.points.filter((p) => !p.listed).map((p) => <Mark key={p.naics} p={{ x: p.x, y: p.y, href: null }} tip={tip(p)} stop={false} hollow r={3.5} stroke="var(--s3)" />)}
          {listed.map((p) => <Mark key={p.naics} p={{ x: p.x, y: p.y, href: `#naics-${p.naics}` }} tip={tip(p)} stop={p.rank === 1} r={4.5} />)}
        </Marks>
        {([["md:hidden", (p) => p.label], ["max-md:hidden", (p) => p.label_wide]] as [string, (p: (typeof listed)[number]) => string | undefined][]).map(([show, place]) => (
          <g key={show} className={show} aria-hidden>
            {listed.map((p) => {
              const { lead, ...at } = SIDE[place(p) ?? "r"];
              return (
                <svg key={p.naics} x={`${p.x}%`} y={`${p.y}%`} overflow="visible" className="pointer-events-none">
                  {lead ? <line x1={0} y1={0} x2={lead[0]} y2={lead[1]} stroke="var(--ink)" strokeWidth={0.75} /> : null}
                  <text {...at} className="fill-ink font-mono text-[10.5px] font-medium" style={{ paintOrder: "stroke", stroke: "var(--surface)", strokeWidth: 3 }}>{p.rank}</text>
                </svg>
              );
            })}
          </g>
        ))}
      </Plot>
      <div className="mt-1 text-center font-mono text-[11px] text-muted">Share of employment in small firms</div>
      <ol className="mt-4 grid grid-cols-1 gap-x-6 gap-y-0.5 text-[12.5px] leading-snug text-ink-2 sm:grid-cols-2">
        {listed.map((p) => <li key={p.naics} className="flex gap-2"><span className="w-5 shrink-0 text-right font-mono text-[11px] text-ink">{p.rank}</span><span>{p.title}</span></li>)}
      </ol>
    </Figure>
  );
}
