import Link from "next/link";
import { ChangelogList } from "@/components/Changelog";
import { IndicatorCard } from "@/components/IndicatorCard";
import { StackVertical } from "@/components/StackVertical";
import { StatusChip } from "@/components/StatusChip";
import { capture, obsIndex } from "@/lib/data";

export default function CaptureLens() {
  const c = capture();
  const idx = obsIndex();
  return (
    <div className="flex flex-col gap-8">
      <section>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="text-2xl font-semibold tracking-tight">Capture lens</h1>
          <Link href="/" className="text-sm text-ink-2 hover:text-ink">← Switch to diffusion lens</Link>
        </div>
        <p className="mt-2 max-w-3xl text-lg leading-snug">Who keeps the surplus, layer by layer. The compute layer's bar is sized by its filed segment operating income; the other layers get bars as their series land.</p>
      </section>
      <StackVertical layers={c.layers} shares={c.margin_shares} obsIndex={idx} />
      <ol className="flex flex-col gap-3">
        {c.layers.map((l) => {
          const published = l.indicators.filter((i) => i.published);
          const statuses = published.map((i) => i.status).filter(Boolean) as string[];
          const summary = statuses.length ? statuses.sort((a, b) => statuses.filter((s) => s === b).length - statuses.filter((s) => s === a).length)[0] : null;
          return (
            <li key={l.id} className="rounded-lg bg-surface ring-hair p-4">
              <div className="flex flex-wrap items-center gap-3">
                <Link href={`/layers/${l.id}`} className="font-medium hover:underline">{l.order}. {l.name}</Link>
                <StatusChip status={summary} />
                {published.length ? <span className="text-xs text-muted">{published.length} indicator{published.length === 1 ? "" : "s"}</span> : null}
                {l.id === "training_input" ? <Link href="/buckets/return_arrow" className="text-xs text-ink-2 hover:text-ink ml-auto">⇄ return arrow</Link> : null}
              </div>
              <p className="text-sm text-ink-2 mt-1">{l.description}</p>
              {published.length ? <div className="mt-3 grid gap-3 md:grid-cols-2">{published.map((i) => <IndicatorCard key={i.id} c={i} obsIndex={idx} />)}</div> : null}
            </li>
          );
        })}
      </ol>
      <section>
        <h2 className="text-sm font-medium text-ink-2 mb-2">Last three status changes</h2>
        <ChangelogList events={c.recent_status_events} obsIndex={idx} />
      </section>
    </div>
  );
}
