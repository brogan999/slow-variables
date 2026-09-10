"use client";

import { CartesianGrid, Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Point } from "@/lib/data";
import { fmt as fmtUnit, tick } from "@/lib/format";

type Rule = { periods: number; dead_band: number; higher_is: string; rationale: string };

// Direction indicators: the trend over the rule's window with the dead band drawn around the window's first point,
// so the reader sees whether the move cleared it. Older points are drawn faint for context.
export function DirectionChart({ points, unit, rule }: { points: Point[]; unit: string; rule: Rule }) {
  const pts = points.filter((p) => p.value !== null).map((p) => ({ t: Date.parse(p.as_of), v: p.value as number, as_of: p.as_of }));
  if (!pts.length) return <p className="text-sm text-muted">No approved observations yet.</p>;
  const window = pts.slice(-(rule.periods + 1));
  const base = window[0].v;
  const ys = pts.map((p) => p.v);
  const lo = Math.min(...ys, base - rule.dead_band), hi = Math.max(...ys, base + rule.dead_band);
  const pad = (hi - lo || Math.abs(hi) || 1) * 0.15;
  const monthYr = (t: number) => new Date(t).toLocaleDateString("en", { month: "short", year: "2-digit", timeZone: "UTC" });
  return (
    <div className="w-full">
    <div className="h-72 w-full" role="img" aria-label={`${unit} over time with the direction rule's dead band`}>
      <ResponsiveContainer>
        <LineChart data={pts} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" strokeDasharray="0" vertical={false} />
          <XAxis type="number" dataKey="t" domain={["dataMin", "dataMax"]} tickFormatter={monthYr} stroke="var(--axis)" tick={{ fill: "var(--muted)", fontSize: 11 }} />
          <YAxis type="number" dataKey="v" domain={[lo - pad, hi + pad]} tickFormatter={tick(unit)} stroke="var(--axis)" tick={{ fill: "var(--muted)", fontSize: 11 }} width={52} />
          <ReferenceArea x1={window[0].t} x2={window[window.length - 1].t} y1={base - rule.dead_band} y2={base + rule.dead_band} fill="var(--ink)" fillOpacity={0.05} label={{ value: "dead band", fill: "var(--muted)", fontSize: 11, position: "insideTopLeft" }} />
          <Tooltip cursor={{ stroke: "var(--axis)" }} content={({ payload }) => { const d = payload?.[0]?.payload as (typeof pts)[number] | undefined; return d ? <div className="rounded panel px-2 py-1 text-xs"><div>{fmtUnit(d.v, unit)}</div><div className="text-muted">{d.as_of}</div></div> : null; }} />
          <Line type="monotone" dataKey="v" stroke="var(--s1)" strokeWidth={2} dot={{ r: 3, fill: "var(--s1)" }} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
    <p className="text-xs text-muted mt-1">Direction over the last {rule.periods} periods; the band is ±{fmtUnit(rule.dead_band, unit)} around the window&apos;s first point. Higher reads {rule.higher_is.replace(/_/g, " ")}.</p>
    </div>
  );
}
