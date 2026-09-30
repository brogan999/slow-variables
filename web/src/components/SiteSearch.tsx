"use client";

import { SearchIcon } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { EVIDENCE, STOPS } from "@/lib/nav";

type Hit = { k: string; t: string; s: string; h: string; a?: string[] };
const PAGES: Hit[] = [
  ...STOPS.map((s) => ({ k: "Page", t: `${s.n} · ${s.name}`, s: s.question, h: s.href })),
  ...EVIDENCE.map(([h, t]) => ({ k: "Page", t, s: "Evidence", h })),
];
const PER_KIND = 8;

/** Site search: every word typed must appear in a record's title, line or aliases. The index loads on first open. */
export function SiteSearch() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [index, setIndex] = useState<Hit[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [active, setActive] = useState(0);
  const loading = useRef(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      // Cmd-K on a Mac (Ctrl-K there deletes to the end of a line), Ctrl-K elsewhere
      const mod = /Mac|iP/.test(navigator.platform) ? e.metaKey : e.ctrlKey;
      if (mod && !e.shiftKey && !e.altKey && e.key?.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!open || index || loading.current) return;
    loading.current = true;
    setFailed(false);
    fetch("/search.json")
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: Hit[]) => setIndex(d))
      .catch(() => setFailed(true))
      .finally(() => { loading.current = false; });
  }, [open, index]);

  const { groups, total } = useMemo(() => {
    const words = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!words.length) return { groups: [] as [string, Hit[]][], total: 0 };
    const out = new Map<string, Hit[]>();
    let total = 0;
    for (const hit of [...PAGES, ...(index ?? [])]) {
      const hay = `${hit.t} ${hit.s} ${(hit.a ?? []).join(" ")}`.toLowerCase();
      if (!words.every((w) => hay.includes(w))) continue;
      total += 1;
      const list = out.get(hit.k) ?? [];
      if (list.length < PER_KIND) list.push(hit);
      out.set(hit.k, list);
    }
    return { groups: [...out.entries()], total };
  }, [q, index]);
  const flat = useMemo(() => groups.flatMap(([, hits]) => hits), [groups]);
  // each group's first result index in `flat`, so a result's position is derived, never counted while rendering
  const starts = useMemo(() => groups.reduce<number[]>((acc, _group, g) => [...acc, g ? acc[g - 1] + groups[g - 1][1].length : 0], []), [groups]);
  useEffect(() => { document.getElementById(`search-hit-${active}`)?.scrollIntoView({ block: "nearest" }); }, [active]);

  const go = (h: string) => {
    setOpen(false);
    setQ("");
    // pushState fires no hashchange, so a same-page anchor is set directly and the folded section it sits in opens
    const [path, hash] = h.split("#");
    if (hash && path === window.location.pathname) window.location.hash = hash;
    else router.push(h);
  };
  const onKeyDown = (e: React.KeyboardEvent) => {
    if (!flat.length || e.nativeEvent.isComposing) return;
    if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => (a + 1) % flat.length); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => (a - 1 + flat.length) % flat.length); }
    else if (e.key === "Enter") { e.preventDefault(); go(flat[active]?.h ?? flat[0].h); }
  };

  return (
    <Sheet open={open} onOpenChange={(o) => { setOpen(o); if (!o) setQ(""); }}>
      <SheetTrigger render={<Button variant="ghost" size="sm" aria-label="Search the site" aria-keyshortcuts="Meta+K Control+K" className="gap-1.5" />}>
        <SearchIcon aria-hidden className="size-4" /><span className="hidden sm:inline">Search</span>
      </SheetTrigger>
      <SheetContent side="top" className="bg-surface p-4 md:p-6 max-h-[85vh] overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl flex flex-col gap-3">
          <SheetTitle className="display text-xl">Search</SheetTitle>
          <SheetDescription className="text-sm text-ink-2">Indicators, forecasts, claims, companies, sources, jobs and pages. Every word you type must match.</SheetDescription>
          <Input
            autoFocus
            value={q}
            onChange={(e) => { setQ(e.target.value); setActive(0); }}
            onKeyDown={onKeyDown}
            placeholder="Try: inference, Harvey, chip share"
            role="combobox"
            aria-autocomplete="list"
            aria-expanded={flat.length > 0}
            aria-controls="search-results"
            aria-activedescendant={flat.length ? `search-hit-${active}` : undefined}
            aria-label="Search the site"
            className="bg-background text-base"
          />
          <p className="sr-only" aria-live="polite">{q ? (total > flat.length ? `${total} matches; the first ${PER_KIND} of each kind are shown` : `${total} matches`) : ""}</p>
          {failed ? <p className="text-sm text-error">The search index did not load. Try again later, or use the menu.</p> : null}
          {q && !flat.length && (index || failed) ? <p className="text-sm text-ink-2">Nothing matches every word. Try fewer words.</p> : null}
          {q && !index && !failed ? <p className="text-sm text-muted">Loading the index…</p> : null}
          <div id="search-results" role="listbox" aria-label="Results" className="flex flex-col gap-4">
            {groups.map(([kind, hits], g) => (
              <div key={kind} role="group" aria-label={kind} className="flex flex-col">
                <div aria-hidden className="eyebrow mb-1">{kind}{hits.length === PER_KIND ? " · first eight" : ""}</div>
                  {hits.map((hit, j) => {
                    const i = starts[g] + j;
                    return (
                      <Link key={`${hit.k}-${hit.h}-${hit.t}`} href={hit.h} prefetch={false} tabIndex={-1} id={`search-hit-${i}`} role="option" aria-selected={i === active}
                        onMouseEnter={() => setActive(i)} onClick={(e) => { if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return; e.preventDefault(); go(hit.h); }}
                        className={`block rounded-[3px] px-2 py-1.5 ${i === active ? "bg-surface-2" : ""}`}>
                        <span className="block font-medium text-ink">{hit.t}</span>
                        {hit.s ? <span className="text-xs text-ink-2 line-clamp-1">{hit.s}</span> : null}
                      </Link>
                    );
                  })}
              </div>
            ))}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
