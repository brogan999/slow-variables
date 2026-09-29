import Link from "next/link";
import type { OpportunitiesDoc, Opportunity } from "@/lib/data";

const link = "underline decoration-grid underline-offset-2 hover:decoration-ink";
const STAGE: Record<string, string> = { now: "Now", next: "Next", later: "Later", endgame: "Endgame" };

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-0.5 sm:grid-cols-[12rem_1fr] sm:gap-4">
      <dt className="text-muted">{label}</dt>
      <dd className="text-ink-2">{children}</dd>
    </div>
  );
}

const orBlank = (s: string) => (s ? s : <span className="italic text-muted">not yet written</span>);

function Card({ o }: { o: Opportunity }) {
  return (
    <li id={`op-${o.id}`} className="fig p-4 md:p-5 flex flex-col gap-3 scroll-mt-24">
      <header className="flex flex-col gap-1 md:flex-row md:items-baseline md:gap-4">
        <h3 className="text-[1.05rem] font-semibold leading-snug text-ink">{o.name}</h3>
        <span className="md:ml-auto text-sm font-semibold text-ink md:text-right">{o.rent.verdict}</span>
      </header>
      <p className="text-sm text-ink-2">
        Sits in <Link href={`/value-chain#mm-${o.primary.id}`} className={link}>{o.primary.number} {o.primary.name}</Link>
        {o.adjacent.length ? <>; touches {o.adjacent.map((a, i) => <span key={a.id}>{i ? ", " : ""}<Link href={`/value-chain#mm-${a.id}`} className={link}>{a.name}</Link></span>)}</> : null}
      </p>
      <dl className="grid gap-2 text-sm">
        <Field label="The problem">{o.bottleneck}</Field>
        <Field label="Sold to">{orBlank(o.customer)}</Field>
        <Field label="First step">{o.wedge}</Field>
        <Field label="Charges for">{orBlank(o.unit_sold)}</Field>
        <Field label="Why a lab would not just bundle it">{orBlank(o.why_not_bundled)}</Field>
        <Field label="What it builds up">{o.durable_asset}{o.powers.length ? <span className="text-muted"> ({o.powers.join(", ")})</span> : null}</Field>
        <Field label="Why that profit">{o.rent_reason}</Field>
        <Field label="Wrong if">{o.falsifier}</Field>
        <Field label="Already on the map">
          {o.unmapped ? <span className="italic">No companies yet: the tracker has not mapped this category, which says where its coverage stops, not that the market is empty</span>
            : o.none_independent ? <span className="italic">Only companies that have been acquired or have closed</span>
            : <>{o.examples.join(", ")}{o.n_more_examples ? ` and ${o.n_more_examples} more` : ""}</>}
        </Field>
        <Field label="Builds on the site's reading">
          <ul className="flex flex-col gap-1">{o.builds_on.map((b) => <li key={b.ref}><Link href={b.href} className={link}>{b.title}</Link></li>)}</ul>
        </Field>
        {o.prerequisites ? <Field label="Needs first">{o.prerequisites}</Field> : null}
        {o.see_also ? <Field label="The version that could hold">See <a href={`#op-${o.see_also.id}`} className={link}>{o.see_also.name}</a></Field> : null}
      </dl>
      {o.blank.length ? <p className="text-xs text-muted">Not yet written: {o.blank.join(", ")}.</p> : null}
    </li>
  );
}

export function Opportunities({ d }: { d: OpportunitiesDoc }) {
  const tiers = d.counts.by_tier.map((x) => `${x.n} ${x.tier}`).join(" · ");
  return (
    <div className="flex flex-col gap-8">
      <p className="font-mono text-[12px] text-muted">
        {d.counts.records} businesses · {d.counts.unmapped} in categories the tracker has not mapped yet · profit by the rent rule: {tiers} · {d.counts.kept_by_incumbents} kept by incumbent firms
      </p>
      <figure className="fig" style={{ margin: 0 }}>
        <div className="fig-head"><span className="fig-n" /><h2 className="fig-title">A sequence of bets</h2><span className="fig-note">each stage opens only once its gate is passed</span></div>
        <ol className="grid md:grid-cols-4">
          {d.sequence.map((s, i) => (
            <li key={s.stage} className={`p-4 flex flex-col gap-2 text-sm ${i ? "border-t md:border-t-0 md:border-l border-grid" : ""}`}>
              <span className="eyebrow">{STAGE[s.stage] ?? s.stage}</span>
              <a href={`#op-${s.opportunity}`} className={`text-ink font-semibold leading-snug ${link}`}>{s.name}</a>
              <span className="text-ink-2"><span className="text-muted">{s.label}: </span>{s.gate}</span>
            </li>
          ))}
        </ol>
      </figure>
      <section className="flex flex-col gap-4" aria-labelledby="op-list">
        <h2 id="op-list" className="display text-[1.6rem]">The businesses</h2>
        <ol className="flex flex-col gap-4">{d.opportunities.map((o) => <Card key={o.id} o={o} />)}</ol>
      </section>
    </div>
  );
}
