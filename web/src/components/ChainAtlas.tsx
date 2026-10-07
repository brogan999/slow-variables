import Link from "next/link";
import type { AtlasBusiness, ChainAtlasDoc } from "@/lib/data";

const link = "underline decoration-grid underline-offset-2 hover:decoration-ink";
const tag = "ml-2 inline-block rounded-[2px] border border-axis px-1.5 align-[1px] font-mono text-[10px] uppercase tracking-[0.06em] text-ink-2";
const h4 = "text-[10.5px] font-semibold uppercase tracking-[0.1em] text-muted";

// The state of each row in the chosen future, as CSS: the export names every future, so the rules are written from it.
function states(d: ChainAtlasDoc): string {
  return d.futures.map((f) => {
    const on = `.chain-atlas:has(#ca-${f.key}:checked)`;
    return [
      `${on} [data-f="${f.key}"].ca-when, ${on} .ca-says[data-f="${f.key}"] { display: block; }`,
      `${on} .ca-strip i[data-f="${f.key}"] { outline: 2px solid var(--ink); outline-offset: 1px; }`,
      `${on} [data-${f.key}="unchanged"] { opacity: 0.5; }`,
      `${on} [data-${f.key}="stronger"] .ca-n { background: var(--ink); color: var(--background); }`,
      `${on} [data-${f.key}="weaker"] .ca-n { box-shadow: none; border: 1.5px dashed var(--ink-2); color: var(--ink-2); }`,
      `${on} [data-${f.key}="breaks"] .ca-n, ${on} [data-${f.key}="breaks"] .ca-name { text-decoration: line-through; color: var(--muted); }`,
    ].join("\n");
  }).join("\n");
}

function Row({ b }: { b: AtlasBusiness }) {
  const state = Object.fromEntries(b.marks.map((m) => [`data-${m.key}`, m.effect]));
  return (
    <details {...state} className="border-b border-grid bg-surface">
      <summary className="grid grid-cols-[2.1rem_minmax(0,1fr)] items-center gap-x-3 gap-y-1 px-3 py-2.5 md:grid-cols-[2.1rem_minmax(0,1fr)_auto_6.5rem]">
        <span className="ca-n">{b.n}</span>
        <span>
          <span className="ca-name text-[15px] font-semibold leading-snug">{b.name}</span>
          {b.stage ? <span className={tag}>{b.stage}</span> : null}
          {b.holds ? <span className={tag}>no future on the grid weakens it</span> : null}
          <span className="mt-0.5 block font-serif text-[15px] leading-snug text-ink-2">{b.take}</span>
        </span>
        <span className="ca-strip col-start-2 md:col-start-auto" role="img" aria-label={b.moved.length ? b.moved.map((m) => m.label).join("; ") : "No future on the grid changes it"}>
          {b.marks.map((m) => <i key={m.key} data-f={m.key} data-e={m.effect} title={m.label} />)}
        </span>
        <span className="col-start-2 font-mono text-[11px] text-ink-2 md:col-start-auto md:text-right">
          {b.marks.map((m) => <span key={m.key} data-f={m.key} className="ca-when">{m.effect === "unchanged" ? m.word : `${m.word} here`}</span>)}
        </span>
      </summary>
      <div className="grid gap-x-6 gap-y-3 px-3 pb-4 pt-1 text-[13px] text-ink-2 md:grid-cols-3 md:pl-[3.6rem]">
        <div><h4 className={h4}>The problem</h4><p>{b.problem}.</p></div>
        <div><h4 className={h4}>The profit, by the site&apos;s rule</h4><p>{b.profit}.</p></div>
        <div><h4 className={h4}>What would undo it</h4><p>{b.kills}</p></div>
        <div className="md:col-span-3">
          <h4 className={h4}>Future by future</h4>
          {b.moved.length ? (
            <ul className="flex flex-col gap-1">
              {b.moved.map((m) => <li key={m.key}><span className="font-medium text-ink">{m.label}.</span> {m.reason}</li>)}
            </ul>
          ) : <p>No future on the grid changes it. That is no judgement that it holds: the futures that bear on it are not on the grid yet.</p>}
        </div>
        <p className="md:col-span-3">Sits on {b.primary.number} {b.primary.name}. <Link href={b.href} className={link}>The full record: what it sells first, what it builds up and what would prove it wrong</Link></p>
        <p className="border-l-2 border-dotted border-axis pl-2 text-xs text-muted md:col-span-3">A model&apos;s judgement, not a reading: the call, the line under the name, what would undo it and each future&apos;s effect. The problem and the profit are the site&apos;s own record.</p>
      </div>
    </details>
  );
}

