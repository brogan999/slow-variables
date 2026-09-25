import Link from "next/link";
import { ArticleLayout, MarginPanel } from "@/components/ArticleLayout";
import { PageHeader } from "@/components/PageHeader";
import { census, type CensusIndex } from "@/lib/data";
import { fmt } from "@/lib/format";

export const metadata = { title: "The automatability census", description: "Which knowledge work passes a structural hand-over screen, task by task, role by role and industry by industry, with the part all three scoring models pass beside every total." };

const usd = (v: number | null | undefined) => (v === 0 ? "$0" : fmt(v, "USD"));
const rules = (strict: number, loose: number) => `${fmt(strict, "share")} strict, ${fmt(loose, "share")} loose`;
const interval = (ci: number[]) => `${fmt(ci[0], "share")} to ${fmt(ci[1], "share")}`;
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
function Rows<T>({ head, rows, row, label }: { head: string[]; rows: T[]; row: (r: T) => React.ReactNode; label?: string }) {
  return (
    <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={label ?? `Table: ${head.join(", ")}`}>
      <table className="data w-full text-sm">
        <thead><tr>{head.map((h) => <th key={h} scope="col">{h}</th>)}</tr></thead>
        <tbody>{rows.map(row)}</tbody>
      </table>
    </div>
  );
}

const industryHead = ["Industry (code)", "Payroll, all workers", "Passes the screen", "All three pass", "Share of payroll", "Waiting on a check"];
const industryRow = (i: CensusIndex["industries"][number]) => (
  <tr key={i.naics} id={`naics-${i.naics}`}><th scope="row">{i.title} <span className="text-muted font-mono text-[11px]">{i.naics}</span></th><td className="tabular-nums">{usd(i.payroll)}</td><td className="tabular-nums">{usd(i.passes)}</td><td className="tabular-nums"><A3 v={i.agreed3} /></td><td className="tabular-nums">{fmt(i.share_total, "share")}</td><td className="tabular-nums">{usd(i.blocked_by_missing_check)}</td></tr>
);

const OUTCOME = (p: boolean | null) => (p === true ? "passed" : p === false ? "failed" : "—"); // null: pending or descriptive; its result says which
const WHEN = { pre17: "Set before the first scores (17 September)", pre24: "Set before this version's scores (24 September)", post: "Found after seeing the data" } as const;

