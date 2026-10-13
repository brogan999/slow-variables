# Mining: ore-or-waste calls checked against what the mill received

## The record

A mine predicts what is in the ground several times, each time in finer detail. The resource model divides the rock into blocks and estimates the metal content, or grade, of each from widely spaced drill holes. The grade-control model re-estimates the same ground from closely spaced samples, days before it is dug. The dig plan then marks each patch as ore, low-grade or waste. Ore goes to the mill and waste to the dump.

The mill weighs and tests what actually arrives. Reconciliation is the monthly comparison of predicted tonnes, grade and metal against what the mill measured.

An illustration, not a real file: a geologist tests the samples from one level of a pit, estimates the grade of each block, and draws the line between ore and waste. The surveyor marks it on the ground and the trucks follow it. Over the month the mill processes a blend from several parts of the pit. At month end the reconciliation sheet shows that the mill received a tenth less metal than grade control predicted. Someone investigates why, and changes the estimating settings.

One real price exists, for mine data of a different kind. In 2023 a minerals explorer that uses AI paid another explorer US$175,000 [aem-2023] for test results, 13 [aem-2023] drill holes and airborne surveys covering ground the buyer itself held. That was a neighbour buying information about its own land, not a purchase of training data.

## Why it might matter for training AI

This is a prediction followed by a physical measurement, the kind of check that is hard to argue with.

The check is coarser than it looks. The mill measures a month's blended feed, often after the rock has sat in stockpiles. It does not say which block or which call was wrong. A mining software company's own case study describes stockpile grades being updated by hand in a spreadsheet at month end [datamine].

No lab, vendor or broker was found naming mining, and no purchase of this record was found.

## Who holds it and who may share it

The mining company or joint venture owns the record. The software companies only process it, and say so. One geology software maker's terms state that customer data remains the customer's and will be copied only as needed to provide the service [seequent-terms]. Another's statement on its AI feature says each training run uses only that user's own data and that the company keeps no copy [micromine-ai]. So no software company can license it, and some have promised in public not to pool it.

What the law makes public in Western Australia is exploration reports only. The state mines department's summary says explorers must file yearly reports and that the department may release them after five [wamex] years, subject to objections. Its archive holds over 120,000 [wamex-portal] reports, more than 105,000 [wamex-portal] of them public, and a database of more than 2 million [wamex] drill holes. None of it is grade control, dig plans or mill results. The regulation itself was not read.

Mines do change hands through insolvency. At a gold operation that entered administration in 2026, trade press reported about 40% [matsa] unplanned dilution, meaning waste mixed into the ore: a live case of ore-or-waste calls failing against production. In such cases the data is part of the secured asset and goes with the mine to its buyer, who needs it to restart.

## Who is already there

Software for the reconciliation task exists and is sold as software, with no data business attached [datamine] [intellisense].

One company builds machine-learning models for grade control and reconciliation inside each customer's site, using that site's existing data. It claims 32 to 55% [stratum-tech] lower deviation in reconciliation.

AI-led explorers buy or trade for exploration data: the purchase above and an alliance giving one explorer access to a large miner's exploration databases [bhp-kobold]. All of it is exploration, none reconciliation.

Public real data is scarce. One open set from a Brazilian processing plant has 737,453 [frothiq] rows and covers the plant side only.

No dataset, public test or seller of this record was found.

## What would have to be stripped

Almost no personal information: a geologist's initials on a log. The sensitive content is commercial. Grade and reconciliation results can move a listed company's share price. Joint-venture partners have confidentiality terms. Map layers that record native title and heritage sites would have to come out, and locations would have to be shifted and grades rescaled to hide the mine.

## What stands in the way

- No buyer was found outside mining-AI companies, and their customers hand them the data.
- The check is monthly and blended. At most mines the truth about a single block does not exist.
- The owner is the only party who can license it and has market reasons to refuse.
- When a mine is sold out of insolvency, the data follows the mine.

> **A model's judgement, not a reading:** weak. The record is real and plainly owned by the miner, but the check is coarser than it first appears, and the only buyers found are mining-AI companies that get the data from their own customers at no charge.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
