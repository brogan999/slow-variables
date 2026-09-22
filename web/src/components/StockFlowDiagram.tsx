import Link from "next/link";
import { Figure, Key } from "./Figure";
import type { Bucket, Card, Tally } from "@/lib/data";
import { words } from "@/lib/data";

type Valve = { id: string; from: string; to: string; name: string; status: string; indicator_ids: string[] };
type Props = { buckets: (Bucket & { status: string; tally?: Tally; indicators: Card[] })[]; valves: Valve[]; sources?: number };

// Five stocks stacked vertically (label sizes chosen for 375px, where the SVG scales to about 0.75), valves between them, the return arrow up the left,
// the leak out to the right into the capture lens. Valve colour = status; icon + text always.
const STROKE: Record<string, string> = {
  faster_than_normal: "var(--fast)", slower_than_normal: "var(--slow)", consistent_with_normal: "var(--ink)",
  emerging: "var(--muted)", not_yet_measurable: "var(--muted)", unmeasured: "var(--axis)", mixed: "var(--ink-2)",
};
const GLYPH: Record<string, string> = { faster_than_normal: "▲", slower_than_normal: "▼", consistent_with_normal: "●", emerging: "◐", mixed: "◐" };

const tallyText = (b: { tally?: Tally }) => (b.tally ? `${b.tally.scored} of ${b.tally.published} count` : "");
// a status glyph is decoration beside its word, so a screen reader skips it
const G = ({ s }: { s: string }) => <span aria-hidden>{GLYPH[s] ?? "○"} </span>;

// The figure card around the diagram: the SVG from a phablet up, and on a phone the same stages as a ladder of
// boxes and valves in HTML, so its text stays readable instead of shrinking with a scaled drawing.
export function StockFlowDiagram({ buckets, valves, sources }: Props) {
  const main = buckets.filter((b) => b.id !== "return_arrow").sort((a, b) => a.order - b.order);
  const v = (id: string) => valves.find((x) => x.id === id);
  const brake = buckets.flatMap((b) => b.indicators).find((c) => c.id === "safety_brake_events");
  const loops = [
    { name: "Feedback into methods", status: v("return_arrow")?.status ?? "unmeasured", href: "/buckets/return_arrow" },
    { name: "Backlash and brakes (a balancing loop)", status: brake?.status ?? "unmeasured", href: brake ? "/indicators/safety_brake_events" : undefined },
    { name: "Moving goalposts (a balancing loop)", status: "unmeasured", href: "/predictions#nk_benchmarks_false_summits" },
    { name: "Profits, to who keeps them", status: v("leak")?.status ?? "unmeasured", href: "/capture" },
  ];
  return (
    <Figure
      title="Five stages, and the flows between them"
      note="each arrow carries the status of the indicators that measure it"
      keys={<>
        {(["faster_than_normal", "consistent_with_normal", "slower_than_normal", "emerging"] as const).map((st) => (
          <Key key={st} swatch={<svg width="18" height="10" aria-hidden><line x1="0" x2="18" y1="5" y2="5" stroke={STROKE[st]} strokeWidth="2" /></svg>}>{GLYPH[st]} {words(st)}</Key>
        ))}
        <Key swatch={<svg width="18" height="10" aria-hidden><line x1="0" x2="18" y1="5" y2="5" stroke="var(--axis)" strokeWidth="2" strokeDasharray="4 3" /></svg>}>○ unmeasured</Key>
      </>}
      foot={<>
        <p>Each box is a stage the technology has to pass through, each arrow the flow from one stage to the next. On the right, two things that push back: public backlash and safety brakes, and tests that keep moving the goalposts. Down the left, what use feeds back into better methods.</p>
        {sources ? <p>The statuses rest on readings from {sources} sources; each stage&apos;s page names them, indicator by indicator, and <Link href="/sources" className="underline decoration-grid underline-offset-2 hover:text-ink">the sources page</Link> lists them all.</p> : null}
      </>}
    >
      <div className="hidden sm:flex justify-center"><Drawing buckets={buckets} valves={valves} /></div>
      <ol className="sm:hidden flex flex-col">
        {main.map((b, i) => (
          <li key={b.id} className="flex flex-col">
            <Link href={`/buckets/${b.id}`} className="block rounded-[3px] bg-surface ring-1 ring-grid px-3 py-2.5 hover:ring-ink">
              <span className="block font-sans font-semibold text-ink">{b.order}. {b.name}</span>
              <span className="block text-[13px] text-ink-2"><G s={b.status} />{words(b.status)}{b.tally ? ` · ${tallyText(b)}` : ""}</span>
            </Link>
            {i < main.length - 1 ? <ValveRow valve={v(b.valve)} /> : null}
          </li>
        ))}
      </ol>
      <ul className="sm:hidden mt-4 flex flex-col gap-1.5 text-[13px] text-ink-2">
        {loops.map((l) => {
          const body = <><span className="text-ink">{l.name}</span> · <G s={l.status} />{words(l.status)}</>;
          return <li key={l.name}>{l.href ? <Link href={l.href} className="underline decoration-grid underline-offset-2 hover:decoration-ink">{body}</Link> : body}</li>;
        })}
      </ul>
    </Figure>
  );
}

