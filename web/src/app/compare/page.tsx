import Link from "next/link";
import { StatusChip } from "@/components/StatusChip";
import { Num } from "@/components/Provenance";
import { compare, obsIndex, words } from "@/lib/data";

export const metadata = { title: "Compare" };

const LEAN: Record<string, string> = { nk: "Normal Technology", ai2027: "AI 2027", open: "open" };

export default function ComparePage() {
  const { rows, tally } = compare();
  const idx = obsIndex();
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">Compare</h1>
        <p className="text-lg leading-snug text-ink-2 max-w-[60ch]">The same evidence read against both worldviews. Each row is a published indicator; the two middle columns say what <em>AI as Normal Technology</em> and <em>AI 2027</em> (with the lab timelines that share its premise) expect it to show, citing the sourced claims on the prediction ledger. The last column is not an opinion: it is derived from the indicator&apos;s current status. Faster than normal leans AI 2027; consistent with normal or slower leans Normal Technology; emerging, unclear or unmeasured is open.</p>
      </div>
      <p className="text-sm"><span className="font-medium tabular-nums">{tally.nk}</span> lean Normal Technology · <span className="font-medium tabular-nums">{tally.ai2027}</span> lean AI 2027 · <span className="font-medium tabular-nums">{tally.open}</span> open</p>
      <div className="overflow-x-auto">
        <table className="data w-full text-sm align-top">
          <thead><tr><th scope="col" className="w-[22%]">Indicator</th><th scope="col" className="w-[30%]">Normal Technology expects</th><th scope="col" className="w-[30%]">AI 2027 expects</th><th scope="col">Leans</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.indicator}>
                <td>
                  <Link href={`/indicators/${r.indicator}`} className="font-medium hover:underline">{r.card.name}</Link>
                  <div className="mt-1 flex flex-wrap items-center gap-2"><StatusChip status={r.card.published ? r.card.status : null} /><span className="text-xs"><Num p={r.card.latest} unit={r.card.unit} obsIndex={idx} /></span></div>
                </td>
                <td className="text-ink-2">{r.nk}<Preds items={r.nk_predictions} /></td>
                <td className="text-ink-2">{r.ai2027}<Preds items={r.ai2027_predictions} /></td>
                <td className="whitespace-nowrap font-medium">{LEAN[r.leans]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted">Rows are the diffusion-lens indicators both worldviews make claims about. Capture-lens indicators (who keeps the surplus) are scored on the <Link href="/predictions" className="underline decoration-grid underline-offset-4">prediction ledger</Link> under the capture theses.</p>
    </div>
  );
}

function Preds({ items }: { items: { id: string; claimant: string; status: string | null }[] }) {
  if (!items.length) return null;
  return <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs">{items.map((p) => <Link key={p.id} href={`/predictions#${p.id}`} className="text-muted hover:underline">{p.claimant.split(" (")[0]}: {words(p.status ?? "unscored")}</Link>)}</div>;
}
