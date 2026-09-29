import { atlas, board, census, futures, index, indicator, sources, stack } from "@/lib/data";
import { plain } from "@/lib/format";

// The site search index, written once at build time from the same exports the pages read.
export const dynamic = "force-static";

export type Hit = { k: string; t: string; s: string; h: string; a?: string[] };

const untoken = (t: string) => t.replace(/\[(fact|test|cite):[^\]]+\]/g, "…");

export function GET() {
  const hits: Hit[] = [];
  for (const c of index().indicators) {
    const why = c.published ? plain(indicator(c.id).why_it_matters) : c.unpublished_reason ?? "";
    hits.push({ k: "Indicator", t: c.name, s: why, h: c.published ? `/indicators/${c.id}` : `/indicators#${c.id}` });
  }
  for (const f of board().folios) for (const r of f.rows) hits.push({ k: r.kind === "outlook" ? "Claim" : "Forecast", t: untoken(r.line), s: r.who, h: r.href });
  for (const l of stack().layers)
    for (const sub of l.sublayers)
      for (const e of sub.entities) if (e.is_primary) hits.push({ k: "Company", t: e.name, s: sub.name, h: `/stack/${sub.id}#${e.id}`, a: e.aliases });
  for (const s of sources()) hits.push({ k: "Source", t: s.name, s: s.org ?? "", h: `/sources#${s.id}` });
  for (const r of census().roles) hits.push({ k: "Job", t: r.title, s: r.function, h: r.href });
  for (const c of futures().categories) hits.push({ k: "Futures", t: c.name, s: "Imagined technologies by category", h: c.href });
  for (const d of atlas().domains) hits.push({ k: "Atlas", t: d.name, s: untoken(d.thesis), h: `/singularity/atlas/${d.id}` });
  return Response.json(hits);
}
