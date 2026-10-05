import { IndicatorTable } from "@/components/IndicatorTable";
import { PageHeader } from "@/components/PageHeader";
import { index, indicator, judgements, obsIndex } from "@/lib/data";
import { plain } from "@/lib/format";

export const metadata = { title: "Indicators" };

export default function Indicators() {
  const { indicators } = index();
  const judged = judgements();
  const why = Object.fromEntries(indicators.map((c) => [c.id, plain(indicator(c.id).why_it_matters)]));
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Indicators" lede="Every gauge the site reads, with what it tells you. Unpublished rows have a definition and data but do not yet meet the publishing rules (a status, counterevidence, and either two sources or one primary source), so they carry no status and no page." />
      <IndicatorTable indicators={indicators} why={why} obsIndex={obsIndex()} judged={judged.surfaces.indicators ?? {}} />
    </div>
  );
}
