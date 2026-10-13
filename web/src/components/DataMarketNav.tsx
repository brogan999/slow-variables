import Link from "next/link";

// The data market's own menu, one row that scrolls sideways on a phone and never wraps.
const PAGES = [["/data-market", "Signals"], ["/data-market/vendors", "Vendors"], ["/data-market/prices", "Prices and pay"], ["/data-market/sources", "Every kind of record"], ["/data-market/dossiers", "Dossiers"]] as const;

export function DataMarketNav({ here }: { here: (typeof PAGES)[number][0] }) {
  return (
    <nav aria-label="The data market" className="-mx-1 flex items-baseline gap-5 overflow-x-auto whitespace-nowrap border-b border-grid px-1 pb-2 text-sm">
      <span className="eyebrow shrink-0">The data market</span>
      {PAGES.map(([href, name]) => (
        <Link key={href} href={href} aria-current={href === here ? "page" : undefined} className={href === here ? "font-medium text-ink" : "text-ink-2 hover:text-ink"}>
          {name}
        </Link>
      ))}
    </nav>
  );
}
