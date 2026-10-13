# The working records of biology laboratories

## The record

Bench science leaves a working record behind the published result. It has four layers. The first is the lab notebook, now usually electronic, in which a scientist writes what was planned, done and seen, together with the database that tracks samples and results. The second is the loop from a failed run to its fix: a robot script or a test goes wrong, the operator alters something, and the run is repeated. The third is the out-of-specification investigation: regulated manufacturers must formally investigate any result that falls outside the registered limit, recording the cause and retesting. The fourth is the dossier a drug company submits to a regulator, together with the study reports of companies that have stopped trading.

An illustration, not a real file: a contract manufacturer tests a batch of tablets. The strength test reads 94 against a permitted range of 95 to 105. The analyst and supervisor look for an obvious slip, such as a wrong dilution, and find none. Quality staff open a full investigation and suspect the reference sample the test is measured against has degraded. A second analyst retests with a fresh reference. Six retests all read about 100. The cause is recorded, the batch is released and a corrective step is logged. One case holds a stated problem, a chain of decisions and an outcome few would dispute.

## Why it might matter for training AI

Biology is among the best-documented areas of lab demand, though much of the evidence is of talks and grants, not purchases. A brokerage news summary said in December 2025 that OpenAI had approached the lab-equipment company Revvity about licensing data and that other labs had opened talks with early-stage biotechnology companies [thefly]. The OpenAI Foundation gave US$500,000 to the non-profit 1Day Sooner to buy failed biotech companies' regulatory files in bankruptcy [pivotnews], and US$40 million to a university for cancer-vaccine data [mit-tr]. Meta, Google DeepMind and Isomorphic Labs jointly put US$300 million into a programme that generates data, and get a year's head start on what it produces [strategic-signal].

The answer on buying is split. Measurement data and regulatory files have named money behind them. The failed-run-and-fix loop and the investigation trail appear only in buyers' adverts. And the labs' own published work points the other way: OpenAI and Ginkgo Bioworks ran 36,000 reaction conditions over six cycles, with the model writing its own notebook entries [ginkgo-pr]. They made the loop themselves.

## Who holds it and who may share it

Notebook software companies hold the data and their customers own it, but the companies have begun writing themselves rights. Benchling's enterprise agreement says the customer exclusively owns its data [benchling-msa], and its AI terms say it will not train models on that data without express permission [benchling-ai-service]. Its terms for free and academic users are different: a project switched to public view gives Benchling a permanent licence to distribute and sell that dataset, including for AI training [benchling-tos]. Dotmatics, which owns the notebook product LabArchives, says the customer keeps all rights in its data [dotmatics]. LabArchives keeps data readable for three years or more once a licence has ended [labarchives].

Contract labs and shared facilities hold other people's results. One Australian research institute's facility terms assign the intellectual property in the service to the customer on payment [cmri]. The national genomics facility throws samples away between one and three months after it delivers results, and keeps client records confidential [agrf]. What a facility can call its own is the log of quality checks and reruns, once clients' results are taken out.

When a biotech fails, the buyer of the drug usually takes the data with it. 1Day Sooner's fund therefore bids only for non-exclusive copies in American bankruptcies [ctd-commons]. In Australia, one listed biotech, Paradigm Biopharmaceuticals, entered voluntary administration in September 2026 [asx-paradigm]. How many Australian biotechs fail each year was not found, and the terms of Australian contract research firms and universities were not read.

## Who is already there

Fallow Labs, which calls itself an AI lab, advertises for lab notebooks, test results, failed experiments and regulatory files, including from companies winding down; who stands behind it was not established [fallow]. DataNexx brokers lab-system and deviation records and pays the owner only if a licence closes [datanexx]. 1Day Sooner's fund says a non-exclusive copy of a regulatory file is worth tens of thousands of dollars, by its own estimate [ctd-commons]. Harell Data, which raised US$15 million in 2026, hosts biotechs' datasets so that model-builders train on them in place [geekwire]. Eli Lilly gives biotechs the use of its models in exchange for data contributions made through federated learning, which keeps their proprietary data private [revvity-lilly].

Well-funded science companies such as Periodic Labs and Lila run their own automated laboratories and do not buy.

No Australian seller or broker was found. Nor was anyone selling the troubleshooting loop as a scored product.

## What would have to be stripped

Anything at the level of an individual patient; Fallow excludes such records from what it asks for [fallow]. Names of staff. Third parties' trade secrets, such as a customer's recipe inside a contract lab's files. DataNexx itself warns owners that research contracts, licences and grant terms can bar licensing even of data they hold [datanexx]. Work on dangerous pathogens or toxins may be unsellable.

## What stands in the way

- Labs and science start-ups generate the loop themselves, with clean rights.
- The buyer of a failed company's drug, or its lender, usually takes the data exclusively.
- Contract and licence terms block much of the rest.
- The notebook software company may sell the pooled data itself.
- One lab's troubleshooting may not transfer to another; nobody has shown that it improves a model.
- Observed prices for a dead company's science are small.

> **A model's judgement, not a reading:** worth a test, as a way of bringing failed and shelved Australian biotech programmes to buyers who already advertise for them, not as a new kind of record. Demand is the best documented of any field examined, but the prices seen for dead-company science are modest, nobody has been shown buying the troubleshooting form, and the best-funded players generate theirs in-house.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
