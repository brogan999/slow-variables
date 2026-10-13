import type { DataMarketDoc } from "@/lib/data";

// Who pays whom: money runs from model builders to vendors, and from vendors to the people and the companies whose
// work or records become the data. Each arrow carries the number of published figures the site could quote for it.
// Drawn by hand: a node is a ruled box, an arrow a hairline with a head, and nothing here is computed.
function Arrow({ className = "" }: { className?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 120 12" preserveAspectRatio="none" className={`h-3 w-full text-ink ${className}`}>
      <line x1="0" y1="6" x2="112" y2="6" stroke="currentColor" strokeWidth="1" vectorEffect="non-scaling-stroke" />
      <path d="M112 1.5 L120 6 L112 10.5 Z" fill="currentColor" />
    </svg>
  );
}

function Leg({ f, hollow = false }: { f: DataMarketDoc["flow"][number]; hollow?: boolean }) {
  return (
    <div className="flex min-w-0 flex-1 flex-col gap-1.5">
      <span className="flex items-baseline gap-2">
        <span className={`num text-[1.9rem] leading-none ${hollow ? "text-muted" : "text-ink"}`}>{f.n}</span>
        <span className="text-[11px] uppercase tracking-[0.1em] text-muted">{f.n === 1 ? "published figure" : "published figures"}</span>
      </span>
      <Arrow className={hollow ? "opacity-40" : ""} />
      <span className="text-[12.5px] leading-snug text-ink-2">{f.says}</span>
    </div>
  );
}

const node = "flex shrink-0 items-center justify-center rounded-[3px] border border-ink bg-surface px-4 py-3 text-center text-[14px] font-medium leading-tight text-ink md:w-[9.5rem]";

export function DataMarketFlow({ flow }: { flow: DataMarketDoc["flow"] }) {
  const [people, companies, builders] = flow;
  return (
    <div role="img" aria-label={`Who pays whom. ${builders.from} pay ${builders.to}: ${builders.n} published figures. ${people.from} pay ${people.to}: ${people.n}. ${companies.from} pay ${companies.to}: ${companies.n}.`} className="panel flex flex-col gap-5 p-5 md:flex-row md:items-center md:gap-6">
      <div className={node}>Model builders</div>
      <Leg f={builders} hollow />
      <div className={node}>Vendors</div>
      <div className="flex min-w-0 flex-[2] flex-col gap-5">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:gap-6">
          <Leg f={people} />
          <div className={node}>People who make the data</div>
        </div>
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:gap-6">
          <Leg f={companies} />
          <div className={node}>Companies that hold records</div>
        </div>
      </div>
    </div>
  );
}
