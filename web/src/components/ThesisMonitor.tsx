import type { ThesisVerdict } from "@/lib/data";
import { ObsLinks } from "./Provenance";

const WORD: Record<string, string> = { supported: "holds", contradicted: "contradicted", unsupported: "does not hold", untestable: "untestable" };
const MARK: Record<string, string> = { true: "✓", false: "✗", null: "?" };

// The brief's Appendix B rules, evaluated nightly. Every condition names the observations it read.
export function ThesisMonitor({ verdicts, obsIndex }: { verdicts: ThesisVerdict[]; obsIndex: Record<string, string> }) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {verdicts.map((v) => (
        <details key={v.id} className="panel p-3">
          <summary className="cursor-pointer text-sm"><span className="font-medium">{v.name}</span> <span className={v.state === "untestable" ? "text-muted" : v.state === "contradicted" ? "text-slow" : "text-ink-2"}>· {WORD[v.state] ?? "untestable"}</span></summary>
          <p className="mt-2 text-xs text-muted">{v.logic}</p>
          <ul className="mt-2 flex flex-col gap-1.5 text-xs">
            {v.conds.map((c) => (
              <li key={c.text} className="flex gap-2">
                <span className="w-3 shrink-0 text-ink-2">{MARK[String(c.holds)]}</span>
                <span><span className="text-ink">{c.text}</span> <span className="text-ink-2">— {c.detail}</span>{c.obs_ids.length ? <span className="ml-1"><ObsLinks ids={c.obs_ids} obsIndex={obsIndex} max={2} /></span> : null}</span>
              </li>
            ))}
          </ul>
          {v.counter?.length ? (
            <ul className="mt-2 flex flex-col gap-1.5 text-xs border-t border-grid pt-2">
              <li className="text-muted">Contradicted when:</li>
              {v.counter.map((c) => (
                <li key={c.text} className="flex gap-2">
                  <span className="w-3 shrink-0 text-ink-2">{MARK[String(c.holds)]}</span>
                  <span><span className="text-ink">{c.text}</span> <span className="text-ink-2">— {c.detail}</span></span>
                </li>
              ))}
            </ul>
          ) : null}
        </details>
      ))}
    </div>
  );
}
