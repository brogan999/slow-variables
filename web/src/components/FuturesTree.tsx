import type { CSSProperties } from "react";
import Link from "next/link";
import type { FuTree, FuTreeNode } from "@/lib/data";
import { fmt } from "@/lib/format";
import { link } from "./FuturesParts";
import { FuturesTreeTally } from "./FuturesTreeTally";

// who keeps the rest: solid, outlined, hatched or grey, never a hue
const SELLER: Record<string, string> = { incumbents: "bg-ink", anyone: "ft-open", maker: "hatch text-ink", permit: "bg-axis" };
const STEPS = [1, 2, 3];
const h4 = "text-[10.5px] font-semibold uppercase tracking-[0.1em] text-muted";

// A node lights when every gate it needs is ticked. The export names each node's gates, so the rules are written
// from it: one selector per distinct set of gates, and the board switches with no script.
function lit(d: FuTree): string {
  const sets = Array.from(new Set(d.lanes.flatMap((l) => l.nodes).map((n) => n.needs.join(" ")))).filter(Boolean);
  const on = sets.map((s) => `.fu-tree${s.split(" ").map((g) => `:has(#ft-g-${g}:checked)`).join("")} .ft-node[data-needs="${s}"]`);
  return `${on.join(",\n")} { border-style: solid; border-color: var(--ink); color: var(--ink); background: var(--surface); }\n${on.map((s) => `${s} .ft-bar`).join(",\n")} { opacity: 1; }`;
}

function Bar({ n, className }: { n: FuTreeNode; className: string }) {
  return (
    <span className={`ft-bar flex overflow-hidden rounded-[1px] ${className}`} aria-hidden>
      {n.shares.filter((s) => s.n).map((s) => <span key={s.id} className={SELLER[s.id]} style={{ width: `${s.width}%` }} />)}
    </span>
  );
}

function Built({ n }: { n: FuTreeNode }) {
  return <span className="inline-flex gap-px" role="img" aria-label={`Today: ${n.built.word}`}>{STEPS.map((i) => <i key={i} className={`h-1.5 w-1.5 ${i <= n.built.step ? "bg-current" : "border border-current"}`} />)}</span>;
}

function Tile({ n, kind }: { n: FuTreeNode; kind: string }) {
  return (
    <a href={`#ft-${n.id}`} data-needs={n.needs.join(" ")} className="ft-node" style={{ "--ft-col": n.col } as CSSProperties}>
      <span className="font-mono text-[10px] sm:sr-only"><span className="sr-only">{kind}, </span>{n.label}</span>
      <span className="text-[11.5px] font-semibold leading-tight">{n.name}</span>
      <span className="mt-auto flex items-center gap-1.5 font-mono text-[10.5px]">
        <span className="sr-only">Waits on: {n.gate.name}. Large or vast prizes, as a model judges it: </span>{fmt(n.n, "count")}
        <Bar n={n} className="h-1.5 flex-1" />
        <Built n={n} />
      </span>
    </a>
  );
}

function Entry({ n, kind }: { n: FuTreeNode; kind: string }) {
  return (
    <article id={`ft-${n.id}`} className="grid gap-x-6 gap-y-1.5 border-t border-grid py-3 scroll-mt-24 md:grid-cols-[15rem_minmax(0,1fr)]">
      <div className="flex flex-col gap-1">
        <h4 className="text-[15px] font-semibold leading-snug">{n.name}</h4>
        <span className="font-mono text-[11px] text-ink-2">{kind} · {n.label}</span>
        <Bar n={n} className="mt-1 h-2 w-full max-w-[12rem]" />
      </div>
      <div className="flex flex-col gap-1.5 text-[13px] text-ink-2">
        <p><span className="font-medium text-ink">Large or vast prizes, as a model judges it: {fmt(n.n, "count")}.</span> By seller: {n.shares.filter((s) => s.n).map((s, i) => <span key={s.id}>{i ? "; " : ""}in {fmt(s.n, "count")}, {s.word}</span>)}.</p>
        <p><span className="font-medium text-ink">Waits on:</span> {n.gate.name}. <span className="font-medium text-ink">Today:</span> {n.built.word}.</p>
        {n.after.length ? <p><span className="font-medium text-ink">Comes after:</span> {n.after.map((a, i) => <span key={a.id}>{i ? "; " : ""}<a href={`#ft-${a.id}`} className={link}>{a.name}</a>{a.cross ? ` (${a.kind})` : ""}</span>)}.</p> : null}
        <p><span className="font-medium text-ink">In the stories:</span> {n.examples.map((x, i) => <span key={`${x.name}-${x.imagined}-${x.author}`}>{i ? " " : ""}<em>{x.name}</em> ({x.author}, {x.imagined}): {x.line}</span>)} <Link href={n.href} className={link}>All ideas of this kind</Link></p>
      </div>
    </article>
  );
}

// The board: a tick box for each gate, one row for each kind of technology, and a tile for each decade it has a prize in.
export function FuturesTree({ d }: { d: FuTree }) {
  const gates = d.gates.filter((g) => !g.open);
  const cols = { "--ft-cols": d.decades.length } as CSSProperties;
  return (
    <div className="fu-tree flex flex-col gap-8" style={cols}>
      <style>{lit(d)}</style>
      <fieldset id="ft-gates" className="flex flex-col gap-3 border-y border-grid py-3 scroll-mt-24">
        <legend className="eyebrow">Assume this has happened</legend>
        <div className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2 lg:grid-cols-3">
          {gates.map((g) => (
            <label key={g.id} className="flex items-baseline gap-2">
              <input type="checkbox" name="ft-gate" id={`ft-g-${g.id}`} className="translate-y-[1px] accent-ink" />
              <span><span className="font-medium">{g.name}.</span> <span className="text-[13px] text-ink-2">{g.says}</span></span>
            </label>
          ))}
        </div>
        <FuturesTreeTally gates={gates.map((g) => g.id)} tallies={d.tallies} nodes={d.nodes} sellers={d.sellers} />
        <noscript><p className="text-xs text-muted">Without script the tiles still light as you tick a gate; only the running count above stays where it began.</p></noscript>
        <p className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11px] text-ink-2">
          {d.sellers.map((s) => <span key={s.id}><i className={`mr-1.5 inline-block h-2.5 w-3.5 align-[-1px] ${SELLER[s.id]}`} />{s.word}</span>)}
          <span><span className="mr-1.5 inline-flex gap-px align-[1px] text-ink">{STEPS.map((i) => <i key={i} className="h-1.5 w-1.5 bg-current" />)}</span>squares filled: {d.built.map((b) => b.word).join(", then ")}</span>
          <span>each mark and count as a model judges it</span>
        </p>
      </fieldset>

      <section id="ft-board" className="flex flex-col gap-3 scroll-mt-24">
        <div className="ft-row ft-head" aria-hidden>
          {d.decades.map((k) => <span key={k.key} className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-muted" style={{ "--ft-col": k.col } as CSSProperties}>{k.label}</span>)}
        </div>
        {d.lanes.map((lane) => (
          <div key={lane.id} className="flex flex-col gap-1">
            <h3 className={h4}>{lane.name}</h3>
            <div className="ft-row">{lane.nodes.map((n) => <Tile key={n.id} n={n} kind={lane.name} />)}</div>
          </div>
        ))}
      </section>

      <section id="ft-nodes" className="flex flex-col gap-6 scroll-mt-24">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Every node</h2>
          <p className="text-sm text-ink-2 max-w-[72ch]">What the stories put in each place on the board, what it waits on, and what has to come before it. A node always comes after the one before it in its own row; a link to another kind of technology names that kind.</p>
        </div>
        {d.lanes.map((lane) => (
          <div key={lane.id}>
            <header className="border-b-2 border-ink pb-1.5"><h3 className="text-lg font-bold tracking-tight">{lane.name}</h3></header>
            {lane.nodes.map((n) => <Entry key={n.id} n={n} kind={lane.name} />)}
          </div>
        ))}
      </section>
      <p className="text-xs text-muted max-w-[72ch]">A model&apos;s judgement, not a reading. Every count on this page counts the site&apos;s judgement of profit, made by a model for each idea as if it worked the way its story promises. Each node&apos;s name, how far along it is today and the links between kinds of technology were made {d.made_by.date} by Claude, a model made by Anthropic ({d.made_by.model}). {d.made_by.method} Reviewed by {d.made_by.reviewed_by}. No status, metric or answer on the site reads this page.</p>
    </div>
  );
}
