# Contests that produce graded expert reasoning

## The record

A competition can be designed so that what it leaves behind is a professional's reasoning, in writing, about a real case, plus an independent fact showing whether that reasoning held up. This page covers two versions, and they come out differently.

**The case contest.** The organiser has a stock of cases that are finished but whose results were never published: insurance claims, disputes, loans. Each entrant studies a file, says how it ended and explains the call. The real outcome scores them. A forward-looking variant uses decisions that have not yet been made.

**The drill-target challenge.** A miner opens up its exploration data and entrants propose drilling spots, with reasons. The best proposals get drilled, and the score is the laboratory's reading of how much metal the rock holds.

A worked example of the drill version, from a real contest. In 2019 OZ Minerals, a miner, ran the Explorer Challenge with Unearthed, a contest platform, offering a prize pool of A$1 million, drawing "over one thousand global participants from sixty-two countries" [unearthed-2019]. The company then drilled "the top consensus targets ... in an initial program of 5 holes for 2,503.1m", and reported that "no significant mineralisation was intersected" [ozl-q4-2019]. Five scored outcomes, all negative.

## Why it might matter for training AI

A real case with a real result is hard to fake, and data vendors' pages show labs asking for expert judgement and for tests that cannot be gamed.

What was found shows interest in forecasting as a test of AI systems, not as something bought from people. Metaculus, a forecasting site, runs tournaments for AI bots [metaculus-aib]. Mantic, a company building forecasting systems, says it raised US$25 million [mantic]. No price paid by a lab for human forecasters' written reasoning was found.

## Who holds it and who may share it

**The reasoning.** What an entrant writes is the entrant's, unless the rules of the contest transfer or license it. Since the organiser drafts those rules, ownership can be settled cleanly from the start. The terms of the two mining contests on this point were not read.

**The cases.** They belong to the insurer, lender, law firm or dispute body that handled them. If the outcomes are public, as court judgments are, an AI system may already have seen them.

**The drilling data and results.** They belong to the mining company.

On Australian contest law, Victoria's gambling regulator advises anyone running a commercial-scale tipping competition online to take legal advice on the federal interactive gambling law [vgccc]. The statutes themselves were not opened, so how an outcome-prediction contest would be classed was not established.

## Who is already there

Every component exists.

- **Mining.** Besides the Explorer Challenge, a Canadian contest in 2016 offered C$1 million for targets on an old gold mine [integra]. No drilling result from it was found.
- **Forecasting.** Metaculus runs FutureEval to measure the forecasting accuracy of AI [metaculus-futureeval]. Mantic says its system beat all 676 human entrants in one Metaculus contest in 2026 [mantic].
- **Law.** A research paper gave 200 American class-action complaints to legal experts, who predicted the outcome correctly 53% of the time against 63% for a small AI system [classaction-paper].
- **Insurance.** A paper from October 2026 describes a test of 3,780 claim cases "grounded in real claim materials" [insclaimbench]. A broker, DataNexx, lists closed insurance claims with "assessor reports ... and settlement outcomes" for licence [datanexx].

What was not found is a contest set up in order to sell labs the scored reasoning of practitioners.

## What would have to be stripped

For the case contest, the files carry personal and sensitive information, and every limit that binds the holder of the files passes through to the organiser. An entrant who works in the field must not draw on an employer's knowledge of the actual case. The purpose of the contest, including any use for training AI, would have to be told to entrants at the start.

For the drill version there is nothing personal. The constraint is when a listed company may release its results.

## What stands in the way

**The case contest**

- No buyer for human forecasting reasoning has been shown.
- Professionals are not reliably better than AI systems at predicting bare outcomes, so the word "expert" may carry little.
- Without private, unpublished cases it becomes what a forecasting site already does.
- One outcome is a weak score for a piece of reasoning. People are often right for the wrong reasons.
- The legal class of a prediction contest varies by state.

**The drill-target challenge**

- Far too few scored outcomes for the money: five holes from the one Australian precedent, none positive.

> **A model's judgement, not a reading:** for the case contest, worth a small test in its forward-looking form, on public decisions not yet made; it gives clean ownership and an objective score cheaply, but nothing yet shows a lab paying for human forecasting reasoning. For the drill-target challenge, dead: the one Australian precedent produced a handful of scored outcomes, all negative, at great cost.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
