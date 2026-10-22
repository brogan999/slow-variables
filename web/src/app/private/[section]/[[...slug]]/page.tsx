import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { configured, load, type PrivateManifest } from "@/lib/private";

const link = "underline decoration-grid underline-offset-4 hover:decoration-ink";

type Query = Record<string, string | string[] | undefined>;
type Table = { title: string; columns: string[]; rows: string[][]; filters: string[] };
const field = "h-9 rounded-[3px] border border-border bg-surface px-2 text-base sm:text-sm";

// A table is filtered here, on the server, from the address: a plain form, one select for each filter column and a
// text box. The first filter always holds one value, so the whole table never leaves in a single response.
function TableView({ table, query }: { table: Table; query: Query }) {
  const asked = (k: string) => (typeof query[k] === "string" ? query[k] : "");
  const filters = table.filters.map((name, i) => {
    const col = table.columns.indexOf(name);
    const values = [...new Set(table.rows.map((r) => r[col]))];
    const want = asked(`f${i}`);
    return { name, col, values, key: `f${i}`, value: values.includes(want) ? want : i === 0 ? (values[0] ?? "") : "" };
  });
  const q = asked("q").slice(0, 100);
  const needle = q.toLowerCase();
  const shown = table.rows.filter((r) => filters.every((f) => !f.value || r[f.col] === f.value) && (!needle || r.some((c) => c.toLowerCase().includes(needle))));
  return (
    <div className="flex flex-col gap-4">
      <form method="get" className="flex flex-wrap items-end gap-3 text-sm">
        {filters.map((f, i) => (
          <label key={f.key} className="flex flex-col gap-1">
            <span className="eyebrow">{f.name}</span>
            <select name={f.key} defaultValue={f.value} className={field}>
              {i > 0 ? <option value="">All</option> : null}
              {f.values.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          </label>
        ))}
        <label className="flex flex-col gap-1">
          <span className="eyebrow">Contains</span>
          <input name="q" defaultValue={q} maxLength={100} className={`${field} w-40`} />
        </label>
        <button type="submit" className="inline-flex h-9 items-center rounded-[3px] bg-ink px-3 font-medium text-background hover:bg-ink-2">Show</button>
      </form>
      <p className="text-sm text-muted"><span className="num">{shown.length}</span> rows</p>
      <div className="panel overflow-x-auto">
        <table className="data w-full min-w-[44rem]">
          <thead><tr>{table.columns.map((c) => <th key={c} scope="col" className="whitespace-nowrap">{c}</th>)}</tr></thead>
          <tbody>{shown.map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j} className="min-w-[11rem] align-top">{c}</td>)}</tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}

// One page draws every section and every document. Which exist is decided by the manifest alone: an address is
// looked up in it and never turned into a file name.
export default async function PrivatePage({ params, searchParams }: { params: Promise<{ section: string; slug?: string[] }>; searchParams: Promise<Query> }) {
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
  if (!doc) notFound();
  const body = await load<{ title: string; html?: string; figures?: string[] } & Partial<Table>>(doc.file);
  if (!body) redirect("/private/login");
  const table = doc.kind === "table" && body.columns && body.rows ? { title: body.title, columns: body.columns, rows: body.rows, filters: body.filters ?? [] } : null;
  const prev = sec.documents[at - 1];
  const next = sec.documents[at + 1];
  return (
    <div className="flex max-w-[72rem] flex-col gap-8">
      <div className="flex flex-col gap-3">
        <span className="eyebrow">{eyebrow} · <Link prefetch={false} href={`/private/${sec.slug}`} className="hover:text-ink">{sec.title}</Link></span>
        <h1 className="display text-[2.25rem] md:text-[3.25rem] leading-[1.04] max-w-[24ch]">{body.title}</h1>
      </div>
      {/* Figures are SVG the bundler checked element by element: drawing only, nothing that runs, links or fetches. */}
      {body.figures?.map((svg, i) => <figure key={i} className="panel overflow-x-auto p-3 [&>svg]:block [&>svg]:h-auto [&>svg]:min-w-[780px]" dangerouslySetInnerHTML={{ __html: svg }} />)}
      {table ? <TableView table={table} query={await searchParams} /> : (
        <div className="grid grid-cols-1 gap-x-12 gap-y-8 lg:grid-cols-[minmax(0,1fr)_19rem]">
          {/* The bundle's HTML is produced, escaped, by our own converter from our own private repository. */}
          <article className="prose-folio doc-html min-w-0 max-w-[66ch]" dangerouslySetInnerHTML={{ __html: body.html ?? "" }} />
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
      )}
      <nav aria-label="Previous and next" className="flex flex-wrap justify-between gap-4 border-t border-grid pt-4 text-sm">
        {prev ? <Link prefetch={false} href={`/private/${sec.slug}/${prev.slug}`} className={link}>← {prev.title}</Link> : <span />}
        {next ? <Link prefetch={false} href={`/private/${sec.slug}/${next.slug}`} className={link}>{next.title} →</Link> : null}
      </nav>
    </div>
  );
}
