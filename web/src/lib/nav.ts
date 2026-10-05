// The reading path: three acts, nine stops, in reading order. Everything else is evidence, reached from the pages
// that use it and from the menu.
export const ACTS = [
  { act: "I", title: "Now", stops: [
    { n: "1", name: "The argument", href: "/argument", question: "Is AI a normal technology, or something faster?" },
    { n: "2", name: "How fast", href: "/diffusion", question: "How quickly is AI spreading through firms and work?" },
    { n: "3", name: "How far", href: "/census", question: "How much knowledge work passes the hand-over screen?" },
  ] },
  { act: "II", title: "The money", stops: [
    { n: "4", name: "Who profits", href: "/capture", question: "Who keeps the money AI makes?" },
    { n: "5", name: "What binds", href: "/bottlenecks", question: "Which scarce input sets the pace?" },
    { n: "6", name: "Who owns what", href: "/firm", question: "What does a firm own, and what does it rent, when intelligence is sold by the token?" },
  ] },
  { act: "III", title: "Next", stops: [
    { n: "7a", name: "What people expect", href: "/outlook", question: "What do informed writers expect, and what would settle it?" },
    { n: "7b", name: "Who is right so far", href: "/predictions", question: "Which forecasts are coming true, and which are not?" },
    { n: "8", name: "The long run", href: "/singularity", question: "When does AI surpass us, and what gets built?" },
  ] },
] as const;

export const STOPS = ACTS.flatMap((a) => a.stops.map((s) => ({ ...s, act: a.act, actTitle: a.title })));

// Deep dives light their parent stop; the most specific prefix comes first.
export const STOP_OF = [
  ["/argument", "1"], ["/diffusion", "2"], ["/buckets", "2"], ["/census", "3"],
  ["/capture", "4"], ["/value-chain", "4"], ["/layers", "4"], ["/stack", "4"], ["/ledger", "4"], ["/bottlenecks", "5"], ["/firm", "6"],
  ["/outlook", "7a"], ["/predictions", "7b"], ["/compare", "7b"], ["/singularity", "8"], ["/futures", "8"],
] as const;

export const EVIDENCE = [["/contents", "Contents"], ["/indicators", "Indicators"], ["/stack", "Stack"], ["/value-chain", "Value chain"], ["/ledger", "Ledger"], ["/compare", "Compare"], ["/argument/migration", "The migrating bottleneck"], ["/futures", "Futures"], ["/singularity/atlas", "Atlas"], ["/crosswalk", "Crosswalk"], ["/sources", "Sources"], ["/changelog", "Changelog"], ["/query", "Query"], ["/methodology", "How to read this"]] as const;
