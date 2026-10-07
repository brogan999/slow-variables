import { Button } from "@/components/ui/button";
import { IDEA_MAX } from "@/lib/idea";
import { SITE } from "@/lib/site";

// A reader's own business idea: a plain form that opens Ask with the idea wrapped in one fixed question.
export function IdeaBox({ from = "/value-chain/opportunities" }: { from?: string }) {
  if (!SITE.askOnline) return null;
  return (
    <form action="/ask" className="flex flex-col gap-3 rounded-[3px] border border-ink bg-surface p-4 max-w-[68ch]">
      <label htmlFor="idea-box" className="font-semibold">Test a business of your own</label>
      <p id="idea-what" className="text-sm text-ink-2 leading-relaxed">Describe it in a sentence or two. Ask, the site&apos;s question box, reasons it through against the value chain: where it sits, what is scarce there, where the profit would pool by the rent rule, which of the site&apos;s futures help or hurt it, and what would prove it wrong. It ends with a call on the business: build, build on a condition, or don&apos;t build alone.</p>
      <input type="hidden" name="from" value={from} />
      <textarea id="idea-box" name="idea" required rows={2} maxLength={IDEA_MAX} aria-describedby="idea-what idea-care" placeholder="For example: a marketplace where insurers buy verified records of agent failures" className="w-full rounded-[3px] border border-border bg-background px-3 py-2 text-sm" />
      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" size="sm">Reason it through</Button>
        <p id="idea-care" className="text-xs text-muted max-w-[52ch]">The answer is a model&apos;s reasoning from the site&apos;s records and is not reviewed by a person; its call is a judgement, not advice. Every figure in it is checked against the record it cites. Leave out anything confidential: the idea travels in the page address.</p>
      </div>
    </form>
  );
}
