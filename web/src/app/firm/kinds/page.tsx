import Link from "next/link";
import { Anatomy, KindBars, KindMap, KindPanels, KindShapes, KindSources, NeedsGrid, PanelKey, RollupBars, StageStrip } from "@/components/FirmKinds";
import { firmKinds } from "@/lib/data";

export const metadata = {
  title: "What happens to each kind of firm",
  description: "Kinds of firm, from accounting practices to manufacturers: how much of each one's payroll passes a census screen today, what holds the rest, what each looks like as AI takes on more, and what such firms will need to buy.",
};

const link = "text-ink underline decoration-axis underline-offset-4";
const p = "text-ink-2 leading-relaxed max-w-[68ch]";
const h2 = "display text-[1.6rem] md:text-[2rem] leading-tight scroll-mt-24";

export default function FirmKindsPage() {
  const doc = firmKinds();
  const unmet = doc.needs.filter((n) => !n.opportunities.length).map((n) => n.name.toLowerCase());
  return (
    <div className="flex flex-col gap-8 max-w-[72rem]">
      <div className="flex flex-col gap-3">
        <span className="eyebrow"><Link href="/firm" className="hover:text-ink">Who owns what</Link> · kind by kind</span>
        <h1 className="display text-[2.5rem] md:text-[3.5rem] leading-[1.02]">What happens to each kind of firm</h1>
        <p className={p}>
          <Link href="/firm" className={link}>The page before this one</Link> argues that a firm rents what it can check and owns what it must answer for. This page makes that specific. It takes the kinds of firm below and asks of each: how much of its work can a check settle today, who must still sign, what does it look like as AI takes on more, and what will it need to buy that it does not buy now.
        </p>
        <p className={p}>
          The figures here differ in kind, and each says which it is. A <em>chart</em> draws records: this site&apos;s list of firms bought, and its census, which is a screen scored by AI models. The census covers knowledge work: managers, professional and technical staff including clinicians, sales staff and office staff. A <em>model</em> draws an idea. An <em>illustration</em> is a picture made with AI image generation: an imagined scene that is evidence of nothing, and the words beside it say everything it is there to show. And everything said about what comes next is <em>this site&apos;s judgement</em>, drawn with hatching, with what would prove it wrong beside it.
        </p>
        <p className={p}>
          A task passes the screen when most of the AI models scoring it each find that whether it was done right can be told within hours, that a check which already exists settles it, and that a failure is cheap. Work that needs a body never passes, and nor does a sign-off a person answers for. Passing says nothing about whether today&apos;s AI can do the task.
        </p>
      </div>

      <section className="flex flex-col gap-4" aria-labelledby="today">
        <h2 id="today" className={h2}>Today: little passes, and most of the rest is held for more than a missing check</h2>
        <p className={p}>In no kind of firm does most of the payroll pass the screen. What differs is why. In a law firm and a hospital nearly all of the payroll is work the census covers, and most of it is held: no check that exists today settles it, it is slow to judge or costly when wrong, or it needs a body. A sign-off that a person answers for is only a small part of what holds it. In a freight operator most of the payroll is outside the census altogether, because the census scores knowledge work and not manual, service or production jobs. In a manufacturer and a retailer that outside part is large but not most of the payroll.</p>
        <KindBars doc={doc} />
        <KindShapes doc={doc} />
        <KindMap doc={doc} />
        <RollupBars doc={doc} />
      </section>

      <section className="flex flex-col gap-4" aria-labelledby="stages">
        <h2 id="stages" className={h2}>The stages, on thinner and thinner evidence</h2>
        <p className={p}>An <em>agent</em> is an AI program that carries out a task by itself. Today&apos;s agents work on screens and start each job knowing nothing of the last. The next stage is agents that keep <em>context</em>: what an agent has been told and has seen about a firm or a customer. The one after is robots that do physical work with that knowledge; what this page says of it is <em>extrapolation</em>, a line carried on past the evidence. This site found about as many reversals as successes, and the panels below include them.</p>
        <StageStrip doc={doc} />
      </section>

      <section className="flex flex-col gap-4" aria-labelledby="kinds">
        <h2 id="kinds" className={h2}>Kind by kind</h2>
        <p className={p}>Each panel draws the layers of a firm at each stage, beside a picture of that firm at a later stage as this site imagines it. The first drawing is measured: each layer as wide as its share of today&apos;s knowledge-work payroll, with the part that passes the screen dark. The hatched ones are judgement. This site chose a word for each layer and printed it under the layer; each word is drawn at a fixed width against an outline of today&apos;s, and the widths are not forecast numbers. Where a panel says robots do not bear on a kind of firm, its last drawing repeats the one before.</p>
        <PanelKey doc={doc} />
        <KindPanels doc={doc} />
      </section>

      <section className="flex flex-col gap-4" aria-labelledby="anatomy">
        <h2 id="anatomy" className={h2}>What an AI-run firm looks like</h2>
        <p className={p}>This site drew the same judgement into every panel, so the shape they share is its own view and not a finding. In that view the firm keeps a small group of people who answer for the work. Beneath them sits whatever settles that the work was done right. Beneath that, a wide base that is not employed. The firm rents its thinking and owns what cannot be bought. Kinds of firm differ in how thick the checking layer has to be and in how much of the base is physical.</p>
        <Anatomy doc={doc} />
      </section>

      <section className="flex flex-col gap-4" aria-labelledby="needs">
        <h2 id="needs" className={h2}>Where the opportunity is</h2>
        <p className={p}>If that is the shape, the products these firms lack are mostly in the middle layer and at its edges: a check where none exists, a record of what an agent did and who approved it, a way to get regulated work signed, and insurance that names the software. On the grid below only the check is marked for every kind of firm; the others named here are marked mostly for the kinds where a licence or a regulator stands behind the work. It is this site&apos;s judgement, which nothing on this page tests, that these are better businesses to build than another agent built for a particular trade, because the same product can be sold across trades. Its own list is less sure: it rates the sign-off and the insurance as hard to copy, and the check and the record as easy to copy. The needs with no business on that list yet are these: {unmet.join("; ")}.</p>
        <NeedsGrid doc={doc} />
      </section>

      <section className="flex flex-col gap-3" aria-labelledby="sources">
        <h2 id="sources" className={h2}>Sources</h2>
        <p className="text-xs text-muted max-w-[68ch]">Drafted by a Claude model, made by Anthropic, which is one of the companies these sources discuss and whose model is one of the census&apos;s scorers. Operators&apos; figures are their own unless a source says otherwise. A separate run of a Claude model compared each Now paragraph and each source entry with the fetched pages and asked for corrections, which were made before this was published. That is the same maker&apos;s model checking its own work, not an independent review, and the judgements here have not been tested.</p>
        <KindSources doc={doc} />
      </section>
    </div>
  );
}
