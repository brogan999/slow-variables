import Link from "next/link";
import { Fact } from "@/components/Fact";
import { MarginPanel } from "@/components/ArticleLayout";
import { StackChart } from "@/components/StackChart";
import { StatusChip } from "@/components/StatusChip";
import type { ArgumentDoc, Card } from "@/lib/data";
import { capture } from "@/lib/data";
import { PHASE_WORDS, STATE_WORDS } from "@/lib/format";


export function StackPlate() {
  return (
    <StackChart stack={capture().gross_profit_stack} title="Who keeps the gross profit, quarter by quarter" what="gross profit"
      unmeasured="Apps publish no gross profit we can use, so they are left out rather than guessed."
      caption="Each column is one quarter's gross profit across the parts we can measure: NVIDIA and AMD at the bottom, Microsoft's cloud business above them, and an estimate for OpenAI and Anthropic, hatched, at the top." />
  );
}

export function SlowVariables({ doc, cards }: { doc: ArgumentDoc; cards: Record<string, Card> }) {
  return (
    <ol className="flex flex-col">
      {doc.slow_variables.map((v, i) => {
        const c = cards[v.id];
        const l = c?.latest;
        return (
          <li key={v.id} className="grid gap-x-8 gap-y-2 py-6 border-t border-grid md:grid-cols-[minmax(0,15rem)_minmax(0,1fr)]">
            <div className="flex flex-col gap-2">
              <span className="eyebrow">{String(i + 1).padStart(2, "0")}</span>
              <Link href={`/indicators/${v.id}`} className="display text-[1.5rem] leading-tight hover:underline underline-offset-4 decoration-axis">{v.label}</Link>
              <span className="text-[1.75rem] leading-none">{l && l.value !== null ? <Fact f={{ value: l.value, unit: l.unit ?? c.unit, as_of: l.as_of, obs_ids: l.obs_ids, href: `/indicators/${v.id}`, holds: null }} /> : <span className="text-muted text-base">no reading yet</span>}</span>
              {l ? <span className="text-xs text-muted">as of {l.as_of}</span> : null}
            </div>
            <div className="flex flex-col gap-3 md:pt-7">
              <p className="font-serif text-[1.0625rem] leading-relaxed text-ink">{v.sentence}</p>
              <div><StatusChip status={c?.status} /></div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

export function Exits({ doc }: { doc: ArgumentDoc }) {
  return (
    <ul className="flex flex-col">
      {doc.exits.map((e) => (
        <li key={e.monitor} className="py-5 border-t border-grid grid gap-2 md:grid-cols-[minmax(0,1fr)_12rem] md:gap-8">
          <p className="font-serif text-[1.0625rem] leading-relaxed">{e.text}</p>
          <div className="flex flex-col gap-1 md:text-right">
            <span className="eyebrow">{e.label}</span>
            <span className="text-sm text-ink">{STATE_WORDS[e.state ?? "untestable"] ?? e.state}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}

export function ReadingMargin({ doc }: { doc: ArgumentDoc }) {
  return (
    <>
      <MarginPanel title={`Reading · ${doc.as_of ?? "—"}`} rows={[["Which half, after Perez", PHASE_WORDS[doc.phase.state]], ["How fast", doc.headlines.diffusion.claim], ["Who profits", doc.headlines.capture.claim]]} />
      <MarginPanel title="Instrument">
        <p>Every figure links to the dated, graded records behind it, and is scored against a range published in advance.</p>
        <p>A reading on the edge of a range, or one whose uncertainty spans two, is held rather than scored. Four readings of one survey count once.</p>
        <p><Link href="/methodology" className="text-ink underline decoration-axis underline-offset-2">How to read this →</Link></p>
      </MarginPanel>
    </>
  );
}
