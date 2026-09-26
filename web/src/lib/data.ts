import fs from "node:fs";
import path from "node:path";

// The web never computes a number: every JSON here was written by `ai-tracker export`.
const ROOT = path.join(process.cwd(), "data");

export type Point = {
  as_of: string; value: number | null; low?: number | null; high?: number | null; obs_ids: string[];
  subject?: string; unit?: string; disputed?: boolean; grade?: string; dims?: Record<string, string>; series_key?: string;
  flags?: string[]; dispute_text?: string | null;
  // laid out by the export: the record, how firm the number is, and where the chart draws it (percent from top left)
  href?: string | null; stamp?: Stamp | null; x?: number; y?: number; y_low?: number; y_high?: number; faint?: boolean; partial?: boolean;
};
export type Stamp = "measured" | "reported" | "estimate";
export type Tick = { label: string; x?: number; y?: number; minor?: boolean };
export type ChartT = {
  x: { ticks: Tick[] }; y: { ticks: Tick[]; unit: string | null; log: boolean; chars: number };
  bands: { name: "normal" | "fast"; y: number; height: number }[];
  dead: { x: number; width: number; y: number; height: number } | null;
  change: { label: string; dead_band: string; steps: string } | null; line: boolean; partial: boolean;
  drawn: { metric: string | null; series: string | null; others: number; total: number }; needs: number | null;
  n_drawn: number; stamps: Stamp[];
};
export type BandValue = { value: number; unit: string; as_of: string; obs_ids: string[] };
export type Card = {
  unpublished_reason?: string | null; answers?: string[];
  id: string; name: string; bucket_id: string | null; layer_id: string | null; valve_measured: string | null;
  unit: string; published: boolean; status: string | null; confidence: number | null; leading_lagging: string | null;
  grade: string | null; latest: Point | null; spark: { d: string; end: [number, number] } | null; stale_as_of: string | null; stale_reason?: string | null; n_observations: number;
  pending?: { new_status: string; since: string } | null;
  source_cluster?: string | null; band_value?: BandValue | null;
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
  derived: (Point & { id: string; metric: string; as_of_date: string; input_observation_ids: string[] })[];
  status_events: StatusEvent[]; crosswalk: Crosswalk[]; evidence: Evidence[]; chart: ChartT | null; direction_readings: number | null;
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
  as_of: string; verdict: string; buckets: (Bucket & { indicators: Card[]; n_indicators: number; status: string; tally: Tally })[]; n_sources: number;
  valves: { id: string; from: string; to: string; name: string; status: string; tally: Tally; indicator_ids: string[] }[];
  recent_status_events: StatusEvent[]; what_would_change: string[];
}>("lens/diffusion.json");
export type ChartSourcesT = { metric: string | null; sources: { id: string; name: string; org: string; license: string | null; attribution: string | null }[] };
export type StackPart = { id: string; name: string; value: number; unit: string; as_of: string; obs_ids: string[]; estimated: boolean; stamp: Stamp | null; href: string; y: number; height: number };
export type Stack = {
  quarters: { as_of: string; name: string; label: string; minor: boolean; x: number; cx: number; width: number; parts: StackPart[] }[];
  axis: Axis | null; keys: { id: string; name: string; estimate: boolean }[];
  ends: { id: string; name: string; value: number; unit: string; as_of: string; obs_ids: string[]; y: number }[];
  stamps?: Stamp[]; sources: ChartSourcesT;
};
export const capture = () => read<{ as_of: string; verdict?: string; what_would_change: string[]; layers: (Layer & { indicators: Card[]; n_published: number; status: string; tally: Tally; venture: LayerVenture | null; reading: string })[]; recent_status_events: StatusEvent[]; gross_profit_stack: Stack; margin_stack: Stack }>("lens/capture.json");
export const sources = () => read<Source[]>("sources.json");
export type Skipped = { id: string; name: string; url: string | null; reason: string; attribution: string | null; people?: string[] };
export const skippedSources = () => read<Skipped[]>("skipped_sources.json");
export const changelog = () => read<StatusEvent[]>("changelog.json");
export type RubricBand = { lo: number; hi: number; label: string; span: number };
export const meta = () => read<{ generated_at: string; observations: number; indicators_published: number; sources: number; confidence_rubric: RubricBand[] }>("meta.json");

