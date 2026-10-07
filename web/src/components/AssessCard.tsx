import Link from "next/link";

export type AssessFuture = { progress: string; rules: string; effect: "stronger" | "weaker" | "breaks" | "unchanged"; why: string };
export type Assess = { kind: "idea" | "company"; name: string; call: string; level: "yes" | "cond" | "no"; take: string; wrong_if: string; sits: { label: string; href: string } | null; futures: AssessFuture[] };

const KIND = { idea: "A business idea, reasoned through", company: "A company on the field, reasoned through" };
const CALL = { yes: "bg-ink text-background", cond: "border border-ink text-ink", no: "border border-dashed border-muted text-ink-2" };
// a judged placing: solid, or a dashed outline; never a hatch
const MARK = { stronger: "bg-ink", weaker: "border-[1.5px] border-dashed border-ink-2", breaks: "bg-surface-2 line-through decoration-ink", unchanged: "bg-surface-2" };
const WORD = { stronger: "stronger", weaker: "weaker", breaks: "breaks", unchanged: "unchanged" };

// The card Ask returns beside a reasoned idea or company. The service validates it and lays out one mark per future
// on the outlook's grid; this only draws it.
export function AssessCard({ card }: { card: Assess }) {
  const moved = card.futures.filter((f) => f.effect !== "unchanged");
  return (
    <section className="fig flex flex-col gap-3 p-4" aria-label={`${KIND[card.kind]}: ${card.name}`}>
      <span className="eyebrow">{KIND[card.kind]}</span>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <h3 className="text-lg font-semibold leading-tight">{card.name}</h3>
        <span className={`rounded-[2px] px-2 py-0.5 font-mono text-[11px] uppercase tracking-[0.06em] ${CALL[card.level]}`}>{card.call}</span>
      </div>
      <p className="leading-relaxed text-ink-2 max-w-[60ch]">{card.take}</p>
      <div className="flex flex-col gap-1.5">
        <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">In each future on the outlook&apos;s grid</span>
        <ol className="flex flex-wrap gap-[3px]" aria-label="The business in each future">
          {card.futures.map((f) => (
            <li key={`${f.progress}|${f.rules}`} title={`${f.progress}, ${f.rules.toLowerCase()}: ${WORD[f.effect]}`} className={`h-7 w-5 rounded-[1px] text-center font-mono text-[12px] leading-7 ${MARK[f.effect]}`}>
              <span className="sr-only">{f.progress}, {f.rules.toLowerCase()}: {WORD[f.effect]}</span>
              {f.effect === "breaks" ? <span aria-hidden>×</span> : null}
            </li>
          ))}
        </ol>
        <p className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-[10.5px] text-muted">
          <span><i className={`mr-1 inline-block h-2.5 w-2.5 align-[-1px] ${MARK.stronger}`} />stronger</span>
          <span><i className={`mr-1 inline-block h-2.5 w-2.5 align-[-1px] ${MARK.weaker}`} />weaker</span>
          <span><i className="mr-1 inline-block w-2.5 text-center not-italic">×</i>breaks</span>
          <span><i className={`mr-1 inline-block h-2.5 w-2.5 align-[-1px] ${MARK.unchanged}`} />unchanged</span>
          <span>a model&apos;s judgement of each</span>
        </p>
      </div>
      {moved.length ? (
        <details className="text-sm">
          <summary className="cursor-pointer font-mono text-[11px] text-ink-2">Future by future</summary>
          <ul className="mt-2 flex flex-col gap-1.5">
            {moved.map((f) => (
              <li key={`${f.progress}|${f.rules}`} className="leading-snug"><span className="font-medium">{f.progress}, {f.rules.toLowerCase()}:</span> {WORD[f.effect]}. <span className="text-ink-2">{f.why}</span></li>
            ))}
          </ul>
        </details>
      ) : null}
      <dl className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
        {card.sits ? <div><dt className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">Where it sits</dt><dd><Link href={card.sits.href} className="underline decoration-grid underline-offset-2 hover:decoration-ink">{card.sits.label}</Link></dd></div> : null}
        <div><dt className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">What would prove the call wrong</dt><dd className="text-ink-2">{card.wrong_if}</dd></div>
      </dl>
      <p className="border-l-2 border-dotted border-axis pl-2 text-xs text-muted">A model&apos;s judgement, not a reading: drafted by Claude, a model made by Anthropic, from the site&apos;s records and reviewed by no one. The reasoning and its sources are below.</p>
    </section>
  );
}
