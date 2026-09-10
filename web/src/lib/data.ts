import fs from "node:fs";
import path from "node:path";

// The web never computes a number: every JSON here was written by `ai-tracker export`.
const ROOT = path.join(process.cwd(), "data");

export type Point = {
  as_of: string; value: number | null; low?: number | null; high?: number | null; obs_ids: string[];
  subject?: string; unit?: string; disputed?: boolean; grade?: string; dims?: Record<string, string>; series_key?: string;
};
export type Card = {
  id: string; name: string; bucket_id: string | null; layer_id: string | null; valve_measured: string | null;
  unit: string; published: boolean; status: string | null; confidence: number | null; leading_lagging: string | null;
  grade: string | null; latest: Point | null; sparkline: Point[]; stale_as_of: string | null; n_observations: number;
};
export type StatusEvent = {
  id: string; target_id: string; old_status: string | null; new_status: string; old_conf: number | null; new_conf: number;
  reason: string; evidence_ids: string[]; author: string; created_at: string;
};
export type Band = { lo?: number | null; hi?: number | null } | null;
export type IndicatorDoc = Card & {
  definition: string; why_it_matters: string; proxy_types: string[]; cadence_expected: string; tracker_interpretation: string;
  counterevidence: string; series_keys: string[]; metric: string | null; band_input: string | null;
  normal_band: Band; fast_band: Band; falsifying_band: Band; band_rationale: string | null;
  direction_rule: { periods: number; dead_band: number; higher_is: string; rationale: string } | null;
  proposed_status: string | null; override_note: string | null; related_bottlenecks: number[]; related_indicators: string[];
  related_predictions: string[]; updated_at: string;
  series: { series_key: string; points: Point[] }[];
  derived: (Point & { metric: string; as_of_date: string; input_observation_ids: string[] })[];
  status_events: StatusEvent[]; crosswalk: Crosswalk[];
};
export type Bucket = { id: string; name: string; order: number; stock: string; valve: string; speed_limit: string };
export type Layer = { id: string; name: string; order: number; description: string; dependency_tier: number | null };
export type Sublayer = { id: string; layer_id: string; name: string; order: number; description: string };
export type Crosswalk = { bucket_id: string; layer_id: string; sublayer_id: string | null; relation: string; note: string; shared_indicators: string[] };
export type Observation = Record<string, string | number | boolean | null> & { id: string; series_key: string; grade: string };
export type Source = {
  id: string; name: string; org: string; url: string; kind: string; default_tier: number; cadence: string; lens: string;
  license: string | null; attribution: string | null; last_success_at: string | null; last_error: string | null;
  items_found: number; runs: number; people: string[];
};

function read<T>(rel: string): T {
  return JSON.parse(fs.readFileSync(path.join(ROOT, rel), "utf8")) as T;
}
export const index = () => read<{ indicators: Card[]; buckets: Bucket[]; layers: Layer[]; sublayers: Sublayer[]; crosswalk: Crosswalk[] }>("index.json");
export const indicator = (id: string) => read<Doc>(`indicators/${id}.json`);
export const bucket = (id: string) => read<Bucket & { indicators: Card[]; crosswalk: Crosswalk[] }>(`buckets/${id}.json`);
export const layer = (id: string) => read<Layer & { indicators: Card[]; sublayers: Sublayer[]; crosswalk: Crosswalk[] }>(`layers/${id}.json`);
export const series = (key: string) => read<{ series_key: string; unit: string; source: Source | null; observations: Observation[] }>(`series/${key}.json`);
export const seriesKeys = () => fs.readdirSync(path.join(ROOT, "series")).map((f) => f.replace(/\.json$/, ""));
export const diffusion = () => read<{
  as_of: string; verdict: string; buckets: (Bucket & { indicators: Card[]; status: string })[];
  valves: { id: string; from: string; to: string; name: string; status: string; indicator_ids: string[] }[];
  recent_status_events: StatusEvent[]; what_would_change: string[];
}>("lens/diffusion.json");
export const capture = () => read<{ as_of: string; layers: (Layer & { indicators: Card[] })[]; recent_status_events: StatusEvent[] }>("lens/capture.json");
export const sources = () => read<Source[]>("sources.json");
export const changelog = () => read<StatusEvent[]>("changelog.json");
export const meta = () => read<{ generated_at: string }>("meta.json");

export { fmt, words } from "./format";
export const obsIndex = () => read<Record<string, string>>("obs_index.json");
export type Doc = IndicatorDoc & { points: Point[]; band_value: { value: number; as_of: string | null; obs_ids: string[] } | null };
