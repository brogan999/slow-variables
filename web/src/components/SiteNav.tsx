"use client";

import { ChevronDownIcon, MenuIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { ABOUT, MORE, PRIMARY } from "@/lib/nav";

const isCurrent = (path: string, href: string) => (href === "/" ? path === "/" : path === href || path.startsWith(`${href}/`));

export function SiteNav() {
  const path = usePathname();
  return (
    <nav aria-label="Primary" className="hidden md:flex items-center gap-x-5 text-sm text-ink-2">
      {PRIMARY.map(([href, label]) => (
        <Link key={href} href={href} aria-current={isCurrent(path, href) ? "page" : undefined} className={isCurrent(path, href) ? "text-ink font-medium" : "hover:text-ink"}>{label}</Link>
      ))}
      <MoreMenu key={path} path={path} />
    </nav>
  );
}

// A dependency-free disclosure menu: button + list, closes on Escape, outside click and navigation.
function MoreMenu({ path }: { path: string }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const id = useId();
  const current = MORE.some(([h]) => isCurrent(path, h));
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    const onClick = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    return () => { document.removeEventListener("keydown", onKey); document.removeEventListener("mousedown", onClick); };
  }, [open]);
  return (
    <div ref={ref} className="relative">
      <button type="button" aria-expanded={open} aria-controls={id} aria-current={current ? "true" : undefined} onClick={() => setOpen((o) => !o)}
        className={`inline-flex items-center gap-1 rounded-md -mx-1 px-1 py-0.5 hover:text-ink ${current ? "text-ink font-medium" : ""}`}>
        More <ChevronDownIcon aria-hidden className={`size-3.5 opacity-60 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      <ul id={id} hidden={!open} className="absolute left-0 top-full z-40 mt-2 min-w-44 panel p-1.5 flex flex-col">
        {MORE.map(([href, label]) => (
          <li key={href}><Link href={href} aria-current={isCurrent(path, href) ? "page" : undefined} className={`block rounded px-2 py-1 hover:bg-surface-2 ${isCurrent(path, href) ? "text-ink font-medium" : "text-ink-2 hover:text-ink"}`}>{label}</Link></li>
        ))}
      </ul>
    </div>
  );
}

export function MobileNav() {
  const path = usePathname();
  return (
    <Sheet>
      <SheetTrigger render={<Button variant="ghost" size="icon" className="md:hidden" aria-label="Open menu" />}><MenuIcon aria-hidden /></SheetTrigger>
      <SheetContent side="right" className="bg-surface p-5">
        <SheetTitle className="display text-xl">Menu</SheetTitle>
        <nav aria-label="All pages" className="flex flex-col gap-5 text-base">
          {([["Lenses", PRIMARY], ["Depth", MORE], ["About", ABOUT]] as const).map(([group, items]) => (
            <div key={group}>
              <div className="eyebrow mb-2">{group}</div>
              <ul className="flex flex-col gap-1.5">
                {items.map(([href, label]) => (
                  <li key={href}><Link href={href} aria-current={isCurrent(path, href) ? "page" : undefined} className={isCurrent(path, href) ? "text-ink font-medium" : "text-ink-2 hover:text-ink"}>{label}</Link></li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      </SheetContent>
    </Sheet>
  );
}
