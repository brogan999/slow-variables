import Link from "next/link";
import { indicatorHref } from "@/lib/format";
import { ConfidenceBar, rubricWords } from "@/components/ConfidenceBar";
import { EvidenceLog } from "@/components/EvidenceLog";
import { Callout } from "@/components/Figure";
import { TimeChart } from "@/components/TimeChart";
import { ChangelogList } from "@/components/Changelog";
import { Num, ObsLinks } from "@/components/Provenance";
import { ArticleLayout, MarginPanel } from "@/components/ArticleLayout";
import { Grade, PendingNote, StatusChip } from "@/components/StatusChip";
import { fmt, index, indicator, meta, obsIndex, sources, words, type Band } from "@/lib/data";

export const dynamicParams = false;
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const d = indicator(slug);
  return { title: d.name, description: d.definition };
}
export function generateStaticParams() { return index().indicators.filter((i) => i.published).map((i) => ({ slug: i.id })); }

const band = (b: Band, unit: string) => (b ? [b.lo != null ? `≥ ${fmt(b.lo, unit)}` : null, b.hi != null ? `≤ ${fmt(b.hi, unit)}` : null].filter(Boolean).join(" and ") : "—");

// Seed prose sometimes names a status as a `code_word`; readers see the word.
const plain = (t: string | null | undefined) => (t ?? "").replace(/`([a-z_]+)`/g, (_, w: string) => w.replace(/_/g, " "));

function H2({ id, children }: { id: string; children: React.ReactNode }) {
  return <h2 id={id} className="display text-[1.5rem] md:text-[1.75rem] leading-tight mb-4 scroll-mt-8">{children}</h2>;
}

