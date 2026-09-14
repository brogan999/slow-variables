import type { Metadata } from "next";
import { Fraunces, Geist, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { ChatDrawer } from "@/components/ChatDrawer";
import { Freshness } from "@/components/Freshness";
import { MobileNav, SiteNav } from "@/components/SiteNav";
import { ABOUT } from "@/lib/nav";
import { meta } from "@/lib/data";
import { SITE } from "@/lib/site";

const serif = Fraunces({ subsets: ["latin"], style: ["normal", "italic"], axes: ["opsz", "SOFT"], variable: "--font-fraunces", display: "swap" });
const sans = Geist({ subsets: ["latin"], variable: "--font-geist", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains-mono", display: "swap" });

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: { default: SITE.name, template: `%s · ${SITE.name}` },
  description: SITE.description,
  openGraph: { type: "website", siteName: SITE.name, title: SITE.name, description: SITE.description, url: SITE.url },
  twitter: { card: "summary_large_image", title: SITE.name, description: SITE.description },
  alternates: { types: { "application/rss+xml": "/memos/feed.xml" } },
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
            <div className="flex-1"><SiteNav /></div>
            <div className="flex items-center gap-x-1 shrink-0">
              <ChatDrawer />
              <MobileNav />
            </div>
          </div>
        </header>
        <main id="main" className="mx-auto w-full max-w-[82rem] px-4 md:px-8 py-8 md:py-12 flex-1">{children}</main>
        <footer className="border-t border-grid mt-16">
          <div className="mx-auto max-w-[82rem] px-4 md:px-8 py-10 grid gap-6 md:grid-cols-[1fr_auto] text-sm">
            <div className="flex flex-col gap-1.5 text-muted max-w-xl">
              <span className="display text-lg text-ink">{SITE.name}</span>
              <span>Every number links to the observation behind it. Fast is not good; concentrating is not good. Status colours carry no verdict.</span>
              <Freshness generatedAt={generated} />
            </div>
            <nav aria-label="About" className="flex flex-wrap md:flex-col md:flex-nowrap gap-x-5 gap-y-1.5 text-ink-2">
              {ABOUT.map(([href, label]) => <Link key={href} href={href} className="hover:text-ink">{label}</Link>)}
              <Link href="/methodology#reuse" className="hover:text-ink">Reuse, cite, corrections</Link>
              <Link href="/methodology#privacy" className="hover:text-ink">Privacy and disclaimers</Link>
              <a href="/memos/feed.xml" className="hover:text-ink">Memo feed (RSS)</a>
            </nav>
          </div>
        </footer>
      </body>
    </html>
  );
}
