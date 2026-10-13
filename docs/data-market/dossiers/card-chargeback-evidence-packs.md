# Card chargebacks: the merchant's evidence pack and the bank's ruling

## The record

A chargeback is a cardholder asking their own bank, the issuer, to reverse a card payment. The merchant may contest it by sending an evidence pack through its bank or payment processor, the acquirer. A pack holds the order record, the delivery scan, device and network details, emails with the customer, the refund policy and a short letter of rebuttal. The issuer decides. Either side can then push the matter up to the card scheme, Visa or Mastercard, for a final ruling.

A worked example. The purchase is invented; the fee and time limits are from two Australian acquirers' merchant guides.

- A customer buys a jacket online from a Melbourne shop.
- Some weeks later the customer tells their bank the jacket never arrived. The bank raises a chargeback with a reason code.
- The shop's acquirer debits the purchase price and, at one large bank, a fee of A$25 [nab-guide]. One acquirer gives the shop 7 days [tyro-guide] to answer. The bank allows up to 30 days [nab-guide] on a Visa card and 45 days [nab-guide] on a Mastercard.
- The shop sends its pack: the order confirmation, the courier's proof of delivery, and a chat in which the customer asked about sizing after the delivery date.
- The issuer accepts or pushes back.
- The shop gets its money back, or does not.

The record is the claim, the reason code, the pack, and a win or loss in money a month or more later. Whether issuers give merchants written reasons was not established.

## Why it might matter for training AI

Vendors' pages show labs asking for practice tasks with a check that is hard to game. Here an outside party pays real money or does not. The usable form would be a practice setting in which a system gathers the evidence from order, shipping and support records, builds a pack, and is scored against what actually happened.

The result is noisy. A pack that lost may have been a good pack.

No purchase of this record by a lab or a vendor was found. The companies that value it collect it as a by-product of their own service.

## Who holds it and who may share it

Merchants hold their own packs. Acquirers, processors, dispute companies and the card schemes hold far more. Visa says it processed 106 million [visa-2026] disputes in 2025. A research firm's summary estimates 261 million [datos-2025] chargebacks worldwide that year and puts the Asia-Pacific dispute rate lowest of any region, at 0.007% [datos-2025] of card transactions against 0.051% [datos-2025] in North America.

Can a merchant license its own packs? The schemes' published rules say no, for anything that still contains transaction or cardholder information.

- Mastercard's rules say a merchant must not sell, provide or in any way disclose account or transaction data, or personal information about a cardholder, to anyone other than its acquirer, the acquirer's service provider, Mastercard, or a government with a valid demand. The ban extends to database files and other media created as a result of a transaction [mc-rules].
- Visa's rules let an acquirer or merchant disclose transaction information to third parties, without the issuer's and Visa's consent, only for three purposes: a loyalty programme, fraud control, and completing the original sale [visa-rules].

These rules reach the merchant through its acquirer's contract; one Australian acquirer's terms require compliance with scheme rules [tyro-terms].

Whether a pack with all identifying detail removed is still "transaction data" under the Mastercard rule is untested.

## Who is already there

Justt says it serves more than 250 [justt] enterprise merchants. Chargeflow says it learns from millions of past cases [chargeflow]. Stripe builds packs for its merchants from its own data and theirs and charges only on a win [stripe-smart].

Visa itself announced AI dispute products in 2026, among them one that drafts the merchant's reply and scores its chance of winning [visa-2026].

A free practice setting for chargebacks exists, with a scripted issuer; its cases are made up [chargebackops].

One real Australian set has reached researchers. A payments company gave academics about a hundred and twenty-six thousand [novatti-study] charged-back transactions with customer details, card identifiers and network addresses removed; the fraud rate was 0.31% [novatti-study].

## What would have to be stripped

Almost everything. A pack is personal information from end to end: name, addresses, email, phone, device details, purchase history, support chat and sometimes photographs of identity documents.

## What stands in the way

- Both schemes' rules bar a merchant from selling or disclosing transaction data.
- Visa, Stripe and the dispute companies already train on the record at a scale no outsider can match.
- A stripped pack loses most of what made it useful.
- The result is noisy and the task short, and a free made-up alternative exists.
- No lab has been shown to buy this kind of record.

> **A model's judgement, not a reading:** weak, and dead for buying packs from merchants. Both card schemes' rules bar merchants from selling or disclosing transaction data, the schemes and several funded companies already train on the record, and the only lawful version is a rebuild without identities that competes with a free made-up one.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