export default async function IndicatorPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const d = indicator(slug);
  const idx = obsIndex();
  const { buckets, layers, indicators } = index();
  const srcs = sources();
  const rubric = meta().confidence_rubric;
  const bandUnit = d.band_value?.unit ?? d.unit;
  const current = d.status_events[0];
  const seriesSources = (d.source_ids ?? []).map((id) => srcs.find((s) => s.id === id)).filter(Boolean);
  return (
    <ArticleLayout
      head={
        <header className="flex flex-col gap-3">
          <p className="eyebrow">
            {d.bucket_id ? <Link href={`/buckets/${d.bucket_id}`} className="hover:text-ink">{buckets.find((b) => b.id === d.bucket_id)?.name}</Link> : null}
            {d.bucket_id && d.layer_id ? " · " : null}
            {d.layer_id ? <Link href={`/layers/${d.layer_id}`} className="hover:text-ink">{layers.find((l) => l.id === d.layer_id)?.name}</Link> : null}
          </p>
          <h1 className="display text-[2.25rem] md:text-[3.25rem] leading-[1.04] max-w-[24ch]">{d.name}</h1>
          <p className="font-serif text-lg md:text-xl leading-relaxed text-ink-2 max-w-[62ch]">{d.definition}</p>
        </header>
      }
      margin={
        <>
          <MarginPanel title="Reading">
            <div className="flex flex-col gap-3">
              <div className="self-start"><StatusChip status={d.published ? d.status : "unpublished"} size="lg" /></div>
              {d.pending ? <PendingNote p={d.pending} /> : null}
              {d.stale_as_of ? <p className="text-error">stale since {d.stale_as_of}</p> : null}
              {d.stale_reason ? <p className="text-muted">refreshed irregularly: {d.stale_reason}</p> : null}
              <div><div className="text-muted text-xs">Latest</div><div className="text-base text-ink"><Num p={d.latest} unit={d.unit} obsIndex={idx} /></div></div>
              {d.band_value ? <div><div className="text-muted text-xs">What the rule reads</div><div className="text-base text-ink"><Num p={{ as_of: d.band_value.as_of ?? "", value: d.band_value.value, low: d.band_value.low, high: d.band_value.high, obs_ids: d.band_value.obs_ids }} unit={bandUnit} obsIndex={idx} /></div></div> : null}
            </div>
          </MarginPanel>
          <MarginPanel title="The rule">
            {d.normal_band ? <p>Normal {band(d.normal_band, bandUnit)}; fast {band(d.fast_band, bandUnit)}{d.falsifying_band ? `; falsifying ${band(d.falsifying_band, bandUnit)}` : ""}. Between them it reads emerging.</p> : null}
            {d.direction_rule ? <p>Direction over {d.direction_readings} readings; moves under {fmt(d.direction_rule.dead_band, d.unit)} count as stable; higher means {d.direction_rule.higher_is}.</p> : null}
            <p className="flex items-center gap-3"><ConfidenceBar value={d.confidence} rubric={rubric} /><span>Confidence {d.confidence ?? "—"} of 95: {rubricWords(d.confidence, rubric)}. <Grade grade={d.grade} /></span></p>
            {d.leading_lagging ? <p>{d.timing_rationale}</p> : null}
            <p className="text-muted">Updated {d.updated_at}</p>
          </MarginPanel>
        </>
      }
    >
      <div className="flex flex-col gap-14">
        <section>
          <H2 id="reading">The reading</H2>
          <p className="font-serif text-[1.0625rem] leading-relaxed mb-6">{plain(d.tracker_interpretation)}</p>
          <TimeChart d={d} />
          {d.override_note ? <div className="mt-3"><Callout label="Held by an override note"><p className="text-sm text-ink-2">{d.override_note}</p></Callout></div> : null}
        </section>

        <section>
          <H2 id="why">Why it matters</H2>
          <div className="prose-folio"><p>{plain(d.why_it_matters)}</p></div>
        </section>

        <section>
          <H2 id="against">What cuts against it</H2>
          <div className="prose-folio"><p>{plain(d.counterevidence) || "None recorded; this indicator cannot be published until it has some."}</p></div>
          {d.evidence.length ? <div className="mt-6"><EvidenceLog items={d.evidence} /></div> : null}
        </section>

        <section className="border-t border-grid pt-6 flex flex-col gap-4">
          <details id="track">
            <summary className="cursor-pointer display text-xl">How it is measured</summary>
            <ul className="mt-3 text-sm flex flex-col gap-1">
              {d.series_keys.map((k) => <li key={k}><span className="text-muted">series</span> <code className="text-xs">{k}</code></li>)}
              {d.metric ? <li><span className="text-muted">derived metric</span> <code className="text-xs">{d.metric}</code> <span className="text-muted">(formula in the semantic layer)</span></li> : null}
              {seriesSources.map((s) => s ? <li key={s.id}><span className="text-muted">source</span> <a href={s.url} className="underline decoration-axis underline-offset-4">{s.name}</a> <span className="text-muted">· default tier {s.default_tier} · {s.license}</span></li> : null)}
              <li><span className="text-muted">proxy</span> {d.proxy_types.join(", ")} · <span className="text-muted">cadence</span> {words(d.cadence_expected)}{d.valve_measured ? <> · <span className="text-muted">valve</span> {words(d.valve_measured)}</> : null}</li>
            </ul>
            <p className="mt-3 text-sm text-ink-2 max-w-[75ch]">{d.band_rationale ?? d.direction_rule?.rationale}</p>
            {d.band_input ? <p className="mt-1 text-xs text-muted">Applied to <code>{d.band_input}</code>.</p> : null}
            {d.proposed_status && d.proposed_status !== d.status && !d.override_note ? <p className="mt-2 text-xs text-ink-2">The tracker&apos;s prior expectation was <em>{words(d.proposed_status)}</em>; the evaluator reads <em>{words(d.status)}</em>. The evaluator wins until a reviewed override.</p> : null}
            {d.fits?.length ? (
              <div className="mt-4 overflow-x-auto">
                <div className="text-xs text-muted mb-1">Model comparison (lower AIC fits better; both on ln(horizon) residuals)</div>
                <table className="data w-full text-xs"><thead><tr><th scope="col">fit</th><th scope="col">estimate</th><th scope="col">95% interval</th><th scope="col">n</th><th scope="col">R²</th><th scope="col">AIC</th><th scope="col">inputs</th></tr></thead><tbody>
                  {d.fits.map((f) => { const show = (v: number | null) => fmt(v, f.unit ?? "days"); return (
                    <tr key={f.metric}><td><code>{f.metric}</code></td><td className="tabular-nums">{show(f.value)}</td><td className="tabular-nums">{show(f.value_low)}–{show(f.value_high)}</td><td className="tabular-nums">{f.dims.n}</td><td className="tabular-nums">{f.dims.r2}</td><td className="tabular-nums">{f.dims.aic}</td><td><ObsLinks ids={f.obs_ids} obsIndex={idx} max={2} /></td></tr>
                  ); })}
                </tbody></table>
              </div>
            ) : null}
            {d.derived.length ? <details className="mt-3 text-xs"><summary className="cursor-pointer text-ink-2">Derived rows ({d.derived.length})</summary>
              <div className="overflow-x-auto"><table className="data w-full mt-1"><thead><tr><th scope="col">as of</th><th scope="col">dims</th><th scope="col">value</th><th scope="col">inputs</th></tr></thead><tbody>
                {d.derived.slice().reverse().map((r) => <tr key={r.id} id={`d-${r.id}`} className="scroll-mt-24 target:bg-surface-2"><td>{r.as_of_date}</td><td>{Object.values(r.dims ?? {}).join(" ")}</td><td className="tabular-nums">{fmt(r.value, d.unit)}</td><td><ObsLinks ids={r.obs_ids} obsIndex={idx} max={3} /></td></tr>)}
              </tbody></table></div></details> : null}
          </details>
          <details id="timeline">
            <summary className="cursor-pointer display text-xl">Latest readings</summary>
            <ul className="mt-3 text-sm text-ink-2 flex flex-col gap-1">
              {d.points.slice(-6).reverse().map((p) => <li key={p.as_of + (p.subject ?? "")}><span className="text-muted tabular-nums">{p.as_of}</span> {p.subject ?? p.dims?.model ?? ""} · <Num p={p} unit={d.unit} obsIndex={idx} /></li>)}
            </ul>
          </details>
          <details id="history">
            <summary className="cursor-pointer display text-xl">Why this status, and its history</summary>
            {current ? <p className="mt-3 text-sm text-ink-2 max-w-[75ch]">{current.reason}</p> : <p className="mt-3 text-sm text-muted">No status yet; the evaluator proposes one once an approved observation exists.</p>}
            <div className="mt-3"><ChangelogList events={d.status_events} obsIndex={idx} showTarget={false} /></div>
          </details>
          <details id="confidence">
            <summary className="cursor-pointer display text-xl">Why this confidence</summary>
            {d.confidence_basis ? (
              <p className="mt-3 text-sm text-ink-2">
                Rests on {d.confidence_basis.n_observations} observation{d.confidence_basis.n_observations === 1 ? "" : "s"} from {d.confidence_basis.sources.join(", ") || "no source"}
                {d.confidence_basis.best_tier ? <>; best evidence tier {d.confidence_basis.best_tier}, grade {d.confidence_basis.grade}</> : null}
                {d.confidence_basis.stale_as_of ? <>; stale since {d.confidence_basis.stale_as_of}</> : <>; current</>}.
              </p>
            ) : null}
            <p className="mt-1 text-xs text-muted">Confidence is independent of status: {rubric.slice().reverse().map((b) => `${b.lo}–${b.hi} ${b.label}`).join("; ")}.</p>
          </details>
          <details id="related">
            <summary className="cursor-pointer display text-xl">Related</summary>
            <ul className="mt-3 text-sm flex flex-col gap-1">
              {d.related_indicators.map((r) => { const c = indicators.find((i) => i.id === r); return <li key={r}><Link href={indicatorHref(r, c?.published)} className="hover:underline">{c?.name ?? r}</Link> <StatusChip status={c?.published ? c.status : "unpublished"} /></li>; })}
              {d.related_bottlenecks.length ? <li className="text-ink-2">Bottlenecks {d.related_bottlenecks.map((n, i) => <span key={n}>{i ? ", " : ""}<Link href={`/bottlenecks#b${n}`} className="hover:underline">#{n}</Link></span>)} <span className="text-muted">(Narayanan &amp; Kapoor&apos;s list)</span></li> : null}
              {d.prediction_rows?.map((p) => <li key={p.id} className="text-ink-2">Prediction: <Link href={`/predictions#${p.id}`} className="hover:underline">{p.claimant}</Link> <span className="text-muted">({p.ledger === "nk" ? "Narayanan and Kapoor" : p.ledger === "ai2027" ? "AI 2027" : p.ledger === "lab" ? "lab timelines" : "capture theses"})</span> <StatusChip status={p.status} /></li>)}
              {d.crosswalk.map((c, i) => <li key={i} className="text-ink-2">Crosswalk: <Link href={`/buckets/${c.bucket_id}`} className="hover:underline">{buckets.find((b) => b.id === c.bucket_id)?.name}</Link> ⇄ <Link href={`/layers/${c.layer_id}`} className="hover:underline">{layers.find((l) => l.id === c.layer_id)?.name}</Link> <span className="text-muted">({words(c.relation)})</span></li>)}
            </ul>
          </details>
        </section>
      </div>
    </ArticleLayout>
  );
}
