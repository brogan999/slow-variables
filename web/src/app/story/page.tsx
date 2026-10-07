import Link from "next/link";
import { ReadingsFigure } from "@/components/ArgumentFigures";
import { StackPlate } from "@/components/ArgumentParts";
import { LeanBars, TallyBars } from "@/components/BoardFigures";
import { LabsPlate, TiesPlate } from "@/components/CaptureFigures";
import { ScreenFigure, WholeFigure } from "@/components/CensusFigures";
import { LagModel, StageGauges } from "@/components/DiffusionFigures";
import { Callout } from "@/components/Figure";
import { Anatomy } from "@/components/FirmKinds";
import { FourClocks } from "@/components/FourClocks";
import { Credit, Plate } from "@/components/FuturesParts";
import { FictionLag, SaidAgainstGiven, WorldsGrid } from "@/components/LongRunFigures";
import { ScalePlate } from "@/components/MigrationFigures";
import { DisputeReach } from "@/components/OutlookFigures";
import { PageHeader } from "@/components/PageHeader";
import { PerezCurve } from "@/components/PerezCurve";
import { TimelinePlate } from "@/components/SingularityParts";
import { StoryPanel } from "@/components/StoryPanel";
import { ChainFigure } from "@/components/ValueChainFigures";
import { Illustration } from "@/components/diagrams/illustration";
import { argument, board, capture, census, diffusion, firmKinds, futures, index, meta, outlook, singularity, story, valueChain } from "@/lib/data";
import { ACTS, STOPS, STOP_OF } from "@/lib/nav";

export const metadata = {
  title: "The story in pictures",
  description: "The argument as a run of figures in three acts: what is measured now, where the money is, and what people forecast. Each figure links to the page that holds its sources and limits.",
};

const link = "underline decoration-axis underline-offset-4 hover:decoration-ink";
const stopOf = (route: string) => {
  const n = STOP_OF.find(([href]) => route === href || route.startsWith(`${href}/`))?.[1];
  const s = STOPS.find((x) => x.n === n);
  return s ? `Stop ${s.n} · ${s.name}` : "";
};

