# IT operations work that either held or did not

## The record

Four records sit on this page. Each is a piece of technical work followed by a plain result, and each gets its own verdict.

**Help-desk tickets with the recorded fix.** A managed service provider looks after small businesses' computers. When a user reports a fault, a technician takes remote control of the machine, fixes it and writes a note. The result is whether the ticket reopened in the following days. If recording was on, a video of the screen exists too.

**Mainframe changes against the overnight run.** A bank alters a program written in COBOL, an old business language. The package for the change contains the code before and after, with the test evidence. The result is whether the overnight batch finished or stopped with an error code.

**Factory controller edits against downtime.** An engineer changes the logic in the small industrial computer that runs a machine, and change-management software keeps every version. The result, lost production before and after, sits in a separate system.

**Outage timelines.** Alerts, charts, chat, commands and the written review of a software outage, in order, wrong turns included.

An illustration, not a real file: at nine in the morning a user reports that the email program will not open. A technician connects ten minutes later, tries a repair that fails, finds a damaged add-in, removes it, checks with the user and closes the ticket by half past nine. It does not reopen in the next two weeks.

## Why it might matter for training AI

Vendors' pages show labs asking for long tasks with recovery from failure, and for checks that need no human opinion. All four records have that form.

The help-desk record has something the others lack: a lab has moved towards its holders. In December 2025 OpenAI became a part-owner of Thrive Holdings. A trade publication reported that the deal gives OpenAI access to 7 service providers bought by a Thrive company, and quoted an Omdia analyst saying OpenAI would be able to train on their IT services data [channeldive]. That is a lab buying into the holders. It is not a purchase of a dataset, and no sale of tickets with sessions was found.

## Who holds it and who may share it

**Help-desk sessions** have three layers. The ticket text and the technician's note are the provider's. What appears on the user's screen is the client's: ConnectWise's master agreement says the client alone owns client data [connectwise], and NinjaOne's data-processing agreement says customer data stays the customer's property [ninjaone-dpa]. The third layer is the maker of the remote-access tool. NinjaOne's agreement of June 2026 says it may use aggregated or anonymised data to develop and train its products and its AI models [ninjaone-dpa]. An earlier version was read only in part, so when that wording arrived was not established. Whether session recording is usually switched on was not established.

**Mainframe changes** belong to the bank, insurer or government that runs the system.

**Controller histories** belong to the plant owner, with copies at the firms that built or fitted the machines. A reseller says one long-used product for storing these histories, AutoSave, reaches the end of its supported life in 2026 [becolve], so its users are moving their histories or leaving them behind.

## Who is already there

For help-desk work, OpenAI through Thrive, and the tool makers through their terms. No public test built from real help-desk sessions was found.

For mainframes, a software company, Factory, published a test of old-code tasks in 2026, built from constructed tasks and not real change packages. By its account COBOL accounts for 31 of the 44 tasks that defeated every model [legacy-bench].

For factory controllers, research projects only. Whether the firms that store customers' histories train on them was not confirmed either way.

For outages, the field is crowded with published tests, nearly all made by injecting faults into demonstration systems. A paper comparing them says injected faults are cleaner than real ones, which often have several causes at once [aiops-compare].

## What would have to be stripped

Help-desk recordings are the heaviest case: they show names, email, documents, the client's own customers and passwords as they are typed. Mainframe test files often contain real customer records, and outage logs contain secrets. Controller code holds no personal data. The Australian privacy and workplace-recording rules were not opened for this dossier.

## What stands in the way

- The client owns what is on the screen, and consent has to be gathered client by client.
- A lab-backed buyer of providers and the tool makers already sit upstream of every independent provider.
- Mainframe change packages cannot be reached from outside the firm doing the work.
- Controller histories carry no result of their own; downtime must be joined in, site by site.
- Tests of outage handling are plentiful, and the real evidence stays inside live companies.

> **A model's judgement, not a reading:** help-desk tickets with recorded fixes are worth a test, since they carry the only sign of lab interest here, though the client owns the screen content and stronger parties are already in position. Factory controller histories are worth a small test while an old archive product is being retired. Mainframe change packages are weak, because no outsider can reach them. Outage timelines are weak, because the test slot is full and the real evidence is locked away.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
