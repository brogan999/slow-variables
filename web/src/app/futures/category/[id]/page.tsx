import Link from "next/link";
import { ArticleLayout, MarginPanel } from "@/components/ArticleLayout";
import { Credit, ForecastRow, IdeaCard, Plate, link } from "@/components/FuturesParts";
import { PageHeader } from "@/components/PageHeader";
import { futures, futuresCategory } from "@/lib/data";
import { fmt } from "@/lib/format";

export const dynamicParams = false;
export function generateStaticParams() { return futures().categories.map((c) => ({ id: c.id })); }
export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return { title: `Futures: ${futuresCategory(id).name}` };
}

export default async function FuturesCategoryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const c = futuresCategory(id);
  const words = futures().tier_words;
  return (
    <ArticleLayout
      head={
        <PageHeader eyebrow={<><Link href="/futures" className="hover:text-ink">Futures</Link> · kind of technology</>} title={c.name}
          lede="Every idea of this kind, in the order stories first imagined it, then the dated forecasts about it from the singularity canon.">
          {c.image ? <div className="mt-4 flex flex-col gap-1"><Plate src={c.image} alt={`Illustration for ${c.name}`} eager sizes="(min-width: 1024px) 760px, 100vw" /><Credit /></div> : null}
        </PageHeader>
      }
      margin={
        <MarginPanel title="Rent where the idea could be sold" rows={[["Ideas", fmt(c.n, "count")], ...words.filter((w) => c.tiers[w]).map((w) => [w, fmt(c.tiers[w], "count")] as [string, string])]} />
      }
    >
      <div className="flex flex-col gap-10">
        {c.forecasts.length ? (
          <section aria-labelledby="fc-h">
            <h2 id="fc-h" className="display text-[1.5rem] leading-tight mb-2">Dated forecasts</h2>
            <ul>{c.forecasts.map((f) => <ForecastRow key={f.id} f={f} />)}</ul>
          </section>
        ) : null}
        <section aria-labelledby="ideas-h">
          <h2 id="ideas-h" className="display text-[1.5rem] leading-tight mb-2">Imagined, oldest first</h2>
          <div>{c.ideas.map((x) => <IdeaCard key={x.id} x={x} />)}</div>
        </section>
        <p className="text-[12px] text-muted">Descriptions are this site&apos;s rewording; categories, arrival decades and rent are judged by AI models. <Link href="/methodology#futures" className={link}>Method</Link></p>
      </div>
    </ArticleLayout>
  );
}
