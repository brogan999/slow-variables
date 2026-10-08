"use client";

import Link from "next/link";
import { useSyncExternalStore } from "react";
import { TONE } from "@/components/diagrams/migration";
import type { AtlasState, AtlasTime } from "@/lib/data";

export type MapTile = { id: string; number: string; name: string; scarce: string; businesses: number[]; states: Record<string, Record<AtlasTime, AtlasState>>; moves: Record<string, string> };
export type MapLayer = { number: number; name: string; tiles: MapTile[] };
type Named = { key: string; name: string };

// the scale's words in order, so a level looks up its word; the scorecard's own colours for a reading, ink for a judgement
const WORDS = ["", "slack", "easing", "moderate", "tight", "severe"];
const INK = ["", "color-mix(in srgb, var(--ink) 6%, var(--surface))", "color-mix(in srgb, var(--ink) 16%, var(--surface))", "color-mix(in srgb, var(--ink) 34%, var(--surface))", "color-mix(in srgb, var(--ink) 62%, var(--surface))", "var(--ink)"];
const LEVELS = [1, 2, 3, 4, 5];

const chosen = (name: string, fallback: string) => document.querySelector<HTMLInputElement>(`input[name="${name}"]:checked`)?.value ?? fallback;
const subscribe = (notify: () => void) => { document.addEventListener("change", notify); return () => document.removeEventListener("change", notify); };

// The band carries the state and the words sit on the page's own surface, so they stay readable at every level.
function Band({ s, className }: { s: Pick<AtlasState, "level" | "measured" | "hatched">; className: string }) {
  if (!s.measured) return <span aria-hidden className={className} style={{ background: INK[s.level] }} />;
  return <span aria-hidden className={`${className} ${s.hatched ? "hatch" : ""}`} style={s.hatched ? { color: TONE[WORDS[s.level]] } : { background: TONE[WORDS[s.level]] }} />;
}

function Tile({ c, future, time }: { c: MapTile; future: string; time: AtlasTime }) {
  const s = (c.states[future] ?? c.states.none)[time];
  const move = c.moves[future];
  return (
    <Link href={`#ca-g-${c.id}`} title={`Scarce here: ${c.scarce}${s.gauge ? `. Tonight’s reading of ${s.gauge}` : ""}`} className={`ca-tile ${s.measured ? "" : "ca-judged"}`}>
      <Band s={s} className="ca-band" />
      <span className="font-mono text-[10px] text-ink-2">{c.number}</span>
      <span className="block text-[11px] font-semibold leading-tight sm:hidden lg:block">{c.name}</span>
      <span className="font-mono text-[10px] leading-tight">{s.word}{s.gauge ? <span className="sr-only">, tonight’s reading of {s.gauge}{s.hatched ? ", a low-confidence score" : ""}</span> : null}</span>
      {move ? <span className="font-mono text-[10px] font-semibold leading-tight">{move} in this future</span> : null}
      {c.businesses.length ? <span className="mt-auto font-mono text-[10.5px] font-semibold"><span className="sr-only">businesses </span>{c.businesses.join(" ")}</span> : null}
    </Link>
  );
}

// The chain, drawn once. The page's radios choose a future and a time; this looks up each part's state for that pair in
// the export and re-inks the tiles. It is the page's one island: without script the map shows tonight, no future chosen.
export function ChainAtlasMap({ layers, futures, times }: { layers: MapLayer[]; futures: Named[]; times: Named[] }) {
  const picked = useSyncExternalStore(subscribe, () => `${chosen("ca-future", "none")}|${chosen("ca-time", "now")}`, () => "none|now");
  const [future, time] = picked.split("|") as [string, AtlasTime];
  const f = futures.find((x) => x.key === future), t = times.find((x) => x.key === time);
  return (
    <figure className="fig p-3">
      <p aria-live="polite" className="sr-only">The map shows {t?.name ?? "now"}, {f ? `assuming ${f.name}` : "with no future chosen"}.</p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-7 sm:gap-1.5">
        {layers.map((layer) => (
          <div key={layer.number} className="flex min-w-0 flex-col gap-1">
            <h3 className="text-[9.5px] font-semibold uppercase leading-tight tracking-[0.06em] text-muted sm:min-h-[3.4em]"><span className="font-mono">{layer.number}</span> {layer.name}</h3>
            <div className="grid grid-cols-2 gap-1 sm:flex sm:flex-col">{layer.tiles.map((c) => <Tile key={c.id} c={c} future={future} time={time} />)}</div>
          </div>
        ))}
      </div>
      <figcaption className="mt-3 flex flex-wrap gap-x-5 gap-y-1 border-t border-grid pt-2 font-mono text-[10.5px] text-ink-2">
        <span><span className="mr-1 inline-flex gap-px align-[-1px]">{LEVELS.map((l) => <Band key={l} s={{ level: l, measured: true, hatched: false }} className="inline-block h-2.5 w-3.5" />)}</span>measured tonight: slack to severe</span>
        <span><Band s={{ level: 5, measured: true, hatched: true }} className="mr-1 inline-block h-2.5 w-3.5 align-[-1px]" />hatched: a low-confidence score</span>
        <span><span className="mr-1 inline-flex gap-px align-[-1px]">{LEVELS.map((l) => <Band key={l} s={{ level: l, measured: false, hatched: false }} className="inline-block h-2.5 w-3.5" />)}</span>dashed edge: a model&apos;s judgement, probably slack to probably severe</span>
        <span>numbers: the businesses that sit there</span>
      </figcaption>
    </figure>
  );
}
