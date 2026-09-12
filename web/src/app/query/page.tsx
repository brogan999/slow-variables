import { QueryConsole } from "@/components/QueryConsole";
import { Num, ObsLinks } from "@/components/Provenance";
import { ThesisMonitor } from "@/components/ThesisMonitor";
import { analyses, obsIndex, thesis } from "@/lib/data";

export const metadata = { title: "Query" };

export default function QueryPage() {
  const rows = analyses();
  const idx = obsIndex();
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">Query</h1>
        <p className="text-lg leading-snug text-ink-2 max-w-[60ch]">Saved analyses are materialised by the nightly export from the semantic layer; each shows its latest value, the observations behind it and the formula. The console runs read-only SQL against the same store; the Ask button in the header puts a model in front of it, with every number checked against the record it cites.</p>
      </div>
      <section className="flex flex-col gap-3">
        <h2 className="display text-2xl leading-tight">Saved analyses</h2>
        <ul className="grid gap-3 md:grid-cols-2">
          {rows.map((a) => (
            <li key={a.id} id={a.metric} className="panel p-3 text-sm flex flex-col gap-1.5">
              <div className="font-medium">{a.name}</div>
              <p className="text-xs text-ink-2">{a.question}</p>
              {a.latest ? (
                <div className="flex flex-wrap items-baseline gap-x-2 text-sm">
                  <Num p={{ as_of: a.latest.as_of_date, value: a.latest.value, obs_ids: a.latest.obs_ids }} unit={a.shape?.unit} obsIndex={idx} />{a.dims ? <span className="text-xs text-muted">{Object.values(a.dims).join(", ")}</span> : null}
                </div>
              ) : <span className="text-xs text-muted">unmeasured</span>}
              {a.latest ? (
                <details className="text-xs"><summary className="cursor-pointer text-ink-2">{a.latest.obs_ids.length} observation{a.latest.obs_ids.length === 1 ? "" : "s"}</summary><div className="mt-1"><ObsLinks ids={a.latest.obs_ids} obsIndex={idx} max={24} /></div></details>
              ) : null}
              {a.caveats ? <p className="text-xs text-muted">{a.caveats}</p> : null}
              <details className="text-xs"><summary className="cursor-pointer text-ink-2">Formula</summary><pre className="mt-1 overflow-x-auto whitespace-pre-wrap font-mono text-[11px] text-ink-2">{a.sql}</pre></details>
            </li>
          ))}
        </ul>
      </section>
      <section className="flex flex-col gap-3" id="falsification">
        <h2 className="display text-2xl leading-tight">Falsification monitor</h2>
        <p className="text-sm text-ink-2 max-w-[60ch]">The rule that would falsify the normal-technology reading, evaluated nightly. Each condition names the observations it read.</p>
        <ThesisMonitor verdicts={thesis().filter((v) => v.id === "normal_tech_falsified")} obsIndex={idx} />
      </section>
      <section className="flex flex-col gap-2">
        <h2 className="display text-2xl leading-tight">Console</h2>
        <QueryConsole initial={"SELECT metric, count(*) AS rows, max(as_of_date) AS latest\nFROM derived GROUP BY 1 ORDER BY 1"} />
      </section>
    </div>
  );
}