// Every figure here is another page's, drawn by that page's component from that page's export. The words, and which
// panels are shown, come from story.json: a panel whose figure has no data is not in it.
export default function Story() {
  const doc = story();
  const a = argument(), d = diffusion().figures, c = census(), cap = capture(), o = outlook(), b = board(), s = singularity(), fu = futures();
  const cards = Object.fromEntries(index().indicators.map((x) => [x.id, x]));
  const FIGURES: Record<string, React.ReactNode> = {
    FourClocks: <FourClocks clocks={a.clocks} cards={cards} />,
    LagModel: <LagModel f={d.model} />,
    StageGauges: <StageGauges f={d.gauges} />,
    ReadingsFigure: <ReadingsFigure doc={a} />,
    WholeFigure: <WholeFigure c={c} />,
    ScreenFigure: <ScreenFigure c={c} />,
    PerezCurve: <PerezCurve phase={a.phase} facts={a.facts} />,
    StackPlate: <StackPlate />,
    LabsPlate: <LabsPlate labs={cap.figures.labs} />,
    TiesPlate: <TiesPlate ties={cap.figures.ties} />,
    ChainFigure: <ChainFigure f={valueChain().figures.chain} />,
    ScalePlate: <ScalePlate scale={a.migration.figures.scale} base="/argument/migration" />,
    Anatomy: <Anatomy doc={firmKinds()} picture={false} />,
    DisputeReach: <DisputeReach doc={o} base="/outlook" />,
    TallyBars: <TallyBars b={b} />,
    LeanBars: <LeanBars b={b} />,
    TimelinePlate: <TimelinePlate doc={s} base="/singularity" />,
    SaidAgainstGiven: <SaidAgainstGiven doc={s} />,
    WorldsGrid: <WorldsGrid doc={s} />,
    FictionLag: <FictionLag doc={s} credits={fu.credits} id="fig-fiction-lag" />,
  };
  return (
    <div className="flex flex-col gap-10 md:gap-14">
      <PageHeader eyebrow={doc.eyebrow} title={doc.title} lede={doc.lede}>
        <p className="font-mono text-[12px] text-muted">Readings updated {meta().generated_at.slice(0, 10)}</p>
        <div className="mt-2 max-w-[56rem]">
          <Callout label="How to read this page">
            <ul className="flex flex-col gap-1.5 text-[13.5px] leading-relaxed text-ink-2">
              {doc.disclosure.map((t) => <li key={t}>{t}</li>)}
              <li>Nothing here is advice. <Link href="/legal#advice" className={link}>What that means</Link>.</li>
            </ul>
          </Callout>
        </div>
      </PageHeader>

      <nav aria-label="Acts" className="sticky top-0 z-20 -mx-4 flex gap-x-5 border-b border-grid bg-background px-4 py-2 font-mono text-[11px] uppercase tracking-[0.08em] md:-mx-8 md:px-8">
        {doc.acts.map((act) => <a key={act.id} href={`#${act.anchor}`} className="text-ink-2 hover:text-ink">{act.id} · {ACTS.find((x) => x.act === act.id)?.title}</a>)}
      </nav>

      {doc.acts.map((act, i) => {
        const nav = ACTS.find((x) => x.act === act.id);
        return (
          <section key={act.id} id={act.anchor} aria-labelledby={`${act.anchor}-h`} className="flex scroll-mt-12 flex-col gap-12 md:gap-16">
            <div className="grid items-center gap-5 border-t-2 border-ink pt-6 md:grid-cols-[minmax(0,1fr)_minmax(0,30rem)] md:gap-10">
              <div className="flex flex-col gap-1 md:order-2">
                <Illustration {...act.illustration} stage={null} eager={i === 0} />
                {act.picture_note ? <p className="text-[12.5px] leading-snug text-ink-2">{act.picture_note}</p> : null}
              </div>
              <div className="flex flex-col gap-3">
                <div className="eyebrow">Act {act.id}</div>
                <h2 id={`${act.anchor}-h`} className="display text-[2.25rem] leading-none md:text-[3rem]">{nav?.title}</h2>
                <p className="max-w-[40ch] font-serif text-xl leading-snug text-ink-2">{act.sentence}</p>
                <ul className="mt-1 flex flex-col gap-1 text-sm">
                  {nav?.stops.map((st) => <li key={st.n} className="grid grid-cols-[2rem_1fr] gap-1"><span className="num text-muted">{st.n}</span><Link href={st.href} prefetch={false} className={link}>{st.question}</Link></li>)}
                </ul>
              </div>
            </div>
            {act.panels.map((p) => <StoryPanel key={p.id} p={p} stop={stopOf(p.route)}>{FIGURES[p.figure]}</StoryPanel>)}
          </section>
        );
      })}

      <section aria-labelledby="coda" className="flex flex-col gap-5 border-t-2 border-ink pt-6">
        <h2 id="coda" className="eyebrow">Imagined, not forecast</h2>
        {doc.coda.map((p) => <StoryPanel key={p.id} p={p} stop={stopOf(p.route)}>{FIGURES[p.figure]}</StoryPanel>)}
        <p className="max-w-[62ch] font-serif text-lg leading-relaxed text-ink-2">{doc.closing.strip}</p>
        <div className="grid gap-5 sm:grid-cols-3">
          {doc.plates.flatMap((src) => fu.featured.filter((x) => x.image === src)).map((x) => (
            <figure key={x.id} className="flex flex-col gap-1.5">
              <Plate src={x.image} alt={`Illustration of ${x.name}: ${x.line}`} sizes="(min-width: 640px) 30vw, 100vw" />
              <figcaption className="text-[13px]"><strong className="font-medium">{x.name}</strong> <span className="text-muted">· {x.author}, {x.imagined}</span><br /><span className="text-[12px] text-ink-2">{x.line}</span></figcaption>
            </figure>
          ))}
        </div>
        <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1"><Credit /><Link href="/futures#gallery" prefetch={false} className={`text-sm ${link}`}>The gallery, and the idea bank behind it →</Link></div>
      </section>

      <div className="flex flex-col gap-3">
        <p className="max-w-[62ch] font-serif text-xl leading-relaxed">{doc.closing.words}</p>
        <Link href="/argument#fig-exits" prefetch={false} className={`self-start text-sm font-medium ${link}`}>{doc.closing.exits} →</Link>
      </div>
    </div>
  );
}
