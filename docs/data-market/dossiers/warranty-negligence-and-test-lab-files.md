# Three files with an outside verdict: home-warranty claims, lawyers' negligence claims, and failed product tests

This page covers three unrelated records that share one feature: an outside party later says whether the work was right. They reach different verdicts, so each is marked throughout: **H** for home warranty, **L** for lawyers' negligence, **T** for test laboratories.

## The record

**H.** Three Australian states, New South Wales, Victoria and Queensland, make builders take out state-run insurance for every home they build. Should the builder die, vanish or become insolvent, the scheme pays for the house to be finished or repaired. The claim file holds the owner's claim, an inspector's itemised list of work to be done (the scope), quotes from several builders against that list, the chosen quote and what was finally paid. A second file, on the builder, holds the accounts the insurer used to decide how much work that builder may take on. The verdict there is whether the builder later fails.

An illustration, not a real file: a builder is wound up when a house has only its frame standing. The scheme's inspector writes a scope. Five builders quote against it, from $180,000 to $240,000. The owner picks one at $200,000. Mid-job the new builder finds rotten framing that was not on the list, and the final cost is $220,000. So the file runs from scope to five prices, to the price chosen, to the sum paid.

**L.** Every solicitor must carry insurance against their own mistakes, in most states from a single mutual insurer tied to the law society. A solicitor who makes or fears a mistake notifies the insurer. The claim file holds that notice, the documents from the original matter, the insurer's estimate of cost, its defence lawyers' advice and the outcome. The Victorian insurer publishes anonymised cases of this kind for teaching.

**T.** A maker submits a product to an accredited laboratory to test whether it gives off, or suffers from, radio interference, or whether it is electrically safe. If it fails, an engineer changes the design and it is tested again. The record is the design, the measured failure, the fix and the passing retest. A physical instrument gives both verdicts.

## Why it might matter for training AI

Each is professional work with a hard check attached: a price against what was paid, a lawyer's file against a finding of error, a design against a measuring instrument. Vendors' pages show labs asking for checks of that kind.

No purchase of any of the three by a lab or a vendor was found.

## Who holds it and who may share it

**H.** The holders are the owners: three state bodies. In New South Wales the insurer icare received 749 new claims in a year and covered 23,943 builders [icare-ar]. It invites up to five builders to quote on each claim [icare-quoting], and pays Equifax to run its checks on builders [icare-ar]. In Victoria the insurance authority received 14,342 claims over five years [vago], and responsibility moved to the Building and Plumbing Commission in July 2025 [bpc]. In Queensland, claims for unfinished homes rose from 212 to 730 to 1,387 over three years [qbcc-ar]. The builder who finishes a job owns its own quote and invoices, and the homeowner receives the inspector's report. The state privacy and public-records laws were not opened, so whether any agency may license claim files is not established.

**L.** The insurer owns its claim file, but the documents inside it came from a client's matter. The Victorian insurer opened 514 matters in a year, of which 261 were claims [lplc-ar]. The New South Wales insurer received 714 notifications in a year, by the prior-year figure in the Law Society's 2024 annual report [lawsoc-nsw-ar]. The rules protecting a client's communications with a lawyer were not opened for this dossier. The working assumption is that the protection is the client's to give up, not the insurer's; that is not established here.

**T.** The manufacturer owns the report and the laboratory is bound to secrecy. The international standard that laboratories are accredited against treats information obtained during testing as confidential unless the customer has made it public [iso-17025]. One Australian laboratory's terms pass ownership of the report to the customer on payment and forbid the laboratory to disclose it without the customer's written consent [emctech-terms]. Only the manufacturer can license it.

## Who is already there

**H.** The agencies run the quoting themselves, and Equifax runs the builder scoring. Neither has shown any wish to sell.

**L.** The holders already give the lessons away. The Victorian insurer publishes risk guides and case notes [lplc-ar]. Florida's insurance regulator publishes a database of closed claims against lawyers, with 8,175 entries [florida-study]. Harvey has released a legal test of more than a thousand tasks openly [harvey-lab].

**T.** Passing reports for certified radio devices are public in the United States. Failures and fixes are not, and nobody holds them pooled. Two young companies sell software that works from a customer's own reports: Crado ranks the likely causes of a failure [crado], and Fuchsia manages the compliance process [fuchsia]. Free tools predict interference from a circuit-board layout [kicad-emc].

## What would have to be stripped

**H.** Homeowners' names, addresses and hardship notes, and builders' and their directors' finances. A builder's accounts are hard to disguise from anyone who knows the trade. In December 2025 the Victorian Ombudsman published a report on how that state's insurer handled claims after a large builder collapsed [vic-ombudsman].

**L.** Nearly everything: client confidences, settlement terms, and details of vulnerable clients.

**T.** No personal information. The sensitive content is the design itself, and a fix often reveals a weakness in it.

## What stands in the way

- **H:** the owner is a government agency under public criticism with no reason to license; no buyer has been shown; the work is already done in-house.
- **L:** the client's confidence stands between the file and any sale; the lessons are free; open legal tests and a public claims database remove the scarcity.
- **T:** manufacturers guard design files, so consent will be partial; no buyer has been shown; judging whether a different fix would also have worked needs scarce engineers; two start-ups are asking the same customers for the same files.

> **A model's judgement, not a reading:**
> **Home-warranty claims: weak.** The record is as good as it looked, but a state agency facing public criticism owns it, and the agencies and their contractor already do the estimating themselves.
> **Lawyers' negligence claims: weak, and dead for the raw files.** The client's confidence blocks release, the insurers give the lessons away, and freely available legal tests and a public claims database remove the scarcity.
> **Failed product tests: worth a test.** Ownership is clean, the check is a physical instrument, and no pooled set exists; but no lab buyer has been shown and owners will guard their designs.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
