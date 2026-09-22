import Link from "next/link";
import { ArticleLayout } from "@/components/ArticleLayout";
import { StackPlate } from "@/components/ArgumentParts";
import { ContextFigures } from "@/components/ContextFigure";
import { Folios, Inline, parseEssay } from "@/components/Essay";
import { Agreements, cites, FalsifierBoard, FolioPositions, OutlookMargin, OutlookSources, ScenarioGrid } from "@/components/OutlookParts";
import { JaggedFrontier, ReliabilityGap } from "@/components/Signposts";
import { bottleneckMap, context, outlook, signposts } from "@/lib/data";
import { SITE } from "@/lib/site";

const title = "What happens from here";
const description = "Where the people who think hardest about AI agree and disagree on what comes next, the claims each side makes, tonight's reading of every claim, and the reading that would tell the sides apart.";
// a page's openGraph replaces the site's wholesale, so the share image is named again here
export const metadata = {
  title,
  description,
  openGraph: { title: `${title} · ${SITE.name}`, description, url: "/outlook", siteName: SITE.name, type: "article", images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: SITE.name }] },
};

export default function OutlookPage() {
  const doc = outlook();
  const sp = signposts();
  const rows = Object.fromEntries(bottleneckMap().groups.flatMap((g) => g.sections.flatMap((s) => s.rows.map((r) => [r.id, r.name]))));
  const { title: h1, lede, folios } = parseEssay(doc.essay);
  const plates = {
    reliability: sp.reliability ? <ReliabilityGap doc={sp} /> : null,
    frontier: <JaggedFrontier doc={sp} />,
    adoption: <ContextFigures figures={context().figures.filter((f) => f.id === "adoption_measures")} />,
    stack: <StackPlate />,
    scenarios: <ScenarioGrid doc={doc} rows={rows} />,
    board: <FalsifierBoard doc={doc} />,
  };
  const after = (label: string, i: number) => {
    const fo = label.startsWith("Folio ") ? doc.folios[i] : undefined;
    if (fo) return <FolioPositions doc={doc} folio={fo.id} />;
    return label === "Where they agree" ? <Agreements doc={doc} /> : null;
  };
  return (
    <ArticleLayout
      head={
        <header className="flex flex-col gap-5 pt-4 md:pt-10">
          <div className="eyebrow">What next · the outlook, tested nightly</div>
          <h1 className="display text-[2.75rem] md:text-[4.5rem] leading-[0.98] max-w-[16ch]">{h1}</h1>
          <p className="font-serif text-xl md:text-[1.4rem] leading-[1.55] text-ink-2 max-w-[60ch]"><Inline text={lede} facts={doc.facts} cites={cites(doc)} tests={doc.tests} /></p>
        </header>
      }
      margin={<OutlookMargin doc={doc} />}
    >
      <Folios folios={folios} facts={doc.facts} plates={plates} cites={cites(doc)} tests={doc.tests} after={after} />
      <p className="mt-12 font-serif text-[1.0625rem] leading-relaxed text-ink-2 max-w-[62ch]">
        Read next: <Link href="/bottlenecks" className="underline decoration-axis underline-offset-2 hover:decoration-ink">the bottleneck map</Link>, where these claims mark the stage each expects to bind, and <Link href="/argument" className="underline decoration-axis underline-offset-2 hover:decoration-ink">the argument</Link> this site tests.
      </p>
      <section id="sources" className="mt-20 border-t border-grid pt-8 scroll-mt-8">
        <h2 className="display text-[1.5rem] mb-4">Sources</h2>
        <OutlookSources doc={doc} />
      </section>
    </ArticleLayout>
  );
}
