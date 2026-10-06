import Link from "next/link";
import { ChartSources } from "@/components/ChartSources";
import { Fact } from "@/components/Fact";
import { Figure, Key } from "@/components/Figure";
import { KIND_LABEL } from "@/components/diagrams/kit";
import { Dot, Staves, TONE, Track } from "@/components/diagrams/migration";
import type { MigrationDoc, MigrationFigures } from "@/lib/data";
import { WITHHELD_WORDS } from "@/lib/format";

const link = "underline decoration-axis underline-offset-2 hover:decoration-ink";

function ChainPanel({ s }: { s: MigrationFigures["chain"]["states"][number] }) {
  const short = s.links.find((x) => x.shortest)?.label ?? "";
  return (
    <div className="flex flex-col gap-2">
      <div className="font-sans text-[13px] font-semibold leading-snug text-ink md:min-h-[2.6em]">{s.title}</div>
      <div className="pt-4"><Staves links={s.links} level={s.level} label={`${s.title}. Drawn shortest: ${short}.`} /></div>
      <p className="font-serif text-[13.5px] leading-snug text-ink-2">{s.text}</p>
    </div>
  );
}

// Folio I: the rule as a picture. Two states of one chain; the heights are words from the seed on a fixed scale.
export function ChainPlate({ chain }: { chain: MigrationFigures["chain"] }) {
  const [before, after] = chain.states;
  return (
    <Figure
      id="fig-chain"
      title="The scarcest input sets the pace and its owner collects the rent, until it is relieved"
      note={KIND_LABEL.model}
      keys={<>
        <Key swatch={<span aria-hidden className="inline-block h-3 w-4 bg-tight-5" />}>the bottleneck: the input there is least of</Key>
        <Key swatch={<span aria-hidden className="inline-block h-3 w-4 bg-s3" />}>what the industry can use of each input</Key>
        <Key swatch={<span aria-hidden className="inline-block h-3 w-4 bg-surface-2 ring-1 ring-inset ring-grid" />}>spare: more of it adds nothing</Key>
        <Key swatch={<span aria-hidden className="inline-block w-5 border-t border-dashed border-ink" />}>the pace</Key>
        <Key swatch={<span aria-hidden className="inline-block w-5 border-t-2 border-dotted border-tight-5" />}>where the old bottleneck stood</Key>
      </>}
      foot={<p>A drawing of the rule this folio sets out, not a measurement. The heights are a drawing choice and carry no figures, and the inputs drawn tall are not claimed to be plentiful. Chips and memory are named only to show a move of the kind the next folio records around 2023 and 2024. The real record is untidier: shortages overlapped, chips stayed short after memory ran short, and neither panel shows today. Rent is income from owning something scarce, and it goes to the input&apos;s owner. Where this site tries to read the real thing is the scorecard further down.</p>}
    >
      <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_7.5rem_minmax(0,1fr)] md:gap-4">
        <ChainPanel s={before} />
        <div className="flex md:flex-col items-center justify-center gap-2 border-y md:border-y-0 border-grid py-2 md:py-0 text-center">
          <span aria-hidden className="font-mono text-lg leading-none text-ink max-md:rotate-90">→</span>
          <span className="font-serif text-[12.5px] italic leading-snug text-ink-2">{chain.between}</span>
        </div>
        <ChainPanel s={after} />
      </div>
    </Figure>
  );
}

