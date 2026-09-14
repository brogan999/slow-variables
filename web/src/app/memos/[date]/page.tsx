import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { memo, memos, obsIndex, thesis } from "@/lib/data";
import { STATE_WORDS } from "@/lib/format";
import { headings, MemoBody, slug } from "@/lib/memo-md";

export const dynamicParams = false; // the date names a file; only built memos are served
export function generateStaticParams() { return memos().map((m) => ({ date: m.date })); }
export async function generateMetadata({ params }: { params: Promise<{ date: string }> }): Promise<Metadata> {
  const { date } = await params;
  const m = memo(date);
  return { title: m ? m.title : "Memo", description: m?.lens?.diffusion };
}

export default async function MemoPage({ params }: { params: Promise<{ date: string }> }) {
  const { date } = await params;
  const m = memo(date);
  if (!m) notFound();
  const names = Object.fromEntries(thesis().map((t) => [t.id, t.name]));
  const holds = (v: boolean | string | null) => (v === true ? "holds" : v === false ? "does not hold" : "untestable");
  const toc = headings(m.body);
  return (
    <article className="flex flex-col gap-8">
      <div className="scroll-progress" aria-hidden />
      <header className="flex flex-col gap-3 max-w-[68ch]">
        <p className="eyebrow"><Link href="/memos" className="hover:text-ink">Memos</Link> · {m.since} → {m.date}</p>
        <h1 className="display text-[2.5rem] md:text-[3.5rem] leading-[1.02] max-w-[24ch]">{m.title}</h1>
        <p className="text-sm text-muted">{m.mode === "prose" ? `Drafted by ${m.model} (prompt v${m.prompt_version}); every number checked against the record it cites; approved by merge.` : "Written from the data by a fixed template this week, without a model; approved by merge."}</p>
      </header>
      <div className="grid gap-6 md:grid-cols-2 max-w-4xl">
        {(["diffusion", "capture"] as const).map((k) => m.lens?.[k] ? (
          <blockquote key={k} className="border-l-2 border-grid pl-4 flex flex-col gap-1">
            <span className="eyebrow">{k} lens</span>
            <p className="display italic text-xl leading-snug">{m.lens[k]}</p>
          </blockquote>
        ) : null)}
      </div>
      {m.thesis && Object.keys(m.thesis).length ? <p className="text-xs text-muted max-w-[68ch]">The tests that week: {Object.entries(m.thesis).map(([k, v]) => `${names[k] ?? k.replace(/_/g, " ")}: ${typeof v === "string" ? STATE_WORDS[v] ?? v : holds(v)}`).join(" · ")}</p> : null}
      {toc.length ? (
        <nav aria-label="On this page" className="border-t border-grid pt-4">
          <ol className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-ink-2">
            {toc.map((t, i) => <li key={t}><a href={`#${slug(t)}`} className="hover:text-ink"><span className="num text-muted mr-1.5">{String(i + 1).padStart(2, "0")}</span>{t}</a></li>)}
          </ol>
        </nav>
      ) : null}
      <MemoBody body={m.body} obsIndex={obsIndex()} />
    </article>
  );
}
