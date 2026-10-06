import Link from "next/link";
import { Figure, Key } from "@/components/Figure";
import { KIND_LABEL, Swatch } from "@/components/diagrams/kit";
import { Arrow, Bar, Chip, ChipKey, Step } from "@/components/diagrams/opportunities";
import type { OpMark, OpportunitiesDoc } from "@/lib/data";

// The figures on /value-chain/opportunities. Every count, width and placing is the export's (opportunities.figures);
// where a business lands is the owner's judgement and each figure says so. One rule for hatching: a judged length or
// area is hatched; a judged yes-or-no mark or placing stays solid and carries the word "judgement" in its note and key.
const a = "text-ink underline decoration-axis underline-offset-2";
const th = "border-b border-ink py-1 pr-3 text-left font-medium text-ink-2";
const td = "border-b border-grid py-1 pr-3 align-top";
const marks = (d: OpportunitiesDoc) => Object.fromEntries(d.figures.marks.map((m) => [m.id, m])) as Record<string, OpMark>;
const Chips = ({ ids, by, plain }: { ids: string[]; by: Record<string, OpMark>; plain?: boolean }) => (
  <span className="flex flex-wrap gap-1">{ids.map((i) => <Chip key={i} m={by[i]} plain={plain} />)}</span>
);
const Name = ({ m }: { m: OpMark }) => (
  <span className="flex items-start gap-2 text-[13px] leading-tight"><Chip m={m} /><a href={`#op-${m.id}`} className="text-ink no-underline hover:underline">{m.name}</a></span>
);
const WhoKeys = () => (
  <>
    <Key swatch={<ChipKey pools="innovator" />}>the maker would keep the profit (the owner&apos;s judgement, by the rent rule)</Key>
    <Key swatch={<ChipKey pools="incumbents" />}>someone other than the maker would keep it (here, incumbent firms)</Key>
    <Key swatch={<ChipKey pools="users" />}>it would be competed away to users</Key>
  </>
);
const PlaceKey = () => <Key swatch={<span className="font-mono text-[11px] text-ink">n</span>}>its place in the list, not a rank; select it to read the card</Key>;

// Which number is which business, from the export's marks in the list's order: open under the section's opening
// sentence, folded inside the later figures that draw numbers alone.
export function NumberKey({ d, folded = false }: { d: OpportunitiesDoc; folded?: boolean }) {
  const list = (
    <ol className="columns-1 gap-x-6 text-[12.5px] leading-tight sm:columns-2 lg:columns-3">
      {d.figures.marks.map((m) => <li key={m.id} className="mb-1.5 flex break-inside-avoid items-start gap-2"><Chip m={m} /><a href={`#op-${m.id}`} className="pt-[3px] text-ink no-underline hover:underline">{m.name}</a></li>)}
    </ol>
  );
  if (!folded) return list;
  return (
    <details className="mb-3 border border-grid px-2.5 py-1.5">
      <summary className="cursor-pointer font-mono text-[11px] text-ink-2">Which number is which business</summary>
      <p className="mt-2 mb-2 text-[12px] text-muted">The number is only its place in the list, not a rank.</p>
      {list}
    </details>
  );
}

