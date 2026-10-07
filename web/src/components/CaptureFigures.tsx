import Link from "next/link";
import { Figure, Key } from "@/components/Figure";
import { StatusChip } from "@/components/StatusChip";
import { Bar, Dot, Flow, GaugeDot, Track, TrackDot, Unreachable } from "@/components/diagrams/capture";
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
      title="Every gauge of who keeps the profit, layer by layer, and what each reads at the latest update"
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
      foot={<p>{rule.foot} This is a drawing of an idea, with no number of its own. It is the rule argued in <Link href="/argument/migration" className={a}>the essay on where profit moves</Link>, from Ricardo on rent and Teece on who profits from an invention; the charts on this page show where profit sits now, which is evidence about the rule and not a test of it.</p>}
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
  const est = year.rows.find((r) => r.now.basis?.length);
  const dated = (b: { when: string; href: string | null }) => b.href ? <Link href={b.href} prefetch={false} className={a}>{b.when}</Link> : b.when;
  return (
    <Figure
      id="year-on-year"
      title="How each part's share of the profit moved over the last year"
      note={`${KIND_LABEL.chart} · the newest quarter against the same quarter a year before`}
      keys={<>
        <Key swatch={<Dot hollow />}>a year before</Key>
        <Key swatch={<Dot />}>the newest quarter</Key>
        <Key swatch={<span className="inline-flex gap-1"><Dot hollow hatched /><Dot hatched /></span>}>an estimate by this site, at either end: the labs&apos; share</Key>
      </>}
      foot={<>
      <p>The same shares as the columns in the figures of gross profit and operating income on this page, read at their ends: where each part stood in the newest quarter on file and in the same quarter a year before. Gross profit is revenue less the cost of delivering the product; operating income also takes off research, selling and running costs. A share can rise while the money itself falls, and the reverse, because every part is measured against the total of the parts drawn. Apps, and labs in the operating measure, file nothing usable and are left out, so these are shares of what can be measured, not of the whole industry.</p>
      <p>The labs&apos; share is this site&apos;s estimate, not a filing: for OpenAI and Anthropic, the latest run-rate reported before the quarter ended, divided across the year&apos;s quarters, times Epoch AI&apos;s estimate of what is left after the cost of running the models. A run-rate is a recent month or quarter of sales multiplied up to a year. The run-rate used can be some months older than the quarter, so the labs&apos; two dots are not exactly a year apart and the newest one is likely too low.{est ? <> The run-rates used are dated: {est.now.basis?.map((b, i) => {
        const old = est.then?.basis?.find((o) => o.name === b.name);
        return <span key={b.name}>{i ? "; " : ""}{b.name}, {old ? <>{dated(old)} for {est.then?.quarter} and </> : null}{dated(b)} for {est.now.quarter}</span>;
      })}.</> : null} In the gross-profit rows chips are the whole of NVIDIA and AMD and cloud is a single company&apos;s cloud segment; in the operating-income rows both are the segments named beneath the last figure on this page.</p>
      </>}
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
                    {r.then ? <TrackDot x={r.then.x} hollow hatched={r.then.estimated} tip={`${r.name}, ${r.then.quarter}: ${fmt(r.then.value, "share")}${r.then.estimated ? ", an estimate" : ""}`} /> : null}
                    <TrackDot x={r.now.x} hatched={r.now.estimated} tip={`${r.name}, ${r.now.quarter}: ${fmt(r.now.value, "share")}${r.now.estimated ? ", an estimate" : ""}`} />
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
  ["equity", "var(--s3)", "Paid in by investors", "has raised"],
  ["promised", "var(--s2)", "Signed up to pay suppliers", "signed up to pay"],
] as const;
// Who said the run-rate (Epoch's own source type) and how sure Epoch is of it (its grade, which is also the hatching).
const SAID: Record<string, string> = { press: "a press report", company: "stated by the company", both: "stated by the company and reported by the press", other: "as compiled by Epoch AI" };
const GRADE: Record<string, string> = { estimate: "graded as likely by Epoch AI", reported: "graded as confident by Epoch AI" };
const told = (b: CaptureFigures["labs"]["rows"][number]["run_rate"]) => `${SAID[b.said ?? "other"] ?? SAID.other}${b.stamp && GRADE[b.stamp] ? `, ${GRADE[b.stamp]}` : ""}`;

