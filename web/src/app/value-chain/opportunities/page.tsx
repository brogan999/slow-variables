import Link from "next/link";
import { PowersGlossary } from "@/components/ValueChain";
import { IdeaBox } from "@/components/IdeaBox";
import { Opportunities } from "@/components/Opportunities";
import { TurnModel } from "@/components/OpportunityFigures";
import { opportunities } from "@/lib/data";

export const metadata = {
  title: "What could be built on the value chain",
  description: "Businesses that could be built where the value chain is short of something, each with the profit the site's rent rule gives it and what would prove it wrong.",
};

export default function OpportunitiesPage() {
  const d = opportunities();
  return (
    <div className="flex flex-col gap-8 max-w-[72rem]">
      <div className="flex flex-col gap-3">
        <span className="eyebrow"><Link href="/value-chain" className="hover:text-ink">The value chain</Link> · what could be built</span>
        <h1 className="display text-[2.5rem] md:text-[3.5rem] leading-[1.02]">Businesses that could be built</h1>
        <p className="text-ink-2 leading-relaxed max-w-[68ch]">
          The <Link href="/value-chain" className="underline decoration-grid underline-offset-4">value chain</Link> page judges where each part&apos;s economics are heading, and names what would turn a passing shortage into a lasting profit. Each business below is one that could make such a turn happen: what it would sell first, what it would build up, why the largest AI companies would not simply give it away, and what would prove it wrong. Each is a business described, not a company named: the companies listed with it are the ones the tracker has already placed in the same part of the map, and some may be building something like it.
        </p>
        <p className="text-ink-2 leading-relaxed max-w-[68ch]">
          A few words recur. An <em>agent</em> is an AI program that carries out a task on its own, such as filing a claim or booking a purchase, rather than only answering questions. A <em>lab</em> is a company that builds the largest AI models, such as OpenAI or Anthropic, and a <em>cloud</em> is a company that rents out computing, such as Amazon or Microsoft; both can bundle extra services into what they already sell. A <em>roll-up</em> is a firm that buys many small businesses in one trade and runs them together, and a <em>system of record</em> is the software where a firm keeps the official copy of its work, such as a law firm&apos;s case files.
        </p>
        <p className="text-ink-2 leading-relaxed max-w-[68ch]">
          A <em>rent</em> is profit beyond what it takes to keep a business going, earned because something holds rivals off. The profit shown on each business comes from the rent rule the <Link href="/futures" className="underline decoration-grid underline-offset-4">futures</Link> section uses. Who keeps the profit follows David Teece, an economist who studied why the firm that invents something often fails to keep the returns, and found that when an invention is easy to copy, whoever owns what customers need to use it collects instead. How large it is follows the kind of rent and how long it lasts, from none through thin, moderate and fat to monopoly-like; moderate is set where William Nordhaus, an economist who measured how much of an invention&apos;s value its maker keeps, found it usually sits: a small share. The answers about each case are the owner&apos;s judgement; the result follows the rule. Some businesses keep no lasting profit at all; they are listed anyway, because knowing what will not hold is as useful as knowing what will.
        </p>
        <PowersGlossary powers={d.powers} />
      </div>
      <p className="text-ink-2 leading-relaxed max-w-[68ch]">For a call on each of these, and what each future on the outlook&apos;s grid would do to it, see <Link href="/value-chain/atlas" className="underline decoration-grid underline-offset-4">what to build, future by future</Link>.</p>
      <IdeaBox />
      <TurnModel d={d} />
      <Opportunities d={d} />
      <p className="text-xs text-muted max-w-[68ch]">Drafted by a model from the site&apos;s readings and reviewed by {d.reviewed_by}, who set the order and released every record. What each needs first, who would buy it and the next step were drafted by a model; a company is named as a buyer only where this site&apos;s deal ledgers record the purchase. These are conditions, not forecasts: nothing here is scored.</p>
    </div>
  );
}
