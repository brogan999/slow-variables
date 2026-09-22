import Link from "next/link";
import { Figure, Key } from "./Figure";
import { Fact } from "./Fact";
import { StatusChip } from "./StatusChip";
import type { MapCell, MapDoc, MapReading, MapRow } from "@/lib/data";
import { CLAIM_WORDS, fmt, WITHHELD_WORDS, words } from "@/lib/format";

const link = "underline decoration-grid underline-offset-2 hover:decoration-ink";
// A claim's state read beside a row: "both sides expect this" would there read as both sides expecting the row to bind.
const tonight = (s: string) => (s === "both" ? "tonight's reading fits both sides" : CLAIM_WORDS[s] ?? words(s));
const KIND: Record<string, string> = { supply: "supply", know_how: "know-how", money: "money" };

// A cell's marks are shapes, so no meaning rides on colour: a filled square where the row acts on this stage and the
// site measures the row, an open square where nothing the site reads measures it, a hatched square for each named
// writer, or this site, that expects the row to bind here, and a plus where the stage is this site's placement, not an
// author's. A claim about what happens on a row without saying it binds is listed under the row and marks no cell.
function Glyph({ kind }: { kind: "measured" | "unmeasured" | "writer" }) {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden className="inline-block align-middle">
      {kind === "measured" ? <rect x="1.5" y="1.5" width="11" height="11" fill="var(--s1)" /> : null}
      {kind === "unmeasured" ? <rect x="2" y="2" width="10" height="10" fill="var(--surface)" stroke="var(--s1)" strokeWidth="1.5" /> : null}
      {kind === "writer" ? <rect x="2" y="2" width="10" height="10" fill="url(#hatch-s1)" stroke="var(--s1)" strokeWidth="1" /> : null}
    </svg>
  );
}

function said(c: MapCell): string {
  const parts = [];
  if (c.bites) parts.push(c.measured ? "acts here, and the site measures it" : "acts here, but nothing the site reads measures it");
  if (c.site) parts.push("placed here by this site");
  if (c.writers.length) parts.push(`expected to bind by ${c.writers.map((w) => `${w.who} (${tonight(w.state)})`).join(", ")}`);
  return parts.join("; ");
}

function Cell({ c }: { c: MapCell | undefined }) {
  if (!c) return <span className="sr-only">does not act here</span>;
  return (
    <span className="inline-flex items-center gap-0.5">
      {c.bites ? <Glyph kind={c.measured ? "measured" : "unmeasured"} /> : null}
      {c.writers.map((w, k) => <Glyph key={k} kind="writer" />)}
      {c.site ? <span aria-hidden className="num text-[11px] text-ink-2">+</span> : null}
      <span className="sr-only">{said(c)}</span>
    </span>
  );
}

function Reading({ r }: { r: MapReading }) {
  if (r.kind === "scored") {
    return (
      <span className="block text-[12px] leading-snug text-ink-2">
        <span className="text-ink"><span className="num">{r.score}</span> · {r.word}</span> <span className="text-muted">({KIND[r.kind_of_tight] ?? r.kind_of_tight}; confidence <span className="num">{r.confidence}</span>{r.hatched ? ", low" : ""})</span>
      </span>
    );
  }
  if (r.kind === "withheld") return <span className="block text-[12px] leading-snug text-muted">Not scored: {(r.tag && WITHHELD_WORDS[r.tag]) ?? "no reading yet"}.</span>;
  if (!r.instruments && !r.readings) return <span className="block text-[12px] leading-snug text-muted">Nothing the site reads measures it yet.</span>;
  return (
    <span className="block text-[12px] leading-snug text-ink-2">
      {r.instruments ? <><span className="num">{r.instruments}</span> indicator{r.instruments === 1 ? "" : "s"}: <span className="num">{r.fast}</span> faster than normal, <span className="num">{r.normal}</span> consistent or slower, <span className="num">{r.other}</span> with other statuses</> : null}
      {r.instruments && r.readings ? "; " : ""}
      {r.readings ? <><span className="num">{r.readings}</span> reading{r.readings === 1 ? "" : "s"} with no status</> : null}
    </span>
  );
}

