"use client";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="flex flex-col gap-3 py-12">
      <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">Something failed to render</h1>
      <p className="text-sm text-ink-2">The data behind this page is unchanged; only the view broke.{error.digest ? ` Reference ${error.digest}.` : ""}</p>
      <button onClick={reset} className="w-fit rounded border border-grid px-3 py-1 text-sm hover:bg-surface">Try again</button>
    </div>
  );
}
