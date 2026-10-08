"use client";

import Link from "next/link";
import { useSyncExternalStore } from "react";
import type { AtlasTile, AtlasTime, ChainAtlasDoc } from "@/lib/data";

// tonight's reading takes the site's tightness ramp; a model's judgement is ink with a dashed edge (a judged placing)
const MEASURED = ["", "ca-m1", "ca-m2", "ca-m3", "ca-m4", "ca-m5"];
const JUDGED = ["", "ca-j1", "ca-j2", "ca-j3", "ca-j4", "ca-j5"];
const LEVELS = [1, 2, 3, 4, 5];

const chosen = (name: string, fallback: string) => document.querySelector<HTMLInputElement>(`input[name="${name}"]:checked`)?.value ?? fallback;
const subscribe = (notify: () => void) => { document.addEventListener("change", notify); return () => document.removeEventListener("change", notify); };

// The chain, drawn once. The page's radios choose a future and a time; this looks up each part's state for that pair in
// the export and re-inks the tiles. It is the page's one island: without script the map shows tonight, no future chosen.
export function ChainAtlasMap({ layers }: { layers: ChainAtlasDoc["map"]["layers"] }) {
  const picked = useSyncExternalStore(subscribe, () => `${chosen("ca-future", "none")}|${chosen("ca-time", "now")}`, () => "none|now");
  const [future, time] = picked.split("|") as [string, AtlasTime];
  const Tile = ({ c }: { c: AtlasTile }) => {
    const s = (c.states[future] ?? c.states.none)[time];
    return (
      <Link href={c.href} title={`${s.label}. Scarce here: ${c.scarce}`} aria-label={s.label} className={`ca-tile ${(s.measured ? MEASURED : JUDGED)[s.level]}`}>
        <span className="font-mono text-[10px] opacity-80">{c.number}</span>
        <span className="hidden text-[11px] font-semibold leading-tight lg:block">{c.name}</span>
        <span className="hidden font-mono text-[10px] leading-tight sm:block">{s.word}</span>
        {c.businesses.length ? <span className="mt-auto font-mono text-[10.5px] font-semibold">{c.businesses.join(" ")}</span> : null}
      </Link>
    );
  };
  return (
    <figure className="fig p-3">
      <div className="grid grid-cols-7 gap-1.5">
        {layers.map((layer) => (
          <div key={layer.number} className="flex min-w-0 flex-col gap-1">
            <h3 className="min-h-[3.4em] text-[9.5px] font-semibold uppercase leading-tight tracking-[0.06em] text-muted"><span className="font-mono">{layer.number}</span> <span className="hidden sm:inline">{layer.name}</span></h3>
            {layer.categories.map((c) => <Tile key={c.id} c={c} />)}
          </div>
        ))}
      </div>
      <figcaption className="mt-3 flex flex-wrap gap-x-5 gap-y-1 border-t border-grid pt-2 font-mono text-[10.5px] text-ink-2">
        <span><span className="mr-1 inline-flex gap-px align-[-1px]">{LEVELS.map((l) => <i key={l} className={`inline-block h-2.5 w-3.5 ${MEASURED[l]}`} />)}</span>measured tonight: slack to severe</span>
        <span><span className="mr-1 inline-flex gap-px align-[-1px]">{LEVELS.map((l) => <i key={l} className={`inline-block h-2.5 w-3.5 ${JUDGED[l]}`} />)}</span>a model&apos;s judgement: probably slack to probably severe</span>
        <span>numbers: the businesses that sit there</span>
      </figcaption>
    </figure>
  );
}