export { fmt, words } from "./format";
export const obsIndex = () => read<Record<string, string>>("obs_index.json");
export type Fit = { metric: string; value: number; value_low: number | null; value_high: number | null; as_of_date: string; unit?: string | null; dims: Record<string, string>; obs_ids: string[] };
export type Doc = IndicatorDoc & { source_ids?: string[]; chart_sources?: ChartSourcesT; confidence_basis?: { grade: string | null; best_tier: number | null; sources: string[]; n_observations: number; stale_as_of: string | null }; prediction_rows?: { id: string; claimant: string; ledger: string; status: string | null }[]; points: Point[]; band_value: { value: number; as_of: string | null; obs_ids: string[]; low: number | null; high: number | null } | null; fits: Fit[]; related_metrics: string[] };
export type Prediction = { direction_assessment?: string | null; magnitude_assessment?: string | null; timing_assessment?: string | null;
  id: string; ledger: "nk" | "lab" | "ai2027" | "capture" | "singularity"; claimant: string; claim_text: string; claim_url: string | null; claim_date: string;
  window_start: string | null; window_end: string | null; window_mid?: string | null; operationalisation: string; related_indicators: string[]; proxy_types: string[];
  confidence: number; counterevidence: string; note: string | null; published: boolean; status: string | null; confidence_now: number | null;
  status_events: StatusEvent[]; evidence: Evidence[];
};
export const predictions = () => read<Prediction[]>("predictions.json");
export type LedgerRow = Observation & { parties: { slug: string; entity_id: string | null; name: string; href: string | null }[]; instrument: string; obs_id: string; as_of_date: string; published_date: string; value_numeric: number | null; value_text: string | null; unit: string; tier: number; source_id: string; url: string; disputed: boolean; dispute_text: string | null; raw_snippet: string };
export const ledger = () => read<LedgerRow[]>("ledger.json");
export type ThesisCond = { text: string; holds: boolean | null; obs_ids: string[]; detail: string };
export type ThesisVerdict = { id: string; name: string; holds: boolean | null; state: string; logic: string; conds: ThesisCond[]; counter?: ThesisCond[] };
export const thesis = () => read<ThesisVerdict[]>("thesis.json");
export type Bottleneck = { id: number; title: string; text: string; section: string; bucket_id: string; source_codes: string[]; related_indicators: string[]; domain?: string | null; domain_basis?: string | null; related: { id: string; name: string; status: string | null; published: boolean }[] };
export type BottleneckDoc = { sections: { name: string; bucket_id: string }[]; essays: { code: string; title: string; url: string; date: string }[]; items: Bottleneck[]; summary: { name: string; items: number; watched: number; fast: number; normal: number; other: number }[]; domains: string[]; grid: { name: string; cells: Record<string, number[]> }[] };
export const bottlenecks = () => read<BottleneckDoc>("bottlenecks.json");
export type ComparePred = { id: string; claimant: string; status: string | null };
export type CompareRow = { indicator: string; card: Card; leans: "nk" | "ai2027" | "open" | null; columns: Record<"nk" | "ai2027" | "lab" | "capture", { text: string; predictions: ComparePred[] }> };
export const compare = () => read<{ rows: CompareRow[]; tally: { nk: number; ai2027: number; open: number } }>("compare.json");
export type StackEntity = { id: string; name: string; kind: string; cik: string | null; aliases: string[]; verified: boolean; notes: string | null; founded: number | null; is_primary: boolean; from_date: string | null; to_date: string | null; latest: { series_key: string; value: number | null; value_text: string | null; unit: string; as_of: string; obs_ids: string[] } | null; led_by: { id: string; name: string; href: string }[] };
export type StackSublayer = Sublayer & { entities: StackEntity[]; indicators: Card[]; n_entities: number; n_verified: number; n_indicators: number };
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
  thesis: Record<string, boolean | string | null>; lens: { diffusion?: string; capture?: string }; events: number; new_observations: number; summary?: string; body: string;
};
export const memos = () => read<Memo[]>("memos/index.json");
export function memo(date: string): Memo | null {
  const p = path.join(ROOT, "memos", `${date}.json`);
  return fs.existsSync(p) ? (JSON.parse(fs.readFileSync(p, "utf8")) as Memo) : null;
}
export type VentureSeg = { source: string; kind: string; value: number; obs_ids: string[]; href: string | null; stamp: Stamp | null; y?: number; height?: number };
export type VentureQuarter = {
  as_of: string; name: string; label: string; minor: boolean; label_minor: boolean; x: number; cx: number; width: number; top: number | null;
  venture_dollars?: { value: number; obs_ids: string[] }; round_count?: { value: number; obs_ids: string[] }; venture_dollars_incl_debt?: { value: number; obs_ids: string[] }; by_source?: VentureSeg[];
};
export type LayerVenture = { value: number | null; as_of: string; obs_ids: string[]; prior: { value: number; as_of: string; obs_ids: string[] } | null; arrow: "up" | "down" | "flat" | null; sublayers: { sublayer_id: string; name: string; value: number; as_of: string; obs_ids: string[] }[] };
export type VentureDoc = { sublayer_id: string; quarters: VentureQuarter[]; chart_sources?: ChartSourcesT };
export const venture = (sublayerId: string): VentureDoc | null => { try { return read<VentureDoc>(`venture/${sublayerId}.json`); } catch { return null; } };
export type LadderRow = { obs_id: string; subject: string; name: string; href: string | null; entity_id: string | null; as_of: string; tier: number; url: string; snippet: string };
export type LadderDoc = { current: { value: number; as_of: string; obs_ids: string[] } | null; rungs: { level: number; name: string; description: string; observables: string; production: LadderRow[]; research: LadderRow[] }[]; chart_sources?: ChartSourcesT };
export const ladder = () => read<LadderDoc>("lens/ladder.json");

