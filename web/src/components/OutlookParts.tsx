import { ReasonLink } from "@/components/ReasonLink";
import Link from "next/link";
import { Fragment } from "react";
import { MarginPanel } from "@/components/ArticleLayout";
import { type Cites, Inline, type Tests } from "@/components/Essay";
import { Fact } from "@/components/Fact";
import { Figure } from "@/components/Figure";
import type { OutlookClaim, OutlookDoc, OutlookPosition, OutlookState, OutlookTest } from "@/lib/data";
import { CLAIM_WORDS, fmtLine } from "@/lib/format";

// What happens from here: named writers' positions on each question, the claims they imply, and tonight's reading of
// each claim. Every number comes from the export; a claim's state is the export's, never worked out here.
const GLYPH: Record<OutlookState, string> = { holding: "●", failing: "×", both: "◑", untestable: "○" };
const OP: Record<string, string> = { gt: "above", gte: "at least", lt: "below", lte: "at most" };

export function ClaimState({ state }: { state: OutlookState }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-[2px] border px-1.5 py-0.5 text-xs whitespace-nowrap ${state === "untestable" ? "border-dashed border-muted text-ink-2" : state === "failing" ? "border-ink text-ink" : "border-ink-2 text-ink"}`}>
      <span aria-hidden>{GLYPH[state]}</span>
      <span>{CLAIM_WORDS[state]}</span>
    </span>
  );
}

export const cites = (doc: OutlookDoc): Cites => Object.fromEntries(doc.sources.map((s) => [s.id, { n: s.n, who: s.who, work: s.work }]));

// Who holds a view, in the short form a long author list is given; each name once.
function names(doc: OutlookDoc, ids: string[]) {
  const by = Object.fromEntries(doc.sources.map((s) => [s.id, s]));
  return [...new Set(ids.map((id) => by[id]?.short ?? by[id]?.who).filter(Boolean))].join("; ");
}
const capital = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

// A claim is credited as its position is, unless it names its own makers (a bet's parties), who then take the credit,
// or is this site's own reading of an author's position.
function claimCredit(doc: OutlookDoc, p: OutlookPosition, c: OutlookClaim): string | null {
  if (c.attribution === "site" && p.attribution !== "site") return "This site's reading";
  return c.holders.join() !== p.holders.join() ? capital(names(doc, c.holders)) : null;
}

function Whose({ doc, p, c }: { doc: OutlookDoc; p: OutlookPosition; c?: OutlookClaim }) {
  const own = c ? claimCredit(doc, p, c) : null;
  if (own) return <>{own}</>;
  if (p.attribution === "site") return <>This site&apos;s own position</>;
  const who = capital(names(doc, p.holders));
  return p.attribution === "extension" ? <>An argument of {names(doc, p.holders)}, carried further by this site</> : <>{who}</>;
}

function Threshold({ doc, t }: { doc: OutlookDoc; t: OutlookTest }) {
  const [op, rhs] = Object.entries(t).find(([k]) => k in OP) ?? [];
  if (!op) return null;
  const unit = doc.facts[t.fact]?.unit;
  return <>{OP[op]} {typeof rhs === "string" ? <Fact f={doc.facts[rhs]} /> : <span className="num">{fmtLine(rhs as number, unit)}</span>}</>;
}

function ClaimLine({ doc, p, c, tests }: { doc: OutlookDoc; p: OutlookPosition; c: OutlookClaim; tests: Tests }) {
  return (
    <li id={`claim-${c.id}`} className="scroll-mt-24 target:bg-surface-2 flex flex-col gap-1 sm:flex-row sm:items-baseline sm:gap-3">
      <span className="shrink-0"><ClaimState state={c.state} /></span>
      <span className="font-serif text-[1.0625rem] leading-snug text-ink">
        <Inline text={c.text} facts={doc.facts} cites={cites(doc)} tests={tests} />
        {claimCredit(doc, p, c) ? <span className="block font-sans text-[13px] text-ink-2">{c.attribution === "site" && p.attribution !== "site" ? "This site's reading, not the author's" : `Claimed by ${names(doc, c.holders)}`}</span> : null}
      </span>
    </li>
  );
}

function ClaimTest({ doc, c }: { doc: OutlookDoc; c: OutlookClaim }) {
  const f = c.test ? doc.facts[c.test.fact] : null;
  return (
    <p className="text-[13.5px] leading-relaxed text-ink-2">
      {c.test ? <>Tonight {f ? <Fact f={f} /> : "no reading"}{f?.stale ? ", too old to test" : ""}; the test is <Threshold doc={doc} t={c.test} />{c.due ? <> by <span className="whitespace-nowrap">{c.due}</span></> : null}. </> : <>No reading tests this yet. </>}
      {c.state === "both" ? <>Its rival can live with the same reading{c.rival_until ? <> until <span className="whitespace-nowrap">{c.rival_until}</span></> : null}, so tonight settles nothing. </> : null}
      {c.falsifier ? <>Proved wrong by: {c.falsifier}</> : null}
    </p>
  );
}

function Position({ doc, p, tests }: { doc: OutlookDoc; p: OutlookPosition; tests: Tests }) {
  const rival = doc.positions.find((x) => x.id === p.rival);
  const own = doc.claims.filter((c) => c.position === p.id);
  return (
    <article id={`position-${p.id}`} className="panel px-5 py-4 scroll-mt-24 flex flex-col gap-2.5">
      <div className="flex flex-col gap-0.5">
        <h3 className="display text-[1.25rem] leading-tight">{p.title}</h3>
        <p className="text-[13px] text-ink-2"><Whose doc={doc} p={p} /></p>
      </div>
      <p className="font-serif text-[1.0625rem] leading-relaxed text-ink"><Inline text={p.mechanism} facts={doc.facts} cites={cites(doc)} tests={tests} /></p>
      {own.length ? <ul className="flex flex-col gap-2">{own.map((c) => <ClaimLine key={c.id} doc={doc} p={p} c={c} tests={tests} />)}</ul> : null}
      <ReasonLink q={`Reason through "${p.title}": who holds it, what tonight's readings say, and what would settle it against its rival.`} from={`/outlook#position-${p.id}`} className="self-start" />
      <details className="group">
        <summary className="cursor-pointer text-[13px] text-ink-2 hover:text-ink underline decoration-grid underline-offset-4">The case, the tests and what would refute it</summary>
        <dl className="mt-3 grid gap-x-4 gap-y-1.5 text-[14px] leading-relaxed sm:grid-cols-[9.5rem_minmax(0,1fr)]">
          <dt className="text-ink-2">Strongest case</dt>
          <dd className="text-ink"><Inline text={p.case} facts={doc.facts} cites={cites(doc)} tests={tests} /></dd>
          <dt className="text-ink-2">What would refute it</dt>
          <dd className="text-ink">{p.kill_shot}</dd>
          {rival ? <><dt className="text-ink-2">Its rival</dt><dd><a href={`#position-${rival.id}`} className="underline decoration-axis underline-offset-2 hover:decoration-ink">{rival.title}</a></dd></> : null}
        </dl>
        {own.length ? (
          <div className="mt-3 flex flex-col gap-3 border-t border-grid pt-3">
            {own.map((c) => (
              <div key={c.id} className="flex flex-col gap-0.5">
                {own.length > 1 ? <p className="text-[13.5px] leading-snug text-ink"><Inline text={c.text} facts={doc.facts} tests={tests} /></p> : null}
                <ClaimTest doc={doc} c={c} />
              </div>
            ))}
          </div>
        ) : null}
      </details>
    </article>
  );
}

