import { notFound, redirect } from "next/navigation";
import { configured, session } from "@/lib/private";

export default async function PrivateLoginPage({ searchParams }: { searchParams: Promise<{ e?: string }> }) {
  if (!configured()) notFound();
  if (await session()) redirect("/private");
  const { e } = await searchParams;
  return (
    <form method="post" action="/private/session" className="flex max-w-xs flex-col gap-3 py-8">
      <label htmlFor="password" className="eyebrow">Password</label>
      <input id="password" name="password" type="password" required autoFocus autoComplete="current-password" className="h-10 rounded-[3px] border border-border bg-surface px-3 text-base" />
      {e ? <p role="alert" className="text-sm text-ink-2">Not recognised.</p> : null}
      <button type="submit" className="inline-flex h-10 w-fit items-center rounded-[3px] bg-ink px-4 text-sm font-medium text-background hover:bg-ink-2">Enter</button>
    </form>
  );
}
