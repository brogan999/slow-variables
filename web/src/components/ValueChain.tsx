import Link from "next/link";
import type { EconomicsUnit, Profile } from "@/lib/data";

const DIRECTION: Record<EconomicsUnit["direction"], string> = {
  commoditising: "Commoditising",
  holding: "Holding",
  tightening: "Tightening",
};
const link = "underline decoration-grid underline-offset-4 hover:text-ink";

function Binding({ b }: { b: EconomicsUnit["binding"] }) {
  if (!b.length) return null;
  return (
    <span>
      {b.map((x, i) => (
        <span key={x.id}>{i ? ", " : ""}{x.name} <span className="text-muted">({x.word ?? "no reading"})</span></span>
      ))}
    </span>
  );
}

// One layer unit: the site's judgement of how its economics move, with the rival view beside it.
export function EconomicsUnitView({ u }: { u: EconomicsUnit }) {
  return (
    <article id={`assessment-${u.id}`} className="panel p-5 flex flex-col gap-3 scroll-mt-8">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="display text-xl leading-snug max-w-[40ch]">{u.title}</h3>
        <span className="eyebrow">{DIRECTION[u.direction]}</span>
      </div>
      <p className="text-ink-2 leading-relaxed">{u.mechanism}</p>
      <dl className="grid gap-3 md:grid-cols-2 text-sm leading-relaxed">
        <div><dt className="eyebrow mb-1">Getting cheap and interchangeable</dt><dd className="text-ink-2">{u.commoditising}</dd></div>
        <div><dt className="eyebrow mb-1">Staying scarce</dt><dd className="text-ink-2">{u.stays_scarce}</dd></div>
        <div><dt className="eyebrow mb-1">What would make it last</dt><dd className="text-ink-2">{u.converts_if}</dd></div>
        <div><dt className="eyebrow mb-1">What would prove this wrong</dt><dd className="text-ink-2">{u.kill_shot}</dd></div>
      </dl>
      <p className="text-sm text-ink-2">
        {u.powers.length ? <>Powers here today: {u.powers.join(", ")}. </> : null}
        {u.binding.length ? <>Binds on: <Binding b={u.binding} />. </> : null}
        {u.rival ? <>The rival view: <Link href={`/outlook#position-${u.rival.id}`} className={link}>{u.rival.title}</Link>.</> : null}
      </p>
    </article>
  );
}

// One company: what it sells, to whom, what protects it, and what would have to hold by 2035.
export function ProfileCard({ c }: { c: Profile }) {
  return (
    <article id={`profile-${c.entity}`} className="panel p-5 flex flex-col gap-3 scroll-mt-8">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="display text-xl">{c.name}</h3>
        <span className="eyebrow">{c.role === "club" ? "Already worth over a trillion dollars" : "Candidate"}</span>
      </div>
      <p className="text-sm text-ink-2 leading-relaxed"><span className="text-ink">Market.</span> {c.market}</p>
      <p className="text-sm text-ink-2 leading-relaxed"><span className="text-ink">Customers ({c.concentration}).</span> {c.customers}</p>
      {c.powers.length ? (
        <ul className="text-sm text-ink-2 leading-relaxed list-disc pl-5 marker:text-muted">
          {c.powers.map((p) => <li key={p.power}><span className="text-ink">{p.power}</span>: {p.why}</li>)}
        </ul>
      ) : null}
      <p className="text-sm text-ink-2">Under the site&apos;s rent rule: {c.rent.reads}.{c.depends_on.length ? <> Depends on: <Binding b={c.depends_on} />.</> : null}</p>
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
        {c.source_links.map((s, i) => <span key={s.id}>{i ? ", " : ""}<a href={s.url} className={link} target="_blank" rel="noreferrer">{s.label}</a></span>)}
        ; {c.reviewed_by ? `reviewed by ${c.reviewed_by} on ${c.reviewed}` : "not yet reviewed by a person"}.{c.disclosure ? ` ${c.disclosure}` : ""}
      </p>
    </article>
  );
}

export function PowersGlossary({ powers }: { powers: Record<string, string> }) {
  return (
    <details className="text-sm text-ink-2">
      <summary className="cursor-pointer text-muted hover:text-ink w-fit">What the powers mean</summary>
      <p className="mt-2 max-w-[70ch]">Hamilton Helmer, a strategy consultant and investor who studied why some firms keep earning more than their investors could get elsewhere, found seven ways an advantage lasts: each needs a benefit and a barrier that stops rivals copying it.</p>
      <dl className="mt-2 grid gap-1.5">{Object.entries(powers).map(([k, v]) => <div key={k}><dt className="inline text-ink">{k}</dt>: <dd className="inline">{v}</dd></div>)}</dl>
    </details>
  );
}
