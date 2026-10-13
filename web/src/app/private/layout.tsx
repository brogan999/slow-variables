import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { configured } from "@/lib/private";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Private", robots: { index: false, follow: false } };

export default function PrivateLayout({ children }: { children: React.ReactNode }) {
  if (!configured()) notFound();
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-1 border-b border-grid pb-3 text-xs text-muted">
        <span className="eyebrow">Private. Not public.</span>
        <span>Drafted by Claude, a model made by Anthropic. Anthropic buys from, sells to or competes with companies that may be named here.</span>
      </div>
      {children}
    </div>
  );
}
