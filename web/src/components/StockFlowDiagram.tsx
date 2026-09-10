import Link from "next/link";
import type { Bucket, Card } from "@/lib/data";
import { words } from "@/lib/data";

type Valve = { id: string; from: string; to: string; name: string; status: string; indicator_ids: string[] };
type Props = { buckets: (Bucket & { status: string; indicators: Card[] })[]; valves: Valve[] };

// Five stocks stacked vertically (legible at 390px), valves between them, the return arrow up the left,
// the leak out to the right into the capture lens. Valve colour = status; icon + text always.
const STROKE: Record<string, string> = {
  faster_than_normal: "var(--fast)", slower_than_normal: "var(--slow)", consistent_with_normal: "var(--ink)",
  emerging: "var(--muted)", not_yet_measurable: "var(--muted)", unmeasured: "var(--axis)", mixed: "var(--ink-2)",
};
const GLYPH: Record<string, string> = { faster_than_normal: "▲", slower_than_normal: "▼", consistent_with_normal: "●", emerging: "◐", mixed: "◐" };

export function StockFlowDiagram({ buckets, valves }: Props) {
  const W = 500, BOX = 270, X0 = 84, H = 58, GAP = 58;
  const main = buckets.filter((b) => b.id !== "return_arrow").sort((a, b) => a.order - b.order);
  const ret = buckets.find((b) => b.id === "return_arrow");
  const y = (i: number) => 20 + i * (H + GAP);
  const v = (id: string) => valves.find((x) => x.id === id);
  const total = y(main.length - 1) + H + 20;
  return (
    <svg viewBox={`0 0 ${W} ${total}`} className="w-full max-w-2xl" role="img" aria-label="Stock-and-flow diagram of AI diffusion: five stocks, valves coloured by status">
      <defs>
        <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="context-stroke" />
        </marker>
      </defs>
      {main.map((b, i) => (
        <g key={b.id}>
          <Link href={`/buckets/${b.id}`}>
            <rect x={X0} y={y(i)} width={BOX} height={H} rx={6} fill="var(--surface)" stroke="var(--axis)" />
            <text x={X0 + 12} y={y(i) + 24} fontSize="16" fontWeight="600" fill="var(--ink)">{b.order}. {b.name}</text>
            <text x={X0 + 12} y={y(i) + 44} fontSize="13" fill="var(--ink-2)">{GLYPH[b.status] ?? "○"} {words(b.status)} · {b.indicators.length} indicator{b.indicators.length === 1 ? "" : "s"}</text>
          </Link>
          {i < main.length - 1 ? <ValveArrow valve={v(b.valve)} x={X0 + BOX / 2} y1={y(i) + H} y2={y(i + 1)} /> : null}
        </g>
      ))}
      {ret ? (
        <g>
          <path d={`M${X0} ${y(main.length - 1) + H / 2} H${X0 - 50} V${y(0) + H / 2} H${X0 - 4}`} fill="none"
            stroke={STROKE[v("return_arrow")?.status ?? "unmeasured"]} strokeWidth="2" strokeDasharray={v("return_arrow")?.status === "unmeasured" ? "4 4" : undefined} markerEnd="url(#arr)" />
          <Link href={`/buckets/return_arrow`}>
            <text x={X0 - 58} y={(y(0) + y(main.length - 1)) / 2 + 20} fontSize="13" fill="var(--ink)" transform={`rotate(-90 ${X0 - 58} ${(y(0) + y(main.length - 1)) / 2 + 20})`} textAnchor="middle">
              5. Return arrow · {words(v("return_arrow")?.status)}
            </text>
          </Link>
        </g>
      ) : null}
      <g>
        <path d={`M${X0 + BOX} ${y(main.length - 1) + H / 2} H${X0 + BOX + 44}`} fill="none" stroke={STROKE[v("leak")?.status ?? "unmeasured"]} strokeWidth="2" strokeDasharray="4 4" markerEnd="url(#arr)" />
        <Link href="/capture">
          <text x={X0 + BOX + 50} y={y(main.length - 1) + H / 2 - 6} fontSize="13" fill="var(--ink)">Leak →</text>
          <text x={X0 + BOX + 50} y={y(main.length - 1) + H / 2 + 11} fontSize="12" fill="var(--ink-2)">who keeps it</text>
        </Link>
      </g>
    </svg>
  );
}

function ValveArrow({ valve, x, y1, y2 }: { valve?: Valve; x: number; y1: number; y2: number }) {
  const status = valve?.status ?? "unmeasured";
  const stroke = STROKE[status] ?? "var(--axis)";
  const label = `${GLYPH[status] ?? "○"} ${words(status)}`;
  const inner = (
    <g>
      <line x1={x} y1={y1 + 2} x2={x} y2={y2 - 3} stroke={stroke} strokeWidth="2" strokeDasharray={status === "unmeasured" ? "4 4" : undefined} markerEnd="url(#arr)" />
      <text x={x + 10} y={(y1 + y2) / 2 + 4} fontSize="13" fill="var(--ink-2)">{label}</text>
    </g>
  );
  const first = valve?.indicator_ids[0];
  return first ? <Link href={`/indicators/${first}`}>{inner}</Link> : inner;
}