// The board: a call on each business, one radio per future, and every state already laid out by the export.
export function ChainAtlas({ d }: { d: ChainAtlasDoc }) {
  const rows = d.groups.flatMap((g) => g.businesses);
  return (
    <div className="chain-atlas flex flex-col gap-6">
      <style>{states(d)}</style>
      <fieldset className="flex flex-col gap-2 border-y border-grid py-3">
        <legend className="eyebrow">Assume a future</legend>
        <div className="flex flex-wrap gap-x-5 gap-y-1.5 text-sm">
          <label className="inline-flex items-center gap-1.5"><input type="radio" name="ca-future" id="ca-none" defaultChecked />No particular future</label>
          {d.futures.map((f) => <label key={f.key} className="inline-flex items-center gap-1.5"><input type="radio" name="ca-future" id={`ca-${f.key}`} />{f.name}</label>)}
        </div>
        <p className="ca-says font-serif text-[1.15rem] leading-snug text-ink max-w-[62ch]" data-f="none">With no future chosen, each strip shows every future at once: one mark for each, in the order above.</p>
        {d.futures.map((f) => <p key={f.key} className="ca-says font-serif text-[1.15rem] leading-snug text-ink max-w-[62ch]" data-f={f.key}>{f.says} <span className="font-sans text-xs text-muted">The outlook&apos;s own words for this future.</span></p>)}
        <p className="ca-key flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11px] text-ink-2">
          {d.effects.map((e) => <span key={e.id}><i data-e={e.id} />{e.word}</span>)}
          <span>each mark a model&apos;s judgement</span>
        </p>
      </fieldset>
      <div id="ca-board" className="flex flex-col gap-6 scroll-mt-24">
        {d.groups.map((g) => (
          <section key={g.id}>
            <header className="flex flex-wrap items-baseline gap-x-3 border-b-2 border-ink pb-1.5">
              <h2 className="text-xl font-bold tracking-tight">{g.name}</h2>
              <span className="font-serif text-[15px] text-ink-2">{g.says}</span>
            </header>
            {g.businesses.map((b) => <Row key={b.id} b={b} />)}
          </section>
        ))}
      </div>
      <details id="ca-table" className="fig p-3 scroll-mt-24">
        <summary className="font-mono text-[11px] uppercase tracking-[0.08em] text-ink-2">The table: every business in every future</summary>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full min-w-[56rem] text-[12.5px]">
            <thead><tr><th className="text-left align-bottom">Business</th>{d.futures.map((f) => <th key={f.key} className="px-1 text-left align-bottom text-[10.5px] font-semibold text-muted">{f.name}</th>)}</tr></thead>
            <tbody>
              {rows.map((b) => (
                <tr key={b.id} className="border-t border-grid">
                  <th scope="row" className="py-1 pr-2 text-left font-normal"><span className="font-mono text-muted">{b.n}</span> {b.name}</th>
                  {b.marks.map((m) => <td key={m.key} className={`px-1 ${m.effect === "unchanged" ? "text-muted" : "font-medium"}`}>{m.effect === "unchanged" ? "·" : m.word}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
      {d.made_by ? <p className="text-xs text-muted max-w-[72ch]">A model&apos;s judgement, not a reading. Made {d.made_by.date} by Claude, a model made by Anthropic ({d.made_by.model}). {d.made_by.method} Reviewed by {d.made_by.reviewed_by}. Nothing here is scored, and no status, tally or answer on the site reads it.</p> : null}
    </div>
  );
}
