import Link from "next/link";
import { KIND_LABEL } from "@/components/diagrams/kit";
import type { StoryPanelDoc } from "@/lib/data";

const KIND = { ...KIND_LABEL, mixed: "Part chart, part judgement" } as const;

// One panel of /story: a figure from another page, drawn as it is there with its long foot and folded table hidden
// (globals.css), the story's sentences above it, and beneath it the caveats the foot carried and the way to the rest.
export function StoryPanel({ p, stop, children }: { p: StoryPanelDoc; stop: string; children: React.ReactNode }) {
  const { href, words, carry } = p;
  return (
    <article id={`panel-${p.id}`} className="flex flex-col gap-3 scroll-mt-14">
      <div className="eyebrow">{stop} · {KIND[p.kind]}</div>
      <p className="max-w-[62ch] font-serif text-lg leading-relaxed text-ink md:text-[1.2rem]">{words.join(" ")}</p>
      <div className="story-fig min-w-0">{children}</div>
      <p className="max-w-[48rem] text-[14px] leading-relaxed text-ink-2"><span className="mr-2 font-mono text-[10.5px] uppercase tracking-[0.08em] text-muted">Read it with this</span>{carry.join(" ")}</p>
      <Link href={href} prefetch={false} className="self-start text-sm font-medium underline decoration-axis underline-offset-4 hover:decoration-ink">The full figure, what it leaves out, and its numbers →</Link>
    </article>
  );
}
