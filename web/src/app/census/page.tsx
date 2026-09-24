import Link from "next/link";
import { ArticleLayout, MarginPanel } from "@/components/ArticleLayout";
import { PageHeader } from "@/components/PageHeader";
import { census, type CensusIndex } from "@/lib/data";
import { fmt } from "@/lib/format";

export const metadata = { title: "The automatability census", description: "Which knowledge work AI can take on today, task by task, role by role and industry by industry, with the part all three scoring models agree on beside every total." };

const usd = (v: number | null | undefined) => (v === 0 ? "$0" : fmt(v, "USD"));
const band = (lo: number, hi: number) => `${fmt(lo, "share")} to ${fmt(hi, "share")}`;
// agreed3 is null only where none of the payroll was scored by all three models; zero is a real zero
const A3 = ({ v }: { v: number | null }) => (v === null ? <span className="text-muted">not scored by all three</span> : <>{usd(v)}</>);
const link = "underline decoration-grid underline-offset-4 hover:decoration-ink";

function Section({ id, n, title, lede, children }: { id: string; n: string; title: string; lede: string; children: React.ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className="flex flex-col gap-4 scroll-mt-8">
      <div className="eyebrow">{n}</div>
      <h2 id={`${id}-h`} className="display text-[1.9rem] leading-tight">{title}</h2>
      <p className="font-serif text-[17px] leading-relaxed text-ink-2 max-w-[66ch]">{lede}</p>
      {children}
    </section>
  );
}

// A table that may scroll sideways on a phone is a labelled region keyboard users can focus and scroll.
function Rows<T>({ head, rows, row }: { head: string[]; rows: T[]; row: (r: T) => React.ReactNode }) {
  return (
    <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={`Table: ${head.join(", ")}`}>
      <table className="data w-full text-sm">
        <thead><tr>{head.map((h) => <th key={h} scope="col">{h}</th>)}</tr></thead>
        <tbody>{rows.map(row)}</tbody>
      </table>
    </div>
  );
}

const industryHead = ["Industry", "Payroll", "Can go", "All three agree", "Share of payroll", "Verifier queue"];
const industryRow = (i: CensusIndex["industries"][number]) => (
  <tr key={i.naics} id={`naics-${i.naics}`}><th scope="row">{i.title} <span className="text-muted font-mono text-[11px]">{i.naics}</span></th><td className="tabular-nums">{usd(i.payroll)}</td><td className="tabular-nums">{usd(i.freed)}</td><td className="tabular-nums">{usd(i.agreed3)}</td><td className="tabular-nums">{fmt(i.share_total, "share")}</td><td className="tabular-nums">{usd(i.verifier_queue)}</td></tr>
);

