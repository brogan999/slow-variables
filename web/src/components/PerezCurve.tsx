import { ChartSources } from "@/components/ChartSources";
import { Fact } from "@/components/Fact";
import { Figure, Key } from "@/components/Figure";
import type { ArgumentDoc } from "@/lib/data";
import { PHASE_WORDS } from "@/lib/format";

// Perez's cycle as a schematic: the curve is her shape, not data. Two halves, each of two phases, with a turning point
// between. The only data on it is which phase (or, when the finer phase cannot be told, which half) the published rule
// picks: a region, never a precise position. Percent positions are fixed constants of the drawing, not computed.
const ARTICLE: Record<string, string> = {
  irruption: "irruption", frenzy: "frenzy", installation: "installation", turning_point: "a turning point",
  synergy: "synergy", maturity: "maturity", deployment: "deployment",
};
const CURVE = "M40,206 C120,200 150,150 200,120 C240,96 268,86 300,120 C326,148 340,168 370,150 C420,120 470,80 520,58 C560,42 600,34 636,30";
// a point for a phase; a span for a half
const AT: Record<string, { x: number; y: number } | { from: number; to: number }> = {
  irruption: { x: 15.91, y: 81 }, frenzy: { x: 35.61, y: 40 }, turning_point: { x: 50.91, y: 59.2 },
  synergy: { x: 66.52, y: 44.8 }, maturity: { x: 86.82, y: 16 },
  installation: { from: 6.06, to: 45.45 }, deployment: { from: 56.36, to: 96.97 },
};
const PHASES = [["Irruption", "a new technology finds its first uses"], ["Frenzy", "finance piles in"], ["Turning point", "a crash, then new rules"], ["Synergy", "production leads, gains spread"], ["Maturity", "returns fall, the next revolution starts"]] as const;
const COLS = "grid-cols-[6.06%_19.7%_19.7%_10.91%_20.3%_20.3%_3.03%]";

export function PerezCurve({ phase, facts }: { phase: ArgumentDoc["phase"]; facts: ArgumentDoc["facts"] }) {
  const at = AT[phase.state] ?? null;
  const point = at && "x" in at ? at : null;
  const span = at && "from" in at ? at : null;
  return (
    <Figure
      title="Where the readings put us in Perez's cycle"
      note="schematic, after Perez (2002) · not data"
      keys={<>
        <Key swatch={<span aria-hidden className="inline-block h-2.5 w-4 bg-surface-2 ring-1 ring-grid" />}>the turning point</Key>
        {at ? <Key swatch={<svg width="12" height="12" aria-hidden><circle cx="6" cy="6" r="5" fill="none" stroke="var(--ink)" strokeWidth="1.5" /><circle cx="6" cy="6" r="2.5" fill="var(--ink)" /></svg>}>where the published rule puts the readings</Key> : null}
      </>}
      foot={<>
        <p>The marker is placed by a published rule, using spending on buildings and equipment at <Fact f={facts.capex_to_revenue} /> the AI revenue we can measure, and <Fact f={facts.vendor_financing_4q} /> of commitments signed in four quarters in deals where the seller also funds the buyer. {phase.state === "untestable" ? "One of those series has no reading, so no position is shown." : span ? `By that rule this is ${ARTICLE[phase.state]}; the phase inside it cannot yet be told apart, so the whole half is marked.` : `By that rule this is ${ARTICLE[phase.state] ?? PHASE_WORDS[phase.state]}.`} The rule: {phase.rule}</p>
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
      <div className="relative mt-2 h-40 md:h-52" role="img" aria-label={`Schematic of Carlota Perez's cycle: irruption and frenzy make up installation, then a turning point, then synergy and maturity make up deployment. The tracker's phase rule reads ${PHASE_WORDS[phase.state] ?? phase.state}`}>
        <svg viewBox="0 0 660 250" preserveAspectRatio="none" className="absolute inset-0 h-full w-full" aria-hidden>
          <rect x="300" y="18" width="72" height="194" fill="var(--surface-2)" />
          {[170, 506].map((x) => <line key={x} x1={x} y1="18" x2={x} y2="212" stroke="var(--grid)" strokeDasharray="3 4" vectorEffect="non-scaling-stroke" />)}
          <line x1="40" y1="212" x2="640" y2="212" stroke="var(--axis)" vectorEffect="non-scaling-stroke" />
          <path d={CURVE} fill="none" stroke="var(--ink)" strokeWidth="2" vectorEffect="non-scaling-stroke" />
        </svg>
        {point ? (
          <svg className="absolute inset-0 h-full w-full overflow-visible" aria-hidden>
            <line x1={`${point.x}%`} y1={`${point.y}%`} x2={`${point.x}%`} y2="100%" stroke="var(--ink)" strokeDasharray="2 3" />
            <circle cx={`${point.x}%`} cy={`${point.y}%`} r="9" fill="var(--surface)" stroke="var(--ink)" strokeWidth="2" />
            <circle cx={`${point.x}%`} cy={`${point.y}%`} r="4.5" fill="var(--ink)" />
          </svg>
        ) : null}
        {span ? (
          <svg className="absolute inset-0 h-full w-full overflow-visible" aria-hidden>
            <line x1={`${span.from}%`} y1="3%" x2={`${span.to}%`} y2="3%" stroke="var(--ink)" strokeWidth="2" />
            <line x1={`${span.from}%`} y1="0%" x2={`${span.from}%`} y2="7%" stroke="var(--ink)" strokeWidth="2" />
            <line x1={`${span.to}%`} y1="0%" x2={`${span.to}%`} y2="7%" stroke="var(--ink)" strokeWidth="2" />
          </svg>
        ) : null}
      </div>
      <div className={`grid ${COLS} gap-y-1 text-ink`} aria-hidden>
        <div />
        {PHASES.map(([name, gloss]) => (
          <div key={name} className="text-center"><div className="font-sans text-[10px] md:text-[12px] font-semibold leading-tight">{name.split(" ").map((w) => <span key={w} className="block whitespace-nowrap md:inline md:after:content-['_']">{w}</span>)}</div><div className="hidden md:block font-mono text-[10px] leading-tight text-ink-2">{gloss}</div></div>
        ))}
        <div />
      </div>
      <div className="relative h-6" aria-hidden>
        {point ? <span className="absolute top-1 whitespace-nowrap font-mono text-[11px] text-ink -translate-x-1/2" style={{ left: `${point.x}%` }}>the readings put us here</span> : null}
        {span ? <span className="absolute top-1 whitespace-nowrap font-mono text-[11px] text-ink" style={{ left: `${span.from}%` }}>the readings put us in this half</span> : null}
      </div>
    </Figure>
  );
}
