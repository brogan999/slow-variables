"use client";

import { Button } from "@/components/ui/button";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="flex flex-col gap-3 py-12">
      <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">Something failed to render</h1>
      <p className="text-sm text-ink-2">The data behind this page is unchanged; only the view broke.{error.digest ? ` Reference ${error.digest}.` : ""}</p>
      <Button variant="outline" size="sm" onClick={reset} className="w-fit">Try again</Button>
    </div>
  );
}
