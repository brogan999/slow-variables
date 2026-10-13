# Heir-search files and travel agents' debit memos

Two records share this page and get different verdicts.

## The record

**Heir searches.** Sometimes a person dies leaving no will and no known close relatives. The lawful heirs then have to be proved. A probate genealogist reconstructs the family from certificates of birth, marriage and death and from other records, across countries, until every entitled person is identified and found. In the file are a log of the research, the certificates, the argument for every link, the dead ends and the finished tree. Then a court, an insurer or a public trustee accepts the tree or rejects it.

A worked example, from a case the New South Wales public trustee published with the name changed. "Max" died without a will in 2017 with four known siblings. Because his father had been born in England, certificates were ordered from there. They "revealed Max's father had a further five children with three different partners" [nswtg-genealogy]. Some certificates were missing, so the trustee applied to the Supreme Court, which "confirmed entitlement in accordance with the research done by the team" [nswtg-genealogy].

**Debit memos.** Travel agents book flights in a reservation system, often by typing terse commands. If an airline's auditors later find a ticket broke a fare rule, or used the wrong commission or tax, the airline bills the agency for the difference. The bill is called a debit memo. The agency pays or disputes it. The record is the commands typed, the booking, the fare rules that applied, the memo and the reason code on it, and the outcome.

An illustration, not a real file: an agent changes the date on a ticket and collects a A$150 change fee, misreading a rule that also required the fare to be re-priced. Months later the airline sends a memo for A$400. The agency disputes it, the airline rejects the dispute, and the agency pays.

## Why it might matter for training AI

**Heir searches** are long investigations across many kinds of record, with dead ends, and a court's acceptance as the check. **Debit memos** are a record of software use marked by an outside auditor with money attached.

In neither case was a lab or vendor found buying the record.

## Who holds it and who may share it

**Heir searches.** The trustee or the research firm owns its file. The New South Wales trustee said in 2022 that it was "administering over 2000 intestate estates, 745 of which involve overseas research" [nswtg-nowill]. Where a matter goes to court, the judgment is public and sets out the tree and the reasoning.

Much of the evidence comes from sources used under licence. The Australian terms of Ancestry, in the 2017 version that was opened, allow its content to be used "only for personal or professional family history research" and say "Resale of a work or database or portion thereof is prohibited" [ancestry-terms]. The conditions on registry certificates were not opened.

**Debit memos.** Every ticketing agency holds its own memos. The typed commands are held by the reservation system; whether agencies keep their own logs was not established.

The numbers are large but old. An airline industry working group reported about 2.35 to 2.4 million a year worldwide in 2015 and 2016 [iata-adm-2017]. Nothing newer was found.

The reservation systems' terms are the obstacle. Amadeus's standard terms say the subscriber "shall not compile, cache, sell, distribute or otherwise make available" Amadeus System Data except as expressly permitted [amadeus-terms]. They also bar using the system to train any "third party in the use of the Amadeus System" [amadeus-terms]. The screens an agent sees contain fares and rules, which are system data. The standard agency terms of the other two large systems were not found.

## Who is already there

**Heir searches.** An open-source project, cowork-genealogy, gives an AI system research skills over a free genealogy service, and its repository includes an evaluation harness [cowork-genealogy]. It is free. No company or dataset using closed probate files was found.

**Debit memos.** Start-ups already sell tools to agencies. Aidah says its product, which sits inside Amadeus, brings a "90% reduction in ticket-related ADMs" [aidah]. No sale of command or memo data to labs was found.

## What would have to be stripped

**Heir searches.** Living heirs appear by name in every file, along with their birth dates and addresses, who their parents were, and any adoptions or births outside marriage. Removing the living removes the last generation of the tree, which is what the search was for. How Australian privacy law treats the dead was not established.

**Debit memos.** Passenger names, passport and loyalty numbers, contact details and card fragments. Airlines' private fares and commission agreements are confidential.

## What stands in the way

**Heir searches**

- Take out the living and the answer goes with them; leave them in and privacy is breached.
- A free tool of the same shape exists.
- The evidence is licensed and cannot be passed on whole.
- Published judgments may already have been read by AI systems.
- No buyer was found.

**Debit memos**

- The reservation systems' terms bar compiling or distributing what appears on screen.
- Tools for writing commands and preventing memos are already on sale.
- A usable practice version would need a working imitation of a reservation system with real fare rules. That is the real cost; the agency's files are a small input.

> **A model's judgement, not a reading:** for heir searches, worth a test, though not a strong one. Court judgments offer a free and lawful sample with a verdict attached, but the answer sits in living people's details, a free equivalent exists, and the likely result is a small one-off set of test cases. For debit memos, weak: the check is excellent and the volume large, but the reservation systems' terms bar sharing what agents see, start-ups already sell the obvious products, and the real cost lies in imitating the system.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
