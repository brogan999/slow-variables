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
  return { title: `${r.title}: what AI can take`, description: `Every task of ${r.title.toLowerCase()} in the automatability census, whether it can go to AI today, and why.` };
}

const usd = (v: number | null | undefined) => (v === 0 ? "$0" : fmt(v, "USD"));
const link = "underline decoration-grid underline-offset-4 hover:decoration-ink";

function Task({ t }: { t: CensusTask }) {
  const flags = [
    t.contested ? "the models disagreed" : null,
    t.goes && t.agreed_all_three ? "all three agree" : null,
    t.blocked_by_verifier ? "only an expert can check it today" : null,
    t.n_scorers < 3 ? "not scored by all three" : null,
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
  const goes = d.tasks.filter((t) => t.goes);
  const stays = d.tasks.filter((t) => !t.goes);
  return (
    <ArticleLayout
      head={
        <PageHeader
          eyebrow={<><Link href="/census" className="hover:text-ink">Census</Link> · {r.function} · occupation code {r.occ}</>}
          title={r.title}
          lede={`Every task in this role, whether AI can take it on today under the census rule, and why. The share that can go is a range, not a rank: tightening or loosening the rule moves it.`}
        />
      }
      margin={
        <>
          <MarginPanel title={`Census · version ${d.version}`} rows={[
            ["Share of the work that can go", <span key="s">{fmt(r.share_goes, "share")} <span className="text-muted font-normal">({fmt(r.band_lo, "share")} to {fmt(r.band_hi, "share")})</span></span>],
            ["Payroll that can go", usd(r.freed)],
            ["Of which all three models agree", r.agreed3 === null ? <span key="n" className="text-muted">not scored by all three</span> : usd(r.agreed3)],
            ["Payroll the models disagreed on", usd(r.contested)],
            ["Wage bill", usd(r.wage_bill)],
            ["Workers", fmt(r.emp, "count")],
          ]} />
          <MarginPanel title="Instrument">
            <p>Each task was scored by up to three AI models and the verdict is their vote; no person judged individual tasks.</p>
            <p><a href={d.csv} className={link}>All tasks as CSV</a> · <Link href="/census#method" className={link}>Method and what failed</Link></p>
          </MarginPanel>
        </>
      }
    >
      <div className="flex flex-col gap-12">
        <div className="grid gap-6 md:grid-cols-2 items-start">
          <section aria-labelledby="goes-h" className="panel px-4 py-4">
            <h2 id="goes-h" className="display text-[1.4rem] leading-tight">Can go <span className="text-muted text-base">· {fmt(goes.length, "count")} tasks</span></h2>
            {goes.length ? <ul>{goes.map((t) => <Task key={t.id} t={t} />)}</ul> : <p className="text-sm text-ink-2 mt-2">No task in this role can go under the rule.</p>}
          </section>
          <section aria-labelledby="stays-h" className="panel px-4 py-4 bg-surface-2">
            <h2 id="stays-h" className="display text-[1.4rem] leading-tight">Stays <span className="text-muted text-base">· {fmt(stays.length, "count")} tasks</span></h2>
            <ul>{stays.map((t) => <Task key={t.id} t={t} />)}</ul>
          </section>
        </div>
        {d.industries.length ? (
          <section aria-labelledby="ind-h">
            <h2 id="ind-h" className="display text-[1.4rem] leading-tight mb-3">Where this role works</h2>
            <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Where this role works">
              <table className="data w-full text-sm">
                <thead><tr><th scope="col">Industry</th><th scope="col">Workers</th><th scope="col">Wage bill</th><th scope="col">Can go</th><th scope="col">All three agree</th></tr></thead>
                <tbody>{d.industries.map((i) => (
                  <tr key={i.naics}><th scope="row"><Link href={`/census#naics-${i.naics}`} className={link}>{i.title}</Link></th><td className="tabular-nums">{fmt(i.emp, "count")}</td><td className="tabular-nums">{usd(i.wage_bill)}</td><td className="tabular-nums">{usd(i.freed)}</td><td className="tabular-nums">{r.agreed3 === null ? <span className="text-muted">not scored by all three</span> : usd(i.agreed3)}</td></tr>
                ))}</tbody>
              </table>
            </div>
          </section>
        ) : null}
      </div>
    </ArticleLayout>
  );
}
