import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { memo, memos, obsIndex } from "@/lib/data";
import { headings, MemoBody, slug } from "@/lib/memo-md";

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
  const holds = (v: boolean | null) => (v === true ? "holds" : v === false ? "does not hold" : "untestable");
  const toc = headings(m.body);
  return (
    <article className="flex flex-col gap-8">
      <div className="scroll-progress" aria-hidden />
      <header className="flex flex-col gap-3 max-w-[68ch]">
        <p className="eyebrow"><Link href="/memos" className="hover:text-ink">Memos</Link> · {m.since} → {m.date}</p>
        <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">{m.title}</h1>
        <p className="text-sm text-muted">{m.mode === "prose" ? `Drafted by ${m.model} (prompt v${m.prompt_version}); every number checked against the record it cites; approved by merge.` : `Deterministic digest${m.fallback_reason ? ` (${m.fallback_reason})` : ""}; approved by merge.`}</p>
      </header>
      <div className="grid gap-6 md:grid-cols-2 max-w-4xl">
        {(["diffusion", "capture"] as const).map((k) => m.lens?.[k] ? (
          <blockquote key={k} className="border-l-2 border-grid pl-4 flex flex-col gap-1">
            <span className="eyebrow">{k} lens</span>
            <p className="display italic text-xl leading-snug">{m.lens[k]}</p>
          </blockquote>
        ) : null)}
      </div>
      {m.thesis && Object.keys(m.thesis).length ? <p className="text-xs text-muted max-w-[68ch]">Thesis snapshot: {Object.entries(m.thesis).map(([k, v]) => `${k.replace(/_/g, " ")} ${holds(v)}`).join(" · ")}</p> : null}
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
