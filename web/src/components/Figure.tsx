import type { Stamp as StampT } from "@/lib/data";
import { Stamp } from "./StatusChip";

// The prototype's figure card: a header strip (number, title, what the encoding means), the chart, a key strip, a foot
// with the stamps and sources, and the numbers as a table. The number comes from a CSS counter on <main>.
export function Figure({ title, note, keys, stamps, foot, table, tableLabel = "The numbers", children, id }: {
  title: React.ReactNode; note?: React.ReactNode; keys?: React.ReactNode; stamps?: StampT[]; foot?: React.ReactNode;
  table?: React.ReactNode; tableLabel?: string; children: React.ReactNode; id?: string;
}) {
  return (
    <figure className="fig" id={id}>
      <figcaption className="fig-head">
        <span className="fig-n" aria-hidden />
        <span className="fig-title">{title}</span>
        {note ? <span className="fig-note">{note}</span> : null}
      </figcaption>
      <div className="fig-body">{children}</div>
      {keys ? <div className="fig-key">{keys}</div> : null}
      {foot || stamps?.length ? (
        <div className="fig-foot">
          {stamps?.length ? <span className="inline-flex flex-wrap gap-1.5">{stamps.map((s) => <Stamp key={s} kind={s} />)}</span> : null}
          {foot}
        </div>
      ) : null}
      {table ? <details className="fig-table"><summary>{tableLabel}</summary><div className="overflow-x-auto mt-2">{table}</div></details> : null}
    </figure>
  );
}

// One entry in a key strip: a swatch drawn the way the chart draws it, and its meaning.
export function Key({ swatch, children }: { swatch: React.ReactNode; children: React.ReactNode }) {
  return <span className="inline-flex items-center gap-1.5"><span className="flex shrink-0">{swatch}</span><span>{children}</span></span>;
}

// The prototype's labelled box: a spending signal, an override note, the bells. `id` makes it a section with its
// label as a heading (content that belongs to the page); without one it is an aside note.
export function Callout({ label, id, children }: { label: string; id?: string; children: React.ReactNode }) {
  return id ? (
    <section aria-labelledby={id} className="callout">
      <h2 id={id} className="eyebrow">{label}</h2>
      <div className="mt-1.5">{children}</div>
    </section>
  ) : (
    <aside role="note" className="callout">
      <span className="eyebrow">{label}</span>
      <div className="mt-1.5">{children}</div>
    </aside>
  );
}
