import { IndicatorTable } from "@/components/IndicatorTable";
import { PageHeader } from "@/components/PageHeader";
import { index, obsIndex } from "@/lib/data";

export const metadata = { title: "Indicators" };

export default function Indicators() {
  const { indicators, buckets, layers } = index();
  const names = Object.fromEntries([...buckets, ...layers].map((x) => [x.id, x.name]));
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Indicators" lede="One object, two addresses. Unpublished rows have a definition and data but do not yet meet the publishing rules (a status, counterevidence, and either two sources or one primary source), so they carry no status and no page." />
      <IndicatorTable indicators={indicators} names={names} obsIndex={obsIndex()} />
    </div>
  );
}
