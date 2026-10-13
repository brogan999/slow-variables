# Australian financial advice files and their compliance verdicts

## The record

In Australia, personal financial advice to an ordinary client must be given under a licence. The licence holder, called the licensee, carries the legal responsibility and must be able to show the advice served the client's interests. What proves it is the advice file. It contains the client's circumstances and goals, a measure of their appetite for risk, notes, product research, and a long document, the Statement of Advice, giving the recommendation and the reasons. A technician called a paraplanner usually builds that document from the adviser's brief.

Two kinds of verdict are attached to these files, and they come out differently.

**The check before release.** Before the document goes to the client, a compliance reviewer at the licensee tests it against a list of questions, then either clears it or returns it with a list of faults.

**The review after misconduct.** When wrongdoing is found, every affected file is reviewed again. The reviewer decides whether the advice was suitable and, if it was not, works out compensation.

An illustration, not a real file: a couple in their late fifties want to retire in five years. A paraplanner models moving both their retirement accounts to a new provider and drafts a sixty-page document. The reviewer fails it, because nothing compares the fees and insurance of the old accounts with the new. The comparison, once added, shows the couple would lose a large amount of life cover. The recommendation changes to keep one account, and the file passes.

The second verdict has real numbers. The corporate regulator's final count, to the end of 2022, shows six institutions paid or offered A$4.7 billion [asic-final]. Of that, about four point four billion Australian dollars went to more than one and a half million customers who were charged fees for no service, which is a billing check [asic-final]. The part that turned on a judgement about advice was far smaller: nearly twelve thousand customers shared about two hundred and seventy million Australian dollars [asic-final]. Westpac had 3,341 of them, NAB 3,034, AMP 2,844, ANZ 2,123 and CBA 626 [asic-final].

## Why it might matter for training AI

Vendors' pages show labs asking for finance work, for expert judgement with its reasoning, and for real work across several tools. A draft, the findings against it and the corrected draft make a trace of a decision.

Nothing found shows a purchase of advice-compliance files, Australian or otherwise. A reviewer's pass is also an opinion and not an outcome.

## Who holds it and who may share it

Adviser Ratings counted about fifteen thousand advisers at the start of 2026 [adviser-ratings]. No national count of advice documents was found.

**The licensee** is the file's owner and has to keep it. A regulator's instrument of 2024 sets the period at 7 years from the day of the advice, and that the duty continues even if the licensee stops being licensed [asic-records].

**Compliance software companies** hold the pairs of interest. Advice RegTech describes its product as a system of record for pre-release checks and audits [adviceregtech]. iComply2 sells AI review of advice documents and whole-file audits [icomply2].

**Review records.** The regulator's guide on remediation says licensees should document their approach, decisions, progress and outcomes for consumers, and that the regulator may ask to see those records [rg277]. The files mostly concern advice given years ago and are nearing the end of the retention period.

## Who is already there

- **Advice RegTech** took part in the regulator's 2019 trial, in which its software read advice documents and flagged fee errors, missing alternatives and mismatched risk profiles [asic-trial].
- **The market's stated norm.** A guide for advisers published in October 2026 tells practices to question each vendor about training on client data and to choose tools whose terms rule it out [whatcould].

No dataset, test or paper drawing on Australian advice files turned up, and no seller of files. Nobody licenses them, which here means they are locked and not that they were overlooked.

## What would have to be stripped

An advice file is a financial life story: names, birth dates, tax numbers, income, assets, debts, health disclosures made for insurance, and family and inheritance details. Blanking names is not enough in a long narrative about one household, where age, job, employer's fund, suburb and balances together point to the people. The privacy rules on reusing such information were not opened for this dossier.

## What stands in the way

- The files are dense personal histories, costly to anonymise, in a market that expects them never to be used for training.
- No buyer has been shown, and the rules are Australian.
- The verdict attached is a compliance opinion, not an outcome.
- The reviewed files are ageing out of the retention period and sit with banks that have no reason to release them.
- The software companies that hold the checks could build on them without anyone's help.

> **A model's judgement, not a reading:** weak overall. Files reviewed after misconduct are effectively dead: they sit with banks, concern old advice and are among the most personal records in finance. Draft, findings and corrected draft from the check before release are worth a test only through a compliance-software company with each licensee's agreement, or by having hired specialists write fresh cases. No buyer has been shown for either.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
