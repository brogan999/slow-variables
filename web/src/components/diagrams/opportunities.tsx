import type { OpMark } from "@/lib/data";

// Parts for the figures on /value-chain/opportunities. Every width and count is the export's; nothing here works
// out a number. A business is drawn the same way in every figure: its number in the list, boxed by who keeps the profit.
const BOX: Record<string, string> = {
  innovator: "bg-ink text-surface border-ink",
  users: "border-dashed border-muted text-muted bg-surface",
};
const HELD = "border-ink text-ink bg-surface"; // kept by someone other than the maker

export function Chip({ m, plain = false }: { m: OpMark; plain?: boolean }) {
  return (
    <a href={`#op-${m.id}`} title={`${m.name}: ${m.verdict}`} aria-label={`${m.name}: ${m.verdict}`}
      className={`inline-flex h-[22px] items-center justify-center font-mono text-[11px] leading-none no-underline hover:outline hover:outline-2 hover:outline-offset-1 hover:outline-ink ${plain ? "text-muted" : `min-w-[22px] border-[1.5px] px-1 font-semibold ${BOX[m.pools] ?? HELD}`}`}>
      {m.n}
    </a>
  );
}

// The same boxes without a number, for a key strip.
export function ChipKey({ pools }: { pools: string }) {
  return <span className={`inline-block h-3 w-3 border-[1.5px] ${BOX[pools] ?? HELD}`} />;
}

// One horizontal bar on a faint track that is the whole scale. Hatched means the length is a judgement.
export function Bar({ segs, label }: { segs: { key: string; w: number; fill: string; hatched?: boolean }[]; label: string }) {
  return (
    <div role="img" aria-label={label} className="flex h-4 w-full bg-surface-2">
      {segs.map((s) => <div key={s.key} className={s.hatched ? "hatch" : ""} style={{ width: `${s.w}%`, background: s.hatched ? undefined : s.fill, color: s.fill }} />)}
    </div>
  );
}

// A step in a drawn chain: the card's own label, what the step is, and one record's words as the example.
export function Step({ label, head, example, broken = false, children }: { label: string; head: string; example: string; broken?: boolean; children: React.ReactNode }) {
  return (
    <div className={`flex h-full flex-col gap-1.5 border p-3 ${broken ? "border-dashed border-muted" : "border-ink"}`}>
      <span className="eyebrow">{label}</span>
      <span className="text-[15px] font-semibold leading-snug text-ink">{head}</span>
      <span className="text-[12.5px] leading-snug text-ink-2">{children}</span>
      <span className="mt-auto border-t border-grid pt-1.5 font-serif text-[13px] italic leading-snug text-ink-2">{example}</span>
    </div>
  );
}

export const Arrow = ({ word }: { word?: string }) => (
  <span aria-hidden className="flex items-center justify-center gap-1 whitespace-nowrap py-0.5 font-mono text-[11px] text-muted md:px-1"><span>{word}</span><span className="md:hidden">↓</span><span className="hidden md:inline">→</span></span>
);
