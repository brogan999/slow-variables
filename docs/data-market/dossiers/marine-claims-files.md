# Marine claims files: general average and demurrage

Two different records share this page, and they come out differently.

## The record

**General average.** Under an old rule of the sea, if a ship and what it carries face a shared peril, and saving them costs money or means giving up some property, the cost is split among all those whose property came through, according to what each had at stake. A specialist called an average adjuster works out who pays what. The result, the adjustment, is a long document that sets out the facts, lists each expense, says which rule allows it, values the ship and each cargo, and divides the total.

A worked example from a real case. The container ship Yantian Express caught fire in January 2019. General average was declared [one-line-yantian]. Before any container was released, each cargo owner had to give a bond, and with it either a guarantee from an insurer or, for uninsured cargo, cash: 32.5% of the cargo's value towards salvage and a further 28% towards general average [yantian-notice]. That is 60.5% of the value [yantian-notice], held until the adjustment is finished. The final adjustment then says what each party owes and what is refunded.

**Demurrage.** When a ship is hired for a single cargo, the contract allows the charterer, the party hiring it, a fixed time to load and unload. Keep the ship beyond that and the charterer owes the owner a daily rate called demurrage. The file holds the contract, the ship's formal notice that it is ready, the port agent's timed log, each side's calculation, the letters between them and the figure finally settled.

An illustration, not a real file: the time allowed is 2 days and the rate is US$20,000 a day. The ship waits for a berth and it rains. The owner counts all the waiting and claims 3 days of demurrage, or US$60,000. The charterer says the notice was invalid and leaves out the rain, making it 2 days of demurrage, or US$40,000. They settle at US$50,000. The file holds both sums, the dispute between them and a single figure paid.

## Why it might matter for training AI

Both records turn a contract and a messy timeline into a number that the other side accepted or disputed. That fits what vendors' pages show labs asking for: long office work with a check that is hard to game.

Neither kind of marine claim was found being bought by a lab or a vendor.

## Who holds it and who may share it

**General average.** The adjusting firm keeps the file. The shipowner, the insurers and the salvors hold copies. The international maritime law body's guidelines say the surveyor acts for everyone with a stake, "any of whom are generally entitled to view all his exchanges of correspondence and reports" [cmi-guidelines]. So the adjustment circulates among the parties. No source showed that an adjuster may license it to outsiders, and no confidentiality rule was found in the text of the adjusters' association rules that was opened [aaa-rules].

No count of adjustments a year was found. As a sign of scale, a Lloyd's report counts 754 uses of its standard salvage contract in the ten years to 2013 [lloyds-lof].

**Demurrage.** Owner and charterer each keep a file of their own. In Australia the holders are the large shippers of iron ore, coal and grain. One Western Australian council puts demurrage at a single jetty at A$70 million a year [dcn-kwinana].

The contracts are private and commonly carry a confidentiality clause; the standard clause text was not read. One side could not share the whole file without the other.

## Who is already there

**Demurrage is taken.** Marcura, a claims-processing company, says it handles "20,000+ claims a year" [marcura-service]. It says its system was "trained on more than 700,000 documents" and tracks "which charter party clauses generate the most write-downs" [marcura-blog]. A second firm, Burmester & Vogel, says its engine is "validated against 18k+ real laytime calculations" [bv-laytime]. Two voyage-software companies, Veson and Voyager Portal, manage claims inside their products, from tracking through calculation to invoicing [veson] [voyager].

So settled outcomes are already collected and used. What does not exist is a public test or a set offered to labs.

**General average is untouched.** No dataset, test, paper or company applying AI to adjustments was found.

## What would have to be stripped

Little is personal: crew and surveyor names, signatures, agents' emails. The sensitive content is commercial: freight and demurrage rates, insurers' positions, the other party's documents.

Removing names is not enough. A fire on a known ship, or a queue at a known port on known dates, can be matched to shipping news and public ship-tracking data.

## What stands in the way

**Demurrage**

- The firms that process the claims already hold the outcomes. Whether their customer contracts would let them license the data was not established.
- No buyer has been shown, and shipping is on no list of what labs want.
- Each file has two sides, and disputes go to private arbitration.
- The arithmetic is done by fixed-rule software. What is left for an AI system is reading the contract and the log, which may be too easy to be worth buying; this was not tested.

**General average**

- The cases are few and take years to finish.
- A qualified adjuster would have to check every case, so the cost to build is close to the likely price.
- The adjuster's right to share a finished adjustment is untested.

> **A model's judgement, not a reading:** for demurrage, weak and close to dead for a newcomer, because vendors already collect the claims with their settled outcomes. For general average, worth testing, but only as a small, single set of test cases, since the record is rare and slow.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
