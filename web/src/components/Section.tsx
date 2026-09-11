import type { ReactNode } from "react";

// A numbered editorial section: hairline above, mono eyebrow number, display heading, optional action link.
export function Section({ n, title, action, id, children, className = "" }: { n?: number | string; title: ReactNode; action?: ReactNode; id?: string; children: ReactNode; className?: string }) {
  return (
    <section id={id} className={`border-t border-grid pt-6 ${className}`}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 mb-4">
        <h2 className="display text-2xl md:text-[1.75rem] leading-tight">
          {n !== undefined ? <span aria-hidden className="eyebrow mr-3 align-middle">{String(n).padStart(2, "0")}</span> : null}
          {title}
        </h2>
        {action ? <div className="text-sm text-ink-2">{action}</div> : null}
      </div>
      <div className="text-base leading-[1.6]">{children}</div>
    </section>
  );
}
