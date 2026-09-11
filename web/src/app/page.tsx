import Link from "next/link";
import { ChangelogList } from "@/components/Changelog";
import { Section } from "@/components/Section";
import { StackVertical } from "@/components/StackVertical";
import { StatusChip } from "@/components/StatusChip";
import { StockFlowDiagram } from "@/components/StockFlowDiagram";
import { ThesisMonitor } from "@/components/ThesisMonitor";
import { NumberTicker } from "@/components/ui/number-ticker";
import { capture, diffusion, index, memos, meta, obsIndex, sources, thesis } from "@/lib/data";
import { SITE } from "@/lib/site";

export const metadata = { title: { absolute: `${SITE.name} · how fast AI lands, and who keeps the value` } };

export default function Home() {
  const d = diffusion();
  const c = capture();
  const idx = obsIndex();
  const verdicts = thesis();
  const latest = memos()[0];
  const published = index().indicators.filter((i) => i.published).length;
  const observations = Object.keys(idx).length;
  const nSources = sources().length;
  const generated = meta().generated_at.slice(0, 10);
  const figures: [number, string, string][] = [[published, "indicators published", "/indicators"], [observations, "dated observations", "/query"], [nSources, "sources", "/sources"]];
  return (
    <div className="flex flex-col gap-14 md:gap-20">
      <section className="relative py-10 md:py-16">
        <div aria-hidden className="dots absolute -inset-x-4 -top-6 bottom-0 -z-10 opacity-70" />
        <div className="eyebrow">A public tracker · generated {generated}</div>
        <h1 className="display text-[3.5rem] md:text-[5rem] leading-[0.95] tracking-[-0.02em] mt-3">{SITE.name}</h1>
        <p className="mt-5 text-lg md:text-xl leading-snug text-ink-2 max-w-[60ch]">{SITE.description}</p>
        <div className="mt-10 grid gap-8 md:grid-cols-2">
          <Verdict eyebrow="Diffusion lens" href="/diffusion" sentence={d.verdict} chips={d.buckets.map((b) => [b.name, b.status, `/buckets/${b.id}`])} />
          <Verdict eyebrow="Capture lens" href="/capture" sentence={c.verdict ?? ""} chips={c.layers.map((l) => [l.name, l.status, `/layers/${l.id}`])} />
        </div>
        <ul className="mt-10 flex flex-wrap gap-x-10 gap-y-4">
          {figures.map(([n, label, href]) => (
            <li key={label}>
              <Link href={href} className="group block">
                <span className="num block text-[2.5rem] md:text-[3.5rem] leading-none tracking-[-0.03em]"><NumberTicker value={n} /></span>
                <span className="eyebrow mt-1 block group-hover:text-ink">{label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <Section n={1} title="How fast it moves" action={<Link href="/diffusion" className="hover:text-ink">Diffusion lens →</Link>}>
        <p className="text-ink-2 max-w-[60ch] mb-6">Five stocks from <em>AI as Normal Technology</em>, with a valve between each. A valve carries a status only when a published indicator measures it; everything else reads unmeasured, not a guess.</p>
        <StockFlowDiagram buckets={d.buckets} valves={d.valves} />
      </Section>

      <Section n={2} title="Who keeps it" action={<Link href="/capture" className="hover:text-ink">Capture lens →</Link>}>
        <p className="text-ink-2 max-w-[60ch] mb-6">Seven layers of the stack. Bars are each layer&apos;s share of the stack&apos;s gross profit, with the lab layer estimated and hatched; a layer without a series shows a hairline, and its indicators carry the reading.</p>
        <StackVertical layers={c.layers} bars={c.stack_bars} />
      </Section>

      <Section n={3} title="This week" action={<Link href="/memos" className="hover:text-ink">All memos →</Link>}>
        <div className="grid gap-6 md:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
          {latest ? (
            <article className="panel p-5 flex flex-col gap-3">
              <div className="eyebrow">{latest.since} → {latest.date} · {latest.mode === "prose" ? `drafted by ${latest.model}` : "deterministic digest"}</div>
              <h3 className="display text-2xl md:text-[1.75rem] leading-tight"><Link href={`/memos/${latest.date}`} className="hover:underline underline-offset-4 decoration-grid">{latest.title}</Link></h3>
              <div className="flex gap-8">
                <div><span className="num block text-2xl">{latest.events}</span><span className="eyebrow">status events</span></div>
                <div><span className="num block text-2xl">{latest.new_observations.toLocaleString("en-US")}</span><span className="eyebrow">new observations</span></div>
              </div>
              <p className="text-ink-2">{(latest.summary ?? "").slice(0, 280)}{(latest.summary ?? "").length > 280 ? "…" : ""}</p>
              <Link href={`/memos/${latest.date}`} className="text-sm text-ink-2 hover:text-ink">Read the memo →</Link>
            </article>
          ) : <p className="text-muted">No memo yet; the first runs on Monday 09:17 UTC.</p>}
          <div>
            <div className="eyebrow mb-3">Last three status changes</div>
            <ChangelogList events={d.recent_status_events} obsIndex={idx} />
          </div>
        </div>
      </Section>

      <Section n={4} title="Thesis monitor" action={<span className="text-muted">the falsification rules, evaluated nightly</span>}>
        <ThesisMonitor verdicts={verdicts} obsIndex={idx} />
        <details className="mt-6 group">
          <summary className="cursor-pointer display text-xl">What would change our mind <span className="text-muted text-sm font-sans">({d.what_would_change.length} diffusion · {c.what_would_change.length} capture rules)</span></summary>
          <div className="mt-3 grid gap-6 md:grid-cols-2">
            {([["Diffusion", d.what_would_change], ["Capture", c.what_would_change]] as const).map(([k, rules]) => (
              <div key={k}>
                <div className="eyebrow mb-2">{k}</div>
                <ul className="text-sm text-ink-2 flex flex-col gap-1.5 list-disc pl-5">{rules.map((w) => <li key={w}>{w}</li>)}</ul>
              </div>
            ))}
          </div>
        </details>
      </Section>
    </div>
  );
}

const cap = (t: string) => t.charAt(0).toUpperCase() + t.slice(1);

function Verdict({ eyebrow, href, sentence, chips }: { eyebrow: string; href: string; sentence: string; chips: [string, string | null, string][] }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="eyebrow"><Link href={href} className="hover:text-ink">{eyebrow} →</Link></div>
      <p className="display italic text-[1.375rem] md:text-[1.625rem] leading-snug">{cap(sentence.replace(/^As of \d{4}-\d{2}-\d{2}: /, ""))}</p>
      <ul className="flex flex-wrap gap-x-4 gap-y-2 text-sm">
        {chips.map(([name, status, to]) => (
          <li key={name} className="flex items-center gap-1.5"><Link href={to} className="text-ink-2 hover:text-ink">{name}</Link><StatusChip status={status} /></li>
        ))}
      </ul>
    </div>
  );
}