function Method({ c }: { c: CensusIndex }) {
  const m = c.method as {
    gates: { g: string; v: string; t: string; p: boolean | null; n: string }[];
    adjudication: { scorer: string; tasks: number; stakes_vs_workers: number; grader_vs_workers: number; alone_consumer: number; flags: number }[];
    placebo: { method: string; noise_median: number; trusted: boolean }[];
    stability: { start: number; industry: string; b: number; ci: number }[];
    channel: { runs: { period: string; scorer: string; n: number; coef: number; z: number }[] };
    physical_gate: { removed_usd: number; spotcheck: { sample: number; error_rate: number; ci90: number[]; headline_low_by_usd: number[] } };
    sigma: { sigma: number; before: number; after: number }[];
  };
  const names: Record<string, string> = { A: c.scorers[0], B: c.scorers[1], C: c.scorers[2] };
  const pg = m.physical_gate;
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h3 className="font-medium mb-2">Tests set in advance, reported either way</h3>
        <Rows head={["Test", "Result", "Needed", "Outcome", "Note"]} rows={m.gates} row={(g) => (
          <tr key={g.g}><th scope="row">{g.g}</th><td className="tabular-nums">{g.v}</td><td className="tabular-nums">{g.t}</td><td>{g.p === true ? "passed" : g.p === false ? "failed" : "open"}</td><td className="text-ink-2">{g.n}</td></tr>
        )} />
      </div>
      <div>
        <h3 className="font-medium mb-2">Which model to believe</h3>
        <p className="text-sm text-ink-2 mb-2 max-w-[66ch]">Each model was checked against evidence it never saw: what workers themselves report about the stakes of their tasks and whether anyone checks their work, and how much of observed AI use of a task is AI working alone.</p>
        <Rows head={["Model", "Tasks scored", "Stakes vs workers' reports", "Checking vs workers' reports", "AI alone where it says goes", "Flagged"]} rows={m.adjudication} row={(a) => (
          <tr key={a.scorer}><th scope="row">{names[a.scorer] ?? a.scorer}</th><td className="tabular-nums">{fmt(a.tasks, "count")}</td><td className="tabular-nums">{fmt(a.stakes_vs_workers)}</td><td className="tabular-nums">{fmt(a.grader_vs_workers)}</td><td className="tabular-nums">{fmt(a.alone_consumer, "share")}</td><td className="tabular-nums">{fmt(a.flags, "share")}</td></tr>
        )} />
      </div>
      <div>
        <h3 className="font-medium mb-2">Why keeping the saving is reasoned, not measured</h3>
        <p className="text-sm text-ink-2 mb-2 max-w-[66ch]">A sound method should find nothing when fed random noise. Most of the methods tried found something anyway, and the one that passed flips sign for accountants when the start year moves.</p>
        <div className="grid gap-4 md:grid-cols-2">
          <Rows head={["Method", "Result on noise", "Trusted"]} rows={m.placebo} row={(p) => <tr key={p.method}><th scope="row">{p.method}</th><td className="tabular-nums">{fmt(p.noise_median)}</td><td>{p.trusted ? "yes" : "no"}</td></tr>} />
          <Rows head={["Start year", "Industry", "Estimate", "± interval"]} rows={m.stability} row={(s) => <tr key={`${s.start}${s.industry}`}><td className="tabular-nums">{s.start}</td><th scope="row">{s.industry}</th><td className="tabular-nums">{fmt(s.b)}</td><td className="tabular-nums">{fmt(s.ci)}</td></tr>} />
        </div>
      </div>
      <div>
        <h3 className="font-medium mb-2">How hard a task is to specify: exploratory</h3>
        <p className="text-sm text-ink-2 mb-2 max-w-[66ch]">Not part of the rule. The test was designed after seeing the data: harder-to-specify tasks see less of their AI use come through direct programmatic access rather than chat. It will be re-run once, unchanged, on the next Economic Index release.</p>
        <Rows head={["Period", "Model", "Tasks", "Coefficient", "z"]} rows={m.channel.runs} row={(r) => <tr key={`${r.period}${r.scorer}`}><td className="tabular-nums">{r.period}</td><th scope="row">{r.scorer === "vote" ? "the vote" : names[r.scorer] ?? r.scorer}</th><td className="tabular-nums">{fmt(r.n, "count")}</td><td className="tabular-nums">{fmt(r.coef)}</td><td className="tabular-nums">{fmt(r.z)}</td></tr>} />
      </div>
      <div>
        <h3 className="font-medium mb-2">The physical-work filter</h3>
        <p className="text-sm text-ink-2 max-w-[66ch]">Work that needs a body was removed before scoring: {usd(pg.removed_usd)} of payroll. A reproducible spot check of {fmt(pg.spotcheck.sample, "count")} removed tasks found {fmt(pg.spotcheck.error_rate, "share")} were really desk work (interval {band(pg.spotcheck.ci90[0], pg.spotcheck.ci90[1])}), so the total may be {usd(pg.spotcheck.headline_low_by_usd[0])} to {usd(pg.spotcheck.headline_low_by_usd[2])} too low.</p>
      </div>
      <div>
        <h3 className="font-medium mb-2">Modelled, not measured: what the remaining work costs</h3>
        <p className="text-sm text-ink-2 mb-2 max-w-[66ch]">If the work that stays is a complement to the work that goes, it becomes a larger share of what a job costs. How large depends on an elasticity whose published estimates fall on both sides of the line where the effect reverses, so these figures are conditional.</p>
        <Rows head={["Elasticity", "Share of cost that stays, before", "After"]} rows={m.sigma} row={(s) => <tr key={s.sigma}><td className="tabular-nums">{fmt(s.sigma)}</td><td className="tabular-nums">{fmt(s.before, "share")}</td><td className="tabular-nums">{fmt(s.after, "share")}</td></tr>} />
      </div>
    </div>
  );
}