function Method({ c }: { c: CensusIndex }) {
  const m = c.method;
  const n = c.prose.method_notes;
  const who = (k: string) => c.scorer_names[k] ?? k;
  const sc = m.physical_gate.spotcheck;
  const v = m.validation;
  const note = "text-sm text-ink-2 mb-2 max-w-[66ch]";
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h3 className="font-medium mb-2">Tests the census set itself, reported either way</h3>
        <p className={note}>{n.gates}</p>
        {(["pre17", "pre24", "post"] as const).map((k) => (
          <div key={k} className="mb-4">
            <h4 className="eyebrow mb-1">{WHEN[k]}</h4>
            <Rows label={`Tests: ${WHEN[k]}`} head={["Test", "Result", "Needed", "Outcome", "Note"]} rows={m.gates.filter((g) => g.k === k)} row={(g) => (
              <tr key={`${g.g}|${g.v}`}><th scope="row">{g.g}</th><td className="tabular-nums">{g.v}</td><td className="tabular-nums">{g.t}</td><td>{OUTCOME(g.p)}</td><td className="text-ink-2">{g.n}</td></tr>
            )} />
          </div>
        ))}
      </div>
      <div>
        <h3 className="font-medium mb-2">Do the models agree, and does the screen match observed use?</h3>
        <p className={note}>{n.validation}</p>
        <Rows head={["Check", "Tasks", "Where the task passes", "Where it fails", "Gap within the same job, in points", "Strength"]} rows={[["AI working alone, in chat", v.ai_alone], ["AI working alone, through programmatic access", v.ai_alone_api]] as const} row={([label, t]) => (
          <tr key={label}><th scope="row">{label}</th><td className="tabular-nums">{fmt(t.n, "count")}</td><td className="tabular-nums">{fmt(t.passes, "share")}</td><td className="tabular-nums">{fmt(t.fails, "share")}</td><td className="tabular-nums">{fmt(t.within_occ_pp)}</td><td className="tabular-nums">{fmt(t.within_occ_t)}</td></tr>
        )} />
        <p className="text-sm text-ink-2 mt-2">The census labels the chat test: {v.ai_alone.label}. Agreement across the three models (Fleiss κ): {fmt(v.agreement.fleiss_verdict)} over {fmt(v.agreement.n_called, "count")} tasks.</p>
      </div>
      <div>
        <h3 className="font-medium mb-2">Each model alone, and the same model twice</h3>
        <Rows head={["Model", "Payroll it alone would pass"]} rows={c.scorers} row={(k) => <tr key={k}><th scope="row">{who(k)}</th><td className="tabular-nums">{usd(m.by_scorer[k].passes_usd)}</td></tr>} />
        <p className="text-sm text-ink-2 mt-2 max-w-[66ch]">{n.rescore} {who(m.rescore_stability.scorer)} re-scored {fmt(m.rescore_stability.n_tasks, "count")} tasks and changed {fmt(m.rescore_stability.share_verdicts_changed, "share")} of its verdicts.</p>
      </div>
      <div>
        <h3 className="font-medium mb-2">Which model to believe</h3>
        <p className={note}>{n.adjudication}</p>
        <Rows head={["Model", "Tasks scored", "Matches workers on stakes", "Matches workers on checking", "AI alone where it passes the task"]} rows={m.adjudication} row={(a) => (
          <tr key={a.scorer}><th scope="row">{who(a.scorer)}</th><td className="tabular-nums">{fmt(a.tasks, "count")}</td><td className="tabular-nums">{fmt(a.stakes_vs_workers)}</td><td className="tabular-nums">{fmt(a.grader_vs_workers)}</td><td className="tabular-nums">{fmt(a.alone_consumer, "share")}</td></tr>
        )} />
      </div>
      <div>
        <h3 className="font-medium mb-2">Why keeping the saving is reasoned, not measured</h3>
        <p className={note}>{n.retention}</p>
        <details className="panel px-4 py-3"><summary className="cursor-pointer">The numbers</summary>
          <div className="grid gap-4 md:grid-cols-2 mt-2">
            <Rows head={["Method (the census's name)", "Result on random noise", "Trusted"]} rows={m.placebo} row={(p) => <tr key={p.method}><th scope="row">{p.method}</th><td className="tabular-nums">{fmt(p.noise_median)}</td><td>{p.trusted ? "yes" : "no"}</td></tr>} />
            <Rows head={["First year", "Industry", "How much of a labour-cost fall reached prices", "Give or take"]} rows={m.stability} row={(s) => <tr key={`${s.start}${s.industry}`}><td className="tabular-nums">{s.start}</td><th scope="row">{s.industry}</th><td className="tabular-nums">{fmt(s.b)}</td><td className="tabular-nums">{fmt(s.ci)}</td></tr>} />
          </div>
        </details>
      </div>
      <div>
        <h3 className="font-medium mb-2">How hard a task is to describe: found after seeing the data</h3>
        <p className={note}>{n.channel}</p>
        <details className="panel px-4 py-3"><summary className="cursor-pointer">The numbers ({m.channel.headline.label})</summary>
          <Rows head={["Month", "Tasks with any programmatic use", "Effect on any use", "Its strength", "Tasks with some", "Effect on how much", "Strength of that effect"]} rows={m.channel.runs} row={(r) => <tr key={r.period}><td className="tabular-nums">{r.period}</td><td className="tabular-nums">{fmt(r.n_a, "count")}</td><td className="tabular-nums">{fmt(r.a_coef)}</td><td className="tabular-nums">{fmt(r.a_z)}</td><td className="tabular-nums">{fmt(r.n_b, "count")}</td><td className="tabular-nums">{fmt(r.b_coef)}</td><td className="tabular-nums">{fmt(r.b_z)}</td></tr>} />
        </details>
      </div>
      <div>
        <h3 className="font-medium mb-2">The physical-work filter, checked both ways</h3>
        <p className="text-sm text-ink-2 max-w-[66ch]">Work that needs a body was removed before the vote: {usd(m.physical_gate.removed_usd)} of payroll. A spot check by {who("gemini")} of {fmt(sc.removed.draws, "count")} removed tasks found {fmt(sc.removed.error_rate, "share")} were really desk work (a ninety-five percent interval of {interval(sc.removed.ci95)}), so the payroll that passes may be {usd(sc.removed.effect_usd[0])} to {usd(sc.removed.effect_usd[2])} too low. The same check of {fmt(sc.kept.draws, "count")} kept tasks found {fmt(sc.kept.wrong, "count")} that were really physical (an interval of {interval(sc.kept.ci95)}), so the payroll that passes may also be up to {usd(sc.kept.effect_usd[2])} too high. The filter counts talking with people in person as desk work, which neither check can measure.</p>
      </div>
      <div>
        <h3 className="font-medium mb-2">Modelled, not measured: what the remaining work costs</h3>
        <p className={note}>{n.sigma}</p>
        <Rows head={["Elasticity", "Share of a job's cost in work that stays, before", "After"]} rows={m.sigma} row={(s) => <tr key={s.sigma}><td className="tabular-nums">{fmt(s.sigma)}</td><td className="tabular-nums">{fmt(s.before, "share")}</td><td className="tabular-nums">{fmt(s.after, "share")}</td></tr>} />
      </div>
    </div>
  );
}

