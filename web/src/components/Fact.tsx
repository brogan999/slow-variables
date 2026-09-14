import Link from "next/link";
import type { Fact as FactT } from "@/lib/data";
import { fmt } from "@/lib/format";

// A number inside prose: only the value, linked to the record behind it; the date rides in the title.
export function Fact({ f }: { f: FactT | null | undefined }) {
  if (!f) return <span className="text-muted">(no reading yet)</span>;
  return (
    <Link href={f.href} title={`as of ${f.as_of}; ${f.obs_ids.length} record${f.obs_ids.length === 1 ? "" : "s"}`} className="num text-[0.92em] underline decoration-axis underline-offset-[3px] hover:decoration-ink whitespace-nowrap">
      {fmt(f.value, f.unit)}
    </Link>
  );
}
