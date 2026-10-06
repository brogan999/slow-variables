import Link from "next/link";
import { Figure, Key } from "@/components/Figure";
import { KIND_LABEL, ShareBars, Swatch } from "@/components/diagrams/kit";
import { CountBar, DIRECTION_ORDER, DIRECTION_WORD, JudgedChip, JudgedMark, JudgedPart, NO_RECORD, OWN_FILL, OWN_WORD, OwnSwatch, PartDot, UnjudgedMark } from "@/components/diagrams/valuechain";
import type { MarketMapDoc, OwnState, ValueChainFigures } from "@/lib/data";
import { fmt } from "@/lib/format";

// The value-chain page's figures (Part 45g). Every count, share and position is the export's. One convention with the
// rest of the site: a judged length or area takes the striped fill; a judged yes-or-no mark or placing, which is all
// this page draws, is solid (or a dashed outline) and says "judgement" in its note and its key.
const MIXED = "Chart for the counts, this site's judgement for the directions";
const JUDGED = "A chart of this site's judgements, not of measurements";
const PLACED = "A model of the rule; where each company lands is this site's judgement";
const SHORT_NAMES = "Short names are the tracker's own; each links to a plain statement of the judgement. RL is reinforcement learning, training by practice and grading; HBM is the fast memory stacked beside an AI chip; FDE is an engineer the seller places inside a customer; evals are tests of a model.";
const n = (v: number) => fmt(v, "count");
const link = "text-ink underline decoration-axis underline-offset-2";
const OWN: OwnState[] = ["independent", "bought", "closed"];