function Row({ r, stages }: { r: MapRow; stages: MapDoc["stages"] }) {
  return (
    <tr className="align-top">
      <th scope="row" className="text-left min-w-[11rem]">
        <a href={`#why-${r.id}`} className="font-sans font-semibold text-[14px] text-ink hover:underline underline-offset-2 decoration-grid">{r.name}</a>
        {r.sublayer ? <span className="block text-[11px] text-muted">{r.sublayer.name}</span> : null}
        <Reading r={r.reading} />
        <span className="sm:hidden mt-1.5 flex flex-wrap gap-x-3 gap-y-1">
          {stages.map((s) => <span key={s.id} className="inline-flex items-center gap-1"><span aria-hidden className="num text-[11px] text-muted">{s.n}</span><span className="sr-only">{s.label}:</span><Cell c={r.cells[s.id]} /></span>)}
        </span>
      </th>
      {stages.map((s) => <td key={s.id} className="max-sm:hidden text-center align-middle"><Cell c={r.cells[s.id]} /></td>)}
    </tr>
  );
}

export function BottleneckMap({ doc }: { doc: MapDoc }) {
  return (
    <Figure
      title="Where AI is held up, and at which stage"
      note="today's reading once per row · a row's name opens why"
      keys={<>
        <Key swatch={<Glyph kind="measured" />}>acts on this stage, and the site measures it</Key>
        <Key swatch={<Glyph kind="unmeasured" />}>acts on it, but nothing the site reads measures it</Key>
        <Key swatch={<Glyph kind="writer" />}>a named writer, or this site, expects it to bind here, one square each</Key>
        <Key swatch={<span className="num text-[12px] text-ink-2">+</span>}>placed at this stage by this site, not by the author</Key>
      </>}
      foot={<>
        <p>A row acts on a stage when, being short, it would slow that stage; whether it is short today is its reading. Inside the chain, the reading is the input&apos;s tightness on this site&apos;s scorecard, from slack to severe, with the confidence the score carries; it means something different for supply, know-how and money, so a scored row says which. Outside the chain, the reading is the status of the indicators that read the friction: faster than normal means the barrier is being crossed faster than the normal pace this site allows for; consistent or slower means it is holding. The two scales are never mixed. To bind is to be the scarce thing that sets the pace.</p>
        <p>Narayanan and Kapoor are computer scientists at Princeton who argue that AI will spread slowly, like earlier general-purpose technologies, because of barriers outside the models. The National Bureau of Economic Research is a network of American economists; its 2026 volume on transformative AI adds the last four rows.</p>
      </>}
    >
      <p className="sm:hidden text-[12px] text-ink-2 mb-2">The stages, numbered: {doc.stages.map((s, i) => <span key={s.id}>{i ? ", " : ""}<span className="num">{s.n}</span> {s.label.toLowerCase()}</span>)}.</p>
      <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="The bottleneck map, as a table">
        <table className="data w-full [&_th]:max-sm:px-2">
          <thead>
            <tr>
              <th scope="col" className="text-left">What slows it, and today&apos;s reading</th>
              {doc.stages.map((s) => <th scope="col" key={s.id} className="max-sm:hidden text-center align-bottom">{s.label}</th>)}
            </tr>
          </thead>
          {doc.groups.map((g) => g.sections.filter((sec) => sec.rows.length).map((sec) => (
            <tbody key={`${g.id}-${sec.id}`}>
              <tr><th scope="rowgroup" colSpan={doc.stages.length + 1} className="text-left pt-4!"><span className="block font-sans text-[12px] text-ink">{g.label}: {sec.name}</span></th></tr>
              {sec.rows.map((r) => <Row key={r.id} r={r} stages={doc.stages} />)}
            </tbody>
          )))}
        </table>
      </div>
    </Figure>
  );
}

