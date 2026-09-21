import Link from "next/link";
import { ArticleLayout } from "@/components/ArticleLayout";
import { Folios, Inline, parseEssay } from "@/components/Essay";
import { MigrationMargin, Predictions, ScorecardPlate, StripPlate } from "@/components/MigrationParts";
import { argument } from "@/lib/data";
import { SITE } from "@/lib/site";

const title = "The migrating bottleneck";
const description = "Whichever input to AI is hardest to get sets the pace and collects the profit, until the industry builds its way out and the shortage moves. Where it has sat, where it sits now, and what would prove that wrong.";
// a page's openGraph replaces the site's wholesale, so the share image is named again here
export const metadata = {
  title,
  description,
  openGraph: { title: `${title} · ${SITE.name}`, description, url: "/argument/migration", siteName: SITE.name, type: "article", images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: SITE.name }] },
};

export default function MigrationPage() {
  const doc = argument();
  const m = doc.migration;
  const { title: h1, lede, folios } = parseEssay(doc.essay.migration);
  const plates = { strip: <StripPlate strip={m.strip} />, scorecard: <ScorecardPlate card={m.scorecard} /> };
  return (
    <ArticleLayout
      head={
        <header className="flex flex-col gap-5 pt-4 md:pt-10">
          <div className="eyebrow"><Link href="/argument" className="hover:text-ink">The argument</Link> · what is scarce</div>
          <h1 className="display text-[2.75rem] md:text-[4.5rem] leading-[0.98] max-w-[16ch]">{h1}</h1>
          <p className="font-serif text-xl md:text-[1.4rem] leading-[1.55] text-ink-2 max-w-[60ch]"><Inline text={lede} facts={m.facts} /></p>
        </header>
      }
      margin={<MigrationMargin doc={m} />}
    >
      <Folios folios={folios} facts={m.facts} plates={plates} />
      <section id="predictions" className="mt-16 scroll-mt-8">
        <h2 className="eyebrow mb-2">The predictions, re-tested every night</h2>
        <p className="font-serif text-[1.0625rem] leading-relaxed text-ink-2 max-w-[62ch] mb-2">These are this site&apos;s own calls. The <Link href="/predictions" className="underline decoration-axis underline-offset-2 hover:decoration-ink">predictions ledger</Link> is a different thing: it scores what other people have forecast.</p>
        <Predictions doc={m} />
      </section>
      <section id="sources" className="mt-20 border-t border-grid pt-8 scroll-mt-8">
        <h2 className="display text-[1.5rem] mb-4">Sources</h2>
        <ol className="flex flex-col gap-3 font-serif text-[1.0625rem] leading-relaxed">
          {m.sources.map((s) => (
            <li key={s.url}>{s.who}, <a href={s.url} className="italic underline decoration-axis underline-offset-2 hover:decoration-ink">{s.work}</a>, {s.where}.</li>
          ))}
        </ol>
      </section>
    </ArticleLayout>
  );
}
