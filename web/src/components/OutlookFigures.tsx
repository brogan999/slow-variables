import { Figure, Key } from "@/components/Figure";
import { ClaimState, Whose } from "@/components/OutlookParts";
import { Ends, Gate, HOLLOW, LookMark, LookRows, LookSwatch, Onward } from "@/components/diagrams/outlook";
import { KIND_LABEL, ShareBars, Swatch } from "@/components/diagrams/kit";
import type { OutlookDispute, OutlookDoc, OutlookLook, OutlookReach, OutlookSide } from "@/lib/data";
import { CLAIM_WORDS } from "@/lib/format";

// The outlook's figures of the debate itself. Every count, order and width is the export's (outlook.figures); a claim's
// state is the page's own, and "can't be tested yet" is only split by whether a test has been written.
const LOOKS: OutlookLook[] = ["holding", "failing", "both", "waiting", "no_test"];
const LOOK_WORD: Record<OutlookLook, string> = {
  holding: CLAIM_WORDS.holding, failing: CLAIM_WORDS.failing, both: CLAIM_WORDS.both,
  waiting: "can't be tested yet: a test is written and waiting", no_test: "can't be tested yet: no reading tests it",
};
const LOOK_HEAD: Record<OutlookLook, string> = { holding: "Holding", failing: "Failing", both: "Both sides expect it", waiting: "Test waiting", no_test: "No test yet" };
const REACHES: OutlookReach[] = ["read", "shared", "waiting", "no_test"];
const REACH_WORD: Record<OutlookReach, string> = {
  read: "a claim on it met or missed its line tonight",
  shared: "read tonight, but only readings both sides expect",
  waiting: "a test is written and waiting on a date or a reading",
  no_test: "no reading tests any claim on either side",
};
const REACH_HEAD: Record<OutlookReach, string> = { read: "Read against a line", shared: "Only shared readings", waiting: "Test waiting", no_test: "No test yet" };
const WHOSE: Record<string, string> = { author: "A named writer's own argument", extension: "A writer's argument, carried further by this site", site: "This site's own position" };
const DRAFTED = "These figures were drafted by Claude, an AI model made by Anthropic, a lab whose business several of these positions are about; every count and mark comes from the ledger and its nightly tests, not from the model.";

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
  const against = d.against ? titles(doc)[d.against] : null;
  return (
    <li className="grid gap-x-4 gap-y-1.5 border-t border-grid py-2.5 first:border-0 first:pt-0 sm:grid-cols-[minmax(0,1fr)_8.5rem_minmax(0,1fr)]">
      <Side doc={doc} s={d.left} />
      <span className="whitespace-nowrap font-mono text-[11px] uppercase tracking-wider text-muted sm:pt-0.5 sm:text-center">{d.right ? "each other's rival" : "argues against"}</span>
      {d.right ? <Side doc={doc} s={d.right} /> : against ? (
        <span className="flex min-w-0 flex-col gap-0.5 text-[14px] leading-snug text-ink-2">
          <a href={`#position-${against.id}`} className="decoration-axis underline-offset-2 hover:underline">{against.title}</a>
          <span className="font-mono text-[11px] text-muted">drawn in a row of its own</span>
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
        <p>A row sets a position beside the position it argues against; left and right carry no meaning. Where two positions name each other as rivals they share a row. A position that argues against one drawn elsewhere has a row of its own and names it, so every position is drawn once and every claim is counted once. The rows shown hold each question&apos;s main positions; the rest are folded under it, as they are beneath each part of the essay.</p>
        <p>One mark is one claim and links to it; every claim is listed with its test in the last figure on this page. A mark is tonight&apos;s reading of that claim, not a score for whoever wrote it: a claim that can&apos;t be tested yet is not wrong, and a reading both sides expect is not a win for either. <span className="num">{s.positions}</span> positions and <span className="num">{s.claims}</span> claims are drawn, as read on {doc.as_of}; <span className="num">{s.layer_positions}</span> more positions, this site&apos;s own notes on single parts of the industry, sit on the stack&apos;s pages and are not drawn.</p>
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
      <div className="flex flex-col gap-6">
        {s.folios.map((fo) => (
          <section key={fo.id} className="flex flex-col gap-3">
            <h3 className="eyebrow border-b border-axis pb-1.5">{fo.kicker}</h3>
            <ul className="flex flex-col">{fo.main.map((d) => <Dispute key={d.key} doc={doc} d={d} />)}</ul>
            {fo.more.length ? (
              <details className="group">
                <summary className="cursor-pointer text-[13px] text-ink-2 underline decoration-grid underline-offset-4 hover:text-ink">More positions on this question</summary>
                <ul className="mt-3 flex flex-col">{fo.more.map((d) => <Dispute key={d.key} doc={doc} d={d} />)}</ul>
              </details>
            ) : null}
          </section>
        ))}
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
      foot={<p>The boxes draw the steps this site follows each night, not a measurement; the counts in them are the page&apos;s on {doc.as_of}. A claim moves on when a reading arrives and can move back when its reading grows too old. A claim also can&apos;t be tested while its rival&apos;s test has no reading, because a win needs the rival&apos;s reading too. Holding means a reading met a line tonight, not that the claim has been proved.</p>}
    >
      <ol className="flex flex-col gap-2">
        <Ends>
          <span className="eyebrow">A claim</span>
          <span className={count}>{f.sides.claims}</span>
          <span className="basis-full text-[13px] leading-snug text-ink-2">Each names what would prove it wrong. A claim with a test is set against a reading and a line.</span>
        </Ends>
        <Onward word="every night" />
        <Gate ask="Is there a reading to test it tonight?" why="Not when no reading tests it, the reading is too old, or the claim is about reaching a line by a date that has not come." out="no">
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
        <Onward word="no, or the rival names no test" />
        <Ends out><ClaimState state="holding" /><span className={count}>{doc.tally.holding}</span></Ends>
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
      keys={REACHES.filter((k) => f.counts[k]).map((k) => <Key key={k} swatch={<LookSwatch look={k} />}>{REACH_WORD[k]}</Key>)}
      foot={<p>One mark is one dispute from the first figure: a pair of rival positions, or a position that argues against one drawn elsewhere. Its fill is the furthest any claim on either side has got, and it links to the position. A dark mark means at least one claim on it met or missed its line tonight, on a reading the rival is not recorded as expecting. It does not say which side is right, and a single night&apos;s reading rarely ends an argument. A hollow mark is a dispute this site cannot yet read at all: each claim on it names what would prove it wrong, but no reading this site takes tests it.</p>}
      table={<>
        <table className="data">
          <thead><tr><th scope="col">Question</th>{REACHES.map((k) => <th key={k} scope="col">{REACH_HEAD[k]}</th>)}<th scope="col">Disputes</th></tr></thead>
          <tbody>
            {f.rows.map((r) => <tr key={r.id}><th scope="row">{r.label}</th>{REACHES.map((k) => <td key={k}>{r.counts[k]}</td>)}<td>{r.n}</td></tr>)}
            <tr><th scope="row">All</th>{REACHES.map((k) => <td key={k}>{f.counts[k]}</td>)}<td>{f.n}</td></tr>
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
                    <span className="mt-1 flex self-start"><LookSwatch look={c.reach} /></span>
                    <span><a href={`#position-${c.key}`} className="text-ink decoration-grid underline-offset-2 hover:underline">{name(c.key)}</a> <span className="text-muted">· {REACH_WORD[c.reach]} · claims with a test: <span className="num">{c.tested}</span> of <span className="num">{c.claims}</span></span></span>
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
          marks: r.cells.map((c) => <LookMark key={c.key} look={c.reach} href={`#position-${c.key}`} tip={`${name(c.key)}: ${REACH_WORD[c.reach]}`} />),
          tail: <>{r.counts.no_test} of {r.n} with no test</>,
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
        <p><span className="num">{f.site_rivals}</span> of this site&apos;s own positions are the named rival of a writer&apos;s position, and most of this site&apos;s own positions name no claim yet; where that is so, only one side of the dispute can be tested. <span className="num">{f.site_readings}</span> claims are this site&apos;s reading of a writer&apos;s position, not the writer&apos;s own words; the table counts them as this site&apos;s. {DRAFTED}</p>
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
  return (
    <Figure
      id="fig-due"
      title="The claims that name a date, by the year the date falls"
      note={KIND_LABEL.chart}
      keys={<>
        {lookKeys(drawn)}
        <Key swatch={<span className="inline-block h-3 w-3 bg-axis" />}>square: the claim says it will have happened by then</Key>
        <Key swatch={<span className="inline-block h-3 w-3 rounded-full bg-axis" />}>round: the rival can live with the same reading only until then</Key>
      </>}
      foot={<p>Only claims that name a date are drawn: <span className="num">{d.dated}</span> do and <span className="num">{d.undated}</span> do not, though each of those names what would prove it wrong. A date settles nothing for a claim that no reading tests: <span className="num">{d.with_test}</span> of the dated claims have a test, and for the rest the date will pass with nothing read unless a test is written first. A year with no mark is a year no claim names. The fill is tonight&apos;s reading, as in the first figure; follow a mark to its claim.</p>}
      table={<>
        <table className="data">
          <thead><tr><th scope="col">Date</th><th scope="col">Claim</th><th scope="col">What the date is</th><th scope="col">Tonight</th></tr></thead>
          <tbody>
            {marks.map((m) => (
              <tr key={m.claim}>
                <td className="whitespace-nowrap">{m.date}{m.passed ? ", already passed" : ""}</td>
                <td className="min-w-[14rem]"><a href={`#claim-${m.claim}`} className="decoration-grid underline-offset-2 hover:underline">{f.texts[m.claim]}</a></td>
                <td>{m.kind === "due" ? "the claim says it will have happened by then" : "the rival can live with the same reading until then"}</td>
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
            {y.marks.map((m) => <LookMark key={m.claim} look={f.looks[m.claim]} round={m.kind === "rival_until"} href={`#claim-${m.claim}`} tip={`${m.date}: ${f.texts[m.claim]} (${LOOK_WORD[f.looks[m.claim]]})`} />)}
          </div>
        ))}
      </div>
      <div aria-hidden className="flex gap-1 pt-1.5">
        {d.years.map((y) => <span key={y.year} className="num min-w-0 flex-1 text-center text-[11px] text-ink-2">{y.year}</span>)}
      </div>
    </Figure>
  );
}
