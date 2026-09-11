import Link from "next/link";
import type { ChartSourcesT } from "@/lib/data";

// P1 §9: a line under every chart naming its sources, the metric when the points are derived, and any credit a
// source asks for (Epoch's CC BY). Written by the export; the page only lists it.
export function ChartSources({ cs }: { cs?: ChartSourcesT | null }) {
  if (!cs?.sources.length) return null;
  const credits = cs.sources.filter((s) => s.attribution);
  return (
    <p className="mt-2 text-xs text-muted">
      {cs.metric ? <>Derived (<span className="font-mono">{cs.metric}</span>) from: </> : "Source: "}
      {cs.sources.map((s, i) => (
        <span key={s.id}>{i ? "; " : ""}<Link href={`/sources#${s.id}`} className="underline decoration-grid underline-offset-2 hover:text-ink">{s.name}</Link></span>
      ))}
      .{credits.map((s) => <span key={s.id}> {s.attribution}</span>)}
    </p>
  );
}
