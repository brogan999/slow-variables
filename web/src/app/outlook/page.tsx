import { ArticleLayout } from "@/components/ArticleLayout";
import { StackPlate } from "@/components/ArgumentParts";
import { ContextFigures } from "@/components/ContextFigure";
import { Folios, folioId, Inline, parseEssay } from "@/components/Essay";
import { Agreements, ClaimState, cites, FalsifierBoard, FolioPositions, OutlookMargin, OutlookSources, ScenarioGrid } from "@/components/OutlookParts";
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
          <div role="group" aria-label="Tonight's claims" className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
            {(["holding", "failing", "both", "untestable"] as const).map((k) => <span key={k} className="inline-flex items-center gap-1.5"><ClaimState state={k} /><span className="num text-ink-2">{doc.tally[k]}</span></span>)}
          </div>
          <nav aria-label="The five questions" className="max-w-[62ch]">
            <ol className="flex flex-col gap-1.5 border-l border-grid pl-4 text-[15px]">
              {folios.filter((f) => f.label.startsWith("Folio ")).map((f, i) => (
                <li key={f.label}><a href={`#${folioId(f.label)}`} className="hover:underline"><span className="eyebrow mr-2">{f.label.split("·")[0].trim()}</span>{doc.folios[i]?.kicker ?? f.claim}</a></li>
              ))}
            </ol>
          </nav>
        </header>
      }
      margin={<OutlookMargin doc={doc} />}
    >
      <Folios folios={folios} facts={doc.facts} plates={plates} cites={cites(doc)} tests={doc.tests} after={after} />
      <section id="sources" className="mt-20 border-t border-grid pt-8 scroll-mt-8">
        <h2 className="display text-[1.5rem] mb-4">Sources</h2>
        <OutlookSources doc={doc} />
      </section>
    </ArticleLayout>
  );
}
