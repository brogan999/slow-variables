import Link from "next/link";
import { Fact } from "@/components/Fact";
import { Figure } from "@/components/Figure";
import { ClaimState } from "@/components/OutlookParts";
import type { Place, PlaceState, PlaceTest, Shifts } from "@/lib/data";

// The four places the money can sit, from the model up to the customer: the migration essay's rule applied up the
// stack. Each place's word, readings and test results come from the export; nothing is worked out here.
const MARK: Record<PlaceState, string> = { arriving: "▲", loosening: "◐", moving_on: "▼", not_yet: "·", untestable: "○", not_measured: "○" };
const LOOK: Record<PlaceState, string> = {
  arriving: "border-fast text-ink", loosening: "border-slow text-ink", moving_on: "border-slow text-ink",
  not_yet: "border-ink-2 text-ink", untestable: "border-dashed border-muted text-ink-2", not_measured: "border-dashed border-muted text-ink-2",
};
const answer = (t: PlaceTest) => (t?.holds === true ? "yes" : t?.holds === false ? "not yet" : "can't be tested yet");

function Word({ p }: { p: Place }) {
  return (
    <span className={`inline-flex self-start items-center gap-1.5 rounded-[2px] border-[1.5px] px-2 py-0.5 text-[12.5px] font-medium whitespace-nowrap ${LOOK[p.state]}`}>
      <span aria-hidden className={p.state === "arriving" ? "text-fast" : p.state === "loosening" || p.state === "moving_on" ? "text-slow" : ""}>{MARK[p.state]}</span>
      {p.word}
    </span>
  );
}

export function FourPlaces({ shifts }: { shifts: Shifts | undefined }) {
  if (!shifts?.places.length) return null;
  const chips = shifts.foot_claims.find((c) => c.id === "chips_collect");
  return (
    <Figure
      title="Where the money can sit, from the model up to the customer"
      note="four places up the stack · each tested nightly"
      foot={<>
        <p>
          The rule is the one the <Link href="/argument/migration" className="underline decoration-axis underline-offset-2 hover:decoration-ink">migrating bottleneck</Link> essay sets out: the money goes to whatever cannot be routed around, and moves when that is fixed. Applied up the stack, it passes from the model to running it, to a firm&apos;s own knowledge, to the customer&apos;s front door, as positions in <Link href="/outlook" className="underline decoration-axis underline-offset-2 hover:decoration-ink">what people expect</Link> argue.
          {chips?.state ? <> While the build-out lasts, the chip makers are paid first wherever the money settles: <ClaimState state={chips.state} /></> : null}
        </p>
      </>}
    >
      <ol className="grid gap-px bg-grid md:grid-cols-4">
        {shifts.places.map((p, i) => (
          <li key={p.id} id={`place-${p.id}`} className="flex flex-col gap-3 bg-surface p-4">
            <div className="eyebrow">{`Place ${["one", "two", "three", "four"][i] ?? ""}`}</div>
            <h3 className="font-sans text-[17px] font-bold leading-tight">{p.name}</h3>
            <Word p={p} />
            <p className="font-serif text-[15px] leading-snug text-ink-2">{p.scarce}</p>
            {p.readings.length ? (
              <ul className="flex flex-col gap-2 text-[14px]">
                {p.readings.map((r) => <li key={r.id} className="flex flex-col gap-0.5"><span>{r.label}</span><span><Fact f={r} /> <span className="font-mono text-[11px] text-muted">{r.as_of}</span></span></li>)}
              </ul>
            ) : <p className="text-[14px] text-muted">No reading yet.</p>}
            <dl className="flex flex-col gap-1 border-t border-dashed border-grid pt-2 text-[13px]">
              {p.arriving ? <div><dt className="inline font-medium">Money arriving if {p.arriving.says}: </dt><dd className="inline text-ink-2">{answer(p.arriving)}</dd></div> : null}
              {p.leaving ? <div><dt className="inline font-medium">Moving on if {p.leaving.says}: </dt><dd className="inline text-ink-2">{answer(p.leaving)}</dd></div> : null}
            </dl>
            <p className="text-[13px] text-ink-2"><span className="font-medium text-ink">Who is paid here: </span>{p.sublayers.map((s, k) => <span key={s.id}>{k ? ", " : ""}<Link href={s.href} className="underline decoration-axis underline-offset-2 hover:decoration-ink">{s.name}</Link></span>)}</p>
            <p className="text-[13px] text-ink-2"><span className="font-medium text-ink">What would squeeze it: </span>{p.squeezed_by}</p>
          </li>
        ))}
      </ol>
    </Figure>
  );
}

// The four places as one line of words, for the home page and the essay: the full figure lives on stop 4.
export function FourPlacesCompact({ shifts }: { shifts: Shifts | undefined }) {
  if (!shifts?.places.length) return null;
  return (
    <ol className="flex flex-wrap items-center gap-x-2 gap-y-2 text-[13px]" aria-label="Where the money can sit, tonight">
      {shifts.places.map((p, i) => (
        <li key={p.id} className="flex items-center gap-2">
          {i ? <span aria-hidden className="text-muted">→</span> : null}
          <Link href={`/capture#place-${p.id}`} className="inline-flex items-center gap-1.5 hover:underline"><span className="font-medium">{p.name}</span> <Word p={p} /></Link>
        </li>
      ))}
    </ol>
  );
}
