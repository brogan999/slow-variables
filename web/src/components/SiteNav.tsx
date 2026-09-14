"use client";

import { MenuIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { EVIDENCE, PRIMARY } from "@/lib/nav";

const isCurrent = (path: string, href: string) => (href === "/" ? path === "/" : path === href || path.startsWith(`${href}/`));

export function SiteNav() {
  const path = usePathname();
  return (
    <nav aria-label="Primary" className="hidden md:flex items-center gap-x-6 text-sm text-ink-2">
      {PRIMARY.map(([href, label]) => (
        <Link key={href} href={href} aria-current={isCurrent(path, href) ? "page" : undefined} className={isCurrent(path, href) ? "text-ink font-medium" : "hover:text-ink"}>{label}</Link>
      ))}
    </nav>
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
          {([["Read", PRIMARY], ["Evidence", EVIDENCE]] as const).map(([group, items]) => (
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
