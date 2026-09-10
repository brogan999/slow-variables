import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col gap-3 py-12">
      <h1 className="text-2xl font-semibold tracking-tight">Not found</h1>
      <p className="text-sm text-ink-2">No page at this address. Indicators, series and layers are all listed from the <Link href="/indicators" className="underline decoration-grid underline-offset-4">indicator index</Link>.</p>
    </div>
  );
}
