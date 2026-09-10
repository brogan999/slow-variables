import { words } from "@/lib/format";

// Two accents only (faster/concentrating, slower/dispersing). Icon + text always; colour never carries meaning alone.
const STYLE: Record<string, { glyph: string; cls: string }> = {
  faster_than_normal: { glyph: "▲", cls: "border-fast text-fast" },
  concentrating: { glyph: "▲", cls: "border-fast text-fast" },
  slower_than_normal: { glyph: "▼", cls: "border-slow text-slow" },
  dispersing: { glyph: "▼", cls: "border-slow text-slow" },
  consistent_with_normal: { glyph: "●", cls: "border-ink-2 text-ink" },
  stable: { glyph: "●", cls: "border-ink-2 text-ink" },
  emerging: { glyph: "◐", cls: "border-muted text-ink-2" },
  unclear: { glyph: "◐", cls: "border-muted text-ink-2" },
  mixed: { glyph: "◐", cls: "border-muted text-ink-2" },
  not_yet_measurable: { glyph: "○", cls: "border-dashed border-muted text-muted" },
};

export function StatusChip({ status, size = "sm" }: { status: string | null | undefined; size?: "sm" | "lg" }) {
  const s = STYLE[status ?? ""] ?? { glyph: "○", cls: "border-dashed border-muted text-muted" };
  const pad = size === "lg" ? "px-3.5 py-1 text-base" : "px-2 py-0.5 text-xs";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${pad} ${s.cls} whitespace-nowrap`}>
      <span aria-hidden>{s.glyph}</span>
      <span>{words(status)}</span>
    </span>
  );
}

export function Grade({ grade, tier }: { grade: string | null | undefined; tier?: number }) {
  if (!grade) return null;
  return (
    <span className="inline-flex items-center rounded border border-grid px-1.5 py-0.5 num text-[11px] font-medium text-ink-2"
      title={tier ? `Evidence tier ${tier}; grade ${grade} is derived from the tier` : `Grade ${grade}, derived from evidence tier`}>
      <span aria-hidden>{grade}{tier ? <span className="ml-1 text-muted">t{tier}</span> : null}</span>
      <span className="sr-only">grade {grade}{tier ? `, evidence tier ${tier}` : ""}</span>
    </span>
  );
}
