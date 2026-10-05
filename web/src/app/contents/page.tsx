import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { PAGES, REFERENCE, UNDER } from "@/lib/contents";
import { ACTS } from "@/lib/nav";
import { SITE } from "@/lib/site";

export const metadata = {
  title: "Contents",
  description: "Every page and section of Slow Variables, with the question each one answers.",
};

const link = "underline decoration-grid underline-offset-4 hover:decoration-ink";

function Entry({ href, n, deep = false }: { href: string; n?: string; deep?: boolean }) {
  const p = PAGES[href];
  return (
    <article className={`flex flex-col gap-2 ${deep ? "border-l border-grid pl-4" : ""}`}>
      <h3 className={deep ? "text-base font-medium" : "display text-[1.5rem] leading-tight"}>
        {n ? <span className="font-mono text-[12px] text-muted mr-2 align-middle">{n}</span> : null}
        <Link href={href} className={link}>{p.name}</Link>
      </h3>
      <p className="font-serif text-[17px] leading-snug text-ink-2 max-w-[60ch]">{p.question}</p>
      {p.sections ? (
        <ul className="flex flex-col gap-1 text-sm max-w-[56rem]">
          {p.sections.map(([id, name, q]) => (
            <li key={id} className="grid gap-x-3 sm:grid-cols-[minmax(0,17rem)_minmax(0,1fr)]">
              <Link href={`${href}#${id}`} className={`${link} text-ink`}>{name}</Link>
              <span className="text-ink-2">{q}</span>
            </li>
          ))}
        </ul>
      ) : null}
      {p.each?.map(([prefix, what]) => <p key={prefix} className="text-sm text-muted max-w-[72ch]">{what}</p>)}
    </article>
  );
}

export default function Contents() {
  return (
    <div className="flex flex-col gap-12">
      <PageHeader eyebrow="Contents" title="What each page answers" lede="Every page and named section of the site, with the question it answers. The three acts are in reading order; the pages after them hold the evidence and the rules." />
      {ACTS.map((a) => (
        <section key={a.act} aria-labelledby={`act-${a.act}`} className="flex flex-col gap-8 border-t border-grid pt-6">
          <h2 id={`act-${a.act}`} className="eyebrow">Act {a.act} · {a.title}</h2>
          {a.stops.map((s) => (
            <div key={s.href} className="flex flex-col gap-5">
              <Entry href={s.href} n={s.n} />
              {(UNDER[s.href] ?? []).map((h) => <Entry key={h} href={h} deep />)}
            </div>
          ))}
        </section>
      ))}
      <section aria-labelledby="reference" className="flex flex-col gap-8 border-t border-grid pt-6">
        <h2 id="reference" className="eyebrow">Evidence and reference</h2>
        {REFERENCE.filter((h) => h !== "/ask" || SITE.askOnline).map((h) => <Entry key={h} href={h} />)}
      </section>
    </div>
  );
}