// The chain as one picture: the layers in order, how many companies the tracker follows in each, and where the page
// judges each part's economics to be heading.
export function ChainFigure({ f }: { f: ValueChainFigures["chain"] }) {
  return (
    <Figure
      id="fig-chain"
      title="The chain in one picture: where the companies are, and which way this site judges each part's profit is heading"
      note={MIXED}
      keys={<>
        <Key swatch={<Swatch fill="var(--s1)" />}>companies the tracker follows in the layer (a count)</Key>
        {DIRECTION_ORDER.map((d) => <Key key={d} swatch={<JudgedMark d={d} />}>{DIRECTION_WORD[d].toLowerCase()}, a judgement: {f.means[d]}</Key>)}
        <Key swatch={<UnjudgedMark />}>a part with companies in it and no judgement on this page yet</Key>
      </>}
      foot={<>
        <p>The layers run in the order work flows, from power and chips to the people who use the products. The bars count each company on the <a href="#market-map" className={link}>market map</a> below once, by the part of the chain the tracker files it under. The map sorts the same companies into its own finer layers and categories and lets a company sit in more than one, so its counts are larger and do not line up with these bars. The folded table lists the parts behind each bar. A bar is the tracker&apos;s reach, not the size of any market: a tall bar means many companies followed. The last layers hold none because the site reads them through surveys and statistics, not through companies.</p>
        <p>Each direction is a judgement, not a measurement, drafted by Claude, a model made by Anthropic, whose own part of the chain (frontier labs) is among those judged: follow it to read the argument, the view against it and what would prove it wrong. {n(f.n_unjudged_companies)} of the {n(f.n_companies)} companies sit in parts with no judgement yet, and {n(f.n_unfiled)} are on the map without a part of the chain. The parts with no judgement are ones the site has not yet written up, not ones it judged unimportant.</p>
        <p>{SHORT_NAMES}</p>
      </>}
      tableLabel="The numbers: companies followed and the judged direction, part by part"
      table={
        <table className="data">
          <thead><tr><th scope="col">Layer</th><th scope="col">Part of the chain</th><th scope="col">Companies followed</th><th scope="col">Direction, judged</th></tr></thead>
          <tbody>
            {f.layers.flatMap((l) => [
              ...l.parts.map((p) => <tr key={p.id}><td>{l.name}</td><th scope="row">{p.name}</th><td>{n(p.n)}</td><td>{p.direction ? DIRECTION_WORD[p.direction] : "no judgement yet"}</td></tr>),
              <tr key={l.id}><td>{l.name}</td><th scope="row">The whole layer</th><td>{n(l.n)}</td><td>{DIRECTION_ORDER.filter((d) => l.tally[d]).map((d) => `${n(l.tally[d])} ${DIRECTION_WORD[d].toLowerCase()}`).join(", ")}</td></tr>,
            ])}
            <tr><td>On the map without a part of the chain</td><th scope="row">{f.unfiled.join(", ")}</th><td>{n(f.n_unfiled)}</td><td>not filed under a part</td></tr>
          </tbody>
        </table>
      }
    >
      <div className="hidden md:block" role="group" aria-label="The layers of the chain left to right, with companies followed and judged directions">
        <div className="grid gap-x-3" style={{ gridTemplateColumns: `6.5rem repeat(${f.layers.length}, minmax(0, 1fr))` }}>
          <span />
          {f.layers.map((l, i) => (
            <div key={l.id} className="flex items-start gap-1 pb-2 text-[13px] font-semibold leading-tight text-ink">
              <span>{l.name}</span>{i < f.layers.length - 1 ? <span aria-hidden className="ml-auto font-normal text-muted">→</span> : null}
            </div>
          ))}
          <span className="self-end pb-1 font-mono text-[10.5px] uppercase leading-tight tracking-wider text-muted">Companies followed</span>
          {f.layers.map((l) => (
            <div key={l.id} className="flex h-28 flex-col justify-end border-b border-ink" title={`${l.name}: ${n(l.n)} companies followed`}>
              <span className="font-mono text-[12px] text-ink">{n(l.n)}</span>
              <div style={{ height: `${l.h}%`, background: "var(--s1)" }} />
            </div>
          ))}
          {DIRECTION_ORDER.map((d) => [
            <span key={d} className="border-b border-grid py-2 font-mono text-[10.5px] uppercase leading-tight tracking-wider text-muted">{DIRECTION_WORD[d]}<span className="block normal-case tracking-normal">judged</span></span>,
            ...f.layers.map((l) => (
              <div key={`${d}-${l.id}`} className="flex flex-col gap-1.5 border-b border-grid py-2">
                {l.marks[d].map((m) => <JudgedPart key={m.unit} d={d} name={m.name} title={m.title} href={m.href} />)}
              </div>
            )),
          ])}
          <span className="py-2 font-mono text-[10.5px] uppercase leading-tight tracking-wider text-muted">No judgement yet</span>
          {f.layers.map((l) => (
            <div key={l.id} className="flex flex-col gap-1.5 py-2">
              {l.unjudged.map((p) => <span key={p.id} className="flex items-start gap-1.5 text-[11.5px] leading-tight text-muted"><span className="mt-px flex"><UnjudgedMark /></span><span>{p.name}</span></span>)}
            </div>
          ))}
        </div>
      </div>
      <ol className="flex flex-col gap-4 md:hidden">
        {f.layers.map((l, i) => (
          <li key={l.id} className="flex flex-col gap-1.5">
            <div className="flex items-baseline gap-2 text-[13px] font-semibold text-ink">
              <span>{l.name}</span><span className="ml-auto font-mono text-[12px] font-normal">{n(l.n)}</span>
            </div>
            <div className="h-2.5 w-full bg-surface-2"><div className="h-full" style={{ width: `${l.h}%`, background: "var(--s1)" }} /></div>
            {DIRECTION_ORDER.filter((d) => l.marks[d].length).map((d) => (
              <div key={d} className="flex flex-col gap-1">
                <span className="font-mono text-[10.5px] uppercase tracking-wider text-muted">{DIRECTION_WORD[d]}, judged</span>
                {l.marks[d].map((m) => <JudgedPart key={m.unit} d={d} name={m.name} title={m.title} href={m.href} />)}
              </div>
            ))}
            {l.unjudged.length ? (
              <div className="flex flex-col gap-1">
                <span className="font-mono text-[10.5px] uppercase tracking-wider text-muted">No judgement yet</span>
                {l.unjudged.map((p) => <span key={p.id} className="flex items-start gap-1.5 text-[11.5px] leading-tight text-muted"><span className="mt-px flex"><UnjudgedMark /></span><span>{p.name}</span></span>)}
              </div>
            ) : null}
            {i < f.layers.length - 1 ? <span aria-hidden className="text-muted">↓</span> : null}
          </li>
        ))}
      </ol>
    </Figure>
  );
}

