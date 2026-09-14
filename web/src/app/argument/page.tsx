import { ArticleLayout } from "@/components/ArticleLayout";
import { Exits, ReadingMargin, StackPlate } from "@/components/ArgumentParts";
import { Folios, Inline, parseEssay } from "@/components/Essay";
import { FourClocks } from "@/components/FourClocks";
import { PerezCurve } from "@/components/PerezCurve";
import { argument, index } from "@/lib/data";

export const metadata = { title: "The argument", description: "Why a fast technology shows up slowly, who gets paid while it does, and the numbers that would prove the argument wrong." };

export default function ArgumentPage() {
  const doc = argument();
  const cards = Object.fromEntries(index().indicators.map((c) => [c.id, c]));
  const { title, lede, folios } = parseEssay(doc.essay.full);
  const plates = { clocks: <FourClocks clocks={doc.clocks} cards={cards} />, perez: <PerezCurve phase={doc.phase} facts={doc.facts} />, stack: <StackPlate /> };
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
      <section id="exits" className="mt-16 scroll-mt-8">
        <h2 className="eyebrow mb-2">The list, re-tested every night</h2>
        <Exits doc={doc} />
      </section>
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
