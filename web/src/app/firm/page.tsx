import Link from "next/link";
import { ArticleLayout } from "@/components/ArticleLayout";
import { Folios, folioId, Inline, parseEssay } from "@/components/Essay";
import { CensusCutPlate, FirmMargin, RegimesPlate, SeatedPositions, ShapesPlate } from "@/components/FirmParts";
import { ClaimState, cites, OutlookSources } from "@/components/OutlookParts";
import { Anatomy } from "@/components/FirmKinds";
import { firm, firmKinds } from "@/lib/data";
import { SITE } from "@/lib/site";

const title = "Who owns what";
const description = "Where a firm's boundary moves when intelligence is bought by the token: why most firms should rent it, where owning wins, what stays scarce, and what would prove each claim wrong.";
// a page's openGraph replaces the site's wholesale, so the share image is named again here
export const metadata = {
  title,
  description,
  openGraph: { title: `${title} · ${SITE.name}`, description, url: "/firm", siteName: SITE.name, type: "article", images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: SITE.name }] },
};

export default function FirmPage() {
  const doc = firm();
  const { title: h1, lede, folios } = parseEssay(doc.essay);
  const c = cites(doc);
  return (
    <ArticleLayout
      head={
        <header className="flex flex-col gap-5 pt-4 md:pt-10">
          <div className="eyebrow">The money · the firm, argued from the outlook&apos;s claims</div>
          <h1 className="display text-[2.5rem] md:text-[4rem] leading-[1] max-w-[18ch]">{h1}</h1>
          <p className="font-serif text-xl md:text-[1.4rem] leading-[1.55] text-ink-2 max-w-[60ch]"><Inline text={lede} facts={doc.facts} cites={c} tests={doc.tests} /></p>
          <p className="text-[15px] text-ink-2 max-w-[60ch]">The specifics, in figures: <Link href="/firm/kinds" className="text-ink underline decoration-axis underline-offset-4">what happens to each kind of firm</Link>, what an AI-run firm looks like, and what such firms will need to buy.</p>
          <div role="group" aria-label="Tonight's claims on this page" className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
            {(["holding", "failing", "both", "untestable"] as const).map((k) => <span key={k} className="inline-flex items-center gap-1.5"><ClaimState state={k} /><span className="num text-ink-2">{doc.tally[k]}</span></span>)}
          </div>
        </header>
      }
      margin={<FirmMargin doc={doc} />}
    >
      <Folios folios={folios} facts={doc.facts} plates={{ regimes: <RegimesPlate regimes={doc.regimes} />, shapes: <ShapesPlate doc={doc} />, jobs: <CensusCutPlate cut={doc.census_cut} />, anatomy: <Anatomy doc={firmKinds()} /> }} cites={c} tests={doc.tests} after={(label) => <SeatedPositions doc={doc} folio={folioId(label).replace(/^folio-/, "")} />} />
      <section id="sources" className="mt-20 border-t border-grid pt-8 scroll-mt-8">
        <h2 className="display text-[1.5rem] mb-4">Sources</h2>
        <OutlookSources doc={doc} />
      </section>
    </ArticleLayout>
  );
}
