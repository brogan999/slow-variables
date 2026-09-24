import Link from "next/link";
import { ArticleLayout, MarginPanel } from "@/components/ArticleLayout";
import { Credit, Plate, Sources, link } from "@/components/FuturesParts";
import { PageHeader } from "@/components/PageHeader";
import { futures } from "@/lib/data";
import { fmt } from "@/lib/format";

export const metadata = {
  title: "Futures: what fiction imagined, and when it may arrive",
  description: "Thousands of technologies imagined in science fiction, by the decade they were imagined and the decade they may arrive, each with who would keep the profit.",
};

function Section({ id, eyebrow, title, lede, children }: { id: string; eyebrow: string; title: string; lede: React.ReactNode; children: React.ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className="flex flex-col gap-4 scroll-mt-8">
      <div className="eyebrow">{eyebrow}</div>
      <h2 id={`${id}-h`} className="display text-[1.9rem] leading-tight">{title}</h2>
      <p className="font-serif text-[17px] leading-relaxed text-ink-2 max-w-[66ch]">{lede}</p>
      {children}
    </section>
  );
}

export default function FuturesPage() {
  const f = futures();
  return (
    <ArticleLayout
      head={
        <PageHeader
          eyebrow="Futures"
          title="What fiction imagined, and when it may arrive"
          lede="A collection of thousands of technologies imagined in science fiction, laid out by the decade a story first imagined each one and the decade it may arrive, with a judgement of who would keep the profit if it were ever sold."
        />
      }
      margin={
        <>
          <MarginPanel title="The collection" rows={[
            ["Imagined technologies", fmt(f.n_ideas, "count")],
            ["Dated forecasts from the singularity reading list", fmt(f.n_forecasts, "count")],
            ["Ideas illustrated", fmt(f.n_idea_images, "count")],
            ["Kinds of technology illustrated", fmt(f.n_category_images, "count")],
          ]} />
          <MarginPanel title="Where it comes from"><Sources /></MarginPanel>
        </>
      }
    >
      <div className="flex flex-col gap-16">
        <Section id="imagined" eyebrow="Part I" title="When each idea was imagined" lede="Each bar counts the ideas first imagined in that decade; the darker part is how many have since been built. It measures what the glossary records, which leans on the pulp magazine and paperback boom and may favour ideas that later came true, not how imaginative each decade was; ideas from recent decades have also had less time to be built.">
          <ol className="flex flex-col gap-1.5">
            {f.imagined.map((d) => (
              <li key={d.key} className="grid grid-cols-[6.5rem_1fr_5.5rem] items-center gap-3 text-[13px]">
                {d.href ? <Link href={d.href} className={link}>{d.label}</Link> : <span className="text-muted">{d.label}</span>}
                <span className="relative h-3 bg-surface-2 rounded-sm" aria-hidden>
                  <span className="absolute inset-y-0 left-0 bg-s3 rounded-sm" style={{ width: `${d.width}%` }} />
                  <span className="absolute inset-y-0 left-0 bg-s1 rounded-sm" style={{ width: `${d.built_width}%` }} />
                </span>
                <span className="tabular-nums text-ink-2">{fmt(d.n, "count")}{d.n ? <span className="text-muted"> · {fmt(d.built, "count")} built</span> : null}</span>
              </li>
            ))}
          </ol>
        </Section>

        <Section id="expected" eyebrow="Part II" title="When they may arrive" lede={<>For the ideas not yet built, the upper bar is the decade AI models judged a working, commercial version most likely. The lower bar counts dated forecasts made in the books and essays of the <Link href="/singularity" className={link}>singularity reading list</Link>, set at the decade their author gave (for a range, its first year). The two are different kinds of claim and are never added together.</>}>
          <ol className="flex flex-col gap-2">
            {f.expected.map((d) => (
              <li key={d.key} className="grid grid-cols-[1fr] sm:grid-cols-[10rem_1fr_11rem] items-center gap-x-3 gap-y-1 text-[13px]">
                <Link href={d.href} className={link}>{d.label}</Link>
                <span className="flex flex-col gap-0.5" aria-hidden>
                  <span className="h-2.5 bg-surface-2 rounded-sm relative"><span className="absolute inset-y-0 left-0 bg-s2 rounded-sm" style={{ width: `${d.judged_width}%` }} /></span>
                  <span className="h-2.5 bg-surface-2 rounded-sm relative"><span className="absolute inset-y-0 left-0 bg-fast rounded-sm" style={{ width: `${d.stated_width}%` }} /></span>
                </span>
                <span className="tabular-nums text-ink-2 text-[12px]">{fmt(d.judged, "count")} judged · {fmt(d.stated, "count")} stated</span>
              </li>
            ))}
          </ol>
          <p className="text-[12px] text-muted">Upper bar: ideas, judged by AI models. Lower bar: forecasts stated by their authors.</p>
        </Section>

        <Section id="categories" eyebrow="Part III" title="Kinds of technology, and who would profit" lede={<>Each idea was sorted into one kind of technology and, where it could be sold, judged by AI models for how much lasting profit it could earn and who would keep it: fat means a large margin that lasts for decades, moderate a typical one, thin a small or brief one, and monopoly-like one that rivals can barely touch. Where anyone could copy the idea, competition hands the gain to users instead. <Link href="/methodology#futures" className={link}>How the profit is judged</Link></>}>
          <div className="grid gap-5 sm:grid-cols-2">
            {f.categories.map((c) => (
              <Link key={c.id} href={c.href} className="panel px-3 py-3 flex flex-col gap-2 hover:border-ink">
                {c.image ? <Plate src={c.image} alt="" sizes="(min-width: 640px) 400px, 100vw" /> : null}
                <span className="font-medium">{c.name}</span>
                <span className="text-[12px] text-ink-2 tabular-nums">{fmt(c.n, "count")} ideas · {fmt(c.built, "count")} built</span>
                <span className="text-[11px] text-muted">Profit: {f.tier_words.filter((w) => c.tiers[w]).map((w) => `${w} ${fmt(c.tiers[w], "count")}`).join(" · ")}</span>
              </Link>
            ))}
          </div>
          <Credit />
        </Section>

        <Section id="gallery" eyebrow="Part IV" title="A gallery" lede={<>A few of the ideas the site&apos;s owner picked out of the idea bank for a closer look, in the order they were first imagined; each picture shows the idea as if it already existed. Every illustrated idea appears with its picture on the pages for its <Link href="#categories" className={link}>kind of technology</Link>.</>}>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {f.featured.map((x) => (
              <figure key={x.id} className="flex flex-col gap-1.5">
                {x.image ? <Plate src={x.image} alt={`Illustration of ${x.name}: ${x.line}`} sizes="(min-width: 1024px) 280px, (min-width: 640px) 45vw, 100vw" /> : null}
                <figcaption className="text-[13px]"><strong className="font-medium">{x.name}</strong> <span className="text-muted">· {x.author}, {x.imagined}</span><br /><span className="text-ink-2 text-[12px]">{x.line}</span></figcaption>
              </figure>
            ))}
          </div>
          <Credit />
        </Section>
        <Sources />
      </div>
    </ArticleLayout>
  );
}
