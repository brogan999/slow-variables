"use client";

import { useState } from "react";

type Found = "" | "shown" | "elsewhere" | "none";

// Search a company to show only the cards it sits in; or show only the categories the tracker has not mapped.
// The page stays complete without this: it only toggles attributes on the server-rendered cards.
function apply(q: string, gaps: boolean): Found {
  const root = document.getElementById("market-map");
  if (!root) return "";
  const needle = q.trim().toLowerCase();
  let shown = false;
  let anywhere = false;
  root.querySelectorAll<HTMLElement>(".mm-card").forEach((card) => {
    const match = !needle || (card.dataset.names ?? "").split("|").some((x) => x.includes(needle));
    card.hidden = (gaps && card.dataset.state !== "unmapped") || (!!needle && !match);
    if (needle && match) {
      anywhere = true;
      if (!card.hidden) shown = true;
    }
    let chipHit = false;
    card.querySelectorAll<HTMLElement>(".mm-chip, .mm-row").forEach((el) => {
      const hit = !!needle && (el.dataset.name ?? "").includes(needle);
      el.dataset.hit = hit ? "1" : "0";
      if (hit && el.classList.contains("mm-chip")) chipHit = true;
    });
    // a match past the card's chips is in its list: open it so the highlighted row shows
    const details = card.querySelector("details");
    if (details && needle && match && !chipHit) details.open = true;
  });
  root.querySelectorAll<HTMLElement>(".mm-layer").forEach((layer) => {
    const cards = [...layer.querySelectorAll<HTMLElement>(".mm-card")];
    layer.hidden = cards.length ? cards.every((c) => c.hidden) : gaps || !!needle;
  });
  return !needle ? "" : shown ? "shown" : anywhere ? "elsewhere" : "none";
}

const SAY: Record<Found, string> = { "": "", shown: "showing the categories it sits in", elsewhere: "not among the categories shown", none: "not on the map" };

export function MarketMapFilter() {
  const [q, setQ] = useState("");
  const [gaps, setGaps] = useState(false);
  const [found, setFound] = useState<Found>("");

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-y border-grid py-2">
      <label className="flex items-center gap-2 text-sm text-ink-2">
        <span>Find a company</span>
        <input id="mm-search" type="search" value={q} placeholder="e.g. Harvey"
          onChange={(e) => { setQ(e.target.value); setFound(apply(e.target.value, gaps)); }}
          className="w-[14rem] max-w-full rounded-[2px] bg-surface px-2 py-1 text-sm text-ink ring-1 ring-grid focus:outline-none focus:ring-ink" />
      </label>
      <label className="flex items-center gap-2 text-sm text-ink-2">
        <input id="mm-gaps" type="checkbox" checked={gaps} onChange={(e) => { setGaps(e.target.checked); setFound(apply(q, e.target.checked)); }} />
        <span>Only categories not yet mapped</span>
      </label>
      <span className="font-mono text-[12px] text-muted" aria-live="polite">{SAY[found]}</span>
    </div>
  );
}
