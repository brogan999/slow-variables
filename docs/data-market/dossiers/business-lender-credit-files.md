# Business lenders' credit files and invoice-finance ledgers

## The record

This page covers two records kept by lenders to small and mid-sized businesses.

**The credit file.** For a business loan: the application and accounts, the analyst's credit memo (a written case for lending that covers the business, its cash flow, the security, the risks, the proposed terms and a risk grade), the approval and its conditions, the yearly review notes, and any waivers. If the loan goes bad, the file continues with demand letters, a rescue deal or the appointment of a receiver, the sale of the security and the final loss.

**The invoice-finance ledger.** A business raises cash against its unpaid invoices. The financier records each invoice offered, any check made with the customer who owes the money, the cash advanced, and then what happened: paid in full, paid short, disputed, or found to be fake.

An illustration, not a real file: a lender advances $400,000 to a labour-hire firm against its invoices. The memo notes that a handful of customers owe most of the money, sets a limit and takes a guarantee from the director. Some months later a checking call finds one customer disputing $100,000, and the lender stops funding that customer's invoices. Then the largest customer collapses and the lender appoints a receiver over its client. Within two years it has recovered 60 cents in the dollar. The last step follows a real pattern: the administrators' report on one failed Australian financier records its lender appointing receivers over invoice-finance clients [bizpay-report].

The answer comes quickly for an invoice and slowly for a loan.

## Why it might matter for training AI

Vendors' pages show labs asking for finance work, for expert judgement with reasons, and for real records where the steps are visible. A memo followed by the loan's actual result offers judgement with an outcome attached.

No purchase of such records by a lab or a vendor was found. Where labs want a banker's reasoning, the evidence is that they pay experts to write it fresh.

## Who holds it and who may share it

Lenders hold their own files. The dossier found several Australian non-bank business lenders that failed or sold books in recent years. One, liquidated in 2023, had a loan pool valued at $2.56 million [herald-funda] and by a press account had assessed loans within a day. Another entered administration the same year with a loan book of about 150 [bizpay-report] clients, carried at $2.7 million [bizpay-report], and was later sold through a deed with its creditors [bizpay-deed]. A listed company sold its invoice-finance portfolio for $2 million [spenda-grapple] in 2025. One working financier has told investors it is merging three [earlypay-fy25] old loan systems into one.

Invoice finance is sizeable. An industry yearbook estimates about A$95 billion [bcr-2026] of invoices were financed in Australia in 2025.

On a sale of a loan book the buyer takes the debts and, in the wording of one such deed, the benefit of the contracts [bizpay-deed]. In an insolvency the secured lender's receiver usually controls the loan book and the liquidator the company's records.

Controlling a file is not the same as a right to reuse it. Borrowers' information is held in confidence. For credit-bureau reports inside a file, the credit-reporting part of the Privacy Act restricts use and disclosure to listed purposes [privacy-act]; only its headings and definitions were read, so what those sections permit was not established. Whether a liquidator may sell copies of a failed lender's files with names removed was also not established.

## Who is already there

One American processor of loan applications says it handles roughly 750,000 [ocrolus] a month and sells credit signals built on the resulting dataset inside its own product. That is bank statements, not memos or recoveries.

A maker of memo-drafting software for banks advertises a contractual promise that neither it nor its suppliers may use bank or borrower data to train or improve foundation models [aloan]. Lenders are starting to demand that clause.

A research company sells a map of who lends to whom in the United States, built from more than 40 million [applied-econ] archived loan documents covering 1.8 million [applied-econ] firms. Nothing suggests it contains credit memos.

No seller, dataset or public test was found for the whole file from memo to recovery.

## What would have to be stripped

A company borrower is not a person, but small-business files are full of people: directors, guarantors, sole traders, their tax returns, home addresses and the properties pledged. Credit-bureau reports and anything derived from them would have to come out. So would the names of the customers on an invoice ledger, which are businesses with their own claims to confidentiality.

## What stands in the way

- The rich file is not where the failures are. Lenders that fail tend to be newer firms that decide by algorithm in a day, so a written memo and yearly reviews may barely exist. This is an inference from how fast those lenders said they assessed loans.
- Confidence and credit-reporting law fence the most useful parts, and lenders increasingly write a ban on training into their contracts.
- No buyer has been shown for records that carry real outcomes.
- Australian volumes from any one failed lender are small.
- Processors and software platforms already capture the value where it exists.

> **A model's judgement, not a reading:** weak for credit files. The memo-to-recovery file is wanted in principle and nobody sells it, but the Australian lenders whose failure might release files hold thin ones, the law fences the credit-bureau parts, and no buyer has been shown. The invoice-finance ledger of a small working financier is the one part worth a closer look.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
