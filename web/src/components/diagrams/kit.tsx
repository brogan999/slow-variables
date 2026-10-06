// The diagram kit: small drawings that take everything laid out by the export (percentages and labels), so nothing
// here works out a number. A chart shows records; a model is a drawing of an idea and says so.

export const KIND_LABEL = { chart: "Chart", model: "A model, not a measurement", illustration: "Illustration, not evidence" } as const;

export type Seg = { key: string; x: number; w: number; fill: string; hatched?: boolean; tip: string };

// Rows of stacked horizontal bars that share one scale: the whole bar is the whole of the thing named on its left.
export function ShareBars({ rows, label }: { rows: { name: string; note?: string; segs: Seg[]; tick?: { x: number; tip: string } }[]; label: string }) {
  return (
    <div role="group" aria-label={label} className="flex flex-col gap-2.5">
      {rows.map((r) => (
        <div key={r.name} className="grid grid-cols-1 gap-1 sm:grid-cols-[13rem_1fr] sm:items-center sm:gap-3">
          <div className="text-[13px] leading-tight text-ink">{r.name}{r.note ? <span className="ml-1.5 font-mono text-[11px] text-muted">{r.note}</span> : null}</div>
          <div className="relative h-5 w-full">
            {r.segs.map((s) => (
              <div key={s.key} title={s.tip} className={`absolute inset-y-0 ${s.hatched ? "hatch" : ""}`} style={{ left: `${s.x}%`, width: `${s.w}%`, background: s.hatched ? undefined : s.fill, color: s.fill, boxShadow: "inset -1px 0 0 var(--surface)" }} />
            ))}
            {r.tick ? <div title={r.tick.tip} className="absolute -inset-y-0.5 w-0.5 bg-surface" style={{ left: `${r.tick.x}%` }} /> : null}
          </div>
        </div>
      ))}
    </div>
  );
}

export type Tier = { key: string; label: string; w: number; inner?: number; tip: string; hatched?: boolean; fill?: string };

// A firm drawn as stacked layers, widest where most of the payroll is. `inner` shades part of a layer from its left.
export function Pyramid({ tiers, label, compact = false }: { tiers: Tier[]; label: string; compact?: boolean }) {
  return (
    <div role="img" aria-label={label} className="flex flex-col items-center gap-0.5">
      {tiers.map((t) => (
        <div key={t.key} title={t.tip} className={`relative ${compact ? "h-3.5" : "h-6"} ${t.hatched ? "hatch" : ""}`} style={{ width: `max(${t.w}%, 3px)`, background: t.hatched ? undefined : (t.fill ?? "var(--s3)"), color: t.fill ?? "var(--s3)" }}>
          {t.inner ? <div className="absolute inset-y-0 left-0" style={{ width: `${t.inner}%`, background: "var(--s1)" }} /> : null}
          {compact ? null : <span className="absolute inset-0 flex items-center justify-center font-mono text-[10px] uppercase tracking-wider text-surface mix-blend-difference">{t.label}</span>}
        </div>
      ))}
    </div>
  );
}

// A swatch for a key strip, drawn the way the figure draws the thing.
export function Swatch({ fill, hatched = false }: { fill: string; hatched?: boolean }) {
  return <span className={`inline-block h-2.5 w-4 ${hatched ? "hatch" : ""}`} style={{ background: hatched ? undefined : fill, color: fill }} />;
}
