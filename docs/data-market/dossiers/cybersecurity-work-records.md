# The working records of cybersecurity firms

## The record

Security service firms make four records. The first is alert triage. A security operations centre is the team that watches an organisation's alarms. When an alert arrives, an analyst runs a series of searches over the logs and then closes it as false, harmless or genuine. What is kept is the alert, the searches in order, the notes and the verdict. The second is the penetration-test report, from a paid and authorised attempt to break in: each weakness found, the proof, the client's fix and the result of the retest. The third is the incident timeline, an hour-by-hour account of what responders found and did during a breach. The fourth is a recording of a test call, in which a tester phones staff pretending to be the IT desk and tries to obtain a password.

An illustration, not a real file: in the small hours an alert fires because a finance employee appears to have signed in from two distant countries. The analyst first pulls that person's recent sign-ins and finds an unfamiliar device. A second search of the mailbox finds a new rule forwarding mail to an outside address. A third looks for the same source address across other users and finds two more. The analyst escalates. Next day the client's own team confirms a stolen password. The final label matters less than the three searches and the reason for each.

## Why it might matter for training AI

Labs pay for tests of what their models can do in security. Forbes reported in September 2025 that Irregular, which tests models for OpenAI and others, had raised US$80 million at a US$450 million valuation [forbes-irregular].

The labs' own conduct in 2026 says more. Under Project Glasswing, Anthropic gave selected organisations its strongest model with up to US$100 million in usage credits [anthropic-glasswing]. Its Cyber Verification Program covers operations-centre and incident-response work and states that data retention is required for enrolled organisations, and gives the reason as monitoring for cyber misuse; it does not say the retained data is used for training [anthropic-cvp]. OpenAI runs a comparable access programme for banks and security companies [govinfosecurity]. The labs are getting live security work to pass through their own models by giving access away. They were not found buying archives of past work.

One finding runs in the record's favour. Alert-Bench, an academic test published in October 2026, replayed 1,247 alerts through a working log system and found that every AI approach it tried missed at least 40.4% of the alerts tied to an attack, mostly because it did not fetch the right evidence [alert-bench]. The analyst's sequence of searches is the missing skill.

No purchase by a lab or vendor of triage records, test reports, incident timelines or call recordings was found.

## Who holds it and who may share it

The client owns its logs and the report it paid for. The service firm owns, at most, its analysts' methods and notes, subject to the client contract. No such contract was opened, so that split is not established in detail.

The profession has a rule. CREST accredits many testing firms, and its code of conduct covers penetration testing, incident response and operations centres. It requires members to keep confidential the data and research from earlier assignments and not to use them in other assignments, and not to disclose client information to any third party without the client's specific approval [crest-code]. Reuse without the client's consent is therefore barred outright.

In Australia the two largest providers now belong to overseas groups. CyberCX, with about 1,400 staff, announced in August 2025 that Accenture had agreed to buy it [cybercx]. Tesserent was bought by Thales in 2023 [thales-tesserent]. Sekuro, an independent, says it has more than 800 clients [sekuro]. No Australian provider was found selling its records or saying it trains on them.

## Who is already there

The large security companies use their own data. CrowdStrike says its triage assistant was trained on millions of real decisions from its managed service [crowdstrike-pr]. Microsoft has given away a public dataset of 1.6 million alerts and 1 million incidents with customers' triage labels from 6.1k organisations [guide-paper]. It holds labels, not the searches behind them.

Specialists such as Irregular sell tests and practice environments to labs, not found records. Penetration-test reports that clients chose to publish are free to read, one project extracts their findings for model training [redblue], and made-up reports are published for the same purpose [synthetic-pentest]. One company sells a test run entirely by AI, so the report is becoming a machine's output [turbopentest].

Nobody was found selling real analysts' search sequences. Their holders are not free to sell, and those able to use them produce their own.

## What would have to be stripped

Logs carry usernames, network addresses, email subjects and sometimes passwords and keys. A report on a weakness that has not been fixed is a weapon in the wrong hands. Breach reports are often commissioned through lawyers and may be legally protected; the Australian law on that point, and on recording phone calls, was not opened and is not established here. The person on a recorded test call did not agree to any resale.

## What stands in the way

- The client owns the record, and the profession's code forbids reuse without the client's approval.
- Through their access programmes the labs already see live security work, and they retain it.
- The large security companies sit on millions of labelled decisions, and one of them has released a large set free.
- Funded specialists already hold the relationships with the labs.
- Security data goes stale quickly.
- The largest Australian holders are owned offshore.

> **A model's judgement, not a reading:** weak. There is real, funded demand for security skill in AI, and specialist testers, the big security companies' own data and the labs' free model access already meet it. Clients own the records that exist, and the profession's code rules out reuse. All that is left is a small test, built by experts on staged attacks.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
> *Anthropic is one of the companies this page describes, and it made the model that wrote the page. Read what it says about Anthropic with that in mind.*