// Where the judged power is: each judged part of the chain against the kinds of lasting advantage. Two judgements, two
// marks: the part's own (a tint) and its single-part companies' (a number).
export function PowerGrid({ f }: { f: ValueChainFigures["powers"] }) {
  const cols = `minmax(7.5rem, 1fr) repeat(${f.cols.length}, minmax(1.5rem, 3.25rem))`;
  return (
    <Figure
      id="fig-powers"
      title="Where this site judges a lasting advantage exists today, and of which kind"
      note={JUDGED}
      keys={<>
        <Key swatch={<span className="inline-block h-3.5 w-3.5 bg-axis ring-1 ring-inset ring-ink-2" />}>the part&apos;s own judgement names this power as present today (a judgement)</Key>
        <Key swatch={<span className="inline-flex h-3.5 w-3.5 items-center justify-center font-mono text-[10px] text-ink ring-1 ring-inset ring-axis">n</span>}>a number: profiled companies in this part judged, each on its own, to hold the power (a judgement about companies, not about the part)</Key>
        <Key swatch={<span className="inline-block h-3.5 w-3.5 ring-1 ring-inset ring-grid" />}>neither</Key>
        {DIRECTION_ORDER.map((d) => <Key key={d} swatch={<JudgedMark d={d} />}>beside a part: judged {DIRECTION_WORD[d].toLowerCase()}</Key>)}
      </>}
      foot={<>
        <p>A <em>power</em> is a reason a firm keeps earning more than its rivals: a benefit that sits behind a barrier rivals cannot cross. The kinds are Hamilton Helmer&apos;s, each defined beside the grid. Every mark is this site&apos;s judgement, drafted by Claude, a model made by Anthropic, which is one of the frontier labs judged here: {n(f.n_units_naming)} of the {n(f.n_units)} judged parts name any power as present today.</p>
        <p>The two marks are separate judgements and they do not always agree. The tint judges the part as a whole; the number judges single companies, profiled one at a time. Most parts name no power while some companies inside them are credited with one: a company can hold an advantage its part of the chain does not. {f.multi.map((c) => c.name).join(", ")} are profiled in more than one part, so their powers are listed in the table and left out of the numbers. A blank row means no power was named, not that the part earns nothing.</p>
        <p>{SHORT_NAMES}</p>
      </>}
      tableLabel="The judgements: the powers each part names, and the profiled companies judged to hold each"
      table={<>
        <table className="data min-w-[40rem]">
          <thead><tr><th scope="col">Part of the chain</th><th scope="col">Direction, judged</th><th scope="col">Powers the part&apos;s judgement names</th><th scope="col">Companies profiled in this part alone, judged to hold a power</th></tr></thead>
          <tbody>{f.rows.map((r) => (
            <tr key={r.unit}><th scope="row">{r.name}</th><td>{DIRECTION_WORD[r.direction]}</td>
              <td>{r.cells.filter((c) => c.named).map((c) => c.power).join(", ") || "none named"}</td>
              <td>{r.cells.filter((c) => c.n).map((c) => `${c.power}: ${c.companies.join(", ")}`).join("; ") || (r.n_single ? "none judged to hold one" : "no company profiled in this part alone")}</td></tr>
          ))}</tbody>
        </table>
        <table className="data mt-4">
          <thead><tr><th scope="col">Company profiled in more than one part</th><th scope="col">The parts</th><th scope="col">Powers the company is judged to hold, not tied to either part</th></tr></thead>
          <tbody>{f.multi.map((c) => <tr key={c.entity}><th scope="row">{c.name}</th><td>{c.parts.join("; ")}</td><td>{c.powers.join(", ") || "none"}</td></tr>)}</tbody>
        </table>
        <table className="data mt-4">
          <thead><tr><th scope="col">Power</th><th scope="col">What it means</th></tr></thead>
          <tbody>{f.cols.map((p, i) => <tr key={p}><th scope="row">{p}</th><td>{f.gloss[i]}</td></tr>)}</tbody>
        </table>
      </>}
    >
      <div className="grid gap-x-8 gap-y-5 lg:grid-cols-[minmax(0,1fr)_17rem]">
        <div className="overflow-x-auto">
          <div role="group" aria-label="Each judged part of the chain against the kinds of power" className="grid w-full items-center gap-x-0.5 gap-y-1 sm:gap-x-1" style={{ gridTemplateColumns: cols }}>
            <span />
            {f.cols.map((p, i) => <span key={p} title={`${p}: ${f.gloss[i]}`} className="flex h-28 items-end justify-center pb-1"><span className="font-mono text-[11px] leading-none text-ink-2 [writing-mode:vertical-rl] rotate-180">{p}</span></span>)}
            {f.rows.map((r, i) => [
              i === 0 || f.rows[i - 1].layer !== r.layer ? <span key={`${r.unit}-layer`} className="col-span-full mt-2 border-b border-grid pb-0.5 font-mono text-[10.5px] uppercase tracking-wider text-muted">{r.layer_name}</span> : null,
              <Link key={r.unit} href={r.href} prefetch={false} className="flex items-start gap-1.5 text-[12px] leading-tight text-ink-2 hover:text-ink" title={`${r.name}: judged ${DIRECTION_WORD[r.direction].toLowerCase()}`}>
                <span className="mt-px flex"><JudgedMark d={r.direction} /></span><span>{r.label}</span>
              </Link>,
              ...r.cells.map((c, k) => (
                <span
                  key={`${r.unit}-${c.power}`}
                  title={`${r.name}, ${c.power} (${f.gloss[k]}): ${c.named ? "named in this part's judgement" : "not named in this part's judgement"}${c.n ? `; companies profiled in this part alone and judged to hold it: ${c.companies.join(", ")}` : ""}`}
                  className={`flex h-6 w-full items-center justify-center font-mono text-[11.5px] font-semibold leading-none text-ink ring-1 ring-inset ${c.named ? "bg-axis ring-ink-2" : c.n ? "ring-axis" : "ring-grid"}`}
                >
                  {c.n ? n(c.n) : null}
                </span>
              )),
            ])}
          </div>
        </div>
        <dl className="flex flex-col gap-2 self-start text-[12px] leading-snug text-ink-2">
          <dt className="font-mono text-[10.5px] uppercase tracking-wider text-muted">The kinds of power, in plain words</dt>
          {f.cols.map((p, i) => <dd key={p}><span className="font-semibold text-ink">{p}</span>: {f.gloss[i]}</dd>)}
        </dl>
      </div>
    </Figure>
  );
}

