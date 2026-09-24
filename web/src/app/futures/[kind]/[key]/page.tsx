import Link from "next/link";
import { ArticleLayout, MarginPanel } from "@/components/ArticleLayout";
import { ForecastRow, IdeaCard, Sources } from "@/components/FuturesParts";
import { PageHeader } from "@/components/PageHeader";
import { futures, futuresDecade } from "@/lib/data";
import { fmt } from "@/lib/format";

export const dynamicParams = false;
export function generateStaticParams() {
  const f = futures();
  return [
    ...f.imagined.filter((d) => d.href).map((d) => ({ kind: "imagined", key: d.key })),
    ...f.expected.map((d) => ({ kind: "expected", key: d.key })),
  ];
}
export async function generateMetadata({ params }: { params: Promise<{ kind: string; key: string }> }) {
  const { kind, key } = await params;
  const d = futuresDecade(kind, key);
  return { title: `Futures: ${d.title}` };
}

export default async function FuturesDecadePage({ params }: { params: Promise<{ kind: string; key: string }> }) {
  const { kind, key } = await params;
  const d = futuresDecade(kind, key);
  const imagined = d.kind === "imagined";
  return (
    <ArticleLayout
      head={
        <PageHeader
          eyebrow={<><Link href="/futures" className="hover:text-ink">Futures</Link> · {imagined ? "imagined" : "expected"}</>}
          title={d.title}
          lede={imagined
            ? "The technologies stories first imagined in this decade, by kind, with whether each has been built since and who would keep the profit."
            : "Dated forecasts that name this time, as their authors stated them, then the unbuilt ideas AI models placed here."}
        />
      }
      margin={
        <MarginPanel title="This decade" rows={imagined
          ? [["Ideas", fmt(d.n, "count")], ["Built since", fmt(d.built, "count")]]
          : [["Forecasts stated by authors", fmt(d.stated, "count")], ["Ideas judged by AI models", fmt(d.judged, "count")]]} />
      }
    >
      <div className="flex flex-col gap-10">
        {!imagined && d.forecasts?.length ? (
          <section aria-labelledby="stated-h">
            <h2 id="stated-h" className="display text-[1.5rem] leading-tight mb-2">What authors forecast for {d.phrase}</h2>
            <ul>{d.forecasts.map((f) => <ForecastRow key={f.id} f={f} />)}</ul>
          </section>
        ) : null}
        {d.groups.length ? (
          <section aria-labelledby="ideas-h" className="flex flex-col gap-3">
            <h2 id="ideas-h" className="display text-[1.5rem] leading-tight">{imagined ? "By kind of technology" : "Unbuilt ideas AI models place here"}</h2>
            {d.groups.map((g) => (
              <details key={g.id} className="panel px-4 py-3" open={d.groups.length === 1 || g.n <= 12}>
                <summary className="cursor-pointer font-medium">{g.name} <span className="text-muted font-normal">· {fmt(g.n, "count")}</span></summary>
                <div className="mt-1">{g.ideas.map((x) => <IdeaCard key={x.id} x={x} />)}</div>
              </details>
            ))}
          </section>
        ) : null}
        <Sources />
      </div>
    </ArticleLayout>
  );
}
