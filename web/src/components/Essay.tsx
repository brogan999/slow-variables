import type { ReactNode } from "react";
import { Fact } from "@/components/Fact";
import type { ArgumentDoc } from "@/lib/data";

// The argument essays: "# title", a lede, then folios of "### label", "## claim", paragraphs and "[plate:x]" lines.
// Numbers only ever arrive as [fact:id] tokens resolved by the export.
const TOKEN = /(\[fact:[a-z0-9_]+\])/g;

export function parseEssay(md: string) {
  const blocks = md.split(/\n{2,}/).map((b) => b.trim()).filter(Boolean);
  const title = blocks[0]?.startsWith("# ") ? blocks.shift()!.slice(2) : "";
  const lede = blocks.shift() ?? "";
  const folios: { label: string; claim: string; blocks: string[] }[] = [];
  for (const b of blocks) {
    if (b.startsWith("### ")) folios.push({ label: b.slice(4), claim: "", blocks: [] });
    else if (b.startsWith("## ") && folios.length) folios[folios.length - 1].claim = b.slice(3);
    else folios[folios.length - 1]?.blocks.push(b);
  }
  return { title, lede, folios };
}

export function Inline({ text, facts }: { text: string; facts: ArgumentDoc["facts"] }) {
  return <>{text.split(TOKEN).map((p, i) => {
    const m = p.match(/^\[fact:([a-z0-9_]+)\]$/);
    return m ? <Fact key={i} f={facts[m[1]]} /> : <span key={i}>{p}</span>;
  })}</>;
}

export function Folios({ folios, facts, plates }: { folios: ReturnType<typeof parseEssay>["folios"]; facts: ArgumentDoc["facts"]; plates: Record<string, ReactNode> }) {
  return (
    <>
      {folios.map((f) => (
        <section key={f.label} id={`folio-${f.label.split("·").pop()?.trim().replace(/^the /, "").replace(/\s+/g, "-")}`} className="border-t border-grid pt-10 mt-12 first:mt-0 first:border-0 first:pt-0 scroll-mt-8">
          <div className="eyebrow">{f.label}</div>
          <h2 className="display text-[1.875rem] md:text-[2.375rem] leading-[1.08] mt-3 mb-6 max-w-[24ch]">{f.claim}</h2>
          <div className="prose-folio">
            {f.blocks.map((b, i) => {
              const plate = b.match(/^\[plate:([a-z]+)\]$/);
              return plate ? <div key={i} className="fig-slot">{plates[plate[1]]}</div> : <p key={i}><Inline text={b} facts={facts} /></p>;
            })}
          </div>
        </section>
      ))}
    </>
  );
}
