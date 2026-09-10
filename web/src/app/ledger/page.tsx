import Link from "next/link";
import { Grade } from "@/components/StatusChip";
import { ledger, sources } from "@/lib/data";
import { fmt } from "@/lib/format";

const NAMES: Record<string, string> = { nvidia: "Nvidia", openai: "OpenAI", amd: "AMD", coreweave: "CoreWeave", oracle: "Oracle", microsoft: "Microsoft", anthropic: "Anthropic", meta: "Meta", nebius: "Nebius", amazon: "Amazon" };
const INSTR: Record<string, string> = { equity: "equity", guarantee: "guarantee", loi: "letter of intent", backstop: "backstop", backstop_talks: "backstop (talks)", warrant: "warrant", commitment: "commitment", azure_commitment: "Azure commitment", aws_commitment: "AWS commitment", contract: "take-or-pay contract", total_commitments: "stated total", commercial_rpo: "commercial RPO", rpo_share: "RPO share", guarantee_customer: "guarantee (announcement)", cds_5y_bps: "5-year CDS" };

export default function LedgerPage() {
  const rows = ledger();
  const srcs = sources();
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Circular financing ledger</h1>
        <p className="text-sm text-ink-2 max-w-3xl">Money that goes round the stack instead of out of it: suppliers investing in, guaranteeing, or buying capacity back from their own customers. Every row is a filed or announced instrument with its verbatim snippet; reported-only rows are flagged. The cumulative signed total feeds the <Link href="/indicators/circular_financing_scale" className="underline decoration-grid underline-offset-4">circular financing scale</Link> indicator; letters of intent, talks and self-reported aggregates are shown but not summed.</p>
      </div>
      <div className="overflow-x-auto">
        <table className="data w-full text-sm">
          <thead><tr><th>Date</th><th>Parties</th><th>Instrument</th><th>Amount</th><th>Grade</th><th>Source</th><th>Flags</th><th>Snippet</th></tr></thead>
          <tbody>
            {rows.map((r) => {
              const src = srcs.find((s) => s.id === r.source_id);
              return (
                <tr key={r.obs_id} id={r.obs_id}>
                  <td className="whitespace-nowrap tabular-nums">{r.as_of_date}</td>
                  <td className="whitespace-nowrap">{r.parties.map((p) => NAMES[p] ?? p).join(" → ")}</td>
                  <td className="whitespace-nowrap text-ink-2">{INSTR[r.instrument] ?? r.instrument.replace(/_/g, " ")}</td>
                  <td className="whitespace-nowrap tabular-nums"><Link href={`/series/${r.series_key}#${r.obs_id}`} className="underline decoration-grid underline-offset-4">{r.value_numeric !== null ? fmt(r.value_numeric, r.unit === "shares" || r.unit === "GW" || r.unit === "bps" ? undefined : r.unit) : "—"}</Link>{r.unit === "shares" ? " shares" : r.unit === "GW" ? " GW" : r.unit === "bps" ? " bps" : ""}</td>
                  <td><Grade grade={r.grade} tier={r.tier} /></td>
                  <td className="text-xs"><a href={r.url} className="underline decoration-grid underline-offset-4">{src?.name ?? r.source_id}</a></td>
                  <td className="text-xs">{r.disputed ? <span className="text-slow" title={r.dispute_text ?? ""}>⚑ reported / disputed</span> : null}</td>
                  <td className="text-xs text-ink-2 max-w-md">{r.value_text ? <span className="italic">{r.value_text}. </span> : null}{r.raw_snippet.slice(0, 220)}{r.raw_snippet.length > 220 ? "…" : ""}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
