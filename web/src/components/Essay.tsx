import type { ReactNode } from "react";
import { Fact } from "@/components/Fact";
import { fmtLine } from "@/lib/format";
import type { ArgumentDoc } from "@/lib/data";

// The argument essays: "# title", a lede, then folios of "### label", "## claim", paragraphs and "[plate:x]" lines.
// Numbers only ever arrive as tokens resolved by the export: [fact:id] a reading, [test:id] the line a claim is tested
// against, [cite:id] the source a sentence rests on (numbered by the export in order of first citation).
const TOKEN = /(\[(?:fact|test|cite):[a-z0-9_]+\])/g;
export type Cites = Record<string, { n: number; who: string; work: string }>;
export type Tests = Record<string, { line: number; unit: string }>;

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

export function Inline({ text, facts, cites, tests }: { text: string; facts: ArgumentDoc["facts"]; cites?: Cites; tests?: Tests }) {
  return <>{text.split(TOKEN).map((p, i) => {
    const m = p.match(/^\[(fact|test|cite):([a-z0-9_]+)\]$/);
    if (!m) return <span key={i}>{p}</span>;
    if (m[1] === "fact") return <Fact key={i} f={facts[m[2]]} />;
    if (m[1] === "test") {
      const t = tests?.[m[2]];
      return t ? <span key={i} className="num text-[0.92em] whitespace-nowrap">{fmtLine(t.line, t.unit)}</span> : null;
    }
    const c = cites?.[m[2]];
    return c ? <sup key={i} className="ml-px"><a href={`#source-${m[2]}`} title={`${c.who}, ${c.work}`} aria-label={`source ${c.n}: ${c.who}, ${c.work}`} className="num text-[0.7em] text-ink-2 hover:text-ink no-underline">{c.n}</a></sup> : null;
  })}</>;
}

export function Folios({ folios, facts, plates, cites, tests, after }: { folios: ReturnType<typeof parseEssay>["folios"]; facts: ArgumentDoc["facts"]; plates: Record<string, ReactNode>; cites?: Cites; tests?: Tests; after?: (label: string, i: number) => ReactNode }) {
  return (
    <>
      {folios.map((f, fi) => (
        <section key={f.label} id={`folio-${(f.label.split("·").pop() ?? "").trim().replace(/^the /, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}`} className="border-t border-grid pt-10 mt-12 first:mt-0 first:border-0 first:pt-0 scroll-mt-8">
          <div className="eyebrow">{f.label}</div>
          <h2 className="display text-[1.875rem] md:text-[2.375rem] leading-[1.08] mt-3 mb-6 max-w-[24ch]">{f.claim}</h2>
          <div className="prose-folio">
            {f.blocks.map((b, i) => {
              const plate = b.match(/^\[plate:([a-z]+)\]$/);
              return plate ? <div key={i} className="fig-slot">{plates[plate[1]]}</div> : <p key={i}><Inline text={b} facts={facts} cites={cites} tests={tests} /></p>;
            })}
          </div>
          {after?.(f.label, fi)}
        </section>
      ))}
    </>
  );
}
