# Public inquiry exhibits and planning examination libraries

## The record

Two public stocks of real internal documents, each with an official conclusion attached.

The first is inquiry exhibits. A royal commission is a public inquiry with the power to compel documents. The documents it relied on are published as exhibits: emails, papers that went to boards, briefing notes and notes for file. A report with findings follows. Australia's inquiries into banking, the Robodebt welfare scheme, aged care and two casino operators each published exhibits this way.

The second is planning examination libraries. In England and Wales a very large project, such as a major road, wind farm or power station, is examined in public by an appointed panel. All of it is filed in a numbered library, from the application through the panel's rounds of written questions and the replies to them, down to the panel's recommendation and the decision the minister takes.

A worked example from one real library, for the Keadby Next Generation Power Station [keadby-library]. The application documents are numbered from APP-001 [keadby-library]. The panel's first written questions are document PD-008 [keadby-library]. The applicant and the objectors answer at the first deadline. The draft consent order, the legal instrument that would permit the project, is then revised at successive deadlines, from revision 3 through to a final revision 6 dated 16 June 2026 [keadby-library]. A test question could give an AI system the application together with that first round of questions, then ask which conditions the panel will insist on changing, and mark the answer against the tracked changes and the recommendation.

## Why it might matter for training AI

Data vendors' pages show labs asking for long office work on real documents and for tests that are hard to game. Both stocks offer real documents with an official outcome to mark against. What could be sold is a private set of test questions with marking guides, not the documents.

No purchase by a lab of a test built from inquiry or planning documents was found.

## Who holds it and who may share it

The host of the documents is not their owner. Each document belongs to whoever wrote it.

The Robodebt commission's site says its material is under a Creative Commons Attribution licence "with the exception of ... content supplied by third parties", and that where a third party holds copyright, "Their permission may be required to use the material" [robodebt-copyright]. Whether the exhibits fall inside or outside that licence is not stated there and was not established. In the banking inquiry the exhibits were written inside the banks; its copyright page could not be opened.

The Planning Inspectorate's terms say: "We do not authorise the use or republishing of third party documents without the permission of the original intellectual property holder" [pins-terms]. That covers everything written by applicants and objectors. The panel's own questions and reports are the government's.

So no single party is able to license either stock in full. The official side, which is the side that does the marking, can be reused with attribution. The exhibits and applications cannot be passed on without each author's permission.

On copyright more broadly, Australia's Attorney-General said in October 2025 that the government was "ruling out a Text and Data Mining Exception" [ag-2025]. How Australian or American copyright law would treat a commercial test set built from these documents was not established; the relevant statutes and cases were not opened.

## Who is already there

Nothing built on royal commission exhibits turned up: no dataset, no test, no product. The same goes for the planning libraries.

The Planning Inspectorate's guidance now asks parties to say when they have used AI to prepare a submission [pins-advice], which suggests consultants already use AI systems on these documents in private.

## What would have to be stripped

People are named in the exhibits, among them junior officials, bank employees and bank customers. The Robodebt and aged-care exhibits include vulnerable people. Objectors' names and addresses appear in planning submissions. Test questions would have to avoid turning on a named individual's conduct.

One design avoids most of the copyright problem: supply a pointer to each public document and a freshly written question, with the marking guide drawn from the official report, and let the buyer fetch the document itself.

## What stands in the way

- Nobody has been shown to buy a ready-made test of this kind from an unknown seller.
- The famous outcomes are public. An AI system may recall what a commissioner found without reasoning from the documents. Whether public web crawls hold these documents was not established here; a single crawl would prove little, since labs gather the web themselves.
- Only decisions made after an AI system was trained are clean. Planning decisions keep arriving: for one offshore wind project the recommendation was dated 14 May 2026 and the order was made on 8 June 2026 [dogger-bank-south].
- A pointer file with marking guides is something a lab could rebuild itself.
- Commission findings are judgements about conduct, which are harder to mark without argument than a planning panel's document-by-document changes.
- A commercial product built on the files of people harmed by a government scheme would be badly received.

> **A model's judgement, not a reading:** weak. Reading the documents costs nothing and no one has yet packaged them, yet what could be sold is a list of pointers and marking guides that a lab could reproduce, and the well-known outcomes are already public. A rolling set built on planning decisions not yet made is the one form that others could not easily copy.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
