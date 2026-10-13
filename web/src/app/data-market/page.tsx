import Link from "next/link";
import { DataMarketNav } from "@/components/DataMarketNav";
import { PageHeader } from "@/components/PageHeader";
import { dataMarket } from "@/lib/data";

export const metadata = {
  title: "The data market",
  description: "What the firms that sell training data to AI model builders show their buyers asking for, read from the firms' own public pages. A model's reading, labelled as one.",
};

const link = "underline decoration-grid underline-offset-4";

export default function DataMarketPage() {
  const d = dataMarket();
  return (
    <div className="flex flex-col gap-10 max-w-[72rem]">
      <DataMarketNav here="/data-market" />
      <PageHeader
        eyebrow={<><Link href="/capture" className="hover:text-ink">Who profits</Link> · the data market</>}
        title="What are the people who train AI buying?"
        lede="AI models learn from examples. The public internet supplied the first of them for free. What comes next has to be made, bought or recorded, and a trade has grown up to supply it."
      />

      <section id="dm-how" className="scroll-mt-24 flex flex-col gap-3 max-w-[68ch] text-ink-2 leading-relaxed">
        <h2 className="display text-2xl text-ink">How this is read</h2>
        <p>
          Model builders do not publish what they buy. The firms that sell to them do, without meaning to. A vendor&apos;s job listings say which experts it needs. Its research posts say which problems its customers have set it. Its terms say what a customer may do with the goods.
        </p>
        <p>
          This page reads those pages for <span className="num text-ink">{d.counts.sellers}</span> vendors with evidence of fast growth in the past year, <span className="num text-ink">{d.counts.weak}</span> more whose evidence of growth is weak, and <span className="num text-ink">{d.counts.builders}</span> companies that build models, for robots or for language, whose pages say what they train on or buy. It cites <span className="num text-ink">{d.counts.pages}</span> pages, each fetched and dated. Nothing comes from social media.
        </p>
        <p className="border-l-2 border-dotted border-axis pl-3 text-[13.5px] leading-snug">
          <span className="text-muted">A model&apos;s reading of the vendors&apos; own pages, not a measurement. </span>
          {d.made_by.method} Then {d.made_by.reviewed_by}. A page shows what a company says of itself; the site reports that it says so and does not vouch that it is true. <Link href="/methodology#company-claims" className={link}>How this is made</Link>.
        </p>
        <p className="text-[13.5px] leading-snug">{d.disclosure}</p>
      </section>

      <section id="dm-signals" className="scroll-mt-24 flex flex-col gap-4">
        <div className="flex flex-col gap-2 max-w-[68ch]">
          <h2 className="display text-2xl">The signals</h2>
          <p className="text-ink-2 leading-relaxed">
            Each row is one thing the pages show buyers asking for: <span className="num text-ink">{d.counts.signals}</span> in all, the most widely shown first. The bar and the figure beside it count the vendors with good evidence of growth whose own pages show it; vendors with weak evidence are counted apart, hatched. Open a row for what it implies and for each vendor&apos;s page.
          </p>
        </div>
        <ol className="panel divide-y divide-grid">
          {d.signals.map((s) => (
            <li key={s.id} id={s.id} className="scroll-mt-24">
              <details className="group">
                <summary className="grid cursor-pointer list-none grid-cols-[1fr_auto] items-baseline gap-x-4 gap-y-1 px-4 py-3 md:grid-cols-[minmax(0,1fr)_9rem_3.5rem_5.5rem] hover:bg-background">
                  <span className="flex flex-col gap-0.5">
                    <span className="text-[15px] leading-snug text-ink group-open:font-medium">{s.headline}</span>
                    <span className="eyebrow !text-[10px] !tracking-[0.12em]">{s.theme_name}</span>
                  </span>
                  <span className="hidden h-2 self-center rounded-sm bg-grid md:block" aria-hidden>
                    <span className="block h-2 rounded-sm bg-slow" style={{ width: `${s.bar}%` }} />
                  </span>
                  <span className="num text-right text-[15px] text-ink" title="vendors with good evidence of growth">{s.evidenced}</span>
                  <span className="col-span-2 text-xs text-muted md:col-span-1 md:text-right">
                    {s.weak ? <><span className="hatch mr-1 inline-block h-2 w-3 align-baseline text-slow" aria-hidden />+{s.weak} weak evidence</> : null}
                  </span>
                </summary>
                <div className="flex flex-col gap-3 px-4 pb-4 pt-1 max-w-[76ch]">
                  <p className="text-ink-2 leading-relaxed"><span className="text-muted">What it implies buyers want: </span>{s.implies}</p>
                  <ul className="flex flex-wrap gap-x-4 gap-y-1 text-[13px] text-ink-2">
                    {s.evidence.map((e) => (
                      <li key={e.vendor}>
                        <a href={e.url} rel="nofollow noopener" className={link}>{e.name}</a>
                        <span className="num ml-1 text-[11px] text-muted">read {e.retrieved_at}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </details>
            </li>
          ))}
        </ol>
      </section>

      <section id="dm-limits" className="scroll-mt-24 flex flex-col gap-3 max-w-[68ch] text-ink-2 leading-relaxed">
        <h2 className="display text-2xl text-ink">What the pages do not show</h2>
        <p>
          Almost no page gives a price that a model builder paid. The prices that are published are what vendors pay their experts and what they offer companies for records. Those that could be checked against their page are on <Link href="/data-market/prices" className={link}>prices and pay</Link>.
        </p>
        <p>
          The vendors disagree with each other. Some say data made by people matters less with each new model; others say data made by machines helps less at the frontier.
        </p>
        <p>
          A vendor absent from a row may still do the thing the row describes. It is listed only where one of its own pages, read here, shows it. Some vendors are missing altogether because none of their pages answered.
        </p>
      </section>
    </div>
  );
}
