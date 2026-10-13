# Process plants: operators' control changes and the control-room history of closed plants

## The record

A refinery, smelter, mill or power station is run from a control room. Each control loop has a target the operator types in (the setpoint), a sensor reading, an output such as a valve position, and a mode: manual, automatic, or handed to a more advanced controller. A database called a historian stores all of these every few seconds or minutes, for many thousands of measuring points, for decades. A laboratory system stores tests of product quality every few hours. The control system's event journal records who changed what, along with alarms. Shift logs hold the operator's reasons in plain words.

This page covers two forms of the record: the operator's changes set against later product quality, at any plant, and the whole control-room history of a plant that has closed.

An illustration, not a real file: in the small hours, an operator at an alumina refinery sees the temperature of the process liquid drifting. The operator takes the loop into manual and raises the steam target by a few percent. The reading follows over the next half hour and an alarm clears. The morning laboratory sample shows the product back within its limits. The shift log reads "feed change, raised steam".

One company that builds AI controllers publishes what it needs, which gives real numbers for the shape. It asks for every part of each main loop to be recorded, at one-minute [imubit-data] intervals, with at least 200 [imubit-data] laboratory samples, and says its models are usually trained on 2 to 5 [imubit-data] years of history.

## Why it might matter for training AI

Vendors' pages show labs asking for manufacturing records and for real work where the steps are visible, though most of those voices are middlemen. One marketplace's summary for buyers lists production telemetry among the data on offer [privara].

A plant's behaviour is particular to that plant. The history of a closed plant can teach general physics and operator habits, but nobody will run a controller on a demolished unit. That narrows the likely buyer to builders of general models.

No purchase of historian data by a lab was found, and no completed broker sale. Every process-AI company found trains inside a customer's contract on that customer's own data.

## Who holds it and who may share it

The plant's owner owns the data. The historian's maker licenses only the software. The most common historian's published terms describe the licence as personal and non-transferable [aveva-pi]. They require the maker's written consent before the software is moved or the licence assigned, and require use to end when a subscription expires [osisoft-licence]. They also say that sharing data through the software as part of a business model or commercial engagement needs a separate agreement with the maker [osisoft-usage]. Whether exporting to plain files for a data licence falls under that clause was not established.

The practical point is one of timing. The owner would have to export the data while its licence is live. That deadline comes before demolition.

Australian closures, as checked:

- An alumina refinery in Western Australia stopped production in 2024, and its owner announced permanent closure in 2025. The owner said demolition and clean-up would begin in 2026 and run for six [alcoa-2025] years. The plant's capacity was 2.2 million [alcoa-2025] tonnes a year. The owner is solvent.
- A coal power station in New South Wales was due to close in 2023, by its owner's announcement that January [agl-2023]; early demolition was under way in 2025 [hunternet].
- A Victorian oil refinery's decommissioning was completed in 2023 [liberty].
- A Victorian paper mill sometimes described as closed is still operating [opal].

Whether any of these owners archived its historian was not established.

## Who is already there

Brokers already list this record. One works on commission and names historians and plant control systems among what it takes from owners [datanexx]. One runs an anonymous marketplace that lists production telemetry and names frontier AI labs as buyers [privara]. A third, by a press account, sources operating data from distressed companies and bankruptcies [petrarch-article]. None shows a completed sale of historian data.

The process-AI companies train plant by plant. One describes a model built for each plant from that customer's own historian and laboratory data [imubit-fpm]. Another says data stays with the customer [intellisense].

Nobody was found working with closed Australian plants.

## What would have to be stripped

Operators' log-in names in the event journal and names in shift logs are ordinary employee information and would be removed or replaced. The commercial sensitivities are the confidentiality of whoever licensed the process design, customers' names in laboratory records, and the details of sister plants that still run the same process.

## What stands in the way

- No buyer for historian data has been shown anywhere.
- An owner with sister plants still running has a reason to refuse.
- The software licence may lapse, or the servers be scrapped, before anything is exported.
- Without the list that says what each measuring point physically is, and without the event journal, the archive is close to unusable.
- The historian maker's clause on commercial data sharing.

> **A model's judgement, not a reading:** worth a small test. At least one solvent owner is closing a plant on a known timetable, so the question can be put cheaply and soon; but no buyer for this record has been shown, and several brokers already list it.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
