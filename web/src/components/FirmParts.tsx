import Link from "next/link";
import { MarginPanel } from "@/components/ArticleLayout";
import { Fact } from "@/components/Fact";
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

export function RegimesPlate({ regimes }: { regimes: FirmDoc["regimes"] }) {
  return (
    <figure className="not-prose">
      <figcaption className="eyebrow mb-3">{regimes.title}</figcaption>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[40rem] border-collapse text-left text-[14px] leading-snug">
          <thead>
            <tr>{regimes.columns.map((c) => <th key={c} scope="col" className="border-b border-ink py-2 pr-4 align-bottom font-medium text-ink-2">{c}</th>)}</tr>
          </thead>
          <tbody>
            {regimes.rows.map((row) => (
              <tr key={row[0]} className="border-b border-grid align-top">
                {row.map((cell, i) => (i === 0 ? <th key={i} scope="row" className="py-2.5 pr-4 font-medium text-ink">{cell}</th> : <td key={i} className="py-2.5 pr-4 text-ink-2">{cell}</td>))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-[13px] leading-relaxed text-ink-2">{regimes.note}</p>
    </figure>
  );
}

const th = "border-b border-ink py-2 pr-4 align-bottom font-medium text-ink-2";
const td = "py-2.5 pr-4 text-ink-2";

// The shapes writers have argued for, each credited by its number in the page's sources, then what novelists pictured.
export function ShapesPlate({ doc }: { doc: FirmDoc }) {
  const n = Object.fromEntries(doc.sources.map((x) => [x.id, x.n]));
  const { shapes, fiction } = doc;
  return (
    <figure className="not-prose">
      <figcaption className="eyebrow mb-3">{shapes.title}</figcaption>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[44rem] border-collapse text-left text-[14px] leading-snug">
          <thead>
            <tr>{["The shape", "Who argues it", "What goes first", "What stays", "What would show it"].map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr>
          </thead>
          <tbody>
            {shapes.rows.map((r) => (
              <tr key={r.shape} className="border-b border-grid align-top">
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
      <p className="mt-3 text-[13px] leading-relaxed text-ink-2">{shapes.note}</p>
      <div className="mt-6 border-l-2 border-grid pl-4">
        <div className="eyebrow mb-2">{fiction.label}</div>
        <ul className="flex flex-col gap-2 text-[14px] leading-snug text-ink-2">
          {fiction.works.map((w) => <li key={w.title}><span className="text-ink">{w.author}, <i>{w.title}</i> ({w.year}).</span> {w.picture}</li>)}
        </ul>
        <p className="mt-3 text-[13px] leading-relaxed text-ink-2">{fiction.note}</p>
      </div>
    </figure>
  );
}

// The census by kind of job, best paid first. Every share is the bundle's, summed by the export.
export function CensusCutPlate({ cut }: { cut: FirmDoc["census_cut"] }) {
  if (!cut.groups?.length) return null;
  return (
    <figure className="not-prose">
      <figcaption className="eyebrow mb-3">What the census screen says of each kind of job, best paid first</figcaption>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[40rem] border-collapse text-left text-[14px] leading-snug">
          <thead>
            <tr>{["Kind of job", "Passes the screen", "Waits only on a check", "Needs a body", "Held for other reasons"].map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr>
          </thead>
          <tbody>
            {cut.groups.map((g) => (
              <tr key={g.code} className="border-b border-grid align-top" title={g.ref}>
                <th scope="row" className="py-2.5 pr-4 font-medium text-ink">{g.name}</th>
                {[g.share_passes, g.share_waits_on_check, g.share_physical, g.share_rest].map((v, i) => <td key={i} className={`${td} tabular-nums`}>{fmt(v, "share")}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-[13px] leading-relaxed text-ink-2">
        Shares of each group&apos;s payroll, from <Link href="/census" className="text-ink underline decoration-axis underline-offset-2">the census</Link> ({cut.version}), a screen scored by three AI models and not a record of what has been automated. Groups are the occupation code&apos;s major groups, ordered by average pay; the census has no field for seniority, so this reads kinds of job, not rungs within one. &ldquo;Held for other reasons&rdquo; is work that is slow to judge, costly when wrong, or a sign-off a person answers for.
      </p>
    </figure>
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
