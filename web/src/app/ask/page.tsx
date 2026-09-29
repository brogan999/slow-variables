import { Chat } from "@/components/Chat";

export const metadata = {
  title: "Ask",
  description: "Ask the tracker's data about AI's pace, who profits and what happens next; every number is checked against the record it cites.",
};

// A question arriving in the link (?q=, from a "Reason through this" link) is rendered from the first paint,
// so the greeting never flashes before it.
export default async function AskPage({ searchParams }: { searchParams: Promise<{ q?: string | string[]; from?: string | string[] }> }) {
  const sp = await searchParams;
  const one = (v?: string | string[]) => (Array.isArray(v) ? v[0] : v)?.trim() || undefined;
  return <Chat initialQ={one(sp.q)} initialFrom={one(sp.from)} />;
}
