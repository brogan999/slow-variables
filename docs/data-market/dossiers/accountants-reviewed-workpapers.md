# Accountants' reviewed files: tax workpapers, audit files and private pension fund audits

## The record

Accounting work is checked in layers: a junior prepares the file, a senior marks what is wrong, the junior answers, and the file is signed. This page covers three versions of that record.

**Tax and accounting workpapers.** For each client each year: the source records, a schedule for each account, the preparer's treatment, the manager's queries, the answers, the tax return as filed, and sometimes a later change by the tax office.

**Audit files.** The risk assessment, the samples tested, the exceptions found, the manager's and partner's review notes with how each was cleared, the adjustments proposed and waived, and the signed opinion.

**Audits of self-managed super funds.** In Australia a family can run its own small pension fund, with the members as trustees. Each fund must be audited every year by a registered auditor, who gives one opinion on the accounts and another on whether the fund obeyed the pension law. Where a breach meets set tests, the auditor must report it to the tax office.

An illustration, not a real file: a fund's accountant sends the year's accounts and documents to the auditor. The auditor's checklist flags a $40,000 transfer to a member's personal bank account. The auditor asks whether it was a pension payment or a loan. The accountant replies that the member was short of cash and repaid it four months later. The auditor treats it as a loan to a member, applies the tax office's reporting tests, qualifies the compliance opinion, reports the breach as already put right, and writes to the trustees. The final check is a rule whose answer the regulator defined.

## Why it might matter for training AI

Vendors' pages show labs asking for accounting and tax firms' records and for expert judgement with reasons. A reviewer's query and the correction that follows is that.

The clearest sign of value is not a purchase. An investment group backed by OpenAI owns accounting firms in the United States and raised US$2 billion in 2026 [techcrunch-2026]. An account of its tax product says the product keeps what the software proposed, what the accountant changed and what went into the filed return [montana]. That is the review record, captured inside firms the group owns, with no data bought from anyone.

No purchase of pension fund audit files by a lab or a vendor was found.

## Who holds it and who may share it

There were about 672,805 [ato-mar-2026] self-managed funds in March 2026. One audit software product says it keeps review points, red flags and queries against each line and can export them with the audit file [cloudoffis].

Who may share is set by professional rules:

- The Australian auditing guidance on working papers says they are the auditor's property, and that the client's consent is needed before the auditor gives anyone else access unless the law requires it [gs011].
- The accountants' ethics code goes beyond disclosure. It says a member must not use confidential client information for the advantage of the member, the firm or a third party, unless the client has authorised it [apes110]. Whether removing names takes a file outside that rule was not established.
- The Tax Practitioners Board's code says a tax agent must not disclose a client's affairs to a third party without the client's permission or a legal duty [tpb].
- The software companies cannot be the route. Xero's developer terms say data drawn through its developer platform must not be used to train or fine-tune AI models [xero-terms]. MYOB's developer terms contain a similar bar and extend it to pooled or shared datasets [myob-terms]. Files a firm exports from its own system are a different matter.

## Who is already there

In the United States, the OpenAI-backed group described above. Nothing like it was found in Australia.

Australian makers of fund audit software describe automated checks and AI flags in their products [cloudoffis] [evolv] [asf]. None says it trains models on client files or sells data.

For Australian pension fund audit files, no buyer, public test or research paper was found.

## What would have to be stripped

These files are full of identified people: names, addresses, tax file numbers, bank accounts, income, fund balances and sometimes health details. All of it would have to go, and the amounts would have to be altered.

## What stands in the way

- Every file needs the client's authority. For a pension fund the client is the trustees, whom the auditor usually reaches only through the fund's accountant.
- The rules are Australian. Whether a lab would pay for work under one country's pension and tax law is unanswered.
- Auditors of these funds are closely watched by the tax office, and a seller who gets this wrong risks professional discipline.
- A group that owns firms can capture the same record from the inside.

> **A model's judgement, not a reading:** pension fund audit files are worth a small test: ownership is clear, the files are standard, the software keeps the review trail and the final check is a rule, but each file needs the client's authority and a buyer for Australian-only work is unproven. General tax and audit workpapers are weak for anyone who does not own the firms; that is a contest of capital already under way.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
