import Link from "next/link";
import type { AtlasBusiness, AtlasTile, ChainAtlasDoc } from "@/lib/data";
import { ChainAtlasMap } from "./ChainAtlasMap";

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
      `${on} [data-${f.key}="unchanged"] { opacity: 0.62; }`,
      `${on} [data-${f.key}="stronger"] .ca-n { background: var(--ink); color: var(--background); }`,
      `${on} [data-${f.key}="weaker"] .ca-n { box-shadow: none; border: 1.5px dashed var(--ink-2); color: var(--ink-2); }`,
      `${on} [data-${f.key}="breaks"] .ca-n, ${on} [data-${f.key}="breaks"] .ca-name { text-decoration: line-through; color: var(--muted); }`,
    ].join("\n");
  }).join("\n");
}

function Row({ b }: { b: AtlasBusiness }) {
  const state = Object.fromEntries(b.marks.map((m) => [`data-${m.key}`, m.effect]));
  return (
    <details {...state} className="ca-row border-b border-grid bg-surface">
      <summary className="grid grid-cols-[2.1rem_minmax(0,1fr)] items-center gap-x-3 gap-y-1 px-3 py-2.5 md:grid-cols-[2.1rem_minmax(0,1fr)_auto_6.5rem]">
        <span className="ca-n">{b.n}</span>
        <span>
          <span className="ca-name text-[15px] font-semibold leading-snug underline decoration-grid decoration-dotted underline-offset-4">{b.name}</span>
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
        <div><h3 className={h4}>The problem</h3><p>{b.problem}.</p></div>
        <div><h3 className={h4}>The profit, by the site&apos;s rule</h3><p>{b.profit}.</p></div>
        <div><h3 className={h4}>What would overturn this call</h3><p>{b.kills}</p></div>
        <div className="md:col-span-3">
          <h3 className={h4}>Future by future</h3>
          {b.moved.length ? (
            <ul className="flex flex-col gap-1">
              {b.moved.map((m) => <li key={m.key}><span className="font-medium text-ink">{m.label}.</span> {m.reason}</li>)}
            </ul>
          ) : <p>No future on the grid changes it. That is no judgement that it holds: the futures that bear on it are not on the grid yet.</p>}
        </div>
        <p className="md:col-span-3">Sits on <Link href={b.primary.href} className={link}>{b.primary.number} {b.primary.name}</Link>. <Link href={b.href} className={link}>The full record: what it sells first, what it builds up and what would prove it wrong</Link></p>
        <p className="border-l-2 border-dotted border-axis pl-2 text-xs text-muted md:col-span-3">A model&apos;s judgement, not a reading: the call, the line under the name, what would overturn it and each future&apos;s effect. The problem, the profit and its place in the order of bets are the site&apos;s own record.</p>
      </div>
    </details>
  );
}

// One part of the chain under "the ground": what is scarce, the three words, and what each future does to it.
function Ground({ c }: { c: AtlasTile }) {
  const base = c.states.none;
  return (
    <details className="ca-row border-b border-grid bg-surface">
      <summary className="grid grid-cols-[2.6rem_minmax(0,1fr)] items-baseline gap-x-3 px-3 py-2">
        <span className="font-mono text-[12px] text-muted">{c.number}</span>
        <span>
          <span className="ca-name text-[15px] font-semibold leading-snug underline decoration-grid decoration-dotted underline-offset-4">{c.name}</span>
          {c.businesses.map((n) => <span key={n} className={tag}>business {n}</span>)}
          <span className="mt-0.5 block text-[13px] leading-snug text-ink-2">{c.scarce}: {base.now.word} now, {base.mature.word} at the mature state.</span>
        </span>
      </summary>
      <div className="flex flex-col gap-2 px-3 pb-4 pt-1 text-[13px] text-ink-2 md:pl-[4.1rem]">
        <p>{c.reason} In the transition: {base.transition.word}.</p>
        {c.moved.length ? <ul className="flex flex-col gap-1">{c.moved.map((m) => <li key={m.key}><span className="font-medium text-ink">{m.name}: {m.word}.</span> {m.reason}</li>)}</ul> : <p>No future on the grid is judged to move it.</p>}
        <p><Link href={c.href} className={link}>{c.n_entities ? "The companies the site places here" : "This part on the map"}</Link>{c.n_entities ? ", each with a link to have Ask reason it through." : ": the tracker has placed no independent company here yet."}</p>
        <p className="border-l-2 border-dotted border-axis pl-2 text-xs text-muted">A model&apos;s judgement, not a reading{base.now.measured ? ", except the word for now, which is tonight’s reading" : ""}: what is scarce, each word, the reason and each future&apos;s move.</p>
      </div>
    </details>
  );
}

