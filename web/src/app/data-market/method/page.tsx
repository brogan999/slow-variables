import Link from "next/link";
import { DataMarketNav } from "@/components/DataMarketNav";
import { PageHeader } from "@/components/PageHeader";
import { dataMarket } from "@/lib/data";

export const metadata = {
  title: "The data market: how it was made",
  description: "How the data-market section was made: how many kinds of record were looked at, what each check changed, what is left out, and where the work is weak.",
};

const link = "underline decoration-grid underline-offset-4";
const REVIEW: Record<string, string> = {
  pairings: "Vendors paired with signals",
  register: "Further vendors from a public register",
  headlines: "Signals",
  prices: "Prices",
  levels: "Levels of the kinds of record",
  sources: "Dossier sources that would not open",
  figures: "Numbers in the dossiers",
  quotations: "Quotations in the dossiers",
};

export default function DataMarketMethodPage() {
  const d = dataMarket();
  return (
    <div className="flex flex-col gap-10 max-w-[72rem]">
      <DataMarketNav here="/data-market/method" />
      <PageHeader
        eyebrow={<><Link href="/capture" className="hover:text-ink">Who profits</Link> · <Link href="/data-market" className="hover:text-ink">the data market</Link></>}
        title="How it was made, and what is wrong with it"
        lede="This section was researched and written by a model, and checked by further runs of the same model. No person reviewed each line. This page says what was done, how much each check changed, what was left out and where the work is weak."
      />
      <p className="max-w-[68ch] text-[13.5px] leading-snug text-ink-2">{d.made_by.method} {d.disclosure} The rules every page of this section follows are in <Link href="/methodology#company-claims" className={link}>How to read this</Link>.</p>

      <section id="dm-narrowing" className="scroll-mt-24 flex flex-col gap-3">
        <h2 className="display text-2xl">From candidates to dossiers</h2>
        <ol className="flex flex-col md:flex-row">
          {d.method.narrowing.map((s) => (
            <li key={s.id} className="panel flex flex-1 flex-col gap-1 p-4">
              <span className="num text-[2rem] leading-none text-ink">{s.n}</span>
              <span className="text-[13px] leading-snug text-ink-2">{s.says}</span>
            </li>
          ))}
        </ol>
        <p className="max-w-[68ch] text-sm leading-relaxed text-ink-2">The kinds of record are on <Link href="/data-market/sources" className={link}>every kind of record</Link>; the dossiers are <Link href="/data-market/dossiers" className={link}>listed here</Link>.</p>
      </section>

      <section id="dm-reviews" className="scroll-mt-24 flex flex-col gap-3">
        <div className="flex max-w-[68ch] flex-col gap-2">
          <h2 className="display text-2xl">What each check changed</h2>
          <p className="text-ink-2 leading-relaxed">Each check was a separate run that read the first run&apos;s work against its evidence. The share it changed is the best measure here of how far a first reading can be trusted.</p>
        </div>
        <div className="panel overflow-x-auto">
          <table className="w-full min-w-[40rem] border-collapse text-sm">
            <thead>
              <tr className="border-b border-grid">
                <th className="px-4 py-2 text-left eyebrow">What was checked</th>
                <th className="px-2 py-2 text-right eyebrow">Checked</th>
                <th className="px-2 py-2 text-right eyebrow">Changed</th>
                <th className="px-4 py-2 text-left eyebrow">What the check did</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-grid">
              {d.method.reviews.map((r) => (
                <tr key={r.id} className="align-top">
                  <td className="px-4 py-2.5 font-medium text-ink">{REVIEW[r.id] ?? r.id}</td>
                  <td className="num px-2 py-2.5 text-right text-ink">{r.checked}</td>
                  <td className="num px-2 py-2.5 text-right text-ink">{r.changed}</td>
                  <td className="px-4 py-2.5 text-[13px] leading-snug text-ink-2">{r.what}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section id="dm-left-out" className="scroll-mt-24 flex max-w-[68ch] flex-col gap-3">
        <h2 className="display text-2xl">What is left out</h2>
        <ul className="list-disc pl-5 flex flex-col gap-2 text-ink-2 leading-relaxed">
          {d.method.left_out.map((t) => <li key={t}>{t}</li>)}
        </ul>
      </section>

      <section id="dm-found-wrong" className="scroll-mt-24 flex max-w-[68ch] flex-col gap-3">
        <h2 className="display text-2xl">What is wrong with it</h2>
        <p className="text-ink-2 leading-relaxed">Three further runs were asked to attack the work. These are their findings that still stand.</p>
        <ul className="list-disc pl-5 flex flex-col gap-2 text-ink-2 leading-relaxed">
          {d.method.found_wrong.map((t) => <li key={t}>{t}</li>)}
        </ul>
      </section>
    </div>
  );
}