// Each row's reasons, instruments and claims, one disclosure per row, opened from the row's name in the map.
export function MapReasons({ doc }: { doc: MapDoc }) {
  return (
    <div className="flex flex-col gap-5">
      {doc.groups.map((g) => g.sections.filter((sec) => sec.rows.length).map((sec) => (
        <section key={`${g.id}-${sec.id}`} className="flex flex-col gap-1.5">
          <h3 className="font-sans font-semibold text-[13px] text-ink">{g.label}: {sec.name}</h3>
          {sec.rows.map((r) => (
            <details key={r.id} id={`why-${r.id}`} className="scroll-mt-24 target:bg-surface-2 border-t border-grid pt-1.5">
              <summary className="cursor-pointer text-[14px] text-ink">{r.name}</summary>
              <div className="mt-1.5 mb-2 flex flex-col gap-1.5 text-[13px] leading-snug text-ink-2 max-w-[64ch]">
                {r.what ? <p>{r.what}</p> : null}
                {r.reading.kind === "withheld" && r.reading.because ? <p><span className="text-ink">Why it is not scored:</span> {r.reading.because}</p> : null}
                {r.reads ? <p><span className="text-ink">What its score reads:</span> {r.reads}</p> : null}
                <ul className="flex flex-col gap-1">
                  {doc.stages.filter((s) => r.cells[s.id]?.why).map((s) => (
                    <li key={s.id}><span className="text-ink">{s.label}:</span> {r.cells[s.id].why}{r.cells[s.id].site ? " Placed by this site." : ""}</li>
                  ))}
                </ul>
                {r.instruments.length ? (
                  <p><span className="text-ink">Read by:</span> {r.instruments.map((m, k) => (
                    <span key={k}>{k ? "; " : ""}{m.href ? <Link href={m.href} prefetch={false} className={link}>{m.label}</Link> : m.label}{m.unpublished ? " (not published)" : m.status ? <> <StatusChip status={m.status} /></> : null}</span>
                  ))}</p>
                ) : null}
                {r.readings?.length ? (
                  <p><span className="text-ink">Readings with no status:</span> {r.readings.map((x, k) => (
                    <span key={k}>{k ? "; " : ""}{x.label} <Fact f={{ ...x, href: x.href ?? "" }} /> <span className="text-muted">({x.as_of})</span></span>
                  ))}</p>
                ) : null}
                {r.claims.length ? (
                  <p><span className="text-ink">Expected:</span> {r.claims.map((w, k) => <span key={k}>{k ? " " : ""}{w.who}: &ldquo;{w.text}&rdquo; <Link href={w.href} prefetch={false} className={link}>{tonight(w.state)}</Link>.</span>)}</p>
                ) : null}
                {r.note ? <p className="text-muted">{r.note}</p> : null}
                {r.domains && Object.keys(r.domains).length ? (
                  <p><span className="text-ink">Their barriers by domain:</span> {Object.entries(r.domains).map(([d, ids], k) => <span key={d}>{k ? "; " : ""}{d} {ids.map((n, j) => <span key={n}>{j ? " " : ""}<a href={`#b${n}`} className={link}>{n}</a></span>)}</span>)}</p>
                ) : null}
                {r.family && r.href ? <a href={r.href} className={link}>Narayanan and Kapoor&apos;s list for this family</a> : null}
                {r.source ? <span className="text-muted">From {r.source}.</span> : null}
                {r.layer && r.href ? <Link href={r.href} prefetch={false} className={link}>Its row on the tightness scorecard</Link> : null}
              </div>
            </details>
          ))}
        </section>
      )))}
    </div>
  );
}

// Startup money under each sub-layer the chain's inputs sit in, all read at one quarter end. Money raised by selling
// new shares in startups only: the build-out itself is paid for with big companies' capital spending and debt.
export function Bets({ doc }: { doc: MapDoc }) {
  const names = Object.fromEntries(doc.groups.flatMap((g) => g.sections.flatMap((s) => s.rows.map((r) => [r.id, r.name]))));
  const asOf = doc.bets.find((b) => b.as_of)?.as_of;
  return (
    <div className="overflow-x-auto" tabIndex={0} role="region" aria-label="Startup money by sub-layer">
      <table className="data w-full">
        <thead><tr><th scope="col">Sub-layer</th><th scope="col" className="max-sm:hidden">Inputs it holds</th><th scope="col" className="text-right">Firms tracked</th><th scope="col" className="text-right">Raised in the four quarters{asOf ? ` to ${asOf}` : ""}</th></tr></thead>
        <tbody>{doc.bets.map((b) => (
          <tr key={b.sublayer.id}>
            <td><Link href={`/stack/${b.sublayer.id}`} prefetch={false} className={link}>{b.sublayer.name}</Link></td>
            <td className="max-sm:hidden text-ink-2">{b.rows.map((id) => names[id] ?? id).join(", ")}</td>
            <td className="num text-right">{b.firms}</td>
            <td className="num text-right whitespace-nowrap">{b.venture ? <Link href={b.venture.href} prefetch={false} className={link}>{fmt(b.venture.value, "USD")}</Link> : <span className="text-muted">none on file</span>}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}
