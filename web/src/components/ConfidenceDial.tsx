// Confidence 0-95 as an arc with the rubric's four bands; text carries the number, the arc is decoration.
const BANDS = [[0, 50, "limited or vague"], [50, 70, "mixed or hard to operationalise"], [70, 90, "good evidence, some ambiguity"], [90, 95, "multiple strong independent sources"]] as const;

export function ConfidenceDial({ value, size = 44 }: { value: number | null | undefined; size?: number }) {
  if (value === null || value === undefined) return null;
  const r = (size - 6) / 2, c = size / 2, frac = Math.max(0, Math.min(95, value)) / 95;
  const a = Math.PI * (1 + frac), x = c + r * Math.cos(a), y = c + r * Math.sin(a);
  const label = BANDS.find(([lo, hi]) => value >= lo && value < hi)?.[2] ?? BANDS[3][2];
  return (
    <span className="inline-flex items-center gap-1.5" title={`Confidence ${value} of 95: ${label}`}>
      <svg width={size} height={size / 2 + 4} viewBox={`0 0 ${size} ${size / 2 + 4}`} aria-hidden>
        <path d={`M${c - r},${c} A${r},${r} 0 0 1 ${c + r},${c}`} fill="none" stroke="var(--grid)" strokeWidth="3" />
        <path d={`M${c - r},${c} A${r},${r} 0 ${frac > 0.5 ? 1 : 0} 1 ${x},${y}`} fill="none" stroke="var(--ink)" strokeWidth="3" strokeLinecap="round" />
      </svg>
      <span className="num text-xs"><span className="font-medium">{value}</span><span className="text-muted">/95</span><span className="sr-only"> confidence, {label}</span></span>
    </span>
  );
}
