import Link from "next/link";
import { DataMarketNav } from "@/components/DataMarketNav";
import { PageHeader } from "@/components/PageHeader";
import { dataMarket } from "@/lib/data";

export const metadata = {
  title: "The data market: prices and pay",
  description: "What vendors of AI training data pay their experts, offer companies for records and charge for their goods, each figure quoted from the page it came from.",
};

const link = "underline decoration-grid underline-offset-4";

export default function DataMarketPricesPage() {
  const d = dataMarket();
  return (
    <div className="flex flex-col gap-8 max-w-[72rem]">
      <DataMarketNav here="/data-market/prices" />
      <PageHeader
        eyebrow={<><Link href="/capture" className="hover:text-ink">Who profits</Link> · <Link href="/data-market" className="hover:text-ink">the data market</Link></>}
        title="What is paid, and for what"
        lede="Almost no page says what a model builder paid. What vendors do publish is what they pay the people who make the data, what they offer companies for their records, and now and then a price of their own."
      />
      <p className="max-w-[68ch] border-l-2 border-dotted border-axis pl-3 text-[13.5px] leading-snug text-ink-2">
        Each of the <span className="num text-ink">{d.counts.prices}</span> figures here is quoted from the page it links to, and the words beside the link are the page&apos;s own. <span className="text-muted">The short description of what is being paid for is a model&apos;s, checked by a second run of the same model and by no person.</span> A job listing shows what a vendor offers, not what anyone accepted; a company&apos;s own page is its claim. Listings are taken down, so a link may no longer show what was read on the day given. Many more figures were found than are shown: one is shown only where the page, fetched under this site&apos;s rules, states it in a single passage. <Link href="/methodology#company-claims" className={link}>How this is made</Link>.
      </p>
      {d.prices.groups.map((g) => (
        <section key={g.unit} className="flex flex-col gap-3">
          <h2 className="display text-2xl">{g.name} <span className="num text-base font-normal text-muted">{g.n}</span></h2>
          <ul className="panel divide-y divide-grid text-sm">
            {g.rows.map((r) => (
              <li key={r.id} className="grid grid-cols-1 gap-x-4 gap-y-1 px-4 py-3 md:grid-cols-[9rem_minmax(0,1fr)_13rem_22rem]">
                <span className="font-medium text-ink"><Link href={`/data-market/vendors#${r.vendor}`} className="hover:underline">{r.name}</Link></span>
                <span className="text-ink-2">{r.what}</span>
                <span className="num text-ink">{r.amount}</span>
                <span className="text-[12.5px] leading-snug text-ink-2">
                  <q className="font-serif">{r.snippet}</q>
                  <span className="mt-1 block text-[11px] text-muted">
                    <a href={r.url} rel="nofollow noopener" className={link}>{r.whose_name}</a> <span className="num">read {r.retrieved_at}</span>
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
