# Every Bottleneck to AI Diffusion Named by Narayanan and Kapoor

*Consolidated from 224 verbatim-verified passages across 18 essays at normaltech.ai (2024 to 2026). Bottlenecks are grouped by the authors' own four-stage framework: methods → products → individual adoption → organizational and structural adaptation, plus the external, regulatory, safety, and market limits that act across stages. Source codes in brackets are expanded in the legend at the end. The raw passages with quotes are in `bottlenecks_raw.json`.*

## Theoretical foundations

The bottleneck list below is built only from claims the authors make themselves. Four intellectual lineages sit behind it. Two of them supply concrete mechanisms that appear as numbered entries. The other two frame the list rather than populate it.

**1. The economic history of general-purpose technologies.** The most concrete source, cited directly in the flagship essay through Paul David's 1990 paper on electrification and the Solow productivity paradox. It supplies entries 28, 29, and 61.

> "As an example, Paul A. David's analysis of electrification shows that the productivity benefits took decades to fully materialize. Electric dynamos were 'everywhere but in the productivity statistics' for nearly 40 years after Edison's first central generating station. This was not just technological inertia; factory owners found that electrification did not bring substantial efficiency gains. What eventually allowed gains to be realized was redesigning the entire layout of factories around the logic of production lines." [ANT]

**2. Jeffrey Ding on diffusion capacity.** Cited by name in three essays. Ding's argument that a nation's capacity to spread innovations through its economy matters more than who invents first supplies entries 37 and 38.

> "As Jeffrey Ding has shown, the capacity to diffuse innovations throughout the economy varies greatly between countries and has a major effect on their overall power and economic growth. As an example of how diffusion can be a bottleneck, recall the example of the electrification of factories described above." [ANT]

> "The important question in the context of great power competition is not which country builds AGI first, but rather which country better enables diffusion." [AGI]

**3. Diffusion-of-innovations theory.** Named once, in a footnote, as the origin of the four-stage framework that organizes this list. The authors never cite Rogers by name or use his adoption attributes, so the theory provides the skeleton (methods, products, individual adoption, structural adaptation) but no individual entries.

> "The framework is adapted from the classic diffusion-of-innovations theory and also influenced by recent writers such as Jeffrey Ding who have analyzed geopolitical competition in AI through the lens of the innovation-diffusion gap." [Guide]

**4. Rejection of technological determinism.** Stated as a core premise in two essays. It is the reason the authors believe external barriers exist at all, and why they treat impacts as emergent rather than readable from the technology. It has no numbered entry because it is a premise, not a barrier.

> "The normal technology frame is about the relationship between technology and society. It rejects technological determinism, especially the notion of AI itself as an agent in determining its future. It is guided by lessons from past technological revolutions, such as the slow and uncertain nature of technology adoption and diffusion." [ANT]

> "Unpredictable societal effects have been a hallmark of powerful technologies ranging from automobiles to social media. This is because they are emergent effects of complex interactions between technology and people. They don't tend to be predictable based on the logic of the technology alone. That's why rejecting technological determinism is one of the core premises of the normal technology essay." [Guide]

## Stage 1: Methods → products (the model-to-product gap)

