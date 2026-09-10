import type { ReactNode } from "react";

export function PageHeader({ eyebrow, title, lede, action, children }: { eyebrow?: ReactNode; title: ReactNode; lede?: ReactNode; action?: ReactNode; children?: ReactNode }) {
  return (
    <header className="flex flex-col gap-2">
      {eyebrow ? <div className="eyebrow">{eyebrow}</div> : null}
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
        <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">{title}</h1>
        {action ? <div className="text-sm text-ink-2">{action}</div> : null}
      </div>
      {lede ? <p className="text-lg leading-snug text-ink-2 max-w-[60ch]">{lede}</p> : null}
      {children}
    </header>
  );
}
