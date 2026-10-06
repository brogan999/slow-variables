import Link from "next/link";
import { ArticleLayout, MarginPanel } from "@/components/ArticleLayout";
import { Plate as AtlasPlate } from "@/components/AtlasParts";
import { Plate as FuturesPlate } from "@/components/FuturesParts";
import { DueLines, FictionLag, LaneSpread, SaidAgainstGiven, WorldsGrid } from "@/components/LongRunFigures";
import { Scrubber } from "@/components/Scrubber";
import { Due, Fiction, Latest, ORDER, Questions, Sources, TimelinePlate, Undated, Worlds } from "@/components/SingularityParts";
import { atlas, futures, singularity } from "@/lib/data";
import { fmt } from "@/lib/format";
import { SITE } from "@/lib/site";

const title = "Timelines to the singularity";
const description = "The people who have dared to date the arrival of machines smarter than us, from the 1960s to this year, on one timeline, each read against what this site measures tonight.";
// a page's openGraph replaces the site's wholesale, so the share image is named again here
export const metadata = {
  title,
  description,
  openGraph: { title: `${title} · ${SITE.name}`, description, url: "/singularity", siteName: SITE.name, type: "article", images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: SITE.name }] },
};

function Folio({ n, id, label, title: h, children, lede }: { n: string; id: string; label: string; title: string; lede?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className="mt-16 scroll-mt-8">
      <div className="gild-rule mb-6" aria-hidden />
      <p className="eyebrow mb-1"><span className="text-gild-ink">{n}</span> · {label}</p>
      <h2 id={`${id}-h`} className="display text-[1.75rem] md:text-[2.1rem] leading-tight mb-3">{h}</h2>
      {lede ? <p className="font-serif text-[1.0625rem] leading-relaxed text-ink-2 max-w-[62ch] mb-4">{lede}</p> : null}
      {children}
    </section>
  );
}

export default function SingularityPage() {
  const d = singularity();
  const fu = futures();
  const at = atlas();
  return (
    <ArticleLayout
      head={
        <header className="flex flex-col gap-5 pt-4 md:pt-10">
          <div className="eyebrow">What next · the long view</div>
          <h1 className="display text-[2.75rem] md:text-[4.25rem] leading-[0.98] max-w-[16ch]">{title}</h1>
          <p className="drop-cap font-serif text-xl md:text-[1.35rem] leading-[1.55] text-ink max-w-[60ch]">{d.intro}</p>
        </header>
      }
      margin={<>
        <MarginPanel title={<>Reading · {d.as_of}</>}>
          <Scrubber stops={d.stops} tallies={d.tallies} words={d.words} order={ORDER} />
        </MarginPanel>
        <MarginPanel title="Instrument">
          <p className="text-sm leading-relaxed">Every forecast here is a dated prediction in <Link href="/predictions#singularity-ledger" className="underline decoration-axis underline-offset-2 hover:decoration-ink">the ledger</Link>, in this site&apos;s words, with its source, its test and a reasoned status. Slide the year to see what had been forecast by then.</p>
          <p className="text-sm leading-relaxed mt-2"><Link href="/methodology#singularity" className="underline decoration-axis underline-offset-2 hover:decoration-ink">How forecasts are placed and scored →</Link></p>
        </MarginPanel>
      </>}
    >
      <Folio n="I" id="timeline" label="the timeline" title="The dates people have dared to give, on one line" lede="Each row is a milestone; each mark, one forecaster's year for it. The glyph is how the forecast reads tonight.">
        <TimelinePlate doc={d} />
        <details className="mt-4">
          <summary className="cursor-pointer text-sm text-ink-2">Calls that give odds, or doubt a date, but name no year</summary>
          <div className="mt-3"><Undated doc={d} /></div>
        </details>
        <LaneSpread doc={d} />
        <SaidAgainstGiven doc={d} />
      </Folio>
      <section aria-labelledby="beyond" className="mt-12 flex flex-col gap-4">
        <h2 id="beyond" className="eyebrow">Beyond the dated calls</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <Link href="/futures" className="group panel flex flex-col gap-3 p-4">
            {fu.featured[0]?.image ? <FuturesPlate src={fu.featured[0].image} alt={fu.featured[0].line} sizes="(min-width: 768px) 420px, 100vw" /> : null}
            <span className="font-sans text-lg font-semibold group-hover:underline">Futures: every technology fiction has imagined</span>
            <span className="text-[15px] text-ink-2"><span className="num">{fmt(fu.n_ideas, "count")}</span> inventions from novels and stories, when each was imagined, whether it was built, and who would keep the profit.</span>
          </Link>
          <Link href="/singularity/atlas" className="group panel flex flex-col gap-3 p-4">
            <AtlasPlate p={at.hero} sizes="(min-width: 768px) 420px, 100vw" decorative />
            <span className="font-sans text-lg font-semibold group-hover:underline">The atlas: how each part of life changes</span>
            <span className="text-[15px] text-ink-2">Work, money, health, politics and more, era by era, from what sourced writers expect.</span>
          </Link>
        </div>
        <p className="font-mono text-[11px] text-muted">The pictures are illustrations made with image models, not evidence.</p>
      </section>
      <Folio n="II" id="due" label="the calls whose time has come" title="The dates that have already come" lede="Forecasts whose window has closed. Happening means the milestone arrived as said; slower than said means its date passed without it.">
        <DueLines doc={d} />
        <Due doc={d} />
      </Folio>
      <Folio n="III" id="now" label="where the forecasters sit now" title="The latest word from each forecaster" lede="The most recent year each forecaster has given for each milestone, among forecasts made since 2023. The glyph is how the forecast reads tonight; each links to it.">
        <Latest doc={d} />
      </Folio>
      <Folio n="IV" id="watch" label="ten things to watch" title="What would tell the fast story from the slow one" lede="Each question names what this site reads tonight, and what a fast or a slow answer would look like.">
        <Questions doc={d} />
      </Folio>
      <Folio n="V" id="worlds" label="four worlds for 2036" title="Four ways the next decade could go" lede={<>Each world maps onto the cells of the <Link href="/outlook#scenarios" className="underline decoration-axis underline-offset-2 hover:decoration-ink">scenario grid</Link>. None is crowned: a world reads consistent until one of its signposts fails. <Link href="/singularity/atlas" className="underline decoration-axis underline-offset-2 hover:decoration-ink">What each world would change, part of life by part of life →</Link></>}>
        <WorldsGrid doc={d} />
        <Worlds doc={d} />
      </Folio>
      <Folio n="VI" id="fiction" label="imagined futures" title="What the novelists imagined" lede="Stories, not forecasts: none is scored. Those set in a named year sit on the timeline's last row.">
        <Fiction doc={d} />
        <FictionLag doc={d} credits={fu.credits} />
      </Folio>
      <section id="sources" className="mt-20 border-t border-grid pt-8 scroll-mt-8">
        <h2 className="display text-[1.5rem] mb-4">Sources</h2>
        <Sources doc={d} />
      </section>
    </ArticleLayout>
  );
}
