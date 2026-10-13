import Link from "next/link";
import { DataMarketNav } from "@/components/DataMarketNav";
import { PageHeader } from "@/components/PageHeader";
import { dataMarket } from "@/lib/data";

export const metadata = {
  title: "The data market: vendors",
  description: "The firms that sell training data to AI model builders, and the robot-model builders that say what they train on: what each sells and which signals its own pages show. A model's reading, labelled as one.",
};

const link = "underline decoration-grid underline-offset-4";
const ANCHOR = { evidenced: "dm-evidenced", weak: "dm-weak", builders: "dm-builders" } as const;

export default function DataMarketVendorsPage() {
  const d = dataMarket();
  return (
    <div className="flex flex-col gap-8 max-w-[72rem]">
      <DataMarketNav here="/data-market/vendors" />
      <PageHeader
        eyebrow={<><Link href="/capture" className="hover:text-ink">Who profits</Link> · <Link href="/data-market" className="hover:text-ink">the data market</Link></>}
        title="Who sells, and what their pages show"
        lede="Each vendor, what it sells in its own terms, and the signals its own pages show. A mark in a column means a page of that vendor's, read here, shows a signal on that theme."
      />
      <p className="max-w-[68ch] border-l-2 border-dotted border-axis pl-3 text-[13.5px] leading-snug text-ink-2">
        <span className="text-muted">A model&apos;s reading of the vendors&apos; own pages, not a measurement. </span>
        An empty column does not mean a vendor does not do that work, only that no page read here shows it. Which vendors have weak evidence of growth is a call made in the research. {d.disclosure} <Link href="/methodology#company-claims" className={link}>How this is made</Link>.
      </p>
      {d.board.groups.map((g) => (
        <section key={g.id} id={ANCHOR[g.id]} className="scroll-mt-24 flex flex-col gap-3">
          <div className="flex flex-col gap-1 max-w-[68ch]">
            <h2 className="display text-2xl">
              {g.name} <span className="num text-base font-normal text-muted">{g.n}</span>
              {g.id === "weak" ? <span className="ml-2 rounded-sm border border-dashed border-axis px-1.5 py-0.5 align-middle text-[10px] font-semibold uppercase tracking-[0.12em] text-muted">weak evidence</span> : null}
            </h2>
            <p className="text-sm leading-relaxed text-ink-2">{g.says}</p>
          </div>
          <div className="panel overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-grid align-bottom">
                  <th className="px-4 py-2 text-left eyebrow">Vendor</th>
                  <th className="px-2 py-2 text-right eyebrow">Signals</th>
                  {d.board.columns.map((c) => (
                    <th key={c.theme} className="hidden md:table-cell px-1 py-2 eyebrow !tracking-[0.06em]"><span className="inline-block rotate-180 [writing-mode:vertical-rl]">{c.label}</span></th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-grid">
                {g.vendors.map((v) => (
                  <tr key={v.id} id={v.id} className="scroll-mt-24 align-top">
                    <td className="px-4 py-2.5">
                      <details>
                        <summary className="cursor-pointer list-none"><span className="font-medium text-ink hover:underline">{v.name}</span>
                        <span className="mt-1 flex flex-wrap gap-x-2 gap-y-0.5 text-[11.5px] leading-snug text-muted md:hidden">
                          {v.cells.map((on, i) => (on ? <span key={d.board.columns[i].theme} className="flex items-center gap-1"><span aria-hidden className={`inline-block h-1.5 w-1.5 rounded-full ${g.id === "weak" ? "border border-slow" : "bg-slow"}`} />{d.board.columns[i].label}</span> : null))}
                        </span>
                        </summary>
                        <div className="mt-1.5 flex max-w-[52ch] flex-col gap-2 pb-1 text-[13px] leading-snug text-ink-2">
                          <p>{v.sells}</p>
                          <ul className="flex flex-col gap-1">
                            {v.shown.map((s) => (
                              <li key={s.id}><Link href={`/data-market#${s.id}`} className={link}>{s.headline}</Link></li>
                            ))}
                          </ul>
                          <p className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">
                            {v.pages.map((u, i) => (
                              <a key={u} href={u} rel="nofollow noopener" className={link}>page {i + 1}</a>
                            ))}
                          </p>
                        </div>
                      </details>
                    </td>
                    <td className="num px-2 py-2.5 text-right text-ink">{v.n_signals}</td>
                    {v.cells.map((on, i) => (
                      <td key={d.board.columns[i].theme} className="hidden md:table-cell px-1 py-2.5 text-center">
                        {on ? <span className={`inline-block h-2.5 w-2.5 rounded-full ${g.id === "weak" ? "border border-slow" : "bg-slow"}`} title={d.board.columns[i].label} /> : null}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  );
}
