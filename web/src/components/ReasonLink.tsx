import Link from "next/link";

// Opens Ask with a question written from this page's context; the page's path goes with it.
export function ReasonLink({ q, from, className = "" }: { q: string; from: string; className?: string }) {
  return <Link href={`/ask?${new URLSearchParams({ q, from })}`} prefetch={false} className={`text-xs text-ink-2 underline decoration-grid underline-offset-2 hover:text-ink ${className}`}>Reason through this</Link>;
}
