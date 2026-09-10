import Link from "next/link";
import { Num } from "@/components/Provenance";
import { Grade, StatusChip } from "@/components/StatusChip";
import { index, obsIndex } from "@/lib/data";

export default function Indicators() {
  const { indicators, buckets, layers } = index();
  const idx = obsIndex();
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold tracking-tight">Indicators</h1>
      <p className="text-sm text-ink-2 max-w-3xl">One object, two addresses. Unpublished rows have a definition but no approved observation yet, so they carry no status.</p>
      <div className="overflow-x-auto">
        <table className="data w-full text-sm">
          <thead><tr><th>Indicator</th><th>Bucket</th><th>Layer</th><th>Status</th><th>Conf</th><th>Grade</th><th>Latest</th><th>Obs</th></tr></thead>
          <tbody>
            {indicators.map((c) => (
              <tr key={c.id}>
                <td><Link href={`/indicators/${c.id}`} className="font-medium hover:underline">{c.name}</Link>{c.published ? null : <span className="ml-2 text-xs text-muted">unpublished</span>}</td>
                <td className="text-ink-2">{buckets.find((b) => b.id === c.bucket_id)?.name ?? "—"}</td>
                <td className="text-ink-2">{layers.find((l) => l.id === c.layer_id)?.name ?? "—"}</td>
                <td><StatusChip status={c.published ? c.status : null} /></td>
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
