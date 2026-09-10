import Link from "next/link";

// The memo body is markdown written by the memo job (a model or the digest); this renders the subset it uses:
// headings, paragraphs, bullet lists, bold, and citation tokens [obs:id] / [derived:id] / [ind:id] as links.
const TOKEN = /(\[(?:obs|derived|ind|event):[A-Za-z0-9_.-]+\]|\*\*[^*]+\*\*|https?:\/\/[^\s)]+)/g;

function inline(text: string, obsIndex: Record<string, string>) {
  return text.split(TOKEN).map((p, i) => {
    const m = p.match(/^\[(obs|derived|ind|event):([A-Za-z0-9_.-]+)\]$/);
    if (m) {
      const [, kind, id] = m;
      const href = kind === "obs" ? (obsIndex[id] ? `/series/${obsIndex[id]}#${id}` : null) : kind === "ind" ? `/indicators/${id}` : kind === "event" ? "/changelog" : "/query";
      const label = `${kind}:${id.slice(0, 8)}`;
      return href ? <Link key={i} href={href} className="font-mono text-[11px] text-ink-2 underline decoration-grid underline-offset-2">{label}</Link> : <span key={i} className="font-mono text-[11px] text-muted">{label}</span>;
    }
    if (p.startsWith("**") && p.endsWith("**")) return <strong key={i}>{p.slice(2, -2)}</strong>;
    if (/^https?:\/\//.test(p)) return <a key={i} href={p} className="underline decoration-grid underline-offset-2 break-all">{p.replace(/^https?:\/\//, "").slice(0, 60)}</a>;
    return <span key={i}>{p}</span>;
  });
}

export function MemoBody({ body, obsIndex }: { body: string; obsIndex: Record<string, string> }) {
  const blocks = body.split(/\n{2,}/).map((b) => b.trim()).filter(Boolean);
  return (
    <div className="flex flex-col gap-3 text-[15px] leading-relaxed max-w-3xl">
      {blocks.map((b, i) => {
        if (b.startsWith("## ")) return <h2 key={i} className="text-sm font-medium text-ink-2 mt-3">{b.slice(3)}</h2>;
        if (b.startsWith("# ")) return <h2 key={i} className="text-base font-medium mt-3">{b.slice(2)}</h2>;
        if (b.split("\n").every((l) => l.startsWith("- "))) return <ul key={i} className="list-disc pl-5 flex flex-col gap-1">{b.split("\n").map((l, j) => <li key={j}>{inline(l.slice(2), obsIndex)}</li>)}</ul>;
        return <p key={i}>{inline(b, obsIndex)}</p>;
      })}
    </div>
  );
}
