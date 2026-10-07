import Link from "next/link";
import { ArticleLayout } from "@/components/ArticleLayout";
import { ArgumentMap, ExitsFigure, ReadingsFigure } from "@/components/ArgumentFigures";
import { Exits, ReadingMargin, SlowVariables, StackPlate } from "@/components/ArgumentParts";
import { Folios, Inline, parseEssay } from "@/components/Essay";
import { FourClocks } from "@/components/FourClocks";
import { PerezCurve } from "@/components/PerezCurve";
import { FourPlacesCompact } from "@/components/FourPlaces";
import { argument, index, outlook } from "@/lib/data";

export const metadata = { title: "The argument", description: "Why a fast technology shows up slowly, who gets paid while it does, and the numbers that would prove the argument wrong." };

export default function ArgumentPage() {
  const doc = argument();
  const cards = Object.fromEntries(index().indicators.map((c) => [c.id, c]));
  const { title, lede, folios } = parseEssay(doc.essay.full);
  const plates = { clocks: <FourClocks clocks={doc.clocks} cards={cards} />, perez: <><PerezCurve phase={doc.phase} facts={doc.facts} /><div className="not-prose mt-4"><FourPlacesCompact shifts={outlook().shifts} /></div></>, stack: <StackPlate />, record: <CaseRecord rows={doc.record} />,
    map: <ArgumentMap doc={doc} />, readings: <ReadingsFigure doc={doc} />, exits: <ExitsFigure doc={doc} /> };
  return (
    <ArticleLayout
      head={
        <header className="flex flex-col gap-5 pt-4 md:pt-10">
          <div className="eyebrow">The argument, in full</div>
          <h1 className="display text-[2.75rem] md:text-[4.5rem] leading-[0.98] max-w-[16ch]">{title}</h1>
          <p className="font-serif text-xl md:text-[1.4rem] leading-[1.55] text-ink-2 max-w-[60ch]"><Inline text={lede} facts={doc.facts} /></p>
        </header>
      }
      margin={<ReadingMargin doc={doc} />}
    >
      <Folios folios={folios} facts={doc.facts} plates={plates} />
      <section id="slow-variables" className="mt-16 scroll-mt-8">
        <h2 className="eyebrow mb-2">The five slow variables</h2>
        <p className="font-serif text-lg text-ink-2 leading-relaxed mb-6 max-w-[60ch]">Five numbers that change slowly and decide what the fast ones amount to. Each links to its sources, its history and the rule that grades it.</p>
        <SlowVariables doc={doc} cards={cards} />
      </section>
      <section id="exits" className="mt-16 scroll-mt-8">
        <h2 className="eyebrow mb-2">The list, re-tested every night</h2>
        <Exits doc={doc} />
      </section>
      <p className="mt-12 font-serif text-lg">A deep dive from here: <Link href="/argument/migration" className="underline decoration-axis underline-offset-4 hover:decoration-ink">the migrating bottleneck, on what is scarce in making AI and where that shortage moves →</Link></p>
      <section id="sources" className="mt-20 border-t border-grid pt-8 scroll-mt-8">
        <h2 className="display text-[1.5rem] mb-4">Sources</h2>
        <ol className="flex flex-col gap-3 font-serif text-[1.0625rem] leading-relaxed">
          {doc.sources.map((s) => (
            <li key={s.url}>{s.who}, <a href={s.url} className="italic underline decoration-axis underline-offset-2 hover:decoration-ink">{s.work}</a>, {s.where}.</li>
          ))}
        </ol>
      </section>
    </ArticleLayout>
  );
}

// The fuller record behind Folio IV, closed by default so the essay reads straight through
function CaseRecord({ rows }: { rows: { title: string; text: string }[] }) {
  return (
    <details className="group panel p-4 not-prose">
      <summary className="cursor-pointer list-none font-sans text-base font-medium"><span className="text-muted mr-2 inline-block transition-transform group-open:rotate-90">▸</span>Read the full record: who kept the money, stage by stage, and where the usual stories go too far</summary>
      <div className="mt-4 flex flex-col gap-4">
        {rows.map((r) => (
          <p key={r.title} className="font-serif text-[1.05rem] leading-[1.6]"><strong className="font-sans font-semibold">{r.title}.</strong> {r.text.split(/\*([^*]+)\*/).map((t, i) => (i % 2 ? <em key={i}>{t}</em> : t))}</p>
        ))}
        <p className="text-sm text-ink-2">The works behind each paragraph are listed with the essay&apos;s sources below.</p>
      </div>
    </details>
  );
}

