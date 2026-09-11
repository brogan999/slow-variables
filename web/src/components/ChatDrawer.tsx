"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";

type Cite = { kind: string; id: string; href: string | null };
type Answer = { answer: string; status: "ok" | "revised" | "blocked"; citations: Cite[]; usage?: { usd: number } };
type State = { kind: "idle" } | { kind: "busy" } | { kind: "answer"; a: Answer } | { kind: "error"; text: string };

const OFFLINE = "The query service is offline right now. Everything on the page still links to its observations.";

// Ask sheet: the question is scoped by the page it was asked from so the model starts in the right lens.
export function ChatDrawer() {
  const path = usePathname();
  const [q, setQ] = useState("");
  const [s, setS] = useState<State>({ kind: "idle" });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    setS({ kind: "busy" });
    try {
      const r = await fetch("/api/query/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: `${q.trim()} (asked from ${path})` }) });
      const j = await r.json();
      if (r.status === 429) setS({ kind: "error", text: "Today's question budget is spent; it resets at midnight UTC." });
      else if (!r.ok) setS({ kind: "error", text: j.error === "offline" ? OFFLINE : `The service answered with an error (${j.error ?? r.status}).` });
      else setS({ kind: "answer", a: j });
    } catch {
      setS({ kind: "error", text: OFFLINE });
    }
  }

  return (
    <Sheet>
      <SheetTrigger render={<Button variant="outline" size="sm" className="rounded-full" />}>Ask</SheetTrigger>
      <SheetContent side="right" aria-describedby="ask-desc" className="bg-surface overflow-y-auto p-5 data-[side=right]:sm:max-w-md">
        <SheetHeader className="p-0">
          <SheetTitle className="display text-2xl">Ask the data</SheetTitle>
          <SheetDescription id="ask-desc" className="text-muted">Answers come from the same store as the site; every number is checked against the record it cites.</SheetDescription>
        </SheetHeader>
        <form onSubmit={submit} className="flex flex-col gap-3">
          <Textarea value={q} onChange={(e) => setQ(e.target.value)} rows={3} placeholder="What is the latest 50% horizon and its doubling time?" aria-label="Question" className="bg-background" />
          <div className="flex items-center justify-between gap-3">
            <span className="eyebrow">{path}</span>
            <Button type="submit" size="sm" disabled={s.kind === "busy"}>{s.kind === "busy" ? "Asking…" : "Ask"}</Button>
          </div>
          <div aria-live="polite" className="text-sm leading-relaxed">
            {s.kind === "error" ? <p className="text-slow">{s.text}</p> : null}
            {s.kind === "answer" ? <AnswerView a={s.a} /> : null}
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

function AnswerView({ a }: { a: Answer }) {
  const parts = a.answer.split(/(\[(?:obs|derived|ind|event):[A-Za-z0-9_.-]+\]|⟦unverified: [^⟧]*⟧)/g);
  const byId = new Map(a.citations.map((c) => [`[${c.kind}:${c.id}]`, c]));
  return (
    <div className="flex flex-col gap-2">
      {a.status === "blocked" ? <p className="text-slow text-xs">This answer failed the citation check twice; the unverified numbers are marked and should not be relied on.</p> : null}
      <p>
        {parts.map((p, i) => {
          const c = byId.get(p);
          if (c) return c.href ? <Link key={i} href={c.href} className="font-mono text-[11px] text-ink-2 underline decoration-grid underline-offset-2">{c.kind}:{c.id.slice(0, 8)}</Link> : <span key={i} className="font-mono text-[11px] text-muted">{p}</span>;
          if (p.startsWith("⟦")) return <mark key={i} className="bg-slow/15 text-slow">{p.slice(1, -1)}</mark>;
          return <span key={i}>{p}</span>;
        })}
      </p>
      {a.status === "revised" ? <p className="text-xs text-muted">Revised once after the citation check.</p> : null}
    </div>
  );
}