// The page's test for lasting profit, drawn as the steps the site's rent rule takes, with each profiled company at the
// step where the site's answers about it stop. No size word sits beside a name: the size is in the folded table.
export function RentRule({ f }: { f: ValueChainFigures["rent"] }) {
  return (
    <Figure
      id="fig-rent"
      title="Who keeps the profit: the questions this site asks of each company, and where its answers send each one"
      note={PLACED}
      keys={<>
        <Key swatch={<span className="inline-block h-3 w-4 border border-ink" />}>a question the rule asks, in order; the first yes settles it</Key>
        <Key swatch={<span className="inline-block h-3 w-4 border border-dashed border-ink-2" />}>a profiled company, placed by this site&apos;s answers about it (a judgement)</Key>
      </>}
      foot={<>
        <p>A <em>rent</em> is profit beyond what it takes to keep a business going, earned because something holds rivals off. The steps follow David Teece, an economist who studied why the firm that invents something often fails to keep the returns. The drawing shows the rule, which has no numbers of its own. How large a lasting profit the rule gives each business follows the kind of rent and how long it is judged to last, and is in the folded table: it is a lasting profit beyond a normal return, not what the company earns today.</p>
        <p>Where a company lands is this site&apos;s judgement. The answers about each were drafted by Claude, a model made by Anthropic, from the company&apos;s filings; Anthropic is itself placed here and competes with, sells to or buys from many of the others. Alex Brogan reviewed every profile before it was published, and the rule then decides. A company placed where whoever owns the scarce thing keeps the profit may itself be one of those owners; the rule files it there because others like it hold the same thing. Only companies the site has profiled appear, on each layer&apos;s page; a company on the map with no profile is absent, which is no judgement of it. Each placing judges the company&apos;s business inside the AI chain, not the whole company. None of it is advice to buy or sell, or a forecast of a share price.</p>
      </>}
      tableLabel="Each profiled company and how the rule reads its business in the AI chain"
      table={
        <table className="data min-w-[34rem]">
          <thead><tr><th scope="col">Company</th><th scope="col">The step that settles it</th><th scope="col">How the rule reads its business in the AI chain</th></tr></thead>
          <tbody>{f.steps.flatMap((s) => s.companies.map((c) => <tr key={c.entity}><th scope="row">{c.name}</th><td>{s.question}</td><td>{c.reads}</td></tr>))}</tbody>
        </table>
      }
    >
      <ol className="flex flex-col">
        {f.steps.map((s, i) => {
          const last = i === f.steps.length - 1;
          const owners = [...new Set(s.companies.map((c) => c.goes_to))];
          return (
            <li key={s.question} className="grid gap-x-3 gap-y-2 md:grid-cols-[minmax(0,1fr)_3.5rem_minmax(0,1.5fr)]">
              <div className="flex flex-col">
                <div className={`flex flex-col gap-1 border p-3 ${last ? "border-dashed border-axis" : "border-ink"}`}>
                  <span className="text-[14px] font-semibold leading-snug text-ink">{s.question}</span>
                  <span className="text-[12.5px] leading-snug text-ink-2">{s.why}</span>
                </div>
                {last ? null : <span aria-hidden className="hidden py-1 pl-4 font-mono text-[11px] text-muted md:block">no ↓</span>}
              </div>
              <span className="pt-0 font-mono text-[11px] text-muted md:pt-4 md:text-center">{last ? "so →" : "yes →"}</span>
              <div className="flex flex-col gap-2 pb-2 md:pb-5">
                <span className="border-l-2 border-ink pl-2 text-[14px] font-semibold leading-snug text-ink">{s.keeps}</span>
                {owners.map((o) => (
                  <div key={o ?? "self"} className="flex flex-wrap items-center gap-1 pl-2.5">
                    {o ? <span className="w-full pt-0.5 text-[11.5px] leading-snug text-muted">Judged to go to {o}:</span> : null}
                    {s.companies.filter((c) => c.goes_to === o).map((c) => <JudgedChip key={c.entity} name={c.name} tip={`${c.name}, its business in the AI chain: ${c.reads} (this site's judgement)`} />)}
                  </div>
                ))}
                {s.companies.length ? null : <span className="pl-2.5 text-[12px] text-muted">No profiled company stops here.</span>}
              </div>
              {last ? null : <span aria-hidden className="pb-1 pl-4 font-mono text-[11px] text-muted md:hidden">no ↓</span>}
            </li>
          );
        })}
      </ol>
    </Figure>
  );
}

