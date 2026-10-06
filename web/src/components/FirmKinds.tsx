import Link from "next/link";
import { Figure, Key } from "@/components/Figure";
import { KIND_LABEL, Pyramid, ShareBars, Swatch } from "@/components/diagrams/kit";
import type { FirmKind, FirmKindsDoc, KindPart } from "@/lib/data";
import { fmt } from "@/lib/format";

// What happens to each kind of firm: the figures. Every share and position is the export's.
const FILL: Record<KindPart, string> = { passes: "var(--s1)", waits_on_check: "var(--tight-2)", held: "var(--s3)", outside: "var(--s3)" };
const PART: Record<KindPart, string> = {
  passes: "passes the screen", waits_on_check: "waits only on a check", held: "held for more than a missing check", outside: "not office work, so outside the census",
};
const TIER = { managers: "Managers", professionals: "Professionals", sales: "Sales", support: "Office support" } as const;
const share = (k: FirmKind, p: KindPart) => ({ passes: k.share_passes, waits_on_check: k.share_waits_on_check, held: k.share_held, outside: k.share_outside })[p];
const census = <Link href="/census" className="text-ink underline decoration-axis underline-offset-2">the census</Link>;

export function KindBars({ doc }: { doc: FirmKindsDoc }) {
  return (
    <Figure
      id="fig-bars"
      title="How much of each kind of firm's payroll a check can settle"
      note={KIND_LABEL.chart}
      keys={<>{(Object.keys(PART) as KindPart[]).map((p) => <Key key={p} swatch={<Swatch fill={FILL[p]} hatched={p === "outside"} />}>{PART[p]}</Key>)}</>}
      foot={<p>Shares of each kind of firm&apos;s whole payroll, from {census} ({doc.version}), a screen scored by three AI models and not a record of what has been automated. A kind of firm is one or more of the census&apos;s industries; hover a bar for its share.</p>}
      table={
        <table className="data">
          <thead><tr><th scope="col">Kind of firm</th><th scope="col">Passes</th><th scope="col">All three models pass</th><th scope="col">Waits only on a check</th><th scope="col">Held for more</th><th scope="col">Outside the census</th><th scope="col">Industries</th></tr></thead>
          <tbody>{doc.kinds.map((k) => (
            <tr key={k.id}><th scope="row">{k.name}</th><td>{fmt(k.share_passes, "share")}</td><td>{fmt(k.share_agreed3, "share")}</td><td>{fmt(k.share_waits_on_check, "share")}</td><td>{fmt(k.share_held, "share")}</td><td>{fmt(k.share_outside, "share")}</td><td className="text-muted">{k.titles.join("; ")}</td></tr>
          ))}</tbody>
        </table>
      }
    >
      <ShareBars
        label="Each kind of firm's payroll, split by what the census screen says of it"
        rows={doc.kinds.map((k) => ({
          name: k.name,
          segs: k.bar.map((s) => ({ key: s.part, x: s.x, w: s.w, fill: FILL[s.part], hatched: s.part === "outside", tip: `${k.name}: ${fmt(share(k, s.part), "share")} ${PART[s.part]}` })),
        }))}
      />
    </Figure>
  );
}

export function KindShapes({ doc }: { doc: FirmKindsDoc }) {
  return (
    <Figure
      id="fig-shapes"
      title="The shape of each kind of firm today, by where its office payroll sits"
      note={KIND_LABEL.chart}
      keys={<><Key swatch={<Swatch fill="var(--s3)" />}>a layer, as wide as its share of office payroll</Key><Key swatch={<Swatch fill="var(--s1)" />}>the part of that layer that passes the screen</Key></>}
      foot={<p>Layers are groups of occupations, not ranks: the census has no field for seniority. Top to bottom: managers, professionals, sales, office support. From {census} ({doc.version}).</p>}
    >
      <div className="grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-3 lg:grid-cols-4">
        {doc.kinds.map((k) => (
          <div key={k.id} className="flex flex-col gap-2">
            <Pyramid
              compact
              label={`${k.name}: ${k.tiers.map((t) => `${TIER[t.id]} ${fmt(t.share, "share")}`).join(", ")}`}
              tiers={k.tiers.map((t) => ({ key: t.id, label: TIER[t.id], w: t.w, inner: t.pass_w, tip: `${TIER[t.id]}: ${fmt(t.share, "share")} of office payroll, ${fmt(t.share_passes, "share")} of it passes` }))}
            />
            <div className="text-center text-[12px] leading-tight text-ink-2">{k.name}</div>
          </div>
        ))}
      </div>
    </Figure>
  );
}

const JUDGED = "This site's judgement";
const STAGE_FILL = "var(--s3)";

