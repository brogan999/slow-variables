import Link from "next/link";
import type { DataMarketDoc } from "@/lib/data";

// One mark for each level: solid where the record is openly sold or released, hatched where an incumbent uses its
// own, a small dot where only nearby players were found, an open square where nobody was, a faint one where no
// search was run. A ring means a dossier examines it.
const MARK: Record<string, string> = {
  "3": "bg-slow",
  "2": "hatch text-slow",
  "1": "bg-[radial-gradient(circle,var(--slow)_0_2px,transparent_2.5px)] shadow-[inset_0_0_0_1px_var(--grid)]",
  "0": "shadow-[inset_0_0_0_1px_var(--axis)]",
  null: "bg-grid",
};
const RING = "outline outline-2 outline-offset-1 outline-fast";

export function Mark({ level, className = "" }: { level: number | null; className?: string }) {
  return <span aria-hidden className={`inline-block h-2.5 w-2.5 rounded-[1px] ${MARK[String(level)]} ${className}`} />;
}

/** Every kind of record as one mark, by family. `base` is the page the marks link into ("" for this page);
 * `dense` sets the families in two columns on a wide screen, for a page where the field is the opening image. */
export function DataMarketField({ sources, base = "", dense = false }: { sources: DataMarketDoc["sources"]; base?: string; dense?: boolean }) {
  return (
    <div className="flex flex-col gap-4">
      <ul className="flex flex-wrap gap-x-5 gap-y-1.5 text-[13px] text-ink-2">
        {sources.key.map((k) => (
          <li key={String(k.level)} className="flex items-center gap-1.5"><Mark level={k.level} /> {k.name} <span className="num text-muted">{k.n}</span></li>
        ))}
        <li className="flex items-center gap-1.5"><span aria-hidden className={`inline-block h-2.5 w-2.5 rounded-[1px] ${RING}`} /> <Link href="/data-market/dossiers" className="underline decoration-grid underline-offset-4">Examined in a dossier</Link> <span className="num text-muted">{sources.examined}</span></li>
      </ul>
      <div className={dense ? "lg:columns-2 lg:gap-x-12 max-md:[&>*:nth-child(n+9)]:hidden" : ""}>
        {sources.families.map((f) => (
          <div key={f.name} className={`mb-2 grid break-inside-avoid grid-cols-1 gap-x-4 gap-y-1 ${dense ? "md:grid-cols-[13rem_1fr]" : "md:grid-cols-[15rem_1fr]"}`}>
            <a href={`${base}#${f.rows[0].id}-family`} className="text-[12.5px] leading-tight text-ink-2 hover:text-ink md:text-right">{f.name} <span className="num text-muted">{f.n}</span></a>
            <div className="flex flex-wrap content-start gap-[3px]">
              {f.marks.map((m) => (
                <a key={m.id} href={`${base}#${m.id}`} title={m.name} aria-label={m.name}><Mark level={m.level} className={m.dossier ? `block ${RING}` : "block"} /></a>
              ))}
            </div>
          </div>
        ))}
      </div>
      {dense ? <p className="text-[13px] text-ink-2 md:hidden">The largest families are shown. <Link href={base || "/data-market/sources"} className="underline decoration-grid underline-offset-4">See every family</Link>.</p> : null}
    </div>
  );
}