// Folio IV: every scored input ranked on the one scale, a stand-in score drawn apart, the unscored as hollow marks.
export function ScalePlate({ scale }: { scale: MigrationFigures["scale"] }) {
  const lines = scale.bands.slice(1).map((b) => b.x);
  const ranked = scale.rows.filter((r) => !r.hatched);
  const standIns = scale.rows.filter((r) => r.hatched);
  const grid = "sm:grid sm:grid-cols-[10.5rem_minmax(0,1fr)_6.5rem] sm:gap-x-3";
  const words = (
    <div className="relative h-4" aria-hidden>
      {scale.bands.map((b) => <span key={b.word} className="absolute top-0 text-center font-mono text-[10px] text-muted" style={{ left: `${b.x}%`, width: `${b.w}%` }}>{b.word}</span>)}
    </div>
  );
  const row = (r: MigrationFigures["scale"]["rows"][number], first: boolean) => {
    const tip = `${r.name}: ${r.score}, ${r.word}${r.hatched ? ", low confidence" : ""}`;
    return (
      <li key={r.id} className={`py-1 sm:py-0.5 sm:items-center ${grid}`}>
        <div className="flex items-baseline justify-between gap-2 text-[12.5px] leading-tight text-ink sm:justify-end sm:text-right">
          <span>{r.name}</span>
          <span className="sm:hidden whitespace-nowrap text-[12px] text-ink-2"><span className="num">{r.score}</span> · {r.word}</span>
        </div>
        <div>
          {first ? <div className="mt-1.5 sm:hidden">{words}</div> : null}
          <Track lines={lines} tall>
            <div className="absolute left-0 top-1/2 h-0.5 -translate-y-1/2" style={{ width: `${r.x}%`, background: TONE[r.word] }} aria-hidden />
            <a href={`#input-${r.id}`} data-tip={tip} aria-label={tip} title={tip} tabIndex={0} data-stop={first || undefined} className="mark absolute top-1/2 flex -translate-x-1/2 -translate-y-1/2" style={{ left: `${r.x}%` }}>
              <Dot fill={TONE[r.word]} hatched={r.hatched} />
            </a>
          </Track>
        </div>
        <div className="max-sm:hidden whitespace-nowrap text-[12.5px] text-ink"><span className="num">{r.score}</span> · {r.word}</div>
      </li>
    );
  };
  return (
    <Figure
      id="fig-scale"
      title="Every input on one scale, and the ones that cannot be placed on it"
      note={KIND_LABEL.chart}
      keys={<>
        {[...scale.bands].reverse().map((b) => <Key key={b.word} swatch={<Dot fill={TONE[b.word]} />}>{b.word}</Key>)}
        {standIns.length ? <Key swatch={<Dot fill={TONE.moderate} hatched />}>low confidence</Key> : null}
        <Key swatch={<Dot hollow />}>no score</Key>
      </>}
      foot={<p>Each solid mark is an input&apos;s tightness score from the scorecard below, tightest first. {standIns.length ? "A hatched mark is a score this site holds with low confidence because its gauge is a stand-in for the thing itself; it is drawn apart and is not ranked with the rest. " : null}A hollow mark is an input with no score: it has no place on the scale, so it is drawn beside it, never in the middle. Inputs that sit close together are not in a meaningful order. Each mark links to its row in the scorecard, where the gauges and their sources are.</p>}
      tableLabel="The scores"
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">Input</th><th scope="col">Tightness</th><th scope="col">Reads as</th><th scope="col">Confidence</th></tr></thead>
          <tbody>
            {scale.rows.map((r) => <tr key={r.id}><td>{r.name}</td><td className="num">{r.score}</td><td>{r.word}</td><td className="num">{r.confidence}{r.hatched ? " (low, not ranked)" : ""}</td></tr>)}
            {scale.unscored.map((u) => <tr key={u.id}><td>{u.name}</td><td colSpan={3} className="text-muted">no score</td></tr>)}
          </tbody>
        </table>
      }
    >
      <div className="font-sans">
        <div className={`max-sm:hidden ${grid}`}><div className="sm:col-start-2">{words}</div></div>
        <ul className="flex flex-col" data-marks>{ranked.map((r, i) => row(r, i === 0))}</ul>
        {standIns.length ? (
          <div className="mt-3 border-t border-grid pt-3">
            <div className={grid}><div className="mb-1 text-[11.5px] leading-tight text-ink-2 sm:col-span-2 sm:col-start-2">Low confidence: a stand-in, kept out of the ranking</div></div>
            <ul className="flex flex-col" data-marks>{standIns.map((r) => row(r, false))}</ul>
          </div>
        ) : null}
        <div className="mt-3 border-t border-grid pt-3 sm:grid sm:grid-cols-[10.5rem_minmax(0,1fr)] sm:gap-x-3">
          <div className="text-[12.5px] leading-tight text-ink sm:text-right">No score<span className="block text-[11.5px] text-ink-2"><span className="num">{scale.unscored.length}</span> of the <span className="num">{scale.total}</span> inputs</span></div>
          <ul className="mt-2 sm:mt-0 flex flex-wrap gap-x-3 gap-y-1.5">
            {scale.unscored.map((u) => (
              <li key={u.id}><a href={`#input-${u.id}`} className="inline-flex items-center gap-1.5 text-[11.5px] leading-tight text-ink-2 hover:text-ink"><Dot hollow small />{u.name}</a></li>
            ))}
          </ul>
        </div>
      </div>
    </Figure>
  );
}

