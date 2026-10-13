# Simulator sessions and harbour pilots' recordings

## The record

Two records sit on this page. Both come out weak, for different reasons.

**Simulator sessions.** A trainee flies an aircraft, steers a ship or works a mining machine in a simulator. Several times each second the simulator stores what the trainee did with the controls and how the vehicle responded. An instructor marks the session. The record is the inputs, the motion and the mark.

**Harbour pilots' recordings.** A marine pilot comes aboard to bring a ship to its berth, carrying a portable unit: a tablet fed by an accurate satellite receiver of its own and by the ship's identification transmitter. The screen gives the ship's position and heading, how fast it is turning and how fast each end is approaching the berth. The passage is stored for replay.

An illustration, not a real file, with one real figure. A bulk carrier takes on a pilot at the entrance to Port Phillip, where about 5,800 large commercial ships are piloted in a year [ga-pilots]. The unit begins recording when it is switched on, and for about two hours logs where the ship is and how it is turning. The result is the speed at the moment of touching and whether anything was struck.

What the pilot's recording leaves out decides the matter. When a ship struck a bridge in Baltimore, the US transport safety board's laboratory examined the log from the pilot's unit. It found the ship's identification messages and separate readings for heading and rate of turn [ntsb]. Orders to the helm, the engine and the tugs were absent, and so was voice. Those are on the ship's own black box. The pilot's unit records where the ship went, not what the pilot did.

## Why it might matter for training AI

Vendors' pages show labs asking for records of experts controlling machines with every action attached, such as game play with controller inputs and remote operation of robots. A graded simulator log has that form. A pilot's track without actions does not.

No lab or vendor was found asking for ship, aircraft or mining-machine operation, and no buyer was found for either record.

## Who holds it and who may share it

**Airline simulators.** CAE, a Canadian training company, sells a system that collects data from its simulators alongside instructors' electronic grades [cae]. The airlines own their crews' training records. A template agreement from the international pilots' federation says outside parties may seek flight data for safety purposes, that anonymised data can go to them if the pilots' association is told on each occasion, and that data which is only useful when tied to particular flights needs the association's agreement [ifalpa]. Sale to an AI company is not addressed in the template.

**Ship simulators.** The Australian Maritime College in Launceston has a full bridge simulator and tug simulators and trains pilots for several ports and resource companies [amc-sim]. The centre holds the logs. Who owns them depends on each training contract, and none was seen.

**Mining simulators.** Immersive Technologies of Perth says it works with more than 360 sites, and that it monitors how operators brake, change gear and manage speed [immersive].

**Pilots' recordings.** The firms and port corporations that provide pilots hold them. The Australasian pilots' institute's code of practice says recording should begin automatically, that recordings should be kept safe and archived, and that the policy belongs in the provider's safety system [ampi]. No statute on who owns the recordings was found.

**The ship's black box.** A circular of the International Maritime Organization, issued in 2002, says the shipowner owns the recorder and its information in all circumstances [imo].

## Who is already there

- **CAE** and **Immersive Technologies** each use their own sector's simulator data themselves.
- **OMC International** sells analysis of pilotage performance to ports and has published a position on the ethical use of such data, covering what pilots should be told about collection, access, retention and discipline [omc].
- **Researchers** at a Japanese university built a berthing planner by imitation learning based on ship-tracking (AIS) data, and verified it with data from one port [osaka].

No seller of pilots' tracks to AI companies turned up, and public tracking data supports the same research at lower precision.

## What would have to be stripped

A named pilot's or trainee's performance is personal information and belongs to their employment history. The pilots' bodies whose documents were read want such data used for learning and not for punishment. Simulator models are licensed from manufacturers, as Immersive says of its own [immersive], and such licences may limit use of the logs.

## What stands in the way

- No buyer: no lab or vendor is on record asking for this kind of operation.
- The pilot's unit records no actions. The actions are on the black box, which belongs to the shipowner.
- Each simulator sector has an incumbent using the data, under manufacturers' licences on the models.
- Pilots' bodies' stance on performance data.

> **A model's judgement, not a reading:** weak for both. A harbour pilot's unit records the ship's track and not the pilot's actions. Simulators do record actions, but every sector that runs them already has a company using the data, under union and manufacturer limits. No buyer has asked for either.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
