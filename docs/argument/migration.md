# The bottleneck doesn't sit still. It migrates.

Making an AI model takes electricity, buildings, chips, memory, data, skilled people and money, all at the same time. Whichever of them is hardest to get sets the pace for the rest and collects most of the profit, until the industry builds its way out of the shortage. Then the shortage turns up somewhere else. This essay sets out why that happens, where the shortage has sat so far, and how this site tries to tell where it sits now.

### Folio I · the rule

## When every part is needed, the scarcest one gets paid

A factory line runs at the speed of its slowest station. Eliyahu Goldratt, an Israeli physicist who became a management writer, built a theory on that observation in The Goal, a novel about a failing factory that he wrote with Jeff Cox in 1984. A system, he argued, does only as well as its constraint allows, the constraint being whatever most limits it. Speeding up anything else is wasted effort. His method also ends on a warning: relieve the constraint and another one will limit the system instead, so go back to the first step and look again. This essay calls that constraint the bottleneck: the one input that is hardest to get, which sets the pace for everything else.

Who gets paid is an older question. David Ricardo, an English economist, asked in 1817 why landlords grew rich when bread grew dear. Most people assumed that high rents made corn expensive. Ricardo argued that it ran the other way: "Corn is not high because a rent is paid, but a rent is paid because corn is high." Good land is limited, so when people want more corn the extra money ends up with whoever owns the good land, and the owner need do nothing to earn it. Economists still use his word, rent, for income that comes from owning something scarce, as opposed to income from effort. Ricardo was writing about farms. Read a little more widely, his point is that the payment goes to whatever cannot quickly be made more of.

Put the two together and you have a rule for an industry in which every part is needed at once. The bottleneck sets the pace, and the owner of the bottleneck collects the rent. The first essay on this site met the same idea from the other side, through David Teece, a business economist who studied why inventors so often watch someone else profit from their inventions: the money settles with whoever owns what the invention cannot do without. In AI the clearest case is NVIDIA, the largest designer of AI chips, which keeps [fact:nvda_margin] of its sales as gross profit, meaning what is left after the cost of making the chips. That is what a bottleneck looks like in a company's accounts.

A margin like that is also an invitation. Every buyer who pays it has a reason to find a way around it, every rival has a reason to build a substitute, and every supplier has a reason to expand. So the rent is temporary by construction. The interesting question is never only who holds the bottleneck today. It is where the shortage goes once this one is relieved.

### Folio II · the record

## It has already moved more than once, and never in single file

It started with people. In 2012 a neural network, a program loosely modelled on connected brain cells that learns from examples, won a well-known image-recognition contest far ahead of the runner-up. It was built at the University of Toronto by Alex Krizhevsky, Ilya Sutskever and their adviser Geoffrey Hinton, and it turned research in computer vision toward neural networks. What ran short was people who could build them. Yoshua Bengio, a leading researcher in the field, estimated at the time that only about fifty such experts existed in the world. Google bought Hinton's three-person company in 2013 and the AI company DeepMind in 2014, a deal that MIT Technology Review described as a purchase of people, not products.

Then computing power. In January 2020 researchers at OpenAI posted a paper called "Scaling Laws for Neural Language Models". It found that a language model improves smoothly and predictably as its size, its training text and the computing power spent on it are scaled up together. If more computing power reliably buys a better model, computing power is worth queuing for, and the queue duly formed. NVIDIA's sales to data centres more than tripled in the financial year that ended in January 2024. Notice where the shortage went next. TSMC, the Taiwanese firm that manufactures those chips, said in 2023 that making the chips themselves was no problem; what was very tight was its capacity for advanced packaging, the step that joins a processor to its memory. In May 2024 SK Hynix, the leading maker of the fast stacked memory that AI chips use, said its supply was sold out for that year and almost sold out for the next.

Text ran short at about the same time. In 2022 researchers at DeepMind found that large language models were "significantly undertrained", meaning they had been given too little text for their size. The same year researchers at Epoch AI estimated that the stock of high-quality language data would be exhausted "likely before 2026". When scraped text stops being enough, labs pay people to write better text. A 2022 paper from OpenAI trained a model on demonstrations and rankings from about forty hired contractors, and the people hired to judge the results preferred the answers of a small model trained that way to those of a model more than a hundred times its size. By the middle of 2023 Scale AI, a firm that sells such work, was advertising for trainers with expertise in law, finance and programming. In 2025 Meta took a minority stake in Scale AI, which its audited accounts carry at [fact:meta_scale_price]. Surge AI, a rival that has never raised outside money, was reported to have passed [fact:surge_revenue] in yearly revenue.

Running the models was expensive for a while and then stopped being. Epoch AI reported in March 2025 that the price of reaching a fixed level of performance had been falling by between nine and nine hundred times a year, depending on the task. OpenRouter, a marketplace that sends each request to whichever model suits it, started in early 2023; in August 2026 the payments company Stripe agreed to buy it. A router earns its keep while models differ widely in price and quality. The better it works, the faster they converge, and the less anyone needs a router.

Electricity came last and may stay longest. In July 2022 Dominion Energy, a utility in Virginia, began telling data-centre companies that power for some new sites in Loudoun County would be delayed for years. In 2024 the United States Department of Energy told Congress that waits of three years were commonly quoted for a large power transformer, where under a year had been normal before the pandemic. In April 2025 the International Energy Agency projected that the electricity used by data centres would more than double by 2030.

