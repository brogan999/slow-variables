// Number formatting shared by server and client components (no node imports here).
const sig = (v: number) => (Math.abs(v) >= 100 ? v.toFixed(0) : Math.abs(v) >= 10 ? v.toFixed(1) : v.toFixed(2));

export function fmt(v: number | null | undefined, unit?: string): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  switch (unit) {
    case "share": return `${(v * 100).toFixed(1)}%`;
    case "pct": case "pct_change_yoy": case "pct_change_qoq_saar": return `${v.toFixed(1)}%`;
    case "USD": case "usd": {
      const a = Math.abs(v);
      const [d, s] = a >= 1e12 ? [v / 1e12, "T"] : a >= 1e9 ? [v / 1e9, "B"] : a >= 1e6 ? [v / 1e6, "M"] : a >= 1e3 ? [v / 1e3, "k"] : [v, ""];
      return `$${s ? (Math.abs(d) >= 100 ? d.toFixed(0) : d.toFixed(1)) : sig(d)}${s}`;
    }
    case "ratio": return `${sig(v)}×`;
    case "minutes": return v >= 60 ? `${(v / 60).toFixed(1)} h` : `${sig(v)} min`;
    case "days": return `${v.toFixed(0)} days`;
    case "count": return v.toFixed(0);
    default: return unit ? `${sig(v)} ${unit}` : sig(v);
  }
}

export const tick = (unit: string) => (v: number) => {
  if (unit === "share") return `${Math.round(v * 100)}%`;
  if (unit === "USD" || unit === "usd") return fmt(v, unit);
  if (unit === "minutes") return v >= 60 ? `${Math.round(v / 60)}h` : `${sig(v)}m`;
  return sig(v);
};

export const words = (s: string | null | undefined) => (s ?? "unmeasured").replace(/_/g, " ");

// Mode of the scored statuses; emerging and not-yet-measurable never outvote a scored reading (matches store._summarise).
const UNSCORED = new Set(["emerging", "not_yet_measurable", "not_yet_testable"]);
export function summarise(statuses: (string | null | undefined)[]): string | null {
  const all = statuses.filter((s): s is string => !!s);
  if (!all.length) return null;
  const scored = all.filter((s) => !UNSCORED.has(s));
  const pool = scored.length ? scored : all;
  const counts = [...new Set(pool)].map((s) => [pool.filter((x) => x === s).length, s] as const).sort((a, b) => b[0] - a[0]);
  if (counts.length > 1 && counts[0][0] === counts[1][0]) return scored.length ? "mixed" : counts[0][1];
  return counts[0][1];
}