// How firm the map is: the share of each layer's companies that carry the tracker's verified flag.
export function VerifiedBars({ m }: { m: MarketMapDoc }) {
  const f = m.figures.verified;
  return (
    <Figure
      id="fig-verified"
      title="How much of the map is verified: the share of each layer's companies that carry the tracker's verified flag"
      note={KIND_LABEL.chart}
      keys={<>
        <Key swatch={<Swatch fill="var(--s1)" />}>verified: the tracker&apos;s record ties the company to a filing or to a row in a dataset (bold on the map)</Key>
        <Key swatch={<Swatch fill={NO_RECORD} />}>not yet verified: no such check is recorded</Key>
      </>}
      foot={<p>Each bar is all the companies the map places in a layer, counted once. Verified is a flag on the tracker&apos;s own record of a company; the tracker&apos;s notes do not say who set each flag or when. It says the company itself was matched to a record; it does not say a person reviewed where the company sits on the map, and it says nothing about how good the company is. A company not yet verified has simply not been through that check; nothing here says its entry is wrong. The last bar is the whole map.</p>}
      table={
        <table className="data">
          <thead><tr><th scope="col">Layer</th><th scope="col">Companies</th><th scope="col">Verified</th><th scope="col">Not yet verified</th><th scope="col">Share verified</th></tr></thead>
          <tbody>{f.rows.map((r) => <tr key={r.id}><th scope="row">{r.name}</th><td>{n(r.n)}</td><td>{n(r.n_verified)}</td><td>{n(r.n_unverified)}</td><td>{fmt(r.share_verified, "share")}</td></tr>)}</tbody>
        </table>
      }
    >
      <ShareBars
        label="The share of each layer's companies that carry the tracker's verified flag"
        rows={f.rows.map((r) => ({
          name: r.name,
          note: `${fmt(r.share_verified, "share")} · ${n(r.n_verified)} of ${n(r.n)}`,
          segs: r.segs.map((s) => ({ key: s.state, x: s.x, w: s.w, fill: s.state === "verified" ? "var(--s1)" : NO_RECORD, tip: `${r.name}: ${n(s.state === "verified" ? r.n_verified : r.n_unverified)} ${s.state === "verified" ? "verified" : "not yet verified"}` })),
        }))}
      />
    </Figure>
  );
}

