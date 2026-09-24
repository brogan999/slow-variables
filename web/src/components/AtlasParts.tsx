import Link from "next/link";
import type { AtDomain, AtMapRow, AtPlate, AtReading, AtlasDoc } from "@/lib/data";
import { Figure } from "./Figure";
import { Fact } from "./Fact";

const link = "underline decoration-axis underline-offset-2 hover:decoration-ink";

// A plate: WebP at three widths, laid out by the browser from srcset. Plain <img>, not next/image: the files are already
// sized and the site serves no image optimiser.
// `decorative` when a link beside it already names the plate, so the link is not read out with the whole alt text.
export function Plate({ p, sizes, eager, decorative, className = "" }: { p: AtPlate; sizes: string; eager?: boolean; decorative?: boolean; className?: string }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={p.src} srcSet={p.srcset} sizes={sizes} alt={decorative ? "" : p.alt} width={1024} height={p.height} loading={eager ? "eager" : "lazy"}
      fetchPriority={eager ? "high" : undefined} className={`block w-full h-auto ${className}`} />
  );
}

export function Reading({ r }: { r: AtReading }) {
  return (
    <div className="border-t border-grid pt-2 first:border-0 first:pt-0">
      <p className="text-ink-2 text-[13px]">{r.label}</p>
      {r.reading ? <p className="text-[13px]"><Fact f={r.reading} /> <span className="text-muted">· {r.year}</span></p> : <p className="text-muted text-[13px]">No public series yet</p>}
    </div>
  );
}

// The map. One plain table: a row per domain, a cell per era. Each cell holds one count per world and the "all" count;
// the radios above show one set at a time through :has() rules in globals.css, so it works without JavaScript and
// every count is a link with its own label.
export function AtlasMap({ doc }: { doc: AtlasDoc }) {
  const eras = doc.eras;
  return (
    <div className="atlas-map">
      {doc.filter ? (
        <fieldset className="flex flex-wrap items-center gap-x-4 gap-y-2 mb-3 text-sm">
          <legend className="eyebrow mb-2">Show the works that assume</legend>
          <label className="inline-flex items-center gap-1.5"><input type="radio" name="atlas-world" value="all" id="aw-all" defaultChecked /> all works</label>
          {doc.worlds.map((w) => (
            <label key={w.id} className="inline-flex items-center gap-1.5"><input type="radio" name="atlas-world" value={w.id} id={`aw-${w.id}`} /> {w.short.toLowerCase()}</label>
          ))}
        </fieldset>
      ) : null}
      <Figure
        title="How many sourced works expect change, by part of life and era"
        note="a darker cell means more sourced works expect change there, not that change is more likely"
        foot={<span>Counts distinct works in the canon; a work that expects the change whichever way things go counts in every world. An empty cell means no work in this canon places a change there, not that none will happen: the canon leans to writers who expect transformative AI, and the later eras assume it arrives, which the brake doubts.</span>}
      >
        <div className="overflow-x-auto">
          <table className="data atlas-table w-full">
            <thead>
              <tr><th scope="col">Part of life</th>{eras.map((e) => <th key={e.id} scope="col" className="text-center"><abbr title={e.label} className="no-underline">{e.short}</abbr></th>)}</tr>
            </thead>
            <tbody>
              {doc.map.map((r) => <MapRow key={r.id} r={r} />)}
            </tbody>
          </table>
        </div>
      </Figure>
    </div>
  );
}

function MapRow({ r }: { r: AtMapRow }) {
  return (
    <tr>
      <th scope="row" className="text-left font-normal">
        <Link href={r.href} className="flex items-center gap-2.5">
          <span className="hidden sm:block w-9 h-9 shrink-0 overflow-hidden rounded-full border border-axis"><Plate p={r.plate} sizes="36px" decorative className="h-full object-cover" /></span>
          <span className="font-serif text-[1rem] text-ink underline decoration-axis underline-offset-2">{r.name}</span>
        </Link>
      </th>
      {r.cells.map((c) => {
        const all = c.counts[0];
        return (
          <td key={c.era} className="p-0 text-center">
            {all.n ? (
              <Link href={c.href} className="block">
                {c.counts.map((k) => (
                  <span key={k.world} data-w={k.world} className={`atlas-n lvl-${k.level}`}>
                    <span aria-hidden>{k.n || "—"}</span><span className="sr-only">{k.label}</span>
                  </span>
                ))}
              </Link>
            ) : <span className="atlas-n lvl-0" style={{ display: "block" }}><span aria-hidden>—</span><span className="sr-only">{all.label}</span></span>}
          </td>
        );
      })}
    </tr>
  );
}

export function PlateCards({ doc }: { doc: AtlasDoc }) {
  return (
    <ol className="grid gap-6 sm:grid-cols-2">
      {doc.domains.map((d) => (
        <li key={d.id} className="panel overflow-hidden flex flex-col">
          <Link href={`/singularity/atlas/${d.id}`} className="group flex flex-col h-full">
            <Plate p={d.plate} sizes="(min-width: 1024px) 420px, (min-width: 640px) 45vw, 100vw" decorative className="aspect-[4/3] object-cover object-[center_30%]" />
            <div className="p-4 flex flex-col gap-1.5">
              <p className="eyebrow"><span className="text-gild-ink">{roman(d.n)}</span> · {d.plate.allegory}</p>
              <h3 className="display text-xl leading-tight group-hover:underline decoration-axis underline-offset-4">{d.name}</h3>
              <p className="font-serif text-[0.98rem] leading-relaxed text-ink-2">{d.thesis}</p>
            </div>
          </Link>
        </li>
      ))}
    </ol>
  );
}

export const roman = (n: number) => ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"][n - 1];

export function EraSection({ era }: { era: AtDomain["eras"][number] }) {
  return (
    <section id={era.id} aria-labelledby={`${era.id}-h`} className="mt-12 scroll-mt-8">
      <div className="gild-rule mb-5" aria-hidden />
      <h2 id={`${era.id}-h`} className="display text-[1.6rem] leading-tight">{era.label}</h2>
      <p className="text-sm text-ink-2 mt-1 max-w-[60ch]">{era.definition}</p>
      {era.entries.length ? (
        <ul className="mt-4 flex flex-col">
          {era.entries.map((e) => (
            <li key={e.id} id={e.id} className="border-t border-grid py-3.5 scroll-mt-24 target:bg-surface-2">
              <p className="font-serif text-[1.08rem] leading-relaxed text-ink">{e.line}</p>
              <p className="mt-1 text-sm text-ink-2">{e.who}, <a href={e.url} className={`italic ${link}`}>{e.work}</a>, {e.year}</p>
              <p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs">
                {e.any ? <span className="world-chip">in any world</span> : e.world_labels.map((w) => <span key={w} className="world-chip">{w}</span>)}
              </p>
              {e.reads.map((r) => <p key={r.id} className="mt-1.5 text-xs text-ink-2">Bears on: {r.label}, <Fact f={r.reading} /></p>)}
            </li>
          ))}
        </ul>
      ) : <p className="mt-3 text-sm text-muted">No sourced work places a change here.</p>}
    </section>
  );
}
