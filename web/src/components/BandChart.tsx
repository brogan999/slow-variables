"use client";

import { CartesianGrid, ErrorBar, Legend, ReferenceArea, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import type { Band, Point } from "@/lib/data";
import { fmt as fmtUnit, tick } from "@/lib/format";

type Series = { name: string; points: Point[] };
type Props = { series: Series[]; unit: string; log?: boolean; bands?: { normal: Band; fast: Band } | null };

const COLORS = ["var(--s1)", "var(--s2)"];
const yr = (t: number) => new Date(t).getUTCFullYear().toString();

export function BandChart({ series, unit, log, bands }: Props) {
  const data = series.map((s) => s.points.filter((p) => p.value !== null).map((p) => ({
    t: Date.parse(p.as_of), v: p.value as number, subject: p.subject ?? p.dims?.model ?? "", disputed: !!p.disputed,
    err: p.low != null && p.high != null ? [(p.value as number) - p.low, p.high - (p.value as number)] : undefined, as_of: p.as_of,
  })));
  const all = data.flat();
  if (!all.length) return <p className="text-sm text-muted">No approved observations yet.</p>;
  const ys = all.map((d) => d.v);
  const domain: [number, number] = log ? [Math.min(...ys) / 2, Math.max(...ys) * 2] : [0, Math.max(...ys) * 1.15];
  return (
    <div className="h-72 w-full" role="img" aria-label={`${series.map((s) => s.name).join(" and ")} over time, ${unit}`}>
      <ResponsiveContainer>
        <ScatterChart margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" strokeDasharray="0" vertical={false} />
          <XAxis type="number" dataKey="t" domain={["dataMin", "dataMax"]} tickFormatter={yr} stroke="var(--axis)" tick={{ fill: "var(--muted)", fontSize: 11 }} />
          <YAxis type="number" dataKey="v" scale={log ? "log" : "linear"} domain={domain} tickFormatter={tick(unit)} stroke="var(--axis)"
            tick={{ fill: "var(--muted)", fontSize: 11 }} width={48} label={{ value: unit, angle: -90, position: "insideLeft", fill: "var(--muted)", fontSize: 11 }} />
          {bands?.normal ? <ReferenceArea y1={bands.normal.lo ?? undefined} y2={bands.normal.hi ?? undefined} fill="var(--ink)" fillOpacity={0.04} label={{ value: "normal", fill: "var(--muted)", fontSize: 11, position: "insideTopRight" }} /> : null}
          {bands?.fast ? <ReferenceArea y1={bands.fast.lo ?? undefined} y2={bands.fast.hi ?? undefined} fill="var(--fast)" fillOpacity={0.08} label={{ value: "fast", fill: "var(--fast)", fontSize: 11, position: "insideBottomRight" }} /> : null}
          <Tooltip cursor={{ stroke: "var(--axis)" }} content={({ payload }) => {
            const d = payload?.[0]?.payload as (typeof all)[number] | undefined;
            if (!d) return null;
            return (
              <div className="rounded bg-surface ring-hair px-2 py-1 text-xs">
                <div className="font-medium">{d.subject}</div>
                <div>{fmtUnit(d.v, unit)}{d.err ? ` (${fmtUnit(d.v - d.err[0], unit)}–${fmtUnit(d.v + d.err[1], unit)})` : ""}</div>
                <div className="text-muted">{d.as_of}{d.disputed ? " · disputed" : ""}</div>
              </div>
            );
          }} />
          {series.length > 1 ? <Legend wrapperStyle={{ fontSize: 12 }} /> : null}
          {data.map((d, i) => (
            <Scatter key={series[i].name} name={series[i].name} data={d} fill={COLORS[i % COLORS.length]} fillOpacity={0.9}
              shape={(p: { cx?: number; cy?: number; payload?: { disputed: boolean } }) => (
                <circle cx={p.cx} cy={p.cy} r={4.5} fill={p.payload?.disputed ? "var(--surface)" : COLORS[i % COLORS.length]}
                  stroke={COLORS[i % COLORS.length]} strokeWidth={2} />
              )}>
              <ErrorBar dataKey="err" direction="y" width={3} stroke={COLORS[i % COLORS.length]} strokeOpacity={0.5} />
            </Scatter>
          ))}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
