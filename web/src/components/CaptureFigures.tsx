import Link from "next/link";
import { Figure, Key } from "@/components/Figure";
import { StatusChip } from "@/components/StatusChip";
import { Bar, Flow, GaugeDot, Track, TrackDot } from "@/components/diagrams/capture";
import { KIND_LABEL, Swatch } from "@/components/diagrams/kit";
import type { CaptureFigures } from "@/lib/data";
import { fmt, words } from "@/lib/format";

// The figures on /capture. Every number, width and position is the export's (src/ai_tracker/capture_figures.py);
// nothing here works one out. A chart draws records; the model draws the page's rule and says so.

const a = "underline decoration-axis underline-offset-2 hover:decoration-ink";
const th = "border-b border-ink py-2 pr-4 align-bottom font-medium text-ink-2";
const td = "py-2 pr-4 text-ink-2";
const tbl = "w-full min-w-[34rem] border-collapse text-left text-[13px] leading-snug";

// Every capture gauge as one square, layer by layer from the chips up, under the word it reads tonight.
export function GaugesPlate({ gauges }: { gauges: CaptureFigures["gauges"] }) {
  const label = Object.fromEntries(gauges.words.map((w) => [w.id, w.label]));
  return (
    <Figure
      id="gauges"
      title="Every gauge of who keeps the profit, layer by layer, and what each reads tonight"
      note={`${KIND_LABEL.chart} · each square is a gauge and links to its page`}
      keys={<>{gauges.words.map((w) => <Key key={w.id} swatch={<GaugeDot word={w.id} />}>{w.label.toLowerCase()}{w.id === "concentrating" ? " (concentrating)" : w.id === "dispersing" ? " (dispersing)" : ""}</Key>)}</>}
      foot={<>
        <p>Each square is a published gauge that this site scores for direction: whether profit, sales or financing in that layer are gathering with fewer firms (concentrating) or spreading out to more firms or to buyers (dispersing). A gauge reads too early or unclear until it has enough readings to show a direction. The word beside each layer is a vote of its gauges, counting gauges that share a source once, so it is not a tally of the squares.</p>
        <p>It does not show how far a gauge has moved, only its direction, and a layer with few squares is thinly measured, not quiet. Gauges of how fast AI is spreading sit on <Link href="/diffusion" className={a}>the other lens</Link>.</p>
      </>}
      table={
        <table className={tbl}>
          <thead><tr>{["Layer", "Gauge", "Reads tonight"].map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr></thead>
          <tbody>{gauges.layers.flatMap((l) => l.groups.flatMap((g) => g.marks.map((m) => (
            <tr key={m.id} className="border-b border-grid align-top">
              <td className={td}>{l.name}</td>
              <th scope="row" className="py-2 pr-4 font-normal text-ink"><Link href={m.href} prefetch={false} className={a}>{m.name}</Link></th>
              <td className={td}>{words(m.status)}</td>
            </tr>
          ))))}</tbody>
        </table>
      }
      tableLabel="Every gauge and its reading"
    >
      <div className="flex flex-col">
        <div aria-hidden className="hidden grid-cols-[13rem_repeat(4,minmax(0,1fr))] gap-x-4 pb-2 font-mono text-[11px] uppercase tracking-wider text-muted md:grid">
          <span>Layer, from the chips up</span>{gauges.words.map((w) => <span key={w.id}>{w.label}</span>)}
        </div>
        {gauges.layers.map((l) => (
          <div key={l.id} className="grid grid-cols-1 gap-x-4 gap-y-2 border-t border-grid py-3 md:grid-cols-[13rem_repeat(4,minmax(0,1fr))] md:items-center">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 md:flex-col md:items-start">
              <Link href={l.href} className={`text-[14px] font-medium text-ink ${a}`}>{l.name}</Link>
              <StatusChip status={l.status} />
            </div>
            {l.n ? l.groups.map((g) => (
              <div key={g.word} className={`flex flex-wrap items-center gap-1.5 ${g.n ? "" : "max-md:hidden"}`}>
                {g.n ? <span className="w-full font-mono text-[10.5px] uppercase tracking-wider text-muted md:hidden">{label[g.word]}</span> : null}
                {g.marks.map((m) => <GaugeDot key={m.id} word={g.word} href={m.href} tip={`${m.name}: ${words(m.status)}`} />)}
              </div>
            )) : <p className="text-[13px] text-muted md:col-span-4">No gauge here is scored for direction yet.</p>}
          </div>
        ))}
      </div>
    </Figure>
  );
}

const TONE: Record<string, string> = { away: "border-slow", while: "border-muted", stays: "border-fast" };

// The page's rule as a drawing: two questions about anything a buyer needs, and where the profit goes on each answer.
export function RulePlate({ rule }: { rule: CaptureFigures["rule"] }) {
  const last = rule.outcomes.find((o) => o.answer === "Yes");
  return (
    <Figure
      id="rule"
      title={rule.title}
      note={KIND_LABEL.model}
      keys={<>
        <Key swatch={<span className="inline-block h-2.5 w-4 border-[1.5px] border-ink" />}>a question</Key>
        <Key swatch={<span className="inline-block h-2.5 w-4 border-l-[3px] border-fast bg-surface-2" />}>profit gathers with the holder</Key>
        <Key swatch={<span className="inline-block h-2.5 w-4 border-l-[3px] border-muted bg-surface-2" />}>profit that does not last</Key>
        <Key swatch={<span className="inline-block h-2.5 w-4 border-l-[3px] border-slow bg-surface-2" />}>profit passed on to buyers</Key>
      </>}
      foot={<p>{rule.foot} This is a drawing of an idea from economics, with no number of its own; the charts on this page are where it is tested.</p>}
    >
      <div className="flex flex-col gap-4">
        <p className="text-[14px] text-ink-2"><span className="eyebrow mr-2">Start</span>{rule.start}</p>
        <ol className="grid gap-4 md:grid-cols-3">
          {rule.questions.map((q, i) => (
            <li key={q.id} className="flex flex-col gap-2">
              {i ? <span className="eyebrow">If yes</span> : <span aria-hidden className="eyebrow max-md:hidden">&nbsp;</span>}
              <div className="flex grow flex-col gap-1.5 border-[1.5px] border-ink p-3">
                <h3 className="font-sans text-[16px] font-bold leading-tight">{q.ask}</h3>
                <p className="text-[13px] leading-snug text-ink-2">{q.explain}</p>
              </div>
              {rule.outcomes.filter((o) => o.after === q.id && o.answer === "No").map((o) => (
                <div key={o.id} className="flex flex-col gap-2">
                  <span className="eyebrow">If no</span>
                  <div className={`flex flex-col gap-1 border-l-[3px] bg-surface-2 p-3 ${TONE[o.id] ?? "border-muted"}`}>
                    <span className="text-[14px] font-semibold text-ink">{o.word}</span>
                    <p className="text-[13px] leading-snug text-ink-2">{o.text}</p>
                  </div>
                </div>
              ))}
            </li>
          ))}
          {last ? (
            <li className="flex flex-col gap-2">
              <span className="eyebrow">If yes to both</span>
              <div className={`flex flex-col gap-1 border-l-[3px] bg-surface-2 p-3 ${TONE[last.id]}`}>
                <span className="text-[14px] font-semibold text-ink">{last.word}</span>
                <p className="text-[13px] leading-snug text-ink-2">{last.text}</p>
              </div>
              <div className="mt-1 flex flex-col gap-1.5">
                <span className="eyebrow">{rule.defences_label}</span>
                <ul className="flex flex-col gap-1 text-[13px] leading-snug text-ink-2">{rule.defences.map((d) => <li key={d} className="border-l border-grid pl-2">{d}</li>)}</ul>
              </div>
            </li>
          ) : null}
        </ol>
      </div>
    </Figure>
  );
}

// The profit split in the newest quarter against the same quarter a year before, for each part of each measure.
export function YearPlate({ year }: { year: CaptureFigures["year"] }) {
  const stacks = [...new Set(year.rows.map((r) => r.stack))];
  return (
    <Figure
      id="year-on-year"
      title="How each part's share of the profit moved over the last year"
      note={`${KIND_LABEL.chart} · the newest quarter against the same quarter a year before`}
      keys={<>
        <Key swatch={<span className="inline-block h-2.5 w-2.5 rounded-full border-[1.5px] border-s1 bg-surface" />}>a year before</Key>
        <Key swatch={<span className="inline-block h-2.5 w-2.5 rounded-full bg-s1" />}>the newest quarter</Key>
        <Key swatch={<span className="hatch inline-block h-2.5 w-2.5 rounded-full border-[1.5px] border-s1 text-s1" />}>the newest quarter, where the figure is an estimate</Key>
      </>}
      foot={<p>The same shares as the columns in the figures of gross profit and operating income on this page, read at their ends: where each part stood in the newest quarter on file and in the same quarter a year before. Gross profit is revenue less the cost of delivering the product; operating income also takes off research, selling and running costs. A share can rise while the money itself falls, and the reverse, because every part is measured against the total of the parts drawn. Apps, and labs in the operating measure, file nothing usable and are left out, so these are shares of what can be measured, not of the whole industry.</p>}
      table={
        <table className={tbl}>
          <thead><tr>{["Measure", "Part", "A year before", "Newest quarter", "Change"].map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr></thead>
          <tbody>{year.rows.map((r) => (
            <tr key={r.stack + r.id} className="border-b border-grid align-top">
              <td className={td}>{r.what}</td>
              <th scope="row" className="py-2 pr-4 font-normal text-ink">{r.name}{r.estimated ? " (estimated)" : ""}</th>
              <td className={`${td} tabular-nums`}>{r.then ? <>{fmt(r.then.value, "share")} <span className="text-muted">{r.then.quarter}</span></> : "no quarter on file"}</td>
              <td className={`${td} tabular-nums`}><Link href={r.now.href} prefetch={false} className={a}>{fmt(r.now.value, "share")}</Link> <span className="text-muted">{r.now.quarter}</span></td>
              <td className={`${td} tabular-nums`}>{r.change ?? "—"}</td>
            </tr>
          ))}</tbody>
        </table>
      }
    >
      <div className="flex flex-col gap-5">
        {stacks.map((s) => {
          const rows = year.rows.filter((r) => r.stack === s);
          return (
            <div key={s} className="flex flex-col gap-1.5">
              <div className="eyebrow">Share of {rows[0].what}{rows[0].then ? <span className="ml-2 normal-case tracking-normal text-muted">{rows[0].then.quarter} to {rows[0].now.quarter}</span> : null}</div>
              {rows.map((r) => (
                <div key={r.id} className="grid grid-cols-[minmax(0,1fr)_4.5rem] items-center gap-x-3 sm:grid-cols-[10rem_minmax(0,1fr)_5.5rem]">
                  <span className="text-[13px] leading-tight text-ink max-sm:col-span-2">{r.name}{r.estimated ? <span className="text-muted"> (estimated)</span> : null}</span>
                  <Track ticks={year.ticks} label={`${r.name}: ${r.then ? `${fmt(r.then.value, "share")} in ${r.then.quarter}, ` : ""}${fmt(r.now.value, "share")} in ${r.now.quarter}`}>
                    {r.then ? <span aria-hidden className="absolute top-1/2 h-[3px] -translate-y-1/2 bg-s3" style={r.rose ? { left: `${r.then.x}%`, right: `calc(100% - ${r.now.x}%)` } : { left: `${r.now.x}%`, right: `calc(100% - ${r.then.x}%)` }} /> : null}
                    {r.then ? <TrackDot x={r.then.x} hollow tip={`${r.name}, ${r.then.quarter}: ${fmt(r.then.value, "share")}`} /> : null}
                    <TrackDot x={r.now.x} hatched={r.estimated} tip={`${r.name}, ${r.now.quarter}: ${fmt(r.now.value, "share")}`} />
                  </Track>
                  <span className="num text-right text-[12.5px] text-ink">{fmt(r.now.value, "share")}<span className="block text-[11px] text-muted">{r.change ?? ""}</span></span>
                </div>
              ))}
              <div aria-hidden className="grid grid-cols-[minmax(0,1fr)_4.5rem] gap-x-3 sm:grid-cols-[10rem_minmax(0,1fr)_5.5rem]">
                <span className="max-sm:hidden" />
                <div className="relative h-4 font-mono text-[10.5px] text-muted">{year.ticks.map((t) => <span key={t.x} className="absolute -translate-x-1/2" style={{ left: `${t.x}%` }}>{t.label}</span>)}</div>
              </div>
            </div>
          );
        })}
      </div>
    </Figure>
  );
}

const LAB_BARS = [
  ["run_rate", "var(--s1)", "Sales a year, at the latest pace", "sells a year"],
  ["equity", "var(--s3)", "Raised from investors", "has raised"],
  ["promised", "var(--s2)", "Promised to suppliers", "has promised"],
] as const;

// Each lab's yearly sales pace beside the money it has raised and the spending it has promised, on one dollar scale.
export function LabsPlate({ labs }: { labs: CaptureFigures["labs"] }) {
  return (
    <Figure
      id="labs"
      title="What each AI lab sells in a year, against what it has raised and what it has promised to spend"
      note={`${KIND_LABEL.chart} · one dollar scale · estimates are hatched`}
      keys={<>
        <Key swatch={<Swatch fill="var(--s1)" hatched />}>sales a year at the latest pace (run-rate), an estimate</Key>
        <Key swatch={<Swatch fill="var(--s1)" />}>the same, where a figure was reported and not estimated</Key>
        <Key swatch={<Swatch fill="var(--s3)" />}>money raised from investors by that date</Key>
        <Key swatch={<Swatch fill="var(--s2)" />}>spending promised to suppliers, at face</Key>
      </>}
      foot={<>
        <p>What each bar rests on. A run-rate is a single month of sales multiplied up to a year, as reported by the press or the lab itself and compiled by Epoch AI, hatched where Epoch marks it as an estimate: it is not booked revenue, no auditor has checked it, and labs differ on whether they count sales before or after a partner&apos;s cut. Money raised is the sum of the funding rounds on record up to the date of the run-rate; where few rounds are on record the sum is a floor, and the multiple under the lab&apos;s name, its run-rate over the money raised, flatters it. Spending promised is the face value of the contracts and commitments on <Link href="/ledger" className={a}>the financing ledger</Link> that name the lab as buyer: it runs over many years, counts amounts described as up to a ceiling in full, includes deals reported by the press and not confirmed, and is not money paid. A lab with no such bar has no deal on the ledger, which is not the same as having promised nothing.</p>
        <p>Every lab is drawn by the same rule, in order of money raised. {labs.absent.length ? <>No run-rate is on record for {labs.absent.join(" or ")}, so they have no row; a lab inside a larger company is rarely reported apart. </> : null}This page is drafted by a Claude model, made by Anthropic, which is drawn here; the figures are other people&apos;s reports of it, not its own.</p>
      </>}
      table={
        <table className={tbl}>
          <thead><tr>{["Lab", "Run-rate", "As of", "Raised by then", "Rounds on record", "Run-rate over money raised", "Promised to suppliers", "Deals"].map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr></thead>
          <tbody>{labs.rows.map((r) => (
            <tr key={r.id} className="border-b border-grid align-top">
              <th scope="row" className="py-2 pr-4 font-medium text-ink">{r.name}</th>
              <td className={`${td} tabular-nums`}>{r.run_rate.href ? <Link href={r.run_rate.href} prefetch={false} className={a}>{fmt(r.run_rate.value, "USD")}</Link> : fmt(r.run_rate.value, "USD")}{r.run_rate.stamp === "estimate" ? " (estimate)" : ""}</td>
              <td className={`${td} tabular-nums whitespace-nowrap`}>{r.run_rate.as_of}</td>
              <td className={`${td} tabular-nums`}>{fmt(r.equity.value, "USD")}</td>
              <td className={`${td} tabular-nums`}>{fmt(r.equity.n, "count")}</td>
              <td className={`${td} tabular-nums`}><Link href={r.ratio.href} prefetch={false} className={a}>{fmt(r.ratio.value, "ratio")}</Link></td>
              <td className={`${td} tabular-nums`}>{r.promised ? fmt(r.promised.value, "USD") : "none on the ledger"}</td>
              <td className={`${td} tabular-nums`}>{r.promised ? fmt(r.promised.n, "count") : "—"}</td>
            </tr>
          ))}</tbody>
        </table>
      }
    >
      <div className="flex flex-col">
        {labs.rows.map((r) => (
          <div key={r.id} className="grid grid-cols-1 gap-x-4 gap-y-1.5 border-t border-grid py-3 first:border-t-0 first:pt-0 sm:grid-cols-[11rem_minmax(0,1fr)]">
            <div className="flex flex-wrap items-baseline gap-x-2 sm:flex-col">
              <span className="text-[14px] font-medium text-ink">{r.name}</span>
              <span className="font-mono text-[11px] text-muted whitespace-nowrap">as of {r.run_rate.as_of}</span>
              <span className="font-mono text-[11px] text-muted">sells <Link href={r.ratio.href} prefetch={false} className={a}>{fmt(r.ratio.value, "ratio")}</Link> what it has raised</span>
            </div>
            <div className="flex flex-col gap-1">
              {LAB_BARS.map(([k, fill, name, short]) => {
                const b = r[k];
                return b ? (
                  <div key={k} className="grid grid-cols-[5.75rem_minmax(0,1fr)_3.5rem] items-center gap-x-2">
                    <span className="font-mono text-[11px] text-muted">{short}</span>
                    <Bar w={b.w} fill={fill} hatched={k === "run_rate" && b.stamp === "estimate"} tip={`${r.name}: ${name.toLowerCase()}, ${fmt(b.value, "USD")}`} />
                    <span className="num text-right text-[12px] text-ink">{fmt(b.value, "USD")}</span>
                  </div>
                ) : null;
              })}
            </div>
          </div>
        ))}
      </div>
    </Figure>
  );
}

const KINDS = { buy: ["var(--s1)", "a promise to buy"], stake: ["var(--s3)", "a stake or a guarantee"] } as const;

// Who is tied to whom on the financing ledger: suppliers and investors on the left, the labs on the right.
export function TiesPlate({ ties }: { ties: CaptureFigures["ties"] }) {
  if (!ties) return null;
  const side = (nodes: NonNullable<CaptureFigures["ties"]>["left"], align: string) => (
    <div className="relative">
      {nodes.map((n) => (
        <span key={n.id} className={`absolute inset-x-0 -translate-y-1/2 text-[11.5px] leading-[1.15] text-ink sm:text-[12.5px] ${align}`} style={{ top: `${n.label_y}%` }}>
          {n.name} <span className="num whitespace-nowrap text-muted">{fmt(n.value, "USD")}</span>
        </span>
      ))}
    </div>
  );
  return (
    <Figure
      id="ties"
      title="The same companies fund the labs and sell to them: money promised between each pair"
      note={`${KIND_LABEL.chart} · face value promised, not money paid · ${fmt(ties.total.value, "USD")} in all`}
      keys={<>
        <Key swatch={<Swatch fill={KINDS.buy[0]} />}>a promise to buy: a contract or a spending commitment, mostly the lab buying computing</Key>
        <Key swatch={<Swatch fill={KINDS.stake[0]} />}>a stake or a guarantee: money or credit the supplier puts behind the other side</Key>
      </>}
      foot={<>
        <p>Each band joins a supplier or investor, on the left, to a frontier lab, on the right, and its thickness is the face value of the signed deals between them on <Link href="/ledger" className={a}>the financing ledger</Link> as of {ties.total.as_of}: the same rows that <Link href={ties.total.href} className={a}>the gauge of circular financing</Link> counts, from company filings and announcements and, for a few, press reports. Circular financing means a supplier funding the customer that then spends the money with that supplier, so where a pair has a band of each colour, money is promised in both directions.</p>
        <p>A few very large deals make up most of the total, so a single cancelled or renegotiated deal would redraw the picture. These are promises, most of them running for many years: amounts described as up to a ceiling are counted in full, and nothing here says how much has been paid. Letters of intent and talks are on the ledger but not drawn. Suppliers beyond the largest are gathered into a single band, and deals with no frontier lab in them, such as a data-centre owner leasing to a cloud company, run along the bottom. The ledger holds what this site has found and read, so it is a floor.</p>
      </>}
      table={
        <table className={tbl}>
          <thead><tr>{["Supplier or investor", "Other side", "Kind", "Face value", "Deals", "Of which press-reported"].map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr></thead>
          <tbody>{ties.pairs.map((p) => (
            <tr key={p.a + p.b + p.kind} className="border-b border-grid align-top">
              <th scope="row" className="py-2 pr-4 font-medium text-ink">{p.a_name}</th>
              <td className={td}>{p.b_name}</td>
              <td className={td}>{KINDS[p.kind][1]}</td>
              <td className={`${td} tabular-nums`}><Link href={p.href} prefetch={false} className={a}>{fmt(p.value, "USD")}</Link></td>
              <td className={`${td} tabular-nums`}>{fmt(p.n, "count")}</td>
              <td className={`${td} tabular-nums`}>{p.press ? fmt(p.press, "count") : "—"}</td>
            </tr>
          ))}</tbody>
        </table>
      }
      tableLabel="Every pairing and its face value"
    >
      <div className="mb-4 mt-1 grid h-[35rem] sm:h-[30rem] grid-cols-[5.75rem_minmax(0,1fr)_5.75rem] gap-x-2 sm:grid-cols-[10rem_minmax(0,1fr)_10rem] sm:gap-x-3">
        {side(ties.left, "text-right")}
        <div className="relative">
          <Flow
            label="Bands between suppliers and investors on the left and frontier labs on the right, each as thick as the face value promised between the pair"
            left={ties.left} right={ties.right}
            bands={ties.bands.map((b) => ({ key: b.left + b.right + b.kind, d: b.d, fill: KINDS[b.kind][0], tip: `${b.left_name} and ${b.right_name}: ${KINDS[b.kind][1]}, ${fmt(b.value, "USD")} at face` }))}
          />
        </div>
        {side(ties.right, "text-left")}
      </div>
    </Figure>
  );
}

// The concentration indices the site holds, on one scale from many equal firms to a single firm.
export function ConcentrationPlate({ strip }: { strip: CaptureFigures["concentration"] }) {
  if (!strip.rows.length) return null;
  const cols = "grid grid-cols-1 gap-x-4 gap-y-1 sm:grid-cols-[17rem_minmax(0,1fr)_3rem] sm:items-center";
  return (
    <Figure
      id="concentration"
      title="The concentration indices this site holds, on one scale"
      note={`${KIND_LABEL.chart} · each dot is an index of concentration at its latest reading`}
      keys={<Key swatch={<span className="inline-block h-2.5 w-2.5 rounded-full bg-s1" />}>the latest reading of the index; further right means fewer firms hold more of the market</Key>}
      foot={<p>The index is the Herfindahl index, HHI for short: square each firm&apos;s share of a market and add the squares. It sits near the left when many firms hold equal shares and reaches the right end when a single firm holds everything. The dots are not like for like. The chip and cloud rows each count only a handful of listed companies&apos; filed segments, and an index over so few firms cannot read low however evenly they share, so those rows overstate concentration in the wider market. The lab and model rows count the text passing through a single router, OpenRouter, in its published top table; large buyers mostly go direct to the labs and never appear there. What each index counts is in the table beneath. Read the order of the rows, not the exact gaps.</p>}
      table={
        <table className={tbl}>
          <thead><tr>{["Index", "Layer", "Reading", "As of", "Reads tonight", "What it counts"].map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr></thead>
          <tbody>{strip.rows.map((r) => (
            <tr key={r.id} className="border-b border-grid align-top">
              <th scope="row" className="py-2 pr-4 font-normal text-ink"><Link href={r.href} prefetch={false} className={a}>{r.name}</Link></th>
              <td className={td}>{r.layer}</td>
              <td className={`${td} tabular-nums`}>{fmt(r.value)}</td>
              <td className={`${td} tabular-nums whitespace-nowrap`}>{r.as_of}</td>
              <td className={td}>{words(r.status)}</td>
              <td className={`${td} min-w-[18rem]`}>{r.counts}</td>
            </tr>
          ))}</tbody>
        </table>
      }
    >
      <div className="flex flex-col gap-3">
        {strip.rows.map((r) => (
          <div key={r.id} className={cols}>
            <Link href={r.href} prefetch={false} className={`text-[13px] leading-tight text-ink ${a}`}>{r.name}</Link>
            <div className="grid grid-cols-[minmax(0,1fr)_3rem] items-center gap-x-4 sm:contents">
              <Track label={`${r.name}: ${fmt(r.value)}`}><TrackDot x={r.x} tip={`${r.name}: ${fmt(r.value)} as of ${r.as_of}`} /></Track>
              <span className="num text-right text-[12.5px] text-ink">{fmt(r.value)}</span>
            </div>
          </div>
        ))}
        <div aria-hidden className={cols}>
          <span className="max-sm:hidden" />
          <div className="flex justify-between font-mono text-[10.5px] text-muted max-sm:mr-[4rem]"><span>many equal firms</span><span>a single firm</span></div>
        </div>
      </div>
    </Figure>
  );
}
