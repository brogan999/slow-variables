import { words } from "@/lib/format";

// Two accents only (faster/concentrating, slower/dispersing). The glyph and the border carry the hue; the word stays
// ink, because text never wears a data colour. Colour never carries meaning alone.
const STYLE: Record<string, { glyph: string; hue: string }> = {
  faster_than_normal: { glyph: "▲", hue: "fast" },
  concentrating: { glyph: "▲", hue: "fast" },
  slower_than_normal: { glyph: "▼", hue: "slow" },
  dispersing: { glyph: "▼", hue: "slow" },
  consistent_with_normal: { glyph: "●", hue: "ink" },
  stable: { glyph: "●", hue: "ink" },
  emerging: { glyph: "◐", hue: "muted" },
  unclear: { glyph: "◐", hue: "muted" },
  mixed: { glyph: "◐", hue: "muted" },
  not_yet_measurable: { glyph: "○", hue: "none" },
  no_capture_rule_yet: { glyph: "○", hue: "none" },
  unpublished: { glyph: "○", hue: "none" },
};
const HUE: Record<string, { border: string; glyph: string }> = {
  fast: { border: "border-fast", glyph: "text-fast" },
  slow: { border: "border-slow", glyph: "text-slow" },
  ink: { border: "border-ink-2", glyph: "text-ink" },
  muted: { border: "border-muted", glyph: "text-ink-2" },
  none: { border: "border-dashed border-muted", glyph: "text-muted" },
};

export function StatusChip({ status, size = "sm" }: { status: string | null | undefined; size?: "sm" | "lg" }) {
  const s = STYLE[status ?? ""] ?? { glyph: "○", hue: "none" };
  const h = HUE[s.hue];
  const pad = size === "lg" ? "px-3 py-1 text-base" : "px-1.5 py-0.5 text-xs";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-[2px] border ${pad} ${h.border} ${s.hue === "none" ? "text-muted" : "text-ink"} whitespace-nowrap`}>
      <span aria-hidden className={h.glyph}>{s.glyph}</span>
      <span>{words(status)}</span>
    </span>
  );
}

// Where a figure comes from, in a word: filed or measured by the tracker's own connector, reported by someone else,
// or an estimate. Border and word carry it; no hue.
export function Stamp({ kind }: { kind: "measured" | "reported" | "estimate" }) {
  const cls = kind === "measured" ? "border-ink text-ink" : kind === "reported" ? "border-muted text-ink-2" : "border-dashed border-muted text-ink-2";
  return (
    <span className={`inline-flex items-center gap-1 rounded-[2px] border px-1.5 py-px font-mono text-[10px] font-medium uppercase tracking-[0.07em] whitespace-nowrap ${cls}`}>
      {kind === "estimate" ? <span aria-hidden className="hatch inline-block h-2 w-2 text-muted" /> : null}
      {kind}
    </span>
  );
}

// A company, the prototype's chip. `exit` marks a sale: a solid ring and an arrow, no colour.
export function Chip({ name, meta, href, exit }: { name: string; meta?: string; href?: string; exit?: boolean }) {
  const body = (
    <>
      {exit ? <span aria-hidden>→</span> : null}
      <span className="text-ink">{name}</span>
      {meta ? <span className="text-muted">· {meta}</span> : null}
    </>
  );
  const cls = `inline-flex items-center gap-1 rounded-[2px] bg-surface-2 px-2 py-0.5 font-mono text-[11px] text-ink-2 whitespace-nowrap ${exit ? "ring-1 ring-ink" : "ring-1 ring-axis"}`;
  return href ? <a href={href} className={`${cls} hover:ring-ink`}>{body}</a> : <span className={cls}>{body}</span>;
}

// The evaluator crossed a band and a human has not yet written the reason: the card keeps the old status and says so.
export function PendingNote({ p }: { p: { new_status: string; since: string } | null | undefined }) {
  if (!p) return null;
  const s = STYLE[p.new_status] ?? { glyph: "○" };
  return (
    <span className="text-xs text-ink-2">
      Evaluator reads <span aria-hidden>{s.glyph}</span> {words(p.new_status)} since {p.since}; reason pending
    </span>
  );
}

export function Grade({ grade, tier }: { grade: string | null | undefined; tier?: number }) {
  if (!grade) return null;
  return (
    <span className={`inline-flex items-center rounded-[2px] border ${grade === "D" ? "border-bind" : "border-grid"} px-1.5 py-0.5 num text-[11px] font-medium text-ink-2`}
      title={tier ? `Evidence tier ${tier}; grade ${grade} is derived from the tier` : `Grade ${grade}, derived from evidence tier`}>
      <span aria-hidden>{grade}{tier ? <span className="ml-1 text-muted">t{tier}</span> : null}</span>
      <span className="sr-only">grade {grade}{tier ? `, evidence tier ${tier}` : ""}</span>
    </span>
  );
}
