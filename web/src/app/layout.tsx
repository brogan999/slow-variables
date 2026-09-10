import type { Metadata } from "next";
import { Instrument_Sans, Instrument_Serif, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { ChatDrawer } from "@/components/ChatDrawer";
import { Freshness } from "@/components/Freshness";
import { NavLinks } from "@/components/NavLinks";
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

const NAV = [
  ["/", "Diffusion"], ["/capture", "Capture"], ["/memos", "Memos"], ["/stack", "Stack"], ["/indicators", "Indicators"], ["/predictions", "Predictions"], ["/compare", "Compare"], ["/bottlenecks", "Bottlenecks"], ["/ledger", "Ledger"], ["/crosswalk", "Crosswalk"], ["/query", "Query"],
  ["/sources", "Sources"], ["/methodology", "Methodology"], ["/changelog", "Changelog"],
] as const;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const generated = meta().generated_at;
  return (
    <html lang="en" suppressHydrationWarning className={`${serif.variable} ${sans.variable} ${mono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-surface focus:px-3 focus:py-1 focus:ring-hair">Skip to content</a>
        <header className="border-b border-grid">
          <div className="mx-auto max-w-5xl px-4 py-3 flex items-baseline gap-x-5">
            <Link href="/" className="display text-xl tracking-tight shrink-0">{SITE.name}</Link>
            <nav aria-label="Primary" className="min-w-0 flex-1 flex gap-x-4 text-sm text-ink-2 overflow-x-auto whitespace-nowrap md:flex-wrap md:whitespace-normal md:gap-y-1 -mx-1 px-1">
              <NavLinks items={NAV} />
            </nav>
            <ChatDrawer />
            <ThemeToggle />
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
