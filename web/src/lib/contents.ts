// What question each page, and each named section of it, answers. The /contents page prints this; a test keeps it
// complete (every static route has an entry) and true (every section anchor exists).
// A section is [anchor, name, question]. `each` describes pages made once per record: [path prefix, what one answers].

export type Section = readonly [anchor: string, name: string, question: string];
export type Page = { name: string; question: string; sections?: readonly Section[]; each?: readonly (readonly [prefix: string, what: string])[] };

export const PAGES: Record<string, Page> = {
  "/": { name: "Home", question: "What does the site say tonight, and where should a reader start?", sections: [
    ["readings", "Tonight's three readings", "Which three numbers sum up where things stand tonight?"],
    ["changes", "Latest changes", "What has moved since the last update?"],
    ["path", "The path", "In what order should the site be read?"],
  ] },
  "/story": { name: "The story in pictures", question: "What does the argument look like, figure by figure, from now to what is forecast?", sections: [
    ["act-now", "Now", "How fast is AI spreading, and how much work passes the screen?"],
    ["act-money", "The money", "Where is the money, who keeps it, and what is scarce?"],
    ["act-next", "Next", "What do people expect, and what can be read of it yet?"],
  ] },
  "/argument": { name: "The argument", question: "Is AI a normal technology, or something faster?", sections: [
    ["folio-name", "Watch the variables that move slowly", "Why watch slow-moving measures and not the news?"],
    ["folio-pace", "Four machines, four clocks", "How long did earlier general-purpose technologies take to pay off?"],
    ["folio-money", "The money arrives first", "Why does investment run ahead of results, and is that a warning sign?"],
    ["folio-spoils", "Inventing it and keeping the money", "Why do inventors so often fail to keep the profit?"],
    ["folio-readings", "Where the slow variables stand", "What do the slow variables read tonight?"],
    ["folio-exits", "What would prove this wrong", "What evidence would overturn this site's view?"],
    ["slow-variables", "The five slow variables", "Which measures does the argument rest on?"],
    ["exits", "The list, re-tested every night", "Has any disproving condition been met?"],
  ] },
  "/argument/migration": { name: "The migrating bottleneck", question: "Which input is scarce now, and where does the shortage move next?", sections: [
    ["folio-rule", "The scarcest part gets paid", "Why does the scarcest input collect the profit?"],
    ["folio-record", "It has already moved", "Where has the shortage been so far, and how did it move?"],
    ["folio-tell", "Watch what the labs buy", "What do the labs' purchases reveal about what they find scarce?"],
    ["folio-reading", "The scorecard", "How tight is each input tonight, and which cannot be scored?"],
    ["folio-blind-spots", "What nobody publishes", "Which possible shortages have no public data?"],
    ["folio-predictions", "What binds now and next", "What binds now, what binds next, and what would prove each wrong?"],
    ["predictions", "The predictions, re-tested every night", "Are those predictions holding?"],
  ] },
  "/diffusion": { name: "How fast", question: "How quickly is AI spreading through firms and work?", sections: [
    ["stages", "The stages, one card each", "How far along is each stage, from what models can do to how work is reorganised?"],
    ["readings", "How close each stage is to fast", "Where does each gauge's number sit between its normal range and its fast range?"],
    ["trust", "How far to trust each stage's reading", "How old, and how well evidenced, are the readings behind each stage?"],
  ], each: [["/buckets/", "One page per stage: its readings, what would move it, and the evidence against."]] },
  "/census": { name: "How far", question: "How much knowledge work passes the hand-over screen?", sections: [
    ["dial", "How strict should the screen be?", "How much does the answer change if the rule is stricter or looser?"],
    ["roles", "What happens to a job", "How much of each job passes the screen?"],
    ["functions", "What to automate", "Which business functions hold the most work that passes?"],
    ["industries", "Industry by industry", "Which industries hold the most work that passes?"],
    ["rollups", "Where a rollup could start", "Which industries have both work to hand over and many small firms to buy?"],
    ["deals", "Businesses", "In which kinds of business would an owner keep the saving, and what are buyers doing?"],
    ["method", "Method, and what failed", "How was this measured, and which of its own tests did it fail?"],
    ["caveats-h", "What every figure carries", "What limits apply to every figure on the page?"],
  ], each: [["/census/roles/", "One page per role: each task, whether it passes, and why."]] },
  "/capture": { name: "Who profits", question: "Who keeps the money AI makes?", sections: [
    ["layers", "The layers, from the chips up", "What share of the profit does each layer keep?"],
  ], each: [["/layers/", "One page per layer: who is in it, what it earns, and who this site judges holds lasting power."]] },
  "/value-chain": { name: "The value chain", question: "Who are the companies at each step, and which hold lasting power?", sections: [
    ["vc-compute_physical", "Compute & physical", "Who makes the chips, clouds and power, and who holds power there?"],
    ["vc-model", "Model", "Which labs build the models, and can they keep their margins?"],
    ["vc-training_input", "Training input", "Who supplies the data and expert work models learn from?"],
    ["vc-serving_orchestration", "Serving & orchestration", "Who runs and routes models for others?"],
    ["vc-deployment_application", "Deployment & application", "Who builds the products and puts AI to work in firms?"],
    ["vc-adopters", "Adopters", "What do the firms using AI gain?"],
    ["vc-labour_consumers", "Labour & consumers", "What reaches workers and consumers?"],
    ["market-map", "The market map", "Which companies sit in each finer category, and where does coverage stop?"],
  ] },
  "/value-chain/opportunities": { name: "Businesses that could be built", question: "Where is the chain short of something a new business could supply?", sections: [
    ["op-rule", "The rent rule, drawn", "Who would keep each business's profit, and how large would it be?"],
    ["op-glance", "The businesses at a glance", "Where do they sit on the chain, how crowded is it there, and which kinds of firm would need them?"],
    ["op-list", "The businesses", "What is each business, what profit would it keep, and what would prove it wrong?"],
  ] },
  "/value-chain/atlas": { name: "What to build, future by future", question: "Which businesses are worth building, and which hold whatever happens?", sections: [
    ["ca-own", "Test a business of your own", "What would the site's records say about a business that is not on the list?"],
    ["ca-board", "A call on each business", "Which should be built, which only on a condition, and what does each future do to them?"],
    ["ca-table", "Every business in every future", "Which businesses does each future strengthen, weaken or break?"],
  ] },
  "/stack": { name: "The stack", question: "What are the layers and sub-layers, and which companies does the tracker follow in each?",
    each: [["/stack/", "One page per sub-layer: its companies, its readings and the venture money going in."]] },
  "/ledger": { name: "Circular financing ledger", question: "How much of AI's demand is paid for by its own suppliers?" },
  "/bottlenecks": { name: "What binds", question: "Which scarce input sets the pace?" },
  "/firm": { name: "Who owns what", question: "What does a firm own, and what does it rent, when intelligence is sold by the token?", sections: [
    ["folio-boundary", "Where a firm ends", "What sets the line between what a firm does and what it buys?"],
    ["folio-leak", "Asking reveals what you know", "Why does dealing with outsiders get dearer when everyone rents the same models?"],
    ["folio-liability", "Who answers for the work", "Why does answering for an agent's work pull the operation inside the firm?"],
    ["folio-edge", "Centre or edge", "Which decisions move to head office, and which have to stay on the spot?"],
    ["folio-rent", "Rent or own", "When should a firm rent intelligence, and when should it own it?"],
    ["folio-residue", "What stays scarce", "What does not get cheaper when intelligence does?"],
    ["folio-shape", "The shape of the firm", "Which layers of a firm go first, who argues what, and what does the census say of each kind of job?"],
    ["folio-limit", "The firm in the limit", "What is left of a firm when the argument is carried to its end, and who profits?"],
    ["folio-record", "What the records show", "What do this site's ledgers show so far, and where do its own leans disagree?"],
  ] },
  "/firm/kinds": { name: "What happens to each kind of firm", question: "What does AI do to an accounting practice, a hospital or a freight operator, and what will such firms need to buy?", sections: [
    ["today", "Today", "How much of each kind of firm's payroll passes the census screen, and what holds the rest?"],
    ["stages", "The stages", "What is known now, what is judged next, and what is extrapolated for a world with robots?"],
    ["kinds", "Kind by kind", "What does each kind of firm look like at each stage, and what would prove that wrong?"],
    ["anatomy", "What an AI-run firm looks like", "What shape does this site judge these kinds of firm are heading towards?"],
    ["needs", "Where the opportunity is", "What will AI-run firms need to buy, and which business would supply it?"],
  ] },
  "/outlook": { name: "What people expect", question: "What do informed writers expect, and what would settle it?", sections: [
    ["folio-can-ai-do-whole-jobs-reliably", "Whole jobs", "Can AI do whole jobs reliably, or only single skills?"],
    ["folio-who-checks-the-work", "Who checks the work", "Does checking AI's work become a business, and for whom?"],
    ["folio-is-adoption-slow-or-just-hard-to-see", "Adoption", "Is adoption slow, or just hard to see?"],
    ["folio-does-work-reorganise-fast-enough-to-show-up-in-output", "Output", "Does work reorganise fast enough to show up in output?"],
    ["folio-who-keeps-the-money", "Who keeps the money", "Do the labs keep their margins as open models catch up?"],
    ["folio-where-they-agree", "Where they agree", "On what do the two sides agree?"],
    ["folio-the-futures-still-open", "The futures still open", "Which futures do tonight's readings still allow?"],
    ["folio-every-claim-tested-nightly", "Every claim, tested nightly", "How did each claim fare against tonight's readings?"],
  ] },
  "/predictions": { name: "Who is right so far", question: "Which forecasts are coming true, and which are not?", sections: [
    ["folio-capability", "Capability", "Are forecasts about what models can do coming true?"],
    ["folio-products", "Products and applications", "Are forecasts about products built on models coming true?"],
    ["folio-adoption", "Early adoption", "Are forecasts about who uses AI coming true?"],
    ["folio-reorganisation", "Adaptation", "Are forecasts about firms reorganising work coming true?"],
    ["folio-value", "Value capture", "Are forecasts about who keeps the money coming true?"],
  ] },
  "/compare": { name: "Compare", question: "Does the same evidence favour the normal-technology view or the fast one?" },
  "/singularity": { name: "The long run", question: "When does AI surpass us, and what gets built?", sections: [
    ["timeline", "The dates people have dared to give", "When does each forecaster expect each milestone?"],
    ["beyond", "Beyond the dated calls", "What do people expect without naming a date?"],
    ["due", "The dates that have already come", "Which forecast dates have passed, and what happened?"],
    ["now", "The latest word from each forecaster", "What is each forecaster's most recent position?"],
    ["watch", "Fast story or slow one", "Which readings would tell the fast story from the slow one?"],
    ["worlds", "The ways the next decade could go", "What are the futures the site keeps open?"],
    ["fiction", "What the novelists imagined", "What did fiction expect, and when?"],
  ] },
  "/singularity/atlas": { name: "Atlas", question: "What do named writers expect to change in each part of life?", sections: [
    ["map", "The map", "Where do the sourced works expect change, and by when?"],
    ["plates", "Eight parts of life", "What is expected in money, work, meaning, power, war, science, health and an ordinary day?"],
  ], each: [["/singularity/atlas/", "One page per part of life: each writer's expectation, in this site's words, with its source."]] },
  "/futures": { name: "Futures", question: "What did fiction imagine, has it been built, and who would profit?", sections: [
    ["imagined", "When each idea was imagined", "In which decade was each idea first imagined?"],
    ["expected", "When they may arrive", "When might the unbuilt ones arrive?"],
    ["categories", "Kinds of technology", "What kinds of technology are there, and who would keep the profit from each?"],
    ["gallery", "A gallery", "What might these inventions look like?"],
  ], each: [["/futures/", "One page per decade: the ideas imagined or expected then."], ["/futures/category/", "One page per kind of technology: its ideas and the dated forecasts about it."]] },
  "/indicators": { name: "Indicators", question: "What is measured, what does each reading tell you, and how sure is it?",
    each: [["/indicators/", "One page per indicator: its reading, status, evidence against, and history."], ["/series/", "One page per data series: every observation and the source it came from."]] },
  "/crosswalk": { name: "Crosswalk", question: "How does a reading filed under how fast AI spreads also say who keeps the money?" },
  "/sources": { name: "Sources", question: "Where does every figure come from, and is each source still being read?", sections: [
    ["read-not-ingested", "Read, not ingested", "Which sources are read by hand, and why are they not data here?"],
    ["who-we-read", "Who we read", "Whose work does the tracker follow?"],
  ] },
  "/changelog": { name: "Changelog", question: "Which readings changed status, when, and on what evidence?" },
  "/query": { name: "Query", question: "Can I check a figure or run my own question against the data?", sections: [
    ["falsification", "Falsification monitor", "Has the rule that would overturn the normal-technology reading been met?"],
  ] },
  "/methodology": { name: "How to read this", question: "How are the readings made, graded and kept honest?", sections: [
    ["read", "How to read this", "What do the statuses, bands, grades and confidence numbers mean?"],
    ["framing", "How we frame value capture", "How does the site decide who captures value?"],
    ["charts", "How the charts read", "How should the charts be read?"],
    ["tightness", "Tightness scores", "How is each input's tightness score made?"],
    ["signposts", "Signposts", "What is a signpost, and how is one tested?"],
    ["outlook", "Claims about what happens next", "How are claims about the future tested each night?"],
    ["census", "The automatability census", "How was the census measured, and what are its limits?"],
    ["futures", "Futures", "How were the imagined technologies dated, judged and illustrated?"],
    ["reuse", "Reuse, citation and corrections", "How may the data be reused, and how are errors corrected?"],
    ["judgements", "A model's judgement where there is no reading", "Where does a model's opinion fill a gap, and how is it kept apart from the readings?"],
    ["not-measured", "Not measured, and why", "What does the site leave out, and why?"],
  ] },
  "/legal": { name: "Legal notice", question: "Who runs the site, and on what terms may it be used?", sections: [
    ["operator", "Who runs this site", "Who is responsible for the site?"],
    ["advice", "Not advice", "Is anything here investment advice?"],
    ["ai", "AI-generated content", "Which parts were written or judged by AI models?"],
    ["conflicts", "Conflicts of interest", "What does the owner hold that could bias the site?"],
    ["licences", "Licences", "Under what terms may the data and words be reused?"],
  ] },
  "/ask": { name: "Ask", question: "Can I put a question to the data in plain words?" },
};

// Deep dives listed under the stop they belong to, and the reference pages that belong to none.
export const UNDER: Record<string, readonly string[]> = {
  "/argument": ["/argument/migration"],
  "/capture": ["/value-chain", "/value-chain/opportunities", "/value-chain/atlas", "/stack", "/ledger"],
  "/firm": ["/firm/kinds"],
  "/predictions": ["/compare"],
  "/singularity": ["/singularity/atlas", "/futures"],
};
export const REFERENCE = ["/", "/story", "/indicators", "/crosswalk", "/sources", "/query", "/ask", "/changelog", "/methodology", "/legal"] as const;
