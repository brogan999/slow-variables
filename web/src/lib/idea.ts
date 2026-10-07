// The one question a reader's own business idea becomes. It names the tools so Ask reads the value chain, the rent
// rule and the futures and then answers, and it is shown to the reader as the question asked.
export const IDEA_MAX = 600;

const clip = (idea: string) => idea.trim().slice(0, IDEA_MAX);

export const ideaQuestion = (idea: string) =>
  `Reason through this business idea briefly, using the value_chain, rent_rubric and scenarios tools only: ${clip(idea)}. Where does it sit on the value chain and what is scarce there, where would its profit pool by the rent rule, which futures would strengthen or weaken it, and what would prove it wrong? Say which parts are your judgement. End with one call: build, build on a condition, or don't build alone.`;
