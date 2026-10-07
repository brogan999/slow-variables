import type { DirectedReading, RangedReading } from "@/lib/data";
import { STATE_WORDS } from "@/lib/format";

// Parts for the figures on /argument. Every place (a zone's start and width, a mark's x) arrives from the export as a
// percentage of its strip, so nothing here works out a number.

// Why a number that falls inside a range is not scored there: the evaluator's own checks, in a reader's words.
export const HELD_WORDS: Record<string, string> = {
  interval: "its margin of error spans more than one range",
  edge: "it sits on the line between ranges",
  tier: "its best evidence is a company describing itself",
  single: "every reading comes from a single source, and a scored status needs a second",
  reason: "a written reason on its own page holds it",
};

export const ZONE_WORDS: Record<string, string> = { normal: "ordinary", between: "between", fast: "faster" };
const TINT: Record<string, React.CSSProperties> = {
  normal: { background: "var(--surface-2)" },
  between: { boxShadow: "inset 0 0 0 1px var(--grid)" },
  fast: { background: "var(--fast)", opacity: 0.16 },
};
export const ZoneSwatch = ({ zone }: { zone: "normal" | "between" | "fast" }) => <span className="inline-block h-2.5 w-4" style={TINT[zone]} />;

// A reading's mark. Solid: scored in the range it sits in. Ringed: between the ranges. Hollow and dashed: held, and so
// drawn outside the strip. A square is a reading graded by direction; hatched when it rests on an estimate.
export function Dot({ kind, hue = "var(--ink)" }: { kind: "scored" | "between" | "held" | "start"; hue?: string }) {
  return (
    <svg width="14" height="14" aria-hidden className="block">
      {kind === "scored" ? <circle cx="7" cy="7" r="5.5" fill={hue} stroke="var(--surface)" strokeWidth="1.5" /> : null}
      {kind === "between" ? <><circle cx="7" cy="7" r="5" fill="var(--surface)" stroke="var(--ink-2)" strokeWidth="1.5" /><circle cx="7" cy="7" r="2" fill="var(--ink-2)" /></> : null}
      {kind === "held" ? <circle cx="7" cy="7" r="5" fill="var(--surface)" stroke="var(--ink)" strokeWidth="1.5" strokeDasharray="2.5 2" /> : null}
      {kind === "start" ? <circle cx="7" cy="7" r="3.5" fill="var(--surface)" stroke="var(--ink-2)" strokeWidth="1.5" /> : null}
    </svg>
  );
}

export const DIRECTION_HUE: Record<string, string> = { concentrating: "var(--fast)", dispersing: "var(--slow)" };
export function Square({ hue, hatched }: { hue: string; hatched: boolean }) {
  return <span className={`block h-3 w-3 ${hatched ? "hatch" : ""}`} style={{ color: hue, background: hatched ? undefined : hue, boxShadow: `0 0 0 1.5px ${hue}` }} />;
}

