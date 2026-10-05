import type { Metadata } from "next";
import { Archivo, IBM_Plex_Mono, Newsreader } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { AskPanel } from "@/components/AskPanel";
import { Freshness } from "@/components/Freshness";
import { HoverLayer } from "@/components/HoverLayer";
import { HatchDefs } from "@/components/chart";
import { JourneyRail, NextStop } from "@/components/Journey";
import { OpenOnHash } from "@/components/OpenOnHash";
import { SiteMenu } from "@/components/SiteNav";
import { SiteSearch } from "@/components/SiteSearch";
import { ACTS } from "@/lib/nav";
import { meta } from "@/lib/data";
import { SITE } from "@/lib/site";

const sans = Archivo({ subsets: ["latin"], variable: "--font-archivo", display: "swap" });
const serif = Newsreader({ subsets: ["latin"], style: ["normal", "italic"], axes: ["opsz"], variable: "--font-newsreader", display: "swap" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-plex-mono", display: "swap" });

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: { default: SITE.name, template: `%s · ${SITE.name}` },
  description: SITE.description,
  openGraph: { type: "website", siteName: SITE.name, title: SITE.name, description: SITE.description, url: SITE.url },
  twitter: { card: "summary_large_image" }, // title, description and image come from each page's openGraph
};


export default function RootLayout({ children }: { children: React.ReactNode }) {
  const generated = meta().generated_at;
  return (
    <html lang="en" className={`${serif.variable} ${sans.variable} ${mono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-1 focus:ring-hair">Skip to content</a>
        <header className="border-b border-grid">
          <div className="mx-auto max-w-[82rem] px-4 md:px-8 py-4 flex items-center gap-x-6">
            <Link href="/" className="display text-[1.375rem] shrink-0">{SITE.name}</Link>
            <div className="flex-1" />
            <div className="flex items-center gap-x-2 shrink-0 text-sm">
              <Link href="/indicators" className="hidden sm:inline text-ink-2 hover:text-ink px-2">Evidence</Link>
              <SiteSearch />
              {SITE.askOnline ? <Link href="/ask" className="inline-flex h-7 items-center rounded-[3px] border border-border bg-background px-2.5 text-[0.8rem] font-medium hover:bg-surface-2">Ask</Link> : null}
              <SiteMenu />
            </div>
          </div>
        </header>
        <main id="main" className="mx-auto w-full max-w-[82rem] px-4 md:px-8 py-8 md:py-12 flex-1"><JourneyRail />{children}<NextStop /></main>
        <footer className="border-t border-grid mt-16">
          <div className="mx-auto max-w-[82rem] px-4 md:px-8 py-10 flex flex-col gap-6 text-sm">
            <nav aria-label="All stops" className="flex flex-wrap gap-x-8 gap-y-2 text-ink-2">
              {ACTS.map((a) => (
                <span key={a.act} className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <span className="eyebrow">Act {a.act} · {a.title}</span>
                  {a.stops.map((s) => <Link key={s.href} href={s.href} className="hover:text-ink">{s.name}</Link>)}
                </span>
              ))}
              <Link href="/contents" className="underline decoration-grid underline-offset-4 hover:decoration-ink">Contents: what each page answers</Link>
            </nav>
            <div className="grid gap-6 md:grid-cols-[1fr_auto]">
            <div className="flex flex-col gap-1.5 text-muted max-w-xl">
              <span className="display text-lg text-ink">{SITE.name}</span>
              <span>Every number links to the observation behind it. Fast is not good; concentrating is not good. Status colours carry no verdict.</span>
              <Freshness generatedAt={generated} />
            </div>
            <nav aria-label="About" className="flex flex-wrap content-start gap-x-6 gap-y-1.5 text-ink-2">
              <Link href="/indicators" className="hover:text-ink">All the evidence</Link>
              <Link href="/methodology" className="hover:text-ink">How to read this</Link>
              <Link href="/methodology#reuse" className="hover:text-ink">Reuse and cite</Link>
              <Link href="/legal" className="hover:text-ink">Legal</Link>
              <Link href="/legal#privacy" className="hover:text-ink">Privacy</Link>
              <a href={SITE.repo} className="hover:text-ink">Source code</a>
            </nav>
            </div>
          </div>
        </footer>
        <HatchDefs />
        <HoverLayer />
        <OpenOnHash />
        {SITE.askOnline ? <AskPanel /> : null}
      </body>
    </html>
  );
}
