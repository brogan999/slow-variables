import Link from "next/link";
import { ChainAtlas } from "@/components/ChainAtlas";
import { ChainTerms } from "@/components/ChainTerms";
import { IdeaBox } from "@/components/IdeaBox";
import { chainAtlas } from "@/lib/data";

export const metadata = {
  title: "What to build, future by future",
  description: "A call on each business that could be built on the AI value chain, and what each future on the outlook's grid would do to it. A model's judgement, labelled as one.",
};

const link = "underline decoration-grid underline-offset-4";

export default function ChainAtlasPage() {
  const d = chainAtlas();
  return (
    <div className="flex flex-col gap-8 max-w-[72rem]">
      <div className="flex flex-col gap-3">
        <span className="eyebrow"><Link href="/value-chain" className="hover:text-ink">The value chain</Link> · what to build</span>
        <h1 className="display text-[2.5rem] md:text-[3.5rem] leading-[1.02]">What to build, future by future</h1>
        <p className="text-ink-2 leading-relaxed max-w-[68ch]">
          The site lists <Link href="/value-chain/opportunities" className={link}>businesses that could be built</Link> where the value chain is short of something. This page takes a position on each: build it, build it on a condition, or don&apos;t build it alone, with one line of reasoning. Then it asks what each future would do to that business. A <em>future</em> here is one square of the grid on the <Link href="/outlook" className={link}>outlook</Link> page: how far AI goes, crossed with how the rules settle. Only the squares a named writer argues for are used.
        </p>
        <p className="text-ink-2 leading-relaxed max-w-[68ch]">
          Choose a future and the businesses it strengthens fill in, the ones it weakens turn to a dashed outline, any it breaks are struck through, and the rest fade. A business that some future strengthens and none weakens is marked. Open any row for the problem it solves, the profit the site&apos;s rent rule gives it, what would overturn the call, and the reason behind each future&apos;s effect. Every call and every effect is a model&apos;s judgement, not a reading, and each is labelled.
        </p>
        <ChainTerms />
        <p className="text-ink-2 leading-relaxed max-w-[68ch]">
          The <em>value chain</em> is the run of businesses from power and chips to the products people use. A <em>rent</em> is profit beyond what it takes to keep a business going, and the <em>rent rule</em> is how this site judges who would keep it and how large it would be; the <Link href="/value-chain/opportunities" className={link}>businesses page</Link> sets it out. An <em>open model</em> is one whose maker publishes it for anyone to run, and <em>tuning</em> is adjusting such a model for one kind of work. An <em>identity firm</em> is a company that confirms who a person or a program is before another system lets it in.
        </p>
      </div>
      <div id="ca-own" className="scroll-mt-24"><IdeaBox from="/value-chain/atlas" /></div>
      <ChainAtlas d={d} />
    </div>
  );
}
