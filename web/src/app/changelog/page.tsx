import { ChangelogList } from "@/components/Changelog";
import { changelog, obsIndex } from "@/lib/data";

export default function ChangelogPage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold tracking-tight">Changelog</h1>
      <p className="text-sm text-ink-2 max-w-3xl">Generated from status events. Every change names its evidence, its reason and its author; nothing here can be hand-edited.</p>
      <ChangelogList events={changelog()} obsIndex={obsIndex()} />
    </div>
  );
}
