"use client";

import { useState } from "react";

// "As of" a year: dims the forecasts made after it and shows the counts export wrote for that stop. It compares a
// mark's precomputed year with the stop and counts nothing itself.
export function Scrubber({ stops, tallies, words, order }: { stops: number[]; tallies: Record<string, Record<string, number>>; words: Record<string, string>; order: string[] }) {
  const [i, setI] = useState(stops.length - 1);
  const stop = stops[i];
  const move = (n: number) => {
    setI(n);
    document.querySelectorAll<HTMLElement>(".sg-mark[data-made]").forEach((el) => {
      if (Number(el.dataset.made) > stops[n]) el.setAttribute("data-later", "");
      else el.removeAttribute("data-later");
    });
  };
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor="sg-asof" className="font-mono text-[11px] uppercase tracking-[0.14em] text-ink-2">Forecasts made by <span className="text-ink">{i === stops.length - 1 ? "today" : stop}</span></label>
      <input id="sg-asof" type="range" min={0} max={stops.length - 1} step={1} value={i} onChange={(e) => move(Number(e.target.value))}
        aria-valuetext={i === stops.length - 1 ? "today" : String(stop)} className="w-full accent-[var(--ink)]" />
      <dl className="grid grid-cols-[1fr_auto] gap-x-3 gap-y-1 text-sm" aria-live="polite">
        {order.map((w) => <div key={w} className="contents"><dt className="text-ink-2">{words[w]}</dt><dd className="num text-ink">{tallies[String(stop)]?.[w] ?? 0}</dd></div>)}
      </dl>
    </div>
  );
}
