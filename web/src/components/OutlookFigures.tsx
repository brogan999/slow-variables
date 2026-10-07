import { Figure, Key } from "@/components/Figure";
import { ClaimState, Whose } from "@/components/OutlookParts";
import { Ends, Gate, HOLLOW, LookMark, LookRows, LookSwatch, Onward } from "@/components/diagrams/outlook";
import { KIND_LABEL, ShareBars, Swatch } from "@/components/diagrams/kit";
import type { OutlookDispute, OutlookDoc, OutlookLook, OutlookSettleMark, OutlookSide } from "@/lib/data";
import { CLAIM_WORDS } from "@/lib/format";

// The outlook's figures of the debate itself. Every count, order and width is the export's (outlook.figures); a claim's
// state is the page's own, and "can't be tested yet" is only split by whether a test has been written.
const LOOKS: OutlookLook[] = ["holding", "failing", "both", "waiting", "no_test"];
const LOOK_WORD: Record<OutlookLook, string> = {
  holding: CLAIM_WORDS.holding, failing: CLAIM_WORDS.failing, both: CLAIM_WORDS.both,
  waiting: "can't be tested yet: a test is written and waiting", no_test: "can't be tested yet: no reading tests it",
};
const LOOK_HEAD: Record<OutlookLook, string> = { holding: "Holding", failing: "Failing", both: "Both sides expect it", waiting: "Test waiting", no_test: "No test yet" };
// A dispute read against a line is drawn three ways, by what was read; the rest are drawn as in the first figure.
const REACHES: OutlookSettleMark[] = ["told_apart", "held", "missed", "shared", "waiting", "no_test"];
const REACH_WORD: Record<OutlookSettleMark, string> = {
  told_apart: "a claim on it met its line tonight and carries a test of what the rival expects",
  held: "a claim on it met its line tonight; this does not say which side is right",
  missed: "a claim on it missed its line tonight, and none met one",
  shared: "read tonight, but only readings both sides expect",
  waiting: "a test is written and waiting on a date or a reading",
  no_test: "no reading tests any claim on either side",
};
const REACH_HEAD: Record<OutlookSettleMark, string> = { told_apart: "Met a line, with a test for the rival", held: "Met a line, no test for the rival", missed: "Missed a line", shared: "Only shared readings", waiting: "Test waiting", no_test: "No test yet" };
const WHOSE: Record<string, string> = { author: "A named writer's own argument", extension: "A writer's argument, carried further by this site", site: "This site's own position" };
// Each tie named here is one a drawn writer's source states in the ledger (tests/test_outlook_figures.py checks it).
const DRAFTED = "These figures were drafted by Claude, an AI model made by Anthropic. Several of these positions are about that lab's business, and among the writers drawn here are advisers to it, a writer at its institute and the founder of a firm that holds a stake in it; each writer's ties are given with their source at the foot of the page. Every count and mark comes from the ledger and its nightly tests, not from the model.";

const lookKeys = (drawn: Partial<Record<OutlookLook, number | boolean>>) => LOOKS.filter((k) => drawn[k]).map((k) => <Key key={k} swatch={<LookSwatch look={k} />}>{LOOK_WORD[k]}</Key>);
const titles = (doc: OutlookDoc) => Object.fromEntries(doc.positions.map((p) => [p.id, p]));

function ClaimMarks({ doc, ids }: { doc: OutlookDoc; ids: string[] }) {
  const f = doc.figures;
  return <>{ids.map((id) => <LookMark key={id} look={f.looks[id]} href={`#claim-${id}`} tip={`${f.texts[id]} (${LOOK_WORD[f.looks[id]]})`} />)}</>;
}

function Side({ doc, s }: { doc: OutlookDoc; s: OutlookSide }) {
  const p = titles(doc)[s.id];
  return (
    <div className="flex min-w-0 flex-col gap-0.5">
      <a href={`#position-${p.id}`} className="text-[14px] font-medium leading-snug text-ink decoration-axis underline-offset-2 hover:underline">{p.title}</a>
      <span className="text-[12px] leading-snug text-ink-2"><Whose doc={doc} p={p} /></span>
      {s.claims.length ? <div className="-mx-1 flex flex-wrap"><ClaimMarks doc={doc} ids={s.claims} /></div> : <span className="pt-0.5 font-mono text-[11px] text-muted">names no claim yet</span>}
    </div>
  );
}

