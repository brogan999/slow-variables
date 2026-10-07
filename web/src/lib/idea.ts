// The one question a reader's own business idea becomes. The reader sees it as the question asked, so it is in plain
// words; the idea leads, so a follow-up that remembers only the start of a turn still carries it.
export const IDEA_MAX = 450;

const clip = (idea: string) => Array.from(idea.trim()).slice(0, IDEA_MAX).join("");

export const ideaQuestion = (idea: string) =>
  `Business idea: "${clip(idea)}". Reason it through from the site's assessment of the value chain, its rent rule and its futures. Where does it sit on the value chain and what is scarce there, where would its profit pool by the rent rule, which of the site's futures would strengthen or weaken it, and what would prove it wrong? Say which parts are your judgement, and keep it short. End with one call on the business: build, build on a condition, or don't build alone.`;