// Folio III: the acquisitions tally's newest reading, one mark for each deal it counted, by buyer and quarter. One
// colour: how this site files a buyer is not a fact about the buyer.
export function DealsPlate({ deals }: { deals: MigrationFigures["deals"] }) {
  if (!deals) return null;
  const cols = "grid grid-cols-[minmax(0,6.5rem)_repeat(4,minmax(0,1fr))_1.75rem] sm:grid-cols-[11rem_repeat(4,minmax(0,1fr))_2.5rem] gap-x-1.5 sm:gap-x-3";
  const off = "bg-surface ring-1 ring-inset ring-s2";
  return (
    <Figure
      id="fig-deals"
      title="Deals announced by labs and computing companies for the companies around them, by buyer and quarter"
      note={KIND_LABEL.chart}
      keys={<>
        <Key swatch={<span aria-hidden className="inline-block h-2.5 w-2.5 bg-s2" />}>a deal, in the quarter it was announced</Key>
        {deals.buyers.some((b) => b.cells.some((c) => c.deals.some((d) => d.called_off))) ? <Key swatch={<span aria-hidden className={`inline-block h-2.5 w-2.5 ${off}`} />}>a deal its record notes was later called off; it still counts</Key> : null}
      </>}
      foot={<p>One mark for each of the <Fact f={deals.total} /> deals in this site&apos;s tally for the year to its newest searched quarter. A mark is an announcement, not a completed purchase: it may be a purchase, a hire of the team, or a licence or stake that came with the company&apos;s leaders, and a deal later called off still counts. The buyers are a mix of companies that train AI models, large technology companies that also do so, and companies that sell computing power. Do not read the totals from left to right as a trend: the tally is kept by hand from public announcements, quiet hires surface late, a quarter with more marks may only have been searched more thoroughly, and a later search can add marks to quarters already drawn. What each bought company does is written only in the notes on each record, so it is not drawn here. The figures on this page were drafted by a Claude model, made by Anthropic{deals.buyers.some((b) => b.id === "anthropic") ? ", which is one of the buyers drawn" : null}.</p>}
      tableLabel="Every deal counted"
      table={<>
        <table className="data w-full">
          <thead><tr><th scope="col">Buyer</th><th scope="col">Announced</th><th scope="col">Company (record id)</th></tr></thead>
          <tbody>
            {deals.buyers.flatMap((b) => b.cells.flatMap((c) => c.deals.map((d) => (
              <tr key={d.href}><td>{b.name}</td><td className="num whitespace-nowrap">{d.day}</td><td><Link href={d.href} prefetch={false} className={`font-mono text-[11px] ${link}`}>{d.target}</Link>{d.called_off ? <span className="text-ink-2"> later called off</span> : null}</td></tr>
            ))))}
          </tbody>
        </table>
        <ChartSources cs={deals.chart_sources} />
      </>}
    >
      <div className="font-sans" role="group" aria-label="Deals by buyer and by quarter; every mark is one deal">
        <div className={`${cols} items-end border-b border-grid pb-1.5`} aria-hidden>
          <span />
          {deals.quarters.map((q) => <span key={q.id} className="font-mono text-[10px] leading-tight text-muted">{q.months}<span className="block">{q.year}</span></span>)}
          <span className="text-right font-mono text-[10px] text-muted">all</span>
        </div>
        <div data-marks>
          {deals.buyers.map((b, bi) => (
            <div key={b.id} className={`${cols} items-center border-b border-grid/60 py-1.5`}>
              <span className="text-[12px] sm:text-[12.5px] leading-tight text-ink">{b.name}</span>
              {b.cells.map((c) => (
                <span key={c.quarter} className="flex flex-wrap gap-[3px]">
                  {c.deals.map((d, di) => {
                    const tip = `${b.name}: a deal announced ${d.day}${d.called_off ? ", later called off" : ""}`;
                    return <Link key={d.href} href={d.href} prefetch={false} data-tip={tip} aria-label={tip} title={tip} data-stop={(bi === 0 && di === 0 && c === b.cells.find((x) => x.deals.length)) || undefined} className={`mark block h-2.5 w-2.5 ${d.called_off ? off : "bg-s2"}`} />;
                  })}
                </span>
              ))}
              <span className="num text-right text-[12px] text-ink-2">{b.n}</span>
            </div>
          ))}
        </div>
        <div className={`${cols} pt-1.5`}>
          <span className="text-[12px] text-ink-2">All buyers</span>
          {deals.quarters.map((q) => <span key={q.id} className="num text-[12px] text-ink-2">{q.n}</span>)}
          <span className="num text-right text-[12px] font-semibold text-ink">{deals.total.value}</span>
        </div>
      </div>
    </Figure>
  );
}

