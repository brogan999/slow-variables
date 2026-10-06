import Link from "next/link";
import { MarginPanel } from "@/components/ArticleLayout";
import { Fact } from "@/components/Fact";
import { Figure, Key } from "@/components/Figure";
import { KIND_LABEL, Pyramid, ShareBars, Swatch } from "@/components/diagrams/kit";
import { Position } from "@/components/OutlookParts";
import type { FirmDoc } from "@/lib/data";
import { fmt } from "@/lib/format";

// Who owns what: the essay's own parts. Positions, claims and their states are the outlook's records, drawn by the
// outlook's components; nothing here works out a state or a number.

// After a folio: the positions seated under it in seed/firm.yaml, each with its claims and tonight's reading.
export function SeatedPositions({ doc, folio }: { doc: FirmDoc; folio: string }) {
  const here = (doc.folios[folio] ?? []).flatMap((id) => doc.positions.filter((p) => p.id === id));
  if (!here.length) return null;
  return (
    <details className="group mt-8">
      <summary className="cursor-pointer text-[15px] text-ink underline decoration-axis underline-offset-4">The positions on this question, and tonight&apos;s reading of each claim</summary>
      <div className="mt-4 flex flex-col gap-4">{here.map((p) => <Position key={p.id} doc={doc} p={p} tests={doc.tests} page="/firm" />)}</div>
    </details>
  );
}

const th = "border-b border-ink py-2 pr-4 align-bottom font-medium text-ink-2";
const td = "py-2.5 pr-4 text-ink-2";
const censusLink = <Link href="/census" className="text-ink underline decoration-axis underline-offset-2">the census</Link>;
const PLACE = { rent: "0%", both: "50%", own: "100%" } as const;

