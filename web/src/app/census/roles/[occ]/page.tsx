import Link from "next/link";
import { ArticleLayout, MarginPanel } from "@/components/ArticleLayout";
import { PageHeader } from "@/components/PageHeader";
import { census, censusRole, type CensusTask } from "@/lib/data";
import { fmt } from "@/lib/format";

export const dynamicParams = false;
export function generateStaticParams() { return census().roles.map((r) => ({ occ: r.occ })); }
export async function generateMetadata({ params }: { params: Promise<{ occ: string }> }) {
  const { occ } = await params;
  const r = censusRole(occ).role;
  return { title: `${r.title}: the hand-over screen`, description: `Every task of ${r.title.toLowerCase()} in the automatability census, whether it passes the structural hand-over screen, which models pass it, and why.` };
}

const usd = (v: number | null | undefined) => (v === 0 ? "$0" : fmt(v, "USD"));
const link = "underline decoration-grid underline-offset-4 hover:decoration-ink";

function Task({ t, names, order }: { t: CensusTask; names: Record<string, string>; order: string[] }) {
  const passing = order.filter((k) => t.passes_by[k]).map((k) => names[k] ?? k);
  const flags = [
    t.passes && t.agreed_all_three ? "all three pass it" : passing.length ? `passed by ${passing.join(", ")}` : null,
    t.contested ? "the models disagreed" : null,
    t.blocked_by_missing_check ? "waiting on a check" : null,
    t.not_called ? "not called: fewer than three scores" : null,
  ].filter(Boolean);
  return (
    <li className="py-2.5 border-t border-grid first:border-0">
      <p className="text-[15px]">{t.task}</p>
      <p className="text-[12px] text-ink-2 mt-1">{t.why} · {fmt(t.time_share, "share")} of the role&apos;s time · {usd(t.payroll)}{flags.length ? ` · ${flags.join(" · ")}` : ""}</p>
    </li>
  );
}

export default async function CensusRolePage({ params }: { params: Promise<{ occ: string }> }) {
  const { occ } = await params;
  const d = censusRole(occ);
  const r = d.role;
  const names = census().scorer_names;
  const passes = d.tasks.filter((t) => t.passes);
  const stays = d.tasks.filter((t) => !t.passes);
  return (
    <ArticleLayout
      head={
        <PageHeader
          eyebrow={<><Link href="/census" className="hover:text-ink">Census</Link> · {r.function} · occupation code {r.occ}</>}
          title={r.title}
          lede={`Every task in this role, whether it passes the census's structural hand-over screen, which models pass it, and why. It is a screen, not a claim about what AI can do: a task can pass and still be beyond the systems of the day. The stricter and looser rules re-vote every task, and small differences between roles are noise.`}
        />
      }
      margin={
        <>
          <MarginPanel title={`Census · version ${d.version}`} rows={[
            ["Share of the work that passes", fmt(r.share_passes, "share")],
            ["Under the stricter and looser rules", `${fmt(r.rule_strict, "share")} and ${fmt(r.rule_loose, "share")}`],
            ...d.scorers.map((k) => [`Under ${names[k] ?? k} alone`, fmt(r.by_scorer[k], "share")] as [string, string]),
            ["Payroll that passes the screen", usd(r.passes)],
            ["Of which all three models pass", r.agreed3 === null ? <span key="n" className="text-muted">not scored by all three</span> : usd(r.agreed3)],
            ["Observed AI use in this role", r.ai_exposure === null ? "—" : fmt(r.ai_exposure, "share")],
            ["Payroll the models disagreed on", usd(r.contested)],
            ["Wage bill", usd(r.wage_bill)],
            ["Workers", fmt(r.emp, "count")],
          ]} />
          <MarginPanel title="Instrument">
            <p>Each task was scored by three AI models and the verdict is their vote, under a rule frozen before this version's scores; no person judged individual tasks.{r.split === "equal" ? " The Labor Department publishes this role only with related ones, so its payroll is split evenly among them." : ""}</p>
            <p><a href={d.csv} className={link}>All tasks as CSV</a> · <Link href="/census#method" className={link}>Method and what failed</Link></p>
          </MarginPanel>
        </>
      }
    >
      <div className="flex flex-col gap-12">
        <div className="grid gap-6 md:grid-cols-2 items-start">
          <section aria-labelledby="goes-h" className="panel px-4 py-4">
            <h2 id="goes-h" className="display text-[1.4rem] leading-tight">Passes the screen <span className="text-muted text-base">· {fmt(r.n_passes, "count")} of {fmt(r.n_tasks, "count")} tasks</span></h2>
            {passes.length ? <ul>{passes.map((t) => <Task key={t.id} t={t} names={names} order={d.scorers} />)}</ul> : <p className="text-sm text-ink-2 mt-2">No task in this role passes the screen.</p>}
          </section>
          <section aria-labelledby="stays-h" className="panel px-4 py-4 bg-surface-2">
            <h2 id="stays-h" className="display text-[1.4rem] leading-tight">Does not pass</h2>
            <ul>{stays.map((t) => <Task key={t.id} t={t} names={names} order={d.scorers} />)}</ul>
          </section>
        </div>
        {d.industries.length ? (
          <section aria-labelledby="ind-h">
            <h2 id="ind-h" className="display text-[1.4rem] leading-tight mb-3">Where this role works</h2>
            <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Table: industries employing this role">
              <table className="data w-full text-sm">
                <thead><tr><th scope="col">Industry</th><th scope="col">Workers</th><th scope="col">Wage bill</th><th scope="col">Passes the screen</th><th scope="col">All three pass</th></tr></thead>
                <tbody>{d.industries.map((i) => (
                  <tr key={i.naics}><th scope="row"><Link href={`/census#naics-${i.naics}`} className={link}>{i.title}</Link></th><td className="tabular-nums">{fmt(i.emp, "count")}</td><td className="tabular-nums">{usd(i.wage_bill)}</td><td className="tabular-nums">{usd(i.passes)}</td><td className="tabular-nums">{i.agreed3 === null ? <span className="text-muted">not scored by all three</span> : usd(i.agreed3)}</td></tr>
                ))}</tbody>
              </table>
            </div>
          </section>
        ) : null}
      </div>
    </ArticleLayout>
  );
}