// Folio IV: each reading's age against the age at which it stops counting, and what the scoring rule would leave.
export function AgesPlate({ ages }: { ages: MigrationFigures["ages"] }) {
  return (
    <Figure
      id="fig-ages"
      title="How old each reading is, against the age at which it stops counting"
      note={KIND_LABEL.chart}
      keys={<>
        <Key swatch={<span aria-hidden className="inline-block h-2 w-5 bg-s3" />}>a reading&apos;s age, as a share of its limit</Key>
        {ages.near ? <Key swatch={<span aria-hidden className="inline-block h-2 w-5 bg-s1" />}>near its limit: little of it left</Key> : null}
        <Key swatch={<span aria-hidden className="inline-block h-3 w-0.5 bg-muted" />}>past this fainter line, a reading is near its limit</Key>
        <Key swatch={<span aria-hidden className="inline-block h-3 w-px bg-ink" />}>the limit: older than this, the reading is dropped</Key>
      </>}
      foot={<p>Every bar is one gauge behind a score, as long as its newest reading is old; the right edge is that gauge&apos;s own age limit, which differs from gauge to gauge. A dark bar has little of its limit left. A newer reading from the publisher sends the bar back to the left. The note beside an input says what the same scoring rule gives if the dark readings lapse with nothing newer: arithmetic on today&apos;s records, not a forecast, and it does not say whether a newer reading is due. Where the note shows a higher score, that is only because a gauge drops out and the rest are left to speak alone; nothing has got tighter. Prices fetched daily have short limits, are refreshed each night, and are aged from the last fetch.</p>}
      tableLabel="The ages"
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">Input</th><th scope="col">Gauge</th><th scope="col">Reading dated</th><th scope="col">Age, of limit</th><th scope="col">Counts until</th></tr></thead>
          <tbody>
            {ages.rows.flatMap((r) => r.gauges.map((g) => (
              <tr key={`${r.id}-${g.id}`}><td>{r.name}</td><td className="min-w-[11rem]"><Link href={g.href} prefetch={false} className={link}>{g.label}</Link></td><td className="num whitespace-nowrap">{g.as_of_label}</td><td className="num whitespace-nowrap">{g.age_days} of {g.max_age_days} days</td><td className="num whitespace-nowrap">{g.last_label}</td></tr>
            )))}
          </tbody>
        </table>
      }
    >
      <div className="font-sans">
        {ages.near ? <p className="mb-3 text-[12.5px] leading-snug text-ink-2">Inputs with a score today: <span className="num text-ink">{ages.scored_now}</span>. <span className="block" />Still scored if every reading near its limit lapsed with nothing newer: <span className="num text-ink">{ages.scored_after}</span>.</p> : null}
        <div className="flex flex-col gap-3">
          {ages.rows.map((r) => {
            const near = r.gauges.some((g) => g.near);
            return (
              <div key={r.id} className="border-t border-grid pt-2">
                <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 text-[12.5px] leading-tight">
                  <span className="font-medium text-ink">{r.name}</span>
                  <span className="text-ink-2"><span className="num">{r.score}</span> · {r.word} today</span>
                  {near ? <span className="border border-ink px-1.5 py-px text-[11px] text-ink">{r.after ? <>would read <span className="num">{r.after.score}</span> · {r.after.word}</> : "score would be withheld"}</span> : null}
                </div>
                {r.gauges.map((g) => (
                  <div key={g.id} className="mt-1.5 sm:grid sm:grid-cols-[minmax(0,15rem)_minmax(0,1fr)_10.5rem] sm:items-center sm:gap-x-3">
                    <div className="text-[11.5px] leading-tight text-ink-2">{g.label}</div>
                    <div className="relative mt-1 h-2.5 border-r border-ink bg-surface-2 sm:mt-0" title={`${g.label}: ${g.age_days} of ${g.max_age_days} days`}>
                      <div className={`absolute inset-y-0 left-0 ${g.near ? "bg-s1" : "bg-s3"}`} style={{ width: `max(${g.x}%, 2px)` }} />
                      <div aria-hidden className="absolute -inset-y-0.5 w-0.5 bg-muted" style={{ left: `${ages.near_x}%` }} />
                    </div>
                    <div className={`mt-0.5 text-[11px] leading-tight sm:mt-0 ${g.near ? "text-ink" : "text-muted"}`}>{g.near ? <>counts until <span className="num">{g.last_label}</span></> : <><span className="num">{g.age_days}</span> of <span className="num">{g.max_age_days}</span> days</>}</div>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>
    </Figure>
  );
}

// Folio V: the unscored inputs by the reason each has no score. One group is read as candidates, and says so.
export function BlindPlate({ blind, card }: { blind: MigrationFigures["blind"]; card: MigrationDoc["scorecard"] }) {
  const why = Object.fromEntries(card.inputs.map((i) => [i.id, i.withheld?.because ?? ""]));
  return (
    <Figure
      id="fig-blind"
      title="Why each unscored input has no score"
      note={`${KIND_LABEL.chart}, with one judgement marked`}
      keys={<>
        <Key swatch={<Dot hollow />}>an input with no score</Key>
        <Key swatch={<span aria-hidden className="hatch inline-block h-3 w-4 text-s1 ring-1 ring-s1/60" />}>this site&apos;s conjecture: where the shortage may go next</Key>
      </>}
      foot={<p>The groups and their counts are the scorecard&apos;s own reasons for withholding a score. Reading one group as candidates for the next bottleneck is this site&apos;s conjecture, hatched and labelled where it is drawn: an input nobody publishes a series for may be short, or may only be unmeasured. Each name links to its row in the scorecard.</p>}
      tableLabel="Each reason in full"
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">Input</th><th scope="col">Why it has no score</th></tr></thead>
          <tbody>
            {blind.groups.flatMap((g) => g.inputs.map((i) => <tr key={i.id}><td className="whitespace-nowrap">{i.name}</td><td className="min-w-[16rem]">{WITHHELD_WORDS[g.kind]}. {why[i.id]}</td></tr>))}
          </tbody>
        </table>
      }
    >
      <div className="grid gap-4 font-sans sm:grid-cols-3">
        {blind.groups.map((g) => (
          <div key={g.kind} className="flex flex-col gap-2 border-t-2 border-ink pt-2">
            <div className="flex items-baseline gap-2"><span className="num text-[1.6rem] leading-none text-ink">{g.n}</span><span className="text-[11.5px] text-muted">of <span className="num">{blind.total}</span> unscored</span></div>
            <div className="text-[12.5px] font-medium leading-snug text-ink first-letter:uppercase">{WITHHELD_WORDS[g.kind]}</div>
            {g.conjecture ? <div className="hatch px-2 py-1 text-s1/25 ring-1 ring-s1/60"><span className="bg-surface px-1 text-[11px] leading-snug text-ink box-decoration-clone">conjecture: candidates for the next bottleneck</span></div> : null}
            <ul className="flex flex-col gap-1">
              {g.inputs.map((i) => <li key={i.id}><a href={`#input-${i.id}`} className="inline-flex items-center gap-1.5 text-[12px] leading-tight text-ink-2 hover:text-ink"><Dot hollow small />{i.name}</a></li>)}
            </ul>
          </div>
        ))}
      </div>
    </Figure>
  );
}
