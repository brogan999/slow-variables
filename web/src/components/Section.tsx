import type { ReactNode } from "react";

// A folio: hairline above, a small instrument label, a claim as the heading, optional action link.
export function Section({ n, title, action, id, children, className = "" }: { n?: number | string; title: ReactNode; action?: ReactNode; id?: string; children: ReactNode; className?: string }) {
  return (
    <section id={id} className={`border-t border-grid pt-8 mt-4 ${className}`}>
      {n !== undefined ? <div aria-hidden className="eyebrow mb-2">{typeof n === "number" ? `§ ${String(n).padStart(2, "0")}` : n}</div> : null}
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 mb-5">
        <h2 className="display text-[1.75rem] md:text-[2rem] leading-tight">{title}</h2>
        {action ? <div className="text-sm text-ink-2">{action}</div> : null}
      </div>
      <div className="text-base leading-[1.65]">{children}</div>
    </section>
  );
}
