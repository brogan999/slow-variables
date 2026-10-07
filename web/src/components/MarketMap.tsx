import Link from "next/link";
import type { MarketMapCategory, MarketMapDoc, MarketMapEntity } from "@/lib/data";
import { MarketMapFilter } from "./MarketMapFilter";

const link = "underline decoration-grid underline-offset-2 hover:decoration-ink";
const OWNERSHIP: Record<string, string> = { acquired: "acquired", being_acquired: "acquisition pending", defunct: "closed" };

function provenance(e: MarketMapEntity): string {
  if (e.default) return `Placed by its sub-layer (${e.label.replaceAll("_", " ")})`;
  if (e.source === "hand" && e.label.startsWith("default of ")) return `Placed by its sub-layer (${e.label.slice(11).replaceAll("_", " ")})`;
  if (e.source === "hand") return `Placed by hand (${e.label.replace(/;?\s*hand placement,?\s*\(?/i, ", ").replace(/^, |\)$/g, "").replace(/\s+/g, " ").replace("review 28", "review, 28").trim()})`;
  return `${e.source_name ?? e.source}, section “${e.label}”${e.read ? `, read ${e.read}` : ""}`;
}

const owned = (e: MarketMapEntity) => (e.ownership ? `${OWNERSHIP[e.ownership]}${e.ownership_note ? `: ${e.ownership_note}` : ""}` : null);

// A company chip: bold when the tracker has verified the entity (a filing or a dataset row), not when its placement was
// reviewed; an acquired or closed company carries a muted word, and its provenance is the chip's title and the card's list.
function EntityChip({ e }: { e: MarketMapEntity }) {
  return (
    <span
      data-name={e.name.toLowerCase()}
      title={[e.legal_name !== e.name ? e.legal_name : null, e.leaf, provenance(e), owned(e)].filter(Boolean).join(" · ")}
      className={`mm-chip inline-flex items-center gap-1 rounded-[2px] bg-surface-2 px-1.5 py-0.5 text-[12px] ring-1 ring-axis ${e.verified ? "font-semibold text-ink" : "text-ink-2"}`}
    >
      {e.name}
      {e.ownership ? <span className="font-normal text-muted">({OWNERSHIP[e.ownership]})</span> : null}
    </span>
  );
}

function Leaves({ c }: { c: MarketMapCategory }) {
  return (
    <span role="img" className="flex flex-wrap gap-[3px]" aria-label={`${c.leaves_covered} of ${c.n_leaves} parts have a company`}>
      {c.leaves.map((l) => (
        <span key={l.name} title={`${l.name}: ${l.n}`} className={`inline-block h-[9px] w-[9px] rounded-full ${l.n ? "bg-ink-2" : "ring-1 ring-inset ring-axis"}`} />
      ))}
    </span>
  );
}

function Card({ c }: { c: MarketMapCategory }) {
  const state = c.out_of_scope ? "scope" : c.n_entities === 0 ? "unmapped" : "mapped";
  const byId = new Map(c.entities.map((e) => [e.id, e]));
  const groups = [...c.leaves.map((l) => l.name), null].map((leaf) => ({ leaf, es: c.entities.filter((e) => e.leaf === leaf) })).filter((g) => g.es.length);
  return (
    <article
      id={`mm-${c.id}`}
      data-state={state}
      data-names={c.entities.map((e) => e.name.toLowerCase()).join("|")}
      className={`mm-card fig flex flex-col gap-2 p-3 ${state === "scope" ? "bg-surface-2" : ""}`}
    >
      <header className="flex items-baseline gap-2">
        <span className="font-mono text-[11px] text-muted">{c.number}</span>
        <h4 className={`text-[14px] font-semibold leading-tight ${state === "scope" ? "text-muted" : "text-ink"}`}>{c.name}</h4>
        <span className="ml-auto font-mono text-[12px] text-ink">{c.n_entities || ""}</span>
      </header>
      <Leaves c={c} />
      {state === "scope" ? <p className="text-[12px] italic text-muted">{c.out_of_scope}</p> : null}
      {state === "unmapped" ? (
        <p className="rounded-[2px] border border-dashed border-muted px-2 py-3 text-[12px] italic text-muted">Not yet mapped by the tracker. This says where our coverage stops, not that the market is empty.</p>
      ) : null}
      {c.chips.length ? (
        <div className="flex flex-wrap gap-[3px]">
          {c.chips.map((id) => <EntityChip key={id} e={byId.get(id)!} />)}
          {c.n_more ? <span className="px-1 font-mono text-[11px] text-muted">+{c.n_more}</span> : null}
        </div>
      ) : null}
      <footer className="flex gap-3 font-mono text-[10.5px] text-muted">
        <span>{c.leaves_covered}/{c.n_leaves} parts</span>
        <span>{c.n_indicators ? `${c.n_indicators} indicator${c.n_indicators > 1 ? "s" : ""}` : "no indicator"}</span>
      </footer>
      {c.n_entities || c.n_indicators ? (
        <details className="text-[12.5px]">
          <summary className="cursor-pointer font-mono text-[11px] text-ink-2">Companies, sources and readings</summary>
          <dl className="mt-2 flex flex-col gap-2">
            {groups.map((g) => (
              <div key={g.leaf ?? "none"}>
                <dt className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">{g.leaf ?? "Part not assigned"}</dt>
                {[...new Set(g.es.map(provenance))].map((src) => (
                  <dd key={src} className="leading-snug">
                    <span className="text-muted">{src}: </span>
                    {g.es.filter((e) => provenance(e) === src).map((e, k) => (
                      <span key={e.id} data-name={e.name.toLowerCase()} className="mm-row">
                        {k ? ", " : ""}
                        <span className={e.verified ? "font-semibold" : ""}>{e.name}</span>
                        {e.legal_name !== e.name ? <span className="text-muted"> ({e.legal_name})</span> : null}
                        {e.ownership ? <span className="text-muted"> ({owned(e)})</span> : null}
                      </span>
                    ))}
                  </dd>
                ))}
              </div>
            ))}
          </dl>
          {c.n_indicators ? (
            <p className="mt-2">Readings: {c.indicators.map((i, k) => <span key={i.id}>{k ? ", " : ""}<Link href={`/indicators/${i.id}`} className={link}>{i.name}</Link></span>)}</p>
          ) : null}
          {c.venture_sublayers.length ? (
            <p className="mt-1 text-muted">Venture money for {c.venture_sublayers.map((s, k) => <span key={s}>{k ? ", " : ""}<Link href={`/stack/${s}`} className={link}>{s.replaceAll("_", " ")}</Link></span>)}, as recorded by sub-layer.</p>
          ) : null}
        </details>
      ) : null}
    </article>
  );
}

