# Planners' changes to a software forecast, and what happened next

## The record

Each line of this log carries three numbers, and now and then a typed note. The first number is the software's proposal, the second is the figure a person put in its place, and the third is the outcome. It turns up in three trades.

In demand planning, a program predicts how much of every product will sell in the coming month. A planner raises or lowers some of the forecasts, often typing a reason. Actual sales arrive weeks later.

In retail buying, quantities are ordered months in advance and prices are cut as the season goes on. The result is how much of the stock sold at each price.

In hotels, a pricing system suggests what to charge for a room on every coming night. The hotel's revenue manager takes the suggestion or changes it. Bookings follow.

An illustration, not a real file: the system forecasts sales of 10,000 cases of a drink for December. The planner raises it to 13,000 and types "retailer promotion, week 50". Actual sales are 10,000. The system was right and the planner was 3,000 cases too high. The trade calls this comparison "forecast value added": did the human step make the forecast better than the step before it?

## Why it might matter for training AI

The appeal is an expert decision with a hard check. Sales figures do not flatter anyone.

No lab or vendor was found buying records of this kind. Those found using them are consultancies and the makers of planning software, each working on one customer's data at a time.

## Who holds it and who may share it

The company whose planners made the changes owns the record. The software company processes it. What the published contracts say differs by vendor.

IDeaS, which sells hotel pricing software, says in its acceptable use policy that its reporting and extraction tools "must not be used to provide data to third parties without explicit approval from IDeaS" [ideas-aup]. Read plainly, a hotel could not send its history to a data buyer without that approval.

PROS, a pricing-software company, says in its subscription agreement that "Customer retains all right, title and interest in and to all Customer Data", and that it will use de-identified customer data for its own machine learning [pros-msa].

For several other large planning vendors no published customer terms were found. One point was not established anywhere: whether the stored system forecast, which is the vendor's output, counts as the customer's data.

## Who is already there

The bare record is already public and well studied.

A 2025 paper in the International Journal of Forecasting pooled "the publicly available data on around 147,000 forecasts from six studies" [ijf-2025]. It found that human adjustments improved the forecasts "for only just over half" of products, and that evidence of forecasters making good use of information the software lacked was weak [ijf-2025].

Two consultancies have trained on one client's log each. First Analytics says that on a test of 900,000 overrides its machine and the planners were "virtually tied" [first-analytics]. EyeOn says the direction and size of a change predicted whether it helped, and that the written explanations "had only a limited impact on the model’s predictions" [eyeon].

For hotels, an economics paper studied about 6 million price observations from 9 hotels, holding the system's recommendation, the manager's price and the bookings [cesifo-10849]. It reports that about 85% of managers' price updates copy the recommendation exactly [cesifo-10849].

The software companies learn from customers' overrides inside their own products, as the PROS and SAP terms allow.

What does not exist in public is a large set from many companies with the surrounding context. Nobody has been shown to want one.

## What would have to be stripped

Little of it is personal: planners' user names and names typed into comment fields. Hotel booking records carry guest details, which would be left out.

The sensitive content is commercial. Suppliers' cost prices, promotion plans agreed with particular customers and retailers' trading terms are held alongside the forecasts, and are usually covered by confidentiality clauses with third parties. Pooling forward prices from competing hotels raises competition concerns; the hotel paper's authors chose hotels with no neighbouring client of the same system, which they say reduces "concerns about algorithmic collusion" [cesifo-10849].

## What stands in the way

- Nobody has been found buying planning records that come with outcomes.
- The signal is thin. The best pooled study finds the human change helps only about half the time, and one consultancy found the typed reason adds little.
- A public pool of the bare record already exists.
- By itself the log is a few numbers and a brief note. To be useful it would need what the planner could see when deciding: sales history, the promotion calendar, stock and customer emails. That is most of a company's records, not a log.
- Some vendor terms forbid passing the data on, and third parties' trading terms sit inside it.
- The software companies already do the learning inside their products and gain nothing by releasing the data.

> **A model's judgement, not a reading:** weak. The check is real and there is little personal data, but the record alone is thin, a public version exists, research suggests the human changes add little on average, and nobody was found buying it. It survives only as one part of a wider deal for a company's records.
> *Claude, a model made by Anthropic, judged this on 10 October 2026; a separate run of the same model reviewed it.*
