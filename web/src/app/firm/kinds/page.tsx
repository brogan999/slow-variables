import Link from "next/link";
import { Anatomy, KindBars, KindMap, KindPanels, KindShapes, KindSources, NeedsGrid, RollupBars, StageStrip } from "@/components/FirmKinds";
import { firmKinds } from "@/lib/data";

export const metadata = {
  title: "What happens to each kind of firm",
  description: "Twelve kinds of firm, from accounting practices to manufacturers: how much of each one's work a check can settle today, what each looks like as AI takes on more, and what such firms will need to buy.",
};

const link = "text-ink underline decoration-axis underline-offset-4";
const p = "text-ink-2 leading-relaxed max-w-[68ch]";
const h2 = "display text-[1.6rem] md:text-[2rem] leading-tight scroll-mt-24";

export default function FirmKindsPage() {
  const doc = firmKinds();
  return (
    <div className="flex flex-col gap-8 max-w-[72rem]">
      <div className="flex flex-col gap-3">
        <span className="eyebrow"><Link href="/firm" className="hover:text-ink">Who owns what</Link> · kind by kind</span>
        <h1 className="display text-[2.5rem] md:text-[3.5rem] leading-[1.02]">What happens to each kind of firm</h1>
        <p className={p}>
          <Link href="/firm" className={link}>The page before this one</Link> argues that a firm rents what it can check and owns what it must answer for. This page makes that specific. It takes twelve kinds of firm and asks of each: how much of its work can a check settle today, who must still sign, what does it look like as AI takes on more, and what will it need to buy that it does not buy now.
        </p>
        <p className={p}>
          Three things here are different in kind, and each figure says which it is. A <em>chart</em> draws records: this site&apos;s census, which is a screen scored by AI models, and its list of firms bought. A <em>model</em> draws an idea. And everything said about what comes next is <em>this site&apos;s judgement</em>, drawn with hatching, with what would prove it wrong beside it.
        </p>
      </div>

      <section className="flex flex-col gap-4" aria-labelledby="today">
        <h2 id="today" className={h2}>Today: little passes, and most of the rest waits on a check or a signature</h2>
        <p className={p}>In no kind of firm does most of the payroll pass the screen. What differs is why. A law firm and a hospital are held by who must sign. A freight operator, a manufacturer and a retailer are mostly work the census cannot see, because it is not done at a desk.</p>
        <KindBars doc={doc} />
        <KindShapes doc={doc} />
        <KindMap doc={doc} />
        <RollupBars doc={doc} />
      </section>

      <section className="flex flex-col gap-4" aria-labelledby="stages">
        <h2 id="stages" className={h2}>Three stages, on thinner and thinner evidence</h2>
        <p className={p}>An <em>agent</em> is an AI program that carries out a task by itself. Today&apos;s agents work on screens and start each job knowing nothing of the last. The next stage is agents that keep what they learn about one firm or one customer. The one after is robots that do physical work with that knowledge. Reversals are as well recorded as successes, and the panels below include them.</p>
        <StageStrip doc={doc} />
      </section>

      <section className="flex flex-col gap-4" aria-labelledby="kinds">
        <h2 id="kinds" className={h2}>Kind by kind</h2>
        <p className={p}>Each panel draws the firm three times. The first drawing is measured: layers as wide as their share of today&apos;s office payroll. The hatched ones are judgement: each layer drawn thinner or wider by a word this site chose, on a fixed scale, not by a forecast number.</p>
        <KindPanels doc={doc} />
      </section>

      <section className="flex flex-col gap-4" aria-labelledby="anatomy">
        <h2 id="anatomy" className={h2}>What an AI-run firm looks like</h2>
        <p className={p}>Put the panels side by side and one shape recurs. The firm keeps a small group of people who answer for the work. Beneath them sits whatever settles that the work was done right. Beneath that, a wide base that is not employed. The firm rents its thinking and owns what cannot be bought. Kinds of firm differ in how thick the checking layer has to be and in how much of the base is physical.</p>
        <Anatomy doc={doc} />
      </section>

      <section className="flex flex-col gap-4" aria-labelledby="needs">
        <h2 id="needs" className={h2}>Where the opportunity is</h2>
        <p className={p}>If that is the shape, the products these firms lack are mostly in the middle layer and at its edges: a check where none exists, a record of what an agent did and who approved it, a way to get regulated work signed, and insurance that names the software. They are needed across nearly every kind of firm, which is why this site judges them the better businesses to build than another agent for one trade. Four needs have no business on this site&apos;s list yet: training people once the junior work is gone, people on call, running autonomy in stages, and running robots.</p>
        <NeedsGrid doc={doc} />
      </section>

      <section className="flex flex-col gap-3" aria-labelledby="sources">
        <h2 id="sources" className={h2}>Sources</h2>
        <p className="text-xs text-muted max-w-[68ch]">Drafted by a Claude model, made by Anthropic, which is one of the companies these sources discuss and whose model is one of the census&apos;s three scorers. Operators&apos; figures are their own unless a source says otherwise. A separate model run checked every source and attribution before this was published.</p>
        <KindSources doc={doc} />
      </section>
    </div>
  );
}