// Server-only: which indicators have a page, so links to unpublished ones go to their row on /indicators instead of a 404.
let _published: Set<string> | null = null;
export const publishedIds = () => (_published ??= new Set(index().indicators.filter((c) => c.published).map((c) => c.id)));
export type Fact = { value: number; unit: string; as_of: string; obs_ids: string[]; href: string; holds?: boolean | null; stale?: boolean };
export type ClockSeries = {
  id: string; label: string; name: string; unit: string; from: string; multiple: Fact; stamp: Stamp | null; label_y: number;
  series: { as_of: string; value: number; obs_ids: string[]; multiple: number; x: number; y: number; href: string | null }[];
};
export type Axis = { ticks: Tick[]; unit: string | null; log: boolean; chars: number };
export type Gauge = {
  id: string; label: string; weight: number; max_age_days: number | null; knots: [number, number][] | null; scale_rationale: string | null;
  unfed: { kind: string; because: string } | null; required: boolean; log10: boolean; unit: string | null; reading: Fact | null; age_days: number | null;
  grade: string | null; points: number | null; pinned: "low" | "high" | null; unavailable: string | null;
};
export type TightInput = {
  id: string; n: number; name: string; kind: string; what: string; reads: string | null; ceiling: number; ceiling_rationale: string | null;
  score: number | null; word: string | null; confidence: number | null; at_ceiling: boolean; hatched: boolean; used: number; defined: number;
  factors: { coverage: number; freshness: number; source: number } | null; obs_ids: string[]; withheld: { kind: string; because: string } | null; gauges: Gauge[];
};
export type Scorecard = {
  kinds: { id: string; name: string; tight_means: string }[]; inputs: TightInput[]; total: number;
  scored: Omit<Fact, "value" | "as_of"> & { value: number | null; as_of: string | null };
  method: Record<string, unknown> & { words: [number, string][]; hatch_under: number }; chart_sources: ChartSourcesT;
};
export type StripRow = { id: string; label: string; predicted: boolean; spans: { from: number; to: number; running: boolean; level: "binding" | "present"; because: string; source: string; left: number; width: number; anchor: string }[] };
export type OwnPrediction = { id: string; when: "now" | "next" | "watch"; claim: string; text: string; fact: string | null; state: "holding" | "failing" | "untestable" };
export type MigrationDoc = {
  as_of: string; facts: Record<string, Fact | null>; scorecard: Scorecard; strip: { from: number; to: number; now: number; now_x: number; ticks: Tick[]; rows: StripRow[] };
  predictions: OwnPrediction[]; tally: Record<"holding" | "failing" | "untestable", number>; sources: { who: string; work: string; where: string; url: string }[];
};
export type ArgumentDoc = {
  as_of: string | null;
  essay: { home: string; full: string; migration: string };
  record: { title: string; text: string }[];
  migration: MigrationDoc;
  facts: Record<string, Fact | null>;
  slow_variables: { id: string; label: string; sentence: string }[];
  clocks: { start: string; drawn: ClockSeries[]; listed: string[]; holds: boolean | null; chart: { x: { ticks: Tick[] }; y: Axis } | null; chart_sources: ChartSourcesT };
  phase: { state: "installation" | "turning_point" | "deployment" | "untestable"; rule: string; as_of: string | null; history: { as_of: string; raw: string; state: string }[]; chart_sources: ChartSourcesT };
  exits: { monitor: string; label: string; text: string; state: string | null }[];
  headlines: Record<"diffusion" | "capture", { monitor: string; state: string; claim: string }>;
  sources: { who: string; work: string; where: string; url: string }[];
};
export const argument = () => read<ArgumentDoc>("argument.json");