export function TurnModel({ d }: { d: OpportunitiesDoc }) {
  const o = d.opportunities.find((x) => x.id === d.figures.example);
  if (!o) return null;
  return (
    <Figure
      id="fig-turn"
      title="How a passing shortage becomes a lasting profit, and the two ways it fails"
      note={KIND_LABEL.model}
      keys={<>
        <Key swatch={<span className="inline-block h-3 w-4 border border-ink" />}>a step every card describes, under the card&apos;s own label</Key>
        <Key swatch={<span className="inline-block h-3 w-4 border border-dashed border-muted" />}>what stops the turn</Key>
        <Key swatch={<span className="font-serif text-[12px] italic">words</span>}>the worked example, in its record&apos;s own words</Key>
      </>}
      foot={<p>A drawing of the argument each card makes, not a measurement. The example is <a href={`#op-${o.id}`} className={a}>{o.name}</a>, the opening record in the list; every other card fills the same boxes. It does not show how likely any step is: nothing on this page is scored.</p>}
    >
      <div className="grid gap-1 md:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr] md:items-stretch">
        <Step label="The problem" head="A shortage" example={o.bottleneck}>Something the chain is short of today. Alone it passes: once relieved, the shortage moves elsewhere.</Step>
        <Arrow />
        <Step label="First step" head="One narrow thing to sell" example={o.wedge}>What the business sells first, to the buyers who feel the shortage most.</Step>
        <Arrow />
        <Step label="What it builds up" head="Something rivals cannot quickly copy" example={o.durable_asset}>A record, a standing or a habit that grows with each customer and still holds rivals off after the shortage eases.</Step>
        <Arrow />
        <Step label="Why that profit" head="A rent" example={`${o.rent.verdict}. ${o.rent_reason}`}>Profit beyond what keeps the business going, sized by the rent rule drawn below.</Step>
      </div>
      <div className="mt-3 grid gap-1 md:grid-cols-2">
        <Step broken label="Why a lab would not just bundle it" head="Fails if a larger firm gives it away" example={o.why_not_bundled}>A lab or a cloud can fold a service into what it already sells. Each card says why this one would be left alone.</Step>
        <Step broken label="Wrong if" head="Fails if the shortage ends another way" example={o.falsifier}>Each card names the event that would undo it, so the reader can watch for it.</Step>
      </div>
    </Figure>
  );
}

const ASK: Record<string, { q: string; then: string }> = {
  "appropriability=tight": { q: "Can the maker stop others copying it, by patent, secrecy or know-how that is hard to learn?", then: "If so" },
  "complementary_assets=specialised+asset_owner=innovator": { q: "If not: does the maker itself own what customers need in order to use it, something only a few hold?", then: "If so" },
  "complementary_assets=specialised": { q: "If not: does someone else own that?", then: "If so" },
  otherwise: { q: "Otherwise: it is easy to copy and nothing scarce stands in the way.", then: "So" },
};

// the rubric's raw answers, in the reader's words, for the folded tables
const YES: Record<string, string> = { tight: "yes", weak: "no" };
const NEEDS: Record<string, string> = { specialised: "something only a few hold", generic: "nothing scarce" };

export function WhoKeeps({ d }: { d: OpportunitiesDoc }) {
  const by = marks(d);
  return (
    <Figure
      id="fig-keeps"
      title="Who keeps the profit: the rule asks its questions in order, and the earliest that fits decides"
      note="A model of the rule; each placing is the owner's judgement"
      keys={<><WhoKeys /><PlaceKey /></>}
      foot={<p>The questions are the rent rule&apos;s, after David Teece, read top to bottom; the answers given for each business are the owner&apos;s judgement, and the result follows the rule. It shows who would keep a profit, not how large it is (the next figure) or whether the business gets built.</p>}
      table={
        <table className="w-full border-collapse text-[12px]">
          <thead><tr><th className={th}>Business</th><th className={th}>Can the maker stop copying?</th><th className={th}>What customers need to use it</th><th className={th}>Held by</th><th className={th}>Result</th></tr></thead>
          <tbody>{d.opportunities.map((o) => <tr key={o.id}><td className={td}>{by[o.id].n}. {o.name}</td><td className={td}>{YES[o.rent.appropriability]}</td><td className={td}>{NEEDS[o.rent.complementary_assets]}</td><td className={td}>{by[o.id].owner}</td><td className={td}>{o.rent.verdict}</td></tr>)}</tbody>
        </table>
      }
    >
      <ol className="flex flex-col">
        {d.figures.keeps.map((r, i) => (
          <li key={r.key} className={`grid gap-2 py-3 md:grid-cols-[minmax(0,1fr)_5rem_minmax(0,1.3fr)] md:items-center ${i ? "border-t border-grid" : ""}`}>
            <p className="text-[14px] leading-snug text-ink">{ASK[r.key]?.q ?? r.key}</p>
            <Arrow word={ASK[r.key]?.then} />
            <div className="flex flex-col gap-2">
              {r.groups.length ? r.groups.map((g) => (
                <div key={g.pools} className="flex flex-col gap-1.5 border border-grid p-2.5">
                  <span className="text-[13px] font-semibold text-ink">{g.pools === "users" ? "Competed away to users: no lasting profit" : `Kept by ${g.keeper}`}</span>
                  {g.ops.length ? <Chips ids={g.ops} by={by} /> : <span className="text-[12px] italic text-muted">no business on this page</span>}
                </div>
              )) : <span className="text-[12px] italic text-muted">no business on this page</span>}
            </div>
          </li>
        ))}
      </ol>
    </Figure>
  );
}

