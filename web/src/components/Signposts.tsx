import { ChartSources } from "./ChartSources";
import { Figure, Key } from "./Figure";
import { Mark, Marks, Plot } from "./chart";
import type { HalPoint, Signposts } from "@/lib/data";
import { fmt } from "@/lib/format";

// How jagged the frontier is: the best score so far on each test the site reads, one row per test on one percent
// scale, furthest along first. A signpost carries no status; a test no recent model has been scored on is faded (bar
// and dot only, so its words keep their contrast). Each test has its own scale, so rows are not compared.
export function JaggedFrontier({ doc }: { doc: Signposts }) {
  const stamps = [...new Set(doc.tests.flatMap((t) => (t.stamp ? [t.stamp] : [])))];
  const last = doc.tests[0];
  return (
    <Figure
      title="How far along each capability test the best model is"
      note="best score so far on each test · each dot links to the row that set it"
      stamps={stamps}
      keys={<>
        <Key swatch={<svg width="10" height="10" aria-hidden><circle cx="5" cy="5" r="4" fill="var(--s1)" /></svg>}>the record</Key>
        <Key swatch={<svg width="10" height="10" aria-hidden><circle cx="5" cy="5" r="4" fill="var(--s1)" opacity="0.35" /></svg>}>faded: no model released in the last {doc.stale_after_days} days has been scored on this test</Key>
      </>}
      foot={<>
        <p>Each score is on its own test&apos;s scale. Most are the share of tasks solved; GDPval&apos;s is how often graders prefer the model&apos;s work to a professional&apos;s; FrontierSWE&apos;s is partial credit on each task, averaged over five runs; PostTrainBench&apos;s is the average score of the models the agent post-trained, across several benchmarks. The tests measure different things, so read each row against its own scale, not against the others. A record close to a perfect score leaves that test little room to show further progress. Scores sit at model release dates, often from runs with no limit on compute.</p>
        <p><a href="/outlook#source-jones_b" className="underline decoration-grid underline-offset-2 hover:decoration-ink">Benjamin Jones</a>, an economist who studies where scientific progress comes from, argues that a high share of tasks solved is not a measure of progress in research: research needs every one of its steps done, so the steps a model still fails set the pace, however many others it solves. <a href="/outlook#position-compounding" className="underline decoration-grid underline-offset-2 hover:decoration-ink">AI 2027&apos;s forecasters</a> expect the remaining steps to fall to the models themselves.</p>
        <ChartSources cs={doc.chart_sources} />
      </>}
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">test</th><th scope="col">record</th><th scope="col">set</th><th scope="col">newest scored release</th><th scope="col">whose figure</th></tr></thead>
          <tbody>{doc.tests.map((t) => (
            <tr key={t.test}><td>{t.name}</td><td className="num">{t.href ? <a href={t.href} className="underline decoration-grid underline-offset-2 hover:decoration-ink">{fmt(t.value, "share")}</a> : fmt(t.value, "share")}</td><td className="num whitespace-nowrap">{t.as_of}</td><td className="num whitespace-nowrap">{t.newest}</td><td>{t.whose}</td></tr>
          ))}</tbody>
        </table>
      }
    >
      <ol data-marks className="flex flex-col">
        {doc.tests.map((t) => {
          const tip = `${t.name} · best ${fmt(t.value, "share")} · set ${t.as_of}${t.stale ? ` · no model released after ${t.newest} scored` : ""}`;
          return (
            <li key={t.test} className="grid gap-x-4 gap-y-1 py-2.5 border-t border-grid first:border-t-0 sm:grid-cols-[minmax(0,15rem)_minmax(0,1fr)_4.5rem] items-center">
              <div>
                <div className="font-sans font-semibold text-[14px] text-ink">{t.name}</div>
                <div className="text-[12px] leading-snug text-ink-2">{t.what}; <span className="text-muted">{t.whose}</span></div>
                {t.stale ? <div className="text-[12px] leading-snug text-muted">No model released after {t.newest} has been scored on it.</div> : null}
              </div>
              <div className="relative h-6" role="presentation">
                <div className="absolute inset-x-0 top-1/2 h-px bg-grid" aria-hidden />
                {doc.axis.ticks.map((k) => <div key={k.x} aria-hidden className="absolute top-1 bottom-1 w-px bg-grid" style={{ left: `${k.x}%` }} />)}
                <div aria-hidden className={`absolute top-1/2 h-px ${t.stale ? "bg-s1/35" : "bg-s1"}`} style={{ left: 0, width: `${t.x}%` }} />
                {t.href ? (
                  <a href={t.href} data-tip={tip} aria-label={tip} title={tip} tabIndex={0} data-stop={t === last || undefined}
                    className="mark absolute top-1/2 -translate-x-1/2 -translate-y-1/2 grid h-6 w-6 place-items-center" style={{ left: `${t.x}%` }}>
                    <span aria-hidden className={`block h-2.5 w-2.5 rounded-full ring-2 ring-surface ${t.stale ? "bg-s1/35" : "bg-s1"}`} />
                  </a>
                ) : null}
              </div>
              <div className="num text-[13px] text-ink sm:text-right">{fmt(t.value, "share")} <span className="block text-[11px] text-muted">{t.as_of}</span></div>
            </li>
          );
        })}
      </ol>
      <div className="hidden sm:grid grid-cols-[15rem_minmax(0,1fr)_4.5rem] gap-x-4" aria-hidden>
        <div />
        <div className="relative h-5">{doc.axis.ticks.map((k) => <span key={k.x} className="absolute top-1 -translate-x-1/2 whitespace-nowrap num text-[10px] text-muted" style={{ left: `${k.x}%` }}>{k.label}</span>)}</div>
      </div>
    </Figure>
  );
}

