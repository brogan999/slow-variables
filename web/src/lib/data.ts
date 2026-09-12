import fs from "node:fs";
import path from "node:path";

// The web never computes a number: every JSON here was written by `ai-tracker export`.
const ROOT = path.join(process.cwd(), "data");

export type Point = {
  as_of: string; value: number | null; low?: number | null; high?: number | null; obs_ids: string[];
  subject?: string; unit?: string; disputed?: boolean; grade?: string; dims?: Record<string, string>; series_key?: string;
  flags?: string[]; dispute_text?: string | null;
};
export type Card = {
  unpublished_reason?: string | null; answers?: string[];
  id: string; name: string; bucket_id: string | null; layer_id: string | null; valve_measured: string | null;
  unit: string; published: boolean; status: string | null; confidence: number | null; leading_lagging: string | null;
  grade: string | null; latest: Point | null; sparkline: Point[]; stale_as_of: string | null; stale_reason?: string | null; n_observations: number;
  pending?: { new_status: string; since: string } | null;
};
export type StatusEvent = {
  id: string; target_type?: "indicator" | "prediction"; target_id: string; old_status: string | null; new_status: string; old_conf: number | null; new_conf: number;
  reason: string; evidence_ids: string[]; author: string; created_at: string; counterevidence_considered?: string | null;
};
export type Band = { lo?: number | null; hi?: number | null } | null;
export type Evidence = { id: string; target: string; stance: "for" | "against" | "context"; as_of: string; summary: string; url: string; tier: number; grade: string; source_id: string; snippet: string; entity_id: string | null };
export type IndicatorDoc = Card & {
  definition: string; why_it_matters: string; proxy_types: string[]; cadence_expected: string; tracker_interpretation: string;
  counterevidence: string; series_keys: string[]; metric: string | null; band_input: string | null;
  normal_band: Band; fast_band: Band; falsifying_band: Band; band_rationale: string | null;
  direction_rule: { periods: number; dead_band: number; higher_is: string; rationale: string } | null;
  proposed_status: string | null; override_note: string | null; timing_rationale?: string | null; related_bottlenecks: number[]; related_indicators: string[];
  related_predictions: string[]; updated_at: string;
  series: { series_key: string; points: Point[] }[];
  derived: (Point & { metric: string; as_of_date: string; input_observation_ids: string[] })[];
  status_events: StatusEvent[]; crosswalk: Crosswalk[]; evidence: Evidence[];
};
export type Bucket = { id: string; name: string; order: number; stock: string; valve: string; speed_limit: string };
export type Tally = { scored: number; published: number; margin: number; only: string | null };
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
export const layer = (id: string) => read<Layer & { tally?: Tally; indicators: Card[]; sublayers: Sublayer[]; crosswalk: Crosswalk[]; venture: LayerVenture | null; commoditisation: { proxies: { id: string; name: string; status: string | null }[]; line: string } | null }>(`layers/${id}.json`);
export const series = (key: string) => read<{ series_key: string; unit: string; source: Source | null; observations: Observation[]; withdrawn: Observation[] }>(`series/${key}.json`);
export const seriesKeys = () => fs.readdirSync(path.join(ROOT, "series")).map((f) => f.replace(/\.json$/, ""));
export const diffusion = () => read<{
  as_of: string; verdict: string; buckets: (Bucket & { indicators: Card[]; status: string; tally: Tally })[];
  valves: { id: string; from: string; to: string; name: string; status: string; tally: Tally; indicator_ids: string[] }[];
  recent_status_events: StatusEvent[]; what_would_change: string[];
}>("lens/diffusion.json");
export type ChartSourcesT = { metric: string | null; sources: { id: string; name: string; org: string; license: string | null; attribution: string | null }[] };
export type StackPart = { label: string; value: number; estimated: boolean; grade: string | null; href: string; obs_ids: string[] };
export type StackBar = { value: number; as_of: string; estimated: boolean; parts: StackPart[]; obs_ids: string[] };
export type StackRow = { as_of: string; layer_id: string | null; basis?: string; value: number; obs_ids: string[] };
export const capture = () => read<{ as_of: string; verdict?: string; what_would_change: string[]; layers: (Layer & { indicators: Card[]; status: string; tally: Tally; venture: LayerVenture | null; reading: string })[]; recent_status_events: StatusEvent[]; stack_bars: Record<string, StackBar>; gross_profit_stack_series: StackRow[]; margin_stack_series: StackRow[]; gross_profit_stack_sources: ChartSourcesT; margin_stack_sources: ChartSourcesT }>("lens/capture.json");
export const sources = () => read<Source[]>("sources.json");
export type Skipped = { id: string; name: string; url: string | null; reason: string; attribution: string | null; people?: string[] };
export const skippedSources = () => read<Skipped[]>("skipped_sources.json");
export const changelog = () => read<StatusEvent[]>("changelog.json");
export const meta = () => read<{ generated_at: string; observations: number; indicators_published: number; sources: number }>("meta.json");

