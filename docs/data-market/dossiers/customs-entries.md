# Customs entries and what the border agency later decided

## The record

Three records sit on this page, and each has its own verdict.

**The whole declaration with its later correction.** Every commercial shipment entering a country is declared to the border agency. A declaration names the goods and gives the tariff code that sets the duty, the value, where they were made and whether a trade agreement lowers the duty. A licensed customs broker usually files it for the importer. Some declarations are checked later, by a request for documents, an audit, a penalty or a refund. A checked declaration is professional work with an outside verdict: the original line, the documents behind it, the finding and the corrected line.

**The tariff code alone.** Choosing the code for a product, taken as a task by itself.

**Freight invoice disputes.** A shipper agrees rates with carriers. Each carrier's invoice is checked against the contract, mismatches are disputed, and the carrier gives a credit or refuses with proof. The record is the invoice, the contract terms, the dispute and the carrier's reply.

A worked example from the Australian border agency's own monitoring. Over nine months of the 2024–25 year it checked 5,226 import declaration lines [abf-update]. It found errors in 1,579 of them, which is 30.2% [abf-update]. The most common error was the tariff code, with 351 detections [abf-update]. So roughly three checked lines in ten were wrong somewhere, and the code was the commonest fault.

An illustration of one corrected file, not a real one: a broker files insulated steel bottles as general household steelware and claims a trade-agreement discount. An audit later finds the wrong code, a discount certificate that did not cover the supplier, and a wrong value.

## Why it might matter for training AI

Vendors' pages show labs asking for long office work on real documents and for checks that are hard to game. Here the check comes from a party with the opposite interest: the agency collecting the duty, or the carrier that sent the bill. That is rarer than an expert's opinion.

No purchase of whole declarations with corrections, or of freight disputes, by a lab or a vendor was found.

## Who holds it and who may share it

The importer owns its declarations. The broker holds copies as the importer's agent. The broker's software company processes them. The agency holds the outcomes.

**United States.** The customs agency ruled in January 2026 on who may share them. Its ruling restates the regulation that keeps a broker's client records confidential unless a court orders disclosure or the client authorises it in writing, then says the regulation "does not constrain an importer's ability to divulge its own records" [cbp-ruling]. The same ruling says a company without a broker's licence is doing customs business impermissibly if its AI tool suggests codes beyond the six-digit level for goods that will be entered [cbp-ruling]. The ruling thus separates sharing past records from advising on live shipments.

**Australia.** The border agency's guide to penalty notices says owners must keep commercial documents for 5 years [abf-guide]. No rule matching the American confidentiality regulation was found in the broker licence conditions that were read. That is a gap in this dossier and not a finding.

**Freight.** The shipper owns its invoices and disputes; the audit firm processes them. Cass Information Systems says that in 2025 it handled 35 million freight invoices, worth US$37 billion [cass].

## Who is already there

The tariff code alone is well covered in public. A research group released 18,731 published American rulings, covering 2,992 codes, as a training and test set; the general model it tested scored 25% on the full ten-digit code and a fine-tuned open model 40% [atlas]. A second test used 632 online shop products labelled by 26 tariff experts; the best AI agent scored 46.8% against 95.0% for the experts [hscodecomp].

Several companies train on their own flow. Zonos says its classifier learns from official rulings and from the product listings it sees daily [zonos]. WiseTech, a maker of freight-forwarding software, publishes terms for its AI agents saying the customer always owns its data and that none is extracted [wisetech]. In freight, Loop says its software audits invoices against contracts and opens and tracks disputes with carriers [loop].

What no public set holds is the whole declaration with a real correction, covering code, value, origin and discount together with the documents. Freight disputes with carriers' replies sit only with the firms that process them.

## What would have to be stripped

There is little personal information: named contacts, sole traders, brokers' staff. The sensitive content is commercial. Who the suppliers are, what each unit costs and how much is bought are trade secrets, and an audit finding records the importer's own mistake, so only files already settled with the agency would be suitable.

## What stands in the way

- Nobody has been shown to want it. Demand for logistics records is voiced by middlemen, not buyers.
- The best-known part of the task is already public, which holds down the value of anything nearby.
- Most declarations are never checked. Those that end in a real correction are few and arrive years late.
- Importers are reluctant to hand over supplier prices and evidence of their own errors.
- The software companies that process declarations and freight bills can build on them without anyone's help.

> **A model's judgement, not a reading:** whole declarations with audit corrections, gathered with each importer's consent, are worth a test: the right to share is clearer here than in most records and there is little personal data, though no buyer is proven. Freight invoice disputes are weak. Tariff codes alone are dead, because the public record already covers them.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