// After each folio of the essay: its three main positions, then the rest folded away, each with its claims.
export function FolioPositions({ doc, folio }: { doc: OutlookDoc; folio: string }) {
  const here = doc.positions.filter((p) => p.folio === folio);
  const shown = here.filter((p) => p.visible);
  const more = here.filter((p) => !p.visible);
  return (
    <div className="mt-8 flex flex-col gap-4">
      <h3 className="eyebrow">The positions, and tonight&apos;s reading of each claim</h3>
      <div className="flex flex-col gap-4">{shown.map((p) => <Position key={p.id} doc={doc} p={p} tests={doc.tests} />)}</div>
      {more.length ? (
        <details className="group">
          <summary className="cursor-pointer text-[15px] text-ink underline decoration-axis underline-offset-4">More positions on this question</summary>
          <div className="mt-4 flex flex-col gap-4">{more.map((p) => <Position key={p.id} doc={doc} p={p} tests={doc.tests} />)}</div>
        </details>
      ) : null}
    </div>
  );
}

export function Agreements({ doc }: { doc: OutlookDoc }) {
  return (
    <ul className="mt-6 flex flex-col">
      {doc.agree.map((a) => (
        <li key={a.id} className="py-4 border-t border-grid flex flex-col gap-1.5">
          <p className="font-serif text-[1.125rem] leading-snug text-ink">{a.text}</p>
          <p className="text-[13px] leading-relaxed text-ink-2">Held by {names(doc, a.holders)}.</p>
          {a.dissent.length ? <p className="text-[13px] leading-relaxed text-ink-2">Dissent: {a.dissent_text ?? names(doc, a.dissent)}</p> : <p className="text-[13px] leading-relaxed text-muted">No source here dissents.</p>}
        </li>
      ))}
    </ul>
  );
}

