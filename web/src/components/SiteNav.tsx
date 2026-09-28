"use client";

import { MenuIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { ACTS, EVIDENCE, STOPS } from "@/lib/nav";

const under = (path: string, href: string) => path === href || path.startsWith(`${href}/`);
// Only the most specific matching link is current, so a deep dive never marks its parent too.
const current = (path: string) =>
  [...STOPS.map((s) => s.href), ...EVIDENCE.map(([h]) => h)].filter((h) => under(path, h)).sort((a, b) => b.length - a.length)[0];

/** The one full menu, at every width: the path by act, then the evidence. Following a link closes it. */
export function SiteMenu() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const here = current(path);
  const item = (href: string, label: string, n?: string) => (
    <li key={href}>
      <Link href={href} onClick={() => setOpen(false)} aria-current={href === here ? "page" : undefined} className={`inline-flex gap-2 ${href === here ? "text-ink font-medium" : "text-ink-2 hover:text-ink"}`}>
        {n ? <span className="num w-6 text-muted">{n}</span> : null}{label}
      </Link>
    </li>
  );
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger render={<Button variant="ghost" size="sm" aria-label="Open menu" className="gap-1.5" />}><MenuIcon aria-hidden className="size-4" /><span className="hidden sm:inline">Menu</span></SheetTrigger>
      <SheetContent side="right" className="bg-surface p-5 overflow-y-auto">
        <SheetTitle className="display text-xl">Menu</SheetTitle>
        <nav aria-label="All pages" className="flex flex-col gap-5 text-base">
          {ACTS.map((a) => (
            <div key={a.act}>
              <div className="eyebrow mb-2">Act {a.act} · {a.title}</div>
              <ul className="flex flex-col gap-1.5">{a.stops.map((s) => item(s.href, s.name, s.n))}</ul>
            </div>
          ))}
          <div>
            <div className="eyebrow mb-2">Evidence</div>
            <ul className="flex flex-col gap-1.5">{EVIDENCE.map(([href, label]) => item(href, label))}</ul>
          </div>
        </nav>
      </SheetContent>
    </Sheet>
  );
}
