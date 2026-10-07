// The one question a reader's own business idea becomes. The reader sees it as the question asked, so it is in plain
// words; the idea leads, so a follow-up that remembers only the start of a turn still carries it.
export const IDEA_MAX = 450;

const clip = (text: string, max = IDEA_MAX) => Array.from(text.trim().replaceAll('"', "'")).slice(0, max).join("");
const NAME_MAX = 80;

export const ideaQuestion = (idea: string) =>
  `Business idea: "${clip(idea)}". Reason it through from the site's assessment of the value chain, its rent rule and its futures. Where does it sit on the value chain and what is scarce there, where would its profit pool by the rent rule, which of the site's futures would strengthen or weaken it, and what would prove it wrong? Say which parts are your judgement, and keep it short. End with one call on the business: build, build on a condition, or don't build alone.`;

// The one question a company on the map becomes: the company and the part of the chain the map places it on.
export const companyQuestion = (company: string, part: string) =>
  `Company: "${clip(company, NAME_MAX)}", which the site's map of the value chain places on "${clip(part, NAME_MAX)}". Reason through the business it is in from the site's assessment of the value chain, its rent rule and its futures. What is scarce where it sits, where does the profit pool by the rent rule, which of the site's futures would strengthen or weaken it, and what would prove the view wrong? Say which parts are your judgement, and keep it short. End with one call on its position: well placed, placed on a condition, or exposed.`;
