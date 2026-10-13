import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { configured, load, type PrivateManifest } from "@/lib/private";

const link = "underline decoration-grid underline-offset-4 hover:decoration-ink";

// One page draws every section and every document. Which exist is decided by the manifest alone: an address is
// looked up in it and never turned into a file name.
export default async function PrivatePage({ params }: { params: Promise<{ section: string; slug?: string[] }> }) {
  if (!configured()) notFound();
  const manifest = await load<PrivateManifest>("manifest.json");
  if (!manifest) redirect("/private/login");
  const { section, slug = [] } = await params;
  const sec = manifest.sections.find((s) => s.slug === section);
  if (!sec || slug.length > 1) notFound();
  const eyebrow = <Link prefetch={false} href="/private" className="hover:text-ink">Contents</Link>;

  if (!slug.length) {
    return (
      <div className="flex max-w-[72rem] flex-col gap-6">
        <span className="eyebrow">{eyebrow}</span>
        <h1 className="display text-[2.25rem] md:text-[3.25rem] leading-[1.04] max-w-[24ch]">{sec.title}</h1>
        <ol className="flex flex-col gap-1.5 font-serif text-lg">
          {sec.documents.map((d) => <li key={d.slug}><Link prefetch={false} href={`/private/${sec.slug}/${d.slug}`} className={link}>{d.title}</Link></li>)}
        </ol>
      </div>
    );
  }

  const at = sec.documents.findIndex((d) => d.slug === slug[0]);
  const doc = sec.documents[at];
  if (!doc || doc.kind !== "doc") notFound();
  const body = await load<{ title: string; html: string }>(doc.file);
  if (!body) redirect("/private/login");
  const prev = sec.documents[at - 1];
  const next = sec.documents[at + 1];
  return (
    <div className="flex max-w-[72rem] flex-col gap-8">
      <div className="flex flex-col gap-3">
        <span className="eyebrow">{eyebrow} · <Link prefetch={false} href={`/private/${sec.slug}`} className="hover:text-ink">{sec.title}</Link></span>
        <h1 className="display text-[2.25rem] md:text-[3.25rem] leading-[1.04] max-w-[24ch]">{body.title}</h1>
      </div>
      <div className="grid grid-cols-1 gap-x-12 gap-y-8 lg:grid-cols-[minmax(0,1fr)_19rem]">
        {/* The bundle's HTML is produced, escaped, by our own converter from our own private repository. */}
        <article className="prose-folio doc-html min-w-0 max-w-[66ch]" dangerouslySetInnerHTML={{ __html: body.html }} />
        <aside className="self-start text-[12.5px] leading-snug text-ink-2 lg:sticky lg:top-6">
          <nav aria-label="This section" className="panel p-4">
            <h2 className="eyebrow mb-2">{sec.title}</h2>
            <ol className="flex flex-col gap-1.5">
              {sec.documents.map((d) => (
                <li key={d.slug}>{d.slug === doc.slug ? <span aria-current="page" className="font-semibold text-ink">{d.title}</span> : <Link prefetch={false} href={`/private/${sec.slug}/${d.slug}`} className={link}>{d.title}</Link>}</li>
              ))}
            </ol>
          </nav>
        </aside>
      </div>
      <nav aria-label="Previous and next" className="flex flex-wrap justify-between gap-4 border-t border-grid pt-4 text-sm">
        {prev ? <Link prefetch={false} href={`/private/${sec.slug}/${prev.slug}`} className={link}>← {prev.title}</Link> : <span />}
        {next ? <Link prefetch={false} href={`/private/${sec.slug}/${next.slug}`} className={link}>{next.title} →</Link> : null}
      </nav>
    </div>
  );
}