const STANCE: Record<string, string> = { keeps: "the owner likely keeps the saving", check: "check before buying", passes: "the saving likely goes to clients" };

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
            ["Knowledge payroll that passes the structural hand-over screen", <Link key="h" href="#dial" className={link}>{usd(h.passes)}</Link>],
            ["Of which all three models pass", usd(h.agreed3)],
            ["Knowledge payroll scored", usd(h.payroll)],
            ...c.scorers.map((k) => [`${c.scorer_names[k]} alone would pass`, usd(h.by_scorer[k])] as [string, string]),
            ["Agreement across the three models (Fleiss κ: one is perfect, zero is chance)", fmt(h.fleiss_kappa)],
            ["Verdicts that changed when the same model re-scored", fmt(h.rescore_changed, "share")],
            ["Waiting on a check", usd(h.blocked_by_missing_check)],
            ["Removed as physical work", usd(h.physical_removed)],
            ["Removed as an accountable sign-off", usd(h.accountable_removed)],
            ["Modelled saving (modelled, not measured: passing is not saving)", usd(h.modelled_saving)],
          ]} />
          <MarginPanel title="Instrument">
            <p>Judged by {c.scorers.map((k) => c.scorer_names[k]).join(", ")}; the verdict on each task is their vote, under a rule frozen before this version's scores and shaped after seeing earlier usage data. Imported as published from the census&apos;s own files and checked against their published hashes.</p>
            <p>Download: {Object.entries(c.csv).map(([f, href], i) => <span key={f}>{i ? ", " : ""}<a href={href} className={link}>{f}</a></span>)}.</p>
            <p>Query every table in the <Link href="/query" className={link}>SQL console</Link>, e.g. <code className="text-[12px]">SELECT title, share_passes, rule_strict, rule_loose, passes_usd, agreed3_usd FROM census_roles WHERE function = &apos;Finance&apos;</code>.</p>
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
          <Rows head={["Rule", "Passes the screen", "All three pass"]} rows={c.dial} row={(d) => (
            <tr key={d.rule} className={d.headline ? "bg-surface-2" : undefined}><th scope="row">{d.rule}{d.headline ? <strong className="font-medium text-ink"> (the rule used)</strong> : null}</th><td className="tabular-nums">{usd(d.passes)}</td><td className="tabular-nums">{usd(d.agreed3)}</td></tr>
          )} />
        </Section>

        <Section id="roles" n="Part I · roles" title={s.roles.title} lede={s.roles.lede}>
          <div className="flex flex-col gap-2">
            {fns.map((fn) => (
              <details key={fn} className="panel px-4 py-3">
                <summary className="cursor-pointer font-medium">{fn}</summary>
                <Rows head={["Role", "Share that passes (stricter and looser rules)", "Passes the screen", "All three pass", "Observed AI use"]} rows={c.roles.filter((r) => r.function === fn)} row={(r) => (
                  <tr key={r.occ}><th scope="row"><Link href={r.href} className={link}>{r.title}</Link></th><td className="tabular-nums">{fmt(r.share_passes, "share")} <span className="text-muted">({rules(r.rule_strict, r.rule_loose)})</span></td><td className="tabular-nums">{usd(r.passes)}</td><td className="tabular-nums"><A3 v={r.agreed3} /></td><td className="tabular-nums">{r.ai_exposure === null ? <span className="text-muted">—</span> : fmt(r.ai_exposure, "share")}</td></tr>
                )} />
              </details>
            ))}
          </div>
        </Section>

        <Section id="functions" n="Part II · functions" title={s.functions.title} lede={s.functions.lede}>
          <Rows head={["Function", "Knowledge payroll", "Passes the screen", "All three pass", "Share that passes (stricter and looser rules)", "Waiting on a check"]} rows={c.functions} row={(f) => (
            <tr key={f.function}><th scope="row">{f.function}</th><td className="tabular-nums">{usd(f.payroll)}</td><td className="tabular-nums">{usd(f.passes)}</td><td className="tabular-nums"><A3 v={f.agreed3} /></td><td className="tabular-nums">{fmt(f.share_passes, "share")} <span className="text-muted">({rules(f.rule_strict, f.rule_loose)})</span></td><td className="tabular-nums">{usd(f.blocked_by_missing_check)}</td></tr>
          )} />
        </Section>

        <Section id="industries" n="Part III · industries" title={s.industries.title} lede={s.industries.lede}>
          <Rows head={industryHead} rows={c.industries.slice(0, 15)} row={industryRow} />
          <details className="panel px-4 py-3">
            <summary className="cursor-pointer font-medium">Every other industry, by payroll that passes</summary>
            <Rows head={industryHead} rows={c.industries.slice(15)} row={industryRow} />
          </details>
        </Section>

        <Section id="deals" n="Part IV · businesses" title={s.deals.title} lede={s.deals.lede}>
          <div className="grid gap-4 md:grid-cols-2">
            {c.deals.cards.map((d) => (
              <article key={d.key} id={`deal-${d.key}`} className="panel px-4 py-4 flex flex-col gap-2 text-sm">
                <div className="flex flex-wrap gap-2 items-baseline">
                  <span className="eyebrow">{STANCE[d.stance] ?? d.stance}</span>
                  {d.anchored ? <span className="eyebrow text-muted">· sized by occupation, not industry</span> : null}
                </div>
                <h3 className="font-medium text-base">{d.name}</h3>
                <p className="text-ink-2"><strong className="font-medium text-ink">Priced as</strong> {d.invoice}.</p>
                <p className="tabular-nums">Payroll {usd(d.payroll)} · passes the screen {usd(d.passes)} <span className="text-muted">({usd(d.passes_strict)} under the stricter rule, {usd(d.passes_loose)} under the looser)</span> · all three pass <A3 v={d.agreed3} /></p>
                <p className="text-ink-2">{d.stance_why} <span className="text-muted">Reasoned from how the business prices its work, not measured.</span></p>
                <details><summary className="cursor-pointer">Why, the questions that kill it, comparables and sources</summary>
                  <div className="flex flex-col gap-2 mt-2 text-ink-2">
                    <p>{d.why}</p>
                    {d.excl ? <p>{d.excl}</p> : null}
                    <ul className="list-disc pl-5">{d.kill.map((k) => <li key={k}>{k}</li>)}</ul>
                    <p>Comparables, illustrating the pricing model, not researched targets: {d.comps.join("; ")}.</p>
                    {d.sources.length ? <p>Sources: {d.sources.map((x, i) => <span key={x.cited_as}>{i ? ", " : ""}<a href={x.href} className={link}>{new URL(x.cited_as).hostname}</a></span>)}</p> : null}
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
