"use client";

import { ChevronDownIcon, MenuIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";

import { ABOUT, MORE, PRIMARY } from "@/lib/nav";

const isCurrent = (path: string, href: string) => (href === "/" ? path === "/" : path === href || path.startsWith(`${href}/`));

export function SiteNav() {
  const path = usePathname();
  const moreCurrent = MORE.some(([h]) => isCurrent(path, h));
  return (
    <>
      <nav aria-label="Primary" className="hidden md:flex items-center gap-x-5 text-sm text-ink-2">
        {PRIMARY.map(([href, label]) => (
          <Link key={href} href={href} aria-current={isCurrent(path, href) ? "page" : undefined} className={isCurrent(path, href) ? "text-ink font-medium" : "hover:text-ink"}>{label}</Link>
        ))}
        <DropdownMenu>
          <DropdownMenuTrigger render={<Button variant="ghost" size="sm" className={`-mx-2 px-2 font-normal text-sm ${moreCurrent ? "text-ink font-medium" : "text-ink-2"}`} />}>
            More <ChevronDownIcon aria-hidden className="opacity-60" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="min-w-44">
            {MORE.map(([href, label]) => (
              <DropdownMenuItem key={href} render={<Link href={href} aria-current={isCurrent(path, href) ? "page" : undefined} />} className={isCurrent(path, href) ? "font-medium" : ""}>{label}</DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </nav>
      <Sheet>
        <SheetTrigger render={<Button variant="ghost" size="icon" className="md:hidden" aria-label="Open menu" />}><MenuIcon aria-hidden /></SheetTrigger>
        <SheetContent side="right" className="bg-surface">
          <SheetTitle className="display text-xl">Slow Variables</SheetTitle>
          <nav aria-label="All pages" className="flex flex-col gap-5 text-base">
            {[["Lenses", PRIMARY], ["Depth", MORE], ["About", ABOUT]].map(([group, items]) => (
              <div key={group as string}>
                <div className="eyebrow mb-2">{group as string}</div>
                <ul className="flex flex-col gap-1.5">
                  {(items as readonly (readonly [string, string])[]).map(([href, label]) => (
                    <li key={href}><Link href={href} aria-current={isCurrent(path, href) ? "page" : undefined} className={isCurrent(path, href) ? "text-ink font-medium" : "text-ink-2 hover:text-ink"}>{label}</Link></li>
                  ))}
                </ul>
              </div>
            ))}
          </nav>
        </SheetContent>
      </Sheet>
    </>
  );
}
