# The records of closing and failed companies in Australia

## The record

When a company stops trading it leaves behind its whole working history: email, chat, shared drives, the accounting ledger, the customer database, job and ticket systems, contracts and code. If the company is insolvent, the files go to a liquidator or an administrator: an accountant, registered for the purpose, who sells whatever remains and pays the creditors. If the company is solvent and is being closed on purpose, which is called a members' voluntary liquidation, its directors and shareholders remain on hand and can sign.

The numbers, as reported from the corporate regulator's statistics: in the 2025–26 financial year more than fourteen thousand companies went into external administration for the first time [accountants-daily]. Most are small. Of the administrators' reports lodged in 2022–23, 82% concerned companies with fewer than 20 employees, and 83% concerned companies with assets of A$100,000 or less [asic-23-346mr].

No Australian sale of such records was found. The model case is American. A transcription company called cielo24 closed after more than a decade [simpleclosure-blog]. Its shutdown agent, SimpleClosure, says it found a language-technology buyer for the company's data assets, which paid what it calls "mid-six figures" [simpleclosure-blog].

## Why it might matter for training AI

Data vendors' own pages show labs asking for the internal records of ordinary companies.

The trade exists in the United States at small size. SimpleClosure says more than 350 companies have listed with it, and forecasts that it will return more than US$10 million to them by the end of 2026 [simpleclosure-pr]. The one large price on record is a bid, not a sale: Google offered US$10 million for the records of the failed Spirit Airlines [spirit-auction-notice], and the court has not approved it. No purchase of Australian company records by a lab or a vendor was found.

## Who holds it and who may share it

The company owns its records. The liquidator's or administrator's firm holds them. Microsoft, Google, Xero and Slack only host them, and the accounts lapse when the bills stop.

The Corporations Act, section 477(2)(c), says a liquidator may "sell or otherwise dispose of, in any manner, all or any part of the property of the company" [corps-act-477]. Whether a mailbox or a shared drive counts as property under that section was not established. The regulator's guidance says whoever was the final external administrator has to hold on to the company's books for five years once the administration is over [asic-rg81], so the records usually survive long after anyone has reason to open them.

Privacy law is the harder part. The Privacy Act normally leaves small businesses alone, but section 6D removes that exemption from anyone who "discloses personal information about another individual to anyone else for a benefit, service or advantage", unless the person consented or a law authorises it [privacy-act-6d]. A law firm's note for liquidators, published in 2024, says a distressed company is "unlikely to hold the exceedingly broad consents that would be required", and that "it is unlikely the court would approve an order allowing for the explicit sale of personal information" [hwle-2024]. The court decision that note relies on was not itself read.

One Australian precedent points the other way, on narrower facts. When the retailer Dick Smith failed in 2016, its receivers told customers before the customer database went to another retailer and let them opt out [dick-smith-asx]. That was a customer list passing to a similar shop, not staff email passing to an AI lab.

## Who is already there

- SimpleClosure, in the United States, sells source code and "workspace data" for closing startups and does its own stripping of personal data [simpleclosure-assethub].
- The General Data Company, with a San Francisco address, offers the "document estates of wound-down European companies" under what it calls a "written administrator mandate" [general-data-insolvency].
- Tonic.ai sells the stripping of personal data as a service for this trade, and argues that whoever does it should be independent of the broker [tonic-usecase].
- An Irish law firm told insolvency practitioners in September 2026 that operational data "may warrant consideration" as an asset [william-fry].

The buyers look to America first. micro1's page asks for companies with "30+ employees" and says "We currently prioritize US companies, followed by other Western markets" [micro1-data-partnerships].

No Australian operator, professional guidance or law-firm note on sales for AI training was found.

## What would have to be stripped

Everything that identifies a person: staff, customers, suppliers' contacts. The 2024 note says "Any appropriately aggregated or de-identified information is outside the scope" of the privacy principles entirely [hwle-2024]. Whether the stripping step is itself a permitted use of the records was not established. Supplier and customer contracts carry their own confidentiality terms, and legal advice held in the files is privileged.

## What stands in the way

- No buyer has been shown to want Australian company records.
- Most failed companies are below the size buyers ask for.
- The published legal view is sceptical that personal information can be sold out of a liquidation, and a liquidator is personally exposed for a small sum.
- The Spirit Airlines hearing was moved to 6 November 2026, according to one press report [travel-weekly]. More than 120 members of Congress have asked that employee records be left out [technology-org]. Insolvency lawyers everywhere will read the outcome.

> **A model's judgement, not a reading:** worth a small test. The trade works in the United States for small companies and nobody was found doing it in Australia, but most Australian failures are smaller than buyers ask for and local legal commentary doubts that personal information can be sold from a liquidation.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
