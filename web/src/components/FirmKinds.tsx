import Link from "next/link";
import { Figure, Key } from "@/components/Figure";
import { KIND_LABEL, Pyramid, Swatch } from "@/components/diagrams/kit";
import type { FirmKind, FirmKindsDoc, KindPart } from "@/lib/data";
import { fmt } from "@/lib/format";

// What happens to each kind of firm: the figures. Every share and position is the export's. Hatching is kept for
// this site's judgement; everything measured, the part outside the census included, is a plain fill.
const FILL: Record<KindPart, string> = {
  passes: "var(--s1)", waits_on_check: "var(--tight-2)", needs_body: "color-mix(in srgb, var(--s2) 60%, var(--s3))", held: "var(--s3)", outside: "var(--surface-2)",
};
const EDGE = "inset 0 0 0 1px var(--axis)"; // the pale part outside the census keeps a border so it reads as part of the bar
const PART: Record<KindPart, string> = {
  passes: "passes the screen", waits_on_check: "waits only on a check", needs_body: "needs a body",
  held: "held: no existing check, slow to judge, costly when wrong, or a sign-off", outside: "manual, service and production jobs, which the census does not score",
};
const TIER = { managers: "Managers", professionals: "Professional and technical staff", sales: "Sales", support: "Office support" } as const;
const share = (k: FirmKind, p: KindPart) => ({ passes: k.share_passes, waits_on_check: k.share_waits_on_check, needs_body: k.share_needs_body, held: k.share_held, outside: k.share_outside })[p];
const short = (name: string) => name.split(" or ")[0].replace(" and IT services company", "").replace(" and business-support firm", "").replace(" and logistics operator", "").replace("Customer-support", "Customer support");
const census = <Link href="/census" className="text-ink underline decoration-axis underline-offset-2">the census</Link>;
const Box = ({ fill, edge = false }: { fill: string; edge?: boolean }) => <span className="inline-block h-2.5 w-4" style={{ background: fill, boxShadow: edge ? EDGE : undefined }} />;

export function KindBars({ doc }: { doc: FirmKindsDoc }) {
  return (
    <Figure
      id="fig-bars"
      title="In every kind of firm only a small part of payroll passes the screen"
      note={KIND_LABEL.chart}
      keys={<>{(Object.keys(PART) as KindPart[]).map((p) => <Key key={p} swatch={<Box fill={FILL[p]} edge={p === "outside"} />}>{PART[p]}</Key>)}<Key swatch={<span className="relative inline-block h-2.5 w-4" style={{ background: FILL.passes }}><span className="absolute inset-y-0 left-1/2 w-px bg-surface" /></span>}>the white line inside the dark part: all the scoring models pass what lies to its left</Key></>}
      foot={<p>Shares of each kind of firm&apos;s whole payroll, from {census} ({doc.version}), a screen scored by AI models and not a record of what has been automated. The part most of the models pass is printed beside each name, with the smaller part all of them pass. A kind of firm is one or more of the census&apos;s industries. A kind&apos;s name is wider than the industries behind it; the table lists them.</p>}
      table={
        <table className="data">
          <thead><tr><th scope="col">Kind of firm</th><th scope="col">Passes</th><th scope="col">All the models pass</th><th scope="col">Waits only on a check</th><th scope="col">Needs a body</th><th scope="col">Held for more</th><th scope="col">Outside the census</th><th scope="col">Industries</th></tr></thead>
          <tbody>{doc.kinds.map((k) => (
            <tr key={k.id}><th scope="row">{k.name}</th><td>{fmt(k.share_passes, "share")}</td><td>{fmt(k.share_agreed3, "share")}</td><td>{fmt(k.share_waits_on_check, "share")}</td><td>{fmt(k.share_needs_body, "share")}</td><td>{fmt(k.share_held, "share")}</td><td>{fmt(k.share_outside, "share")}</td><td className="text-muted">{k.titles.join("; ")}</td></tr>
          ))}</tbody>
        </table>
      }
    >
      <div role="group" aria-label="Each kind of firm's payroll, split by what the census screen says of it" className="flex flex-col gap-3">
        {doc.kinds.map((k) => (
          <div key={k.id} className="grid grid-cols-1 gap-1 sm:grid-cols-[15rem_1fr] sm:items-center sm:gap-3">
            <div className="text-[13px] leading-tight text-ink">{k.name}
              <span className="block font-mono text-[11px] text-muted">{fmt(k.share_passes, "share")} passes · {fmt(k.share_agreed3, "share")} all the models</span>
            </div>
            <div className="relative h-5 w-full">
              {k.bar.map((s) => (
                <div key={s.part} title={`${k.name}: ${fmt(share(k, s.part), "share")} ${PART[s.part]}${s.part === "passes" ? ` (${fmt(k.share_agreed3, "share")} with all the models agreeing)` : ""}`} className="absolute inset-y-0" style={{ left: `${s.x}%`, width: `${s.w}%`, background: FILL[s.part], boxShadow: s.part === "outside" ? EDGE : "inset -1px 0 0 var(--surface)" }} />
              ))}
              <div aria-hidden className="absolute inset-y-0 w-px bg-surface" style={{ left: `${k.agreed_w}%` }} />
            </div>
          </div>
        ))}
      </div>
    </Figure>
  );
}

