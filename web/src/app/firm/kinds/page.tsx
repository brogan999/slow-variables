import Link from "next/link";
import { KindBars, KindShapes } from "@/components/FirmKinds";
import { firmKinds } from "@/lib/data";

export const metadata = {
  title: "What happens to each kind of firm",
  description: "Twelve kinds of firm, from accounting practices to manufacturers: how much of each one's work a check can settle today, what each looks like as AI takes on more, and what such firms will need to buy.",
};

export default function FirmKindsPage() {
  const doc = firmKinds();
  return (
    <div className="flex flex-col gap-8 max-w-[72rem]">
      <div className="flex flex-col gap-3">
        <span className="eyebrow"><Link href="/firm" className="hover:text-ink">Who owns what</Link> · kind by kind</span>
        <h1 className="display text-[2.5rem] md:text-[3.5rem] leading-[1.02]">What happens to each kind of firm</h1>
      </div>
      <KindBars doc={doc} />
      <KindShapes doc={doc} />
    </div>
  );
}
