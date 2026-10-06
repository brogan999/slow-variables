import Link from "next/link";
import { indicatorHref } from "@/lib/format";
import { BoardFlow, DueCalendar, ForecasterMarks, LeanBars, SourceMarks, TallyBars } from "@/components/BoardFigures";
import { ChangelogList } from "@/components/Changelog";
import { EvidenceLog } from "@/components/EvidenceLog";
import { Inline } from "@/components/Essay";
import { Fact } from "@/components/Fact";
import { PageHeader } from "@/components/PageHeader";
import { StatusChip, WordChip } from "@/components/StatusChip";
import { type BoardRow, board, index, obsIndex, outlook, predictions } from "@/lib/data";

export const metadata = { title: "Predictions" };

const KIND: Record<string, string> = { ledger: "dated claim", outlook: "tested nightly", migration: "bottleneck essay", exit: "what would change our mind" };

function Rows({ rows, label, leans = {} }: { rows: BoardRow[]; label: Record<string, string>; leans?: Record<string, string> }) {
  const o = outlook();
  return (
    <ul>
      {rows.map((r) => (
        <li key={`${r.kind}-${r.id}`} data-word={r.word} className="border-t border-grid py-3 grid gap-x-4 gap-y-1.5 sm:grid-cols-[12rem_minmax(0,1fr)]">
          <div><WordChip word={r.word} label={label[r.word]} /></div>
          <div className="min-w-0">
            <p className="text-[15px] leading-snug text-ink"><Inline text={r.line} facts={o.facts} tests={o.tests} /></p>
            <p className="mt-1 text-xs text-ink-2">
              {r.who} · {KIND[r.kind]}
              {r.reading ? <> · reads <Fact f={r.reading} /> as of {r.reading.as_of}</> : null}
              {" · "}<Link href={r.href} className="underline decoration-grid underline-offset-2 hover:text-ink">details<span className="sr-only"> of {r.who}&apos;s prediction</span></Link>
            </p>
            {r.judgement ? (
              <p className="mt-2 border-l-2 border-dotted border-axis pl-3 text-[13px] leading-snug text-ink-2">
                <span className="text-muted">A model&apos;s judgement, not a reading: </span>
                <strong className="font-medium text-ink">{leans[r.judgement.lean] ?? r.judgement.lean}.</strong> {r.judgement.reason}{" "}
                <span className="text-muted">
                  {r.judgement.rests_on.length
                    ? <>Rests on {r.judgement.rests_on.map((x, k) => <span key={x.id}>{k ? ", " : ""}<Link href={x.href} className="underline decoration-grid underline-offset-2 hover:text-ink">{x.name}</Link></span>)}.</>
                    : "Rests on the model's general knowledge, not on a reading here."}
                </span>
              </p>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}

function Board() {
  const b = board();
  const label = Object.fromEntries(b.words.map((w) => [w.id, w.label]));
  const leans = Object.fromEntries((b.leans ?? []).map((w) => [w.id, w.label]));
  return (
    <div className="board-filter flex flex-col gap-8">
      <TallyBars b={b} />
      <div role="group" className="-mt-5 flex flex-wrap items-center gap-2" aria-label="Tonight's tally">
        {b.words.map((w) => <span key={w.id} className="inline-flex items-center gap-1.5"><WordChip word={w.id} label={w.label} /><span className="num text-sm text-ink-2">{b.tally[w.id]}</span></span>)}
      </div>
      <details className="text-sm -mt-5">
        <summary className="cursor-pointer text-ink-2">What the words mean</summary>
        <dl className="mt-2 grid gap-x-4 gap-y-1 sm:grid-cols-[12rem_minmax(0,1fr)]">
          {b.words.map((w) => <div key={w.id} className="contents"><dt><WordChip word={w.id} label={w.label} /></dt><dd className="text-ink-2">{w.meaning}</dd></div>)}
        </dl>
        <p className="mt-2 text-ink-2">Each family keeps its own vocabulary on its own page; the board maps it: {b.mapping.map((m) => `${m.kind} ${m.state.replaceAll("_", " ")} → ${b.words.find((w) => w.id === m.word)?.label.toLowerCase()}`).join("; ")}.</p>
      </details>
      <BoardFlow b={b} />
      <SourceMarks b={b} />
      <LeanBars b={b} />
      {b.judged && b.leans ? (
        <details className="text-sm -mt-5">
          <summary className="cursor-pointer text-ink-2">On the forecasts that are too early to tell, how a model leans</summary>
          <div role="group" className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1" aria-label="How the model leans">
            {b.leans.map((w) => <span key={w.id} className="inline-flex items-baseline gap-1.5"><span className="border-l-2 border-dotted border-axis pl-2 text-ink">{w.label}</span><span className="num text-ink-2">{b.judged!.tally[w.id]}</span></span>)}
          </div>
          <dl className="mt-2 grid gap-x-4 gap-y-1 sm:grid-cols-[12rem_minmax(0,1fr)]">
            {b.leans.map((w) => <div key={w.id} className="contents"><dt className="text-ink">{w.label}</dt><dd className="text-ink-2">{w.meaning}</dd></div>)}
          </dl>
          <p className="mt-2 text-ink-2 max-w-[72ch]">Each lean is a model&apos;s judgement, not a reading, and it changes no status word and no tally above. It was made by {b.judged.model} on {b.judged.date}; reviewed by {b.judged.reviewed_by}. {b.judged.method}</p>
          <p className="mt-2 text-ink-2 max-w-[72ch]">A lean is not the confidence number on a forecast&apos;s card below. Confidence says how firm the evidence behind the status is; the lean says whether the model expects the forecast to come true. The model is made by Anthropic, and some of these forecasts are about Anthropic and its rivals.</p>
        </details>
      ) : null}
      <fieldset className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
        <legend className="eyebrow mb-2">Show</legend>
        <label className="inline-flex items-center gap-1.5"><input type="radio" name="board-word" id="bw-all" defaultChecked className="accent-[var(--ink)]" />every forecast</label>
        {b.words.filter((w) => w.id !== "too_early").map((w) => <label key={w.id} className="inline-flex items-center gap-1.5"><input type="radio" name="board-word" id={`bw-${w.id}`} className="accent-[var(--ink)]" />{w.label.toLowerCase()} only</label>)}
      </fieldset>
      {b.folios.map((f) => (
        <section key={f.id} aria-labelledby={`folio-${f.id}`}>
          <h2 id={`folio-${f.id}`} className="display text-2xl leading-tight">{f.label}</h2>
          <p className="text-sm text-muted mb-2">{f.question}</p>
          <Rows rows={f.rows.filter((r) => r.word !== "too_early")} label={label} />
          {f.too_early ? (
            <details className="border-t border-grid">
              <summary className="cursor-pointer py-2 text-sm text-ink-2">
                {f.too_early} more that are too early to tell
                {f.leans && b.leans ? <span className="text-muted"> · a model leans: {b.leans.filter((w) => f.leans![w.id]).map((w) => `${w.label} ${f.leans![w.id]}`).join(", ")}</span> : null}
              </summary>
              <Rows rows={f.rows.filter((r) => r.word === "too_early")} label={label} leans={leans} />
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

const LEDGERS: Record<string, string> = { nk: "Narayanan & Kapoor", lab: "Lab timelines", ai2027: "AI 2027", capture: "Capture theses", singularity: "Timelines to the singularity" };

export default function PredictionsPage() {
  const b = board();
  const rows = predictions();
  const idx = obsIndex();
  const { indicators } = index();
  return (
    <div className="flex flex-col gap-6">
      <PageHeader eyebrow="Who is right so far · every forecast on the site" title="Which forecasts are coming true, and which are not"
        lede={<>{b.n ? <><span className="num">{b.n}</span> forecasts from the labs, named writers and this site, each read against the latest data and given one word. </> : "Every forecast from the labs, named writers and this site, each read against the latest data and given one word. "}Tap &ldquo;details&rdquo; for the test, the reading and the source.</>} />
      <Board />
      <section className="flex flex-col gap-6" aria-labelledby="who-and-when">
        <h2 id="who-and-when" className="display text-[1.75rem] leading-tight mt-4">Who said it, and when it falls due</h2>
        <DueCalendar b={b} />
        <ForecasterMarks b={b} />
      </section>
      <div>
        <h2 className="display text-[1.75rem] leading-tight mt-4">The dated claims in their own words</h2>
        <p className="text-sm text-ink-2 max-w-[60ch]">Other people&apos;s claims with a date attached, quoted from the linked source (the singularity forecasts are in this site&apos;s words, credited and linked) and scored with the AI 2027 tracker&apos;s vocabulary (confirmed, ahead, on track, behind, emerging, not yet testable). A claimant&apos;s self-assessment never resolves a claim.</p>
      </div>
      {Object.entries(LEDGERS).map(([ledger, name]) => {
        const items = rows.filter((p) => p.ledger === ledger && p.published);
        const ours = ledger === "singularity";
        const head = <h3 className="display text-xl leading-tight mb-3 mt-2 inline">{name} <span className="text-muted">· {items.length}</span></h3>;
        const body = (
          <>
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
                    {ours ? (
                      <p className="mt-2 border-l-2 border-grid pl-3 text-base leading-[1.6]">{p.claim_text} <span className="text-xs text-muted">In this site&apos;s words.</span> {p.claim_url ? <a href={p.claim_url} className="text-xs text-ink-2 underline decoration-grid underline-offset-4">source</a> : null}</p>
                    ) : (
                      <blockquote className="mt-2 border-l-2 border-grid pl-3 text-base leading-[1.6]">&ldquo;{p.claim_text}&rdquo; {p.claim_url ? <a href={p.claim_url} className="text-xs text-ink-2 underline decoration-grid underline-offset-4">source</a> : null}</blockquote>
                    )}
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
          </>
        );
        return ours ? (
          <details key={ledger} id="singularity-ledger" className="group">
            <summary className="cursor-pointer">{head} <span className="text-sm text-ink-2">— open to read them all</span></summary>
            <p className="mt-2 text-sm text-ink-2">Every one is placed on <Link href="/singularity" className="underline decoration-grid underline-offset-4">the singularity timeline</Link>.</p>
            <div className="mt-3">{body}</div>
          </details>
        ) : (
          <section key={ledger}>{head}{body}</section>
        );
      })}
    </div>
  );
}
