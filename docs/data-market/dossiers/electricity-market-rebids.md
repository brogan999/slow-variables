# Electricity market rebids and the trader's written reason

## The record

Eastern and southern Australia share one wholesale electricity market. Every generator, battery and large flexible load tells the market operator, AEMO, how much power it will supply at each step of a ladder of prices. The prices on the ladder are fixed the day before. The volume offered at each step can still be moved until shortly before the power is needed. Each such move is a rebid. The operator's software then chooses the cheapest workable set of offers and sets a price for each region, interval by interval.

The market rules say each rebid must come with a brief, verifiable and specific reason [ner-3822]. The published table holds the reason as a short line of text, a one-letter category (plant, a change in the operator's forecast or instructions, commercial, or error) and the times of the event the trader relied on [mms-model]. All of it is released the next day.

An illustration, not a real file: at 9:35 in the morning the operator's forecast of Queensland demand rises from 2,400 to 2,600 megawatts. A trader at a gas plant moves 150 megawatts from the $300 step down to the $60 step so the plant will be called on, and files the reason "0935 A 30-MIN PD FORECAST DEMAND INCREASE 2400 2600". Minutes later the public tables show how much the plant was told to generate and what the region's price was. So one record is the state of the market beforehand, the move, a one-line reason, and what the market then paid.

## Why it might matter for training AI

Vendors' pages show labs asking for practice tasks with a check that is hard to game. Here the check is a market price. The record could only be useful as a practice setting, where a system places bids against a replay of a past day and is scored on the money they would have earned, or as a private test. As raw data it has little value, because anyone may download it.

No purchase of an energy-market practice setting by a lab or a vendor was found.

## Who holds it and who may share it

AEMO publishes the bids. Its copyright notice gives a general permission for anyone to use AEMO material "for any purpose", provided it is attributed accurately [aemo-copyright].

Two loose ends remain. The general terms of use on the same website speak of personal use, or use as authorised, and point to the permission notice [aemo-legal]; the two pages sit awkwardly together. And the reason text is written by the trader, not by AEMO or on its behalf. Whether the permission reaches that text was not established.

Traders' own internal logs are fuller than the published line and are not public.

The energy regulator reports that rebids grew from 5.4 million a year in 2020 [aer-2026] to 73 million in 2025 [aer-2026].

## Who is already there

A university group has released free tools that download the bid tables, chart bids by plant, and replay the market. The replay tool's documentation says it can recreate past dispatch closely from the public bids [nempy]. The hard part of a practice setting, the engine, is therefore already free.

Researchers have studied rebids for years: a consultant's report for the market's rule-maker [roam], a journal study in 2016 [energy-econ-2016] and public code covering a decade of rebidding [rebid-analysis]. A 2024 paper tuned a language model on participants' bids to forecast prices; only its abstract was read [llm-bids-2024].

Free tests of AI systems on electricity markets exist for Texas [ercot-bench], for battery trading with language-model agents [alphasearch], for several American markets [energyagentbench] and for Europe [bessbidder]. Commercial auto-bidding software already does the live job for batteries.

Nobody was found packaging the reason text itself.

## What would have to be stripped

Nothing, by design: the record describes plants and companies. Whether some reason lines carry a trader's initials was not checked.

## What stands in the way

- The data is free to everyone and the replay engine is open source, so nothing here can be held exclusively.
- The reasons are thin. The regulator's own template is a time, a category letter and a few words [aer-guideline], and a practitioner's guide says they are often vague [mdavis].
- Most reasons are now written by software. The regulator says automated bidding accounts for the vast majority of rebids by renewable and battery plants [aer-bulletin-2026]. It opened a review of its rebidding guideline in March 2026 that canvasses the use of artificial intelligence in bidding [aer-consult-2026].
- Scoring is contestable for any plant large enough to move the price, because the replay must then guess how rivals would have responded. The replay tool is documented only for repeating history, not for changing one participant's bids.
- Demand for energy trading in particular is voiced by a middleman, not a buyer.

> **A model's judgement, not a reading:** weak. The permission to use the data is clear and the outcome is a real market price, but the data is free to all, an open replay engine already exists, and the written reasons are short compliance lines that software now mostly produces.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
