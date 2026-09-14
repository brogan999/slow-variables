import Link from "next/link";
import { ArticleLayout } from "@/components/ArticleLayout";
import { Exits, ReadingMargin, SlowVariables, StackPlate } from "@/components/ArgumentParts";
import { Folios, Inline, parseEssay } from "@/components/Essay";
import { FourClocks } from "@/components/FourClocks";
import { PerezCurve } from "@/components/PerezCurve";
import { argument, index, memos } from "@/lib/data";
import { SITE } from "@/lib/site";

export const metadata = { title: { absolute: `${SITE.name} · how fast AI lands, and who keeps the value` } };

export default function Home() {
  const doc = argument();
  const cards = Object.fromEntries(index().indicators.map((c) => [c.id, c]));
  const { title, lede, folios } = parseEssay(doc.essay.home);
  const latest = memos()[0];
  const plates = { clocks: <FourClocks clocks={doc.clocks} cards={cards} />, perez: <PerezCurve phase={doc.phase} facts={doc.facts} />, stack: <StackPlate /> };
  return (
    <ArticleLayout
      head={
        <header className="flex flex-col gap-5 pt-4 md:pt-10">
          <div className="eyebrow">The argument this tracker tests</div>
          <h1 className="display text-[2.75rem] md:text-[4.5rem] leading-[0.98] max-w-[16ch]">{title}</h1>
          <p className="font-serif text-xl md:text-[1.4rem] leading-[1.55] text-ink-2 max-w-[60ch]"><Inline text={lede} facts={doc.facts} /></p>
        </header>
      }
      margin={<ReadingMargin doc={doc} />}
    >
      <Folios folios={folios} facts={doc.facts} plates={plates} />
      <p className="mt-10 font-serif text-lg"><Link href="/argument" className="underline decoration-axis underline-offset-4 hover:decoration-ink">Read the full argument, with its sources →</Link></p>

      <section id="slow-variables" className="mt-24 scroll-mt-8">
        <div className="eyebrow">What the site measures</div>
        <h2 className="display text-[1.875rem] md:text-[2.375rem] leading-[1.08] mt-3 mb-3">The five slow variables</h2>
        <p className="font-serif text-lg text-ink-2 leading-relaxed mb-6 max-w-[60ch]">Five numbers that change slowly and decide what the fast ones amount to. Each links to its sources, its history and the rule that grades it.</p>
        <SlowVariables doc={doc} cards={cards} />
      </section>

      <section id="exits" className="mt-24 scroll-mt-8">
        <div className="eyebrow">The exits</div>
        <h2 className="display text-[1.875rem] md:text-[2.375rem] leading-[1.08] mt-3 mb-6">What would change our mind</h2>
        <Exits doc={doc} />
      </section>

      {latest ? (
        <section className="mt-24 border-t border-grid pt-8">
          <div className="eyebrow">This week</div>
          <p className="mt-3 font-serif text-xl"><Link href={`/memos/${latest.date}`} className="underline decoration-axis underline-offset-4 hover:decoration-ink">{latest.title}</Link></p>
          <p className="mt-1 text-sm text-muted">The weekly memo, {latest.since} to {latest.date}. <Link href="/memos" className="hover:text-ink">All memos →</Link></p>
        </section>
      ) : null}
    </ArticleLayout>
  );
}