// One slow variable on its own scale: the ordinary range, the gap, the faster range, and tonight's number. A held
// number is never drawn inside a range: it hangs beneath the strip on a dashed stem, hollow.
export function RangeStrip({ r, edge, tip }: { r: RangedReading; edge: (v: number) => string; tip: string }) {
  const out = r.lane === "outside";
  return (
    <div role="img" aria-label={tip} className="relative">
      <div className="relative h-8 font-mono text-[10px] leading-[1.25] text-muted" aria-hidden>
        {r.zones.map((z, i) => (
          <span key={z.key} className={`absolute bottom-1 whitespace-nowrap ${i === 0 ? "text-left" : i === r.zones.length - 1 ? "text-right" : "text-center"}`} style={i === 0 ? { left: 0 } : i === r.zones.length - 1 ? { right: 0 } : { left: `${z.x}%`, width: `${z.w}%` }}>
            <span className="block text-ink-2">{ZONE_WORDS[z.key]}</span>
            <span className="block">{z.key === "normal" ? <>up to {edge(r.edges[0].at)}</> : z.key === "fast" ? <>{edge(r.edges[1].at)} or more</> : <>&nbsp;</>}</span>
          </span>
        ))}
      </div>
      <div className="relative h-5">
        {r.zones.map((z) => <div key={z.key} aria-hidden className="absolute inset-y-0" style={{ left: `${z.x}%`, width: `${z.w}%`, ...TINT[z.key] }} />)}
        {r.edges.map((e) => <div key={e.x} aria-hidden className="absolute -inset-y-1 w-px bg-ink-2" style={{ left: `${e.x}%` }} />)}
        {out ? null : <span title={tip} className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2" style={{ left: `${r.x}%` }}><Dot kind={r.lane === "inside" ? "scored" : "between"} hue={r.status === "faster_than_normal" ? "var(--fast)" : "var(--ink)"} /></span>}
      </div>
      {out ? (
        <div className="relative h-6" aria-hidden>
          <span className="absolute top-0 h-2.5 border-l border-dashed border-ink" style={{ left: `${r.x}%` }} />
          <span title={tip} className="absolute top-2.5 -translate-x-1/2" style={{ left: `${r.x}%` }}><Dot kind="held" /></span>
        </div>
      ) : null}
    </div>
  );
}

// One slow variable graded by direction, on a scale from nothing: where it stood when the rule's window opened, the
// band round that reading inside which a move does not count, and where it stands tonight.
export function DirectionStrip({ r, tip, whole }: { r: DirectedReading; tip: string; whole?: string }) {
  const hue = DIRECTION_HUE[r.status ?? ""] ?? "var(--ink-2)";
  return (
    <div>
    <div role="img" aria-label={tip} title={tip} className="relative h-5 border-b border-axis">
      <div aria-hidden className="absolute inset-y-0" style={{ left: `${r.dead.x}%`, width: `${r.dead.w}%`, background: "var(--surface-2)" }} />
      <div aria-hidden className="absolute top-1/2 h-0.5 -translate-y-1/2" style={{ left: `${r.move.x}%`, width: `${r.move.w}%`, background: hue }} />
      <span className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2" style={{ left: `${r.start.x}%` }}><Dot kind="start" /></span>
      <span className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 bg-surface" style={{ left: `${r.end.x}%` }}><Square hue={hue} hatched={r.estimate} /></span>
    </div>
    <div className="mt-0.5 flex justify-between font-mono text-[10px] text-muted" aria-hidden><span>nothing</span><span>{whole}</span></div>
    </div>
  );
}

// An exit's state, or one condition's result, in the site's words for the nightly test. Glyph and border carry it.
const STATE: Record<string, { glyph: string; cls: string }> = {
  supported: { glyph: "●", cls: "border-ink text-ink" },
  unsupported: { glyph: "✕", cls: "border-ink-2 text-ink" },
  contradicted: { glyph: "◀", cls: "border-ink text-ink" },
  untestable: { glyph: "○", cls: "border-dashed border-muted text-muted" },
};
export function StateChip({ state }: { state: string | null }) {
  const s = STATE[state ?? "untestable"] ?? STATE.untestable;
  return <span className={`inline-flex items-center gap-1.5 rounded-[2px] border px-1.5 py-0.5 font-sans text-xs whitespace-nowrap ${s.cls}`}><span aria-hidden>{s.glyph}</span><span>{STATE_WORDS[state ?? "untestable"] ?? state}</span></span>;
}
export const COND_WORDS: Record<string, string> = { true: "met", false: "not met", null: "cannot be tested yet" };
export function CondMark({ holds }: { holds: boolean | null }) {
  const s = holds === true ? STATE.supported : holds === false ? STATE.unsupported : STATE.untestable;
  return <span title={COND_WORDS[String(holds)]} className={`inline-flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-[2px] border font-sans text-[11px] leading-none ${s.cls} ${holds === true ? "bg-ink text-surface" : ""}`}><span aria-hidden>{holds === true ? "✓" : s.glyph}</span><span className="sr-only">{COND_WORDS[String(holds)]}</span></span>;
}
