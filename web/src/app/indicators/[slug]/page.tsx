import Link from "next/link";
import { indicatorHref } from "@/lib/format";
import { ConfidenceDial } from "@/components/ConfidenceDial";
import { DirectionChart } from "@/components/DirectionChart";
import { EvidenceLog } from "@/components/EvidenceLog";
import { BandChart } from "@/components/BandChart";
import { ChangelogList } from "@/components/Changelog";
import { Num, ObsLinks } from "@/components/Provenance";
import { Section } from "@/components/Section";
import { Grade, PendingNote, StatusChip } from "@/components/StatusChip";
import { fmt, index, indicator, obsIndex, sources, words, type Band } from "@/lib/data";

export const dynamicParams = false;
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const d = indicator(slug);
  return { title: d.name, description: d.definition };
}
export function generateStaticParams() { return index().indicators.filter((i) => i.published).map((i) => ({ slug: i.id })); }

const band = (b: Band, unit: string) => (b ? [b.lo != null ? `≥ ${fmt(b.lo, unit)}` : null, b.hi != null ? `≤ ${fmt(b.hi, unit)}` : null].filter(Boolean).join(" and ") : "—");
const SECTIONS: [string, string][] = [["evidence", "Evidence"], ["status", "Status and reasoning"], ["measures", "What this measures"], ["track", "How we track this"], ["interpretation", "Tracker interpretation"], ["evidence-log", "Evidence log"], ["counterevidence", "Counterevidence"], ["timeline", "Timeline notes"], ["history", "Update history"], ["confidence", "Confidence"], ["related", "Related"]];
const RUBRIC = (c: number | null) => c === null ? "no status yet" : c >= 90 ? "multiple strong independent sources" : c >= 70 ? "good evidence, some ambiguity" : c >= 50 ? "mixed or hard to operationalise" : "limited or vague evidence";

