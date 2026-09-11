import Link from "next/link";
import { publishedIds } from "@/lib/data";
import { indicatorHref } from "@/lib/format";

// The memo body is markdown written by the memo job (a model or the digest); this renders the subset it uses:
// headings, paragraphs, bullet lists, bold, and citation tokens [obs:id] / [derived:id] / [ind:id] / [event:id] as links.
const TOKEN = /(\[(?:obs|derived|ind|event):[A-Za-z0-9_.-]+\]|\*\*[^*]+\*\*|https?:\/\/[^\s)]+)/g;

export const slug = (t: string) => t.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
export const headings = (body: string) => body.split(/\n{2,}/).map((b) => b.trim()).filter((b) => b.startsWith("## ")).map((b) => b.slice(3));

function inline(text: string, obsIndex: Record<string, string>) {
  return text.split(TOKEN).map((p, i) => {
    const m = p.match(/^\[(obs|derived|ind|event):([A-Za-z0-9_.-]+)\]$/);
    if (m) {
      const [, kind, id] = m;
      const href = kind === "obs" ? (obsIndex[id] ? `/series/${obsIndex[id]}#${id}` : null) : kind === "ind" ? indicatorHref(id, publishedIds().has(id)) : kind === "event" ? "/changelog" : "/query";
      const label = `${kind}:${id.slice(0, 8)}`;
      return href ? <Link key={i} href={href} className="num text-[11px] text-ink-2 underline decoration-grid underline-offset-2">{label}</Link> : <span key={i} className="num text-[11px] text-muted">{label}</span>;
    }
    if (p.startsWith("**") && p.endsWith("**")) return <strong key={i} className="font-medium">{p.slice(2, -2)}</strong>;
    if (/^https?:\/\//.test(p)) return <a key={i} href={p} className="underline decoration-grid underline-offset-2 break-all">{p.replace(/^https?:\/\//, "").slice(0, 60)}</a>;
    return <span key={i}>{p}</span>;
  });
}

export function MemoBody({ body, obsIndex }: { body: string; obsIndex: Record<string, string> }) {
  const blocks = body.split(/\n{2,}/).map((b) => b.trim()).filter(Boolean);
  return (
    <div className="flex flex-col gap-4 text-[17px] leading-[1.65] max-w-[68ch]">
      {blocks.map((b, i) => {
        if (b.startsWith("## ")) return <h2 key={i} id={slug(b.slice(3))} className="display text-2xl leading-tight border-t border-grid pt-6 mt-6 scroll-mt-6">{b.slice(3)}</h2>;
        if (b.startsWith("# ")) return <h2 key={i} className="display text-2xl leading-tight mt-6">{b.slice(2)}</h2>;
        if (b.split("\n").every((l) => l.startsWith("- "))) return <ul key={i} className="list-disc pl-5 flex flex-col gap-2 text-base leading-[1.6]">{b.split("\n").map((l, j) => <li key={j}>{inline(l.slice(2), obsIndex)}</li>)}</ul>;
        return <p key={i}>{inline(b, obsIndex)}</p>;
      })}
    </div>
  );
}
