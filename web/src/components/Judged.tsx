import type { Judgement } from "@/lib/data";

// One mark for every model judgement on the site: a dotted rule, the same label, the word, then the reason.
// It sits beside a slot that has no reading and replaces nothing.
export function Judged({ j, className = "" }: { j?: Judgement | null; className?: string }) {
  if (!j) return null;
  return (
    <span className={`mt-1.5 block border-l-2 border-dotted border-axis pl-3 text-[12.5px] leading-snug text-ink-2 ${className}`}>
      <span className="text-muted">A model&apos;s judgement, not a reading: </span>
      <strong className="font-medium text-ink">{j.label}.</strong> {j.reason}
    </span>
  );
}

// The one-line version for a table cell: the word, with the reason on hover and for screen readers.
export function JudgedWord({ j }: { j?: Judgement | null }) {
  if (!j) return null;
  return (
    <span className="mt-1 block border-l-2 border-dotted border-axis pl-2 text-xs text-ink-2" title={j.reason}>
      <span className="text-muted">a model judges: </span>{j.label}<span className="sr-only">. {j.reason}</span>
    </span>
  );
}
