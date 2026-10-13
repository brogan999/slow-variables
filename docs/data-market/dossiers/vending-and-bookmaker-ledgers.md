# Vending operators' and bookmakers' ledgers

Two small-business ledgers share this page and get different verdicts.

## The record

**Vending.** The machines stand on premises that belong to others, and their owner, the operator, travels a round to restock them. A small modem in each machine reports every sale, stock level and fault. The ledger holds, for each machine, the layout of products and prices, every sale with its time, every restock visit, each price or product change, write-offs and the commission paid to the site.

An illustration, not a real file: a machine in a hospital corridor sells 60 colas a week at A$4. The operator raises the price to A$5. Sales fall to 50 a week, so weekly takings rise from A$240 to A$250. The operator then halves the restocking visits to one a week, the cola runs out on a Thursday, and about 10 sales are lost. Decision, response and cash result sit in one ledger within weeks.

**Bookmaking.** A bookmaker's trader sets the odds on each runner and moves them as money arrives. The ledger holds each price offered with the time of each change, each bet taken, the amount the book stands to lose on each outcome, the closing price just before the event starts, and the result. The trade treats the closing price as the best estimate of the true chance.

An illustration, not a real file: a trader opens a horse at $5.00. Two customers known to be well informed each bet $400. The trader cuts the price to $4.00. By the start the horse is $3.50 elsewhere. The cut was in the right direction and too small. The horse wins and the book loses $3,000 on the race.

## Why it might matter for training AI

**Vending.** The best-known test of whether an AI system can run a business over a long stretch, Vending-Bench from Andon Labs, simulates exactly this trade. Andon says of it that "daily sales are simulated based on equations that can be gamed" [vending-bench-2]. The original paper says an AI system invents the three demand numbers behind each product [vending-bench-paper]. A real ledger could ground that simulation.

**Bookmaking.** The closing price is a fast, hard check on a forecast.

In neither case was a lab or vendor found buying such records.

## Who holds it and who may share it

**Vending.** The operator owns the ledger. The telemetry company processes it.

One published term cuts against sharing. The terms that Nayax, one such company, sets for its developer interface list as prohibited "Selling, licensing, or purchasing DZ Data", defined to include "data anonymized, aggregated or derived from such data" [nayax-devzone]. On that wording, an operator that draws its own records out through the interface may not sell them. Nayax's main terms of service were not opened, and other telemetry companies' terms were not found.

**Bookmaking.** The bookmaker owns its ledger. Customer accounts are personal information. One racing-industry article counts 371 registered bookmakers in Australia in 2024 [the-straight]. The on-course trade has been shrinking: the bookmakers' association told Parliament around 2011 that it represented about 600 on-course bookmakers and that their share of turnover had fallen from 9.3% to 2.8% in a decade [aba-submission]. Licence conditions were not opened. Whether on-course ledger software keeps a timed history of every price change, or only the bets struck, was not established.

## Who is already there

**Vending.** Andon Labs runs real AI-operated machines with Anthropic, so it has a small real ledger of its own [project-vend-2]. Real sales data has been used in research: one forecasting paper draws on a Chinese operator's 3,023 machines and more than 30 million transactions [usff-paper]. It holds sales only, without the operator's restock and price decisions. Nobody was found selling real decision ledgers.

**Bookmaking.** The checkable part is public and already packaged. PuntersEdge, an Australian service, offers "every price move for a race, per runner per book" across 15 racing bookmakers, with closing prices and results [puntersedge]. Public tests already score AI systems against betting markets. One, covering 104 football matches, reports that "none beats the market's Brier score", a standard measure of forecast accuracy [wc2026-agents].

A bookmaker's own ledger adds only what is private: the bets, the customers behind them and how the book was balanced.

## What would have to be stripped

**Vending.** Very little. Card details sit with the payment processor. Site names and addresses would go, since a site's contract may make its sales confidential.

**Bookmaking.** A great deal. Customer names, account numbers, betting histories and credit balances are personal. Bookmakers also mark their winning customers, which is the most informative field and the most sensitive.

## What stands in the way

**Vending**

- The ledger records sales at whatever prices the operator set. It does not show what would have sold at other prices, so a demand formula is still needed.
- The natural buyer already runs real machines.
- At least one telemetry company's terms bar selling the data.

**Bookmaking**

- Prices, closing prices and results are public, and an archive of them is already on sale.
- The private part is customers' betting data.
- Small on-course books may hold no timed record of price changes.
- No buyer was found. Whether labs avoid gambling data was not established.

> **A model's judgement, not a reading:** for vending, worth a small test. A real ledger answers a flaw the best-known test's own maker has put in writing, but there is one obvious buyer, which runs real machines already, and the ledger by itself cannot show what would have sold at other prices. For bookmaking, weak: the check is real, but the prices and results are public and already sold, and the only private layer is customers' bets.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
