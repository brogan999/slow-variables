import Link from "next/link";
import { notFound } from "next/navigation";
import { ArticleLayout, MarginPanel } from "@/components/ArticleLayout";
import { EraSection, Plate, Reading, roman } from "@/components/AtlasParts";
import { atlas } from "@/lib/data";
import { SITE } from "@/lib/site";

export const dynamicParams = false;
export function generateStaticParams() { return atlas().domains.map((d) => ({ domain: d.id })); }
export async function generateMetadata({ params }: { params: Promise<{ domain: string }> }) {
  const { domain } = await params;
  const d = atlas().domains.find((x) => x.id === domain);
  const title = d ? `${d.name}: how it changes` : "Atlas";
  return {
    title,
    description: d?.thesis,
    openGraph: { title: `${title} · ${SITE.name}`, description: d?.thesis, url: `/singularity/atlas/${domain}`, siteName: SITE.name, type: "article", images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: SITE.name }] },
  };
}
const link = "underline decoration-axis underline-offset-2 hover:decoration-ink";

export default async function AtlasDomainPage({ params }: { params: Promise<{ domain: string }> }) {
  const { domain } = await params;
  const doc = atlas();
  const d = doc.domains.find((x) => x.id === domain);
  if (!d) notFound();
  const name = (id: string | null) => doc.domains.find((x) => x.id === id)?.name;
  return (
    <ArticleLayout
      head={
        <header className="flex flex-col gap-5 pt-4 md:pt-10">
          <nav aria-label="Breadcrumb" className="eyebrow"><Link href="/singularity" className={link}>Singularity</Link> / <Link href="/singularity/atlas" className={link}>Atlas</Link> / <span className="text-gild-ink">{roman(d.n)}</span></nav>
          <h1 className="display text-[2.5rem] md:text-[3.75rem] leading-[1] max-w-[18ch]">{d.name}</h1>
          <p className="drop-cap font-serif text-xl md:text-[1.3rem] leading-[1.55] text-ink max-w-[60ch]">{d.thesis}</p>
          <p className="text-sm text-ink-2">After {d.thesis_from.join(", ")}.</p>
          <figure className="panel overflow-hidden mt-2 max-w-[400px]">
            <Plate p={d.plate} sizes="(min-width: 640px) 400px, 100vw" eager />
            <figcaption className="px-4 py-2 text-xs text-ink-2">{d.plate.allegory}. An illustration made with an image model, not evidence.</figcaption>
          </figure>
        </header>
      }
      margin={<>
        <MarginPanel title="Already moving">
          {d.readings.length ? d.readings.map((r) => <Reading key={r.id} r={r} />) : <p>No public series yet. Nothing this site reads measures this part of life.</p>}
        </MarginPanel>
        <MarginPanel title="Eras">
          <ul className="flex flex-col gap-1">{d.eras.map((e) => <li key={e.id}><a href={`#${e.id}`} className={link}>{e.label}</a> <span className="text-muted">· {e.entries.length}</span></li>)}</ul>
        </MarginPanel>
        <MarginPanel title="Parts of life">
          <ol className="flex flex-col gap-1">{doc.domains.map((x) => <li key={x.id}>{x.id === d.id ? <span aria-current="page" className="text-ink font-medium">{x.name}</span> : <Link href={`/singularity/atlas/${x.id}`} className={link}>{x.name}</Link>}</li>)}</ol>
        </MarginPanel>
      </>}
    >
      {d.eras.map((e) => <EraSection key={e.id} era={e} />)}
      {d.disagreement ? (
        <section aria-labelledby="split-h" className="mt-14">
          <div className="gild-rule mb-5" aria-hidden />
          <h2 id="split-h" className="display text-[1.6rem] leading-tight">Where they split</h2>
          <p className="font-serif text-[1.1rem] mt-2">{d.disagreement.question}</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {d.disagreement.sides.map((s, i) => (
              <div key={i} className="panel p-4">
                <p className="font-serif text-[1rem] leading-relaxed">{s.view}</p>
                <p className="mt-2 text-xs text-ink-2">{s.who.join("; ")}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}
      {d.fiction.length ? (
        <section aria-labelledby="fic-h" className="mt-14">
          <div className="gild-rule mb-5" aria-hidden />
          <h2 id="fic-h" className="display text-[1.6rem] leading-tight">The novelists&apos; version</h2>
          <p className="text-sm text-ink-2 mt-1">Stories, not forecasts: none is counted on the map.</p>
          <ul className="mt-3 grid gap-x-8 sm:grid-cols-2">
            {d.fiction.map((f) => (
              <li key={f.href} className="border-t border-grid py-2.5">
                <p className="font-serif"><Link href={f.href} className={`italic ${link}`}>{f.title}</Link> <span className="text-ink-2">· {f.author}, {f.year}</span></p>
                <p className="text-sm text-ink-2 mt-0.5">{f.line}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      {d.leaning.length ? (
        <section aria-labelledby="lean-h" className="mt-14">
          <div className="gild-rule mb-5" aria-hidden />
          <h2 id="lean-h" className="display text-[1.6rem] leading-tight">Dated predictions on the same readings</h2>
          <ul className="mt-3">
            {d.leaning.map((r) => <li key={r.id} className="border-t border-grid py-2.5 text-sm"><Link href={r.href} className={link}>{r.line}</Link> <span className="text-ink-2">· {r.who}</span></li>)}
          </ul>
        </section>
      ) : null}
      <section aria-labelledby="src-h" className="mt-16 border-t border-grid pt-8">
        <h2 id="src-h" className="display text-[1.4rem] mb-3">Sources</h2>
        <ol className="flex flex-col gap-2 font-serif text-[0.98rem]">
          {d.sources.map((s) => <li key={s.id}>{s.who}, <a href={s.url} className={`italic ${link}`}>{s.work}</a>, {s.year}.</li>)}
        </ol>
      </section>
      <nav aria-label="Other parts of life" className="mt-12 flex justify-between gap-4 text-sm">
        {d.prev ? <Link href={`/singularity/atlas/${d.prev}`} className={link}>← {name(d.prev)}</Link> : <span />}
        {d.next ? <Link href={`/singularity/atlas/${d.next}`} className={link}>{name(d.next)} →</Link> : <Link href="/singularity/atlas" className={link}>Back to the map →</Link>}
      </nav>
    </ArticleLayout>
  );
}