export type SignpostTest = {
  test: string; name: string; what: string; whose: string; value: number; unit: string; as_of: string; obs_ids: string[];
  href: string | null; stamp: Stamp | null; newest: string; stale: boolean; x: number;
};
export type HalPoint = { measure: "accuracy" | "reliability"; unit: string; as_of: string; value: number; obs_ids: string[]; label: string; x: number; y: number; href: string | null };
export type HalTrend = {
  id: string; measure: "accuracy" | "reliability"; value: number; label: string; as_of: string; n: number; obs_ids: string[]; href: string;
  x1: number; y1: number; x2: number; y2: number; label_y: number;
};
export type Signposts = {
  stale_after_days: number; tests: SignpostTest[]; axis: { ticks: Tick[] }; chart_sources: ChartSourcesT;
  reliability: { points: HalPoint[]; trends: HalTrend[]; x: { ticks: Tick[] }; y: Axis; stamps: Stamp[]; chart_sources: ChartSourcesT } | null;
};
export const signposts = () => read<Signposts>("signposts.json");

export type ContextPoint = {
  as_of: string; value: number; obs_ids: string[]; href: string | null; x: number; y: number; joined: boolean;
  id?: string; inputs?: { label: string; href: string | null }[];
};
export type ContextDoc = {
  start: string;
  figures: { id: string; title: string; unit: string; caption: string; page: string; note: string; lines: { label: string; points: ContextPoint[]; label_y: number }[]; x: { ticks: Tick[] }; y: Axis; stamps: Stamp[]; chart_sources: ChartSourcesT }[];
};
export const context = () => read<ContextDoc>("context.json");

export type MapWriter = { who: string; text: string; state: string; href: string };
export type MapCell = { bites: boolean; measured: boolean; why: string | null; site: boolean; writers: MapWriter[] };
export type MapReading =
  | { kind: "scored"; score: number; word: string; confidence: number; hatched: boolean; kind_of_tight: string; obs_ids: string[] }
  | { kind: "withheld"; because: string | null; tag: string | null; kind_of_tight: string }
  | { kind: "tally"; instruments: number; fast: number; normal: number; other: number; readings: number };
export type MapRow = {
  focus?: "now" | "predicted" | "both" | null;
  id: string; name: string; what?: string; reads?: string | null; note?: string | null; family?: string; source?: string; href: string | null;
  layer?: { id: string; name: string }; sublayer?: { id: string; name: string } | null;
  reading: MapReading; cells: Record<string, MapCell>; claims: MapWriter[]; domains?: Record<string, number[]>;
  instruments: { label: string; href: string | null; status?: string | null; unpublished?: boolean }[];
  readings?: { label: string; value: number; unit: string; as_of: string; obs_ids: string[]; href: string | null }[];
};
export type MapDoc = {
  stages: { id: string; label: string; n: number }[]; scored: number;
  groups: { id: string; label: string; sections: { id: string; name: string; rows: MapRow[] }[] }[];
  bets: { sublayer: { id: string; name: string }; rows: string[]; firms: number; as_of: string | null;
    venture: { value: number; unit: string; as_of: string; obs_ids: string[]; href: string } | null }[];
};
export const bottleneckMap = () => read<MapDoc>("map.json");

