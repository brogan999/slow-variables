import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { memo, memos, obsIndex } from "@/lib/data";
import { MemoBody } from "@/lib/memo-md";

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
  return (
    <article className="flex flex-col gap-4">
      <div>
        <p className="text-xs text-muted"><Link href="/memos" className="hover:underline">Memos</Link> · {m.since} to {m.date}</p>
        <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">{m.title}</h1>
        <p className="text-xs text-muted mt-1">{m.mode === "prose" ? `Drafted by ${m.model} (prompt v${m.prompt_version}), every number checked against the record it cites; approved by merge.` : `Deterministic digest${m.fallback_reason ? ` (${m.fallback_reason})` : ""}; approved by merge.`}</p>
      </div>
      <dl className="grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2 max-w-3xl">
        <div><dt className="text-xs text-muted">Diffusion lens</dt><dd>{m.lens?.diffusion}</dd></div>
        <div><dt className="text-xs text-muted">Capture lens</dt><dd>{m.lens?.capture}</dd></div>
      </dl>
      {m.thesis && Object.keys(m.thesis).length ? <p className="text-xs text-muted">Thesis snapshot: {Object.entries(m.thesis).map(([k, v]) => `${k.replace(/_/g, " ")} ${holds(v)}`).join(" · ")}</p> : null}
      <MemoBody body={m.body} obsIndex={obsIndex()} />
    </article>
  );
}
