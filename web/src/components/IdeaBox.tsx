import { Button } from "@/components/ui/button";
import { IDEA_MAX } from "@/lib/idea";
import { SITE } from "@/lib/site";

// A reader's own business idea: a plain form that opens Ask with the idea wrapped in one fixed question.
export function IdeaBox() {
  if (!SITE.askOnline) return null;
  return (
    <form action="/ask" className="flex flex-col gap-3 rounded-[3px] border border-ink bg-surface p-4 max-w-[68ch]">
      <label htmlFor="idea" className="flex flex-col gap-1">
        <span className="font-semibold">Test a business of your own</span>
        <span className="text-sm text-ink-2 leading-relaxed">Describe it in a sentence or two. Ask, the site&apos;s question box, reasons it through against the value chain: where it sits, what is scarce there, where the profit would pool by the rent rule, which futures help or hurt it, and what would prove it wrong. It ends with a call: build, build on a condition, or don&apos;t build alone.</span>
      </label>
      <input type="hidden" name="from" value="/value-chain/opportunities" />
      <textarea id="idea" name="idea" required rows={2} maxLength={IDEA_MAX} placeholder="For example: a marketplace where insurers buy verified records of agent failures" className="w-full rounded-[3px] border border-border bg-background px-3 py-2 text-sm" />
      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" size="sm">Reason it through</Button>
        <span className="text-xs text-muted">The answer is a model&apos;s reasoning from the site&apos;s records and is not reviewed by a person. Every figure in it is checked against the record it cites.</span>
      </div>
    </form>
  );
}