function Dispute({ doc, d }: { doc: OutlookDoc; d: OutlookDispute }) {
  const pos = titles(doc);
  const against = d.against ? pos[d.against] : null;
  // a position argued against under another question names that question
  const under = against && against.folio !== pos[d.left.id].folio ? doc.folios.find((x) => x.id === against.folio)?.kicker : null;
  return (
    <li className="grid gap-x-4 gap-y-1.5 border-t border-grid py-2.5 first:border-0 first:pt-0 sm:grid-cols-[minmax(0,1fr)_9.5rem_minmax(0,1fr)]">
      <Side doc={doc} s={d.left} />
      <span className="whitespace-nowrap font-mono text-[11px] uppercase tracking-wider text-muted sm:pt-0.5 sm:text-center">{d.right ? "↔ each other's rival" : "argues against →"}</span>
      {d.right ? <Side doc={doc} s={d.right} /> : against ? (
        <span className="flex min-w-0 flex-col gap-0.5 text-[14px] leading-snug text-ink-2">
          <a href={`#position-${against.id}`} className="decoration-axis underline-offset-2 hover:underline">{against.title}</a>
          <span className="font-mono text-[11px] text-muted">{under ? <>drawn under {under}</> : "drawn elsewhere under this question"}</span>
        </span>
      ) : null}
    </li>
  );
}

export function SidesMap({ doc }: { doc: OutlookDoc }) {
  const f = doc.figures;
  const s = f.sides;
  return (
    <Figure
      id="fig-sides"
      title="All the questions at once: the rival positions on each, and how each side's claims read tonight"
      note={KIND_LABEL.chart}
      keys={lookKeys(f.counts)}
      foot={<>
        <p>Each question is folded to a line: its claims, one mark each, and how many positions argue it. Open a question for its rows, the positions the essay argues first; each position is set out in full beneath its part of the essay.</p>
        <p>A row sets a position beside the position it argues against. Where the middle reads each other&apos;s rival, each position names the other, and the side the ledger lists first is on the left: that is usually the writer the essay starts from, and never a position this site wrote. Where it reads argues against, the challenge runs one way: the position on the left names the one on the right as its rival, and the one on the right does not name it back. A position that argues against one drawn elsewhere has a row of its own and names it, so every position is drawn once and every claim is counted once.</p>
        <p>One mark is one claim and links to it; every claim is listed in the last figure on this page, with its test where it has one. A mark is tonight&apos;s reading of that claim, not a score for whoever wrote it: a claim that can&apos;t be tested yet is not wrong, and a reading both sides expect is not a win for either. <span className="num">{s.positions}</span> positions and <span className="num">{s.claims}</span> claims are drawn, as read on {doc.as_of}; <span className="num">{s.layer_positions}</span> more positions, this site&apos;s own notes on single parts of the industry, sit on the stack&apos;s pages and are not drawn.</p>
        <p>{DRAFTED}</p>
      </>}
      table={
        <table className="data">
          <thead><tr><th scope="col">Question</th><th scope="col">Positions</th>{LOOKS.map((k) => <th key={k} scope="col">{LOOK_HEAD[k]}</th>)}<th scope="col">Claims</th></tr></thead>
          <tbody>
            {s.folios.map((fo) => <tr key={fo.id}><th scope="row">{fo.kicker}</th><td>{fo.positions}</td>{LOOKS.map((k) => <td key={k}>{fo.counts[k]}</td>)}<td>{fo.claims}</td></tr>)}
            <tr><th scope="row">All</th><td>{s.positions}</td>{LOOKS.map((k) => <td key={k}>{f.counts[k]}</td>)}<td>{s.claims}</td></tr>
          </tbody>
        </table>
      }
    >
      <div className="flex flex-col">
        {s.folios.map((fo) => {
          const rows = [...fo.main, ...fo.more];
          return (
            <details key={fo.id} className="border-t border-grid py-2.5 first:border-0 first:pt-0 last:pb-0">
              <summary className="cursor-pointer">
                <span className="inline-grid w-[calc(100%-1.5rem)] gap-x-3 gap-y-1 align-top sm:grid-cols-[15rem_minmax(0,1fr)_auto] sm:items-start">
                  <span className="text-[14px] font-medium leading-snug text-ink">{fo.kicker}</span>
                  <span className="-m-1 flex flex-wrap"><ClaimMarks doc={doc} ids={rows.flatMap((d) => [...d.left.claims, ...(d.right?.claims ?? [])])} /></span>
                  <span className="whitespace-nowrap font-mono text-[11px] text-muted"><span className="num">{fo.positions}</span> positions</span>
                </span>
              </summary>
              <ul className="mb-2 mt-3 flex flex-col border-l border-grid pl-3 sm:pl-4">{rows.map((d) => <Dispute key={d.key} doc={doc} d={d} />)}</ul>
            </details>
          );
        })}
      </div>
    </Figure>
  );
}

