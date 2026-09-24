import Link from "next/link";
import { futures, type FuForecast, type FuIdea } from "@/lib/data";

export const link = "underline decoration-grid underline-offset-4 hover:decoration-ink";

// An illustration: two WebP widths written by scripts/futures_images.py; made in ChatGPT, never evidence.
export function Plate({ src, alt, sizes = "(min-width: 768px) 480px, 100vw", eager = false, className = "" }: { src: string; alt: string; sizes?: string; eager?: boolean; className?: string }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element -- static WebP pairs in public/, served as written
    <img src={`${src}-960.webp`} srcSet={`${src}-480.webp 480w, ${src}-960.webp 960w`} sizes={sizes} width={960} height={640} alt={alt} loading={eager ? "eager" : "lazy"} decoding="async" className={`w-full h-auto rounded-sm ${className}`} />
  );
}

export const Credit = () => <span className="text-[11px] text-muted">Illustrations made by the site&apos;s owner with ChatGPT image generation; not evidence.</span>;

// Every Futures page names where the ideas come from: names, works, authors and years are the glossary's.
export function Sources() {
  const [glossary, bank] = futures().credits;
  const a = (c: { name: string; url: string; archived: boolean }) => <><a href={c.url} className={link}>{c.name}</a>{c.archived ? " (archived copy)" : ""}</>;
  return (
    <p className="text-[12px] text-muted max-w-[66ch]">
      Ideas from {a(glossary)}, as compiled in {a(bank)}; names, works, authors and years are theirs and every description is this site&apos;s rewording. Categories, arrival decades and profit are judged by AI models, not people. <Link href="/methodology#futures" className={link}>Method</Link>
    </p>
  );
}

export function IdeaCard({ x }: { x: FuIdea }) {
  return (
    <article id={x.id} className="flex flex-col gap-1.5 py-3 border-t border-grid first:border-0 scroll-mt-8">
      {x.image ? <figure className="flex flex-col gap-0.5 max-w-[360px]"><Plate src={x.image} alt={`Illustration of ${x.name}: ${x.line}`} sizes="(min-width: 768px) 360px, 100vw" /><Credit /></figure> : null}
      <h3 className="font-medium text-[15px]">{x.name}</h3>
      <p className="text-[12px] text-muted">{x.work}{x.work ? ", " : ""}{x.author} · {x.imagined}</p>
      <p className="text-[14px] text-ink-2">{x.line}</p>
      <p className="text-[12px] text-ink-2">{x.built ? x.arrival : <>{x.arrival} · {x.judged}</>}</p>
      <p className="text-[12px] text-ink-2">Profit, as AI models judge it: {x.profit}</p>
    </article>
  );
}

export function ForecastRow({ f }: { f: FuForecast }) {
  return (
    <li id={f.id} className="py-3 border-t border-grid first:border-0 scroll-mt-8">
      <p className="text-[15px]">{f.line}</p>
      <p className="text-[12px] text-ink-2 mt-1">
        <strong className="font-medium text-ink">{f.who}</strong> · {f.when}{f.odds ? ` · ${f.odds}` : ""}
        {f.quote ? <> · <q>{f.quote}</q></> : null}
        {f.ledger ? <> · <Link href={f.ledger} className={link}>on the prediction ledger</Link></> : null}
      </p>
      <p className="text-[11px] text-muted mt-0.5">From {f.works.map((w, i) => <span key={w.title}>{i ? "; " : ""}{w.url ? <a href={w.url} className={link}>{w.title}</a> : <em>{w.title}</em>}, {w.author}, {w.year}</span>)}</p>
    </li>
  );
}
