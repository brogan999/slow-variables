# Machine-shop job records and design change histories

## The record

Three records sit on this page, and they do not share a verdict.

**Programs against inspection.** A job shop cuts metal parts from drawings its customers supply. Each job leaves behind the drawing, the program that steers the cutting machine, a set-up sheet saying how the part was held and which tools were used, and an inspection report from a measuring machine that marks every dimension as inside or outside its allowed range. When a first part fails and the program is changed until a part passes, the file holds an attempt, a measured failure and a fix.

**Quote against actual.** Before taking the job the shop estimated its hours. Afterwards its job card shows the hours and the scrap that really resulted.

**Design changes against the failure behind them.** A manufacturer that owns a product keeps a formal log of each design change and the reason given. Tied to the fault report that prompted it, an entry reads as failure, diagnosis, change, and whether the change held.

An illustration, not a real file: a shop quotes forty aluminium housings at two hours of set-up and twenty minutes a part. The first finished part fails inspection because one bore is slightly too tight. The programmer alters the last cut and swaps a tool, and the next part passes. The job card closes at five hours of set-up, twenty-five minutes a part, and three parts scrapped.

## Why it might matter for training AI

Vendors' pages show labs asking for real work with a check that cannot be argued with, and for design and manufacturing records. A measuring machine's verdict on a part is that kind of check.

No sale of any of the three records to a lab or a data vendor was found. The company best placed to want them went the other way: CloudNC, which sells software that writes cutting programs, built its own factory to make its own data and says it does not train on what customers put in [mms].

## Who holds it and who may share it

The shop holds the first two records. Whether it may share them turns on its customers' purchase terms, and the published ones read alike.

- Mattel's terms say drawings, specifications, tooling and technical information that it supplies or pays for stay its property and may be used only to fill its orders [mattel].
- Textron's terms say the same of drawings and data. They add that anything the supplier devises while doing the work, or derives from the buyer's confidential information, becomes the buyer's [textron].

Under terms like these the cutting program may belong to the customer as well, since it is worked out from the drawing. No court decision on that point was found. What the shop plainly owns is its estimate, its hours and its scrap count, and those say little once the shape of the part is taken away.

The third record is different. The manufacturer owns its own designs and its own change log. Whether an insolvency administrator can sell such a log free of suppliers' confidentiality terms was not established.

CloudNC advertises a government-only cloud option for export-controlled customers [cloudnc], a sign that part data for defence work is treated as controlled. The export rules themselves were not opened for this dossier.

## Who is already there

- **CloudNC** trains on simulated parts and its own factory. Its support page says many firms are unwilling to see their parts teach another company's AI [cloudnc-support].
- **Privara** lists anonymised operating data from industrial equipment for sale to buyers that it says include frontier AI labs [privara]. These are machine readings, not programs with drawings, and no sale is shown.
- **DataNexx** lists inspection, quality and change-control systems among the sources it will broker, on commission, and says on the same page that owning data is not the same as having permission to license it [datanexx].
- **Petrarch** is reported to buy operating data out of bankruptcies, which is the nearest thing to the third record [petrarch].

Nobody was found selling design changes linked to the failures behind them.

## What would have to be stripped

There is little personal information: operators' names on job cards and inspectors' stamps. The sensitive content is the customer's design. Removing the drawing removes the difficulty and most of the worth.

## What stands in the way

- The drawing is the customer's, and on the usual purchase terms so may be the program made from it. The shop holds files it cannot license.
- Any file tied to defence work is likely to be controlled, and cannot be mixed in with the rest.
- For design change logs, supply is thin and brokers of bankrupt companies' data are already active.

> **A model's judgement, not a reading:** weak overall. Programs against inspection, and quotes against actual hours, are close to dead as something to acquire, because the shop that holds the files does not own the drawings they depend on and the leading company has publicly declined to use customers' part data. Design change histories from insolvent product companies are worth a small test.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
