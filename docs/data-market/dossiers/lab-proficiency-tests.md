# Laboratory proficiency tests scored against the known answer

## The record

A proficiency test is an exam that laboratories sit by post. The scheme's operator sends an identical sample, image or written case to all the labs enrolled, and each reports what it finds. The operator, which knows the right answer in advance, scores the labs and tells each how it compared with the rest. The record is the item, its true answer, all the answers given and the scores.

Most rounds are measurements, such as the sugar level in a vial, where a machine gives the answer; those are of no use to a language or image model. The rest are interpretive: reading a blood film, diagnosing from a slide, answering a written case, comparing bullets. A trained person answers these, and they are the subject here.

A worked example from the Australian operator's own conference poster. In its 2025 chemical pathology case-study programme the operator sent out 3 written cases with 5 questions each to 94 enrolled participants [rcpaqap-poster]. They returned 470 answers [rcpaqap-poster], which is 94 people answering 5 questions. An expert committee held the target answers. Staff summarised the anonymous answers with a general AI assistant, the committee edited the result, and reports went out in 28 to 63 days where they had taken 80 to 163 [rcpaqap-poster]. One case therefore yields its text, the target answers, a professional answer from nearly every participant on each question, and the committee's commentary.

## Why it might matter for training AI

Vendors' pages show labs asking for private tests that no model has seen, refreshed often, with a human baseline. Each year's rounds are new, are not published, and arrive with many professionals' answers to every item.

This is a test set and not training material: an item has one answer and no working. No purchase of such a set by a lab or a vendor was found. The nearest thing found is something offered and not something sold: an animal-imaging company, Sage, advertises scoring a customer's model against a sealed set it never licenses for training [sage].

## Who holds it and who may share it

**Australia.** The medical schemes are run by RCPAQAP, a company belonging to the pathologists' Royal College. Its participation guidelines say its material may not be reproduced without written permission, and name a financial incentive to others as a ground on which permission may be refused [rcpaqap-guidelines]. The operator owns the items, the answers and the reports. A lab owns only its own answer.

**United States.** The College of American Pathologists is the main operator. Its terms treat non-public information about its products, data and customers as confidential [cap-terms].

**United Kingdom.** UK NEQAS is a group of schemes hosted in the health service. One of them says participant information is handled under the confidentiality terms of the international standard for such schemes [ukneqas]. Its full clause on reuse was not read.

**Outside medicine.** Proficiency Testing Australia says its reports are under copyright and need its written approval before going to third parties [pta].

## Who is already there

- **RCPAQAP** already applies a language model to participants' answers, under an enterprise arrangement that it says keeps the data out of AI training [rcpaqap-poster].
- **The College of American Pathologists** opened a space in 2025 where members try vendors' pathology AI on slide images [cap-studio].
- **Collaborative Testing Services**, an American operator of forensic schemes, publishes forensic summary reports on the open web, with each participant's answers under an anonymous code. In one DNA test with 35 participants, a mixture from several people split them: 11 included the suspect, 13 excluded him and 11 called it inconclusive [cts-dna]. A firearms test with 280 respondents produced about 20% false identifications on some items, and the examiners' association investigated [afte].

No company was found licensing an operator's interpretive rounds as an AI test. The idea is not new to the operators, who are building next to it themselves.

## What would have to be stripped

Most items hold no patient data, since samples are pooled or anonymised. The Australian operator's privacy policy mentions donor details kept with some tissue [rcpaqap-privacy]. Participant labs are already coded, but in a small round an instrument or method field could point to one lab. Tissue images were given for quality assurance and education; the UK scheme relies on that purpose [ukneqas], and commercial AI use is a different one. An item used to test a model could not safely be reused in a live round.

## What stands in the way

- Nobody has been shown to buy this kind of test, and pathology images and exam-style questions are available elsewhere.
- The Australian operator's own terms single out financial gain to others as a reason to refuse.
- The American operator is building AI evaluation itself, which sets the pattern that operators and not outsiders run it.

> **A model's judgement, not a reading:** worth a test, at the low end. The record is clean, renewed every year and comes with a real human baseline, but it is a test set with no shown buyer, and the Australian operator's own copyright terms name commercial third parties as a case for refusal.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
