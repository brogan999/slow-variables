import Link from "next/link";
import { ArticleLayout, MarginPanel } from "@/components/ArticleLayout";
import { AtlasMap, Plate, PlateCards } from "@/components/AtlasParts";
import { atlas } from "@/lib/data";
import { SITE } from "@/lib/site";

const title = "How the world changes";
const description = "What named writers expect AI to change in money, work, meaning, power, war, science, health and daily life, by era and by which future they assume, beside the public series this site reads for each.";
export const metadata = {
  title,
  description,
  openGraph: { title: `${title} · ${SITE.name}`, description, url: "/singularity/atlas", siteName: SITE.name, type: "article", images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: SITE.name }] },
};
const link = "underline decoration-axis underline-offset-2 hover:decoration-ink";

export default function AtlasPage() {
  const d = atlas();
  return (
    <ArticleLayout
      head={
        <header className="flex flex-col gap-5 pt-4 md:pt-10">
          <nav aria-label="Breadcrumb" className="eyebrow"><Link href="/singularity" className={link}>Singularity</Link> / Atlas</nav>
          <h1 className="display text-[2.75rem] md:text-[4.25rem] leading-[0.98] max-w-[16ch]">{title}</h1>
          <p className="drop-cap font-serif text-xl md:text-[1.35rem] leading-[1.55] text-ink max-w-[60ch]">{d.intro}</p>
          <figure className="panel overflow-hidden mt-2">
            <Plate p={d.hero} sizes="(min-width: 1024px) 760px, 100vw" eager className="aspect-[16/9] object-cover" />
            <figcaption className="px-4 py-2 text-xs text-ink-2">{d.hero.caption}</figcaption>
          </figure>
        </header>
      }
      margin={<>
        <MarginPanel title="Instrument" rows={[["Expectations", d.count.expectations], ["Sourced works", d.count.sources], ["Parts of life", d.count.domains]]}>
          <p>Each expectation is a writer&apos;s view in this site&apos;s words, credited and linked. None is scored: most name no date and no test, so they sit here rather than on <Link href="/predictions" className={link}>the predictions board</Link>.</p>
          <p><Link href="/methodology#atlas" className={link}>How the atlas is built →</Link></p>
        </MarginPanel>
        <MarginPanel title="The worlds">
          <ul className="flex flex-col gap-1">{d.worlds.map((w) => <li key={w.id}>{w.label}</li>)}</ul>
          <p><Link href="/singularity#worlds" className={link}>The worlds, argued</Link> · <Link href="/outlook#scenarios" className={link}>the scenario grid</Link></p>
        </MarginPanel>
      </>}
    >
      <section id="map" aria-labelledby="map-h" className="scroll-mt-8">
        <div className="gild-rule mb-6" aria-hidden />
        <p className="eyebrow mb-1"><span className="text-gild-ink">I</span> · the map</p>
        <h2 id="map-h" className="display text-[1.75rem] md:text-[2.1rem] leading-tight mb-3">Where the sourced works expect change, and when</h2>
        <p className="font-serif text-[1.0625rem] leading-relaxed text-ink-2 max-w-[62ch] mb-4">Rows are parts of life, columns are eras. Pick a world to see only the works that assume it; open a cell to read them.</p>
        <AtlasMap doc={d} />
      </section>
      <section id="plates" aria-labelledby="plates-h" className="mt-16 scroll-mt-8">
        <div className="gild-rule mb-6" aria-hidden />
        <p className="eyebrow mb-1"><span className="text-gild-ink">II</span> · the plates</p>
        <h2 id="plates-h" className="display text-[1.75rem] md:text-[2.1rem] leading-tight mb-5">Eight parts of life</h2>
        <PlateCards doc={d} />
      </section>
      <p className="mt-12 text-xs text-ink-2 max-w-[62ch]">{d.provenance}</p>
    </ArticleLayout>
  );
}