const count = "num text-2xl leading-none text-ink";

// How a claim gets its word. The steps are the method's own; the counts are tonight's.
export function MethodFlow({ doc }: { doc: OutlookDoc }) {
  const f = doc.figures;
  return (
    <Figure
      id="fig-method"
      title="How a claim gets its word each night"
      note={`${KIND_LABEL.model}; the counts are tonight's`}
      keys={<>
        <Key swatch={<span className="inline-block h-2.5 w-4 border border-axis bg-surface-2" />}>a question asked of every claim, in this order</Key>
        <Key swatch={<span className="inline-block h-2.5 w-4 border border-ink bg-surface" />}>where a claim stops, and how many stop there tonight</Key>
      </>}
      foot={<p>The boxes draw the steps this site follows each night, not a measurement; the counts in them are the page&apos;s on {doc.as_of}. A claim moves on when a reading arrives and can move back when its reading grows too old. A claim that meets its line also can&apos;t be tested while its rival&apos;s test has no reading, because a win needs the rival&apos;s reading too; a claim that misses its line is failing either way. A date has come when the reading itself is dated on or after it, not when the calendar says so; only for a record that moves just when it is broken does the calendar count, less an allowance for results to be published. Holding means a reading met a line tonight, not that the claim has been proved, and not that the rival expected otherwise: <span className="num">{f.holding_no_rival_test}</span> of the <span className="num">{doc.tally.holding}</span> holding claims have no test for the rival.</p>}
    >
      <ol className="flex flex-col gap-2">
        <Ends>
          <span className="eyebrow">A claim</span>
          <span className={count}>{f.sides.claims}</span>
          <span className="basis-full text-[13px] leading-snug text-ink-2">Each names what would prove it wrong. A claim with a test is set against a reading and a line.</span>
        </Ends>
        <Onward word="every night" />
        <Gate ask="Is there a reading to test it tonight?" why="Not when no reading tests it, when the reading or the reading it is compared with is missing or too old, or when the claim is about reaching a line by a date that has not come and the reading is still short of it." out="no">
          <span className="flex flex-wrap items-center gap-2"><ClaimState state="untestable" /><span className={count}>{doc.tally.untestable}</span></span>
          <span className="text-[13px] leading-snug text-ink-2"><span className="num text-ink">{f.counts.no_test}</span> have no test yet; <span className="num text-ink">{f.counts.waiting}</span> have a test that is waiting.</span>
        </Gate>
        <Onward word="yes" />
        <Gate ask="Does the reading meet the claim's line?" out="no">
          <span className="flex flex-wrap items-center gap-2"><ClaimState state="failing" /><span className={count}>{doc.tally.failing}</span></span>
        </Gate>
        <Onward word="yes" />
        <Gate ask="Does the rival position expect the same reading?" why="If it does, tonight's reading cannot tell the sides apart." out="yes">
          <span className="flex flex-wrap items-center gap-2"><ClaimState state="both" /><span className={count}>{doc.tally.both}</span></span>
          <span className="text-[13px] leading-snug text-ink-2">Not counted as a win for either side.</span>
        </Gate>
        <Onward word="no, the rival names no test, or the rival's date has passed" />
        <Ends out>
          <ClaimState state="holding" /><span className={count}>{doc.tally.holding}</span>
          <span className="basis-full text-[13px] leading-snug text-ink-2"><span className="num text-ink">{f.holding_no_rival_test}</span> of them have no test for the rival.</span>
        </Ends>
      </ol>
    </Figure>
  );
}

