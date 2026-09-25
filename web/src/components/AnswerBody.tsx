import Link from "next/link";
import { Fragment, useId } from "react";

export type Cite = { kind: string; id: string; href: string | null; label?: string; value?: string | null; date?: string | null; snippet?: string };

// The subset of markdown Ask answers use (paragraphs, bullets, short headings, bold, italic) with citation tokens as
// numbered chips. A chip opens a card (native popover) naming the record; unresolved tokens stay visible as text.
const TOKEN = /(\[(?:obs|derived|ind|event|census|src|pos|claim|pred):[A-Za-z0-9_.-]+\]|⟦unverified: [^⟧]*⟧|\*\*[^*]+\*\*|\*[^*\s][^*]*\*)/g;
const KIND = { obs: "observation", derived: "derived row", ind: "indicator", event: "status change", census: "census row", src: "source", pos: "position", claim: "claim", pred: "prediction" } as Record<string, string>;

export function citeOrder(text: string, cites: Cite[]): Cite[] {
  const byTok = new Map(cites.map((c) => [`[${c.kind}:${c.id}]`, c]));
  const seen = new Map<string, Cite>();
  for (const m of text.matchAll(TOKEN)) { const c = byTok.get(m[0]); if (c && !seen.has(m[0])) seen.set(m[0], c); }
  return [...seen.values()];
}

function Chip({ c, n }: { c: Cite; n: number }) {
  const pid = `cite-${useId().replace(/:/g, "")}`;
  return (
    <>
      <button type="button" popoverTarget={pid} aria-label={`Source ${n}: ${c.label ?? KIND[c.kind] ?? c.kind}`} className="align-super mx-0.5 num text-[10px] leading-none px-1 py-0.5 rounded-[3px] border border-grid text-ink-2 hover:bg-surface-2 hover:text-ink">{n}</button>
      <span id={pid} popover="auto" className="m-auto w-[min(22rem,calc(100vw-2rem))] panel p-3 text-xs leading-relaxed text-ink-2 shadow-lg">
        <span className="eyebrow block">{KIND[c.kind] ?? c.kind} {n}</span>
        <span className="block text-ink font-medium mt-1 break-words">{c.label ?? c.id}</span>
        {c.value || c.date ? <span className="block num mt-0.5">{[c.value, c.date].filter(Boolean).join(" · ")}</span> : null}
        {c.snippet ? <span className="block mt-1.5">{c.snippet}</span> : null}
        {c.href ? <Link href={c.href} className="block mt-2 underline decoration-grid underline-offset-2 text-ink">Open the record</Link> : null}
      </span>
    </>
  );
}

function Inline({ text, nums }: { text: string; nums: Map<string, [Cite, number]> }) {
  return text.split(TOKEN).map((p, i) => {
    const hit = nums.get(p);
    if (hit) return <Chip key={i} c={hit[0]} n={hit[1]} />;
    if (p.startsWith("⟦")) return <mark key={i} className="bg-error/10 text-error">{p.slice(1, -1)}</mark>;
    if (p.startsWith("**") && p.endsWith("**") && p.length > 4) return <strong key={i} className="font-medium text-ink">{p.slice(2, -2)}</strong>;
    if (p.startsWith("*") && p.endsWith("*") && p.length > 2) return <em key={i}>{p.slice(1, -1)}</em>;
    return <Fragment key={i}>{p}</Fragment>;
  });
}

export function AnswerBody({ text, cites }: { text: string; cites: Cite[] }) {
  const nums = new Map(citeOrder(text, cites).map((c, i) => [`[${c.kind}:${c.id}]`, [c, i + 1] as [Cite, number]]));
  const blocks: ({ t: "p" | "h"; s: string } | { t: "ul"; s: string[] })[] = [];
  for (const line of text.split("\n")) {
    const l = line.trim(), last = blocks[blocks.length - 1];
    if (!l) { blocks.push({ t: "p", s: "" }); continue; }
    const bullet = l.match(/^(?:[-*]|\d+\.)\s+(.*)$/);
    if (bullet) { if (last?.t === "ul") last.s.push(bullet[1]); else blocks.push({ t: "ul", s: [bullet[1]] }); continue; }
    const head = l.match(/^#{1,4}\s+(.*)$/);
    if (head) { blocks.push({ t: "h", s: head[1] }); continue; }
    if (last?.t === "p" && last.s) last.s += " " + l; else blocks.push({ t: "p", s: l });
  }
  return (
    <div className="flex flex-col gap-3 text-[1rem] leading-[1.65] text-ink">
      {blocks.map((b, i) => b.t === "ul"
        ? <ul key={i} className="list-disc pl-5 flex flex-col gap-1.5 marker:text-muted">{b.s.map((x, j) => <li key={j}><Inline text={x} nums={nums} /></li>)}</ul>
        : b.t === "h" ? <h3 key={i} className="font-medium text-ink mt-1">{<Inline text={b.s} nums={nums} />}</h3>
        : b.s ? <p key={i}><Inline text={b.s} nums={nums} /></p> : null)}
    </div>
  );
}
