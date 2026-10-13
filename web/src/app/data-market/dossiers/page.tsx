import Link from "next/link";
import { DataMarketNav } from "@/components/DataMarketNav";
import { PageHeader } from "@/components/PageHeader";
import { dataMarketDossiers } from "@/lib/data";

export const metadata = {
  title: "The data market: dossiers",
  description: "Kinds of record that could be training data for AI, each examined closely: what the record is, who holds it and may share it, who is already there, and what stands in the way.",
};

export default function DataMarketDossiersPage() {
  const docs = dataMarketDossiers();
  return (
    <div className="flex flex-col gap-8 max-w-[72rem]">
      <DataMarketNav here="/data-market/dossiers" />
      <PageHeader
        eyebrow={<><Link href="/capture" className="hover:text-ink">Who profits</Link> · <Link href="/data-market" className="hover:text-ink">the data market</Link></>}
        title="Records examined closely"
        lede="A dossier takes one kind of record and asks what it is, who holds it and may share it, who is already using it, what would have to be stripped out, and what stands in the way of it becoming training data."
      />
      <p className="max-w-[68ch] border-l-2 border-dotted border-axis pl-3 text-[13.5px] leading-snug text-ink-2">
        Every figure in a dossier is stated on a page cited in the same sentence, and each page was fetched under this site&apos;s rules. <span className="text-muted">Each dossier ends in a model&apos;s judgement, set apart and labelled; the choice of which records to examine was a model&apos;s too.</span> An example marked as an illustration is invented to show the shape of a record.
      </p>
      <ol className="panel divide-y divide-grid">
        {docs.map((d) => (
          <li key={d.id}>
            <Link href={`/data-market/dossiers/${d.id}`} className="grid grid-cols-[2.5rem_1fr] items-baseline gap-x-3 px-4 py-3 hover:bg-background">
              <span className="num text-sm text-muted">{d.n}</span>
              <span className="text-[15px] leading-snug text-ink">{d.title}</span>
            </Link>
          </li>
        ))}
      </ol>
    </div>
  );
}