export function KindShapes({ doc }: { doc: FirmKindsDoc }) {
  return (
    <Figure
      id="fig-shapes"
      title="In most kinds of firm the professional layer is the widest, and in no layer does most of the payroll pass"
      note={KIND_LABEL.chart}
      keys={<><Key swatch={<Swatch fill="var(--s3)" />}>a layer, as wide as its share of knowledge-work payroll</Key><Key swatch={<Swatch fill="var(--s1)" />}>the part of that layer that passes the screen</Key></>}
      foot={<p>Layers are groups of occupations, not ranks: the census has no field for seniority. Top to bottom: managers, professional and technical staff, sales, office support. Professional and technical staff are every knowledge occupation that is not management, sales or office support: computing, engineering, science, law, education, media, healthcare and community service, with technicians, paralegals and nurses among them. The dark part is what most of the scoring models pass; the part all of them pass is smaller and is in the table below. From {census} ({doc.version}).</p>}
      tableLabel="The numbers: each layer's share of knowledge-work payroll, and how much of the layer passes"
      table={
        <table className="data">
          <thead><tr><th scope="col">Kind of firm</th>{doc.kinds[0].tiers.map((t) => <th key={t.id} scope="col">{TIER[t.id]}</th>)}</tr></thead>
          <tbody>{doc.kinds.map((k) => (
            <tr key={k.id}><th scope="row">{k.name}</th>{k.tiers.map((t) => (
              <td key={t.id}>{fmt(t.share, "share")}<span className="block text-muted">{fmt(t.share_passes, "share")} passes · {fmt(t.share_agreed3, "share")} all the models</span></td>
            ))}</tr>
          ))}</tbody>
        </table>
      }
    >
      <div className="grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-3 lg:grid-cols-4">
        {doc.kinds.map((k) => (
          <div key={k.id} className="flex flex-col gap-2">
            <Pyramid
              compact
              label={`${k.name}: ${k.tiers.map((t) => `${TIER[t.id]} ${fmt(t.share, "share")}`).join(", ")}`}
              tiers={k.tiers.map((t) => ({ key: t.id, label: TIER[t.id], w: t.w, inner: t.pass_w, tip: `${TIER[t.id]}: ${fmt(t.share, "share")} of knowledge-work payroll; ${fmt(t.share_passes, "share")} of it passes, ${fmt(t.share_agreed3, "share")} with all the models agreeing` }))}
            />
            <div className="text-center text-[12px] leading-tight text-ink-2">{k.name}</div>
          </div>
        ))}
      </div>
    </Figure>
  );
}

const JUDGED = "This site's judgement";

function Cites({ ids, doc }: { ids: string[]; doc: FirmKindsDoc }) {
  const n = Object.fromEntries(doc.sources.map((s) => [s.id, s.n]));
  return <>{ids.map((id) => <sup key={id} className="ml-0.5"><a href={`#source-${id}`} className="text-ink-2 no-underline hover:underline">{n[id]}</a></sup>)}</>;
}