// Progress crossed with the rules. A cell is filled only where a named writer argues it, and every cell tonight's
// readings still allow is marked, never just one.
export function ScenarioGrid({ doc, rows }: { doc: OutlookDoc; rows: Record<string, string> }) {
  const s = doc.scenarios;
  const cell = (p: string, r: string) => s.cells.find((c) => c.progress === p && c.rules === r);
  const claim = (id: string) => doc.claims.find((c) => c.id === id);
  const Body = ({ p, r }: { p: string; r: string }) => {
    const c = cell(p, r);
    if (!c) return <span className="text-[13px] text-muted">No source here argues this.</span>;
    return (
      <div className="flex flex-col gap-2">
        <span className={`self-start rounded-[2px] border px-1.5 py-0.5 text-[11px] font-mono uppercase tracking-[0.07em] ${!c.consistent ? "border-dashed border-muted text-muted" : c.tested ? "border-ink text-ink" : "border-muted text-ink-2"}`}>{!c.consistent ? "ruled out tonight" : c.tested ? "still open" : "open, not yet tested"}</span>
        <p className="font-serif text-[15px] leading-snug text-ink">{c.says}</p>
        <p className="text-[12.5px] leading-relaxed text-ink-2">Argued by {names(doc, c.argued_by)}.</p>
        {c.signposts.length ? (
          <ul className="flex flex-col gap-1 text-[12.5px] leading-snug">
            {c.signposts.map((g) => <li key={g.claim} className="flex items-baseline gap-2"><span aria-hidden>{GLYPH[g.state]}</span><a href={`#claim-${g.claim}`} className="text-ink-2 underline decoration-grid underline-offset-2 hover:text-ink">{claim(g.claim) ? <Inline text={claim(g.claim)!.text} facts={doc.facts} tests={doc.tests} /> : g.claim}</a><span className="sr-only">: {CLAIM_WORDS[g.state]}</span></li>)}
          </ul>
        ) : <p className="text-[12.5px] text-muted">No signpost yet.</p>}
        {c.binds_next.length ? <p className="text-[12.5px] leading-snug text-ink-2">Binds next: {c.binds_next.map((id, k) => <span key={id}>{k ? "; " : ""}<Link href={`/bottlenecks#why-${id}`} prefetch={false} className="underline decoration-grid underline-offset-2 hover:text-ink">{rows[id] ?? id}</Link></span>)}.</p> : null}
      </div>
    );
  };
  return (
    <Figure id="scenarios" title="Which futures tonight's readings still allow" note="how far capability goes, down · how the rules settle, across · a cell is filled only where a named writer argues it"
      foot={<p>The long view: every dated forecast of each milestone, from the 1960s to this year, sits on <Link href="/singularity" className="underline decoration-axis underline-offset-2 hover:decoration-ink">one timeline</Link>, where four worlds for 2036 map onto these cells.</p>}>
      <div className="hidden md:block overflow-x-auto">
        <table className="data w-full">
          <thead><tr><th scope="col">Progress</th>{s.rules.map((r) => <th key={r.id} scope="col">{r.label}</th>)}</tr></thead>
          <tbody>
            {s.progress.map((p) => (
              <tr key={p.id}>
                <th scope="row" className="align-top whitespace-nowrap">{p.label}</th>
                {s.rules.map((r) => <td key={r.id} className="align-top min-w-[12rem]"><Body p={p.id} r={r.id} /></td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ul className="md:hidden flex flex-col">
        {s.cells.map((c) => (
          <li key={`${c.progress}-${c.rules}`} className="py-4 border-t border-grid flex flex-col gap-2">
            <span className="eyebrow">{s.progress.find((p) => p.id === c.progress)?.label} · {s.rules.find((r) => r.id === c.rules)?.label}</span>
            <Body p={c.progress} r={c.rules} />
          </li>
        ))}
      </ul>
      <div className="mt-5 flex flex-col gap-1.5">
        <h3 className="eyebrow">Where the rules stand</h3>
        <ul className="flex flex-col gap-1 text-[13px] leading-relaxed text-ink-2">
          {s.anchors.map((a) => <li key={a.source}><span className="num text-ink">{a.date}</span> · {a.text} <a href={`#source-${a.source}`} className="underline decoration-grid underline-offset-2 hover:text-ink">source</a></li>)}
        </ul>
      </div>
    </Figure>
  );
}

// Every claim on the page in one list, with tonight's state and what would prove it wrong.
export function FalsifierBoard({ doc }: { doc: OutlookDoc }) {
  const pos = Object.fromEntries(doc.positions.map((p) => [p.id, p]));
  const text = (c: OutlookClaim) => <a href={`#claim-${c.id}`} className="hover:underline underline-offset-2 decoration-axis"><Inline text={c.text} facts={doc.facts} tests={doc.tests} /></a>;
  return (
    <Figure title="Every claim, with tonight's state, its test and what would prove it wrong" note="by question · each claim links to its position">
      <div className="hidden md:block overflow-x-auto">
        <table className="data w-full">
          <thead><tr><th scope="col">Claim</th><th scope="col">Whose</th><th scope="col">Tonight</th></tr></thead>
          <tbody>
            {doc.folios.map((fo) => (
              <Fragment key={fo.id}>
                <tr><th scope="colgroup" colSpan={3} className="pt-5 text-left">{fo.kicker}</th></tr>
                {doc.claims.filter((c) => c.folio === fo.id).map((c) => (
                  <tr key={c.id}>
                    <td className="min-w-[16rem]">{text(c)}<div className="mt-1"><ClaimTest doc={doc} c={c} /></div></td>
                    <td className="min-w-[9rem] text-ink-2">{pos[c.position] ? <Whose doc={doc} p={pos[c.position]} c={c} /> : null}</td>
                    <td className="whitespace-nowrap"><ClaimState state={c.state} /></td>
                  </tr>
                ))}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
      <div className="md:hidden flex flex-col">
        {doc.folios.map((fo) => (
          <section key={fo.id} className="flex flex-col">
            <h3 className="eyebrow pt-5 pb-2">{fo.kicker}</h3>
            <ul className="flex flex-col">
              {doc.claims.filter((c) => c.folio === fo.id).map((c) => (
                <li key={c.id} className="py-3 border-t border-grid flex flex-col gap-1.5">
                  <span className="self-start"><ClaimState state={c.state} /></span>
                  <span className="text-[15px] leading-snug">{text(c)}</span>
                  <span className="text-[13px] text-ink-2">{pos[c.position] ? <Whose doc={doc} p={pos[c.position]} c={c} /> : null}</span>
                  <ClaimTest doc={doc} c={c} />
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </Figure>
  );
}

export function OutlookSources({ doc }: { doc: OutlookDoc }) {
  return (
    <ol className="flex flex-col font-serif text-[1.0625rem] leading-relaxed">
      {doc.sources.map((s) => (
        <li key={s.id} id={`source-${s.id}`} className="scroll-mt-24 target:bg-surface-2 border-t border-grid first:border-0 py-2">
          <details>
            <summary className="cursor-pointer grid grid-cols-[2rem_minmax(0,1fr)] gap-x-2 marker:content-none list-none">
              <span className="num text-ink-2 text-[0.9em] pt-0.5">{s.n}</span>
              <span>{s.who}, <span className="italic">{s.work}</span>, {s.year}</span>
            </summary>
            <p className="mt-1.5 ml-[2.5rem] text-[15px] leading-relaxed text-ink-2">{s.field[0].toUpperCase() + s.field.slice(1)}. {s.finding}{s.venue ? <> In {s.venue}.</> : null} <a href={s.url} className="underline decoration-axis underline-offset-2 hover:decoration-ink">Read it</a>.</p>
          </details>
        </li>
      ))}
    </ol>
  );
}

export function OutlookMargin({ doc }: { doc: OutlookDoc }) {
  return (
    <>
      <MarginPanel
        title={`Reading · ${doc.as_of}`}
        rows={[
          ["Claims holding", String(doc.tally.holding)],
          ["Failing their test", String(doc.tally.failing)],
          ["A reading both sides expect", String(doc.tally.both)],
          ["Can't be tested yet", String(doc.tally.untestable)],
        ]}
      />
      <MarginPanel title="Instrument">
        <p>Each claim is tested every night against one reading and one line. When the rival position expects the same reading, the claim says so instead of counting it as a win.</p>
        <p><Link href="/methodology#outlook" className="text-ink underline decoration-axis underline-offset-2">How the claims are tested →</Link></p>
        <p>The <Link href="/predictions" className="text-ink underline decoration-axis underline-offset-2">predictions ledger</Link> is a different thing: it scores dated forecasts people made in their own words.</p>
        <p>Where the claims say something will bind, <Link href="/bottlenecks" className="text-ink underline decoration-axis underline-offset-2">the bottleneck map</Link> marks the cell.</p>
      </MarginPanel>
    </>
  );
}
