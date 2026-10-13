# Australian pay calculations and their back-pay corrections

## The record

Australia sets minimum pay through legal instruments called modern awards, one for each industry or occupation. An award lays down job levels, ordinary hours, higher rates for nights, weekends and public holidays, overtime, and allowances. Award interpretation is the name for working out the correct pay for a given person on a given shift.

An employer that discovers past mistakes carries out a remediation, going back over old shifts for the staff affected and paying what is missing. The record is a pair: the amount payroll paid for a shift, and the amount the recalculation finds was due, with the reason they differ.

An illustration, not a real file: a casual shop worker is rostered on a Sunday from early afternoon into the late evening, with one unpaid break. Payroll paid eight hours at the ordinary casual rate. The recalculation applies the Sunday rate, a late-evening rule, and a penalty because the break came too late in the shift. The gap for that shift is about $40. The same working is then repeated for several hundred shifts and several thousand employees.

The totals are real. The workplace regulator, the Fair Work Ombudsman, says that in 2024–25 it got back A$358 million on behalf of more than 249,000 workers [fwo-2025]. Its register of binding undertakings by employers lists the University of Melbourne at A$72 million for more than 25,000 staff [fwo-register].

## Why it might matter for training AI

Vendors' pages show labs asking for practice tasks with checks that cannot be gamed, and for accounting work. A pay answer is right or wrong to the cent. Australian payroll advisers have written publicly that chatbots get penalty rates wrong with confidence [valont].

No lab or vendor was found buying pay-calculation data or tasks. The work is specific to one country; to a foreign lab it would stand in for applying a long rulebook exactly to untidy facts.

## Who holds it and who may share it

Both the payroll data and the recalculation belong to the employer. Three other groups hold copies or tools.

- **Remediation software firms.** PaidRight, of Melbourne, describes the job as gathering payroll data, applying a model of the award, and analysing the gap between paid and owed, with 80 to 120 data points in each calculation [paidright].
- **Accounting firms, law firms and payroll software companies** hold working papers and encoded rules.

Two things limit what an employer may pass on.

Privacy. The Australian privacy regulator's guidance says the exemption for employee records reaches only what an employer itself does in direct connection with the employment, and does not cover contractors handling the records of another organisation's staff [oaic-exemption]. Whether handing pay records to a data buyer falls outside the exemption was not tested in anything opened.

Legal privilege. A law firm's published guidance says employers commonly have lawyers lead the work so that the analysis is privileged, and that existing payroll records do not become privileged merely by being handed to a lawyer [pointon]. On that account the raw timesheets are not protected and the corrected model often is. No court decision on that exact point was found.

**The public side is unusually full.** The Fair Work Commission publishes a database of over 70,000 award pay rates, allowances and penalty rates, free to download and query [fwc-db]. The awards themselves are public. The regulator runs a free official pay calculator [fwo-calc].

## Who is already there

- **PaidRight** and **Yellow Canary** sell remediation and ongoing checking, built on their own encoded award logic.

No public test that takes an award and a roster and asks for the correct pay was found. Nor was any sale of remediation data.

What matters more is that the private records are unnecessary. A remediation is checked by software that encodes the rules, guided by a lawyer's view of what the award means. It is not a verdict from an opposing party. A competent payroll specialist with the published awards and rates can write pay tasks with exact answers.

## What would have to be stripped

Names, staff numbers, tax and bank details, dates of birth, and the names of small sites. Remediation reports raise privilege, and an employer that has given a public undertaking has little wish to see its pattern of errors circulate.

## What stands in the way

- No private data is needed, so nothing keeps others out. The public version can be built by anyone.
- No buyer has been identified, and the task is specific to Australia.
- The right answer is open to dispute at the edges, such as which award covers a job. Courts decide those, and they are the cases without a clean check.
- A model may reach exact pay by calling a rules engine as a tool, which leaves little for training to add.

> **A model's judgement, not a reading:** weak as a source of records, because the private files are both blocked by privilege and privacy and unnecessary, the awards, the rates and an official calculator being public. Worth a test only as a small build from public material, which would have no shown buyer.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
