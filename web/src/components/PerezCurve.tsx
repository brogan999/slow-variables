import { Fact } from "@/components/Fact";
import type { ArgumentDoc } from "@/lib/data";

// Perez's two halves as a schematic; the only data on it is which region the published phase rule picks.
// the centre of each region, on the curve: a phase, never a precise position
const MARK = { installation: [170, 141], turning_point: [336, 148], deployment: [520, 58] } as const;
const WORD = { installation: "installation", turning_point: "a turning point", deployment: "deployment", untestable: "untestable" } as const;

function Curve({ phase, compact }: { phase: ArgumentDoc["phase"]; compact: boolean }) {
  const mark = phase.state !== "untestable" ? MARK[phase.state] : null;
  const big = compact ? 34 : 19, small = compact ? 22 : 11.5;
  return (
    <svg viewBox="0 0 660 250" className={`w-full h-auto ${compact ? "sm:hidden" : "hidden sm:block"}`} role="img" aria-label={`Schematic of Carlota Perez's installation and deployment periods; the tracker's phase rule reads ${WORD[phase.state]}`}>
      <rect x="300" y="18" width="72" height="194" fill="var(--surface-2)" opacity="0.7" />
      <line x1="40" y1="212" x2="640" y2="212" stroke="var(--axis)" strokeWidth={compact ? 2 : 1} />
      <path d="M40,206 C120,200 150,150 200,120 C240,96 268,86 300,120 C326,148 340,168 370,150 C420,120 470,80 520,58 C560,42 600,34 636,30" fill="none" stroke="var(--ink)" strokeWidth={compact ? 3.5 : 2} />
      <text x="50" y={compact ? 48 : 40} className="font-serif" fontSize={big} fill="var(--ink)">Installation</text>
      {compact ? null : <text x="60" y="60" className="font-mono" fontSize={small} fill="var(--ink-2)">finance leads · gains concentrate</text>}
      <text x="336" y={compact ? 244 : 236} textAnchor="middle" className="font-mono" fontSize={small} fill="var(--ink-2)">turning point</text>
      <text x={compact ? 420 : 430} y={170} className="font-serif" fontSize={big} fill="var(--ink)">Deployment</text>
      {compact ? null : <text x="430" y="190" className="font-mono" fontSize={small} fill="var(--ink-2)">production leads · gains spread</text>}
      {mark ? (
        <g>
          <line x1={mark[0]} y1={mark[1]} x2={mark[0]} y2="212" stroke="var(--ink)" strokeDasharray="2 3" strokeWidth={compact ? 2 : 1} />
          <circle cx={mark[0]} cy={mark[1]} r={compact ? 14 : 9} fill="none" stroke="var(--gild)" strokeWidth={compact ? 3 : 2} />
          <circle cx={mark[0]} cy={mark[1]} r={compact ? 7 : 4.5} fill="var(--ink)" />
          <text x={mark[0]} y={mark[1] - (compact ? 26 : 18)} textAnchor="middle" className="font-mono" fontSize={small} fill="var(--ink)">{compact ? "we are here" : "the readings put us here"}</text>
        </g>
      ) : null}
    </svg>
  );
}

export function PerezCurve({ phase, facts }: { phase: ArgumentDoc["phase"]; facts: ArgumentDoc["facts"] }) {
  return (
    <figure className="plate">
      <Curve phase={phase} compact={false} />
      <Curve phase={phase} compact />
      <figcaption className="mt-4 text-sm text-ink-2 leading-relaxed">
        Schematic, after Perez (2002): the curve is her shape, not our data. The marker is placed by a published rule, using spending on buildings and equipment at <Fact f={facts.capex_to_revenue} /> the AI revenue we can measure, and <Fact f={facts.vendor_financing_4q} /> of commitments signed in four quarters in deals where the seller also funds the buyer. {phase.state === "untestable" ? "One of those series has no reading, so no position is shown." : `By that rule this is ${WORD[phase.state]}.`}
        <details className="mt-2"><summary className="cursor-pointer text-ink-2 hover:text-ink">The rule</summary><p className="mt-1">{phase.rule}</p></details>
      </figcaption>
    </figure>
  );
}
