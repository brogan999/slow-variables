import Link from "next/link";
import { notFound } from "next/navigation";
import { DataMarketNav } from "@/components/DataMarketNav";
import { dataMarketDossiers } from "@/lib/data";

export const dynamicParams = false;
export const generateStaticParams = () => dataMarketDossiers().map((d) => ({ id: d.id }));

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const d = dataMarketDossiers().find((x) => x.id === id);
  return { title: d ? `${d.title} · the data market` : "The data market", description: d ? `A dossier on one kind of record that could be training data for AI: ${d.title}.` : undefined };
}

const link = "underline decoration-grid underline-offset-4";
const TOKEN = /(\[[a-z0-9][a-z0-9-]*\]|\*\*[^*]+\*\*)/g;

// Prose with its two marks: **a lead-in** and [a source], which becomes the source's number in the margin list.
function Inline({ text, number }: { text: string; number: Record<string, number> }) {
  return (
    <>
      {text.split(TOKEN).map((p, i) => {
        if (p.startsWith("**")) return <strong key={i} className="font-semibold text-ink">{p.slice(2, -2)}</strong>;
        const key = p.match(/^\[([a-z0-9][a-z0-9-]*)\]$/)?.[1];
        if (!key) return <span key={i}>{p}</span>;
        return number[key] ? <sup key={i} className="ml-px"><a href={`#source-${key}`} className="num text-[0.7em] text-ink-2 no-underline hover:text-ink">{number[key]}</a></sup> : null;
      })}
    </>
  );
}

export default async function DataMarketDossierPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const d = dataMarketDossiers().find((x) => x.id === id);
  if (!d) notFound();
  const number = Object.fromEntries(d.sources.map((s) => [s.key, s.n]));
  return (
    <div className="flex flex-col gap-8 max-w-[72rem]">
      <DataMarketNav here="/data-market/dossiers" />
      <div className="flex flex-col gap-3">
        <span className="eyebrow"><Link href="/data-market" className="hover:text-ink">The data market</Link> · <Link href="/data-market/dossiers" className="hover:text-ink">dossier {d.n}</Link></span>
        <h1 className="display text-[2.25rem] md:text-[3.25rem] leading-[1.04] max-w-[24ch]">{d.title}</h1>
      </div>
      <div className="grid grid-cols-1 gap-x-12 gap-y-8 lg:grid-cols-[minmax(0,1fr)_19rem]">
        <article className="prose-folio max-w-[66ch]">
          {d.blocks.map((b, i) => {
            if (b.kind === "h2") return <h2 key={i} className="display mt-8 text-2xl first:mt-0">{b.text}</h2>;
            if (b.kind === "h3") return <h3 key={i} className="mt-4 text-base font-semibold text-ink">{b.text}</h3>;
            if (b.kind === "ul") return <ul key={i} className="list-disc pl-5">{b.items?.map((t, j) => <li key={j}><Inline text={t} number={number} /></li>)}</ul>;
            if (b.kind === "judgement")
              return (
                <aside key={i} className="my-6 border-l-2 border-dotted border-axis pl-4 font-sans text-[15px] leading-relaxed text-ink-2">
                  <span className="text-muted">A model&apos;s judgement, not a reading: </span>{b.text}
                  <span className="mt-1.5 block text-xs text-muted">{b.by || "Claude, a model made by Anthropic, judged this; a separate run of the same model reviewed it."}</span>
                </aside>
              );
            return <p key={i}><Inline text={b.text ?? ""} number={number} /></p>;
          })}
        </article>
        <aside className="flex flex-col gap-3 self-start text-[12.5px] leading-snug text-ink-2 lg:sticky lg:top-6">
          <div className="panel p-4">
            <h2 className="eyebrow mb-2">Sources</h2>
            <ol className="flex flex-col gap-2">
              {d.sources.map((s) => (
                <li key={s.key} id={`source-${s.key}`} className="scroll-mt-24 grid grid-cols-[1.4rem_1fr] gap-x-1 [overflow-wrap:anywhere]">
                  <span className="num text-muted">{s.n || "·"}</span>
                  <span>
                    <a href={s.url} rel="nofollow noopener" className={link}>{s.name}</a>
                    <span className="num block text-[11px] text-muted">read {s.retrieved_at}</span>
                  </span>
                </li>
              ))}
            </ol>
          </div>
          <p className="px-1 text-xs text-muted">This page was written by Claude, a model made by Anthropic, from the sources listed. Every figure is stated on a page cited in its sentence. <Link href="/methodology#company-claims" className={link}>How this is made</Link>.</p>
        </aside>
      </div>
    </div>
  );
}