function Cites({ ids, doc }: { ids: string[]; doc: FirmKindsDoc }) {
  const n = Object.fromEntries(doc.sources.map((s) => [s.id, s.n]));
  return <>{ids.map((id) => <sup key={id} className="ml-0.5"><a href={`#source-${id}`} className="text-ink-2 no-underline hover:underline">{n[id]}</a></sup>)}</>;
}

// The three stages the page reads every kind of firm through, and what each rests on.
export function StageStrip({ doc }: { doc: FirmKindsDoc }) {
  return (
    <Figure id="fig-stages" title="Three stages, and how much each rests on" note={KIND_LABEL.model}>
      <ol className="grid gap-3 md:grid-cols-3">
        {doc.stages.map((s, i) => (
          <li key={s.id} className="relative flex flex-col gap-1.5 border-t-2 border-ink pt-3">
            <span className="eyebrow">{s.name}</span>
            <span className="text-[15px] font-semibold leading-snug text-ink">{s.what}</span>
            <span className="text-[13px] leading-relaxed text-ink-2">{s.rests_on}{s.sources ? <Cites ids={s.sources} doc={doc} /> : null}</span>
            <span aria-hidden className={`mt-1 h-2 w-full ${i ? "hatch" : ""}`} style={{ background: i ? undefined : "var(--s1)", color: i === 1 ? "var(--s2)" : "var(--s3)" }} />
          </li>
        ))}
      </ol>
    </Figure>
  );
}

// Where each kind of firm sits: across, how much of its office work a check can settle (data); up, how much the law
// or a duty ties the work to the firm (judged, in three bands).
export function KindMap({ doc }: { doc: FirmKindsDoc }) {
  return (
    <Figure
      id="fig-map"
      title="Two things decide what a firm keeps: whether a check exists, and who must answer"
      note="Chart across, judgement up"
      foot={<p>Across: the share of each kind of firm&apos;s office payroll that passes the census screen or waits only on a check, from {census} ({doc.version}). Up: one of three bands this site assigned, by how far a licence or a legal duty ties the work to the firm. Within a band, height means nothing; names are stepped so they do not collide.</p>}
    >
      <div className="overflow-x-auto"><div className="grid min-w-[44rem] grid-cols-[minmax(0,9rem)_1fr] gap-x-3">
        <div className="relative h-80" aria-hidden>
          {doc.map.rungs.map((r) => <div key={r.id} className="absolute right-0 w-full -translate-y-1/2 text-right text-[11px] leading-tight text-ink-2" style={{ top: `${r.y}%` }}>{r.label}</div>)}
        </div>
        <div className="relative h-80 border-b border-l border-axis" role="group" aria-label="Kinds of firm placed by how much of their work a check can settle and by who must answer">
          {doc.map.rungs.map((r) => <div key={r.id} aria-hidden className="absolute inset-x-0 h-1/3 -translate-y-1/2 border-y border-grid" style={{ top: `${r.y}%`, background: r.id === "heavy" ? "color-mix(in srgb, var(--surface-2) 70%, transparent)" : undefined }} />)}
          {doc.kinds.map((k) => (
            <div key={k.id} className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-0.5" style={{ left: `${k.place.x}%`, top: `${k.place.y}%` }} title={`${k.name}: ${fmt(k.share_checkable, "share")} of office payroll passes or waits only on a check`}>
              <span className="h-2.5 w-2.5 rounded-full bg-ink" />
              <span className="whitespace-nowrap text-[11px] leading-none text-ink">{k.name.split(" or ")[0].replace(" and IT services company", "").replace(" and business-support firm", "").replace(" and logistics operator", "")}</span>
            </div>
          ))}
        </div>
        <div />
        <div className="relative mt-1 h-5" aria-hidden>
          {doc.map.x.ticks.map((t) => <span key={t.x} className="absolute -translate-x-1/2 font-mono text-[11px] text-muted" style={{ left: `${t.x}%` }}>{t.label}</span>)}
        </div>
        <div />
        <div className="text-center text-[11px] text-ink-2">share of office work a check can settle, or could with one more check</div>
      </div></div>
    </Figure>
  );
}

const PART_AT = { top: "md:col-start-2 md:row-start-1", check: "md:col-start-2 md:row-start-2", base: "md:col-start-2 md:row-start-3", rented: "md:col-start-2 md:row-start-4", owned: "md:col-start-3 md:row-start-1 md:row-span-3" } as const;
const PART_W = { top: "md:mx-[30%]", check: "md:mx-[15%]", base: "", rented: "", owned: "" } as const;

