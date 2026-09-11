import { ChangelogByMonth } from "@/components/Changelog";
import { changelog, obsIndex } from "@/lib/data";

export const metadata = { title: "Changelog" };

export default function ChangelogPage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">Changelog</h1>
      <p className="text-lg leading-snug text-ink-2 max-w-[60ch]">Generated from status events. Every change names its evidence, its reason and its author; nothing here can be hand-edited.</p>
      <ChangelogByMonth events={changelog()} obsIndex={obsIndex()} />
    </div>
  );
}