// Rent or own, drawn: each case sits on a line from renting to owning, with the table folded beneath.
export function RegimesPlate({ regimes }: { regimes: FirmDoc["regimes"] }) {
  return (
    <Figure
      title={regimes.title}
      note={KIND_LABEL.model}
      foot={<><p>{regimes.note}</p><p>{regimes.places_note}</p></>}
      table={
        <table className="w-full min-w-[40rem] border-collapse text-left text-[13px] leading-snug">
          <thead><tr>{regimes.columns.map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr></thead>
          <tbody>{regimes.rows.map((row) => <tr key={row[0]} className="border-b border-grid align-top">{row.map((cell, i) => (i === 0 ? <th key={i} scope="row" className="py-2.5 pr-4 font-medium text-ink">{cell}</th> : <td key={i} className={td}>{cell}</td>))}</tr>)}</tbody>
        </table>
      }
      tableLabel="The cases as a table, with examples"
    >
      <div className="flex flex-col gap-4">
        <div className="hidden grid-cols-[minmax(0,1fr)_minmax(0,14rem)_minmax(0,1fr)] gap-x-4 font-mono text-[11px] uppercase tracking-wider text-muted md:grid">
          <span>What is scarce in the firm&apos;s work</span><span className="flex justify-between"><span>Rent</span><span>Own</span></span><span>Who wins</span>
        </div>
        {regimes.rows.map((row, i) => (
          <div key={row[0]} className="grid grid-cols-1 gap-x-4 gap-y-1.5 border-t border-grid pt-3 md:grid-cols-[minmax(0,1fr)_minmax(0,14rem)_minmax(0,1fr)] md:items-center">
            <div className="text-[13.5px] font-medium leading-snug text-ink">{row[0]}</div>
            <div title={row[2]} className="relative mx-1.5 h-5">
              <span aria-hidden className="absolute inset-x-0 top-1/2 h-px bg-axis" />
              <span role="img" aria-label={row[2]} className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ink" style={{ left: PLACE[regimes.places[i]] }} />
            </div>
            <div className="text-[13px] leading-snug text-ink-2"><span className="md:hidden">{row[2]}. </span>{row[3]}</div>
          </div>
        ))}
      </div>
    </Figure>
  );
}

// The shapes writers have argued for, each sketched as three layers of people and credited by its number in the
// page's sources, then what novelists pictured.
export function ShapesPlate({ doc }: { doc: FirmDoc }) {
  const n = Object.fromEntries(doc.sources.map((x) => [x.id, x.n]));
  const { shapes, fiction } = doc;
  return (
    <Figure
      title={shapes.title}
      note={KIND_LABEL.model}
      keys={<><Key swatch={<Swatch fill="var(--s2)" hatched />}>a layer of people, drawn against a pyramid today</Key><Key swatch={<span className="inline-block h-2.5 w-4 border border-dashed border-axis" />}>a layer the hypothesis removes</Key></>}
      foot={<p>{shapes.note} Each sketch draws the top, the middle and the base wider or thinner by a word this site chose for the hypothesis; it is a drawing of an argument.</p>}
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-[48rem] border-collapse text-left text-[13.5px] leading-snug">
          <thead>
            <tr>{["", "The shape", "Who argues it", "What goes first", "What stays", "What would show it"].map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr>
          </thead>
          <tbody>
            {shapes.rows.map((r) => (
              <tr key={r.shape} className="border-b border-grid align-top">
                <td className="w-20 py-2.5 pr-3">{r.glyph ? <Pyramid compact label={`${r.shape}: ${r.glyph.map((t) => `${t.id} ${t.word.replace("_", " ")}`).join(", ")}`} tiers={r.glyph.map((t) => ({ key: t.id, label: t.id, w: t.w, hatched: true, fill: "var(--s2)", tip: `The ${t.id}: ${t.word.replace("_", " ")}` }))} /> : null}</td>
                <th scope="row" className="py-2.5 pr-4 font-medium text-ink">{r.shape}</th>
                <td className={td}>{r.who}{r.sources.map((id) => <sup key={id} className="ml-0.5"><a href={`#source-${id}`} className="text-ink-2 no-underline">{n[id]}</a></sup>)}</td>
                <td className={td}>{r.goes_first}</td>
                <td className={td}>{r.stays}</td>
                <td className={td}>{r.would_show}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-6 border-l-2 border-grid pl-4">
        <div className="eyebrow mb-2">{fiction.label}</div>
        <ul className="flex flex-col gap-2 text-[14px] leading-snug text-ink-2">
          {fiction.works.map((w) => <li key={w.title}><span className="text-ink">{w.author}, <i>{w.title}</i> ({w.year}).</span> {w.picture}</li>)}
        </ul>
        <p className="mt-3 text-[13px] leading-relaxed text-ink-2">{fiction.note}</p>
      </div>
    </Figure>
  );
}

const CUT = { passes: ["var(--s1)", "passes the screen"], waits_on_check: ["var(--tight-2)", "waits only on a check"], physical: ["var(--s2)", "needs a body"], rest: ["var(--s3)", "held for more than a missing check"] } as const;

// The census by kind of job, best paid first, as stacked bars; the table is folded beneath. Every share is the
// bundle's, summed and laid out by the export.
export function CensusCutPlate({ cut }: { cut: FirmDoc["census_cut"] }) {
  if (!cut.groups?.length) return null;
  const share = (g: FirmDoc["census_cut"]["groups"][number], p: keyof typeof CUT) => ({ passes: g.share_passes, waits_on_check: g.share_waits_on_check, physical: g.share_physical, rest: g.share_rest })[p];
  return (
    <Figure
      title="What the census screen says of each kind of job, best paid first"
      note={KIND_LABEL.chart}
      keys={<>{(Object.keys(CUT) as (keyof typeof CUT)[]).map((p) => <Key key={p} swatch={<Swatch fill={CUT[p][0]} />}>{CUT[p][1]}</Key>)}<Key swatch={<span className="inline-block h-3 w-0.5 bg-surface outline outline-1 outline-ink" />}>to its left, all three models pass</Key></>}
      foot={<p>Shares of each group&apos;s payroll, from {censusLink} ({cut.version}), a screen scored by three AI models and not a record of what has been automated. Groups are the occupation code&apos;s major groups, ordered by average pay; the census has no field for seniority, so this reads kinds of job, not rungs within one. A task passes when at least two of the three models pass it. The last part is everything else: mostly work that has no existing check and is also slow to judge or costly when wrong, work on which the scorers split over what holds it, and a small part that is a sign-off a person answers for.</p>}
      table={
        <table className="w-full min-w-[40rem] border-collapse text-left text-[13px] leading-snug">
          <thead><tr>{["Kind of job", "Passes the screen", "All three models pass", "Waits only on a check", "Needs a body", "Held for more than a missing check"].map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr></thead>
          <tbody>{cut.groups.map((g) => (
            <tr key={g.code} className="border-b border-grid align-top" title={g.ref}>
              <th scope="row" className="py-2 pr-4 font-medium text-ink">{g.name}</th>
              {[g.share_passes, g.share_agreed3, g.share_waits_on_check, g.share_physical, g.share_rest].map((v, i) => <td key={i} className={`${td} tabular-nums`}>{fmt(v, "share")}</td>)}
            </tr>
          ))}</tbody>
        </table>
      }
    >
      <ShareBars
        label="Each kind of job's payroll, split by what the census screen says of it"
        rows={cut.groups.map((g) => ({
          name: g.name,
          segs: g.bar.map((s) => ({ key: s.part, x: s.x, w: s.w, fill: CUT[s.part][0], tip: `${g.name}: ${fmt(share(g, s.part), "share")} ${CUT[s.part][1]}` })),
          tick: { x: g.agreed3_x, tip: `${g.name}: all three models pass ${fmt(g.share_agreed3, "share")}` },
        }))}
      />
    </Figure>
  );
}

export function FirmMargin({ doc }: { doc: FirmDoc }) {
  return (
    <>
      <MarginPanel
        title={`Reading · ${doc.as_of}`}
        rows={[
          ["Claims holding", String(doc.tally.holding)],
          ["Failing their test", String(doc.tally.failing)],
          ["A reading both sides expect", String(doc.tally.both)],
          ["Can't be tested yet", String(doc.tally.untestable)],
          ["Service firms bought by AI roll-ups, past year", <><Fact f={doc.facts.rollup_service_deals} /> against <Fact f={doc.facts.rollup_service_deals_year_ago} /> the year before</>],
          ["Software products they bought, counted apart", <Fact key="s" f={doc.facts.rollup_software_deals} />],
          ["Firms using AI", <Fact key="f" f={doc.facts.firms_using_ai} />],
        ]}
      />
      <MarginPanel title="Instrument">
        <p>Most of this page is argument. Its readings are few, most of its claims cannot be tested yet, and the last folio says what the readings do and do not show.</p>
        <p>The picture of the firm in the limit is this site&apos;s judgement; no reading tests it whole.</p>
        <p>The claims are tested as <Link href="/methodology#outlook" className="text-ink underline decoration-axis underline-offset-2">the outlook&apos;s are</Link>, and all of them are on <Link href="/predictions" className="text-ink underline decoration-axis underline-offset-2">the forecasts board</Link>, where a model&apos;s lean on some of them disagrees with this essay.</p>
        <p><Link href="/census#deals" className="text-ink underline decoration-axis underline-offset-2">Where the roll-ups are buying, and the census&apos;s figures</Link> · <Link href="/ledger" className="text-ink underline decoration-axis underline-offset-2">who finances whom</Link> · <Link href="/layers/model" className="text-ink underline decoration-axis underline-offset-2">what the labs buy</Link></p>
      </MarginPanel>
      <MarginPanel title="Who wrote this">
        <p>Drafted by a Claude model, made by Anthropic, which is one of the labs this page discusses and whose model is one of the census&apos;s three scorers. Reviewed by Alex Brogan.</p>
      </MarginPanel>
    </>
  );
}
