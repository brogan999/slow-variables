# Two smaller records: small-aircraft defect logs, and forecasts set against what happened

This page covers two unrelated records with different verdicts. Each is marked throughout: **A** for aircraft, **F** for forecasts.

## The record

**A.** Two linked records exist for a small aircraft. The defect log records every fault that a pilot or an engineer reports, the action taken, and whether the repair was lawfully put off for a period. A repeat defect is the same fault coming back soon after it was signed off, which shows the first diagnosis was wrong. The second record pairs the reason a part was removed with what the workshop found when it stripped the part down. A finding of "no fault found" tells us the part was sound and the diagnosis was wrong.

An illustration, not a real file: a flying school's training aircraft is written up for a flickering charging light. The engineer tightens a loose connector and signs it off. Ten flying hours later the same fault is written up. The engineer removes the alternator and sends it away; the workshop tests it and finds nothing wrong. The fault is reported a third time, and this time the voltage regulator is changed, and the fault does not return in the next 200 hours. Three diagnoses: two shown wrong by later facts, one shown right.

**F.** A company forecasts its own cash or budget, saves the forecast at successive dates, and later learns the real figure.

An illustration, not a real file: in November a distributor budgets revenue of $4.0 million for the March quarter. In January it revises this to $3.8 million because a customer's order is late. In February it revises again to $3.6 million. The ledger later shows $3.5 million. Every version notes which assumptions moved and the reason. The check is the bank statement, and every version was fixed in place before the answer was known.

## Why it might matter for training AI

**A.** Fault-finding with a physical check fits what vendors' pages show labs asking for: tasks whose marking is hard to game. No purchase of this kind of record was found.

**F.** Finance is among the most repeated requests. A forecast with a sealed date can be turned into a test: hand a model the company's books as they stood on the forecast date, have it predict the figure, mark that against the outcome, and set it beside the finance team's own forecast. No purchase of this was found either. But finance tests are being built quickly and the best AI systems fall well short on several. MBABench has 101 whole-workbook tasks [mbabench].

## Who holds it and who may share it

**A.** In Australia the log belongs to the aircraft's registered holder. The Civil Aviation Regulations require the holder of the certificate of registration to maintain a log book for the aircraft and to make it available to the regulator and to people maintaining the aircraft [car-50a]. A schedule to the same regulations lets some sign-offs sit in either the log book or the maintenance organisation's own work records [casa-sched6]. The log therefore belongs to the owner or flying school, the job records to the maintenance shop, and the strip-down report to the overhaul workshop. Linking a removal to a finding needs two or three consents. Rules on how long records must be kept were not read.

For airliners the same information already flows to the manufacturer. Airbus's reporting guide asks operators for removal records and suppliers for workshop findings in a standard format [airbus-guide].

**F.** The company owns its forecasts outright. An accountant or software company only holds them. The weak point is the versions: many firms overwrite the file. Where versions survive is in dated documents such as monthly board papers, reports to lenders, and the document sets shown to investors. Two published checklists for such document sets list budget-against-actual comparisons as standard items [telegent] [aistartupcfo]. No law or software term was found that stops an owner licensing its own forecasts, though lender and investor confidentiality clauses were not checked.

## Who is already there

**A.** A free public body of text exists. The US aviation regulator publishes each year's reports of malfunctions and defects as a downloadable file [faa-sdr], and the Australian regulator has a searchable service for major defects [casa-drs]. An open test for airliner maintenance, CAMB, has 7,969 multiple-choice items and 50 fault trees built from real troubleshooting cases [camb]. Several young companies review aircraft records with AI, but for the sale and lease of airliners and engines; one, TRecs, took an investment from an engine maker's leasing arm in May 2026 [businesswire-trecs]. None was found handling the defect logs of small aircraft, and none claims to sell data.

**F.** The tests that exist ask a model to build a spreadsheet model or explain a gap from numbers it is given. BlueFin has 131 finance spreadsheet tasks, and the best model scores under 50% [bluefin]. On FrontierFinance, experts score 77.2% and the best model 70.9% [frontierfinance]. FINCH built 172 workflows partly from the files of Enron, a company that failed in 2001, and the best model passes 38.4% [finch]. None scores a forecast against the eventual outcome at a real, privately owned company. That one of them reached back to Enron for real version histories suggests how scarce the material is.

## What would have to be stripped

**A.** Pilots' and engineers' names and licence numbers, and the registration mark, which identifies the owner. Passages quoted from maintenance manuals are the manufacturer's copyright.

**F.** The numbers usually contain nothing personal. The commentary may name customers, staff and salaries.

## What stands in the way

- **A:** no buyer; a free public body of defect reports and an open test already exist; the records are handwritten and scattered; linking them needs several consents; each holder has little.
- **F:** the versions may simply not exist, because files are overwritten; a single outcome is a noisy mark for one forecast, so many are needed; it appears on no buyer's list of wants; on short-range cash, models may already do as well as finance teams, in which case nobody needs the test.

> **A model's judgement, not a reading:**
> **Small-aircraft defect logs: weak.** The ownership is straightforward and the field is empty, but no buyer has been shown, a free public body of defect reports and an open test already exist, and the companies in the field serve airliner lessors.
> **Forecast versions against actuals: worth a test, as an addition only.** It costs almost nothing to include when a company's records are already being licensed, a bank statement that arrives after the forecast does the marking, and today's finance tests hold nothing like it; but old versions are often lost, and they are on no buyer's list of wants.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
