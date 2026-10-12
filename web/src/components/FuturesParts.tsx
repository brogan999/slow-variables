import Link from "next/link";
import { futures, type FuForecast, type FuIdea, type FuMatrix } from "@/lib/data";

export const link = "underline decoration-grid underline-offset-4 hover:decoration-ink";

// An illustration, made with AI image generation and never evidence. The owner-made set is a stem with two WebP widths
// (scripts/futures_images.py); the generated set is one ready file, which the export names in full.
export function Plate({ src, file, alt, sizes = "(min-width: 768px) 480px, 100vw", eager = false, className = "" }: { src?: string | null; file?: string | null; alt: string; sizes?: string; eager?: boolean; className?: string }) {
  const one = !src && file;
  return (
    // eslint-disable-next-line @next/next/no-img-element -- static WebP in public/, served as written
    <img src={one ? file : `${src}-960.webp`} srcSet={one ? undefined : `${src}-480.webp 480w, ${src}-960.webp 960w`} sizes={one ? undefined : sizes} width={960} height={640} alt={alt} loading={eager ? "eager" : "lazy"} decoding="async" className={`w-full h-auto rounded-sm ${className}`} />
  );
}

export const Credit = () => <span className="text-[11px] text-muted">Illustration made with AI image generation; not evidence.</span>;

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

// a judged placing: solid, outlined or dashed, never a hue
const PRIZE: Record<string, string> = { vast: "bg-ink text-background", large: "border border-ink", small: "border border-axis text-ink-2", none: "border border-dashed border-axis text-muted" };

export function IdeaCard({ x }: { x: FuIdea }) {
  return (
    <article id={x.id} data-v={x.verdict?.key} className="fu-idea flex flex-col gap-1.5 py-3 border-t border-grid first:border-0 scroll-mt-8">
      {x.image || x.image_file ? <figure className="flex flex-col gap-0.5 max-w-[720px]"><Plate src={x.image} file={x.image_file} alt={`Illustration of ${x.name}: ${x.line}`} sizes="(min-width: 768px) 720px, 100vw" /><Credit /></figure> : null}
      <h3 className="font-medium text-[15px]">{x.name}</h3>
      <p className="text-[12px] text-muted">{x.work}{x.work ? ", " : ""}{x.author} · {x.imagined}</p>
      <p className="text-[14px] text-ink-2">{x.line}</p>
      <p className="text-[12px] text-ink-2">{x.built ? x.arrival : <>{x.arrival} · {x.judged}</>}</p>
      {x.verdict ? (
        <>
          <p className="mt-1 flex flex-wrap items-center gap-x-2.5 gap-y-1">
            <span className={`rounded-[2px] px-1.5 py-0.5 font-mono text-[11px] uppercase tracking-[0.06em] ${PRIZE[x.verdict.prize] ?? ""}`}>{x.verdict.prize_word}</span>
            <span className="text-[15px] font-semibold">{x.verdict.prize === "none" ? x.verdict.payer_word : <>{x.verdict.payer_word}; {x.verdict.seller_word}</>}</span>
            <span className="text-[12px] text-muted">as a model judges it</span>
          </p>
          <details className="text-[13px] text-ink-2">
            <summary className="cursor-pointer w-fit font-mono text-[11px] uppercase tracking-[0.08em] text-muted hover:text-ink">Why</summary>
            <div className="mt-1.5 flex flex-col gap-1.5 max-w-[66ch]">
              <p><span className="font-medium text-ink">{x.verdict.prize_word}.</span> {x.verdict.prize_why}</p>
              <p><span className="font-medium text-ink">Who is paid.</span> {x.verdict.money_why}</p>
              <p className="border-l-2 border-dotted border-axis pl-2 text-[12px] text-muted">A model&apos;s judgement, not a reading, of the idea as if it worked the way its story promises. The model is {x.verdict.sure} of this one.</p>
            </div>
          </details>
        </>
      ) : <p className="text-[12px] text-ink-2">Profit, as AI models judge it: {x.profit}</p>}
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

// A category's ideas counted by prize and by which seller keeps the rest (Part 54). A radio in each cell filters the
// cards below with CSS alone; the rules are written from the table, so the page runs no script and computes nothing.
export function VerdictTable({ m, n }: { m: FuMatrix; n: number }) {
  const cells = m.rows.flatMap((r) => r.cells).filter((c) => c.n);
  const css = cells.map((c) => `.fu-verdicts:has(#fv-${c.key}:checked) .fu-idea:not([data-v="${c.key}"]) { display: none; }`).join("\n");
  return (
    <section className="fig p-4 flex flex-col gap-3" role="radiogroup" aria-labelledby="fv-h">
      <style>{css}</style>
      <div>
        <h2 id="fv-h" className="text-[1.1rem] font-semibold leading-tight">How large a prize, and which seller keeps the rest</h2>
        <p className="mt-1 text-[13px] text-ink-2 max-w-[70ch]">Each idea is judged as if it worked the way its story promises: how large a prize it would be, who would pay, and which seller would keep what is left once buyers have had their gain. Choose a cell to see only those ideas; each count is the cards that cell shows. Every placing is a model&apos;s judgement, not a reading.</p>
      </div>
      <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Prize by seller">
        <table className="w-full min-w-[25rem] border-collapse text-[13px]">
          <thead>
            <tr>
              <th scope="col" className="border border-grid bg-background px-2 py-1.5 text-left text-[11px] font-semibold uppercase tracking-[0.06em] text-muted">Seller</th>
              {m.prizes.map((p) => <th key={p.id} scope="col" title={p.means} className="border border-grid bg-background px-2 py-1.5 text-left text-[11px] font-semibold uppercase tracking-[0.06em] text-muted">{p.word}</th>)}
            </tr>
          </thead>
          <tbody>
            {m.rows.map((r) => (
              <tr key={r.id}>
                <th scope="row" title={r.means} className="border border-grid bg-background px-2 py-1.5 text-left text-[12px] font-medium">{r.word}</th>
                {r.cells.map((c, i) => (
                  <td key={c.key} className="border border-grid p-0">
                    {c.n ? (
                      <label className="fu-cell flex cursor-pointer items-center gap-2 px-2 py-1.5 font-mono text-[14px]">
                        <input type="radio" name="fu-verdict" id={`fv-${c.key}`} className="accent-ink" />
                        {c.n}<span className="sr-only"> ideas: {m.prizes[i].word}, {r.word.toLowerCase()}</span>
                      </label>
                    ) : <span className="block px-2 py-1.5 font-mono text-[14px] text-axis" aria-hidden>·</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-ink-2">
        <label className="inline-flex cursor-pointer items-center gap-1.5 font-medium"><input type="radio" name="fu-verdict" id="fv-all" defaultChecked className="accent-ink" />All {n}</label>
      </p>
    </section>
  );
}