// HAL runs the same agents on its own benchmarks and scores two things: whether a task gets solved, and how
// dependably the agent behaves while solving it. Each agent appears twice, at its model's release date. Both scores
// run from 0 to 1 but measure different things, so the figure is read by the slopes of the trend lines, never by the
// heights. Accuracy prints as a share of tasks and reliability as the index HAL prints; each slope's record is a row
// of this figure's own table.
export function ReliabilityGap({ doc }: { doc: Signposts }) {
  const r = doc.reliability;
  if (!r) return null;
  const last = r.points.at(-1);
  return (
    <Figure
      title="How accuracy and reliability have moved across model releases"
      note="HAL's own runs of the same agents, by model release · compare the slopes, not the heights · each dot links to its row"
      stamps={r.stamps}
      keys={<>
        <Key swatch={<svg width="10" height="10" aria-hidden><circle cx="5" cy="5" r="4" fill="var(--s1)" /></svg>}>accuracy: share of tasks solved</Key>
        <Key swatch={<svg width="10" height="10" aria-hidden><circle cx="5" cy="5" r="4" fill="var(--s3)" stroke="var(--s2)" strokeWidth="1.5" /></svg>}>overall reliability: HAL&apos;s index, from 0 to 1, of consistency, predictability and robustness</Key>
        <Key swatch={<svg width="18" height="10" aria-hidden><line x1="0" x2="18" y1="5" y2="5" stroke="var(--s2)" strokeWidth="1.5" /></svg>}>straight-line trend</Key>
      </>}
      foot={<>
        <p>HAL, a team at Princeton that runs agents on its own benchmarks, scores each agent two ways from the same runs. Accuracy is the share of tasks solved; overall reliability is HAL&apos;s index, from 0 to 1, averaging how consistently, predictably and robustly the agent behaves (safety is scored separately). Both run from 0 to 1 but measure different things, so compare how steeply each line climbs, not how high it sits.{r.trends.length ? <> Across these agents the trend in {r.trends.map((t, i) => <span key={t.measure}>{i ? " and in " : ""}{t.measure} is <a href={t.href} className="num underline decoration-grid underline-offset-2 hover:decoration-ink">{t.label}</a></span>)}, where a point is a hundredth of that range; the lines are straight-line fits by this site to HAL&apos;s rows.</> : null}</p>
        <ChartSources cs={r.chart_sources} />
      </>}
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">agent</th><th scope="col">released</th><th scope="col">measure</th><th scope="col">score</th></tr></thead>
          {r.trends.length ? (
            <tbody>{r.trends.map((t) => (
              <tr key={t.id} id={`d-${t.id}`} className="scroll-mt-24 target:bg-surface-2"><td>trend in {t.measure}, fitted to the {t.n} {t.measure} rows below</td><td className="num whitespace-nowrap">to {t.as_of}</td><td>{t.measure}</td><td className="num whitespace-nowrap">{t.label}</td></tr>
            ))}</tbody>
          ) : null}
          <tbody>{r.points.slice().reverse().map((p) => (
            <tr key={p.obs_ids[0]}><td>{p.label}</td><td className="num whitespace-nowrap">{p.as_of}</td><td>{p.measure}</td><td className="num">{p.href ? <a href={p.href} className="underline decoration-grid underline-offset-2 hover:decoration-ink">{score(p)}</a> : score(p)}</td></tr>
          ))}</tbody>
        </table>
      }
    >
      <Plot x={r.x.ticks} y={r.y} label="HAL's accuracy and overall reliability for each agent, by model release, with a straight-line trend through each; each dot links to its row"
        rightWidth="8rem" right={r.trends.map((t) => <span key={t.measure} style={{ top: `${t.label_y}%` }}>{t.measure}<span className="block num text-ink">{t.label}</span></span>)}>
        {r.trends.map((t) => (
          <g key={t.measure} aria-hidden>
            <line x1={`${t.x1}%`} y1={`${t.y1}%`} x2={`${t.x2}%`} y2={`${t.y2}%`} stroke={t.measure === "accuracy" ? "var(--s1)" : "var(--s2)"} strokeWidth="1.5" strokeLinecap="round" />
            <line className="plot-leader" x1={`${t.x2}%`} y1={`${t.y2}%`} x2="100%" y2={`${t.label_y}%`} stroke="var(--axis)" />
          </g>
        ))}
        <Marks>
          {r.points.map((p) => (
            <Mark key={p.obs_ids[0]} p={p} stop={p === last} r={3.5} stroke={p.measure === "accuracy" ? "var(--s1)" : "var(--s2)"} fill={p.measure === "accuracy" ? "var(--s1)" : "var(--s3)"}
              tip={`${p.label} · ${p.measure} ${score(p)} · released ${p.as_of}`} />
          ))}
        </Marks>
      </Plot>
    </Figure>
  );
}

// Accuracy prints as a share of tasks; the reliability index prints as HAL prints it, a plain number from 0 to 1.
const score = (p: HalPoint) => fmt(p.value, p.unit === "index" ? undefined : p.unit);