// The site's picture of an AI-run firm: a narrow top that answers, a checking layer, a wide working base, the models
// rented beneath, and what the firm owns to the side.
export function Anatomy({ doc }: { doc: FirmKindsDoc }) {
  const a = doc.anatomy;
  return (
    <Figure id="fig-anatomy" title={a.title} note={KIND_LABEL.model} foot={<p>{a.note}</p>}>
      <div className="grid gap-2 md:grid-cols-[0_minmax(0,1fr)_minmax(0,16rem)] md:gap-x-4">
        {a.parts.map((p) => (
          <div key={p.id} className={`${PART_AT[p.id as keyof typeof PART_AT]} ${PART_W[p.id as keyof typeof PART_W]} flex flex-col gap-1 border p-3 ${p.id === "rented" ? "border-dashed border-axis bg-transparent" : p.id === "top" ? "border-ink bg-ink text-surface" : p.id === "owned" ? "border-ink bg-surface" : "border-axis bg-surface-2"}`}>
            <span className={`font-mono text-[11px] uppercase tracking-wider ${p.id === "top" ? "text-surface" : "text-ink"}`}>{p.name}</span>
            <span className={`text-[13px] leading-snug ${p.id === "top" ? "text-surface" : "text-ink-2"}`}>{p.does}</span>
          </div>
        ))}
      </div>
    </Figure>
  );
}

function Staged({ k, doc }: { k: FirmKind; doc: FirmKindsDoc }) {
  return (
    <div className="grid grid-cols-3 gap-3">
      {k.staged.map((s, i) => (
        <div key={s.stage} className="flex flex-col gap-1.5">
          <Pyramid
            compact
            label={`${k.name}, ${doc.stages[i].name}: ${s.tiers.map((t) => `${TIER[t.id]} ${t.word ? doc.shape_words[t.word] : "as measured"}`).join(", ")}`}
            tiers={s.tiers.map((t) => ({ key: t.id, label: TIER[t.id], w: t.w, inner: t.inner, hatched: s.judged, fill: s.judged ? "var(--s2)" : STAGE_FILL, tip: `${TIER[t.id]}: ${t.word ? doc.shape_words[t.word] : "as the census has it today"}` }))}
          />
          <span className="text-center font-mono text-[10px] uppercase tracking-wider text-muted">{doc.stages[i].name}</span>
        </div>
      ))}
    </div>
  );
}

// One panel per kind of firm: what is seen now (sourced), what this site judges comes next and later, who signs,
// what the firm will need to buy, and what would prove the view wrong.
export function KindPanels({ doc }: { doc: FirmKindsDoc }) {
  const need = Object.fromEntries(doc.needs.map((n) => [n.id, n.name]));
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {doc.kinds.map((k) => (
        <section key={k.id} id={`kind-${k.id}`} aria-labelledby={`kind-${k.id}-h`} className="fig flex scroll-mt-24 flex-col gap-3 p-4 md:p-5">
          <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
            <h3 id={`kind-${k.id}-h`} className="display text-[1.25rem] leading-tight">{k.name}</h3>
            <span className="font-mono text-[11px] text-muted">{fmt(k.share_passes, "share")} passes · {fmt(k.share_waits_on_check, "share")} waits on a check{k.share_outside > k.share_held ? ` · ${fmt(k.share_outside, "share")} outside the census` : ""}</span>
          </div>
          <Staged k={k} doc={doc} />
          <dl className="flex flex-col gap-2 text-[13.5px] leading-relaxed">
            <div><dt className="eyebrow">Now · what has been published</dt><dd className="text-ink-2">{k.now}<Cites ids={k.sources} doc={doc} /></dd></div>
            <div><dt className="eyebrow">Next · {JUDGED}</dt><dd className="text-ink-2">{k.next}</dd></div>
            <div><dt className="eyebrow">Later · extrapolation</dt><dd className="text-ink-2">{k.later}</dd></div>
            <div><dt className="eyebrow">Who must still sign</dt><dd className="text-ink-2">{k.signs}. <span className="text-muted">{doc.rungs[k.rung]}.</span></dd></div>
            <div><dt className="eyebrow">What it will need to buy</dt><dd className="flex flex-wrap gap-1.5 pt-0.5">{k.needs.map((n) => <a key={n} href={`#need-${n}`} className="border border-grid px-1.5 py-0.5 text-[12px] text-ink no-underline hover:border-ink">{need[n]}</a>)}</dd></div>
            <div><dt className="eyebrow">What would prove this wrong</dt><dd className="text-ink-2">{k.wrong}</dd></div>
          </dl>
        </section>
      ))}
    </div>
  );
}