// Company counts by category on one scale, split by recorded ownership state, with each category's parts as dots:
// filled where the map holds a company, an empty ring where it holds none.
export function CategoryBars({ m }: { m: MarketMapDoc }) {
  const f = m.figures.categories;
  const cov = m.figures.coverage;
  return (
    <Figure
      id="fig-categories"
      title="How many companies the map holds in each category, with the few recorded as bought or closed marked, and the parts of each category where it has placed none"
      note={KIND_LABEL.chart}
      keys={<>
        {OWN.map((s) => <Key key={s} swatch={<OwnSwatch s={s} />}>{OWN_WORD[s]} (counted {n(f.totals[s])} times across the categories)</Key>)}
        <Key swatch={<PartDot filled tip="a part with a company" />}>a part of the category with a company placed in it</Key>
        <Key swatch={<PartDot filled={false} tip="a part with no company" />}>a part with none yet</Key>
      </>}
      foot={<>
        <p>Each bar counts the companies the map places in a category, on a shared scale: the longest bar is the fullest category. A long bar means the tracker follows many companies there; it does not measure the market&apos;s size, its sales or its importance. A company placed in more than one category is counted in each. A company in more than one part of a category is counted once in it, so these counts add to slightly fewer than the placements above. Bought, being bought and closed are the states recorded on each company, with who and when in the card&apos;s list below; the split shows ownership only where the tracker has recorded it. A company with no recorded state is drawn pale, so the dark and outlined segments are a floor: some sales sit in the tracker&apos;s notes and have not yet been recorded as a state.</p>
        <p>A category is split into parts, the finest grain of the map, drawn as the dots at the end of its row. An empty ring says where the tracker&apos;s coverage stops, not that nobody sells there: {n(cov.n_empty)} of the {n(cov.n_parts)} parts in scope hold no company yet. The category set aside as out of scope, which holds the remaining parts, is left out.</p>
        <p>Categories holding few companies ({n(cov.thin_at)} or fewer): {cov.thin.map((t, i) => <span key={t.id}>{i ? ", " : ""}<a href={`#mm-${t.id}`} className={link}>{t.name}</a> ({n(t.n)})</span>)}. Thin here is a property of the tracker, too.</p>
      </>}
      tableLabel="The numbers: companies in each category by ownership state, with the name of every part that holds no company"
      table={<>
        <table className="data min-w-[46rem]">
          <thead><tr><th scope="col">Category</th><th scope="col">Layer</th><th scope="col">Companies</th><th scope="col">No sale or closure recorded</th><th scope="col">Bought, or being bought</th><th scope="col">Closed</th><th scope="col">The parts with no company</th></tr></thead>
          <tbody>{f.layers.flatMap((l) => l.rows.map((r) => (
            <tr key={r.id}><th scope="row">{r.number} {r.name}</th><td>{l.name}</td><td>{r.out_of_scope ? "out of scope for now" : n(r.n)}</td>{r.segs.map((s) => <td key={s.state}>{n(s.n)}</td>)}
              <td className="text-muted">{r.out_of_scope ? "out of scope for now" : r.leaves.filter((p) => !p.n).map((p) => p.name).join("; ") || "none"}</td></tr>
          )))}</tbody>
        </table>
        <table className="data mt-4">
          <thead><tr><th scope="col">Layer</th><th scope="col">Parts in scope</th><th scope="col">With a company</th><th scope="col">With none</th><th scope="col">Companies placed in a category but in no part</th></tr></thead>
          <tbody>{cov.rows.map((r) => <tr key={r.id}><th scope="row">{r.name}</th><td>{n(r.n_parts)}</td><td>{n(r.n_covered)}</td><td>{n(r.n_empty)}</td><td>{n(r.n_unassigned)}</td></tr>)}</tbody>
        </table>
      </>}
    >
      <div className="grid gap-x-8 gap-y-4 lg:grid-cols-2">
        {f.layers.map((l) => (
          <div key={l.id} role="group" aria-label={l.name} className="flex flex-col gap-1.5">
            <div className="border-b border-grid pb-0.5 text-[12.5px] font-semibold leading-tight text-ink"><span className="mr-2 font-mono text-[10.5px] font-normal text-muted">Layer {l.number}</span>{l.name}</div>
            {l.rows.map((r) => (
              <a key={r.id} href={`#mm-${r.id}`} className="grid grid-cols-[8.5rem_minmax(0,1fr)] items-center gap-x-2 gap-y-1 sm:grid-cols-[11.5rem_minmax(0,1fr)_6.25rem]">
                <span className="text-[12px] leading-tight text-ink-2">{r.name}</span>
                {r.out_of_scope ? <span className="font-mono text-[11px] text-muted">out of scope for now</span> : (
                  <CountBar end={r.w} count={n(r.n)} segs={r.segs.map((s) => ({ key: s.state, x: s.x, w: s.w, fill: OWN_FILL[s.state], outline: s.state === "closed", tip: `${r.name}: ${n(s.n)} ${OWN_WORD[s.state]}` }))} />
                )}
                {r.out_of_scope ? null : (
                  <span role="img" aria-label={`${r.name}: the parts of the category, filled where the map holds a company`} className="col-start-2 flex flex-wrap gap-[3px] sm:col-start-3">
                    {r.leaves.map((p) => <PartDot key={p.name} filled={p.n > 0} tip={`${r.name}: ${p.name}, ${p.n ? `${n(p.n)} placed` : "no company yet"}`} />)}
                  </span>
                )}
              </a>
            ))}
          </div>
        ))}
      </div>
    </Figure>
  );
}
