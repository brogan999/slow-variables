import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { ChatDrawer } from "@/components/ChatDrawer";
import { Freshness } from "@/components/Freshness";
import { meta } from "@/lib/data";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: { default: SITE.name, template: `%s · ${SITE.name}` },
  description: SITE.description,
  openGraph: { type: "website", siteName: SITE.name, title: SITE.name, description: SITE.description, url: SITE.url },
  twitter: { card: "summary_large_image", title: SITE.name, description: SITE.description },
};

const NAV = [
  ["/", "Diffusion"], ["/capture", "Capture"], ["/memos", "Memos"], ["/stack", "Stack"], ["/indicators", "Indicators"], ["/predictions", "Predictions"], ["/compare", "Compare"], ["/bottlenecks", "Bottlenecks"], ["/ledger", "Ledger"], ["/crosswalk", "Crosswalk"], ["/query", "Query"],
  ["/sources", "Sources"], ["/methodology", "Methodology"], ["/changelog", "Changelog"],
] as const;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const generated = meta().generated_at;
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-1 focus:ring-hair">Skip to content</a>
        <header className="border-b border-grid">
          <div className="mx-auto max-w-5xl px-4 py-3 flex items-baseline gap-x-5">
            <Link href="/" className="font-semibold tracking-tight shrink-0">{SITE.name}</Link>
            <nav aria-label="Primary" className="min-w-0 flex-1 flex gap-x-4 text-sm text-ink-2 overflow-x-auto whitespace-nowrap md:flex-wrap md:whitespace-normal md:gap-y-1 -mx-1 px-1">
              {NAV.map(([href, label]) => <Link key={href} href={href} className="hover:text-ink">{label}</Link>)}
            </nav>
            <ChatDrawer />
          </div>
        </header>
        <main id="main" className="mx-auto w-full max-w-5xl px-4 py-6 flex-1">{children}</main>
        <footer className="border-t border-grid text-xs text-muted">
          <div className="mx-auto max-w-5xl px-4 py-4 flex flex-wrap gap-x-6 gap-y-1">
            <span>Every number links to the observation behind it.</span>
            <Freshness generatedAt={generated} />
            <span>Fast is not good; concentrating is not good. Status colours carry no verdict.</span>
            <Link href="/methodology" className="hover:text-ink">Reuse, cite, corrections</Link>
          </div>
        </footer>
      </body>
    </html>
  );
}
