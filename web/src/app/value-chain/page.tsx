import Link from "next/link";
import { PowersGlossary } from "@/components/ValueChain";
import { valueChain } from "@/lib/data";

export const metadata = {
  title: "The value chain",
  description: "How the economics of each layer of the AI stack are moving: what is getting cheap and interchangeable, what stays scarce, and the companies that matter in each.",
};

export default function ValueChainPage() {
  const v = valueChain();
  const named = new Map(v.companies.map((c) => [c.entity, c.name]));
  return (
    <div className="flex flex-col gap-8 max-w-[72rem]">
      <div className="flex flex-col gap-3">
        <h1 className="display text-[2.5rem] md:text-[3.5rem] leading-[1.02]">The value chain</h1>
        <p className="text-ink-2 leading-relaxed max-w-[68ch]">
          Every part of building and using AI, from power and chips to the apps people use, earns money differently. This page is the site&apos;s judgement of where each part&apos;s economics are heading: which parts are becoming cheap and interchangeable (commoditising, so the gain passes to buyers), which stay scarce and keep a profit, and what would make a passing advantage last. Each judgement names the view that argues against it and what would prove it wrong. The readings behind them are on each layer&apos;s page.
        </p>
        <PowersGlossary powers={v.powers} />
      </div>
      <ol className="flex flex-col border-t border-grid">
        <li className="hidden md:grid grid-cols-[2fr_0.8fr_2fr_1.6fr] gap-4 py-2 text-sm text-muted border-b border-grid" aria-hidden>
          <span>Part of the chain</span><span>Direction</span><span>Binds on</span><span>Companies profiled</span>
        </li>
        {v.units.map((u) => (
          <li key={u.id} className="grid gap-1 md:gap-4 md:grid-cols-[2fr_0.8fr_2fr_1.6fr] py-3 border-b border-grid text-sm">
            <Link href={`/layers/${u.layer}#assessment-${u.id}`} className="text-ink underline decoration-grid underline-offset-4 hover:decoration-ink">{u.title}</Link>
            <span className="text-ink-2"><span className="md:hidden text-muted">Direction: </span>{u.direction}</span>
            <span className="text-ink-2"><span className="md:hidden text-muted">Binds on: </span>{u.binding.map((b) => `${b.name} (${b.word ?? "no reading"})`).join(", ") || "—"}</span>
            <span className="text-ink-2"><span className="md:hidden text-muted">Companies: </span>{v.companies.filter((c) => c.units.includes(u.id)).map((c) => named.get(c.entity)).join(", ") || "—"}</span>
          </li>
        ))}
      </ol>
      <p className="text-xs text-muted max-w-[68ch]">The judgements and profiles were drafted by a model from the companies&apos; own filings and the site&apos;s readings, and each says whether a person has reviewed it. They are conditions, not forecasts: no company is ranked.</p>
    </div>
  );
}
