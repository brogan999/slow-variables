import { ChangelogByMonth } from "@/components/Changelog";
import { changelog, obsIndex } from "@/lib/data";

export const metadata = { title: "Changelog" };

export default function ChangelogPage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="display text-[2.5rem] md:text-[3.5rem] leading-[1.02] max-w-[24ch]">Changelog</h1>
      <p className="text-lg leading-snug text-ink-2 max-w-[60ch]">Generated from status events. Every change names its evidence, its reason and its author; nothing here can be hand-edited.</p>
      <ChangelogByMonth events={changelog()} obsIndex={obsIndex()} />
    </div>
  );
}
