import Link from "next/link";
export const metadata = { title: "Methodology" };

import { skippedSources, sources } from "@/lib/data";

const TIERS: [string, string, string][] = [
  ["1", "benchmark", "Benchmark or independent evaluation (METR horizons, Epoch benchmarks)"],
  ["2", "model_release", "Model release details (system cards, technical reports)"],
  ["3", "product_behaviour", "Public product behaviour (list prices, usage data from a product)"],
  ["4", "official_filing", "Official filing or policy (SEC filings, government statistics, enacted law, regulator lists)"],
  ["5", "credible_reporting", "Credible reporting (Reuters, Bloomberg, FT, WSJ, CNBC, The Information)"],
  ["6", "published_analysis", "Published analysis with a transparent method (surveys, research notes, analyst baskets)"],
  ["7", "actor_statement", "Statement from an actor about itself (intentions and self-measurements, not outcomes)"],
];

export default function Methodology() {
  const registry: [string | null, string | null][] = [...sources().map((x) => [x.attribution, x.license] as [string | null, string | null]), ...skippedSources().map((x) => [x.attribution, null] as [string | null, string | null])];
  const credits = [...new Map(registry.filter(([a]) => a) as [string, string | null][]).entries()].map(([a, l]) => (l && /CC BY/i.test(l) ? `${a} (${l})` : a));
  return (
    <article className="prose-tight max-w-[68ch] flex flex-col gap-5 text-[17px] leading-[1.65]">
      <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">Methodology</h1>
      <p>One tracker, two lenses. The diffusion lens follows Narayanan and Kapoor&apos;s <em>AI as Normal Technology</em>: five stocks, valves between them, normal and fast bands with falsification thresholds. The capture lens measures who keeps the surplus, layer by layer. They are the same question asked from two ends, so they share one data store, one indicator object and one discipline, adapted from the <a href="https://ai2027-tracker.com/methodology/" className="underline decoration-grid underline-offset-4">AI 2027 tracker</a>.</p>
      <H>Three layers, strictly separated</H>
      <p><strong>Observation</strong> (raw, sourced, dated) → <strong>Derived</strong> (a formula over observations, defined in the semantic layer) → <strong>Indicator</strong> (proxies, status, confidence, evidence, counterevidence). No derived number exists without a traceable path to observation ids, and the site never computes a number: every figure was exported with the ids behind it.</p>
      <H>Evidence tiers</H>
      <div className="overflow-x-auto"><table className="data w-full text-sm"><thead><tr><th scope="col">Tier</th><th scope="col">Name in the data</th><th scope="col">What it covers</th></tr></thead>
        <tbody>{TIERS.map(([n, key, what]) => <tr key={n}><td className="tabular-nums">{n}</td><td><code className="text-xs">{key}</code></td><td className="text-ink-2">{what}</td></tr>)}</tbody></table></div>
      <p>The tier is stored; the letter grade is derived for display. A = tier 1, or tier 4 audited or government statistics. B = tiers 2–3, tier 4 company statements (8-K), tier 6 with a transparent method. C = tier 5, or tier 6 estimates. D = tier 7 or single-source. Tier 7 evidence never moves a status above <em>emerging</em>. <em>Audited</em> is reserved for tier 4 and a 10-K; a run-rate reported by the press or by the company is never audited, whatever its tier.</p>
      <H>Status vocabularies</H>
      <p>Flow indicators (diffusion): consistent with normal · faster than normal · slower than normal · emerging · not yet measurable, each against a normal band, a fast band and an optional falsifying band with a written rationale. Capture indicators: concentrating · dispersing · stable · unclear, from a trend over N periods with a dead-band. Every indicator also carries a timing tag: <em>leading</em> (moves before capture shows in filings), <em>coincident</em> (moves with it) or <em>lagging</em> (confirms it after the fact). Predictions: confirmed · ahead · on track · behind · emerging · not yet testable. <em>Not yet measurable</em> means the thing cannot be measured yet; an indicator whose connector has not landed is simply unpublished.</p>
      <H>Bands</H>
      <p>Each diffusion indicator names the single series or derived metric its bands apply to (shown as &ldquo;applied to&rdquo; on the indicator page), a normal band anchored on the pace of an earlier general-purpose technology at the same age, a fast band anchored on the pace the AI 2027 scenario needs, and where one exists a falsifying threshold. The rationale is written next to the numbers. Bands change only through a reviewed pull request that states why; the evaluator never moves them.</p>
      <H>Confidence, 0–95, independent of status</H>
      <p>90–95 multiple strong independent sources; 70–89 good evidence with some ambiguity; 50–69 mixed or hard to operationalise; below 50 limited or vague.</p>
      <H>Discipline, enforced in code</H>
      <ul className="list-disc pl-5">
        <li>Every observation carries a URL that resolved at ingestion, its HTTP status, a content hash, the retrieval time, the tier, an audited/company-stated/reported/estimated flag, the extraction method and the raw snippet.</li>
        <li>Figures quoted from documents enter through a manual connector that fetches the page and asserts the snippet is a verbatim substring of it. Nothing is typed into an indicator.</li>
        <li>No single-source status change unless the source is a benchmark, a model release or an official filing. Non-empty counterevidence before anything publishes.</li>
        <li>Status lives only in status events, each with a reason, evidence ids and an author. The changelog is generated from them. Observations are superseded, never deleted; disputed figures carry their dispute text everywhere they appear.</li>
        <li>The evaluator proposes; it writes its own reason only for a first reading inside a band, and a band crossing waits for a human. Bands and formulas change only through a reviewed pull request.</li>
        <li>Rebuilt nightly at 06:17 UTC into a pull request that merges itself when the consistency checks, the tests and the site build all pass on exactly what it built; a failure holds it for review. What merges that way was decided by a published rule: observations that passed their source&apos;s checks, and first readings inside a band. A band crossing still waits for a human-written reason, and the card says so meanwhile.</li>
        <li>Fetched HTML passes through a prompt-injection scrub; anything addressed to an AI agent is logged and never stored.</li>
      </ul>
      <H>Query layer</H>
      <p>The Ask button and the console on <Link href="/query" className="underline decoration-grid underline-offset-4">/query</Link> run against the same store the site is exported from, on a separate read-only service. A question goes to a model with four tools (read-only SQL over the semantic layer, a metric lookup, an indicator lookup, and status changes since a date). Every number in an answer must be followed by the citation token of the record it came from; a post-check extracts the numbers and verifies each against that record&apos;s value, confidence bounds, band edges or verbatim snippet. An answer that fails is revised once and otherwise shown as blocked with the unverified numbers marked. The service cannot write observations or statuses, has a daily spend cap, and logs only a hash of each question and the ids of the records its answer cited. The model and prompt version are recorded with every answer.</p>
      <H>Weekly memo</H>
      <p>Each Monday a job assembles what changed since the last memo (status events, new observations by indicator, watchlist posts, staleness, the thesis monitor, and any crosswalk pair whose two sides moved in opposite directions) and asks a model to draft the memo and the two lens sentences under the same citation rule. If no key is configured or the check fails twice, the memo is the deterministic digest of the same facts. Either way it opens a pull request; merging it publishes the memo under <Link href="/memos" className="underline decoration-grid underline-offset-4">/memos</Link>. Nothing in a memo can move a status.</p>
      <H>X posts</H>
      <p>X is never scraped. Posts enter through a curated List on the X API, or through a weekly manual drop of URLs fetched via X&apos;s public embed endpoint. Every post is tier 7 and recorded as a watchlist row; when a post links to a tier 1&ndash;6 artifact, the artifact is fetched and entered as an observation in its own right. Posts never move a status.</p>
      <H>Colour</H>
      <p>Two accents mark direction (faster or concentrating; slower or dispersing) and always ship with an icon and a word. Nothing is red or green: fast is not good, and concentrating is not good.</p>
      <H>Credits</H>
      <p>Method after the <a href="https://ai2027-tracker.com/methodology/" className="underline decoration-grid underline-offset-4">AI 2027 tracker</a> (independent, not affiliated).</p>
      <p className="text-sm text-ink-2">Data credits, generated from the source registry: {credits.join("; ")}.</p>
      <H id="reuse">Reuse, citation and corrections</H>
      <p>Code is MIT licensed. The compiled dataset (observations, derived values, status events) is CC BY 4.0; each observation also carries its upstream source and licence, which govern that row. Cite the site by URL and the observation ids you rely on. Corrections: open an issue or pull request on the repository; every change to a number or a status leaves a dated event in the changelog.</p>
      <H id="privacy">Privacy</H>
      <p>Slow Variables sets no cookies and runs no analytics; the only thing its code stores in your browser is your theme, and only once you pick one. Scripts, fonts and images all come from this site, and its content security policy blocks third-party ones. What you type into Ask or the query console goes through this site&apos;s server to a separate query service on Fly.io; Ask questions, with the path of the page you asked from, then go to Anthropic&apos;s API to draft the answer. That service sees this site&apos;s server, not your browser, and logs a short hash of each question with its outcome, cost, number of lookups and the ids of the records it cited; it never logs what you typed. Vercel, which hosts the site, keeps standard request logs (such as IP address and user agent) under its own policy, and Anthropic handles questions under its commercial terms, so leave personal details out of what you ask.</p>
      <H id="disclaimers">Disclaimers</H>
      <ul className="list-disc pl-5 flex flex-col gap-2">
        <li><strong className="font-medium">Not advice.</strong> Nothing on Slow Variables is investment, financial, legal or career advice, or a recommendation to buy, sell or hold anything.</li>
        <li><strong className="font-medium">Third-party figures.</strong> Figures are shown as the sources beside them published them. The pipeline records where each came from and checks quoted text against the page; it cannot vouch for the number itself, and the data comes as is, without warranty.</li>
        <li><strong className="font-medium">AI-written text.</strong> Ask answers, and the prose of memos marked as model-drafted, are written by an AI model. The citation check confirms that each number matches the record it cites, not that the sentence around it is right, so a checked answer can still be wrong.</li>
        <li><strong className="font-medium">Statuses.</strong> A status is an editorial judgement made under published rules: the maintainer chooses the bands and direction rules, writes down the rationale, and changes them only through a reviewed pull request.</li>
        <li><strong className="font-medium">Conflicts.</strong> The maintainer is involved with a private value-chain map, a firm in the deployment-services sub-layer; that sub-layer is listed and its indicators are held to the same rules.</li>
      </ul>
    </article>
  );
}

function H({ children, id }: { children: React.ReactNode; id?: string }) { return <h2 id={id} className="display text-2xl leading-tight border-t border-grid pt-5 mt-2 scroll-mt-6">{children}</h2>; }
