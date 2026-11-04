"use client";

import { useSyncExternalStore } from "react";
import type { FuTree } from "@/lib/data";
import { fmt } from "@/lib/format";

const subscribe = (notify: () => void) => { document.addEventListener("change", notify); return () => document.removeEventListener("change", notify); };

// The page's one island. It reads which gates are ticked, looks that set up in the export's tallies and prints the
// line; the export did the counting for every set.
export function FuturesTreeTally({ gates, tallies, nodes, sellers }: { gates: string[]; tallies: FuTree["tallies"]; nodes: number; sellers: FuTree["sellers"] }) {
  const none = gates.map(() => "0").join("");
  const key = useSyncExternalStore(subscribe, () => gates.map((g) => (document.getElementById(`ft-g-${g}`) as HTMLInputElement | null)?.checked ? "1" : "0").join(""), () => none);
  const t = tallies[key] ?? tallies[none];
  return (
    <p aria-live="polite" className="font-serif text-[1.15rem] leading-snug text-ink max-w-[62ch]">
      {fmt(t.lit, "count")} of {fmt(nodes, "count")} nodes are lit, holding {fmt(t.n, "count")} large or vast prizes.{" "}
      <span className="mt-1 block font-sans text-[13px] leading-relaxed text-ink-2">
        {sellers.map((s, i) => <span key={s.id}>{i ? "; " : ""}in <span className="font-mono font-medium text-ink">{fmt(t[s.id], "count")}</span>, {s.word}</span>)}, as a model judges it.
      </span>
    </p>
  );
}