None of this happened in single file. Computing power and data were short at the same time, and power arrived while both still were. The chart shows the overlaps. Its spans are this site's reading of the events above, not a measurement, and each one has its reason and its source in the table beneath it.

[plate:strip]

### Folio III · the tell

## Watch what the labs buy

A new bottleneck tends to satisfy three conditions at once. It limits the labs' next step, not their last one; yesterday's constraint is today's commodity. It has not yet become an industry, so there is no standard product, no quoted price and no public data, which is exactly why it is hard to see from outside. And it shows up first in what the labs buy, because a lab knows what it is short of long before anyone publishes a number about it.

That last condition can be watched. This site keeps two tallies by hand from public announcements. The first counts disclosed purchases by labs from the firms that sell training inputs, scored by how firm the evidence is. It is no higher than a year ago. The second counts labs and large technology companies buying neighbouring companies outright: [fact:lab_deals_4q] such deals in the past four quarters, against [fact:lab_deals_year_ago] in the four before. Both tallies rise when coverage improves as well as when buying does, so neither is proof of anything on its own, and neither is used here to say that a named input has peaked.

The buying that is visible points at practice. In September 2025 TechCrunch reported that the leading labs were "demanding more" of what the industry calls reinforcement-learning environments: simulated software tasks in which a model's attempts are graded automatically and the grades are used to train it. It said, citing The Information, that Anthropic's leaders had discussed spending more than a billion dollars on them within a year. A public directory that this site reads lists [fact:rl_vendor_count] firms selling them. A growing list of sellers is supply responding, though. It shows that the business exists, not that the product is short.

### Folio IV · the reading

## Most of the chain cannot be scored from what this site reads today

The scorecard below splits the making of AI into twenty-three inputs, from minerals to money, and asks of each how hard it is to get. The answer is a tightness score from nought to a hundred, read in five words from slack to severe. Each score is built from a few gauges. A gauge takes one published figure, such as how fast the supply of chip packaging is growing, and converts it to points on a scale set by hand. Beside each score is a confidence, worked out from how much of the intended evidence has a reading, how fresh it is and how good its source is. An input with no usable data is not given a middling score. It is withheld, with the reason. Today [fact:inputs_scored] of the twenty-three can be scored.

Most of those scores rest on Epoch AI, a research nonprofit that publishes estimates of the chips, computing power and buildings behind AI. One of its datasets follows the largest AI data centres, most of them in the United States, and gives for each a timeline of how much power the site draws or is expected to draw. At the [fact:dc_sites] sites where Epoch gives both a built figure and a planned one, the plans add up to [fact:dc_gap] what stands today. That is the tightest reading on the card, with a caution attached: [fact:dc_sites_unbuilt] of those sites have nothing built at all yet, and without them the ratio is [fact:dc_gap_built]. Epoch publishes wide error margins for these estimates, so neither figure deserves its second decimal place. And a gap between plans and buildings is what a shortage of builders, equipment and grid connections would produce, but a fast and untroubled build-out would produce it too.

Where the record above and the gauges disagree, the gauges are usually measuring something else. The record says memory and chips are short; the card reads them as moderate, because its gauges read how fast supply is growing, and Epoch counts memory supply in dollars, so dearer memory looks the same as more memory. A shortage shows up first in prices and waiting times, and nobody publishes those. The score for electricity measures demand only: how fast the power drawn by all the AI chips sold so far is growing, which says nothing about how much power can be supplied, and so it is drawn hatched. Money is the one input that reads slack. The five largest builders of data centres have raised their spending on buildings and equipment by [fact:capex_growth] in a year.

[plate:scorecard]

### Folio V · the blind spots

## What nobody publishes is a list of where it may go next

Go back to the second condition. An input that has not yet become an industry has no quoted price and no public data. So the inputs this site cannot score because nobody publishes anything about them are, as a group, candidates for the next bottleneck. They include the work done on a model after its first training, the expert-written data and practice tasks that work consumes, and the testing that says whether any of it helped. This is a conjecture, and it is stated as one. An absence of data is sometimes only an absence.

The same caution applies to the inputs that are scored. Memory supply grew by [fact:hbm_supply_growth] in a year, in dollars, which could mean far more memory or the same memory at a higher price. The grid is invisible from its supply side: this site reads what AI chips would draw, and nothing about what power stations and transmission lines can deliver. In both cases the fix is a better series, not a stronger opinion.

### Folio VI · the predictions

## What binds now, what binds next, and what would prove each wrong

Three cautions belong with any list like the one below. Rent from a bottleneck is temporary by construction, so every entry on it expires. The revenue figures quoted for the firms that sell training data are gross: much of the money passes straight through to the people doing the work. And one risk sits under all of it. The largest builders are spending [fact:capex_to_revenue] as much on buildings and equipment as the AI revenue this site can measure. If that spending stopped, every input on this page would loosen at once, and the question of which was tightest would stop mattering for a while.

With that said, here is what this site expects, and what would show it to be wrong. Each entry is tested every night where a test exists. Where none does, the entry says what outcome would settle it.
