import Link from "next/link";
import type { Fact as FactT } from "@/lib/data";
import { fmt } from "@/lib/format";

// A number inside prose: only the value, linked to the record behind it; the date rides in the title. A reading that has
// aged past its limit also shows its date in plain sight, because a touch screen never shows a title.
export function Fact({ f }: { f: FactT | null | undefined }) {
  if (!f) return <span className="text-muted">(no reading yet)</span>;
  return (
    <>
      <Link href={f.href} title={`as of ${f.as_of}; ${f.obs_ids.length} record${f.obs_ids.length === 1 ? "" : "s"}`} className="num text-[0.92em] underline decoration-axis underline-offset-[3px] hover:decoration-ink whitespace-nowrap">
        {fmt(f.value, f.unit)}
      </Link>
      {f.stale ? <span className="text-muted text-[0.8em]"> (as of {f.as_of})</span> : null}
    </>
  );
}