1. **Application development effort does not vanish.** The "bitter lesson" applies to methods, not products. Real applications still need hand-built business logic, frontends, integrations, and evaluation. [ANT, Slowing, Pivot]
2. **Proof-of-concept to product gap.** A demo that works 90% of the time is a capability, not a product. Executives see quick prototypes and miss the 90% of work needed to finish them. [Pivot, SWE, Slowing]
3. **Capability-reliability gap.** Accuracy has risen sharply while reliability has moved only a few points. A model that is right 70% of the time but fails unpredictably cannot remove the human from the loop, and reliability fixes are application-specific. [ANT, Slowing, Left, OWE]
4. **Compounding unreliability in agents.** An agent making dozens of LLM calls with even a 2% error rate per step becomes useless end to end. [AgentsMatter]
5. **Users expect software-like determinism.** People expect AI products to behave like software. Stochastic outputs violate that expectation, and it is unclear whether determinism can be engineered in. [Pivot, AGI]
6. **Missing interface paradigms.** Current AI products are like PCs before the GUI. Higher-bandwidth interfaces that let users supervise without constant interruption have not been invented. [Slowing, Pivot]
7. **Domain-specific product design.** General capabilities have to be made useful one domain at a time, which requires deep domain knowledge to find the adoption hurdles (Cursor's code-verification UI is their example). [AGI]
8. **AI companies neglected product engineering.** Labs assumed generality exempted them from UX and software engineering, and are rediscovering that both are hard. [Slowing]
9. **Cost of inference.** Cost, not capability, blocks many applications, especially agentic workflows that call models hundreds of times. Cost also sets accuracy, since retries improve success. [Scaling, Pivot, AgentsMatter, OWE]
10. **Judgment tasks resist evaluation.** The tasks whose automation would most transform a profession (legal filings, research) have no single correct answer, so they are the hardest to evaluate and improve. [ANT, Legal]
11. **No verifiers in open domains.** AI became superhuman at chess because of fast, accurate feedback. Law, medicine, and science have no such verifier, so progress is limited to automatically checkable tasks. [Moravec, Agents26]
12. **Real-world knowledge caps reasoning.** AI reasoning in medicine is limited by the medical knowledge that exists, the same limit humans face. [Moravec]
13. **Brittleness outside closed domains.** Systems that excel in narrow demos go off the rails in open-ended settings. [Moravec, OWE]
14. **Agents lack judgment for open-ended work.** In their shadow evaluations, frontier agents given real research questions lacked judgment, creativity, and the ability to backtrack or respond to feedback. [Agents26, OWE]
15. **Non-functional requirements go unmet.** Agent-built software sacrifices quality, maintainability, and security, and successes often rest on human-built test suites, thousands of lines of prompt, or memorized training data. [OWE, Google]
16. **Benchmarks lack construct validity.** Benchmarks overweight what models are good at, miss contextual reasoning, and encourage agents that score well without being useful. Vendor claims cannot be independently checked. [Legal, AgentsMatter, Google]
17. **Real-world messiness cannot be simulated.** Whether a system can automate a job is only knowable after diffusion, because no lab environment captures the world's complexity. [AGI, OWE]

## Stage 2: Product → individual adoption

18. **Deployment is not diffusion.** Instant availability to hundreds of millions says nothing about how many people use a capability, for how long, or for what. [Guide, ANT]
19. **Low intensity of use.** Most users use generative AI infrequently. Nearly a year after release, under 1% of ChatGPT users touched thinking models on a given day. [ANT, Guide]
20. **Human learning curves.** Taking advantage of AI requires continual learning of new workflows and topics. The curve is steep and time-consuming, and it moves at human speed. [Guide, Left, AGI]
21. **Workflow and habit change.** The hard part of adoption is users adapting their workflows, which cannot even start in the first months after a launch. [ANT, Guide, Legal]
22. **Most adoption decisions are "no."** Because deployment is instant, people constantly face adoption choices, and the vast majority of the time they decline, for rational and irrational reasons. [Guide]
23. **Cost of supervising agents.** Agentic work requires constant human supervision, which is time-consuming and mentally exhausting, so realized productivity lags. [SWE, OWE]
24. **Skill erosion and the dependence spiral.** Using AI for tasks one has not mastered erodes skill and control, so responsible users limit offloading. Vendor-specific skills replace unaided ones. [Left, Stack]
25. **Skilled judgment gates "democratization."** Past waves of no-code failed because the barrier is not syntax but the judgment and accountability needed to make good decisions. [SWE]
26. **Verification needs domain expertise.** Checking whether an agent actually succeeded at an open-ended task takes deep expertise and time, and long logs cannot be fully reviewed. [OWE, Left]
27. **Privacy resistance.** Useful assistants need access to sensitive personal and organizational data, which triggers outcry and regulatory limits on data sharing. [Pivot, ANT]

## Stage 3: Organizational and structural adaptation

28. **Organizational change is slower than individual change.** For past general-purpose technologies this stage took decades. It has barely begun even in software engineering. [ANT, Guide, Left, Pivot]
29. **Drop-in replacement fails.** Like electrification, benefits only arrive once work is reorganized: new layouts, processes, hiring, and training. The restructuring is discovered by experimentation, not designed in advance. [ANT, Left]
30. **Tacit organizational knowledge.** Much of what organizations know is unwritten and not in training data. It has to be made available to models gradually through adoption, sector by sector. [ANT, Left, SWE]
31. **Integration into existing systems.** Models must be wired into the many systems organizations already run, a downstream task no model release solves. Enterprise data is locked in Salesforce, Workday, and SAP. [Left, Stack]
32. **Task specification is human labor.** Unambiguously saying what is wanted is a large share of the work. Brooks's "essential complexity" of specification is untouched by AI. [ANT, SWE]
33. **The "decide" and "deliver" layers do not compress.** Understanding requirements and taking accountability for what ships remain human. Once a decision is delegable it stops being a competitive advantage, so human judgment migrates upward. [SWE, Left]
34. **Staged trust.** Organizations grant AI access to consequential decisions only after it proves reliable in less critical contexts. [ANT]
35. **Human-in-the-loop erodes benefits.** Requiring approval of every action mostly destroys the value of automation, so it degrades into rubber-stamping or is outcompeted. [ANT]
36. **Collective action and sclerotic institutions.** Structural change requires solving coordination problems or reforming institutions, which is far less predictable than user behavior (air traffic control is their example). [Guide, AGI]
37. **Underinvestment in complements.** Diffusion depends on public goods the private sector underprovides: AI literacy, workforce training, digitization, open data. [ANT, AGI]
38. **National diffusion capacity.** Following Jeffrey Ding, countries differ enormously in their ability to spread innovations through the economy, and this, not who reaches a milestone first, sets economic outcomes. [ANT, AGI]
39. **Bespoke deployment.** Transforming workplaces requires forward-deployed engineers and consulting partnerships, labor-intensive work outside the product. [Stack, Guide]
40. **Enterprise resistance to lock-in.** Embedded "digital workers" create extreme lock-in and target labor budgets, so enterprises resist, withhold data for training, and demand portability. [Stack]
41. **Deskilling breaks the talent pipeline.** Automating entry-level tasks removes the experiences through which juniors build expertise, a cost that emerges only over time. [Legal, SWE]
42. **Millions of small adaptations.** Impact arrives through countless mundane process and policy tweaks, not a single leap. [AGI, ANT]

## Regulatory, legal, and institutional limits

43. **Regulation in high-consequence domains.** FDA, EU AI Act, and sector rules make deployment slow by design, and regulation often outright prohibits current AI use in productive settings. [ANT, Left, SWE]
44. **Liability uncertainty.** Unclear application of liability law deters adoption. Clear rules (FAA drone rules in 2016) spur it. [ANT, SWE]
45. **Professional guardrails.** Malpractice liability, professional codes, and device regulation keep doctors from delegating decisions to chatbots. [Guide]
46. **Regulation that freezes categories.** Rules insensitive to experimentation reify business models and organizational forms prematurely, and binary automated/not-automated rules discourage new oversight designs. [ANT]
47. **Misplaced burdens on model developers.** Regulation blind to the developer/deployer split saddles general-purpose model makers with context-specific obligations. [ANT]
48. **Unauthorized practice of law.** UPL rules and their state-by-state vagueness deter new entrants, and bar associations cite model unreliability as grounds for caution. [Legal]
49. **Law firm ownership rules.** Restrictions on who can own or share fees with law firms block outside capital and scaled business models. [Legal]
50. **Incumbent resistance to reform.** Lawyers and commerce groups lobby to narrow regulatory sandboxes despite scant evidence of harm. [Legal]
51. **Human adjudication time.** The speed of human judges, lawyers, and clients caps how fast legal processes can move. Adding judges is politically fraught, and Article III likely requires human judges. [Legal]
52. **Courts may restrict access.** Flooded courts respond by tightening doctrines to keep litigants out or by banning AI, counteracting the gains. [Legal]
53. **Policy-mandated human steps.** Platform policies require developer accounts, 2FA dialogs that block synthetic input, and a human pressing publish. [OWE]
54. **State capacity sclerosis.** Veto points and proceduralism hobble governments' ability to deploy AI, coordinate resilience, or even provide services they could. [Gov, ANT]
55. **Policy backlash.** Self-driving cars took 15+ years to deploy and now face bans because policymakers failed to prepare. Public anxiety and backlash from rushed deployments are headwinds. [Moravec, ANT, Left, Pivot]

## External-world and physical speed limits

56. **Clinical trials and real-world experiments.** Treatments need trials with thousands of people over 10 to 15 years. Progress needs data from real experiments that faster AI cannot speed up, and society will not let AI run large-scale experiments on people. [Left, AGI, Agents26]
57. **Costly, unsimulable errors.** Where mistakes are expensive and the world cannot be simulated (driving), safety throttles each iteration of the improvement loop. [ANT]
58. **AI targets non-bottleneck steps.** In an already technological, regulated world, the workflow parts AI improves were optimized by earlier waves. The true bottlenecks resist for external reasons. [Guide]
59. **Physical and social task bundles.** Jobs bundle inspection, loading, paperwork, and negotiation with the "core" task. Bio-harm still depends on materials, equipment, and tacit know-how. [ANT, Gov]
60. **Slow external review.** Deployment depends on systems the developer does not control. An app took 45 minutes to build and ten days to pass App Store review. [OWE]
61. **Infrastructure, energy, and compute.** Grid capacity constrains training and inference. Token supply is scarce today. Breakthroughs deploy slowly when supporting infrastructure does not exist yet (steam to electric took 40 years). [ANT, Stack, Agents26, Moravec]
62. **Inherent limits on prediction.** Many tasks resemble long-range weather forecasting, where mathematical limits are already reached. Forecasting and persuasion have high irreducible error. [Left, ANT, SciTool]
63. **Unrecognized latent bottlenecks and Amdahl's law.** Constraints like RL environments or energy only become visible once they bind, and if many hard steps remain, a hundredfold speedup on the AI-amenable parts yields a small overall gain. [Agents26]

## Safety speed limits (deliberate brakes)

64. **Safety limits in high-consequence tasks.** They predict slow diffusion will remain the norm where errors matter, enforced by regulators and by organizations' own caution. [ANT, AGI]
65. **Business incentives against unsupervised deployment.** Poorly controlled AI is bad business. Unrecoverable failures like deleting production data make companies pull back from hasty automation. [ANT, AGI, Left, Science]
66. **The general-purpose / high-stakes / automated trilemma.** For now an agent can be only two of the three, which keeps AI a collaboration technology rather than an automation one. [Left]
67. **Legibility and control.** Removing humans from task boundaries to let AI run end to end reduces oversight, so autonomy is checked by the need to keep systems legible. [ANT]
68. **Society's choice to keep humans accountable.** Liability law and sector regulation are speed controls society can strengthen deliberately, regardless of capability. [SWE, Left]
69. **Security risks of capable scaffolds.** Prompt injection, data leakage, and agent worms must be solved before assistants get broad access; scaffolds capable enough to test the frontier carry risks that may prevent use. [Pivot, OWE]

## Market and economic limits

70. **Automation devalues the automated task.** Once a task is automated its value collapses and humans move to unautomated tasks, so the AGI goalpost keeps moving. [ANT, AGI]
71. **Competitive arms races dissipate gains.** In law and science, competition is so intense that productivity gains fuel escalation rather than societal value. [Guide, Legal]
72. **Credence goods.** Buyers cannot verify the quality of legal work or judgment-heavy AI output even in hindsight, so they rely on prestige and trust, and normal price competition fails. [Legal, Stack]
73. **Input-based incentives.** Billable hours reward more hours and more output regardless of outcome, absorbing efficiency gains. [Legal]
74. **Growth is capped by the slowest sector.** AI's uneven sectoral effects mean long-run growth is bottlenecked by wherever it diffuses least. [AGI]
75. **Commodity trap and recoupment.** Undifferentiated models push inference to marginal cost, outcomes are hard to measure so value pricing stalls, and incumbents own distribution. This limits how far labs can fund diffusion. [Stack]
76. **Fixed consumer attention.** More apps do not increase usage, capping AI's impact on consumer software. [SWE]
77. **Publisher distrust.** Media organizations' justified wariness and inability to bargain collectively limit the use of journalistic content. [ANT]

## Science-specific bottlenecks

78. **Production of findings is not the bottleneck.** Cheap generation of results will not unlock progress because producing findings is not what limits science. [AGI, Science]
79. **Overproduction drowns novel work.** Attention is finite. As volume explodes, novel work is lost and AI search concentrates attention on already-famous papers. [Science]
80. **Publish-or-perish incentives.** Institutions reward measurable production, making researchers risk-averse and making AI a tool for chasing metrics. Reform is blocked by inertia and Goodhart's law. [Science]
81. **Scientists lack software engineering practice.** Most AI-for-science is software work, but fields have not adopted testing, version control, or code review, so leakage and other errors affect hundreds of papers. [Science, SciTool]
82. **Science does not self-correct.** Code and data go unshared, reviewers do not check code, retractions are near zero, and there is no incentive to debunk. [Science, SciTool]
83. **Prediction without understanding.** AI improves predictive accuracy without explanation, like epicycles, so wrong theories can persist and human understanding, which is the point of science, erodes. [Science, Left, SciTool]
84. **Epistemology change exceeds field capacity.** Adopting AI requires re-litigating validity per field and model type, which no field can do in a couple of years. [SciTool]
85. **Misdirected tools and funding.** AI-for-science tools chase headlines rather than real bottlenecks like error detection, and are evaluated on time saved, not on understanding. [Science, SciTool]

## Upstream: why AI cannot simply accelerate its own diffusion

The authors treat these as the reason recursive self-improvement does not escape the bottlenecks above.

86. **External bottlenecks are immune to self-improvement.** Limits on AI's power sit in deployment, not in the system's design, so improving the design cannot overcome them. [Guide, ANT]
87. **Herding, compute, and declining openness in methods research.** Research herds around fashionable ideas, compute and cost constrain new paradigms, and the industry's culture of open sharing is fading. The AI community may be unusually bad at finding new paradigms. [ANT, Guide]
88. **Data exhaustion.** Readily available data is spent, and more data costs ever more in money, licensing, and reputational risk. Continued scaling is a business decision, not a technical given. [Scaling, Slowing]
89. **Evaluation does not scale.** Every capability increase creates new demand for domain-specific evaluation, which resists automation and absorbs human effort. [Left]

## Legend

| Code | Essay | Date |
|---|---|---|
| ANT | [AI as Normal Technology](https://www.normaltech.ai/p/ai-as-normal-technology) | 2025-04-15 |
| Guide | [A guide to understanding AI as normal technology](https://www.normaltech.ai/p/a-guide-to-understanding-ai-as-normal) | 2025-09-09 |
| AGI | [AGI is not a milestone](https://www.normaltech.ai/p/agi-is-not-a-milestone) | 2025-05-01 |
| Legal | [AI Won’t Automatically Make Legal Services Cheaper](https://www.normaltech.ai/p/ai-wont-automatically-make-legal) | 2026-02-12 |
| SWE | [Why AI hasn’t replaced software engineers, and won’t](https://www.normaltech.ai/p/why-ai-hasnt-replaced-software-engineers) | 2026-06-11 |
| Left | [What will be left for us to work on?](https://www.normaltech.ai/p/what-will-be-left-for-us-to-work) | 2026-07-13 |
| Stack | [Up the Stack: How AI’s Escape From the Commodity Trap Risks Enterprise Lock-in](https://www.normaltech.ai/p/up-the-stack-how-ais-escape-from) | 2026-07-09 |
| Science | [Could AI slow science?](https://www.normaltech.ai/p/could-ai-slow-science) | 2025-07-16 |
| Agents26 | [AI agents can't yet do open-ended AI research](https://www.normaltech.ai/p/ai-agents-cant-yet-do-open-ended) | 2026-08-05 |
| OWE | [Open-world evaluations for measuring frontier AI capabilities](https://www.normaltech.ai/p/open-world-evaluations-for-measuring) | 2026-04-16 |
| Gov | [Do AI Risks Require Extraordinary Government Intervention?](https://www.normaltech.ai/p/do-ai-risks-require-extraordinary) | 2026-05-21 |
| Scaling | [AI scaling myths](https://www.normaltech.ai/p/ai-scaling-myths) | 2024-06-27 |
| Pivot | [AI companies are pivoting from creating gods to building products. Good.](https://www.normaltech.ai/p/ai-companies-are-pivoting-from-creating) | 2024-08-19 |
| Slowing | [Is AI progress slowing down?](https://www.normaltech.ai/p/is-ai-progress-slowing-down) | 2024-12-18 |
| AgentsMatter | [New paper: AI agents that matter](https://www.normaltech.ai/p/new-paper-ai-agents-that-matter) | 2024-07-03 |
| SciTool | [Scientists should use AI as a tool, not an oracle](https://www.normaltech.ai/p/scientists-should-use-ai-as-a-tool) | 2024-06-03 |
| Google | [Did Google’s AI agents really build an operating system for $916?](https://www.normaltech.ai/p/did-googles-ai-agents-really-build) | 2026-05-22 |
| Moravec | [Fact checking Moravec's paradox](https://www.normaltech.ai/p/fact-checking-moravecs-paradox) | 2026-01-29 |