const KIND: Record<string, string> = {
  none: "Nothing holds rivals off",
  scarcity: "Scarcity: it holds something that cannot be expanded",
  switching_cost: "Switching costs: leaving would cost the customer",
  scale_network: "Scale or network: it gets better or cheaper as it grows",
  regulatory: "Regulation: a rule or a licence keeps others out",
};
const BAND: Record<string, string> = {
  none: "text-muted border border-grid", thin: "bg-surface-2 text-ink", moderate: "bg-s3 text-ink", fat: "bg-s2 text-surface", monopoly_like: "bg-s1 text-surface",
};

export function HowLarge({ d }: { d: OpportunitiesDoc }) {
  const by = marks(d);
  const { cols, rows } = d.figures.size;
  return (
    <Figure
      id="fig-size"
      title="How large the profit is: what holds rivals off, against how long it lasts"
      note="A model of the rule; each placing is the owner's judgement"
      keys={<>
        {["thin", "moderate", "fat", "monopoly_like"].map((t) => <Key key={t} swatch={<span className={`inline-block h-3 w-4 ${BAND[t]}`} />}>{t.replace("_", "-")}</Key>)}
        <WhoKeys />
        <PlaceKey />
      </>}
      foot={<p>Each cell is the size the rent rule gives, darker for larger; the cells are the rule&apos;s and are categories, not measurements. Which cell a business sits in is the owner&apos;s judgement. A dashed mark, set apart beneath a line, is a business the first figure sends to users: it would sit in that cell if anyone kept its profit, and keeps none of it. Short means the shortage is expected to move within a few years, medium within a decade or two, long only after decades. The rule is described in the <Link href="/methodology#futures" className={a}>method</Link>.</p>}
      table={
        <table className="w-full border-collapse text-[12px]">
          <thead><tr><th className={th}>Business</th><th className={th}>What holds rivals off</th><th className={th}>How long</th><th className={th}>Result</th></tr></thead>
          <tbody>{d.opportunities.map((o) => <tr key={o.id}><td className={td}>{by[o.id].n}. {o.name}</td><td className={td}>{(KIND[o.rent.rent_kind] ?? o.rent.rent_kind).split(":")[0]}</td><td className={td}>{o.rent.durability}</td><td className={td}>{o.rent.verdict}</td></tr>)}</tbody>
        </table>
      }
    >
      <NumberKey d={d} folded />
      <div className="grid grid-cols-3 gap-x-1 gap-y-1 md:grid-cols-[15rem_1fr_1fr_1fr]">
        <span className="hidden md:block" />
        {cols.map((c) => <span key={c} className="eyebrow pb-1 text-center">{c}</span>)}
        {rows.map((r) => (
          <div key={r.kind} className="contents">
            <span className="col-span-3 pt-2 text-[13px] leading-tight text-ink md:col-span-1 md:self-center md:pt-0 md:pr-3">{KIND[r.kind] ?? r.kind}</span>
            {r.cells.map((c, i) => (
              <div key={cols[i]} className="flex min-h-[4.25rem] flex-col border border-grid">
                <span className={`px-1.5 py-0.5 font-mono text-[10.5px] uppercase tracking-wide ${BAND[c.tier] ?? ""}`}>{c.word}</span>
                {c.ops.length ? <span className="p-1.5"><Chips ids={c.ops} by={by} /></span> : null}
                {c.away.length ? <span className="mt-auto flex flex-col gap-1 border-t border-muted p-1.5"><span className="text-[10.5px] leading-tight text-muted">competed away: keeps none of this</span><Chips ids={c.away} by={by} /></span> : null}
              </div>
            ))}
          </div>
        ))}
      </div>
      <p className="pt-2 text-center font-mono text-[11px] text-muted">how long before the shortage moves →</p>
    </Figure>
  );
}