export type OutlookState = "holding" | "failing" | "both" | "untestable";
export type OutlookTest = { fact: string } & Partial<Record<"gt" | "gte" | "lt" | "lte", number | string>>;
export type OutlookSource = { id: string; n: number; who: string; short?: string; field: string; finding: string; work: string; venue?: string; year: number; url: string; quote?: string };
export type OutlookPosition = {
  id: string; folio: string; title: string; holders: string[]; attribution: "author" | "extension" | "site";
  mechanism: string; case: string; kill_shot: string; rival: string; visible: boolean;
};
export type OutlookClaim = {
  id: string; position: string; text: string; falsifier?: string; row: string | null; stage: string | null; due: string | null; rival_until: string | null;
  test: OutlookTest | null; rival_test: OutlookTest | null; fact: string | null; rival: string; folio: string;
  holders: string[]; attribution: string; state: OutlookState; expected: OutlookState | null;
};
export type OutlookCell = { progress: string; rules: string; argued_by: string[]; says: string; signposts: { claim: string; state: OutlookState }[]; binds_next: string[]; tested: boolean; consistent: boolean };
export type OutlookDoc = {
  as_of: string; essay: string; facts: Record<string, Fact | null>; sources: OutlookSource[]; positions: OutlookPosition[];
  claims: OutlookClaim[]; tally: Record<OutlookState, number>; tests: Record<string, { line: number; unit: string }>;
  folios: { id: string; kicker: string }[];
  scenarios: { progress: { id: string; label: string }[]; rules: { id: string; label: string }[]; cells: OutlookCell[]; anchors: { source: string; date: string; text: string }[] };
  agree: { id: string; text: string; holders: string[]; dissent: string[]; dissent_text?: string }[];
};
export const outlook = () => read<OutlookDoc>("outlook.json");
export type Word = "happening" | "not_happening" | "slower" | "both" | "too_early";
export type BoardRow = {
  id: string; kind: "ledger" | "outlook" | "migration" | "exit"; folio: string; who: string; attribution: string; line: string;
  state: string | null; word: Word; settles: string | null; test: { fact: string; op: string; against: number | string } | null;
  reading: Fact | null; sources: string[]; indicators: string[]; href: string;
};
export type BoardDoc = {
  as_of: string; words: { id: Word; label: string; meaning: string }[]; mapping: { kind: string; state: string; word: Word }[];
  tally: Record<Word, number>; folios: { id: string; label: string; question: string; rows: BoardRow[]; too_early: number }[];
  questions: { question: string; indicator: string | null; note?: string; status: string | null; href: string | null }[];
};
export const board = () => read<BoardDoc>("board.json");

// The singularity timeline (src/ai_tracker/singularity.py): every position is laid out in Python.
export type SgMark = {
  id: string; who: string; line: string; ledger: string; made: string; made_year: number;
  step: boolean; low: number | null; mid: number | null; high: number | null; x_low: number | null; x_high: number | null; x: number | null;
  status: string | null; word: string; settles: string | null; href: string; slot?: number; lane?: string;
  span_width?: number; quoted: boolean; years: string | null;
};
export type SgLane = { id: string; label: string; definition: string; forecasts: SgMark[]; undated: SgMark[]; slots: number; signposts: { id: string; reading: Fact | null }[] };
export type SgFiction = { title: string; author: string; year_written: number; set_in_year?: number; set_in_words?: string; lane: string; line: string; source: string; url: string | null; anchor: string; x: number | null; slot?: number };
export type SgSource = { id: string; who: string; field: string; finding: string; work: string; year: number; url: string; quote?: string };
export type SingularityDoc = {
  as_of: string; intro: string;
  axis: { ticks: { year: number; x: number }[]; breaks: number[]; bins: { label: string; x: number }[]; today: number };
  lanes: SgLane[]; due: SgMark[];
  table: { cols: { id: string; label: string }[]; rows: { who: string; cells: Record<string, { text: string; href: string; word: string; made: string }> }[] }; stops: number[]; tallies: Record<string, Record<string, number>>;
  questions: { id: string; question: string; reads?: string; label?: string; fast: string; slow: string; reading: Fact | null }[];
  worlds: { id: string; label: string; text: string; argued_by: string[]; consistent: boolean; grid: { progress: string; rules: string }[] }[];
  fiction: SgFiction[]; fiction_slots: number; sources: SgSource[]; words: Record<string, string>;
};
export const singularity = () => read<SingularityDoc>("singularity.json");

