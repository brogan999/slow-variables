import Link from "next/link";
import { indicatorHref } from "@/lib/format";
import { StatusChip } from "@/components/StatusChip";
import { Num } from "@/components/Provenance";
import { compare, obsIndex, words } from "@/lib/data";
import type { ComparePred } from "@/lib/data";

export const metadata = { title: "Compare" };

const LEAN: Record<string, string> = { nk: "Normal Technology", ai2027: "AI 2027", open: "open" };
const COLS = [["nk", "Normal Technology expects"], ["ai2027", "AI 2027 expects"], ["lab", "Lab timelines say"], ["capture", "Capture theses say"]] as const;

export default function ComparePage() {
  const { rows, tally } = compare();
  const idx = obsIndex();
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">Compare</h1>
        <p className="text-lg leading-snug text-ink-2 max-w-[60ch]">The same evidence read against four families of claims: <em>AI as Normal Technology</em>, <em>AI 2027</em>, the labs&apos; own timelines, and the capture theses about who pays for the build-out. Each claim sits in its family&apos;s column by the ledger it is filed under, citing the sourced claim on the prediction ledger. The last column is not an opinion: for a diffusion indicator it follows from the current status (faster than normal leans AI 2027; consistent with normal or slower leans Normal Technology; anything else is open). A capture indicator reads concentrating or dispersing, which neither lean describes.</p>
      </div>
      <p className="text-sm"><span className="font-medium tabular-nums">{tally.nk}</span> lean Normal Technology · <span className="font-medium tabular-nums">{tally.ai2027}</span> lean AI 2027 · <span className="font-medium tabular-nums">{tally.open}</span> open</p>
      <div className="overflow-x-auto">
        <table className="data w-full min-w-[56rem] text-sm align-top">
          <thead><tr><th scope="col" className="w-[18%]">Indicator</th>{COLS.map(([k, label]) => <th scope="col" key={k} className="w-[18%]">{label}</th>)}<th scope="col">Leans</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.indicator}>
                <td>
                  <Link href={indicatorHref(r.indicator, r.card.published)} className="font-medium hover:underline">{r.card.name}</Link>
                  <div className="mt-1 flex flex-wrap items-center gap-2"><StatusChip status={r.card.published ? r.card.status : null} /><span className="text-xs"><Num p={r.card.latest} unit={r.card.unit} obsIndex={idx} /></span></div>
                </td>
                {COLS.map(([k]) => <td key={k} className="text-ink-2">{r.columns[k].text || (r.columns[k].predictions.length ? null : <span className="text-muted">no claim</span>)}<Preds items={r.columns[k].predictions} /></td>)}
                <td className="whitespace-nowrap font-medium">{r.leans ? LEAN[r.leans] : <span className="text-muted font-normal">n/a (capture)</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted">Every prediction is scored in full on the <Link href="/predictions" className="underline decoration-grid underline-offset-4">prediction ledger</Link>.</p>
    </div>
  );
}

function Preds({ items }: { items: ComparePred[] }) {
  if (!items.length) return null;
  return <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs">{items.map((p) => <Link key={p.id} href={`/predictions#${p.id}`} className="text-muted hover:underline">{p.claimant.split(" (")[0]}: {words(p.status ?? "unscored")}</Link>)}</div>;
}
