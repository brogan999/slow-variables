"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// aria-current on the section the reader is in; nested routes (/indicators/x) light their index entry.
export function NavLinks({ items }: { items: readonly (readonly [string, string])[] }) {
  const path = usePathname();
  return (
    <>
      {items.map(([href, label]) => {
        const current = href === "/" ? path === "/" : path === href || path.startsWith(`${href}/`);
        return <Link key={href} href={href} aria-current={current ? "page" : undefined} className={current ? "text-ink font-medium" : "hover:text-ink"}>{label}</Link>;
      })}
    </>
  );
}
