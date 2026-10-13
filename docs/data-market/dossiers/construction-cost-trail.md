# The construction cost trail: lender's monthly reports, cost plans and bid estimates

## The record

A quantity surveyor is the professional who measures and prices building work. This page covers three linked records that set a cost forecast against what the work finally cost.

**The lender's surveyor's reports.** A bank or private lender funding a development hires its own quantity surveyor. Before the loan the surveyor reports on whether the building contract price is enough and whether approvals and insurance are in place. Then, each month, the surveyor reviews the builder's claim for payment. The profession's guidance lists what that report holds, including the adjusted contract sum, the value of work completed, the current valuation, progress against the programme and a certificate of the cost to complete [nziqs-2019]. The lender releases that month's money on the certificate.

**Cost plan against final account.** The developer's surveyor prices the design at each stage, then administers the contract. The final account is what the building cost after all changes.

**A civil contractor's bid against actual cost.** A road or pipeline builder prices a tender line by line in estimating software, then tracks actual labour, machinery and materials against the same cost codes.

An illustration, not a real file: a lender funds a $40 million apartment project with a $30 million building contract. In one month the builder claims $3 million. The lender's surveyor walks the site, values the work done at $2.5 million, refuses cladding that is still off site, and certifies $2.5 million. Some months later, changes to the work have used up most of the allowance for surprises, and the surveyor reports that the cost to finish now exceeds the money left in the loan. The lender asks the developer to put in more of its own. The building is finished for $32 million, against a tender-stage cost plan of $29 million.

Each month is a judgement followed by a number that later proves right or wrong.

## Why it might matter for training AI

Vendors' pages show labs asking for construction records, among them estimates and change orders, and for tasks with a check that is hard to game. Cost plans and bids give one answer per project, years later. The lender's reports give a run of certified steps on each.

No purchase of such records by a lab or a vendor was found. The sign of value is that product companies build on them: one American lending-software firm says its payment-review product draws on more than $3 trillion [built-lenders] of real estate finance data.

## Who holds it and who may share it

**Lender's reports.** Quantity-surveying firms, banks and private lenders hold them. The guidance note read, a New Zealand adaptation of the Australian one, says reports go only to the lender that appointed the surveyor unless that lender releases them in writing, and should not be passed on without the authority of both surveyor and lender [nziqs-2019]. So two consents are needed, and in practice a third, because the report describes the borrower's project and its builder. The Australian original was not read.

**Cost plans.** The surveying firm holds the working files. Its client owns the project's commercial information. No firm's engagement terms were found. One slice is public: large projects assessed by the state in New South Wales need a cost report from a certified surveyor on a standard form, and these are published [nsw-edc]. One such report, for a Sydney project, gives an estimate of more than a hundred and eight million Australian dollars [wt-edc] before tax. This is the estimate only. No final account is published.

**Civil bids.** The contractor owns both ends and can consent alone.

**Software platforms.** Procore's customer agreement says customer data remains owned exclusively by the customer, while Procore may compile aggregated data [procore-ssa]. A third-party summary of Procore's developer terms says makers of commercial apps may not use data drawn through its connections to train or test AI systems [procore-summary]; Procore's own page was not opened. Autodesk's terms say a customer's content stays the customer's and that Autodesk uses it in connection with providing and improving its products [autodesk-terms].

## Who is already there

In the United States, a lending-software company launched an AI product in 2025 that reviews builders' payment claims for lenders. It says the product handles thousands of claims a month and can review one in as few as three [built-draw] minutes.

A British cost service sells benchmarks drawn from 21,000 [bcis] projects. It sells averages and cost breakdowns, not the stage-by-stage trail.

No Australian firm was found selling, or training on, cost plans paired with final accounts.

## What would have to be stripped

There is little personal information: the names of consultants and site staff, and signed declarations by the builder's officers. The sensitive content is commercial: the borrower's loan terms, the builder's margins and rates, and the lender's view of the credit.

## What stands in the way

- Lender's reports need the lender's and the surveyor's consent, and in practice the borrower's. One refusal ends it.
- No lab has been shown to buy an estimate paired with the actual cost.
- An American company already holds the equivalent record at a scale that makes an Australian sample look small.
- A report that shows a surveyor missed a cost overrun is evidence against that firm. Firms also treat their archives as an edge.
- Each project yields one final answer, and it arrives late.

> **A model's judgement, not a reading:** worth a small test for the lender's monthly reports and for civil contractors' bids against actual cost: the monthly trail is long, checked at each step and light on personal information, with no Australian firm found working on it, though release needs several consents and no lab has been shown to buy it. Weak for surveyors' cost-plan archives.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
