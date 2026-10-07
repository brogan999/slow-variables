import { Chat } from "@/components/Chat";
import { companyQuestion, ideaQuestion } from "@/lib/idea";

export const metadata = {
  title: "Ask",
  description: "Ask the tracker's data about AI's pace, who profits and what happens next; every number is checked against the record it cites.",
};

// A question arriving in the link (?q=, from a "Reason through this" link) is rendered from the first paint,
// so the greeting never flashes before it. A reader's own business idea (?idea=), or a company from the map (?company=, ?part=), arrives wrapped in its one question.
export default async function AskPage({ searchParams }: { searchParams: Promise<{ q?: string | string[]; idea?: string | string[]; company?: string | string[]; part?: string | string[]; from?: string | string[] }> }) {
  const sp = await searchParams;
  const one = (v?: string | string[]) => (Array.isArray(v) ? v[0] : v)?.trim() || undefined;
  const idea = one(sp.idea), company = one(sp.company);
  return <Chat initialQ={one(sp.q) ?? (idea ? ideaQuestion(idea) : company ? companyQuestion(company, one(sp.part) ?? "the value chain") : undefined)} initialFrom={one(sp.from)} />;
}
