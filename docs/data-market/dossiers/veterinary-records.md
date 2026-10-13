# Veterinary records, from first complaint to outcome

## The record

A veterinary clinic keeps a file on each animal. It records the reason for the visit, the vet's findings, which tests were ordered and what they showed, the diagnosis, the treatment, the charge, and what had happened by the next visit. The file lives in the clinic's practice software, the system that handles bookings, records and billing.

An illustration, not a real file: a cat of about ten is brought in because it is losing weight and drinking heavily. The vet writes up the history and the examination. Blood and urine go to a laboratory and the results return into the file. The diagnosis is early kidney disease. A special diet is prescribed, with a recheck in three months. At the recheck the weight and blood values are entered again. Some years later the file closes with the animal's death. That is one case followed from complaint to outcome, every step dated, and none of it subject to the laws that guard human medical records.

## Why it might matter for training AI

Vendors' pages show labs asking for real records of professional work with the outcome attached, and for healthcare material. A veterinary file is clinical reasoning with a result, without a human patient.

No lab was found asking for veterinary records. Sellers exist and quote prices. No purchase by a named AI lab was found.

## Who holds it and who may share it

**The clinic owns the file.** The veterinary board of Victoria says in its guideline on records that a medical record is the property of the practice or practitioner who made it and not of the animal's owner, and that the vet keeps the owner's personal information confidential [vic-board]. The same board expects records to move with a practice when it is sold [vic-board]. In New South Wales the code of conduct in the Veterinary Practice Regulation 2013 says a practitioner must keep confidential what is learned in practice, and that records are kept for at least 3 years [nsw-reg]; the copy read is the regulation as it stood in 2017. Other states' rules were not opened.

**Who holds files in Australia.** VetPartners says it has more than 270 clinics and hospitals across Australia and New Zealand [vetpartners]. A university group, VetCompass Australia, holds over 15 million records from 180 clinics for research, which a paper puts at 5% of the country's clinics [vet-paper].

**The software company in the middle.** IDEXX owns ezyVet, a practice system. Its terms say the clinic owns its data, and also that the clinic permits the company to use it to improve the software, to pool it, and to pass it to third parties with the clinic and its customers made unidentifiable [ezyvet-terms]. IDEXX's master terms give it a perpetual, royalty-free licence over diagnostic images that clinics submit [idexx-master]. Other software companies' terms were not opened.

## Who is already there

- **Sikka** connects to practice software and sells to AI developers now. It offers two things: anonymised records on a yearly licence, and hosted practice environments in which an AI agent works a clinic's system and is scored on what really happened, priced from $252,000 a year [sikka]. It says its coverage is the United States and Canada and that it is expanding into Australia [sikka].
- **Evident** pulls diagnoses, treatments and outcomes out of clinics' free-text notes and sells them to drug, research and pet-food companies, sharing revenue with the clinics [evident].
- **Sage Veterinary Imaging** licenses scans with specialists' reports to AI labs, including trial batches of 500 to 1,000 studies [sage].
- **A British university project** gives away 17,600 annotated records under an open licence [peteval].
- University groups have trained models on these archives; one American group says it is unable to share the almost two hundred and fifty thousand visits it coded by hand [vet-paper].

The record is not untouched. One seller already prices both the raw records and the practice environment, and has named Australia as its next market.

## What would have to be stripped

The owner's name, address, phone, email and payment details; the clinic's and staff members' names. Free-text notes carry all of these, and sometimes the owner's own health or family circumstances. The duties of confidence above bind each vet personally, so a careless sale could put the seller's right to practise at risk.

## What stands in the way

- No lab has been shown to want veterinary data.
- A seller far larger than any Australian holder is already in the market and is entering Australia.
- The main software company's terms let it pass on anonymised clinic data itself.
- Cleaning free-text notes is costly, and each vet carries a duty of confidence.

> **A model's judgement, not a reading:** weak. The record is rich and the clinic has the right to license it, but the idea that nobody has touched it is false, since several sellers and the main software company's own terms already cover it, and nobody in AI has been shown to buy veterinary records.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