export function MarketMap({ m, figures }: { m: MarketMapDoc; figures?: React.ReactNode }) {
  const n = m.counts;
  return (
    <section id="market-map" className="mm flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <h2 className="display text-[1.8rem] leading-tight">The market map</h2>
        <p className="text-ink-2 leading-relaxed max-w-[68ch]">
          Every company the tracker follows, placed in a finer map of the chain. A company can sit in several places, and each place says which source put it there. {m.credit}
        </p>
        <p className="font-mono text-[12px] text-ink-2">
          {n.layers} layers · {n.categories} categories · {n.leaves} parts · {n.entities} companies · {n.placements} placements · {n.unmapped_categories} categories not yet mapped · {n.excluded} kept off the map · {n.indicators} readings
        </p>
      </div>
      {figures}
      <MarketMapFilter />
      <div className="flex flex-col gap-2 text-[12px] text-ink-2">
        <p className="flex flex-wrap gap-x-4 gap-y-1">
          <span className="inline-flex items-center gap-1.5"><span className="inline-flex gap-[3px]" aria-hidden><span className="inline-block h-[9px] w-[9px] rounded-full bg-ink-2" /><span className="inline-block h-[9px] w-[9px] rounded-full ring-1 ring-inset ring-axis" /></span>each dot is one part of the category; filled means the tracker has a company there</span>
          <span><span className="font-semibold text-ink">Bold</span>: verified through a filing or a dataset</span>
          <span>(acquired), (acquisition pending), (closed): what happened to the company</span>
          <span className="inline-flex items-center gap-1.5"><span className="inline-block h-[10px] w-[16px] border border-dashed border-muted" aria-hidden />not yet mapped: a gap in our coverage, not in the market</span>
        </p>
        <nav aria-label="Layers of the map" className="flex flex-wrap gap-x-3 gap-y-1 font-mono text-[11px]">
          {m.layers.map((L) => <a key={L.id} href={`#mm-layer-${L.id}`} className={link}>{L.number} {L.name}</a>)}
        </nav>
      </div>
      {m.layers.map((L) =>
        L.indicator_only ? (
          <div key={L.id} id={`mm-layer-${L.id}`} data-unmapped="0" className="mm-layer scroll-mt-4 grid gap-3 border-t border-grid pt-4 md:grid-cols-[11rem_minmax(0,1fr)]">
            <div><div className="font-mono text-[11px] text-muted">Layer {L.number}</div><h3 className="font-semibold leading-tight">{L.name}</h3><p className="mt-1 font-mono text-[11px] text-muted">readings only; no companies</p></div>
            <div className="flex flex-wrap gap-1">
              {L.categories.flatMap((c) => c.indicators).map((i) => <Link key={i.id} href={`/indicators/${i.id}`} className="rounded-[2px] bg-surface px-2 py-0.5 text-[12px] text-ink-2 ring-1 ring-grid hover:ring-ink">{i.name}</Link>)}
            </div>
          </div>
        ) : (
          <div key={L.id} id={`mm-layer-${L.id}`} data-unmapped={L.n_unmapped} className="mm-layer scroll-mt-4 grid gap-3 border-t border-grid pt-4 md:grid-cols-[11rem_minmax(0,1fr)]">
            <div>
              <div className="font-mono text-[11px] text-muted">Layer {L.number}</div>
              <h3 className="font-semibold leading-tight">{L.name}</h3>
              <p className="mt-1 font-mono text-[11px] text-muted">{L.n_categories} categories · {L.n_entities} companies{L.n_unmapped ? ` · ${L.n_unmapped} not yet mapped` : ""}</p>
            </div>
            <div className="grid items-start gap-2 [grid-template-columns:repeat(auto-fill,minmax(15rem,1fr))]">
              {L.categories.map((c) => <Card key={c.id} c={c} />)}
            </div>
          </div>
        ),
      )}
      <p className="text-xs text-muted max-w-[68ch]">Placements come from each source&apos;s own section labels and were checked by hand; companies whose work is robotics or autonomy are off the map for now.</p>
    </section>
  );
}