export function DisputeReach({ doc }: { doc: OutlookDoc }) {
  const f = doc.figures.settle;
  const pos = titles(doc);
  const name = (key: string) => `${pos[key].title}, against ${pos[pos[key].rival]?.title ?? "no named rival"}`;
  return (
    <Figure
      id="fig-settle"
      title="Which disputes tonight's readings reach, question by question"
      note={KIND_LABEL.chart}
      keys={REACHES.filter((k) => f.marks[k]).map((k) => <Key key={k} swatch={<LookSwatch look={k} />}>{REACH_WORD[k]}</Key>)}
      foot={<p>One mark is one dispute from the first figure: a pair of rival positions, or a position that argues against one drawn elsewhere; it links to the position. Its fill is how much this site could read on it tonight, taking the claim that got furthest on either side, in this order: a reading that met a claim&apos;s line, then a reading that missed one, then a reading both sides expect, then a test written and waiting, then no test at all. In <span className="num">{f.counts.no_test}</span> of the <span className="num">{f.n}</span> disputes no claim on either side has a test, so nothing this site reads bears on them yet. A dark mark does not mean either side has the better of the argument. A single claim that met its line is enough to fill it, and in only <span className="num">{f.told_apart}</span> of the <span className="num">{f.dark}</span> dark disputes, the ringed marks, does that claim carry a test of what the rival expects; in the rest this site has not written down what the rival would expect of the same reading. An orange mark is a dispute where a claim missed its line and none met one, which does not hand the argument to the other side either. Across the page, <span className="num">{doc.figures.holding_no_rival_test}</span> of the <span className="num">{doc.tally.holding}</span> claims that are holding have no test for the rival. {DRAFTED}</p>}
      table={<>
        <table className="data">
          <thead><tr><th scope="col">Question</th>{REACHES.map((k) => <th key={k} scope="col">{REACH_HEAD[k]}</th>)}<th scope="col">Disputes</th></tr></thead>
          <tbody>
            {f.rows.map((r) => <tr key={r.id}><th scope="row">{r.label}</th>{REACHES.map((k) => <td key={k}>{r.marks[k]}</td>)}<td>{r.n}</td></tr>)}
            <tr><th scope="row">All</th>{REACHES.map((k) => <td key={k}>{f.marks[k]}</td>)}<td>{f.n}</td></tr>
          </tbody>
        </table>
        <div className="mt-4 flex min-w-[16rem] flex-col gap-3 text-[13px] leading-snug">
          <p className="eyebrow">Which dispute each mark is, in the order drawn</p>
          {f.rows.map((r) => (
            <div key={r.id}>
              <p className="font-medium text-ink">{r.label}</p>
              <ol className="mt-1 flex flex-col gap-1.5 text-ink-2">
                {r.cells.map((c) => (
                  <li key={c.key} className="grid grid-cols-[0.75rem_minmax(0,1fr)] items-baseline gap-x-2">
                    <span className="mt-1 flex self-start"><LookSwatch look={c.mark} /></span>
                    <span><a href={`#position-${c.key}`} className="text-ink decoration-grid underline-offset-2 hover:underline">{name(c.key)}</a> <span className="text-muted">· {REACH_WORD[c.mark]} · claims with a test: <span className="num">{c.tested}</span> of <span className="num">{c.claims}</span></span></span>
                  </li>
                ))}
              </ol>
            </div>
          ))}
        </div>
      </>}
      tableLabel="The numbers, and which dispute each mark is"
    >
      <LookRows
        label="Each question's disputes, one mark each, by how far tonight's readings reach"
        rows={f.rows.map((r) => ({
          key: r.id, name: r.label,
          marks: r.cells.map((c) => <LookMark key={c.key} look={c.mark} href={`#position-${c.key}`} tip={`${name(c.key)}: ${REACH_WORD[c.mark]}`} />),
          tail: <>{r.counts.no_test} of {r.n} where no claim has a test</>,
        }))}
      />
    </Figure>
  );
}

export function WhoseBars({ doc }: { doc: OutlookDoc }) {
  const f = doc.figures.whose;
  return (
    <Figure
      id="fig-whose"
      title="Whose arguments these are: the writers' own, the writers' carried further, and this site's"
      note={KIND_LABEL.chart}
      keys={<>
        <Key swatch={<Swatch fill="var(--s2)" />}>positions that make a claim</Key>
        <Key swatch={<span className="inline-block h-2.5 w-4" style={{ background: HOLLOW }} />}>positions that name no claim yet</Key>
      </>}
      foot={<>
        <p>Each bar counts the positions on this page credited that way, on one scale, so a longer bar is more positions. It is a count, not a ranking of writers and not a measure of who is right. Carried further means this site took a named writer&apos;s argument beyond what they wrote, and says so on the position.</p>
        <p><span className="num">{f.site_rivals}</span> of this site&apos;s own positions share a row with a writer&apos;s position, each naming the other as its rival, and most of this site&apos;s own positions name no claim yet; where that is so, only the writer&apos;s side of the dispute can be tested. <span className="num">{f.site_readings}</span> claims are this site&apos;s reading of a writer&apos;s position, not the writer&apos;s own words; the table counts them as this site&apos;s.</p>
        <p>The writers are few: <span className="num">{f.top_two}</span> of the <span className="num">{f.named}</span> positions that name a writer are credited to one or both of the same two, out of <span className="num">{f.writers}</span> writers or groups of writers credited in all. The sources at the foot of the page say who.</p>
        <p>{DRAFTED}</p>
      </>}
      table={
        <table className="data">
          <thead><tr><th scope="col">Whose</th><th scope="col">Positions</th><th scope="col">Make a claim</th><th scope="col">Name no claim yet</th><th scope="col">Claims credited this way</th></tr></thead>
          <tbody>{f.rows.map((r) => <tr key={r.id}><th scope="row">{WHOSE[r.id]}</th><td>{r.n}</td><td>{r.with_claim}</td><td>{r.without}</td><td>{r.claims}</td></tr>)}</tbody>
        </table>
      }
    >
      <ShareBars
        label="Positions on this page, by whose argument each is"
        rows={f.rows.map((r) => ({
          name: WHOSE[r.id], note: `${r.n}`,
          segs: r.bar.map((b) => ({ key: b.part, x: b.x, w: b.w, fill: b.part === "without" ? HOLLOW : "var(--s2)", tip: `${WHOSE[r.id]}: ${b.n} ${b.part === "without" ? "name no claim yet" : "make a claim"}` })),
        }))}
      />
    </Figure>
  );
}

