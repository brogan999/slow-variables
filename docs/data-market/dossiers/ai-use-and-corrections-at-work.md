# Records of people using AI at work, and correcting it

## The record

Three related records sit under this heading. The first is a company's own staff using an AI assistant: what they asked, what the AI answered, and what they changed before using the answer. The second is the usage log of a company that sells a product built on someone else's model, such as a legal or coding assistant. The third is a programmer's session with a coding agent. The full log of one session, from instruction to outcome, is called a trace.

An illustration, not a real file: an accounts clerk at a distributor copies a supplier's statement into the firm's AI assistant and wants it reconciled to the ledger. Back comes a table: ten lines matched, three it cannot explain. The clerk sees that two of the three are one credit note entered twice, says so, gets a corrected table, changes one figure by hand and posts the entry. The record is the request, the first answer, the objection, the second answer, the hand edit and the posted entry. What matters most sits in the middle of that chain: the AI's error, and the fix a capable person applied.

## Why it might matter for training AI

A lab cannot simply use its own business customers' logs, because its contracts forbid it. Anthropic's commercial terms bar it from training models on what customers put through its services [anthropic-terms]. Microsoft says prompts and responses in its Copilot product are not used to train foundation models [ms-copilot]. Business use is therefore traffic the labs carry but may not learn from. Only the customer can release it.

One buyer asks for it in terms. micro1, which buys company records, says it wants people's feedback on what AI produced in real workplaces [micro1-partners].

There is a counter-argument. Most logged use is the model getting something right, which teaches little. The useful slice is failures and corrections, and nobody has measured how large that slice is.

Coding-agent sessions are offered for sale. No priced sale of any company's AI conversation logs turned up.

## Who holds it and who may share it

For business AI tools, the customer owns and the tool-maker processes. Anthropic's terms say the customer keeps all rights to what it puts in and owns what comes out [anthropic-terms]. Cursor, a coding tool, says that with its privacy mode on it will not train on customer data, and that with it off it may [cursor-privacy]. JetBrains collects detailed code data from companies only when they opt in, and says it will not sell or share it [jetbrains-faq]. OpenAI's wording was not read in full, so its position is not established here.

There is a catch. Anthropic's terms also say a customer may not use the service to build a competing product, including to train competing AI models [anthropic-terms]. That clause concerns what the service produced. The human side of a log, meaning the requests, objections and hand edits, is the customer's own work. Whether selling logs for testing rather than training falls outside the clause was not established.

Companies that sell AI products hold their users' sessions under their own customer contracts. Most that sell to businesses promise not to train on customer data, which also stops them selling it.

In Australia, the privacy regulator's guidance on commercial AI products says that where a new use of personal information is outside what people would reasonably expect, an organisation should seek consent or offer a real chance to opt out [oaic-ai]. How the Privacy Act's exemption for employee records applies was read only in commentary and is not established here. Nobody in Australia was found selling, brokering or buying such logs.

## Who is already there

Magma, a Y Combinator company, connects to an AI product's database, packages its traces and corrections, and says it licenses them to labs for a share of the revenue [magma]. Cookiy Labs sells real coding-agent sessions, corrections included, with secrets removed on the developer's own machine [cookiy]. SourceX lists human feedback and scored work licensed for evaluation [sourcex].

JetBrains takes such data for its own models and pays in kind: free licences to selected companies willing to share edit history, prompts and AI responses [jetbrains-blog]. It is a buyer for itself, not a reseller.

What remains open is the everyday use of general-purpose assistants by staff at ordinary companies, corrections included. It is asked for but not yet shown sold.

## What would have to be stripped

Prompts contain whatever staff pasted in: customer records, contracts, health details. The account holder cannot give consent on behalf of other people whose words appear in a log. A class action in California, *In re Otter.AI Privacy Litigation*, is brought by meeting participants who say their conversations were recorded and used to train a transcription service without their agreement [otter-docket]. A separate complaint makes a similar claim against Granola [granola-complaint].

The AI's own output may also have to come out, if the buyer is a different lab from the one whose model wrote it.

## What stands in the way

- Labs and tool-makers already see the traffic.
- Most logs record the model succeeding. The correction slice may be small.
- The competing-model clause takes the AI's outputs out of any sale to a rival lab.
- Personal and client information runs through the prompts, and lawsuits over meeting recordings are live.
- Go-betweens are already in place.
- No priced sale has been shown.

> **A model's judgement, not a reading:** worth a small test as a side-line to the existing trade in company records; weak as a data business in its own right. One named buyer asks for precisely this in its adverts, and the customer is the only party able to release it. But no priced sale was found, others already stand in the middle, and the tool-makers' terms and privacy law remove a good part of every log.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
