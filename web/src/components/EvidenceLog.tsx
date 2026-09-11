import type { Evidence } from "@/lib/data";
import { Grade } from "./StatusChip";

const STANCE: Record<string, string> = { for: "supports", against: "cuts against", context: "context" };

// Dated evidence records: each is an observation with a fetched URL and a verbatim snippet; the stance is part of its series key.
export function EvidenceLog({ items }: { items: Evidence[] }) {
  if (!items.length) return null;
  return (
    <ol className="flex flex-col gap-2 text-sm">
      {items.map((e) => (
        <li key={e.id} id={e.id} className="panel p-3">
          <div className="flex flex-wrap items-center gap-2 text-xs text-ink-2">
            <span className="tabular-nums text-muted">{e.as_of}</span>
            <span className={e.stance === "against" ? "text-slow" : e.stance === "for" ? "text-ink" : "text-muted"}>{STANCE[e.stance] ?? e.stance}</span>
            <Grade grade={e.tier >= 7 ? "D" : e.tier <= 1 ? "A" : e.tier <= 4 ? "B" : "C"} tier={e.tier} />
            <a href={e.url} className="underline decoration-grid underline-offset-4">source</a>
          </div>
          <p className="mt-1">{e.summary}</p>
          <p className="mt-1 text-xs text-muted">&ldquo;{e.snippet}&rdquo;</p>
        </li>
      ))}
    </ol>
  );
}
