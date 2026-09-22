import type { RubricBand } from "@/lib/data";

// Confidence (0 to 95) against its rubric: four segments sized by their span, the one it falls in filled. The number
// and the rubric's words carry the reading; the bar shows where on the scale it sits.
export function ConfidenceBar({ value, rubric }: { value: number | null; rubric: RubricBand[] }) {
  const at = value === null ? undefined : rubric.find((b) => value >= b.lo && value <= b.hi);
  return (
    <span className="inline-flex h-1.5 w-16 shrink-0 gap-px" aria-hidden>
      {rubric.map((b) => <span key={b.lo} style={{ flexGrow: b.span }} className={b === at ? "bg-ink" : "bg-grid"} />)}
    </span>
  );
}

export const rubricWords = (value: number | null, rubric: RubricBand[]) =>
  value === null ? "no status yet" : (rubric.find((b) => value >= b.lo && value <= b.hi)?.label ?? "");