// The stages the page reads every kind of firm through, and what each rests on.
export function StageStrip({ doc }: { doc: FirmKindsDoc }) {
  return (
    <Figure id="fig-stages" title="The stages, and how much each rests on" note={KIND_LABEL.model}>
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

// Where each kind of firm sits. Across: how much of its knowledge-work payroll a check settles or could (data). The
// grouping: how far the law or a duty ties the work to the firm (judged, in bands). One row for each kind, so height
// says nothing.
export function KindMap({ doc }: { doc: FirmKindsDoc }) {
  const by = Object.fromEntries(doc.kinds.map((k) => [k.id, k]));
  const row = "grid grid-cols-[7.5rem_1fr_2.75rem] items-center gap-x-2 sm:grid-cols-[15rem_1fr_3.25rem] sm:gap-x-3";
  return (
    <Figure
      id="fig-map"
      title="Where each kind of firm sits: how much of its work a check could settle, and how far the law ties the work to the firm"
      note="Chart across, judgement in the grouping"
      foot={<p>Across: the share of each kind of firm&apos;s knowledge-work payroll that passes the census screen or waits only on a check, from {census} ({doc.version}). The groups are bands this site assigned, by how far a licence or a legal duty ties the work to the firm; a kind is banded by its most regulated work. Within a band the rows run from the largest share to the smallest, and their order means nothing more.</p>}
    >
      <div className="flex flex-col gap-4">
        {doc.map.bands.map((b) => (
          <div key={b.id} role="group" aria-label={b.label} className="flex flex-col gap-1.5">
            <div className="border-b border-grid pb-1 text-[12.5px] font-medium leading-snug text-ink"><span className="mr-2 font-mono text-[10px] font-normal uppercase tracking-wider text-muted">Band, judged</span>{b.label}</div>
            {b.kinds.map((id) => (
              <div key={id} className={row} title={`${by[id].name}: ${fmt(by[id].share_checkable, "share")} of knowledge-work payroll passes the screen, or would if an accepted check existed. Band: ${b.label}`}>
                <span className="text-[12.5px] leading-tight text-ink-2">{short(by[id].name)}</span>
                <span className="relative block h-4">
                  <span aria-hidden className="absolute inset-x-0 top-1/2 h-px bg-grid" />
                  {doc.map.x.ticks.map((t) => <span key={t.x} aria-hidden className="absolute inset-y-0 w-px bg-grid" style={{ left: `${t.x}%` }} />)}
                  <span className="absolute top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ink" style={{ left: `${by[id].place.x}%` }} />
                </span>
                <span className="num text-right text-[11px] text-ink-2">{fmt(by[id].share_checkable, "share")}</span>
              </div>
            ))}
          </div>
        ))}
        <div className={row} aria-hidden>
          <span />
          <span className="relative block h-4">{doc.map.x.ticks.map((t) => <span key={t.x} className="absolute -translate-x-1/2 font-mono text-[11px] text-muted" style={{ left: `${t.x}%` }}>{t.label}</span>)}</span>
          <span />
        </div>
        <div className="text-center text-[11px] leading-snug text-ink-2">share of knowledge-work payroll that passes the screen, or would if an accepted check existed</div>
      </div>
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
    <div role="group" aria-label={`${k.name}: its layers as measured now, and as this site judges them next and later`} className="flex flex-col gap-2">
      <div className="grid grid-cols-3 gap-3 font-mono text-[10px] uppercase leading-tight tracking-wider text-muted">
        {k.staged.map((s, i) => <span key={s.stage}>{doc.stages[i].name} · {s.judged ? "judged" : "measured"}</span>)}
      </div>
      {k.tiers.map((tier, j) => (
        <div key={tier.id} className="flex flex-col gap-0.5">
          <span className="text-[11.5px] leading-tight text-ink">{TIER[tier.id]}</span>
          <div className="grid grid-cols-3 gap-3">
            {k.staged.map((s) => s.tiers[j]).map((t, i) => (
              <div key={k.staged[i].stage} className="flex flex-col gap-0.5">
                {t.word ? (
                  <span className="relative block h-3">
                    <span className="absolute inset-y-0 left-0 border border-dashed border-axis" style={{ width: `max(${t.was}%, 3px)` }} />
                    <span className="hatch absolute inset-y-0 left-0" style={{ width: `${t.w}%`, color: "var(--s2)" }} />
                  </span>
                ) : (
                  <span className="relative block h-3">
                    <span className="absolute inset-y-0 left-0" style={{ width: `max(${t.w}%, 3px)`, background: "var(--s3)" }}>
                      {t.inner ? <span className="absolute inset-y-0 left-0" style={{ width: `${t.inner}%`, background: "var(--s1)" }} /> : null}
                    </span>
                  </span>
                )}
                {t.word ? <span className="text-[10.5px] leading-tight text-ink-2">{doc.shape_words[t.word]}</span> : <span className="num text-[10.5px] leading-tight text-muted">{fmt(tier.share, "share")}</span>}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// The key to every panel: what is measured, what is judged, and the rule the judged layers are drawn by.
export function PanelKey({ doc }: { doc: FirmKindsDoc }) {
  return (
    <div className="fig flex flex-col gap-3 p-4 text-[12.5px] leading-snug text-ink-2">
      <span className="eyebrow">Measured now; judgement next and later</span>
      <div className="flex flex-wrap gap-x-5 gap-y-2">
        <Key swatch={<Swatch fill="var(--s3)" />}>measured: a layer, as wide as its share of today&apos;s knowledge-work payroll, which is the figure under it; the widest layer fills its column</Key>
        <Key swatch={<Swatch fill="var(--s1)" />}>the part of that layer most of the scoring models pass</Key>
        <Key swatch={<span className="inline-block h-2.5 w-4 border border-dashed border-axis" />}>today&apos;s width, kept as an outline behind each judged layer</Key>
      </div>
      <div className="flex flex-wrap items-end gap-x-6 gap-y-2">
        {doc.drawn.map((d) => (
          <span key={d.word} className="flex flex-col gap-1">
            <span className="relative block h-3 w-24">
              <span className="absolute inset-0 border border-dashed border-axis" />
              <span className="hatch absolute inset-y-0 left-0" style={{ width: `${d.w}%`, color: "var(--s2)" }} />
            </span>
            <span className="text-[11.5px] text-ink">{d.label}</span>
          </span>
        ))}
      </div>
      <p>Drawing rule: this site chose a word for each layer at each later stage, and the word is printed under the layer. Each word has a fixed width, chosen so the steps can be told apart. The widths are not estimates.</p>
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
          <div className="flex flex-col gap-1">
            <h3 id={`kind-${k.id}-h`} className="display text-[1.25rem] leading-tight">{k.name}</h3>
            <span className="font-mono text-[11px] leading-snug text-muted">{fmt(k.share_passes, "share")} passes ({fmt(k.share_agreed3, "share")} with all the models agreeing) · {fmt(k.share_waits_on_check, "share")} waits on a check{k.share_outside > k.share_held ? ` · ${fmt(k.share_outside, "share")} outside the census` : ""}</span>
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
      foot={<p>A roll-up is a buyer that purchases many small firms in a trade and runs them on shared software. From this site&apos;s <Link href="/census#deals" className="text-ink underline decoration-axis underline-offset-2">list of roll-ups by trade</Link>. Purchases are a floor: only some buyers were searched, and a trade here is the roll-up list&apos;s, which can be narrower than the kind of firm. Kinds with no trade on that list are left out, which is not a count of none.</p>}
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

// What these firms will need to buy, against the kinds of firm that need it. A filled cell is this site's judgement,
// not a measurement.
export function NeedsGrid({ doc }: { doc: FirmKindsDoc }) {
  return (
    <Figure
      id="fig-needs"
      title="Only a check is needed by every kind of firm; the record, the sign-off and the insurance cluster where a regulator stands behind the work"
      note="This site's judgement"
      foot={<p>A mark is this site&apos;s judgement of what that kind of firm will need, from what operators, regulators and failures point to where there is any. A need links to the business on this site&apos;s <Link href="/value-chain/opportunities" className="text-ink underline decoration-axis underline-offset-2">list of businesses that could be built</Link> that would meet it, or that would do the whole job in the firm&apos;s place. The last rows have no business on that list yet.</p>}
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-[52rem] border-collapse text-left text-[12.5px] leading-snug">
          <thead>
            <tr>
              <th scope="col" className="w-[19rem] border-b border-ink py-2 pr-3 align-bottom font-medium text-ink-2">The need</th>
              {doc.kinds.map((k) => <th key={k.id} scope="col" className="border-b border-ink px-0.5 pb-2 align-bottom font-normal text-ink-2"><span className="block [writing-mode:vertical-rl] rotate-180 whitespace-nowrap">{short(k.name)}</span></th>)}
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
