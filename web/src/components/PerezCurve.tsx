import { ChartSources } from "@/components/ChartSources";
import { Fact } from "@/components/Fact";
import { Figure, Key } from "@/components/Figure";
import type { ArgumentDoc } from "@/lib/data";
import { PHASE_WORDS } from "@/lib/format";

// Perez's two halves as a schematic: the curve is her shape, not data. The only data on it is which region the
// published phase rule picks, marked at that region's centre: a phase, never a precise position. The drawing stretches
// with its box; the marker and every label are HTML or percent-placed, so none collides with the curve at any width.
const ARTICLE = { installation: "installation", turning_point: "a turning point", deployment: "deployment" } as const;
const CURVE = "M40,206 C120,200 150,150 200,120 C240,96 268,86 300,120 C326,148 340,168 370,150 C420,120 470,80 520,58 C560,42 600,34 636,30";
const AT = { installation: { x: 25.76, y: 56.4, align: "center" }, turning_point: { x: 50.91, y: 59.2, align: "center" }, deployment: { x: 78.79, y: 23.2, align: "end" } } as const;

export function PerezCurve({ phase, facts }: { phase: ArgumentDoc["phase"]; facts: ArgumentDoc["facts"] }) {
  const at = phase.state !== "untestable" ? AT[phase.state] : null;
  return (
    <Figure
      title="Which half of Perez's cycle the readings put us in"
      note="schematic, after Perez (2002) · not data"
      keys={<>
        <Key swatch={<span aria-hidden className="inline-block h-2.5 w-4 bg-surface-2 ring-1 ring-grid" />}>the turning point</Key>
        {at ? <Key swatch={<svg width="12" height="12" aria-hidden><circle cx="6" cy="6" r="5" fill="none" stroke="var(--ink)" strokeWidth="1.5" /><circle cx="6" cy="6" r="2.5" fill="var(--ink)" /></svg>}>where the published rule puts the readings</Key> : null}
      </>}
      foot={<>
        <p>The marker is placed by a published rule, using spending on buildings and equipment at <Fact f={facts.capex_to_revenue} /> the AI revenue we can measure, and <Fact f={facts.vendor_financing_4q} /> of commitments signed in four quarters in deals where the seller also funds the buyer. {phase.state === "untestable" ? "One of those series has no reading, so no position is shown." : `By that rule this is ${ARTICLE[phase.state]}.`} The rule: {phase.rule}</p>
        <ChartSources cs={phase.chart_sources} />
      </>}
      table={phase.history.length ? (
        <table className="data w-full">
          <thead><tr><th scope="col">quarter</th><th scope="col">the rule reads</th><th scope="col">phase shown</th></tr></thead>
          <tbody>{phase.history.slice().reverse().map((h) => <tr key={h.as_of}><td className="num">{h.as_of}</td><td>{PHASE_WORDS[h.raw] ?? h.raw}</td><td>{PHASE_WORDS[h.state] ?? h.state}</td></tr>)}</tbody>
        </table>
      ) : undefined}
    >
      <div className="grid grid-cols-[45.45%_10.91%_43.64%] gap-y-1 text-ink" aria-hidden>
        <div><div className="font-serif text-[1.2rem] leading-tight">Installation</div><div className="font-mono text-[11px] text-ink-2">finance leads, gains concentrate</div></div>
        <div />
        <div className="text-right"><div className="font-serif text-[1.2rem] leading-tight">Deployment</div><div className="font-mono text-[11px] text-ink-2">production leads, gains spread</div></div>
      </div>
      <div className="relative mt-2 h-40 md:h-52" role="img" aria-label={`Schematic of Carlota Perez's installation and deployment periods; the tracker's phase rule reads ${PHASE_WORDS[phase.state]}`}>
        <svg viewBox="0 0 660 250" preserveAspectRatio="none" className="absolute inset-0 h-full w-full" aria-hidden>
          <rect x="300" y="18" width="72" height="194" fill="var(--surface-2)" />
          <line x1="40" y1="212" x2="640" y2="212" stroke="var(--axis)" vectorEffect="non-scaling-stroke" />
          <path d={CURVE} fill="none" stroke="var(--ink)" strokeWidth="2" vectorEffect="non-scaling-stroke" />
        </svg>
        {at ? (
          <svg className="absolute inset-0 h-full w-full overflow-visible" aria-hidden>
            <line x1={`${at.x}%`} y1={`${at.y}%`} x2={`${at.x}%`} y2="100%" stroke="var(--ink)" strokeDasharray="2 3" />
            <circle cx={`${at.x}%`} cy={`${at.y}%`} r="9" fill="var(--surface)" stroke="var(--ink)" strokeWidth="2" />
            <circle cx={`${at.x}%`} cy={`${at.y}%`} r="4.5" fill="var(--ink)" />
          </svg>
        ) : null}
      </div>
      <div className="relative h-6" aria-hidden>
        {at ? <span className={`absolute top-1 whitespace-nowrap font-mono text-[11px] text-ink ${at.align === "end" ? "-translate-x-[92%]" : "-translate-x-1/2"}`} style={{ left: `${at.x}%` }}>the readings put us here</span> : null}
      </div>
    </Figure>
  );
}
