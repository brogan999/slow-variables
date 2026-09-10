import Link from "next/link";
import { Num } from "@/components/Provenance";
import { Grade, StatusChip } from "@/components/StatusChip";
import { index, obsIndex } from "@/lib/data";

export const metadata = { title: "Indicators" };

export default function Indicators() {
  const { indicators, buckets, layers } = index();
  const idx = obsIndex();
  return (
    <div className="flex flex-col gap-4">
      <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">Indicators</h1>
      <p className="text-lg leading-snug text-ink-2 max-w-[60ch]">One object, two addresses. Unpublished rows have a definition and data but do not yet meet the publishing rules (a status, counterevidence, and either two sources or one primary source), so they carry no status and no page.</p>
      <div className="overflow-x-auto">
        <table className="data w-full text-sm">
          <thead><tr><th scope="col">Indicator</th><th scope="col">Bucket</th><th scope="col">Layer</th><th scope="col">Status</th><th scope="col">Conf</th><th scope="col">Grade</th><th scope="col">Latest</th><th scope="col">Obs</th></tr></thead>
          <tbody>
            {indicators.map((c) => (
              <tr key={c.id}>
                <td>{c.published ? <Link href={`/indicators/${c.id}`} className="font-medium hover:underline">{c.name}</Link> : <span className="font-medium text-ink-2">{c.name}</span>}{c.published ? null : <span className="ml-2 text-xs text-muted">unpublished</span>}{!c.published && c.unpublished_reason ? <div className="text-xs text-ink-2 mt-0.5 max-w-md">{c.unpublished_reason}</div> : null}</td>
                <td className="text-ink-2">{buckets.find((b) => b.id === c.bucket_id)?.name ?? "—"}</td>
                <td className="text-ink-2">{layers.find((l) => l.id === c.layer_id)?.name ?? "—"}</td>
                <td>{c.published ? <StatusChip status={c.status} /> : <span className="text-xs text-muted">no status until published</span>}</td>
                <td className="tabular-nums">{c.confidence ?? "—"}</td>
                <td><Grade grade={c.grade} /></td>
                <td><Num p={c.latest} unit={c.unit} obsIndex={idx} /></td>
                <td className="tabular-nums text-ink-2">{c.n_observations}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
