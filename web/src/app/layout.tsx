import type { Metadata } from "next";
import { Instrument_Sans, Instrument_Serif, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { ChatDrawer } from "@/components/ChatDrawer";
import { Freshness } from "@/components/Freshness";
import { SiteNav } from "@/components/SiteNav";
import { ABOUT } from "@/lib/nav";
import { ThemeToggle } from "@/components/ThemeToggle";
import { meta } from "@/lib/data";
import { SITE } from "@/lib/site";

const serif = Instrument_Serif({ weight: "400", style: ["normal", "italic"], subsets: ["latin"], variable: "--font-instrument-serif", display: "swap" });
const sans = Instrument_Sans({ subsets: ["latin"], variable: "--font-instrument-sans", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains-mono", display: "swap" });
const THEME_SCRIPT = `(()=>{try{var t=localStorage.theme,d=t?t==="dark":matchMedia("(prefers-color-scheme: dark)").matches,r=document.documentElement;r.classList.toggle("dark",d);r.style.colorScheme=d?"dark":"light"}catch(e){}})()`;

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: { default: SITE.name, template: `%s · ${SITE.name}` },
  description: SITE.description,
  openGraph: { type: "website", siteName: SITE.name, title: SITE.name, description: SITE.description, url: SITE.url },
  twitter: { card: "summary_large_image", title: SITE.name, description: SITE.description },
};


export default function RootLayout({ children }: { children: React.ReactNode }) {
  const generated = meta().generated_at;
  return (
    <html lang="en" suppressHydrationWarning className={`${serif.variable} ${sans.variable} ${mono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-1 focus:ring-hair">Skip to content</a>
        <header className="border-b border-grid">
          <div className="mx-auto max-w-5xl px-4 py-4 flex items-center gap-x-6">
            <Link href="/" className="display text-[1.375rem] tracking-tight shrink-0">{SITE.name}</Link>
            <div className="flex-1"><SiteNav /></div>
            <div className="flex items-center gap-x-1 shrink-0">
              <ChatDrawer />
              <ThemeToggle />
            </div>
          </div>
        </header>
        <main id="main" className="mx-auto w-full max-w-5xl px-4 py-6 flex-1">{children}</main>
        <footer className="border-t border-grid mt-16">
          <div className="mx-auto max-w-5xl px-4 py-8 grid gap-6 md:grid-cols-[1fr_auto] text-sm">
            <div className="flex flex-col gap-1.5 text-muted max-w-xl">
              <span className="display text-lg text-ink">{SITE.name}</span>
              <span>Every number links to the observation behind it. Fast is not good; concentrating is not good. Status colours carry no verdict.</span>
              <Freshness generatedAt={generated} />
            </div>
            <nav aria-label="About" className="flex md:flex-col gap-x-5 gap-y-1.5 text-ink-2">
              {ABOUT.map(([href, label]) => <Link key={href} href={href} className="hover:text-ink">{label}</Link>)}
              <Link href="/methodology#reuse" className="hover:text-ink">Reuse, cite, corrections</Link>
            </nav>
          </div>
        </footer>
      </body>
    </html>
  );
}