export function RollupBars({ doc }: { doc: FirmKindsDoc }) {
  const rows = doc.kinds.filter((k) => k.rollups);
  return (
    <Figure
      id="fig-rollups"
      title="Where buyers built around AI are already buying firms"
      note={KIND_LABEL.chart}
      keys={<><Key swatch={<Swatch fill="var(--s3)" />}>buyers this site lists in the trade</Key><Key swatch={<Swatch fill="var(--s1)" />}>purchases it has found and recorded</Key></>}
      foot={<p>From this site&apos;s <Link href="/census#deals" className="text-ink underline decoration-axis underline-offset-2">list of roll-ups by trade</Link>. Purchases are a floor: only some buyers were searched, and a trade here is the roll-up list&apos;s, which can be narrower than the kind of firm. Kinds with no trade on that list are left out, which is not a count of none.</p>}
    >
      <div className="flex flex-col gap-3">
        {rows.map((k) => (
          <div key={k.id} className="grid grid-cols-1 gap-1 sm:grid-cols-[13rem_1fr] sm:items-center sm:gap-3">
            <div className="text-[13px] leading-tight text-ink">{k.name}<span className="block text-[11px] text-muted">{k.rollups!.trade}</span></div>
            <div className="flex flex-col gap-0.5">
              <div className="flex items-center gap-2"><span className="h-3" style={{ width: `max(${k.rollups!.buyers_w}%, 2px)`, background: "var(--s3)" }} /><span className="num text-[11px] text-ink-2">{k.rollups!.buyers}</span></div>
              <div className="flex items-center gap-2"><span className="h-3" style={{ width: `max(${k.rollups!.deals_w}%, 2px)`, background: "var(--s1)" }} /><span className="num text-[11px] text-ink-2">{k.rollups!.deals}</span></div>
            </div>
          </div>
        ))}
      </div>
    </Figure>
  );
}

// What these firms will need to buy, against the kinds of firm that need it. A filled cell is this site's reading of
// the published evidence for that kind, not a measurement.
export function NeedsGrid({ doc }: { doc: FirmKindsDoc }) {
  return (
    <Figure
      id="fig-needs"
      title="What AI-run firms will need to buy, and which kinds need it"
      note={KIND_LABEL.model}
      foot={<p>A mark is this site&apos;s reading of what operators, regulators and failures in that trade point to; it is a judgement. A need links to the business on this site&apos;s <Link href="/value-chain/opportunities" className="text-ink underline decoration-axis underline-offset-2">list of businesses that could be built</Link> that would meet it. The last rows have no business on that list yet.</p>}
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-[52rem] border-collapse text-left text-[12.5px] leading-snug">
          <thead>
            <tr>
              <th scope="col" className="w-[19rem] border-b border-ink py-2 pr-3 align-bottom font-medium text-ink-2">The need</th>
              {doc.kinds.map((k) => <th key={k.id} scope="col" className="border-b border-ink px-0.5 pb-2 align-bottom font-normal text-ink-2"><span className="block [writing-mode:vertical-rl] rotate-180 whitespace-nowrap">{k.name.split(" or ")[0].replace(" and IT services company", "").replace(" and business-support firm", "").replace(" and logistics operator", "")}</span></th>)}
            </tr>
          </thead>
          <tbody>
            {doc.needs.map((n, i) => (
              <tr key={n.id} id={`need-${n.id}`} className="scroll-mt-24 border-b border-grid align-top target:bg-surface-2">
                <th scope="row" className="py-2 pr-3 font-normal">
                  <span className="font-medium text-ink">{n.name}</span>
                  <span className="block text-ink-2">{n.what}</span>
                  <span className="block pt-0.5 text-[11.5px]">{n.opportunities.length ? n.opportunities.map((o, j) => <span key={o.id}>{j ? " · " : ""}<Link href={o.href} className="text-ink underline decoration-axis underline-offset-2">{o.name}</Link></span>) : <span className="text-muted">No business on the list yet</span>}</span>
                </th>
                {doc.needs_grid[i].cells.map((on, j) => <td key={doc.kinds[j].id} className="px-0.5 py-2 text-center">{on ? <span role="img" aria-label={`${doc.kinds[j].name} needs this`} className="inline-block h-2.5 w-2.5 rounded-full bg-ink" /> : <span aria-hidden className="inline-block h-2.5 w-2.5 rounded-full border border-grid" />}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Figure>
  );
}

export function KindSources({ doc }: { doc: FirmKindsDoc }) {
  return (
    <ol className="flex flex-col text-[13px] leading-relaxed text-ink-2">
      {doc.sources.map((s) => (
        <li key={s.id} id={`source-${s.id}`} className="scroll-mt-24 border-t border-grid py-2 first:border-0 target:bg-surface-2">
          <span className="num mr-2 text-muted">{s.n}</span>
          {s.who}, <a href={s.url} className="text-ink underline decoration-axis underline-offset-2">{s.work}</a>, {s.venue}{s.year ? `, ${s.year}` : ""}.{s.ties ? <span className="text-muted"> Note: {s.ties}.</span> : null} <span className="text-muted">Read {s.retrieved_at}.</span>
        </li>
      ))}
    </ol>
  );
}
