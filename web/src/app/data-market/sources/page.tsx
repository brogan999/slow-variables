import Link from "next/link";
import { DataMarketNav } from "@/components/DataMarketNav";
import { OpenOnHash } from "@/components/OpenOnHash";
import { PageHeader } from "@/components/PageHeader";
import { dataMarket } from "@/lib/data";

export const metadata = {
  title: "The data market: every kind of record",
  description: "Every kind of record that could be training data for AI, by family, and who is already selling or using each. A model's reading of a search, labelled as one.",
};

const link = "underline decoration-grid underline-offset-4";

// One mark for each level: solid where the record is openly sold, hatched where an incumbent uses its own, a small dot
// where only nearby players were found, an open square where nobody was, and a faint square where no search was run.
const MARK: Record<string, string> = {
  "3": "bg-slow",
  "2": "hatch text-slow",
  "1": "bg-[radial-gradient(circle,var(--slow)_0_2px,transparent_2.5px)] shadow-[inset_0_0_0_1px_var(--grid)]",
  "0": "shadow-[inset_0_0_0_1px_var(--axis)]",
  null: "bg-grid",
};

function Mark({ level, className = "" }: { level: number | null; className?: string }) {
  return <span aria-hidden className={`inline-block h-2.5 w-2.5 rounded-[1px] ${MARK[String(level)]} ${className}`} />;
}

export default function DataMarketSourcesPage() {
  const d = dataMarket();
  return (
    <div className="flex flex-col gap-8 max-w-[72rem]">
      <OpenOnHash />
      <DataMarketNav here="/data-market/sources" />
      <PageHeader
        eyebrow={<><Link href="/capture" className="hover:text-ink">Who profits</Link> · <Link href="/data-market" className="hover:text-ink">the data market</Link></>}
        title="Every kind of record, and who is already there"
        lede="Work leaves records: claim files, inspection reports, dispatch logs, exam scripts. Each could teach a model how the work is done. Each mark below is one kind of record, and its fill says whether anyone is yet selling or using it to train AI."
      />
      <p className="max-w-[68ch] border-l-2 border-dotted border-axis pl-3 text-[13.5px] leading-snug text-ink-2">
        <span className="text-muted">A model&apos;s reading of a search, not a measurement. </span>
        For each of the <span className="num text-ink">{d.sources.n}</span> kinds of record, research runs searched for anyone selling it, or using their own, to train AI, and sorted what they found into the levels below. &ldquo;Nobody found&rdquo; means that search found nobody, not that nobody exists. Links are shown only where the page could be read under this site&apos;s rules; where a level rests on a finding with no link that could be read, the row says so. {d.disclosure} <Link href="/methodology#company-claims" className={link}>How this is made</Link>.
      </p>

      <section id="dm-field" className="scroll-mt-24 flex flex-col gap-4">
        <ul className="flex flex-wrap gap-x-5 gap-y-1.5 text-[13px] text-ink-2">
          {d.sources.key.map((k) => (
            <li key={String(k.level)} className="flex items-center gap-1.5"><Mark level={k.level} /> {k.name} <span className="num text-muted">{k.n}</span></li>
          ))}
        </ul>
        <div className="grid grid-cols-1 gap-x-4 gap-y-2 md:grid-cols-[15rem_1fr]">
          {d.sources.families.map((f) => (
            <div key={f.name} className="contents">
              <a href={`#${f.rows[0].id}-family`} className="text-[12.5px] leading-tight text-ink-2 hover:text-ink md:text-right">{f.name} <span className="num text-muted">{f.n}</span></a>
              <div className="flex flex-wrap content-start gap-[3px]">
                {f.marks.map((m) => (
                  <a key={m.id} href={`#${m.id}`} title={m.name} aria-label={m.name}><Mark level={m.level} className="block" /></a>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section id="dm-families" className="scroll-mt-24 flex flex-col gap-2">
        <h2 className="display text-2xl">The records, family by family</h2>
        {d.sources.families.map((f) => (
          <details key={f.name} id={`${f.rows[0].id}-family`} className="panel scroll-mt-24">
            <summary className="cursor-pointer list-none px-4 py-2.5 text-[15px] font-medium text-ink hover:bg-background">{f.name} <span className="num font-normal text-muted">{f.n}</span></summary>
            <ul className="divide-y divide-grid border-t border-grid">
              {f.rows.map((r) => (
                <li key={r.id} id={r.id} className="scroll-mt-24 grid grid-cols-1 gap-x-4 gap-y-0.5 px-4 py-2 text-sm md:grid-cols-[minmax(0,1fr)_14rem]">
                  <span className="text-ink">{r.name}{r.idea ? <span className="ml-2 text-xs text-muted">a record that would have to be made</span> : null}</span>
                  <span className="flex items-center gap-1.5 text-[13px] text-ink-2"><Mark level={r.level} /> {r.level_name}</span>
                  <span className="text-xs leading-snug text-muted md:col-span-2">
                    {r.holder}{r.holder && r.personal ? "; " : ""}{r.personal}
                    {r.there.map((t, i) => (
                      <span key={t.url}> · <a href={t.url} rel="nofollow noopener" className={link}>link {i + 1}</a> <span className="num">read {t.retrieved_at}</span></span>
                    ))}
                    {r.unlinked ? <span> · rests on a finding with no link that could be read here</span> : null}
                  </span>
                </li>
              ))}
            </ul>
          </details>
        ))}
      </section>
    </div>
  );
}