export default function CensusPage() {
  const c = census();
  const s = c.prose.sections;
  const h = c.headline;
  const fns = c.functions.map((f) => f.function);
  return (
    <ArticleLayout
      head={<PageHeader eyebrow={`Census · version ${c.version}`} title={c.prose.title} lede={c.prose.lede} />}
      margin={
        <>
          <MarginPanel title={`Readings · version ${c.version}`} rows={[
            ["Knowledge payroll that can go", <Link key="h" href="#dial" className={link}>{usd(h.freed)}</Link>],
            ["Of which all three models agree", usd(h.agreed3)],
            ["Knowledge payroll scored", usd(h.payroll)],
            ["Held up only because nothing can check it", usd(h.verifier_queue)],
            ["Decided without the third model", usd(h.without_gemini)],
          ]} />
          <MarginPanel title="Instrument">
            <p>Judged by {c.scorers.join(", ")}; the verdict on each task is their vote. Imported as published from the census&apos;s own files and checked against their fingerprints.</p>
            <p>Download: {Object.entries(c.csv).map(([f, href], i) => <span key={f}>{i ? ", " : ""}<a href={href} className={link}>{f}</a></span>)}.</p>
            <p>Query every table in the <Link href="/query" className={link}>SQL console</Link>, e.g. <code className="text-[12px]">SELECT title, freed, freed_agreed3 FROM census_roles ORDER BY freed_agreed3 DESC</code>.</p>
            <p><Link href="/methodology#census" className={link}>How the census is imported</Link></p>
          </MarginPanel>
        </>
      }
    >
      <div className="flex flex-col gap-16">
        <div className="prose-folio">
          <p>{c.prose.rule}</p>
          <p>{c.prose.agreed}</p>
        </div>

        <Section id="dial" n="The rule" title={s.dial.title} lede={s.dial.lede}>
          <Rows head={["Step", "Rule", "Can go", "All three agree"]} rows={c.dial} row={(d) => (
            <tr key={d.rule} className={d.headline ? "bg-surface-2" : undefined}><td>{d.headline ? "used" : ""}</td><th scope="row">{d.rule}</th><td className="tabular-nums">{usd(d.freed)}</td><td className="tabular-nums">{usd(d.agreed3)}</td></tr>
          )} />
        </Section>

        <Section id="roles" n="Part I · roles" title={s.roles.title} lede={s.roles.lede}>
          <div className="flex flex-col gap-2">
            {fns.map((fn) => (
              <details key={fn} className="panel px-4 py-3">
                <summary className="cursor-pointer font-medium">{fn}</summary>
                <Rows head={["Role", "Share that can go", "Can go", "All three agree"]} rows={c.roles.filter((r) => r.function === fn)} row={(r) => (
                  <tr key={r.occ}><th scope="row"><Link href={r.href} className={link}>{r.title}</Link></th><td className="tabular-nums">{fmt(r.share_goes, "share")} <span className="text-muted">({band(r.band_lo, r.band_hi)})</span></td><td className="tabular-nums">{usd(r.freed)}</td><td className="tabular-nums"><A3 v={r.agreed3} /></td></tr>
                )} />
              </details>
            ))}
          </div>
        </Section>

        <Section id="functions" n="Part II · functions" title={s.functions.title} lede={s.functions.lede}>
          <Rows head={["Function", "Payroll", "Can go", "All three agree", "Share that can go", "Verifier queue"]} rows={c.functions} row={(f) => (
            <tr key={f.function}><th scope="row">{f.function}</th><td className="tabular-nums">{usd(f.payroll)}</td><td className="tabular-nums">{usd(f.freed)}</td><td className="tabular-nums"><A3 v={f.agreed3} /></td><td className="tabular-nums">{fmt(f.share_goes, "share")} <span className="text-muted">({band(f.band_lo, f.band_hi)})</span></td><td className="tabular-nums">{usd(f.verifier_queue)}</td></tr>
          )} />
        </Section>

        <Section id="industries" n="Part III · industries" title={s.industries.title} lede={s.industries.lede}>
          <Rows head={industryHead} rows={c.industries.slice(0, 15)} row={industryRow} />
          <details className="panel px-4 py-3">
            <summary className="cursor-pointer font-medium">Every other industry, by payroll that can go</summary>
            <Rows head={industryHead} rows={c.industries.slice(15)} row={industryRow} />
          </details>
        </Section>

        <Section id="deals" n="Part IV · businesses" title={s.deals.title} lede={s.deals.lede}>
          <div className="grid gap-4 md:grid-cols-2">
            {c.deals.cards.map((d) => (
              <article key={d.key} id={`deal-${d.key}`} className="panel px-4 py-4 flex flex-col gap-2 text-sm">
                <div className="flex flex-wrap gap-2 items-baseline">
                  <span className="eyebrow">{d.stance === "keeps" ? "the owner likely keeps it" : d.stance === "passes" ? "the saving likely passes to clients" : "check before buying"}</span>
                  {d.anchored ? <span className="eyebrow text-muted">sized by one occupation</span> : null}
                </div>
                <h3 className="font-medium text-base">{d.name}</h3>
                <p className="text-ink-2"><strong className="font-medium text-ink">Priced as</strong> {d.invoice}.</p>
                <p className="tabular-nums">Payroll {usd(d.payroll)} · can go {usd(d.freed)} <span className="text-muted">({usd(d.freed_lo)} to {usd(d.freed_hi)})</span> · all three agree {usd(d.agreed3)}</p>
                <p className="text-ink-2">{d.stance_why} <span className="text-muted">Reasoned from how the business prices its work, not measured.</span></p>
                <details><summary className="cursor-pointer">Why, the questions that kill it, comparables and sources</summary>
                  <div className="flex flex-col gap-2 mt-2 text-ink-2">
                    <p>{d.why}</p>
                    {d.excl ? <p>{d.excl}</p> : null}
                    <ul className="list-disc pl-5">{d.kill.map((k) => <li key={k}>{k}</li>)}</ul>
                    <p>Comparables, illustrating the pricing model, not researched targets: {d.comps.join("; ")}.</p>
                    <p>Sources: {d.sources.map((x, i) => <span key={x.cited_as}>{i ? ", " : ""}<a href={x.href} className={link}>{new URL(x.cited_as).hostname}</a></span>)}</p>
                  </div>
                </details>
              </article>
            ))}
          </div>
          <details className="panel px-4 py-3">
            <summary className="cursor-pointer font-medium">Businesses with no card, and why</summary>
            <ul className="list-disc pl-5 mt-2 text-sm text-ink-2 flex flex-col gap-1">{c.deals.not_carded.map((n) => <li key={n.name}><strong className="font-medium text-ink">{n.name}.</strong> {n.why}</li>)}</ul>
          </details>
        </Section>

        <Section id="method" n="Method" title={s.method.title} lede={s.method.lede}>
          <Method c={c} />
        </Section>

        <section aria-labelledby="caveats-h" className="flex flex-col gap-3">
          <h2 id="caveats-h" className="display text-[1.6rem] leading-tight">What every figure here carries with it</h2>
          <ul className="list-disc pl-5 font-serif text-[16px] leading-relaxed text-ink-2 flex flex-col gap-2 max-w-[66ch]">{c.prose.caveats.map((x) => <li key={x}>{x}</li>)}</ul>
        </section>
      </div>
    </ArticleLayout>
  );
}
