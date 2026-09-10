const TIERS = ["Benchmark or independent evaluation", "Model release details (system cards, technical reports)", "Public product behaviour", "Official filing or policy (SEC filings, enacted law, regulator lists)", "Credible reporting (Reuters, Bloomberg, FT, WSJ, The Information)", "Published analysis with transparent method", "Statement from an actor (intentions, not outcomes)"];

export default function Methodology() {
  return (
    <article className="prose-tight max-w-3xl flex flex-col gap-6 text-[15px] leading-relaxed">
      <h1 className="text-2xl font-semibold tracking-tight">Methodology</h1>
      <p>One tracker, two lenses. The diffusion lens follows Narayanan and Kapoor&apos;s <em>AI as Normal Technology</em>: five stocks, valves between them, normal and fast bands with falsification thresholds. The capture lens measures who keeps the surplus, layer by layer. They are the same question asked from two ends, so they share one data store, one indicator object and one discipline, adapted from the <a href="https://ai2027-tracker.com/methodology/" className="underline decoration-grid underline-offset-4">AI 2027 tracker</a>.</p>
      <H>Three layers, strictly separated</H>
      <p><strong>Observation</strong> (raw, sourced, dated) → <strong>Derived</strong> (a formula over observations, defined in the semantic layer) → <strong>Indicator</strong> (proxies, status, confidence, evidence, counterevidence). No derived number exists without a traceable path to observation ids, and the site never computes a number: every figure was exported with the ids behind it.</p>
      <H>Evidence tiers</H>
      <ol className="list-decimal pl-5">{TIERS.map((t, i) => <li key={i}>{t}</li>)}</ol>
      <p>The tier is stored; the letter grade is derived for display. A = tier 1, or tier 4 audited or government statistics. B = tiers 2–3, tier 4 company statements (8-K), tier 6 with a transparent method. C = tier 5, or tier 6 estimates. D = tier 7 or single-source. Tier 7 evidence never moves a status above <em>emerging</em>; <em>audited</em> is reserved for tier 4 and a 10-K.</p>
      <H>Status vocabularies</H>
      <p>Flow indicators (diffusion): consistent with normal · faster than normal · slower than normal · emerging · not yet measurable, each against a normal band, a fast band and an optional falsifying band with a written rationale. Capture indicators: concentrating · dispersing · stable · unclear, from a trend over N periods with a dead-band, plus a leading/lagging tag. Predictions: confirmed · ahead · on track · behind · emerging · not yet testable. <em>Not yet measurable</em> means the thing cannot be measured yet; an indicator whose connector has not landed is simply unpublished.</p>
      <H>Confidence, 0–95, independent of status</H>
      <p>90–95 multiple strong independent sources; 70–89 good evidence with some ambiguity; 50–69 mixed or hard to operationalise; below 50 limited or vague.</p>
      <H>Discipline, enforced in code</H>
      <ul className="list-disc pl-5">
        <li>Every observation carries a URL that resolved at ingestion, its HTTP status, a content hash, the retrieval time, the tier, an audited/company-stated/reported/estimated flag, the extraction method and the raw snippet.</li>
        <li>Figures quoted from documents enter through a manual connector that fetches the page and asserts the snippet is a verbatim substring of it. Nothing is typed into an indicator.</li>
        <li>No single-source status change unless the source is a benchmark, a model release or an official filing. Non-empty counterevidence before anything publishes.</li>
        <li>Status lives only in status events, each with a reason, evidence ids and an author. The changelog is generated from them. Observations are superseded, never deleted; disputed figures carry their dispute text everywhere they appear.</li>
        <li>The evaluator proposes; a human writes the reason. Bands and formulas change only through a reviewed pull request.</li>
        <li>Fetched HTML passes through a prompt-injection scrub; anything addressed to an AI agent is logged and never stored.</li>
      </ul>
      <H>Colour</H>
      <p>Two accents mark direction (faster or concentrating; slower or dispersing) and always ship with an icon and a word. Nothing is red or green: fast is not good, and concentrating is not good.</p>
      <H>Credits and conflicts</H>
      <p>Method after the AI 2027 tracker (independent, not affiliated). Data from METR (Horizon v1.1). Further sources — Epoch AI (CC BY 4.0), SEC EDGAR, BLS, Census BTOS, Stanford Digital Economy Lab, Joy Larkin&apos;s cleverhack trackers — are credited on <a href="/sources" className="underline decoration-grid underline-offset-4">Sources</a> as their connectors land. Disclosure: the maintainer is involved with a private value-chain map, a firm in the deployment-services sub-layer; that sub-layer is listed and its indicators are held to the same rules.</p>
    </article>
  );
}

function H({ children }: { children: React.ReactNode }) { return <h2 className="text-sm font-medium text-ink-2 mt-2">{children}</h2>; }