// A valve between two stages on the phone ladder: a short arrow in the status's colour, and the status in words.
function ValveRow({ valve }: { valve?: Valve }) {
  const status = valve?.status ?? "unmeasured";
  const body = <span className="text-[13px] text-ink-2"><G s={status} />{words(status)}{valve ? <span className="text-muted"> · {valve.name}</span> : null}</span>;
  const first = valve?.indicator_ids[0];
  return (
    <div className="flex items-center gap-3 py-2 pl-5">
      <svg width="10" height="30" aria-hidden className="shrink-0"><line x1="5" y1="0" x2="5" y2="24" stroke={STROKE[status] ?? "var(--axis)"} strokeWidth="1.5" strokeDasharray={status === "unmeasured" ? "4 4" : undefined} /><path d="M1,22 L5,30 L9,22 z" fill={STROKE[status] ?? "var(--axis)"} /></svg>
      {first ? <Link href={`/indicators/${first}`} className="underline decoration-grid underline-offset-2 hover:decoration-ink">{body}</Link> : body}
    </div>
  );
}

function Drawing({ buckets, valves }: Props) {
  const W = 500, BOX = 270, X0 = 84, H = 58, GAP = 58;
  const main = buckets.filter((b) => b.id !== "return_arrow").sort((a, b) => a.order - b.order);
  const ret = buckets.find((b) => b.id === "return_arrow");
  const y = (i: number) => 20 + i * (H + GAP);
  const v = (id: string) => valves.find((x) => x.id === id);
  const total = y(main.length - 1) + H + 20;
  const brake = buckets.flatMap((b) => b.indicators).find((c) => c.id === "safety_brake_events");
  return (
    <svg viewBox={`0 0 ${W} ${total}`} className="w-full max-w-2xl" aria-labelledby="sfd-title" aria-describedby="sfd-desc">
      <title id="sfd-title">Stock-and-flow diagram of AI diffusion</title>
      <desc id="sfd-desc">Five stocks with valves between them; each valve carries the status of the indicators that measure it, as an icon and a word. Two balancing loops return on the right: B1, backlash and safety brakes, carries the safety-brake indicator&apos;s status; B2, moving goalposts, is not measured yet.</desc>
      <defs>
        <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="context-stroke" />
        </marker>
      </defs>
      {main.map((b, i) => (
        <g key={b.id}>
          <Link href={`/buckets/${b.id}`}>
            <rect x={X0} y={y(i)} width={BOX} height={H} rx={4} fill="var(--surface)" stroke="var(--grid)" />
            <text x={X0 + 12} y={y(i) + 24} fontSize="20" fontFamily="var(--font-display)" fill="var(--ink)">{b.order}. {b.name}</text>
            <text x={X0 + 12} y={y(i) + 44} fontSize="14" fontFamily="var(--font-sans)" fill="var(--ink-2)">{GLYPH[b.status] ?? "○"} {words(b.status)}{b.tally ? ` · ${tallyText(b)}` : ""}</text>
          </Link>
          {i < main.length - 1 ? <ValveArrow valve={v(b.valve)} x={X0 + BOX / 2} y1={y(i) + H} y2={y(i + 1)} /> : null}
        </g>
      ))}
      {ret ? (
        <g>
          <path d={`M${X0} ${y(main.length - 1) + H / 2} H${X0 - 50} V${y(0) + H / 2} H${X0 - 4}`} fill="none"
            stroke={STROKE[v("return_arrow")?.status ?? "unmeasured"]} strokeWidth="1.5" strokeDasharray={v("return_arrow")?.status === "unmeasured" ? "4 4" : undefined} markerEnd="url(#arr)" />
          <Link href={`/buckets/return_arrow`}>
            <text x={X0 - 58} y={(y(0) + y(main.length - 1)) / 2 + 20} fontSize="13" fontFamily="var(--font-mono)" fill="var(--ink)" transform={`rotate(-90 ${X0 - 58} ${(y(0) + y(main.length - 1)) / 2 + 20})`} textAnchor="middle">
              5. Feedback into methods · {words(v("return_arrow")?.status)}
            </text>
          </Link>
        </g>
      ) : null}
      {/* balancing loops on the right: B1 brakes (adoption back to methods), B2 goalposts (products back to methods); nested so nothing crosses */}
      <Loop d={`M${X0 + BOX} ${y(2) + 18} H470 V${y(0) + 14} H${X0 + BOX + 4}`} status={brake?.status ?? "unmeasured"} x={X0 + BOX + 8} y={y(2) + 36} name="Backlash and brakes" href={brake ? "/indicators/safety_brake_events" : undefined} />
      <Loop d={`M${X0 + BOX} ${y(1) + 18} H430 V${y(0) + 40} H${X0 + BOX + 4}`} status="unmeasured" x={X0 + BOX + 8} y={y(1) + 34} name="Moving goalposts" href="/predictions#nk_benchmarks_false_summits" />
      <g>
        <path d={`M${X0 + BOX} ${y(main.length - 1) + H / 2} H${X0 + BOX + 44}`} fill="none" stroke={STROKE[v("leak")?.status ?? "unmeasured"]} strokeWidth="2" strokeDasharray={(v("leak")?.status ?? "unmeasured") === "unmeasured" ? "4 4" : undefined} markerEnd="url(#arr)" />
        <Link href="/capture">
          <text x={X0 + BOX + 50} y={y(main.length - 1) + H / 2 - 6} fontSize="15" fontFamily="var(--font-display)" fill="var(--ink)">Profits →</text>
          <text x={X0 + BOX + 50} y={y(main.length - 1) + H / 2 + 11} fontSize="12" fontFamily="var(--font-sans)" fill="var(--ink-2)">who keeps it</text>
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
      <line x1={x} y1={y1 + 2} x2={x} y2={y2 - 3} stroke={stroke} strokeWidth="1.5" strokeDasharray={status === "unmeasured" ? "4 4" : undefined} markerEnd="url(#arr)" />
      <text x={x + 10} y={(y1 + y2) / 2 + 5} fontSize="14" fontFamily="var(--font-sans)" fill="var(--ink-2)">{label}</text>
    </g>
  );
  const first = valve?.indicator_ids[0];
  return first ? <Link href={`/indicators/${first}`}>{inner}</Link> : inner;
}

function Loop({ d, status, x, y, name, href }: { d: string; status: string; x: number; y: number; name: string; href?: string }) {
  const inner = (
    <g>
      <path d={d} fill="none" stroke={STROKE[status] ?? "var(--axis)"} strokeWidth="1.5" strokeDasharray={status === "unmeasured" ? "4 4" : undefined} markerEnd="url(#arr)" />
      <text x={x} y={y} fontSize="13" fontFamily="var(--font-sans)" fill="var(--ink-2)">{name}</text>
      <text x={x} y={y + 16} fontSize="13" fontFamily="var(--font-sans)" fill="var(--ink-2)">{GLYPH[status] ?? "○"} {words(status)}</text>
    </g>
  );
  return href ? <Link href={href}>{inner}</Link> : inner;
}
