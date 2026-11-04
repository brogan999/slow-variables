import Link from "next/link";
import { Sources, link } from "@/components/FuturesParts";
import { FuturesTree } from "@/components/FuturesTree";
import { futuresTree } from "@/lib/data";
import { fmt } from "@/lib/format";

export const metadata = {
  title: "The technology tree: what each imagined technology waits on",
  description: "The unbuilt technologies of science fiction laid out by kind and by decade, with what each waits on, what must come first, and which seller would keep the profit. A model's judgement, labelled as one.",
};

export default function FuturesTreePage() {
  const d = futuresTree();
  return (
    <div className="flex flex-col gap-8 max-w-[72rem]">
      <div className="flex flex-col gap-3">
        <span className="eyebrow"><Link href="/futures" className="hover:text-ink">Futures</Link> · the technology tree</span>
        <h1 className="display text-[2.5rem] md:text-[3.5rem] leading-[1.02]">The technology tree</h1>
        <p className="font-serif text-lg md:text-[1.3rem] leading-relaxed text-ink-2 max-w-[62ch]">
          Strategy games give their players a technology tree: a chart of what can be invented, and what has to be invented first. This page draws one for the technologies science fiction imagined and nobody has built.
        </p>
        <p className="text-ink-2 leading-relaxed max-w-[68ch]">
          Each tile, called a <em>node</em> here, stands for one kind of technology in one decade: the decade in which AI models judged a working version most likely. The number on a node counts the ideas there that a model judged a <em>large</em> prize, one that would change a whole industry, or a <em>vast</em> one, which would change how most people live or work. The bar beside it shows which seller would keep what is left once buyers have had their gain.
        </p>
        <p className="text-ink-2 leading-relaxed max-w-[68ch]">
          A node waits on a <em>gate</em>: the thing more of its ideas were judged to need, before they can exist, than any other; when two tie, the nearer gate is taken. Tick a gate to assume it has happened. A node that waits on nothing new is lit from the start. Any other lights only when its own gate is ticked and every node it comes after is lit, so some gates open nothing until an earlier one is ticked. The count under the gates follows what is lit. Choose any node to read what the stories put there.
        </p>
        <p className="text-[13px] text-muted max-w-[68ch]">
          The board shows {fmt(d.on_board, "count")} such prizes. It leaves off {fmt(d.left_off.n, "count")} more: ideas judged not physically possible or given no decade, ideas in a decade the model gave no node, and every idea of these kinds, which have no row: {d.left_off.kinds.map((k) => k.toLowerCase()).join("; ")}. <Link href="/futures#categories" className={link}>Every kind has its own page</Link>.
        </p>
      </div>
      <FuturesTree d={d} />
      <Sources />
    </div>
  );
}
