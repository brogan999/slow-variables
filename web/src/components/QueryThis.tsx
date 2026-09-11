"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

// L3's "query this" box: opens the Ask sheet with the question; the sheet adds this page's path, which names the series.
export function QueryThis({ seriesKey }: { seriesKey: string }) {
  const [q, setQ] = useState("");
  return (
    <form
      className="flex flex-wrap items-center gap-2"
      onSubmit={(e) => { e.preventDefault(); window.dispatchEvent(new CustomEvent("ask:open", { detail: { q: q.trim() || `What does ${seriesKey} show, and how far can it be trusted?` } })); }}
    >
      <label htmlFor="query-this" className="sr-only">Ask about this series</label>
      <Input id="query-this" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask about this series…" className="bg-background max-w-md text-sm" />
      <Button type="submit" size="sm" variant="outline">Query this series</Button>
    </form>
  );
}
