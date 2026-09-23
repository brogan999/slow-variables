import Link from "next/link";
import { indicatorHref } from "@/lib/format";
import { ChangelogList } from "@/components/Changelog";
import { EvidenceLog } from "@/components/EvidenceLog";
import { Inline } from "@/components/Essay";
import { Fact } from "@/components/Fact";
import { StatusChip, WordChip } from "@/components/StatusChip";
import { type BoardRow, board, index, obsIndex, outlook, predictions } from "@/lib/data";

export const metadata = { title: "Predictions" };

const KIND: Record<string, string> = { ledger: "dated claim", outlook: "tested nightly", migration: "bottleneck essay", exit: "what would change our mind" };

function Rows({ rows, label }: { rows: BoardRow[]; label: Record<string, string> }) {
  const o = outlook();
  return (
    <ul>
      {rows.map((r) => (
        <li key={`${r.kind}-${r.id}`} className="border-t border-grid py-3 grid gap-x-4 gap-y-1.5 sm:grid-cols-[12rem_minmax(0,1fr)]">
          <div><WordChip word={r.word} label={label[r.word]} /></div>
          <div className="min-w-0">
            <p className="text-[15px] leading-snug text-ink"><Inline text={r.line} facts={o.facts} tests={o.tests} /></p>
            <p className="mt-1 text-xs text-ink-2">
              {r.who} · {KIND[r.kind]}
              {r.reading ? <> · reads <Fact f={r.reading} /> as of {r.reading.as_of}</> : null}
              {" · "}<Link href={r.href} className="underline decoration-grid underline-offset-2 hover:text-ink">details<span className="sr-only"> of {r.who}&apos;s prediction</span></Link>
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}

function Board() {
  const b = board();
  const label = Object.fromEntries(b.words.map((w) => [w.id, w.label]));
  return (
    <div className="flex flex-col gap-8">
      <div role="group" className="flex flex-wrap items-center gap-2" aria-label="Tonight's tally">
        {b.words.map((w) => <span key={w.id} className="inline-flex items-center gap-1.5"><WordChip word={w.id} label={w.label} /><span className="num text-sm text-ink-2">{b.tally[w.id]}</span></span>)}
      </div>
      <details className="text-sm -mt-5">
        <summary className="cursor-pointer text-ink-2">What the words mean</summary>
        <dl className="mt-2 grid gap-x-4 gap-y-1 sm:grid-cols-[12rem_minmax(0,1fr)]">
          {b.words.map((w) => <div key={w.id} className="contents"><dt><WordChip word={w.id} label={w.label} /></dt><dd className="text-ink-2">{w.meaning}</dd></div>)}
        </dl>
        <p className="mt-2 text-ink-2">Each family keeps its own vocabulary on its own page; the board maps it: {b.mapping.map((m) => `${m.kind} ${m.state.replaceAll("_", " ")} → ${b.words.find((w) => w.id === m.word)?.label.toLowerCase()}`).join("; ")}.</p>
      </details>
      {b.folios.map((f) => (
        <section key={f.id} aria-labelledby={`folio-${f.id}`}>
          <h2 id={`folio-${f.id}`} className="display text-2xl leading-tight">{f.label}</h2>
          <p className="text-sm text-muted mb-2">{f.question}</p>
          <Rows rows={f.rows.filter((r) => r.word !== "too_early")} label={label} />
          {f.too_early ? (
            <details className="border-t border-grid">
              <summary className="cursor-pointer py-2 text-sm text-ink-2">{f.too_early} more that are too early to tell</summary>
              <Rows rows={f.rows.filter((r) => r.word === "too_early")} label={label} />
            </details>
          ) : null}
          {f.id === "capability" ? (
            <details className="mt-3 text-sm">
              <summary className="cursor-pointer text-ink-2">Ten questions about capability, and what this site reads for each</summary>
              <ul className="mt-2">
                {b.questions.map((q) => (
                  <li key={q.question} className="border-t border-grid py-2 grid gap-x-4 gap-y-1 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
                    <span className="text-ink">{q.question}</span>
                    <span className="text-ink-2">
                      {q.href ? <><Link href={q.href} className="underline decoration-grid underline-offset-2 hover:text-ink">{index().indicators.find((i) => i.id === q.indicator)?.name ?? q.indicator}</Link> {q.status ? <StatusChip status={q.status} /> : null}</> : null}
                      {q.note ? <span className="block">{q.note}</span> : null}
                    </span>
                  </li>
                ))}
              </ul>
            </details>
          ) : null}
        </section>
      ))}
    </div>
  );
}

const LEDGERS: Record<string, string> = { nk: "Narayanan & Kapoor", lab: "Lab timelines", ai2027: "AI 2027", capture: "Capture theses" };

export default function PredictionsPage() {
  const rows = predictions();
  const idx = obsIndex();
  const { indicators } = index();
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="display text-[2.5rem] md:text-[3.5rem] leading-[1.02] max-w-[24ch]">Predictions</h1>
        <p className="text-lg leading-snug text-ink-2 max-w-[60ch]">Every prediction on this site in one place: what the labs, named writers and this site expect, each read against the latest data and given one word. Tap &ldquo;details&rdquo; for the test, the reading and the source.</p>
      </div>
      <Board />
      <div>
        <h2 className="display text-[1.75rem] leading-tight mt-4">The dated claims in their own words</h2>
        <p className="text-sm text-ink-2 max-w-[60ch]">Other people&apos;s claims with a date attached, quoted from the linked source and scored with the AI 2027 tracker&apos;s vocabulary (confirmed, ahead, on track, behind, emerging, not yet testable). A claimant&apos;s self-assessment never resolves a claim.</p>
      </div>
      {Object.entries(LEDGERS).map(([ledger, name]) => {
        const items = rows.filter((p) => p.ledger === ledger && p.published);
        return (
          <section key={ledger}>
            <h3 className="display text-xl leading-tight mb-3 mt-2">{name} <span className="text-muted">· {items.length}</span></h3>
            {items.length ? (
              <ol className="flex flex-col gap-3">
                {items.map((p) => (
                  <li key={p.id} id={p.id} className="panel p-4 scroll-mt-4 target:bg-surface-2">
                    <div className="flex flex-wrap items-center gap-2 text-xs text-ink-2">
                      <h4 className="font-medium text-ink">{p.claimant}</h4>
                      <span className="tabular-nums">{p.claim_date}</span>
                      {p.window_end ? <span>window to {p.window_end}</span> : null}
                      <StatusChip status={p.status} />
                      {p.confidence_now !== null ? <span>conf {p.confidence_now}</span> : null}
                    </div>
                    <blockquote className="mt-2 border-l-2 border-grid pl-3 text-base leading-[1.6]">&ldquo;{p.claim_text}&rdquo; {p.claim_url ? <a href={p.claim_url} className="text-xs text-ink-2 underline decoration-grid underline-offset-4">source</a> : null}</blockquote>
                    <p className="mt-2 text-sm"><span className="text-muted">How we track it.</span> {p.operationalisation}</p>
                    {p.direction_assessment || p.magnitude_assessment || p.timing_assessment ? (
                      <dl className="mt-2 grid gap-x-3 gap-y-1 text-sm sm:grid-cols-[6rem_minmax(0,1fr)]">
                        {([["Direction", p.direction_assessment], ["Magnitude", p.magnitude_assessment], ["Timing", p.timing_assessment]] as const).map(([k, v]) => v ? <div key={k} className="contents"><dt className="text-muted">{k}</dt><dd>{v}</dd></div> : null)}
                      </dl>
                    ) : null}
                    {p.related_indicators.length ? <p className="mt-1 text-xs text-ink-2">Indicators: {p.related_indicators.map((r) => <Link key={r} href={indicatorHref(r, indicators.find((i) => i.id === r)?.published)} className="hover:underline mr-2">{indicators.find((i) => i.id === r)?.name ?? r}</Link>)}</p> : null}
                    <details className="mt-2 text-sm"><summary className="cursor-pointer text-ink-2">Counterevidence and history</summary>
                      <p className="mt-1">{p.counterevidence}</p>
                      {p.evidence.length ? <div className="mt-2"><EvidenceLog items={p.evidence} /></div> : null}
                      <div className="mt-2"><ChangelogList events={p.status_events} obsIndex={idx} showTarget={false} /></div>
                    </details>
                  </li>
                ))}
              </ol>
            ) : <p className="text-sm text-muted">No sourced claims yet in this family.</p>}
          </section>
        );
      })}
    </div>
  );
}
