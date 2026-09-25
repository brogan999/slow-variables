import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { SITE } from "@/lib/site";

export const metadata = {
  title: "Legal notice",
  description: "Who runs Slow Variables, what it is and is not, how its data and words may be used, and how it handles the little it records.",
};

const CHANGED = "24 September 2026"; // bump with every change to this page; the history is in the repository
const link = "underline decoration-axis underline-offset-2 hover:decoration-ink";

function H({ id, children }: { id: string; children: React.ReactNode }) {
  return <h2 id={id} className="display text-[1.4rem] leading-tight mt-10 mb-3 scroll-mt-24">{children}</h2>;
}

export default function Legal() {
  const issues = <a href={`${SITE.repo}/issues`} className={link}>an issue on the public repository</a>;
  const email = <a href={`mailto:${SITE.legalEmail}`} className={link}>{SITE.legalEmail}</a>;
  return (
    <div className="flex flex-col">
      <PageHeader eyebrow="Legal" title="Legal notice" lede={`What ${SITE.name} is, what it is not, and the terms on which you use it. By using the site you accept this notice. Last changed ${CHANGED}.`} />
      <article className="prose-folio max-w-[70ch]">
        <nav aria-label="On this page" className="text-sm text-ink-2 not-prose">
          <ol className="columns-2 gap-8 list-decimal pl-5">
            {[["operator", "Who runs this site"], ["advice", "Not advice"], ["forecasts", "Predictions and forward-looking content"], ["warranty", "Accuracy and no warranty"], ["ai", "AI-generated content"], ["sources", "Sources, quotation and removal"], ["licences", "Licences"], ["links", "Links, names and trademarks"], ["conflicts", "Conflicts of interest"], ["use", "Acceptable use"], ["liability", "Limitation of liability"], ["privacy", "Privacy"], ["accessibility", "Accessibility"], ["general", "General terms and governing law"]].map(([id, t]) => <li key={id}><a href={`#${id}`} className={link}>{t}</a></li>)}
          </ol>
        </nav>

        <H id="operator">Who runs this site</H>
        <p>{SITE.name} ({SITE.url}) is an independent, non-commercial research site run by {SITE.operator}. It is not affiliated with, sponsored by or endorsed by any company, laboratory, publication or data provider it covers, and the operator takes no payment from them. General questions and corrections go through {issues}; privacy requests and copyright or trademark notices go privately to {email}. There is no promised response time.</p>

        <H id="advice">Not advice</H>
        <p>Nothing on this site is investment, financial, legal, tax, accounting, medical, career or other professional advice, a recommendation, or an offer or solicitation to buy or sell anything. Commentary here is general and impersonal: it is written for no particular reader and takes no account of anyone&apos;s circumstances. Using the site creates no adviser, fiduciary, client or other professional relationship. Make your own decisions, and take advice from a qualified professional who knows your situation before acting.</p>

        <H id="forecasts">Predictions and forward-looking content</H>
        <p>Much of the site is about the future: forecasts, predictions, scenarios, expected dates, tightness scores, rent tiers and statuses. These are views about uncertain events, whether other people&apos;s (reworded and credited), this site&apos;s own, or judgements made by AI models under published rules. None is a promise or a guarantee. Actual outcomes can differ widely, a reading that fits a view today can stop fitting tomorrow, and statuses and scores change as data arrives.</p>

        <H id="warranty">Accuracy and no warranty</H>
        <p>Figures are shown as their sources published them and are collected by automated pipelines that can fail, lag or misread a source. The operator checks what can be checked but cannot vouch for any figure, quotation or source. The site, its data, its answers and its downloads are provided &ldquo;as is&rdquo; and &ldquo;as available&rdquo;, without warranties of any kind, express or implied, including accuracy, completeness, timeliness, merchantability, fitness for a particular purpose and non-infringement, to the fullest extent the law allows.</p>

        <H id="ai">AI-generated content</H>
        <p>Parts of this site are written or judged by AI models, and are labelled where they appear. Ask answers are written by an Anthropic model; the site checks that each number matches the record it cites, not that the sentence around it is right, so a checked answer can still be wrong. Weekly memos marked as model-drafted, reworded summaries of sources, and model-judged fields (such as dates, categories, verdicts and rubric scores) can contain errors. The illustrations are made with image models, named in each caption, and are not evidence of anything. Much of the site&apos;s code and wording was drafted with AI assistance and reviewed by the operator.</p>

        <H id="sources">Sources, quotation and removal</H>
        <p>Every figure names its source. Books, papers and newsletters, including paid ones, are reworded in this site&apos;s words and credited to their authors, and exact quotations are kept short, for the purposes of commentary, criticism and research. Lists compiled by others (for example the science-fiction inventions catalogued by Technovelgy and compiled by Not Boring) are credited wherever they are used. If you hold rights in something used here and object to its use, write to {email} with the page, the material and your claim; the operator will review promptly and remove or correct material where that is right. This site does not host content uploaded by users.</p>

        <H id="licences">Licences</H>
        <p>The site&apos;s code is under the MIT licence. The operator&apos;s own contributions to the compiled dataset (observations as recorded, derived values, statuses, scores and the site&apos;s own writing) are under Creative Commons Attribution 4.0 (CC BY 4.0). That licence does not cover third-party material: figures and quotations remain under their sources&apos; own terms, listed on <Link href="/sources" className={link}>the sources page</Link>, and reworded source content and third-party selections (such as the Technovelgy list) are not licensed to you by this site. Fonts are under the SIL Open Font Licence. See <Link href="/methodology#reuse" className={link}>reuse and citation</Link> for how to credit the data.</p>

        <H id="links">Links, names and trademarks</H>
        <p>Links to other sites are for reference only. The operator does not control them, is not responsible for their content, availability or practices, and does not endorse them by linking. Company, product, model and publication names and logos belong to their owners; their appearance here identifies them and implies no affiliation, sponsorship or endorsement.</p>

        <H id="conflicts">Conflicts of interest</H>
        <p>The operator may hold investments in, work with, or have relationships with companies, assets or people mentioned on this site, and may buy or sell such investments at any time. Nothing here is written to promote or disparage any of them. Where a cited writer has disclosed an interest, the site notes it beside their work.</p>

        <H id="use">Acceptable use</H>
        <p>You may read, cite and reuse the site under the licences above. Do not use Ask or the query console for scraping, bulk or automated querying, load testing, attempts to break security, or anything unlawful; do not put personal or confidential information into them. The operator may limit, suspend or withdraw access to any part of the site, including Ask and the query console, at any time and without notice. The site may change, lose data or go offline at any time. Using it creates no contract for services.</p>

        <H id="liability">Limitation of liability</H>
        <p>To the fullest extent the law allows, the operator is not liable for any loss or damage of any kind, whether direct, indirect, incidental, special, consequential or punitive, including lost profits, data, savings or opportunities, arising from or connected with the site, its data, its answers or its downloads, or your reliance on any of them, however caused and even if the operator was told such loss was possible. Where liability cannot be excluded, it is limited to the smallest amount the law allows. Nothing here excludes liability that cannot lawfully be excluded, and nothing here takes away rights you have under consumer law where you live.</p>

        <H id="privacy">Privacy</H>
        <p><strong className="font-medium">What the site stores about you: nothing in your browser.</strong> It sets no cookies, runs no analytics or advertising, and stores nothing on your device. Scripts, fonts and images all come from this site, and its content security policy blocks third-party ones.</p>
        <p><strong className="font-medium">Hosting.</strong> Vercel hosts the site and, like any web host, keeps standard request logs (such as IP address, user agent and the page requested) under its own policy and retention periods.</p>
        <p><strong className="font-medium">Ask and the query console.</strong> What you type goes through this site&apos;s server to a separate query service on Fly.io. Ask questions, with the path of the page you asked from and the last few questions and answers of the same conversation (which the page holds only in its memory, and forgets when you leave or reload it), then go to Anthropic&apos;s API, which drafts the answer under Anthropic&apos;s commercial terms. The query service sees this site&apos;s server, not your browser. It records each answer&apos;s time, outcome, cost, number of lookups, the ids of the records it cited, the model and the prompt version, and the nightly publishes those records in the repository. It never records what you typed, or a hash of it. If the model call fails, the service logs and returns only the kind of error, never its text. Fly.io keeps the service&apos;s logs under its own retention periods. Leave personal details out of what you ask.</p>
        <p><strong className="font-medium">Corrections and contact.</strong> Issues opened on GitHub are public and handled by GitHub as a separate controller under its own policy. Messages to {email} are read by the operator and kept only as long as needed to deal with them.</p>
        <p><strong className="font-medium">For visitors in the EU, UK and similar jurisdictions.</strong> The operator is the controller of the little personal data involved. The lawful basis is legitimate interests: running, securing and improving a free public research site. The processors are Vercel (hosting), Fly.io (the query service) and Anthropic (drafting Ask answers); image-generation services used to make illustrations receive no visitor data. These providers are in the United States, and data they handle may be processed there. You can ask for access to, correction of or erasure of personal data, or object to its use, by writing to {email}; because the site keeps almost nothing that identifies you, there is usually little to find. You may also complain to your data-protection authority.</p>
        <p><strong className="font-medium">Children.</strong> The site is not aimed at children under 13 (under 16 in the EU and UK) and does not knowingly collect their data.</p>

        <H id="accessibility">Accessibility</H>
        <p>The site aims to meet WCAG 2.2 level AA; pages are checked with automated accessibility tests at phone and desktop widths when they change. If something is hard to use, tell us through {issues} or at {email}.</p>

        <H id="general">General terms and governing law</H>
        <p>This notice is governed by the laws of the State of California, United States, without regard to conflict-of-law rules, and the courts of California have jurisdiction, except where the law of the country you live in gives you rights that cannot be displaced. If any part of this notice is found unenforceable, the rest still applies. A failure to enforce any part is not a waiver of it. The operator may change this notice at any time by publishing a new version here; its full history is in <a href={SITE.repo} className={link}>the repository</a>, and the date at the top says when it last changed.</p>
      </article>
    </div>
  );
}