// Each compared lab's yearly sales pace beside the money paid in and the payments signed up to, on one dollar scale;
// a lab with too little on record is listed beneath with no multiple and no bar (the rule is the export's).
export function LabsPlate({ labs }: { labs: CaptureFigures["labs"] }) {
  const compared = labs.rows.filter((r) => !r.thin), thin = labs.rows.filter((r) => r.thin);
  return (
    <Figure
      id="labs"
      title="What the largest AI labs sell in a year, beside what investors have put in and what the labs have signed up to pay suppliers"
      note={`${KIND_LABEL.chart} · one dollar scale · each lab at the date of its own latest report`}
      keys={<>
        <Key swatch={<Swatch fill="var(--s1)" hatched />}>sales a year at the latest pace, from a press report that Epoch AI grades as likely</Key>
        <Key swatch={<Swatch fill="var(--s1)" />}>the same, as stated by the company itself; neither kind is audited</Key>
        <Key swatch={<Swatch fill="var(--s3)" />}>money investors had paid in by that date, from the rounds on record</Key>
        <Key swatch={<Swatch fill="var(--s2)" />}>payments to suppliers the lab has signed up to, over many years, at the full amount written in the deal</Key>
      </>}
      foot={<>
        <p>What each bar rests on. Sales a year is a run-rate: a recent month or quarter of sales multiplied up to a year, or the yearly value of current subscriptions, as told to the press or stated by the lab and compiled by Epoch AI. It is not booked revenue, no auditor has checked it, labs differ on whether they count sales before or after a partner&apos;s cut, and this site marks every such figure as disputed. Each lab is drawn at the date of its own latest report, and those dates differ. Money raised is the sum of the funding rounds on record up to that date; it leaves out debt and any round this site does not hold, so it is a floor. Payments signed up to is the full written amount of the contracts and commitments on <Link href="/ledger" className={a}>the financing ledger</Link> in which the lab is the buyer: they run over many years, amounts described as up to a ceiling are counted in full, some are press reports that the supplier has not confirmed, and none of it is money paid. It is a floor too: deals with no dollar figure are left out, and a lab&apos;s own statement of its total commitments is not used. A lab with no such bar has no priced deal on the ledger, which is not the same as having promised nothing.</p>
        <p>Labs with only a round or two of funding on record, or whose latest figure is much older than the others, are listed beneath without a multiple. {labs.absent.length ? <>{labs.absent.join(" and ")} have no run-rate on record{labs.no_rounds.length ? <>, and {labs.no_rounds.join(" and ")} have a run-rate but no funding round</> : null}, so none of them has a row. </> : null}This page is drafted by a Claude model, made by Anthropic, which is drawn here. Anthropic&apos;s sales figure is a press report, drawn hatched by the same rule as any other lab&apos;s press-reported figure, and the model has no figure of its own.</p>
      </>}
      table={
        <table className={tbl}>
          <thead><tr>{["Lab", "Run-rate", "Dated", "Who said it", "Paid in by then", "Rounds on record", "Raised after that date", "Run-rate over money paid in", "Signed up to pay suppliers", "Deals"].map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr></thead>
          <tbody>{labs.rows.map((r) => (
            <tr key={r.id} className="border-b border-grid align-top">
              <th scope="row" className="py-2 pr-4 font-medium text-ink">{r.name}</th>
              <td className={`${td} tabular-nums`}>{r.run_rate.href ? <Link href={r.run_rate.href} prefetch={false} className={a}>{fmt(r.run_rate.value, "USD")}</Link> : fmt(r.run_rate.value, "USD")}</td>
              <td className={`${td} whitespace-nowrap`}>{r.run_rate.when}</td>
              <td className={`${td} min-w-[11rem]`}>{told(r.run_rate)}</td>
              <td className={`${td} tabular-nums`}>{r.equity.href ? <Link href={r.equity.href} prefetch={false} className={a}>{fmt(r.equity.value, "USD")}</Link> : fmt(r.equity.value, "USD")}</td>
              <td className={`${td} tabular-nums`}>{fmt(r.equity.n, "count")}</td>
              <td className={`${td} tabular-nums`}>{r.later ? fmt(r.later.value, "USD") : "—"}</td>
              <td className={`${td} tabular-nums`}>{r.ratio ? <Link href={r.ratio.href} prefetch={false} className={a}>{fmt(r.ratio.value, "ratio")}</Link> : "not drawn: too little on record"}</td>
              <td className={`${td} tabular-nums`}>{r.promised ? <Link href={r.promised.href ?? "/ledger"} prefetch={false} className={a}>{fmt(r.promised.value, "USD")}</Link> : "no priced deal on the ledger"}</td>
              <td className={`${td} tabular-nums`}>{r.promised ? fmt(r.promised.n, "count") : "—"}</td>
            </tr>
          ))}</tbody>
        </table>
      }
    >
      <div className="flex flex-col">
        {compared.map((r) => (
          <div key={r.id} className="grid grid-cols-1 gap-x-4 gap-y-2 border-t border-grid py-3 first:border-t-0 first:pt-0 sm:grid-cols-[13rem_minmax(0,1fr)]">
            <div className="flex flex-col gap-0.5">
              <span className="text-[14px] font-medium text-ink">{r.name}</span>
              <span className="text-[12px] leading-snug text-ink-2">{r.run_rate.when}: {told(r.run_rate)}</span>
              {r.ratio ? <span className="text-[12px] leading-snug text-muted">a year of sales at this pace is <Link href={r.ratio.href} prefetch={false} className={a}>{fmt(r.ratio.value, "ratio")}</Link> the money raised</span> : null}
              {r.later ? <span className="text-[12px] leading-snug text-muted">a further {fmt(r.later.value, "USD")} was raised after this date and is not in the bar</span> : null}
            </div>
            <div className="flex flex-col gap-1">
              {LAB_BARS.map(([k, fill, name, short]) => {
                const b = r[k];
                return b ? (
                  <div key={k} className="grid grid-cols-[7.25rem_minmax(0,1fr)_3.5rem] items-center gap-x-2">
                    <span className="font-mono text-[11px] text-muted">{short}</span>
                    {b.small
                      ? <span className="border-l-2 pl-1.5 text-[11.5px] leading-tight text-muted" style={{ borderColor: fill }}>too thin to draw on this scale</span>
                      : <Bar w={b.w ?? 0} fill={fill} hatched={k === "run_rate" && b.stamp === "estimate"} tip={`${r.name}: ${name.toLowerCase()}, ${fmt(b.value, "USD")}`} />}
                    <span className="num text-right text-[12px] text-ink">{fmt(b.value, "USD")}</span>
                  </div>
                ) : null;
              })}
            </div>
          </div>
        ))}
        {thin.length || labs.no_rounds.length ? (
          <div className="mt-2 border-t border-ink pt-3">
            <h3 className="eyebrow">Too little on record to compare</h3>
            <ul className="mt-2 flex flex-col gap-1.5 text-[13px] leading-snug text-ink-2">
              {thin.map((r) => {
                const rr = r.run_rate.href ? <Link href={r.run_rate.href} prefetch={false} className={a}>{fmt(r.run_rate.value, "USD")}</Link> : fmt(r.run_rate.value, "USD");
                return (
                  <li key={r.id}><span className="font-medium text-ink">{r.name}</span>: {r.thin_why === "stale"
                    ? <>the latest figure on record, {rr} a year, is from {r.run_rate.when}, too old to set beside the others.{r.later ? <> A further {fmt(r.later.value, "USD")} was raised after that date.</> : null}</>
                    : <>sells {rr} a year as of {r.run_rate.when} ({told(r.run_rate)}). Only {fmt(r.equity.n, "count")} funding {(r.equity.n ?? 0) < 2 ? "round is" : "rounds are"} on record, so no multiple is drawn.</>}
                  </li>
                );
              })}
              {labs.no_rounds.length ? <li><span className="font-medium text-ink">{labs.no_rounds.join(" and ")}</span>: a run-rate is on record but no funding round, so nothing is drawn.</li> : null}
            </ul>
          </div>
        ) : null}
      </div>
    </Figure>
  );
}

const KINDS = { buy: ["var(--s2)", "a promise to buy"], stake: ["var(--s3)", "a stake or a guarantee"] } as const;

// Who is tied to whom on the financing ledger: suppliers and investors on the left, the labs on the right.
export function TiesPlate({ ties }: { ties: CaptureFigures["ties"] }) {
  if (!ties) return null;
  const cols = "grid grid-cols-[5.75rem_minmax(0,1fr)_5.75rem] gap-x-2 sm:grid-cols-[10rem_minmax(0,1fr)_10rem] sm:gap-x-3";
  const side = (nodes: NonNullable<CaptureFigures["ties"]>["left"], align: string) => (
    <div className="relative">
      {nodes.map((n) => (
        <span key={n.id} className={`absolute inset-x-0 -translate-y-1/2 text-[11.5px] leading-[1.15] text-ink sm:text-[12.5px] ${align}`} style={{ top: `${n.label_y}%` }}>
          {n.name} <span className="num whitespace-nowrap text-muted">{fmt(n.value, "USD")}</span>
          {n.both ? <span className="block font-mono text-[10px] uppercase tracking-wide text-ink-2">funds and sells</span> : null}
        </span>
      ))}
    </div>
  );
  const most = ties.right[0];
  return (
    <Figure
      id="ties"
      title="Which companies both fund the labs and sell to them, and which do only one"
      note={`${KIND_LABEL.chart} · the full amounts written in signed deals, not money paid · ${fmt(ties.total.value, "USD")} in all`}
      keys={<>
        <Key swatch={<Swatch fill={KINDS.buy[0]} />}>a promise to buy: a contract or a spending commitment, mostly the lab buying computing</Key>
        <Key swatch={<Swatch fill={KINDS.stake[0]} />}>a stake or a guarantee: money or credit the supplier puts behind the other side</Key>
        <Key swatch={<span className="inline-block h-2.5 w-4 border-[1.5px] border-dashed border-s2 bg-s2/45" />}>paler with a broken edge: reported by the press and marked disputed on the ledger, because the supplier&apos;s own filings do not confirm it</Key>
        <Key swatch={<span className="font-mono text-[10px] uppercase tracking-wide text-ink-2">funds and sells</span>}>a company with both a sale to a lab and a stake in that lab or a guarantee behind it</Key>
      </>}
      foot={<>
        <p>Each band joins a supplier or investor, on the left, to a lab, on the right, and its thickness is the full amount written in the signed deals between them on <Link href="/ledger" className={a}>the financing ledger</Link>; the newest deal on it is dated {ties.total.when}. That is every signed deal the ledger holds since its first row, so it is larger than <Link href={ties.total.href} className={a}>the gauge of circular financing</Link>, which counts only deals signed in the trailing year. Circular financing means a supplier funding the customer that then spends the money with that supplier. The ledger does not record which way money moves, so a band is a tie, not a flow: where a pair has a band of each colour, the same company has both a sale to the lab and a stake in it or a guarantee behind it.</p>
        <p>A few very large deals make up most of the total, so a single cancelled or renegotiated deal would redraw the picture. These are promises, most of them running for many years: amounts described as up to a ceiling are counted in full, and nothing here says how much has been paid. A guarantee is a promise to pay only if the company it backs does not, so it may never be drawn on. Letters of intent and talks are on the ledger but not drawn. Suppliers beyond the largest are gathered into a single band, and deals with no frontier lab in them, such as a data-centre owner leasing to a cloud company, run along the bottom; labs outside the frontier group, such as Mistral, fall in the bottom band. Meta is on the right because this site files it with the frontier labs, though these deals serve its whole business; Alphabet, which owns a rival lab, is on the left because here it is the investor. The ledger holds what this site has found and read, so it is a floor.</p>
      </>}
      table={
        <table className={tbl}>
          <thead><tr>{["Supplier or investor", "Other side", "Kind", "Full amount written", "Deals", "Of which press-reported", "Of which disputed"].map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr></thead>
          <tbody>{ties.pairs.map((p) => (
            <tr key={p.a + p.b + p.kind} className="border-b border-grid align-top">
              <th scope="row" className="py-2 pr-4 font-medium text-ink">{p.a_name}</th>
              <td className={td}>{p.b_name}</td>
              <td className={td}>{KINDS[p.kind][1]}</td>
              <td className={`${td} tabular-nums`}><Link href={p.href} prefetch={false} className={a}>{fmt(p.value, "USD")}</Link></td>
              <td className={`${td} tabular-nums`}>{fmt(p.n, "count")}</td>
              <td className={`${td} tabular-nums`}>{p.press ? fmt(p.press, "count") : "—"}</td>
              <td className={`${td} tabular-nums`}>{p.disputed ? fmt(p.disputed, "count") : "—"}</td>
            </tr>
          ))}</tbody>
        </table>
      }
      tableLabel="Every pairing and the full amount written"
    >
      <div aria-hidden className={`${cols} pb-2 font-mono text-[10.5px] uppercase leading-tight tracking-wider text-muted`}>
        <span className="text-right">Suppliers and investors</span><span /><span>Labs</span>
      </div>
      <div className={`${cols} mb-8 h-[35rem] sm:h-[30rem]`}>
        {side(ties.left, "text-right")}
        <div className="relative">
          <Flow
            label="Bands between suppliers and investors on the left and labs on the right, each as thick as the full amount written in the deals between the pair"
            left={ties.left} right={ties.right}
            bands={ties.bands.map((b) => ({ key: b.left + b.right + b.kind + b.disputed, d: b.d, fill: KINDS[b.kind][0], broken: b.disputed, tip: `${b.left_name} and ${b.right_name}: ${KINDS[b.kind][1]}, ${fmt(b.value, "USD")} written in the deal${b.disputed ? ", marked disputed on the ledger" : ""}` }))}
          />
        </div>
        {side(ties.right, "text-left")}
      </div>
      <p className="max-w-[68ch] text-[13px] leading-snug text-ink-2">Thickness is the full amount written in the deals, not money paid. {most.name} is a party to {fmt(most.share, "share")} of everything drawn. The ledger records no direction, so no arrow is drawn.</p>
    </Figure>
  );
}

const GROUPS: Record<string, string> = { filed: "Among the listed companies that file a segment", router: "Within one router's published top table" };
const GROUP_END: Record<string, string> = { filed: "a single firm", router: "a single lab or model" };

// Each concentration index beside the lowest it could read, in the two groups that can be read together.
export function ConcentrationPlate({ strip }: { strip: CaptureFigures["concentration"] }) {
  if (!strip.rows.length) return null;
  const cols = "grid grid-cols-1 gap-x-4 gap-y-1 sm:grid-cols-[17rem_minmax(0,1fr)_3rem] sm:items-center";
  const groups = [...new Set(strip.rows.map((r) => r.group))];
  return (
    <Figure
      id="concentration"
      title="How concentrated each layer looks, beside the lowest each index could read"
      note={`${KIND_LABEL.chart} · each dot is an index of concentration at its latest reading`}
      keys={<>
        <Key swatch={<Dot />}>the latest reading; the right end of the line is a single firm holding everything</Key>
        <Key swatch={<span className="inline-block h-2.5 w-4 border-r-2 border-ink-2 bg-grid" />}>readings the index cannot give; its right edge is equal shares among the firms counted</Key>
      </>}
      foot={<p>The index is the Herfindahl index, HHI for short: square each firm&apos;s share of a market and add the squares. It reaches the right end when a single firm holds everything. A segment is a division a company reports separately; a router is a service that passes a request to whichever model the buyer picks, its top table is the list of most-used models it publishes each day, and tokens are the pieces of text a model reads and writes. The chip and cloud rows each count only a handful of listed companies&apos; filed segments and say nothing of firms that file none. The lab and model rows count the text passing through a single router, OpenRouter, in its published top table; large buyers mostly go direct to the labs and never appear there. The rows are read on different dates, shown beside each, and what each index counts is in the table beneath. An index over a few firms cannot read low however evenly they share: the block at the left of each row is the part it cannot reach. Read each dot against its own block, and do not rank one row against another.</p>}
      table={
        <table className={tbl}>
          <thead><tr>{["Index", "Layer", "Reading", "Counts", "As of", "Reads now", "What it counts"].map((c) => <th key={c} scope="col" className={th}>{c}</th>)}</tr></thead>
          <tbody>{strip.rows.map((r) => (
            <tr key={r.id} className="border-b border-grid align-top">
              <th scope="row" className="py-2 pr-4 font-normal text-ink"><Link href={r.href} prefetch={false} className={a}>{r.name}</Link></th>
              <td className={td}>{r.layer}</td>
              <td className={`${td} tabular-nums`}>{fmt(r.value)}</td>
              <td className={`${td} tabular-nums whitespace-nowrap`}>{fmt(r.n, "count")} {r.of}</td>
              <td className={`${td} whitespace-nowrap`}>{r.when}</td>
              <td className={td}>{words(r.status)}</td>
              <td className={`${td} min-w-[18rem]`}>{r.counts}</td>
            </tr>
          ))}</tbody>
        </table>
      }
    >
      <div className="flex flex-col gap-6">
        {groups.map((g) => (
          <div key={g} className="flex flex-col gap-3">
            <h3 className="eyebrow">{GROUPS[g] ?? g}</h3>
            {strip.rows.filter((r) => r.group === g).map((r) => (
              <div key={r.id} className={cols}>
                <Link href={r.href} prefetch={false} className={`text-[13px] leading-tight text-ink ${a}`}>{r.name}</Link>
                <div className="grid grid-cols-[minmax(0,1fr)_3rem] items-center gap-x-4 sm:contents">
                  <Track label={`${r.name}: ${fmt(r.value)}, counting ${fmt(r.n, "count")} ${r.of}`}>
                    <Unreachable x={r.floor_x} />
                    <TrackDot x={r.x} tip={`${r.name}: ${fmt(r.value)} as of ${r.when}`} />
                  </Track>
                  <span className="num text-right text-[12.5px] text-ink">{fmt(r.value)}</span>
                </div>
                <span className="max-sm:hidden" />
                <span className="font-mono text-[10.5px] leading-snug text-muted sm:col-span-2">counts {fmt(r.n, "count")} {r.of}; cannot read inside the grey block · as of {r.when}</span>
              </div>
            ))}
            <div aria-hidden className={cols}>
              <span className="max-sm:hidden" />
              <div className="flex justify-end font-mono text-[10.5px] text-muted max-sm:mr-[4rem]"><span>{GROUP_END[g] ?? GROUP_END.filed}</span></div>
            </div>
          </div>
        ))}
      </div>
    </Figure>
  );
}
