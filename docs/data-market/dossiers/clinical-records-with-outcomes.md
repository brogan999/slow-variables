# Clinical records joined across scans, notes, tests and outcomes

## The record

A hospital keeps one patient's story in several separate systems. Scans sit in an imaging archive, doctors' notes in the electronic record, blood results in a laboratory system, tissue slides in a pathology store. What happened later, such as a death, is often held by a registry outside the hospital. The systems share little more than a patient number. A poster about one London hospital trust's data lists 10+ billion rows of clinical facts across isolated systems and 8+ million medical images without standardised linkage [onelondon].

A worked example from a published dataset. Researchers at Stanford found 155,950 cases of a lung-clot CT scan in their hospital's research store [inspect-paper]. They sampled 26,475 scans with their reports and kept the 24,474 that had a report with a summary section [inspect-paper]. After further cleaning, the set held 23,248 scans for 19,402 patients [inspect-paper]. Each scan is joined to the radiologist's summary and to the patient's coded record, which runs to 225,444,005 rows, of which 4,410 are death records [inspect-site]. To allow release, the authors say they removed all unstructured text, and the set is offered "for non-commercial use under a data use agreement" [inspect-paper].

## Why it might matter for training AI

A model shown a scan beside the notes and results, and told what later happened, can learn what no single system contains. Some buyers pay for this. A biotechnology company building a cancer model announced agreements with a drug company and Tempus, whose de-identified cancer data it will use, that "include $200 million in data licensing and model development fees" to Tempus [pathos]. A broker, Protege, says it supplied an unnamed model builder, under the heading "Millions of Verified Imaging Studies for Pre-Training in 30 Days" [protege-case]. In China, a Shandong hospital signed a deal to sell a liver-disease set of 1000余例 (a little over a thousand cases) for 3万元, which is thirty thousand yuan, to a firm building a diagnostic model, according to the university the hospital is attached to [shandong].

In the sources read, no frontier AI lab was named as a buyer of hospital records. The named buyers are drug companies and medical-AI firms. One published benchmark for health models, HealthBench, draws on doctors' time: its responses are graded against "rubrics created by 262 physicians" [healthbench].

## Who holds it and who may share it

The hospital or clinic holds the record. What it may do with it differs by country.

**United States.** The health privacy rule says a hospital or its contractor "may not sell protected health information" unless the patient authorises it [hipaa-sale]. One route the rule gives for treating information as non-identifying is removing a list of identifiers [hipaa-deid]. The list includes "Biometric identifiers, including finger and voice prints" [hipaa-deid].

**Australia.** The privacy regulator examined I-MED, a radiology chain that passed "less than 30 million patient studies" to an AI joint venture without telling patients [oaic-report]. It found the data "had been de-identified sufficiently that it was no longer personal information", closed its preliminary inquiries, and added that its report "should not be taken as an endorsement" [oaic-report]. Its guidance for model developers says sensitive information "generally requires consent to be collected" [oaic-guidance]. The Privacy Act itself was not opened.

**Britain.** NHS England paused data processing for a model trained on the de-identified data of 57 million people after two doctors' bodies raised concerns; Politico reports that the family-doctor data involved had been approved for Covid research only [politico].

**China.** The personal information law lists 医疗健康 (medical and health) information as sensitive, and says that processing sensitive information needs 单独同意, separate consent [pipl]. A 2019 regulation says 禁止买卖人类遗传资源, that buying and selling human genetic resources is banned, and bars foreign organisations and individuals, and bodies they set up or control, from collecting or storing them in China or providing them abroad [hgr]. Whether ordinary scans and notes count as genetic resources was not established. A 2024 rule says a data handler must apply to the national internet regulator for a data-export security assessment if, in a year, it sends abroad the sensitive personal information of 1万人以上, ten thousand people or more; the rule also lists exemptions [cross-border].

## Who is already there

- **Epic Cosmos**, a pool of de-identified records from many health systems, has had a family of models pretrained on 118 million of its patients [epic-paper].
- **Truveta**, which is owned by American health systems, pools their records and says 192 million images can be linked to each patient's history [truveta-paper].
- **Brokers** include Protege, which lists notes, consultation audio and scans [protege-health], Gradient Health [gradient] and Segmed [segmed].
- **Yidu Tech**, which provides data platforms to Chinese hospitals, says it has processed nearly 9 billion authorised records [yidu-report]. A Shenzhen hospital is reported to have completed a trade of a health data product through the city's data exchange [shenzhen], and a vendor's catalogue lists hospital records it calls anonymised for training medical models [catalogue].
- **In Australia**, the I-MED scans went to Annalise.ai, then a joint venture between I-MED and Harrison.ai [oaic-report]. Heidi, a consultation-recording tool, says it "does not use consultation data, session transcriptions, or generated notes to train its AI model in any way" [heidi].
- **Free research sets** exist, such as a Boston hospital's 227,835 chest X-ray studies with reports [mimic-cxr].

The record is not untouched.

## What would have to be stripped

Names, dates, addresses, record numbers, text burned into images, voices, and people named in notes. I-MED hashed identifiers, shifted dates and redacted text near the edges of images, and the regulator still recorded a "very small number" of instances where personal information was shared in error [oaic-report].

Removing names does not settle it:

- A network told whether two chest X-rays came from the same person "with an AUC of 0.9940 and a classification accuracy of 95.55%", where an AUC of one would be perfect [xray-study].
- With every detected identifier masked, an attacking model "still reidentified 9% of clinical notes" [notes-study].
- The better of two GPT models asked to find identifiers in notes reached a recall of 0.8318, meaning it found about five in six [gpt-study].

Joining the scan to the notes and the outcome is what makes the record valuable, and it may also be what makes each patient easier to single out.

## What stands in the way

- The biggest pools already have models trained on them [epic-paper]. Whether their holders would sell the joined record is not shown.
- Prices do not only rise. One drug company "replaced two scheduled $42 million annual fees with three $14 million payments" for Tempus data [trove].
- Sharing that a regulator clears may still change what the holder does. Crikey reported that I-MED "has since quietly begun asking customers for consent" [crikey].
- The joining is engineering done inside each hospital. The London trust lists "High initial implementation costs" among its limits [onelondon].

> **A model's judgement, not a reading:** The demand is real but the supply is already owned. Paid deals exist, yet the buyers shown are drug companies and medical-AI firms, the sellers are the holders themselves or brokers, and the largest pools already have models trained on them. Stripping identity from scans and notes can be weaker than the law's lists of identifiers suggest, which may keep the joined record close to whoever already holds it.
> *Claude, a model made by Anthropic, judged this on 13 October 2026; a separate run of the same model reviewed it.*
