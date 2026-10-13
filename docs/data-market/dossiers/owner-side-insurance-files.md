# Insurance claim files held outside the big insurers

## The record

Large insurers do not license their claim files. This page looks at the same kind of file in three places where someone else owns it. The three get different verdicts.

**The policyholder's claims professional.** A loss assessor, called a public adjuster in the United States, works for the person claiming and not for the insurer, usually for a share of whatever is recovered. The file holds the policy, photographs, the assessor's estimate, the insurer's first offer or refusal, the correspondence and the final settlement.

**Companies that insure themselves.** A company may carry its own risk under a licence to self-insure injuries at work, or through an insurance company it owns. It keeps its own files, from the injury report and medical certificates to the final settlement.

**Sold-off old claims.** An insurer that leaves a line of business can pass its unsettled claims to a specialist buyer, which pays them out, sometimes over decades. The file is years of claim notes, legal advice, medical reports, the reserve held from time to time and the last payment.

An illustration, not a real file, with invented round figures. Hail damages a house. The insurer's inspector offers $36,000. The owner hires a public adjuster for a fee of a tenth of the payout. The adjuster reads the policy, finds a clause covering the cost of meeting current building rules, writes an itemised estimate and asks for more. The insurer adds $12,000. The final payment is $48,000 and the fee is $4,800. The file holds two rival estimates of one loss, the argument, and the figure both sides accepted.

## Why it might matter for training AI

Vendors' pages show labs asking for finance and insurance records, for expert judgement with its reasoning, and for checks that are hard to game. A policyholder-side file offers both sides' numbers and a result the other side agreed to.

No lab has been shown buying records labelled with their outcome, here or elsewhere. The evidence is indirect: Huzzle Labs is building a test from real policies and claim files, scored against the recorded outcome, with sensitive material removed or replaced [huzzle].

## Who holds it and who may share it

**Loss assessors.** In Australia, a guidance sheet from the corporate regulator says that since January 2022 a person paid to pursue a claim on a policyholder's behalf needs a financial services licence that covers claims handling [asic-253]. Several firms are tied to repair builders, so many files end in a repair and not in a negotiated sum. The working file is the firm's, and the policyholder is the firm's client.

**Self-insurers.** Regulators publish the lists: New South Wales names banks, supermarkets, a university and local councils [sira], and Victoria lists 33 [worksafe-vic]. A self-insurer stands as the insurer and the files are its own.

**Buyers of old claims.** A trade magazine counted 42 public deals in 2025, moving about US$5.4 billion of reserves [runoff-mag]. After a full legal transfer the buyer owns the files.

**Privacy.** The Australian privacy regulator's guidance on the principle governing use and disclosure says personal information may be used only for the purpose it was collected for, and that for sensitive information, which includes health information, a second purpose needs consent or a direct relation to the first [oaic-app6]. The guidance does not mention AI training.

## Who is already there

- **InsureThing** released a test of 160 tasks in 2026, written by specialists and not drawn from closed files [insurething].
- **A Chinese university group** published 3,780 cases built on real claim materials and expanded by a language model; the best model scored 73.15% on decision and amount together [insclaimbench].
- **Tailshift** is itself a buyer of old liability claims, and says it holds broad sets of claim notes and legal and medical records, which it uses to price deals [tailshift].

No one turned up licensing files from the policyholder's side that show the first offer and the final payment. The test built from claim files, however, already has several entrants.

## What would have to be stripped

Property files hold names, addresses, pictures of homes and policy numbers: ordinary personal data. Injury files hold named people's medical histories, which are hard to anonymise when a rare injury happens at a known employer. Old-claims files add legal advice and confidentiality terms owed to the original insurer.

## What stands in the way

- No buyer has been shown for claims labelled with their outcome, while several tests already cover the ground.
- The final payment is a bargain struck between two sides, not a correct answer.
- For injury files, consent and anonymising are costly.
- Buyers of old claims treat the data as their advantage and will not sell it.
- In Australia there are few such files, and a good share finish with a builder's repair.

> **A model's judgement, not a reading:** policyholder-side property files are worth a test: ownership is clean, the data is ordinary and every file holds two rival estimates and an agreed result, though no buyer for that form has been shown and others are already building the test version. Self-insured injury files are weak, because they are health records. Sold-off old claims are dead for practical purposes, because their owners treat the data as their edge.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