export { fmt, words } from "./format";
export const obsIndex = () => read<Record<string, string>>("obs_index.json");
export type Fit = { metric: string; value: number; value_low: number | null; value_high: number | null; as_of_date: string; dims: Record<string, string>; obs_ids: string[] };
export type Doc = IndicatorDoc & { chart_sources?: ChartSourcesT; confidence_basis?: { grade: string | null; best_tier: number | null; sources: string[]; n_observations: number; stale_as_of: string | null }; prediction_rows?: { id: string; claimant: string; ledger: string; status: string | null }[]; points: Point[]; band_value: { value: number; as_of: string | null; obs_ids: string[]; low: number | null; high: number | null } | null; fits: Fit[]; related_metrics: string[] };
export type Prediction = { direction_assessment?: string | null; magnitude_assessment?: string | null; timing_assessment?: string | null;
  id: string; ledger: "nk" | "lab" | "ai2027" | "capture"; claimant: string; claim_text: string; claim_url: string | null; claim_date: string;
  window_start: string | null; window_end: string | null; operationalisation: string; related_indicators: string[]; proxy_types: string[];
  confidence: number; counterevidence: string; note: string | null; published: boolean; status: string | null; confidence_now: number | null;
  status_events: StatusEvent[]; evidence: Evidence[];
};
export const predictions = () => read<Prediction[]>("predictions.json");
export type LedgerRow = Observation & { parties: { slug: string; entity_id: string | null; name: string; href: string | null }[]; instrument: string; obs_id: string; as_of_date: string; published_date: string; value_numeric: number | null; value_text: string | null; unit: string; tier: number; source_id: string; url: string; disputed: boolean; dispute_text: string | null; raw_snippet: string };
export const ledger = () => read<LedgerRow[]>("ledger.json");
export type ThesisVerdict = { id: string; name: string; holds: boolean | null; logic: string; conds: { text: string; holds: boolean | null; obs_ids: string[]; detail: string }[] };
export const thesis = () => read<ThesisVerdict[]>("thesis.json");
export type Bottleneck = { id: number; title: string; text: string; section: string; bucket_id: string; source_codes: string[]; related_indicators: string[]; domain?: string | null; domain_basis?: string | null; related: { id: string; name: string; status: string | null; published: boolean }[] };
export type BottleneckDoc = { sections: { name: string; bucket_id: string }[]; essays: { code: string; title: string; url: string; date: string }[]; items: Bottleneck[]; summary: { name: string; items: number; watched: number; fast: number; normal: number; other: number }[]; domains: string[]; grid: { name: string; cells: Record<string, number[]> }[] };
export const bottlenecks = () => read<BottleneckDoc>("bottlenecks.json");
export type ComparePred = { id: string; claimant: string; status: string | null };
export type CompareRow = { indicator: string; card: Card; leans: "nk" | "ai2027" | "open" | null; columns: Record<"nk" | "ai2027" | "lab" | "capture", { text: string; predictions: ComparePred[] }> };
export const compare = () => read<{ rows: CompareRow[]; tally: { nk: number; ai2027: number; open: number } }>("compare.json");
export type StackEntity = { id: string; name: string; kind: string; cik: string | null; aliases: string[]; verified: boolean; notes: string | null; founded: number | null; is_primary: boolean; from_date: string | null; to_date: string | null; latest: { series_key: string; value: number | null; value_text: string | null; unit: string; as_of: string; obs_ids: string[] } | null };
export type StackSublayer = Sublayer & { entities: StackEntity[]; indicators: Card[] };
export type StackDoc = { layers: (Layer & { sublayers: StackSublayer[] })[] };
export const stack = () => read<StackDoc>("stack.json");
export type Analysis = {
  id: string; name: string; question: string; metric: string; dims?: Record<string, string>; related?: string[];
  shape?: { unit?: string }; description?: string | null; caveats?: string | null; sql: string;
  latest: { as_of_date: string; value: number; value_low?: number | null; value_high?: number | null; obs_ids: string[] } | null;
};
export const analyses = () => read<Analysis[]>("analyses.json");
export type Memo = {
  date: string; since: string; title: string; mode: "prose" | "digest"; model: string | null; prompt_version: string; fallback_reason: string | null;
  thesis: Record<string, boolean | null>; lens: { diffusion?: string; capture?: string }; events: number; new_observations: number; summary?: string; body: string;
};
export const memos = () => read<Memo[]>("memos/index.json");
export function memo(date: string): Memo | null {
  const p = path.join(ROOT, "memos", `${date}.json`);
  return fs.existsSync(p) ? (JSON.parse(fs.readFileSync(p, "utf8")) as Memo) : null;
}
export type VentureSeg = { source: string; kind: string; value: number; obs_ids: string[]; href: string | null };
export type VentureQuarter = { as_of: string; venture_dollars?: { value: number; obs_ids: string[] }; round_count?: { value: number; obs_ids: string[] }; venture_dollars_incl_debt?: { value: number; obs_ids: string[] }; by_source?: VentureSeg[] };
export type LayerVenture = { value: number | null; as_of: string; obs_ids: string[]; prior: { value: number; as_of: string; obs_ids: string[] } | null; arrow: "up" | "down" | "flat" | null; sublayers: { sublayer_id: string; name: string; value: number; as_of: string; obs_ids: string[] }[] };
export type VentureDoc = { sublayer_id: string; quarters: VentureQuarter[]; chart_sources?: ChartSourcesT };
export const venture = (sublayerId: string): VentureDoc | null => { try { return read<VentureDoc>(`venture/${sublayerId}.json`); } catch { return null; } };
export type LadderRow = { obs_id: string; subject: string; entity_id: string | null; as_of: string; tier: number; url: string; snippet: string };
export type LadderDoc = { current: { value: number; as_of: string; obs_ids: string[] } | null; rungs: { level: number; name: string; description: string; observables: string; production: LadderRow[]; research: LadderRow[] }[]; chart_sources?: ChartSourcesT };
export const ladder = () => read<LadderDoc>("lens/ladder.json");

// Server-only: which indicators have a page, so links to unpublished ones go to their row on /indicators instead of a 404.
let _published: Set<string> | null = null;
export const publishedIds = () => (_published ??= new Set(index().indicators.filter((c) => c.published).map((c) => c.id)));
