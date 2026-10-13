import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { configured, load, type PrivateManifest } from "@/lib/private";

const link = "underline decoration-grid underline-offset-4 hover:decoration-ink";

export default async function PrivateIndexPage() {
  if (!configured()) notFound();
  const manifest = await load<PrivateManifest>("manifest.json");
  if (!manifest) redirect("/private/login");
  return (
    <div className="flex max-w-[72rem] flex-col gap-10">
      <h1 className="display text-[2.25rem] md:text-[3.25rem] leading-[1.04]">Contents</h1>
      {manifest.sections.map((s) => (
        <section key={s.slug} className="flex flex-col gap-3">
          <h2 className="display text-2xl"><Link prefetch={false} href={`/private/${s.slug}`} className="hover:underline">{s.title}</Link></h2>
          <ol className="flex flex-col gap-1.5 font-serif text-lg">
            {s.documents.map((d) => <li key={d.slug}><Link prefetch={false} href={`/private/${s.slug}/${d.slug}`} className={link}>{d.title}</Link></li>)}
          </ol>
        </section>
      ))}
    </div>
  );
}