export function DueCalendar({ doc }: { doc: OutlookDoc }) {
  const f = doc.figures;
  const d = f.due;
  const marks = d.years.flatMap((y) => y.marks);
  const drawn = Object.fromEntries(marks.map((m) => [f.looks[m.claim], true]));
  const claims = Object.fromEntries(doc.claims.map((c) => [c.id, c]));
  const pos = titles(doc);
  const OUTLINE = { background: "var(--surface)", boxShadow: "inset 0 0 0 1.5px var(--ink-2)" };
  return (
    <Figure
      id="fig-due"
      title="The claims that name a date, by the year the date falls"
      note={KIND_LABEL.chart}
      keys={<>
        {lookKeys(drawn)}
        <Key swatch={<span className="inline-block h-3 w-3" style={OUTLINE} />}>square: the date by which the claim says it will be shown right or wrong</Key>
        <Key swatch={<span className="inline-block h-3 w-3 rounded-full" style={OUTLINE} />}>round: the rival can live with the same reading only until then</Key>
      </>}
      foot={<p>Only claims that name a date are drawn: <span className="num">{d.dated}</span> do and <span className="num">{d.undated}</span> do not, though each of those names what would prove it wrong. A date settles nothing for a claim that no reading tests: <span className="num">{d.with_test}</span> of the dated claims have a test, and for the rest the date will pass with nothing read unless a test is written first. A year with no mark is a year no claim names. <span className="num">{d.site}</span> of the dated claims are this site&apos;s own reading, and for those the date is this site&apos;s too; the table says whose each claim is. The fill is tonight&apos;s reading, as in the first figure; follow a mark to its claim. {DRAFTED}</p>}
      table={<>
        <table className="data">
          <thead><tr><th scope="col">Date</th><th scope="col">Claim</th><th scope="col">Whose claim</th><th scope="col">What the date is</th><th scope="col">Tonight</th></tr></thead>
          <tbody>
            {marks.map((m) => (
              <tr key={m.claim}>
                <td className="whitespace-nowrap">{m.date}{m.passed ? ", already passed" : ""}</td>
                <td className="min-w-[14rem]"><a href={`#claim-${m.claim}`} className="decoration-grid underline-offset-2 hover:underline">{f.texts[m.claim]}</a></td>
                <td className="min-w-[9rem] text-ink-2"><Whose doc={doc} p={pos[claims[m.claim].position]} c={claims[m.claim]} /></td>
                <td className="min-w-[11rem]">{m.kind === "due" ? "the date by which the claim says it will be shown right or wrong" : "the rival can live with the same reading until then"}</td>
                <td>{LOOK_WORD[f.looks[m.claim]]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </>}
    >
      <div role="group" aria-label="Dated claims, one mark each, in the year each date falls" className="flex items-end gap-1 border-b border-axis">
        {d.years.map((y) => (
          <div key={y.year} className="flex min-w-0 flex-1 flex-col items-center justify-end">
            {y.marks.map((m) => <LookMark key={m.claim} look={f.looks[m.claim]} round={m.kind === "rival_until"} href={`#claim-${m.claim}`} tip={`${m.date}${m.site ? ", a date this site set" : ""}: ${f.texts[m.claim]} (${LOOK_WORD[f.looks[m.claim]]})`} />)}
          </div>
        ))}
      </div>
      <div aria-hidden className="flex gap-1 pt-1.5">
        {d.years.map((y) => <span key={y.year} className="num min-w-0 flex-1 text-center text-[11px] text-ink-2">{y.year}</span>)}
      </div>
    </Figure>
  );
}
