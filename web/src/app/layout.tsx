import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { meta } from "@/lib/data";

export const metadata: Metadata = {
  title: "ai-tracker",
  description: "How fast AI value moves through the diffusion stages, and who keeps it. Every number traces to a dated, graded observation.",
};

const NAV = [
  ["/", "Diffusion"], ["/capture", "Capture"], ["/indicators", "Indicators"], ["/predictions", "Predictions"], ["/crosswalk", "Crosswalk"],
  ["/sources", "Sources"], ["/methodology", "Methodology"], ["/changelog", "Changelog"],
] as const;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const generated = meta().generated_at.slice(0, 10);
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <header className="border-b border-grid">
          <div className="mx-auto max-w-5xl px-4 py-3 flex flex-wrap items-baseline gap-x-5 gap-y-1">
            <Link href="/" className="font-semibold tracking-tight">ai-tracker</Link>
            <nav className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink-2">
              {NAV.map(([href, label]) => <Link key={href} href={href} className="hover:text-ink">{label}</Link>)}
            </nav>
          </div>
        </header>
        <main className="mx-auto w-full max-w-5xl px-4 py-6 flex-1">{children}</main>
        <footer className="border-t border-grid text-xs text-muted">
          <div className="mx-auto max-w-5xl px-4 py-4 flex flex-wrap gap-x-6 gap-y-1">
            <span>Every number links to the observation behind it.</span>
            <span>Data generated {generated}.</span>
            <span>Fast is not good; concentrating is not good. Status colours carry no verdict.</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
