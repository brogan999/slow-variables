import Link from "next/link";
import type { EconomicsUnit, Profile } from "@/lib/data";
import { judgements } from "@/lib/data";
import { PhoneCollapse } from "@/components/PhoneCollapse";

export const DIRECTION: Record<EconomicsUnit["direction"], string> = {
  commoditising: "Commoditising",
  holding: "Holding",
  tightening: "Tightening",
};
const link = "underline decoration-grid underline-offset-4 hover:text-ink";

// Each input with its tightness word from the bottleneck scorecard.
export function Binding({ b }: { b: EconomicsUnit["binding"] }) {
  if (!b.length) return null;
  const judged = judgements().surfaces.tightness ?? {};
  return (
    <span>
      {b.map((x, i) => (
        <span key={x.id}>{i ? ", " : ""}{x.name} <span className="text-muted">({x.word ?? (judged[x.id] ? `no reading; a model judges it ${judged[x.id].label}` : "no reading")})</span></span>
      ))}
    </span>
  );
}

// One layer unit: the site's judgement of how its economics move, with the rival view beside it.
export function EconomicsUnitView({ u }: { u: EconomicsUnit }) {
  return (
    <article id={`assessment-${u.id}`} className="panel p-5 flex flex-col gap-3 scroll-mt-24">
      <div className="flex flex-col gap-1.5">
        <span className="eyebrow">{DIRECTION[u.direction]}</span>
        <h3 className="display text-xl leading-snug max-w-[60ch]">{u.title}</h3>
      </div>
      <p className="text-ink-2 leading-relaxed max-w-[68ch]">{u.mechanism}</p>
      <dl className="grid gap-3 md:grid-cols-2 text-sm leading-relaxed">
        <div><dt className="eyebrow mb-1">Getting cheap and interchangeable</dt><dd className="text-ink-2">{u.commoditising}</dd></div>
        <div><dt className="eyebrow mb-1">Staying scarce</dt><dd className="text-ink-2">{u.stays_scarce}</dd></div>
        <div><dt className="eyebrow mb-1">What would make it last</dt><dd className="text-ink-2">{u.converts_if}</dd></div>
        <div><dt className="eyebrow mb-1">What would prove this wrong</dt><dd className="text-ink-2">{u.kill_shot}</dd></div>
        {u.powers.length ? <div><dt className="eyebrow mb-1">Powers here today</dt><dd className="text-ink-2">{u.powers.join(", ")}</dd></div> : null}
        {u.binding.length ? <div><dt className="eyebrow mb-1">Binds on (<Link href="/bottlenecks" className={link}>how tight</Link>)</dt><dd className="text-ink-2"><Binding b={u.binding} /></dd></div> : null}
        {u.rival ? <div><dt className="eyebrow mb-1">The rival view</dt><dd className="text-ink-2"><Link href={`/outlook#position-${u.rival.id}`} className={link}>{u.rival.title}</Link></dd></div> : null}
      </dl>
    </article>
  );
}

// One company: what it sells, to whom, what protects it, and what would have to hold by 2035.
export function ProfileCard({ c }: { c: Profile }) {
  return (
    <article id={`profile-${c.entity}`} className="panel p-5 flex flex-col gap-3 scroll-mt-24">
      <PhoneCollapse summary={
        <div className="flex flex-col gap-1.5">
          <span className="eyebrow">{c.role === "club" ? "Already worth over a trillion dollars" : "Candidate to be worth a trillion dollars"}</span>
          <h4 className="display text-xl">{c.name}</h4>
        </div>
      }>
      <div className="flex flex-col gap-3 mt-3">
      <dl className="flex flex-col gap-3 text-sm leading-relaxed">
        <div><dt className="eyebrow mb-1">Market</dt><dd className="text-ink-2">{c.market}</dd></div>
        <div><dt className="eyebrow mb-1">Customers ({c.concentration})</dt><dd className="text-ink-2">{c.customers}</dd></div>
        {c.powers.length ? (
          <div>
            <dt className="eyebrow mb-1">Powers</dt>
            <dd><ul className="text-ink-2 list-disc pl-5 marker:text-muted flex flex-col gap-1">{c.powers.map((p) => <li key={p.power}><span className="text-ink">{p.power}</span>: {p.why}</li>)}</ul></dd>
          </div>
        ) : <div><dt className="eyebrow mb-1">Powers</dt><dd className="text-ink-2">None that passes the test of a benefit behind a barrier today.</dd></div>}
        <div><dt className="eyebrow mb-1">Under the site&apos;s rent rule</dt><dd className="text-ink-2">{c.rent.reads}.{c.depends_on.length ? <> Depends on: <Binding b={c.depends_on} />.</> : null}</dd></div>
      </dl>
      <div className="grid gap-3 md:grid-cols-2 text-sm leading-relaxed">
        <div>
          <p className="eyebrow mb-1">What would have to hold by 2035</p>
          <ul className="list-disc pl-5 text-ink-2 marker:text-muted flex flex-col gap-1">{c.must_be_true.map((x) => <li key={x}>{x}</li>)}</ul>
        </div>
        <div>
          <p className="eyebrow mb-1">What would show it failing</p>
          <ul className="list-disc pl-5 text-ink-2 marker:text-muted flex flex-col gap-1">{c.would_disprove.map((x) => <li key={x}>{x}</li>)}</ul>
        </div>
      </div>
      <p className="text-xs text-muted">
        Drafted by {c.judged_by} from{" "}
        {c.source_links.map((s, i) => (
          <span key={s.id}>{i ? ", " : ""}<a href={s.url} className={link} target="_blank" rel="noreferrer">{s.label}<span className="sr-only"> (opens in a new tab)</span></a></span>
        ))}
        ; {c.reviewed_by ? `reviewed by ${c.reviewed_by} on ${c.reviewed}` : "not yet reviewed by a person"}.{c.disclosure ? ` ${c.disclosure}` : ""}
      </p>
      </div>
      </PhoneCollapse>
    </article>
  );
}

export function PowersGlossary({ powers }: { powers: Record<string, string> }) {
  return (
    <details className="text-sm text-ink-2">
      <summary className="cursor-pointer text-muted hover:text-ink w-fit">What the powers mean</summary>
      <p className="mt-2 max-w-[70ch]">Hamilton Helmer, a strategy consultant and investor who studied why some firms keep earning more than their investors could get elsewhere, found that an advantage lasts only when a benefit sits behind a barrier that stops rivals copying it, and named the kinds that recur:</p>
      <dl className="mt-2 grid gap-1.5">{Object.entries(powers).map(([k, v]) => <div key={k}><dt className="inline text-ink">{k}</dt>: <dd className="inline">{v}</dd></div>)}</dl>
    </details>
  );
}
