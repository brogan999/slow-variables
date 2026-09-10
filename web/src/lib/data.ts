import fs from "node:fs";
import path from "node:path";

// The web never computes a number: every JSON here was written by `ai-tracker export`.
const ROOT = path.join(process.cwd(), "data");

export type Point = {
  as_of: string; value: number | null; low?: number | null; high?: number | null; obs_ids: string[];
  subject?: string; unit?: string; disputed?: boolean; grade?: string; dims?: Record<string, string>; series_key?: string;
};
export type Card = {
  unpublished_reason?: string | null;
  id: string; name: string; bucket_id: string | null; layer_id: string | null; valve_measured: string | null;
  unit: string; published: boolean; status: string | null; confidence: number | null; leading_lagging: string | null;
  grade: string | null; latest: Point | null; sparkline: Point[]; stale_as_of: string | null; stale_reason?: string | null; n_observations: number;
};
export type StatusEvent = {
  id: string; target_type?: "indicator" | "prediction"; target_id: string; old_status: string | null; new_status: string; old_conf: number | null; new_conf: number;
  reason: string; evidence_ids: string[]; author: string; created_at: string;
};
export type Band = { lo?: number | null; hi?: number | null } | null;
export type Evidence = { id: string; target: string; stance: "for" | "against" | "context"; as_of: string; summary: string; url: string; tier: number; source_id: string; snippet: string; entity_id: string | null };
export type IndicatorDoc = Card & {
  definition: string; why_it_matters: string; proxy_types: string[]; cadence_expected: string; tracker_interpretation: string;
  counterevidence: string; series_keys: string[]; metric: string | null; band_input: string | null;
  normal_band: Band; fast_band: Band; falsifying_band: Band; band_rationale: string | null;
  direction_rule: { periods: number; dead_band: number; higher_is: string; rationale: string } | null;
  proposed_status: string | null; override_note: string | null; related_bottlenecks: number[]; related_indicators: string[];
  related_predictions: string[]; updated_at: string;
  series: { series_key: string; points: Point[] }[];
  derived: (Point & { metric: string; as_of_date: string; input_observation_ids: string[] })[];
  status_events: StatusEvent[]; crosswalk: Crosswalk[]; evidence: Evidence[];
};
export type Bucket = { id: string; name: string; order: number; stock: string; valve: string; speed_limit: string };
export type Layer = { id: string; name: string; order: number; description: string; dependency_tier: number | null };
export type Sublayer = { id: string; layer_id: string; name: string; order: number; description: string };
export type Crosswalk = { bucket_id: string; layer_id: string; sublayer_id: string | null; relation: string; note: string; shared_indicators: string[] };
export type Observation = Record<string, string | number | boolean | null> & { id: string; series_key: string; grade: string };
export type Source = {
  id: string; name: string; org: string; url: string; kind: string; default_tier: number; cadence: string; lens: string;
  license: string | null; attribution: string | null; last_success_at: string | null; last_error: string | null;
  items_found: number; runs: number; people: string[]; health: "ok" | "stale" | "never";
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
export type MarginShare = { value: number; as_of: string; obs_ids: string[] };
export const capture = () => read<{ as_of: string; layers: (Layer & { indicators: Card[] })[]; recent_status_events: StatusEvent[]; margin_shares: Record<string, MarginShare>; margin_stack_series: { as_of: string; layer_id: string | null; value: number; obs_ids: string[] }[] }>("lens/capture.json");
export const sources = () => read<Source[]>("sources.json");
export const changelog = () => read<StatusEvent[]>("changelog.json");
export const meta = () => read<{ generated_at: string }>("meta.json");

export { fmt, words } from "./format";
export const obsIndex = () => read<Record<string, string>>("obs_index.json");
export type Fit = { metric: string; value: number; value_low: number | null; value_high: number | null; as_of_date: string; dims: Record<string, string>; obs_ids: string[] };
export type Doc = IndicatorDoc & { points: Point[]; band_value: { value: number; as_of: string | null; obs_ids: string[]; low: number | null; high: number | null } | null; fits: Fit[]; related_metrics: string[] };
export type Prediction = {
  id: string; ledger: "nk" | "lab" | "ai2027" | "capture"; claimant: string; claim_text: string; claim_url: string | null; claim_date: string;
  window_start: string | null; window_end: string | null; operationalisation: string; related_indicators: string[]; proxy_types: string[];
  confidence: number; counterevidence: string; note: string | null; published: boolean; status: string | null; confidence_now: number | null;
  status_events: StatusEvent[]; evidence: Evidence[];
};
export const predictions = () => read<Prediction[]>("predictions.json");
export type LedgerRow = Observation & { parties: string[]; instrument: string; obs_id: string; as_of_date: string; published_date: string; value_numeric: number | null; value_text: string | null; unit: string; tier: number; source_id: string; url: string; disputed: boolean; dispute_text: string | null; raw_snippet: string };
export const ledger = () => read<LedgerRow[]>("ledger.json");
export type ThesisVerdict = { id: string; name: string; holds: boolean | null; logic: string; conds: { text: string; holds: boolean | null; obs_ids: string[]; detail: string }[] };
export const thesis = () => read<ThesisVerdict[]>("thesis.json");
export type Bottleneck = { id: number; title: string; text: string; section: string; bucket_id: string; source_codes: string[]; related_indicators: string[]; related: { id: string; name: string; status: string | null; published: boolean }[] };
export type BottleneckDoc = { sections: { name: string; bucket_id: string }[]; essays: { code: string; title: string; url: string; date: string }[]; items: Bottleneck[] };
export const bottlenecks = () => read<BottleneckDoc>("bottlenecks.json");
export type CompareRow = { indicator: string; nk: string; ai2027: string; card: Card; leans: "nk" | "ai2027" | "open"; nk_predictions: { id: string; claimant: string; status: string | null }[]; ai2027_predictions: { id: string; claimant: string; status: string | null }[] };
export const compare = () => read<{ rows: CompareRow[]; tally: { nk: number; ai2027: number; open: number } }>("compare.json");
export type StackEntity = { id: string; name: string; kind: string; cik: string | null; aliases: string[]; verified: boolean; notes: string | null; founded: number | null; is_primary: boolean; from_date: string | null; to_date: string | null; latest: { series_key: string; value: number | null; value_text: string | null; unit: string; as_of: string; obs_ids: string[] } | null };
export type StackSublayer = Sublayer & { entities: StackEntity[]; indicators: Card[] };
export type StackDoc = { layers: (Layer & { sublayers: StackSublayer[] })[] };
export const stack = () => read<StackDoc>("stack.json");
export type VentureQuarter = { as_of: string; venture_dollars?: { value: number; obs_ids: string[] }; round_count?: { value: number; obs_ids: string[] } };
export type VentureDoc = { sublayer_id: string; quarters: VentureQuarter[] };
export const venture = (sublayerId: string): VentureDoc | null => { try { return read<VentureDoc>(`venture/${sublayerId}.json`); } catch { return null; } };
export type LadderRow = { obs_id: string; subject: string; entity_id: string | null; as_of: string; tier: number; url: string; snippet: string };
export type LadderDoc = { current: { value: number; as_of: string; obs_ids: string[] } | null; rungs: { level: number; name: string; description: string; observables: string; production: LadderRow[]; research: LadderRow[] }[] };
export const ladder = () => read<LadderDoc>("lens/ladder.json");
