# Records that must be made, not found

This page covers five ways of making a record that would not otherwise exist, or could not otherwise be licensed. They reach different verdicts, so each carries a letter throughout.

## The record

A created record exists only because somebody arranged three things beforehand: permission, a way to capture the work, and a later check on the result.

- **A. Own a business.** The operator of a small real business owns everything it produces: quotes, jobs, ledgers, staff messages, results.
- **B. Give away software.** A tool a business uses every day, for meeting notes or bookkeeping, whose terms give its maker a licence to what passes through.
- **C. Trade a discount for rights.** A firm that installs AI for a client charges less and keeps a copy, with identities removed, of the inputs, steps and results.
- **D. Pay professionals.** A person supplies a finished piece of real work, with the request that prompted it, under a licence.
- **E. Run a panel.** A business owner records a real decision while its result is still unknown, then reports months later how it turned out.

A real example of D. OpenAI's GDPval test is made up of 1,320 tasks drawn from 44 occupations, every one built on real work that someone produced [gdpval]. The professionals who wrote them averaged 14 years' experience, were paid at least US$40 an hour, and each task went through five rounds of expert review [gdpval-paper]. The average task in the core set takes a professional 404 minutes, worth US$361 at median wages [gdpval-paper].

For E, an illustration, not a real file: the owner of a 40-person freight firm records that she will raise prices by 10% on a large but barely profitable customer, and puts the chance of acceptance at 60%. Six months later she reports that the customer accepted 8%. Because the entry was closed before anyone knew the answer, no model can have come across it.

## Why it might matter for training AI

Vendors' pages show labs asking for real work with the process visible, for expert judgement with reasons, and for tests no model has seen. They also show buyers checking where a record came from. With created data, every item can come with its own proof of consent. Most found data cannot offer that.

D has been bought, by action: OpenAI built GDPval this way [gdpval], and WIRED reported in January 2026 that its contractors were being asked to upload real work from past jobs [wired-upload]. For A, labs have reached such data by taking ownership stakes or lending staff; nothing was found showing cash paid for the data itself. For E, no buyer was found.

## Who holds it and who may share it

Ownership is fixed by contract at the moment of creation, which is the point of the category.

- **A.** The business owns its records, subject to its contracts with customers and its privacy promises to them.
- **B.** The user owns its data; the software maker has only the licence its terms grant. JetBrains, the nearest precedent, collects detailed data from companies only when an administrator switches sharing on, and says it will not pass the data to third parties [jetbrains-faq].
- **C.** The data stays the client's, and a copy is licensed.
- **D.** The catch is the employment contract. Handshake asks contributors for documents they own or are authorised to share, and Inc. noted that most employees do not own the documents they create at work [inc-handshake]. Someone who owns the business, practises alone, or freelances with rights retained is placed differently.
- **E.** The owner owns what they write and the documents of their own business.

The Australian privacy and workplace-surveillance rules that would bear on A and B were not opened.

## Who is already there

**A** is occupied by capital. OpenAI took an ownership stake in Thrive Holdings, which buys accounting and IT-services firms, and placed its own research and engineering teams inside the group's companies [reuters-thrive]. General Catalyst says it generally invests upwards of US$100 million in each such business [gc-services], and that one of them, Long Lake, has made 40 acquisitions [gc-longlake]. Andon Labs runs a real shop in San Francisco with an AI manager; the shop had lost US$40,000 by August 2026 [sfstandard].

**B** has a single precedent, and the data there stays with the software maker. JetBrains gives free one-year subscriptions to selected companies willing to share data for its own models [jetbrains-blog]. No free software funded by reselling users' data was found.

**C** is described by one insider as a growing line for the largest vendors. No second source was found.

**D** has posted prices. Handshake offered US$6 a page for up to 50 documents of up to 100 pages each, capped at US$30,000 a person [bi-handshake].

**E** is nearly empty. Metaculus runs forecasting contests for AI systems [metaculus-bots], and sells paid forecasters' reasoning with prices on request [metaculus-pro]. No one was found selling logged decisions with their outcomes.

## What would have to be stripped

Customers' and clients' names from any work document. Staff, pay and health details. In D, anything that belongs to an employer: WIRED reported that OpenAI leaves it to contractors to remove confidential and personal details themselves [wired-upload]. In E, named staff and counterparties. Outcomes that people report about themselves can be wrong or flattering, so a document showing the result is needed.

## What stands in the way

- **A:** the capital needed is very large, and a lab's way in is an ownership stake, not a purchase of data.
- **B:** a long build before any data arrives.
- **C:** rests on one account; not a business alone.
- **D:** contributors submitting work that is not theirs; and it is unproven that a finished task sells for more than it costs to make.
- **E:** no buyer; one outcome is a noisy mark for one decision; people stop answering follow-ups.
- **All:** sales of created data depend on trust and a strong sample, and a newcomer has no one inside a lab to vouch for it.

> **A model's judgement, not a reading:**
> **A, own a business: weak** for anyone without large capital. It works as a strategy, but the players spend heavily and the lab involved was given equity, not charged.
> **B, give away software: weak.** The single precedent keeps its data for itself, and no one was found reselling.
> **C, discount for rights: worth a test, as a contract clause only.** It costs little to ask, and it is not a business in its own right.
> **D, pay professionals: worth a test.** No other route has published prices and a lab's own test made the same way; business owners own their work, which removes the flaw in the employee version. The margin is unproven.
> **E, run a panel: worth a test.** Cheap to try, and a sealed date makes it proof against a model having seen the answer; but no buyer, and a weak check.
> **Overall: worth a test**, as one panel of business owners supplying both real work and logged decisions.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
