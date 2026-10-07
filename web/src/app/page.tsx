import Link from "next/link";
import { Fact } from "@/components/Fact";
import { Inline, parseEssay } from "@/components/Essay";
import { FourPlacesCompact } from "@/components/FourPlaces";
import { StatusChip } from "@/components/StatusChip";
import { argument, changelog, index, meta, outlook } from "@/lib/data";
import { PHASE_WORDS } from "@/lib/format";
import { ACTS } from "@/lib/nav";
import { SITE } from "@/lib/site";

export const metadata = { title: { absolute: `${SITE.name} · how fast AI lands, and who keeps the value` } };

const card = "flex flex-col gap-3 rounded-[4px] border border-grid bg-surface p-5";
const more = "mt-auto text-sm font-medium underline decoration-axis underline-offset-4 hover:decoration-ink";

// The front door: the claim, three readings of it, what changed, and the path. The full essay is stop 1.
export default function Home() {
  const doc = argument();
  const { title, lede } = parseEssay(doc.essay.home);
  const names = Object.fromEntries(index().indicators.map((c) => [c.id, c.name]));
  const latest = changelog().filter((e) => e.target_type !== "prediction" && names[e.target_id]).slice(0, 3);
  const first = ACTS[0].stops[0];
  return (
    <div className="flex flex-col gap-12 md:gap-16">
      <header className="flex max-w-[56rem] flex-col gap-4 pt-2 md:pt-6">
        <div className="eyebrow">How fast AI lands, and who keeps the value</div>
        <h1 className="display text-[2.75rem] leading-[0.98] md:text-[4.5rem]">{title}</h1>
        <p className="max-w-[62ch] font-serif text-xl leading-[1.55] text-ink-2 md:text-[1.35rem]"><Inline text={lede} facts={doc.facts} /></p>
        <p className="font-mono text-[12px] text-muted">Readings updated {meta().generated_at.slice(0, 10)} · newest figure in the essay dated {doc.as_of}</p>
      </header>

      <section aria-labelledby="readings" className="flex flex-col gap-4">
        <h2 id="readings" className="eyebrow">Tonight&apos;s three readings</h2>
        <div className="grid items-start gap-3 md:grid-cols-3">
          <article className={card}>
            <div className="eyebrow">How fast</div>
            <p className="font-serif text-xl leading-snug">{doc.headlines.diffusion.claim}</p>
            <Link href="/diffusion" className={more}>Stop 2 · How fast →</Link>
          </article>
          <article className={card}>
            <div className="eyebrow">Who profits</div>
            <p className="font-serif text-xl leading-snug">{doc.headlines.capture.claim}</p>
            <p className="text-sm text-ink-2">The chip makers&apos; share of the stack&apos;s gross profit: <Fact f={doc.facts.chips_gp_share_now} /></p>
            <Link href="/capture" className={more}>Stop 4 · Who profits →</Link>
          </article>
          <article className={card}>
            <div className="eyebrow">Where we are, after Perez</div>
            <p className="font-serif text-xl leading-snug">{`${(PHASE_WORDS[doc.phase.state] ?? doc.phase.state).replace(/^./, (c) => c.toUpperCase())}, by the site's published rule.`}</p>
            <FourPlacesCompact shifts={outlook().shifts} />
            <Link href="/argument#perez" className={more}>How the phase is read →</Link>
          </article>
        </div>
      </section>

      {latest.length ? (
        <section aria-labelledby="changes" className="flex flex-col gap-3">
          <h2 id="changes" className="eyebrow">Latest changes</h2>
          <ol className="border-t border-grid">
            {latest.map((e) => (
              <li key={e.id} className="grid grid-cols-[6.5rem_1fr] items-baseline gap-x-3 gap-y-1 border-b border-grid py-2.5 text-[15px] md:grid-cols-[7rem_1fr_auto]">
                <span className="font-mono text-[12px] text-muted">{e.created_at.slice(0, 10)}</span>
                <Link href={`/indicators/${e.target_id}`} className="hover:underline">{names[e.target_id]}</Link>
                <span className="col-start-2 md:col-start-auto"><StatusChip status={e.new_status} /></span>
              </li>
            ))}
          </ol>
          <Link href="/changelog" className="self-start text-sm underline decoration-axis underline-offset-4 hover:decoration-ink">Every change, with its reason →</Link>
        </section>
      ) : null}

      <section aria-labelledby="path" className="flex flex-col gap-5 rounded-[4px] bg-surface-2 p-5 md:p-6">
        <h2 id="path" className="eyebrow">The path · three acts, nine stops</h2>
        <div className="grid gap-6 md:grid-cols-3">
          {ACTS.map((a) => (
            <div key={a.act} className="flex flex-col gap-3">
              <div className="eyebrow">Act {a.act} · {a.title}</div>
              <ol className="flex flex-col gap-3">
                {a.stops.map((s) => (
                  <li key={s.n} className="grid grid-cols-[2rem_1fr] gap-2">
                    <span className="num inline-flex h-6 min-w-6 items-center justify-center rounded-full border border-axis bg-surface px-1 text-[11px] text-muted">{s.n}</span>
                    <Link href={s.href} className="group"><span className="block font-semibold group-hover:underline">{s.name}</span><span className="block font-serif text-[15px] leading-snug text-ink-2">{s.question}</span></Link>
                  </li>
                ))}
              </ol>
            </div>
          ))}
        </div>
        <Link href="/story" className="self-start text-sm underline decoration-axis underline-offset-4 hover:decoration-ink">Or see the argument as a run of figures →</Link>
      </section>

      <Link href={first.href} className="group block max-w-3xl rounded-[4px] bg-ink p-6 text-background md:p-8">
        <span className="eyebrow text-background/70">Start the path · stop {first.n} · Act I</span>
        <span className="mt-2 block display text-2xl md:text-3xl">{first.name} <span aria-hidden className="inline-block transition-transform group-hover:translate-x-1">→</span></span>
        <span className="mt-2 block font-serif text-lg text-background/80">{first.question}</span>
      </Link>
    </div>
  );
}
