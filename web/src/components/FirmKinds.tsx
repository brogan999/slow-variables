import Link from "next/link";
import { Figure, Key } from "@/components/Figure";
import { KIND_LABEL, Pyramid, ShareBars, Swatch } from "@/components/diagrams/kit";
import type { FirmKind, FirmKindsDoc, KindPart } from "@/lib/data";
import { fmt } from "@/lib/format";

// What happens to each kind of firm: the figures. Every share and position is the export's.
const FILL: Record<KindPart, string> = { passes: "var(--s1)", waits_on_check: "var(--tight-2)", held: "var(--s3)", outside: "var(--s3)" };
const PART: Record<KindPart, string> = {
  passes: "passes the screen", waits_on_check: "waits only on a check", held: "held for more than a missing check", outside: "not office work, so outside the census",
};
const TIER = { managers: "Managers", professionals: "Professionals", sales: "Sales", support: "Office support" } as const;
const share = (k: FirmKind, p: KindPart) => ({ passes: k.share_passes, waits_on_check: k.share_waits_on_check, held: k.share_held, outside: k.share_outside })[p];
const census = <Link href="/census" className="text-ink underline decoration-axis underline-offset-2">the census</Link>;

export function KindBars({ doc }: { doc: FirmKindsDoc }) {
  return (
    <Figure
      id="fig-bars"
      title="How much of each kind of firm's payroll a check can settle"
      note={KIND_LABEL.chart}
      keys={<>{(Object.keys(PART) as KindPart[]).map((p) => <Key key={p} swatch={<Swatch fill={FILL[p]} hatched={p === "outside"} />}>{PART[p]}</Key>)}</>}
      foot={<p>Shares of each kind of firm&apos;s whole payroll, from {census} ({doc.version}), a screen scored by three AI models and not a record of what has been automated. A kind of firm is one or more of the census&apos;s industries; hover a bar for its share.</p>}
      table={
        <table className="data">
          <thead><tr><th scope="col">Kind of firm</th><th scope="col">Passes</th><th scope="col">All three models pass</th><th scope="col">Waits only on a check</th><th scope="col">Held for more</th><th scope="col">Outside the census</th><th scope="col">Industries</th></tr></thead>
          <tbody>{doc.kinds.map((k) => (
            <tr key={k.id}><th scope="row">{k.name}</th><td>{fmt(k.share_passes, "share")}</td><td>{fmt(k.share_agreed3, "share")}</td><td>{fmt(k.share_waits_on_check, "share")}</td><td>{fmt(k.share_held, "share")}</td><td>{fmt(k.share_outside, "share")}</td><td className="text-muted">{k.titles.join("; ")}</td></tr>
          ))}</tbody>
        </table>
      }
    >
      <ShareBars
        label="Each kind of firm's payroll, split by what the census screen says of it"
        rows={doc.kinds.map((k) => ({
          name: k.name,
          segs: k.bar.map((s) => ({ key: s.part, x: s.x, w: s.w, fill: FILL[s.part], hatched: s.part === "outside", tip: `${k.name}: ${fmt(share(k, s.part), "share")} ${PART[s.part]}` })),
        }))}
      />
    </Figure>
  );
}

export function KindShapes({ doc }: { doc: FirmKindsDoc }) {
  return (
    <Figure
      id="fig-shapes"
      title="The shape of each kind of firm today, by where its office payroll sits"
      note={KIND_LABEL.chart}
      keys={<><Key swatch={<Swatch fill="var(--s3)" />}>a layer, as wide as its share of office payroll</Key><Key swatch={<Swatch fill="var(--s1)" />}>the part of that layer that passes the screen</Key></>}
      foot={<p>Layers are groups of occupations, not ranks: the census has no field for seniority. Top to bottom: managers, professionals, sales, office support. From {census} ({doc.version}).</p>}
    >
      <div className="grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-3 lg:grid-cols-4">
        {doc.kinds.map((k) => (
          <div key={k.id} className="flex flex-col gap-2">
            <Pyramid
              compact
              label={`${k.name}: ${k.tiers.map((t) => `${TIER[t.id]} ${fmt(t.share, "share")}`).join(", ")}`}
              tiers={k.tiers.map((t) => ({ key: t.id, label: TIER[t.id], w: t.w, inner: t.pass_w, tip: `${TIER[t.id]}: ${fmt(t.share, "share")} of office payroll, ${fmt(t.share_passes, "share")} of it passes` }))}
            />
            <div className="text-center text-[12px] leading-tight text-ink-2">{k.name}</div>
          </div>
        ))}
      </div>
    </Figure>
  );
}