// The Singularity Atlas (src/ai_tracker/atlas.py): every count, level and label is worked out in Python.
export type AtPlate = { file: string; height: number; alt: string; allegory: string; caption?: string; src: string; srcset: string };
export type AtCount = { world: string; n: number; level: number; label: string; any: number };
export type AtReading = { id: string; label: string; reading: Fact | null; year: string | null };
export type AtEntry = {
  id: string; domain: string; era: string; line: string; who: string; work: string; year: number; url: string; source: string;
  worlds: string[]; any: boolean; world_labels: string[]; reads: { id: string; label: string; reading: Fact | null }[];
};
export type AtEra = { id: string; label: string; short: string; definition: string };
export type AtDomain = {
  id: string; n: number; name: string; thesis: string; thesis_from: string[]; plate: AtPlate; readings: AtReading[];
  eras: (AtEra & { entries: AtEntry[]; works: number })[]; disagreement: { question: string; sides: { view: string; who: string[] }[] } | null;
  fiction: { title: string; author: string; year: number; line: string; href: string }[]; fiction_more: number;
  leaning: { id: string; line: string; who: string; word: string; word_label: string; href: string }[];
  sources: { id: string; who: string; work: string; year: number; url: string }[]; prev: string | null; next: string | null;
};
export type AtMapRow = { id: string; name: string; href: string; plate: AtPlate; cells: { era: string; href: string; counts: AtCount[] }[] };
export type AtlasDoc = {
  as_of: string; intro: string; provenance: string; hero: AtPlate; eras: AtEra[]; worlds: { id: string; label: string; short: string }[];
  filter: boolean; map: AtMapRow[]; domains: AtDomain[]; count: { expectations: number; sources: number; domains: number };
};
export const atlas = () => read<AtlasDoc>("atlas.json");