export default async function IndicatorPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const d = indicator(slug);
  const idx = obsIndex();
  const { buckets, layers, indicators } = index();
  const srcs = sources();
  const bandOnChart = d.band_input && (d.band_input === `metric:${d.metric}` || d.band_input === d.series_keys[0]);
  const bandUnit = d.band_input?.includes("doubling") ? "days" : d.unit;
  const current = d.status_events[0];
  const visible = SECTIONS.filter(([id]) => id !== "evidence-log" || d.evidence.length);
  const num = (id: string) => visible.findIndex(([x]) => x === id) + 1;
  const seriesSources = Array.from(new Set(d.series.map((s) => s.series_key.split(".")[0]))).map((id) => srcs.find((s) => s.id === id)).filter(Boolean);
  return (
    <article className="flex flex-col lg:grid lg:grid-cols-[15rem_minmax(0,1fr)] lg:gap-12">
      <section aria-label="Indicator summary" className="hidden lg:flex lg:sticky lg:top-8 self-start flex-col gap-4 lg:pt-1">
        <div className="flex flex-wrap items-center gap-2 lg:flex-col lg:items-start lg:gap-3">
          <StatusChip status={d.published ? d.status : null} size="lg" />
          <div className="flex items-center gap-3"><ConfidenceDial value={d.confidence} size={64} /><Grade grade={d.grade} /></div>
          {d.leading_lagging ? <span className="eyebrow">{d.leading_lagging}</span> : null}
        </div>
        <p className="text-xs text-muted">{RUBRIC(d.confidence)}</p>
        {d.stale_as_of ? <p className="text-slow text-xs">stale as of {d.stale_as_of}</p> : null}
        {d.pending ? <p className="text-xs leading-snug"><PendingNote p={d.pending} /></p> : null}
        {d.stale_reason ? <p className="text-muted text-xs">refreshed irregularly: {d.stale_reason}</p> : null}
        {d.normal_band ? (
          <dl className="hidden lg:grid gap-1 text-xs border-t border-grid pt-3">
            <div><dt className="eyebrow">Normal band</dt><dd className="num">{band(d.normal_band, bandUnit)}</dd></div>
            <div><dt className="eyebrow">Fast band</dt><dd className="num">{band(d.fast_band, bandUnit)}</dd></div>
            {d.falsifying_band ? <div><dt className="eyebrow">Falsifying</dt><dd className="num">{band(d.falsifying_band, bandUnit)}</dd></div> : null}
          </dl>
        ) : null}
        {d.direction_rule ? <p className="hidden lg:block text-xs text-ink-2 border-t border-grid pt-3">Direction over {d.direction_rule.periods} periods, dead band {fmt(d.direction_rule.dead_band, d.unit)}; higher = {d.direction_rule.higher_is}.</p> : null}
        <p className="hidden lg:block eyebrow border-t border-grid pt-3">updated {d.updated_at}</p>
        <nav aria-label="On this page" className="hidden lg:block border-t border-grid pt-3">
          <ol className="flex flex-col gap-1 text-xs text-ink-2">
            {visible.map(([id, title], i) => <li key={id}><a href={`#${id}`} className="hover:text-ink"><span className="num text-muted mr-2">{String(i + 1).padStart(2, "0")}</span>{title}</a></li>)}
          </ol>
        </nav>
      </section>
      <div className="flex flex-col gap-10 min-w-0">
      <header>
        <p className="eyebrow">
          {d.bucket_id ? <Link href={`/buckets/${d.bucket_id}`} className="hover:text-ink">{buckets.find((b) => b.id === d.bucket_id)?.name}</Link> : null}
          {d.bucket_id && d.layer_id ? " · " : null}
          {d.layer_id ? <Link href={`/layers/${d.layer_id}`} className="hover:text-ink">{layers.find((l) => l.id === d.layer_id)?.name}</Link> : null}
        </p>
        <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em] mt-1">{d.name}</h1>
        <div className="mt-3 flex flex-wrap items-center gap-3 lg:hidden">
          <StatusChip status={d.published ? d.status : null} size="lg" />
          <ConfidenceDial value={d.confidence} />
          <Grade grade={d.grade} />
          {d.leading_lagging ? <span className="eyebrow">{d.leading_lagging}</span> : null}
          {d.stale_as_of ? <span className="text-slow text-xs">stale as of {d.stale_as_of}</span> : null}
          <PendingNote p={d.pending} />
        </div>
        <p className="mt-3 text-lg leading-snug text-ink-2 max-w-[60ch]">{d.definition}</p>
        {d.timing_rationale ? <p className="mt-2 text-sm text-ink-2 max-w-[60ch]">{d.timing_rationale}</p> : null}
      </header>

      <Section n={num("evidence")} id="evidence" title="Evidence">
        {d.direction_rule ? <DirectionChart points={d.points} unit={d.unit} rule={d.direction_rule} /> : <BandChart series={[{ name: d.name, points: d.points }]} unit={d.unit} log={d.unit === "minutes"} bands={bandOnChart ? { normal: d.normal_band, fast: d.fast_band } : null} />}
        <div className="mt-3 grid gap-3 sm:grid-cols-2 text-sm">
          <div className="panel p-3"><div className="text-xs text-muted">Latest point</div><Num p={d.latest} unit={d.unit} obsIndex={idx} />{d.latest?.subject ? <div className="text-xs text-ink-2">{d.latest.subject}</div> : null}</div>
          {d.band_value ? <div className="panel p-3"><div className="text-xs text-muted">Value the bands apply to</div><Num p={{ as_of: d.band_value.as_of ?? "", value: d.band_value.value, low: d.band_value.low, high: d.band_value.high, obs_ids: d.band_value.obs_ids }} unit={bandUnit} obsIndex={idx} /></div> : null}
        </div>
        <p className="mt-2 text-xs text-muted">{d.n_observations} observations. Hollow points are disputed (see counterevidence). Every point links to its observation.</p>
        {d.fits?.length ? (
          <div className="mt-3 overflow-x-auto">
            <div className="text-xs text-muted mb-1">Model comparison (lower AIC fits better; both on ln(horizon) residuals)</div>
            <table className="data w-full text-xs"><thead><tr><th scope="col">fit</th><th scope="col">estimate</th><th scope="col">95% interval</th><th scope="col">n</th><th scope="col">R²</th><th scope="col">AIC</th><th scope="col">inputs</th></tr></thead><tbody>
              {d.fits.map((f) => { const u = f.metric.includes("blowup") ? "year" : "days"; const show = (v: number | null) => v == null ? "—" : u === "year" ? v.toFixed(1) : `${v.toFixed(0)} days`; return (
                <tr key={f.metric}><td><code>{f.metric}</code></td><td className="tabular-nums">{show(f.value)}</td><td className="tabular-nums">{show(f.value_low)}–{show(f.value_high)}</td><td className="tabular-nums">{f.dims.n}</td><td className="tabular-nums">{f.dims.r2}</td><td className="tabular-nums">{f.dims.aic}</td><td><ObsLinks ids={f.obs_ids} obsIndex={idx} max={2} /></td></tr>
              ); })}
            </tbody></table>
          </div>
        ) : null}
        {d.derived.length ? <details className="mt-2 text-xs"><summary className="cursor-pointer text-ink-2">Derived rows ({d.derived.length})</summary>
          <table className="data w-full mt-1"><thead><tr><th scope="col">as of</th><th scope="col">dims</th><th scope="col">value</th><th scope="col">inputs</th></tr></thead><tbody>
            {d.derived.slice().reverse().map((r) => <tr key={r.as_of_date + JSON.stringify(r.dims)}><td>{r.as_of_date}</td><td>{Object.values(r.dims ?? {}).join(" ")}</td><td className="tabular-nums">{fmt(r.value, d.unit)}</td><td><ObsLinks ids={r.obs_ids} obsIndex={idx} max={3} /></td></tr>)}
          </tbody></table></details> : null}
      </Section>

      <Section n={num("status")} id="status" title="Status and reasoning">
        <div className="flex flex-wrap items-center gap-2"><StatusChip status={d.published ? d.status : null} size="lg" />{current ? <span className="text-xs text-muted">since {current.created_at.slice(0, 10)} · {current.author}</span> : null}</div>
        {current ? <p className="mt-2">{current.reason}</p> : <p className="mt-2 text-muted">No status event yet; the evaluator proposes one once an approved observation exists.</p>}
        {d.proposed_status && d.proposed_status !== d.status ? <p className="mt-2 text-xs text-ink-2">The tracker&apos;s prior expectation was <em>{words(d.proposed_status)}</em>; the evaluator reads <em>{words(d.status)}</em>. The evaluator wins until a reviewed override.</p> : null}
        {d.override_note ? <p className="mt-2 text-xs text-ink-2">Override: {d.override_note}</p> : null}
      </Section>

      <Section n={num("measures")} id="measures" title="What this measures">
        <p className="text-ink-2"><span className="text-muted">Why it matters.</span> {d.why_it_matters}</p>
        <dl className="mt-3 grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
          <div><dt className="text-muted">Proxy types</dt><dd>{d.proxy_types.join(", ")}</dd></div>
          <div><dt className="text-muted">Unit</dt><dd>{d.unit}</dd></div>
          <div><dt className="text-muted">Cadence</dt><dd>{words(d.cadence_expected)}</dd></div>
          {d.valve_measured ? <div><dt className="text-muted">Valve</dt><dd>{words(d.valve_measured)}</dd></div> : null}
        </dl>
      </Section>

      <Section n={num("track")} id="track" title="How we track this">
        <ul className="text-sm flex flex-col gap-1">
          {d.series_keys.map((k) => <li key={k}><span className="text-muted">series</span> <code className="text-xs">{k}</code></li>)}
          {d.metric ? <li><span className="text-muted">derived metric</span> <code className="text-xs">{d.metric}</code> <span className="text-muted">(formula in the semantic layer)</span></li> : null}
          {seriesSources.map((s) => s ? <li key={s.id}><span className="text-muted">source</span> <a href={s.url} className="underline decoration-grid underline-offset-4">{s.name}</a> <span className="text-muted">· default tier {s.default_tier} · {s.license}</span></li> : null)}
        </ul>
        {d.normal_band || d.direction_rule ? (
          <div className="mt-3 panel p-3 text-sm">
            {d.normal_band ? (
              <dl className="grid gap-1 sm:grid-cols-3">
                <div><dt className="text-muted text-xs">Normal band</dt><dd>{band(d.normal_band, bandUnit)}</dd></div>
                <div><dt className="text-muted text-xs">Fast band</dt><dd>{band(d.fast_band, bandUnit)}</dd></div>
                <div><dt className="text-muted text-xs">Falsifying</dt><dd>{band(d.falsifying_band, bandUnit) || "—"}</dd></div>
              </dl>
            ) : null}
            {d.direction_rule ? <p>Direction over {d.direction_rule.periods} periods, dead-band {fmt(d.direction_rule.dead_band, d.unit)}; higher = {d.direction_rule.higher_is}.</p> : null}
            <p className="mt-2 text-ink-2 text-xs">{d.band_rationale ?? d.direction_rule?.rationale}</p>
            {d.band_input ? <p className="mt-1 text-xs text-muted">Applied to <code>{d.band_input}</code>.</p> : null}
          </div>
        ) : null}
      </Section>

      <Section n={num("interpretation")} id="interpretation" title="Tracker interpretation"><p>{d.tracker_interpretation}</p></Section>

      {d.evidence.length ? <Section n={num("evidence-log")} id="evidence-log" title="Evidence log"><EvidenceLog items={d.evidence} /></Section> : null}

      <Section n={num("counterevidence")} id="counterevidence" title="Counterevidence">
        <details open className="rounded-md border border-slow/40 p-4"><summary className="cursor-pointer text-sm font-medium">What cuts against this reading</summary><p className="mt-2">{d.counterevidence || "None recorded — this indicator cannot be published until it has some."}</p></details>
      </Section>

      <Section n={num("timeline")} id="timeline" title="Timeline notes">
        <ul className="text-sm text-ink-2 flex flex-col gap-1">
          {d.points.slice(-6).reverse().map((p) => <li key={p.as_of + (p.subject ?? "")}><span className="text-muted tabular-nums">{p.as_of}</span> {p.subject ?? p.dims?.model ?? ""} · <Num p={p} unit={d.unit} obsIndex={idx} /></li>)}
        </ul>
      </Section>

      <Section n={num("history")} id="history" title="Update history"><ChangelogList events={d.status_events} obsIndex={idx} showTarget={false} /></Section>

      <Section n={num("confidence")} id="confidence" title="Confidence">
        <p><span className="num text-3xl">{d.confidence ?? "—"}</span><span className="text-muted"> / 95 — {RUBRIC(d.confidence)}</span></p>
        <p className="mt-1 text-xs text-muted">Confidence is independent of status: 90–95 multiple strong independent sources; 70–89 good evidence, some ambiguity; 50–69 mixed or hard to operationalise; below 50 limited or vague.</p>
      </Section>

      <Section n={num("related")} id="related" title="Related">
        <ul className="text-sm flex flex-col gap-1">
          {d.related_indicators.map((r) => { const c = indicators.find((i) => i.id === r); return <li key={r}><Link href={indicatorHref(r, c?.published)} className="hover:underline">{c?.name ?? r}</Link> <StatusChip status={c?.published ? c.status : null} /></li>; })}
          {d.related_bottlenecks.length ? <li className="text-ink-2">Bottlenecks {d.related_bottlenecks.map((n, i) => <span key={n}>{i ? ", " : ""}<Link href={`/bottlenecks#b${n}`} className="hover:underline">#{n}</Link></span>)} <span className="text-muted">(Narayanan &amp; Kapoor&apos;s list)</span></li> : null}
          {d.crosswalk.map((c, i) => <li key={i} className="text-ink-2">Crosswalk: <Link href={`/buckets/${c.bucket_id}`} className="hover:underline">{buckets.find((b) => b.id === c.bucket_id)?.name}</Link> ⇄ <Link href={`/layers/${c.layer_id}`} className="hover:underline">{layers.find((l) => l.id === c.layer_id)?.name}</Link> <span className="text-muted">({words(c.relation)})</span></li>)}
        </ul>
      </Section>
      </div>
    </article>
  );
}