// The board: a call on each business, one radio per future, and every state already laid out by the export.
export function ChainAtlas({ d }: { d: ChainAtlasDoc }) {
  const rows = d.groups.flatMap((g) => g.businesses);
  const tiles = new Map(d.map.layers.flatMap((l) => l.categories).map((c) => [c.id, c]));
  return (
    <div className="chain-atlas flex flex-col gap-6">
      <style>{states(d)}</style>
      <fieldset className="flex flex-col gap-2 border-y border-grid py-3">
        <legend className="eyebrow">Assume a future</legend>
        <div className="flex flex-wrap gap-x-5 gap-y-1.5 text-sm">
          <label className="inline-flex items-center gap-1.5"><input type="radio" name="ca-future" id="ca-none" value="none" defaultChecked />No particular future</label>
          {d.futures.map((f) => <label key={f.key} className="inline-flex items-center gap-1.5"><input type="radio" name="ca-future" id={`ca-${f.key}`} value={f.key} />{f.name}</label>)}
        </div>
        <p className="ca-says font-serif text-[1.15rem] leading-snug text-ink max-w-[62ch]" data-f="none">With no future chosen, each strip shows every future at once: one mark for each, in the order above.</p>
        {d.futures.map((f) => <p key={f.key} className="ca-says font-serif text-[1.15rem] leading-snug text-ink max-w-[62ch]" data-f={f.key}>{f.says} <span className="font-sans text-xs text-muted">The <Link href="/outlook#scenarios" className={link}>outlook</Link>&apos;s own words for this future; the writers who argue it are named there.</span></p>)}
        <p className="ca-key flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11px] text-ink-2">
          {d.effects.map((e) => <span key={e.id}><i data-e={e.id} />{e.word}</span>)}
          <span>each mark a model&apos;s judgement</span>
        </p>
        <div className="flex flex-wrap items-baseline gap-x-5 gap-y-1.5 border-t border-grid pt-2 text-sm">
          <span className="eyebrow">At this point in time</span>
          {d.times.map((t, i) => <label key={t.id} className="inline-flex items-center gap-1.5" title={t.says}><input type="radio" name="ca-time" value={t.id} defaultChecked={i === 0} />{t.name}</label>)}
          <span className="text-xs text-muted">Time changes the map; a future never changes what is read now.</span>
        </div>
        {d.not_judged.map((n) => <p key={n.name} className="text-xs text-muted max-w-[72ch]">Not judged, and so not on the list: {n.name}. {n.why}</p>)}
      </fieldset>
      <section id="ca-map" className="flex flex-col gap-2 scroll-mt-24">
        <h2 className="text-xl font-bold tracking-tight">The chain, and what is scarce on it</h2>
        <p className="text-sm text-ink-2 max-w-[72ch]">Each tile is one part of the value chain, from power on the left to applications on the right, and it never moves. Its shade says how short that part is of the thing it most needs. {d.times.map((t) => <span key={t.id}><em>{t.name}</em>: {t.says} </span>)}A tile leads to the companies on that part of the chain.</p>
        <ChainAtlasMap layers={d.map.layers} />
      </section>
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
      <section id="ca-ground" className="flex flex-col gap-6 scroll-mt-24">
        <div>
          <h2 className="text-xl font-bold tracking-tight">The ground under today&apos;s companies</h2>
          <p className="text-sm text-ink-2 max-w-[72ch]">Every part of the chain, sorted by where its shortage is heading between now and the mature state with no future chosen. Open a part for the reason, what each future does to it, and the companies the site places there, each of which can be put to Ask.</p>
        </div>
        {d.ground.map((g) => (
          <div key={g.id}>
            <header className="flex flex-wrap items-baseline gap-x-3 border-b-2 border-ink pb-1.5">
              <h3 className="text-lg font-bold tracking-tight">{g.name}</h3>
              <span className="font-serif text-[15px] text-ink-2">{g.says}</span>
            </header>
            {g.categories.map((id) => <Ground key={id} c={tiles.get(id)!} />)}
          </div>
        ))}
      </section>
      <details id="ca-table" className="fig p-3 scroll-mt-24">
        <summary className="font-mono text-[11px] uppercase tracking-[0.08em] text-ink-2">The table: every business in every future, each cell a model&apos;s judgement</summary>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full min-w-[56rem] text-[12.5px]">
            <thead><tr><th scope="col" className="text-left align-bottom">Business</th>{d.futures.map((f) => <th key={f.key} scope="col" className="px-1 text-left align-bottom text-[10.5px] font-semibold text-muted">{f.name}</th>)}</tr></thead>
            <tbody>
              {rows.map((b) => (
                <tr key={b.id} className="border-t border-grid">
                  <th scope="row" className="py-1 pr-2 text-left font-normal"><span className="font-mono text-muted">{b.n}</span> {b.name}</th>
                  {b.marks.map((m) => <td key={m.key} className={`px-1 ${m.effect === "unchanged" ? "text-muted" : "font-medium"}`}>{m.effect === "unchanged" ? <><span aria-hidden>·</span><span className="sr-only">{m.word}</span></> : m.word}</td>)}
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