// The automatability census (plans Part 21, Part 23): a judged snapshot imported as published. "Passes" means passes the
// structural hand-over screen; agreed3 null = not scored by all three. The only modelled figure is headline.modelled_saving.
export type CensusRole = {
  occ: string; title: string; function: string; href: string; ref: string; emp: number; wage_bill: number;
  share_passes: number; rule_strict: number; rule_loose: number; scorer_min: number; scorer_max: number; by_scorer: Record<string, number>;
  passes: number; agreed3: number | null; scored_by_three: boolean; payroll_scored_by_three: number; contested: number;
  not_called: number; physical_removed: number; accountable_removed: number; ai_exposure: number | null;
  n_tasks: number; n_passes: number; time_share_basis: string; split: string;
};
export type CensusFunction = {
  function: string; ref: string; payroll: number; passes: number; agreed3: number | null; scored_by_three: boolean;
  payroll_scored_by_three: number; share_passes: number; rule_strict: number; rule_loose: number; blocked_by_missing_check: number; roles: number;
};
export type CensusIndustry = {
  naics: string; title: string; ref: string; payroll: number; knowledge_payroll: number; passes: number; agreed3: number | null;
  blocked_by_missing_check: number; share_total: number;
};
export type CensusCard = {
  key: string; name: string; naics: string; invoice: string; why: string; kill: string[]; comps: string[]; scope: string;
  excl: string; anchored: boolean; stance: string; stance_why: string; sources: { cited_as: string; href: string }[];
  payroll: number; passes: number; passes_strict: number; passes_loose: number; agreed3: number | null;
  roles: { title: string; wage_bill: number; share_passes: number; passes: number; agreed3: number | null }[];
};
export type CensusIndex = {
  version: string; generated_at: string; manifest_sha256: string; sources: string[]; scorers: string[]; scorer_names: Record<string, string>;
  prose: { title: string; lede: string; rule: string; agreed: string; caveats: string[]; sections: Record<string, { title: string; lede: string }>; method_notes: Record<string, string> };
  headline: {
    passes: number; agreed3: number; payroll: number; contested: number; blocked_by_missing_check: number; physical_removed: number;
    accountable_removed: number; not_called: number; by_scorer: Record<string, number>; rescore_changed: number; fleiss_kappa: number;
    modelled_saving: number; ref: string;
  };
  dial: { rule: string; passes: number; agreed3: number; alone: number; alone_rest: number; headline: boolean }[];
  functions: CensusFunction[]; industries: CensusIndustry[]; roles: CensusRole[];
  deals: { cards: CensusCard[]; not_carded: { name: string; why: string }[] };
  method: CensusMethod;
  csv: Record<string, string>;
};
type AloneTest = { n: number; passes: number; fails: number; within_occ_pp: number; within_occ_t: number; label?: string };
export type CensusMethod = {
  gates: { k: "pre17" | "pre24" | "post"; g: string; v: string; t: string; p: boolean | null; n: string }[];
  validation: { ai_alone: AloneTest; ai_alone_api: AloneTest; agreement: { n_called: number; fleiss_verdict: number; cohen_verdict: Record<string, number> } };
  adjudication: { scorer: string; tasks: number; stakes_vs_workers: number; grader_vs_workers: number; alone_consumer: number }[];
  placebo: { method: string; noise_median: number; trusted: boolean }[];
  stability: { start: number; industry: string; b: number; ci: number }[];
  channel: { runs: { period: string; n_a: number; n_b: number; a_coef: number; a_z: number; b_coef: number; b_z: number }[]; headline: { period: string; z: number; label: string } };
  by_scorer: Record<string, { passes_usd: number; note: string }>;
  rescore_stability: { scorer: string; n_tasks: number; share_verdicts_changed: number; note: string };
  physical_gate: { removed_usd: number; spotcheck: Record<"removed" | "kept", { set_usd: number; draws: number; wrong: number; error_rate: number; ci95: number[]; effect_usd: number[] }> };
  not_called: { usd: number; share: number };
  sigma: { sigma: number; before: number; after: number }[];
};
export type CensusTask = {
  id: string; ref: string; task: string; passes: boolean; why: string; physical: boolean; accountable: boolean; not_called: boolean;
  contested: boolean; agreed_all_three: boolean; blocked_by_missing_check: boolean; passes_by: Record<string, boolean>; time_share: number; payroll: number;
};
export type CensusRoleDoc = {
  version: string; role: CensusRole; scorers: string[]; tasks: CensusTask[]; csv: string;
  industries: { naics: string; title: string; emp: number; wage_bill: number; passes: number; agreed3: number | null }[];
};
export const census = () => read<CensusIndex>("census/index.json");
export const censusRole = (occ: string) => read<CensusRoleDoc>(`census/roles/${occ}.json`);

// Futures (plan Part 20): imagined and expected technologies by decade, model-judged, rendered as exported.
export type FuIdea = {
  id: string; name: string; work: string; author: string; imagined: number; line: string;
  arrival: string; built: boolean; judged: string | null; profit: string; image: string | null;
};
export type FuForecast = {
  id: string; who: string; line: string; when: string; odds: string | null; quote: string | null;
  ledger: string | null; works: { title: string; author: string; year: number; url?: string }[];
};
export type FuGroup = { id: string; name: string; n: number; ideas: FuIdea[] };
export type FuIndex = {
  n_ideas: number; n_forecasts: number; n_idea_images: number; n_category_images: number; tier_words: string[];
  imagined: { key: string; label: string; n: number; built: number; width: number; built_width: number; href: string | null }[];
  expected: { key: string; label: string; judged: number; stated: number; judged_width: number; stated_width: number; href: string }[];
  categories: { id: string; name: string; n: number; built: number; tiers: Record<string, number>; image: string | null; href: string }[];
  featured: FuIdea[]; credits: { name: string; url: string; archived: boolean }[];
};
export type FuDecade = { kind: "imagined" | "expected"; key: string; label: string; title: string; phrase?: string; n?: number; built?: number; judged?: number; stated?: number; groups: FuGroup[]; forecasts?: FuForecast[] };
export type FuCategory = { id: string; name: string; image: string | null; n: number; tiers: Record<string, number>; ideas: FuIdea[]; forecasts: FuForecast[] };
export const futures = () => read<FuIndex>("futures/index.json");
export const futuresDecade = (kind: string, key: string) => read<FuDecade>(`futures/${kind}/${key}.json`);
export const futuresCategory = (id: string) => read<FuCategory>(`futures/category/${id}.json`);