export function ChainStrip({ d }: { d: OpportunitiesDoc }) {
  const by = marks(d);
  return (
    <Figure
      id="fig-chain"
      title="Where each business would sit on the value chain, and how many companies the map already holds there"
      note="Chart of each record's own placing"
      keys={<>
        <Key swatch={<span className="inline-flex h-[18px] min-w-[18px] items-center justify-center border-[1.5px] border-ink font-mono text-[11px] font-semibold text-ink">n</span>}>a boxed number sits in this part</Key>
        <Key swatch={<span className="font-mono text-[11px] text-muted">n</span>}>a plain number touches this part without sitting in it</Key>
        <WhoKeys />
        <Key swatch={<span className="font-mono text-[10px] text-muted">n on the map</span>}>companies the market map already lists in that part</Key>
        <Key swatch={<span className="inline-block h-3 w-4 border border-dashed border-grid" />}>a part no business here sits in or touches</Key>
      </>}
      foot={<p>Every part of the <Link href="/value-chain#market-map" className={a}>market map</Link>, in the map&apos;s order from physical inputs to applications, with each business in the part its record names and a plain number wherever it touches another. Where a business sits is the judgement in its record. An empty part means no business was written for it, not that none could be. The small count in each part is the number of companies the map lists there, and the part&apos;s name links to that list: these are companies in the same part of the map, not companies building this business, and a small count may mark where the tracker&apos;s coverage stops, not an empty market.</p>}
      table={
        <table className="w-full border-collapse text-[12px]">
          <thead><tr><th className={th}>Part of the chain</th><th className={th}>Sits here</th><th className={th}>Touches</th><th className={th}>Companies on the map</th><th className={th}>Independent</th><th className={th}>Bought, being bought or closed</th></tr></thead>
          <tbody>{d.figures.chain.flatMap((l) => l.categories).map((c) => <tr key={c.id}><td className={td}>{c.number} {c.name}</td><td className={td}>{c.primary.map((i) => by[i].name).join("; ") || "none"}</td><td className={td}>{c.adjacent.map((i) => by[i].name).join("; ") || "none"}</td><td className={td}>{c.n_entities}</td><td className={td}>{c.live}</td><td className={td}>{c.other}</td></tr>)}</tbody>
        </table>
      }
    >
      <NumberKey d={d} folded />
      <div className="flex flex-col gap-3">
        {d.figures.chain.map((l) => (
          <div key={l.id} className="grid gap-1.5 md:grid-cols-[13rem_1fr] md:gap-3">
            <div className="text-[13px] leading-tight text-ink">{l.number} {l.name}<span className="block font-mono text-[11px] text-muted">{l.n_primary ? `${l.n_primary} sit here` : "none sit here"}</span></div>
            <div className="grid grid-cols-2 gap-1 sm:grid-cols-4 lg:grid-cols-8">
              {l.categories.map((c) => {
                const empty = !c.primary.length && !c.adjacent.length;
                return (
                  <div key={c.id} className={`flex flex-col gap-1 border p-1.5 ${empty ? "border-dashed border-grid" : c.primary.length ? "border-ink" : "border-grid"}`}>
                    <Link href={`/value-chain#mm-${c.id}`} className={`text-[10.5px] leading-tight no-underline hover:underline ${empty ? "text-muted" : "text-ink-2"}`}><span className="font-mono">{c.number}</span> {c.name}</Link>
                    <span className="font-mono text-[10px] leading-none text-muted">{c.n_entities ? `${c.n_entities} on the map` : "not yet mapped"}</span>
                    {empty ? null : <span className="mt-auto flex flex-wrap items-center gap-x-1.5 gap-y-1">{c.primary.map((i) => <Chip key={i} m={by[i]} />)}{c.adjacent.map((i) => <Chip key={i} m={by[i]} plain />)}</span>}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </Figure>
  );
}

export function Demand({ d }: { d: OpportunitiesDoc }) {
  const by = marks(d);
  const { rows, off, unmet, kinds } = d.figures.demand;
  return (
    <Figure
      id="fig-demand"
      title="How many kinds of firm are marked with a need each business would meet"
      note="Chart of this site's judgement"
      keys={<>
        <Key swatch={<Swatch fill="var(--s1)" hatched />}>kinds of firm marked, on the kinds-of-firm page, with a need this business would meet (a judgement)</Key>
        <Key swatch={<Swatch fill="var(--tight-3)" hatched />}>kinds of firm with a need that no business here meets</Key>
        <Key swatch={<Swatch fill="var(--surface-2)" />}>the whole bar is every kind of firm that page describes, not every kind there is</Key>
        <WhoKeys />
        <PlaceKey />
      </>}
      foot={<p>A count of the kinds of firm on <Link href="/firm/kinds#needs" className={a}>what happens to each kind of firm</Link> that are marked with a need this business would meet; a kind is counted once however many of its needs point here. Where a need names more than one business, each is given every kind with that need, so businesses that share a need share a bar and the bars cannot be added. Breadth of need is not size of profit: a business may be needed by many kinds of firm and still keep nothing, as the dashed marks show. It counts kinds of firm, not firms, customers or money. The needs, the marks and the link from a need to a business were drafted by a model for that page in October 2026 and are that page&apos;s judgement, so the bars are hatched; they are not part of the owner&apos;s review of the records below, and the owner has not yet reviewed them.</p>}
      table={
        <table className="w-full border-collapse text-[12px]">
          <thead><tr><th className={th}>Business or unmet need</th><th className={th}>Kinds of firm</th><th className={th}>Which</th><th className={th}>Through the need</th></tr></thead>
          <tbody>
            {rows.map((r) => <tr key={r.id}><td className={td}>{by[r.id].n}. {by[r.id].name}</td><td className={td}>{r.count}</td><td className={td}>{r.kinds.join("; ")}</td><td className={td}>{r.needs.map((n) => n.name).join("; ")}</td></tr>)}
            {off.map((i) => <tr key={i}><td className={td}>{by[i].n}. {by[i].name}</td><td className={td} /><td className={td}>not on the grid</td><td className={td}>not on the grid</td></tr>)}
            {unmet.map((u) => <tr key={u.id}><td className={td}>No business listed: {u.name}</td><td className={td}>{u.count}</td><td className={td} /><td className={td}>{u.name}</td></tr>)}
          </tbody>
        </table>
      }
    >
      <div className="flex flex-col gap-2.5">
        {rows.map((r) => (
          <div key={r.id} className="grid gap-1 md:grid-cols-[20rem_1fr_4.5rem] md:items-center md:gap-3">
            <div>
              <Name m={by[r.id]} />
              <span className="block pl-[30px] text-[11px] leading-snug text-muted">{r.needs.map((n, i) => <span key={n.id}>{i ? "; " : ""}<Link href={n.href} className="underline decoration-grid underline-offset-2 hover:text-ink">{n.name}</Link></span>)}</span>
            </div>
            <Bar label={`${r.count} of ${kinds} kinds of firm`} segs={[{ key: "n", w: r.w, fill: "var(--s1)", hatched: true }]} />
            <span className="font-mono text-[12px] text-ink md:text-right">{r.count} of {kinds}</span>
          </div>
        ))}
      </div>
      {off.length ? (
        <>
          <h3 className="eyebrow mt-5 border-t border-grid pt-3">Not on that page&apos;s grid</h3>
          <div className="mt-2 grid gap-x-6 gap-y-1.5 sm:grid-cols-2">{off.map((i) => <Name key={i} m={by[i]} />)}</div>
          <p className="mt-2 max-w-[68ch] text-[12.5px] leading-snug text-ink-2">No need on that page names these businesses. That is a gap in the grid, not a finding that nobody would need them: some sell to labs, clouds and data-centre operators, which that page does not describe.</p>
        </>
      ) : null}
      <h3 className="eyebrow mt-5 border-t border-grid pt-3">Needs on that page that no business here meets</h3>
      <div className="mt-2 flex flex-col gap-2.5">
        {unmet.map((u) => (
          <div key={u.id} className="grid gap-1 md:grid-cols-[20rem_1fr_4.5rem] md:items-center md:gap-3">
            <Link href={u.href} className="text-[13px] leading-tight text-ink underline decoration-grid underline-offset-2">{u.name}</Link>
            <Bar label={`${u.count} of ${kinds} kinds of firm`} segs={[{ key: "n", w: u.w, fill: "var(--tight-3)", hatched: true }]} />
            <span className="font-mono text-[12px] text-ink md:text-right">{u.count} of {kinds}</span>
          </div>
        ))}
      </div>
    </Figure>
  );
}

// Not a figure: most rows carry a single mark and each card already prints its powers, so the grid is folded.
export function PowersTable({ d }: { d: OpportunitiesDoc }) {
  const by = marks(d);
  const p = d.figures.powers;
  return (
    <details className="fig fig-table" id="powers-table" style={{ borderTop: 0 }}>
      <summary>What each business would rely on to hold rivals off: the owner&apos;s judgement, as a table</summary>
      <div className="mt-3 flex flex-col gap-3">
      <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-[13px] leading-tight">
            <thead>
              <tr>
                <th scope="col" className="border-b border-ink py-2 pr-2 align-bottom font-medium text-ink-2">Business</th>
                {p.cols.map((c) => <th key={c} scope="col" className="w-[22px] border-b border-ink px-0 pb-2 align-bottom font-normal text-ink-2 md:w-24 md:px-0.5"><span className="block whitespace-nowrap [writing-mode:vertical-rl] rotate-180 md:rotate-0 md:whitespace-normal md:text-center md:[writing-mode:horizontal-tb]">{c}</span></th>)}
              </tr>
            </thead>
            <tbody>
              {p.rows.map((r) => (
                <tr key={r.id} className="border-b border-grid">
                  <th scope="row" className="py-1.5 pr-2 font-normal"><Name m={by[r.id]} /></th>
                  {r.cells.map((on, j) => <td key={p.cols[j]} className="px-0 text-center md:px-0.5">{on ? <span role="img" aria-label={p.cols[j]} className="inline-block h-2.5 w-2.5 rounded-full bg-ink" /> : <span aria-hidden className="inline-block h-2.5 w-2.5 rounded-full border border-grid" />}</td>)}
                </tr>
              ))}
              <tr>
                <th scope="row" className="py-1.5 pr-2 text-[12px] font-normal text-muted">Businesses naming it</th>
                {p.totals.map((n, j) => <td key={p.cols[j]} className="text-center font-mono text-[12px] text-ink">{n}</td>)}
              </tr>
            </tbody>
          </table>
        </div>
        <div className="flex flex-wrap gap-x-5 gap-y-1 font-mono text-[11px] text-ink-2">
          <Key swatch={<span className="inline-block h-2.5 w-2.5 rounded-full bg-ink" />}>the owner judges the business would build this power</Key>
          <Key swatch={<span className="inline-block h-2.5 w-2.5 rounded-full border border-grid" />}>it does not</Key>
        </div>
        <dl className="grid gap-1 text-[12.5px] leading-snug text-ink-2 md:grid-cols-2 md:gap-x-6">{p.cols.map((k) => <div key={k}><dt className="inline font-medium text-ink">{k}</dt>: <dd className="inline">{d.powers[k]}</dd></div>)}</dl>
        <p className="max-w-none text-[12px] text-muted">The powers are Hamilton Helmer&apos;s; which ones a business would build is the judgement in its record, in the list&apos;s order. The bottom row counts the businesses naming each.{p.unused.length ? ` No business here relies on ${p.unused.join(" or ")}.` : ""} A mark says what the business would rely on, not that it would succeed. These powers and the rent rule&apos;s account of what holds rivals off are separate judgements under separate schemes and need not match: a business can sit in the rule&apos;s regulation row and name switching costs here.</p>
      </div>
    </details>
  );
}
