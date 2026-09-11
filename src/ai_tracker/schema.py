"""Tracker objects. Observation -> Derived -> Indicator; nothing renders without a path back to an Observation."""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from enum import Enum, IntEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Tier(IntEnum):
    BENCHMARK = 1
    MODEL_RELEASE = 2
    PRODUCT_BEHAVIOUR = 3
    OFFICIAL_FILING = 4
    CREDIBLE_REPORTING = 5
    PUBLISHED_ANALYSIS = 6
    ACTOR_STATEMENT = 7


class Basis(str, Enum):
    audited = "audited"
    company_stated = "company_stated"
    reported = "reported"
    estimated = "estimated"


class Extraction(str, Enum):
    api = "api"
    xbrl = "xbrl"
    scrape = "scrape"
    pdf = "pdf"
    llm_extract = "llm_extract"
    manual = "manual"


class Review(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class SourceKind(str, Enum):
    api = "api"
    xbrl = "xbrl"
    formd = "formd"
    csv = "csv"
    rss = "rss"
    html = "html"
    pdf = "pdf"
    arxiv = "arxiv"
    x = "x"
    manual = "manual"


class Lens(str, Enum):
    diffusion = "diffusion"
    capture = "capture"
    both = "both"


class ProxyType(str, Enum):
    benchmark = "benchmark"
    deployment = "deployment"
    product = "product"
    behaviour = "behaviour"
    policy = "policy"
    model_release = "model_release"
    market_structure = "market_structure"
    price = "price"
    capital_flow = "capital_flow"
    welfare = "welfare"


class FlowStatus(str, Enum):
    consistent_with_normal = "consistent_with_normal"
    faster_than_normal = "faster_than_normal"
    slower_than_normal = "slower_than_normal"
    emerging = "emerging"
    not_yet_measurable = "not_yet_measurable"


class Direction(str, Enum):
    concentrating = "concentrating"
    dispersing = "dispersing"
    stable = "stable"
    unclear = "unclear"
    emerging = "emerging"
    not_yet_measurable = "not_yet_measurable"


class LeadLag(str, Enum):
    leading = "leading"
    coincident = "coincident"
    lagging = "lagging"


class Relation(str, Enum):
    same_valve = "same_valve"
    input_to = "input_to"
    leak_from = "leak_from"
    return_arrow = "return_arrow"


UNSCORED = {"emerging", "not_yet_measurable", "not_yet_testable"}
NEEDS_REVIEW = {Extraction.llm_extract, Extraction.manual, Extraction.scrape}


def grade_from_tier(tier: Tier, basis: Basis = Basis.reported, single_source: bool = False) -> str:
    """Display label only; tier is the stored truth. Government statistics (tier 4, reported) are A."""
    if single_source or tier == Tier.ACTOR_STATEMENT:
        return "D"
    if tier == Tier.BENCHMARK or (tier == Tier.OFFICIAL_FILING and basis in (Basis.audited, Basis.reported)):
        return "A"
    if tier in (Tier.MODEL_RELEASE, Tier.PRODUCT_BEHAVIOUR, Tier.OFFICIAL_FILING) or (
        tier == Tier.PUBLISHED_ANALYSIS and basis != Basis.estimated
    ):
        return "B"
    return "C"


def cap_status_by_tier(status: str, best_tier: Tier) -> str:
    """Tier-7 evidence (actor statements) proposes at most `emerging`."""
    return "emerging" if best_tier == Tier.ACTOR_STATEMENT and status not in UNSCORED else status


def short_hash(*parts: object) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


class Observation(BaseModel):
    id: str = ""
    series_key: str
    unit: str
    as_of_date: date
    published_date: date
    retrieved_at: datetime
    url: str
    content_hash: str
    http_status: int
    source_id: str
    tier: Tier
    audited_vs_reported: Basis
    extraction_method: Extraction
    extractor_version: str
    raw_snippet: str = Field(min_length=1)
    value_numeric: float | None = None
    value_text: str | None = None
    value_low: float | None = None
    value_high: float | None = None
    period_start: date | None = None
    entity_id: str | None = None
    run_rate_vs_booked: Literal["run_rate", "booked"] | None = None
    gross_vs_net: Literal["gross", "net"] | None = None
    note: str | None = None  # a maintainer's note carried from the seed row; never a value
    disputed: bool = False
    dispute_text: str | None = None
    review_status: Review = Review.approved
    reviewer_id: str | None = None
    supersedes_id: str | None = None

    @model_validator(mode="after")
    def _rules(self) -> Observation:
        if (self.value_numeric is None) == (self.value_text is None):
            raise ValueError("exactly one of value_numeric / value_text")
        if self.audited_vs_reported == Basis.audited and self.tier != Tier.OFFICIAL_FILING:
            raise ValueError("audited requires tier 4 (official filing)")
        if self.disputed and not self.dispute_text:
            raise ValueError("disputed needs dispute_text")
        if self.extraction_method in NEEDS_REVIEW and not self.reviewer_id:
            self.review_status = Review.pending
        if not self.id:
            self.id = short_hash(
                self.source_id,
                self.series_key,
                self.entity_id,
                self.as_of_date,
                self.period_start,
                self.value_numeric,
                self.value_text,
            )
        return self

    @property
    def grade(self) -> str:
        return grade_from_tier(self.tier, self.audited_vs_reported)


class Derived(BaseModel):
    id: str = ""
    metric: str
    value: float
    value_low: float | None = None
    value_high: float | None = None
    as_of_date: date
    input_observation_ids: list[str] = Field(min_length=1)
    formula_version: str
    computed_at: datetime
    dims: dict[str, str] = {}

    @model_validator(mode="after")
    def _id(self) -> Derived:
        if not self.id:
            self.id = short_hash(self.metric, self.as_of_date, sorted(self.dims.items()))
        return self


class Band(BaseModel):
    lo: float | None = None
    hi: float | None = None

    @model_validator(mode="after")
    def _bound(self) -> Band:
        if self.lo is None and self.hi is None:
            raise ValueError("band needs at least one bound")
        return self

    def contains(self, v: float) -> bool:
        return (self.lo is None or v >= self.lo) and (self.hi is None or v <= self.hi)


class DirectionRule(BaseModel):
    periods: int = 4
    dead_band: float
    higher_is: Literal["concentrating", "dispersing"]
    rationale: str


class Indicator(BaseModel):
    id: str
    name: str
    definition: str
    why_it_matters: str
    proxy_types: list[ProxyType]
    unit: str
    cadence_expected: str
    tracker_interpretation: str
    counterevidence: str = ""
    series_keys: list[str] = []  # fnmatch globs over observation series_key
    metric: str | None = None  # derived metric that is the headline series
    metric_dims: dict[str, str] = {}  # e.g. {"entity": "nvda"} to select one dims slice of the metric
    related_metrics: list[str] = []  # alternative fits shown alongside (model comparison)
    band_input: str | None = None  # series_key glob, or "metric:<name>", that the bands apply to
    bucket_id: str | None = None
    valve_measured: str | None = None
    normal_band: Band | None = None
    fast_band: Band | None = None
    falsifying_band: Band | None = None
    band_rationale: str | None = None
    flow_status: FlowStatus | None = None
    layer_id: str | None = None
    sublayer_id: str | None = None
    direction_rule: DirectionRule | None = None
    direction: Direction | None = None
    leading_lagging: LeadLag | None = None
    timing_rationale: str | None = None  # one sentence why the tag fits; its first word is the tag
    confidence: int = Field(0, ge=0, le=95)
    proposed_status: str | None = None
    override_note: str | None = None
    related_bottlenecks: list[int] = []
    related_indicators: list[str] = []
    related_predictions: list[str] = []
    published: bool = False
    stale_ok: bool = False  # a published indicator may sit past its cadence only with a reason
    unpublished_reason: str | None = None  # rendered on the index when published is false
    stale_reason: str | None = None
    updated_at: date

    @model_validator(mode="after")
    def _rules(self) -> Indicator:
        if not (self.bucket_id or self.layer_id):
            raise ValueError(f"{self.id}: needs a bucket_id or layer_id")
        if self.published and not self.counterevidence.strip():
            raise ValueError(f"{self.id}: published indicators need counterevidence")
        if self.stale_ok and not self.stale_reason:
            raise ValueError(f"{self.id}: stale_ok needs stale_reason")
        if not self.published and not (self.unpublished_reason or "").strip():
            raise ValueError(f"{self.id}: unpublished indicators need an unpublished_reason")
        return self


class StatusEvent(BaseModel):
    id: str = ""
    target_type: Literal["indicator", "prediction"] = "indicator"
    target_id: str
    old_status: str | None = None
    new_status: str
    old_conf: int | None = None
    new_conf: int
    reason: str
    evidence_ids: list[str] = []
    counterevidence_considered: str | None = (
        None  # v2 §8: what a human weighed against the move, when they write one
    )
    author: str
    created_at: datetime

    @model_validator(mode="after")
    def _id(self) -> StatusEvent:
        if not self.id:
            self.id = short_hash(self.target_id, self.new_status, self.created_at)
        return self


class FetchLog(BaseModel):
    id: str = ""
    source_id: str
    started_at: datetime
    finished_at: datetime
    ok: bool
    http_status: int | None = None
    bytes: int = 0
    items_found: int = 0
    items_new: int = 0
    error: str | None = None
    scrubbed: list[str] = []

    @model_validator(mode="after")
    def _id(self) -> FetchLog:
        if not self.id:
            self.id = short_hash(self.source_id, self.started_at)
        return self


class Source(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )  # an unquoted comma in a flow mapping becomes a stray key; refuse it

    id: str
    name: str
    org: str
    url: str
    kind: SourceKind
    default_tier: Tier
    cadence: str
    lens: Lens
    connector: str | None = None
    license: str | None = None
    attribution: str | None = None
    robots_ok: bool = True
    expect_series: list[str] = []
    people: list[str] = []
    watch: dict[str, str] = {}  # feeds connector: slug -> regex over title + description


class SkippedSource(BaseModel):
    """A source the briefs name that is read but not ingested, with the reason (rendered on /sources)."""

    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    url: str | None = None
    reason: str = Field(min_length=1)
    attribution: str | None = None
    people: list[str] = []  # Appendix F: people read through this source, even though it is not ingested


class Bucket(BaseModel):
    id: str
    name: str
    order: int
    speed_limit: str
    stock: str
    valve: str


class Layer(BaseModel):
    id: str
    name: str
    order: int
    description: str
    dependency_tier: int | None = None


class Sublayer(BaseModel):
    id: str
    layer_id: str
    name: str
    order: int
    description: str = ""


class Membership(BaseModel):
    layer_id: str
    sublayer_id: str | None = None
    is_primary: bool = True
    from_date: date | None = None
    to_date: date | None = None


class Entity(BaseModel):
    id: str
    name: str
    kind: Literal["company", "lab", "agency", "person", "university", "fund", "nonprofit"] = "company"
    cik: str | None = None  # 10-digit, zero-padded
    extra_ciks: list[str] = []  # further filers that are the same entity (xAI files under two)
    crunchbase_id: str | None = None
    aliases: list[str] = []
    founded: int | None = None
    hq: str | None = None
    notes: str | None = None
    verified: bool = False
    memberships: list[Membership] = []


class PredStatus(str, Enum):
    confirmed = "confirmed"
    ahead = "ahead"
    on_track = "on_track"
    behind = "behind"
    emerging = "emerging"
    not_yet_testable = "not_yet_testable"


class Prediction(BaseModel):
    id: str
    ledger: Literal["nk", "lab", "ai2027", "capture"]
    claimant: str
    claimant_entity_id: str | None = None
    claim_text: str = Field(min_length=20)  # verbatim
    claim_url: str | None = None
    claim_date: date
    window_start: date | None = None
    window_end: date | None = None
    operationalisation: str
    related_indicators: list[str] = []
    proxy_types: list[ProxyType] = []
    confidence: int = Field(0, ge=0, le=95)
    direction_assessment: str | None = None
    magnitude_assessment: str | None = None
    timing_assessment: str | None = None
    counterevidence: str = ""
    note: str | None = None
    published: bool = False

    @model_validator(mode="after")
    def _rules(self) -> Prediction:
        if self.published and not (self.claim_url and self.counterevidence.strip()):
            raise ValueError(f"{self.id}: published predictions need a fetched claim_url and counterevidence")
        return self


class Essay(BaseModel):
    code: str
    title: str
    url: str
    date: date


class Bottleneck(BaseModel):
    id: int = Field(ge=1, le=89)
    title: str
    text: str
    section: str
    bucket_id: str
    source_codes: list[str]
    related_indicators: list[str] = []
    domain: str | None = None  # from the raw extraction; the grid's second axis (there is no mechanism field)
    domain_basis: str | None = None


class CompareRow(BaseModel):
    indicator: str
    nk: str = ""
    ai2027: str = ""
    lab: str = ""
    capture: str = ""
    predictions: list[str] = []  # grouped into columns by each prediction's own ledger at export
    nk_predictions: list[str] = []
    ai2027_predictions: list[str] = []


class Crosswalk(BaseModel):
    bucket_id: str
    layer_id: str
    relation: Relation
    sublayer_id: str | None = None
    note: str = ""
    shared_indicators: list[str] = []
