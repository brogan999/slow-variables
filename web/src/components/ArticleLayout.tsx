import type { ReactNode } from "react";

// The reading column carries the page; the instrument margin sits beside it (sticky) on wide screens and after
// it on narrow ones. One copy of each in the DOM, in reading order.
export function ArticleLayout({ head, margin, children }: { head: ReactNode; margin: ReactNode; children: ReactNode }) {
  return (
    <div className="grid gap-x-16 lg:grid-cols-[minmax(0,1fr)_300px]">
      <div className="lg:col-start-1 lg:row-start-1 mb-12 md:mb-16">{head}</div>
      <div className="lg:col-start-1 lg:row-start-2 min-w-0">{children}</div>
      <aside aria-label="Readings" className="mt-16 lg:mt-0 lg:col-start-2 lg:row-start-1 lg:row-span-2">
        <div className="lg:sticky lg:top-8 flex flex-col gap-6">{margin}</div>
      </aside>
    </div>
  );
}

export function MarginPanel({ title, rows, children }: { title: ReactNode; rows?: [ReactNode, ReactNode][]; children?: ReactNode }) {
  return (
    <section className="panel px-4 py-4">
      <h2 className="eyebrow mb-3">{title}</h2>
      {rows ? (
        <dl className="flex flex-col gap-2.5 text-[13px]">
          {rows.map(([k, v], i) => (
            <div key={i} className="flex flex-col gap-0.5 border-t border-grid pt-2 first:border-0 first:pt-0">
              <dt className="text-ink-2">{k}</dt>
              <dd className="text-ink font-medium">{v}</dd>
            </div>
          ))}
        </dl>
      ) : null}
      {children ? <div className="text-[13px] leading-relaxed text-ink-2 flex flex-col gap-2">{children}</div> : null}
    </section>
  );
}
