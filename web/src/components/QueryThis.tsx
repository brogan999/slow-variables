import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

// L3's "query this" box: a plain form that opens Ask with the question and this series' page as its context.
export function QueryThis({ seriesKey }: { seriesKey: string }) {
  return (
    <form action="/ask" className="flex flex-wrap items-center gap-2">
      <label htmlFor="query-this" className="sr-only">Ask about this series</label>
      <input type="hidden" name="from" value={`/series/${seriesKey}`} />
      <Input id="query-this" name="q" required placeholder="Ask about this series…" className="bg-background max-w-md text-sm" />
      <Button type="submit" size="sm" variant="outline">Query this series</Button>
    </form>
  );
}
