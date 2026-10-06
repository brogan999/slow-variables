import Link from "next/link";
import { Figure, Key } from "@/components/Figure";
import { KIND_LABEL, ShareBars, Swatch } from "@/components/diagrams/kit";
import { CountBar, DIRECTION_ORDER, DIRECTION_WORD, JudgedChip, JudgedMark, JudgedPart, OWN_FILL, OWN_WORD, OwnSwatch, PartDot, UnjudgedMark } from "@/components/diagrams/valuechain";
import type { MarketMapDoc, OwnState, ValueChainFigures } from "@/lib/data";
import { fmt } from "@/lib/format";

// The value-chain page's figures (Part 45g). Every count, share and position is the export's. Hatching and dashed
// outlines are kept for this site's judgement; the market map's own records are plain fills.
const MIXED = "Chart for the counts, this site's judgement for the directions";
const JUDGED = "A chart of this site's judgements, not of measurements";
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
        {DIRECTION_ORDER.map((d) => <Key key={d} swatch={<JudgedMark d={d} />}>judged {DIRECTION_WORD[d].toLowerCase()}: {f.means[d]}</Key>)}
        <Key swatch={<UnjudgedMark />}>a part with companies in it and no judgement on this page yet</Key>
      </>}
      foot={<>
        <p>The layers run in the order work flows, from power and chips to the people who use the products. The bars count the companies on the <a href="#market-map" className={link}>market map</a> below by the part of the chain the tracker files each under. That is the tracker&apos;s reach, not the size of any market: a tall bar means many companies followed. The last layers hold none because the site reads them through surveys and statistics, not through companies.</p>
        <p>Each hatched mark is a judgement drafted by a model, not a measurement: follow it to read the argument, the view against it and what would prove it wrong. {n(f.n_unjudged_companies)} of the {n(f.n_companies)} companies sit in parts with no judgement yet, and {n(f.n_unfiled)} are on the map without a part of the chain.</p>
      </>}
      tableLabel="The numbers: companies followed and the judged direction, part by part"
      table={
        <table className="data">
          <thead><tr><th scope="col">Layer</th><th scope="col">Part of the chain</th><th scope="col">Companies followed</th><th scope="col">Direction, judged</th></tr></thead>
          <tbody>{f.layers.flatMap((l) => [
            ...l.parts.map((p) => <tr key={p.id}><td>{l.name}</td><th scope="row">{p.name}</th><td>{n(p.n)}</td><td>{p.direction ? DIRECTION_WORD[p.direction] : "no judgement yet"}</td></tr>),
            <tr key={l.id}><td>{l.name}</td><th scope="row">The whole layer</th><td>{n(l.n)}</td><td>{DIRECTION_ORDER.filter((d) => l.tally[d]).map((d) => `${n(l.tally[d])} ${DIRECTION_WORD[d].toLowerCase()}`).join(", ")}</td></tr>,
          ])}</tbody>
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

// Where the judged power is: each judged part of the chain against the kinds of lasting advantage.
export function PowerGrid({ f }: { f: ValueChainFigures["powers"] }) {
  const cols = `minmax(7.5rem, 17rem) repeat(${f.cols.length}, minmax(1.5rem, 3.25rem))`;
  return (
    <Figure
      id="fig-powers"
      title="Where this site judges a lasting advantage exists today, and of which kind"
      note={JUDGED}
      keys={<>
        <Key swatch={<span className="hatch inline-block h-3.5 w-3.5 ring-1 ring-inset ring-current" style={{ color: "var(--s2)" }} />}>the page&apos;s judgement of this part names the power as present today</Key>
        <Key swatch={<span className="inline-flex h-3.5 w-3.5 items-center justify-center font-mono text-[10px] text-ink ring-1 ring-inset ring-axis">n</span>}>how many of the companies profiled in this part are judged to hold it</Key>
        <Key swatch={<span className="inline-block h-3.5 w-3.5 ring-1 ring-inset ring-grid" />}>neither</Key>
      </>}
      foot={<>
        <p>A <em>power</em> is a reason a firm keeps earning more than its rivals: a benefit that sits behind a barrier rivals cannot cross. The kinds are Hamilton Helmer&apos;s; &ldquo;What the powers mean&rdquo; above defines each. Every mark is this site&apos;s judgement, drafted by a model from company filings: {n(f.n_units_naming)} of the {n(f.n_units)} judged parts name any power as present today.</p>
        <p>The counts read the {n(f.n_profiles)} company profiles, which were judged one company at a time. A company profiled in more than one part is counted in each, so a count can credit a part with a power the company earns elsewhere. A blank row means no power was named, not that the part earns nothing.</p>
      </>}
      tableLabel="The judgements: the powers each part names, and the profiled companies judged to hold each"
      table={
        <table className="data">
          <thead><tr><th scope="col">Part of the chain</th><th scope="col">Direction, judged</th><th scope="col">Powers the part&apos;s judgement names</th><th scope="col">Profiled companies judged to hold a power</th></tr></thead>
          <tbody>{f.rows.map((r) => (
            <tr key={r.unit}><th scope="row">{r.name}</th><td>{DIRECTION_WORD[r.direction]}</td>
              <td>{r.cells.filter((c) => c.named).map((c) => c.power).join(", ") || "none named"}</td>
              <td>{r.cells.filter((c) => c.n).map((c) => `${c.power}: ${c.companies.join(", ")}`).join("; ") || (r.n_profiles ? "none judged to hold one" : "no company profiled")}</td></tr>
          ))}</tbody>
        </table>
      }
    >
      <div className="overflow-x-auto">
        <div role="group" aria-label="Each judged part of the chain against the kinds of power" className="grid w-full max-w-[42rem] items-center gap-x-0.5 gap-y-1 sm:gap-x-1" style={{ gridTemplateColumns: cols }}>
          <span />
          {f.cols.map((p) => <span key={p} className="flex h-28 items-end justify-center pb-1"><span className="font-mono text-[11px] leading-none text-ink-2 [writing-mode:vertical-rl] rotate-180">{p}</span></span>)}
          {f.rows.map((r, i) => [
            i === 0 || f.rows[i - 1].layer !== r.layer ? <span key={`${r.unit}-layer`} className="col-span-full mt-2 border-b border-grid pb-0.5 font-mono text-[10.5px] uppercase tracking-wider text-muted">{r.layer_name}</span> : null,
            <Link key={r.unit} href={r.href} prefetch={false} className="flex items-start gap-1.5 text-[12px] leading-tight text-ink-2 hover:text-ink" title={`${r.name}: judged ${DIRECTION_WORD[r.direction].toLowerCase()}`}>
              <span className="mt-px flex"><JudgedMark d={r.direction} /></span><span>{r.name}</span>
            </Link>,
            ...r.cells.map((c) => (
              <span
                key={`${r.unit}-${c.power}`}
                title={`${r.name}, ${c.power}: ${c.named ? "named in this part's judgement" : "not named in this part's judgement"}${c.n ? `; profiled companies judged to hold it: ${c.companies.join(", ")}` : ""}`}
                className={`flex h-6 w-full items-center justify-center ring-1 ring-inset ${c.named ? "hatch ring-current" : c.n ? "ring-axis" : "ring-grid"}`}
                style={{ color: "var(--s2)" }}
              >
                {c.n ? <span className="bg-surface px-1.5 py-px font-mono text-[11.5px] font-semibold leading-[1.3] text-ink">{n(c.n)}</span> : null}
              </span>
            )),
          ])}
        </div>
      </div>
    </Figure>
  );
}

// The page's test for lasting profit, drawn as the steps the site's rent rule takes, with each profiled company at the
// step where the site's answers about it stop.
export function RentRule({ f }: { f: ValueChainFigures["rent"] }) {
  return (
    <Figure
      id="fig-rent"
      title="Who keeps the profit: the questions this site asks of each company, and where its answers send each one"
      note={KIND_LABEL.model}
      keys={<>
        <Key swatch={<span className="inline-block h-3 w-4 border border-ink" />}>a question the rule asks, in order; the first yes settles it</Key>
        <Key swatch={<span className="inline-block h-3 w-4 border border-dashed border-ink-2" />}>a profiled company, placed by this site&apos;s answers about it (a judgement)</Key>
        <Key swatch={<span className="font-mono text-[10.5px] text-muted">thin</span>}>the word after a name: how large the rule reads the profit, from thin through moderate and fat to monopoly-like</Key>
      </>}
      foot={<>
        <p>A <em>rent</em> is profit beyond what it takes to keep a business going, earned because something holds rivals off. The steps follow David Teece, an economist who studied why the firm that invents something often fails to keep the returns. The size follows the kind of rent and how long it is judged to last. The drawing shows the rule, which has no numbers of its own.</p>
        <p>Where a company lands is this site&apos;s judgement: a model drafted the answers about each from its filings, each profile says who reviewed it, and the rule then decides. A company placed with &ldquo;the owner of the scarce thing&rdquo; may itself be one of those owners; the rule files it there because others like it hold the same thing. The profiles are on each layer&apos;s page. None of this ranks a company or forecasts its price.</p>
      </>}
      tableLabel="Each profiled company and how the rule reads it"
      table={
        <table className="data">
          <thead><tr><th scope="col">Company</th><th scope="col">The step that settles it</th><th scope="col">How the rule reads it</th></tr></thead>
          <tbody>{f.steps.flatMap((s) => s.companies.map((c) => <tr key={c.entity}><th scope="row">{c.name}</th><td>{s.question}</td><td>{c.reads}</td></tr>))}</tbody>
        </table>
      }
    >
      <ol className="flex flex-col">
        {f.steps.map((s, i) => {
          const last = i === f.steps.length - 1;
          const owners = [...new Set(s.companies.map((c) => c.kept_by))];
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
                    {o ? <span className="w-full font-mono text-[10.5px] uppercase tracking-wider text-muted">Judged kept by {o}</span> : null}
                    {s.companies.filter((c) => c.kept_by === o).map((c) => <JudgedChip key={c.entity} name={c.name} word={last ? null : c.tier} tip={`${c.name}: ${c.reads} (this site's judgement)`} />)}
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

// Company counts by category on one scale, split by ownership state.
export function CategoryBars({ m }: { m: MarketMapDoc }) {
  const f = m.figures.categories;
  return (
    <Figure
      id="fig-categories"
      title="How many companies the map holds in each category, and how many of them have been bought or have closed"
      note={KIND_LABEL.chart}
      keys={<>{OWN.map((s) => <Key key={s} swatch={<OwnSwatch s={s} />}>{OWN_WORD[s]} (counted {n(f.totals[s])} times across the categories)</Key>)}</>}
      foot={<p>Each bar counts the companies the map places in a category, on a shared scale: the longest bar is the fullest category. A long bar means the tracker follows many companies there; it does not measure the market&apos;s size, its sales or its importance. A company placed in more than one category is counted in each. Bought, being bought and closed are the states recorded on each company, with who and when in the card&apos;s list below; a company with no recorded state is drawn as independent, so a sale the tracker has not recorded shows as independent.</p>}
      tableLabel="The numbers: companies in each category by ownership state"
      table={
        <table className="data">
          <thead><tr><th scope="col">Category</th><th scope="col">Layer</th><th scope="col">Companies</th><th scope="col">Independent</th><th scope="col">Bought, or being bought</th><th scope="col">Closed</th></tr></thead>
          <tbody>{f.layers.flatMap((l) => l.rows.map((r) => (
            <tr key={r.id}><th scope="row">{r.number} {r.name}</th><td>{l.name}</td><td>{r.out_of_scope ? "out of scope for now" : n(r.n)}</td>{r.segs.map((s) => <td key={s.state}>{n(s.n)}</td>)}</tr>
          )))}</tbody>
        </table>
      }
    >
      <div className="grid gap-x-8 gap-y-4 lg:grid-cols-2">
        {f.layers.map((l) => (
          <div key={l.id} role="group" aria-label={l.name} className="flex flex-col gap-1.5">
            <div className="border-b border-grid pb-0.5 text-[12.5px] font-semibold leading-tight text-ink"><span className="mr-2 font-mono text-[10.5px] font-normal text-muted">Layer {l.number}</span>{l.name}</div>
            {l.rows.map((r) => (
              <a key={r.id} href={`#mm-${r.id}`} className="grid grid-cols-[8.5rem_minmax(0,1fr)] items-center gap-x-2 sm:grid-cols-[13rem_minmax(0,1fr)]">
                <span className="text-[12px] leading-tight text-ink-2">{r.name}</span>
                {r.out_of_scope ? <span className="font-mono text-[11px] text-muted">out of scope for now</span> : (
                  <CountBar end={r.w} count={n(r.n)} segs={r.segs.map((s) => ({ key: s.state, x: s.x, w: s.w, fill: OWN_FILL[s.state], outline: s.state === "closed", tip: `${r.name}: ${n(s.n)} ${OWN_WORD[s.state]}` }))} />
                )}
              </a>
            ))}
          </div>
        ))}
      </div>
    </Figure>
  );
}

// Where the map is thin: every part of every layer, filled when a company sits there.
export function CoverageDots({ m }: { m: MarketMapDoc }) {
  const f = m.figures.coverage;
  const layers = m.layers.filter((l) => !l.indicator_only);
  const empty = (id: string) => layers.find((l) => l.id === id)!.categories.filter((c) => !c.out_of_scope).flatMap((c) => c.leaves.filter((p) => !p.n).map((p) => `${p.name} (${c.name})`));
  return (
    <Figure
      id="fig-coverage"
      title="Where the map is thin: the parts of each layer in which the tracker has placed no company yet"
      note={KIND_LABEL.chart}
      keys={<>
        <Key swatch={<PartDot filled tip="a part with a company" />}>a part of a category with a company placed in it</Key>
        <Key swatch={<PartDot filled={false} tip="a part with no company" />}>a part with none yet</Key>
        <Key swatch={<span className="inline-block h-2.5 w-px bg-axis" />}>a gap separates the categories of a layer</Key>
      </>}
      foot={<>
        <p>A category is split into parts, the finest grain of the map. An empty ring says where the tracker&apos;s coverage stops, not that nobody sells there: {n(f.n_empty)} of the {n(f.n_parts)} parts in scope hold no company yet. The category set aside as out of scope is left out.</p>
        <p>Categories holding few companies ({n(f.thin_at)} or fewer): {f.thin.map((t, i) => <span key={t.id}>{i ? ", " : ""}<a href={`#mm-${t.id}`} className={link}>{t.name}</a> ({n(t.n)})</span>)}. Thin here is a property of the tracker, too.</p>
      </>}
      tableLabel="The numbers, with the name of every part that holds no company"
      table={
        <table className="data">
          <thead><tr><th scope="col">Layer</th><th scope="col">Parts</th><th scope="col">With a company</th><th scope="col">With none</th><th scope="col">Companies placed in a category but in no part</th><th scope="col">The parts with none</th></tr></thead>
          <tbody>{f.rows.map((r) => (
            <tr key={r.id}><th scope="row">{r.name}</th><td>{n(r.n_parts)}</td><td>{n(r.n_covered)}</td><td>{n(r.n_empty)}</td><td>{n(r.n_unassigned)}</td><td className="text-muted">{empty(r.id).join("; ") || "none"}</td></tr>
          ))}</tbody>
        </table>
      }
    >
      <div className="flex flex-col gap-3">
        {f.rows.map((r) => (
          <div key={r.id} className="grid grid-cols-1 gap-1 sm:grid-cols-[15rem_minmax(0,1fr)_7.5rem] sm:items-center sm:gap-3">
            <span className="text-[13px] leading-tight text-ink">{r.name}</span>
            <span role="img" aria-label={`${r.name}: ${n(r.n_empty)} of ${n(r.n_parts)} parts hold no company`} className="flex flex-wrap gap-x-2.5 gap-y-1.5">
              {layers.find((l) => l.id === r.id)!.categories.filter((c) => !c.out_of_scope).map((c) => (
                <span key={c.id} className="flex gap-[3px]">{c.leaves.map((p) => <PartDot key={p.name} filled={p.n > 0} tip={`${c.name}: ${p.name}, ${p.n ? `${n(p.n)} placed` : "no company yet"}`} />)}</span>
              ))}
            </span>
            <span className="font-mono text-[11px] text-ink-2">{n(r.n_empty)} empty of {n(r.n_parts)}</span>
          </div>
        ))}
      </div>
    </Figure>
  );
}

// How firm the map is: the share of each layer's companies the tracker has verified.
export function VerifiedBars({ m }: { m: MarketMapDoc }) {
  const f = m.figures.verified;
  return (
    <Figure
      id="fig-verified"
      title="How much of the map has been checked: the share of each layer's companies the tracker has verified"
      note={KIND_LABEL.chart}
      keys={<>
        <Key swatch={<Swatch fill="var(--s1)" />}>verified: the tracker has tied the company to a filing or to a row in a dataset (bold on the map)</Key>
        <Key swatch={<Swatch fill="var(--s3)" />}>not yet verified: no such check has been made yet</Key>
      </>}
      foot={<p>Each bar is all the companies the map places in a layer, counted once. Verified says the company itself was checked against a record; it does not say a person reviewed where the company sits on the map, and it says nothing about how good the company is. The last bar is the whole map.</p>}
      table={
        <table className="data">
          <thead><tr><th scope="col">Layer</th><th scope="col">Companies</th><th scope="col">Verified</th><th scope="col">Not yet verified</th><th scope="col">Share verified</th></tr></thead>
          <tbody>{f.rows.map((r) => <tr key={r.id}><th scope="row">{r.name}</th><td>{n(r.n)}</td><td>{n(r.n_verified)}</td><td>{n(r.n_unverified)}</td><td>{fmt(r.share_verified, "share")}</td></tr>)}</tbody>
        </table>
      }
    >
      <ShareBars
        label="The share of each layer's companies the tracker has verified"
        rows={f.rows.map((r) => ({
          name: r.name,
          note: `${fmt(r.share_verified, "share")} · ${n(r.n_verified)} of ${n(r.n)}`,
          segs: r.segs.map((s) => ({ key: s.state, x: s.x, w: s.w, fill: s.state === "verified" ? "var(--s1)" : "var(--s3)", tip: `${r.name}: ${n(s.state === "verified" ? r.n_verified : r.n_unverified)} ${s.state === "verified" ? "verified" : "not yet verified"}` })),
        }))}
      />
    </Figure>
  );
}
