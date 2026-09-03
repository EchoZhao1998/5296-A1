# Reply to Jasmine — Figures 3 and 4, 3 Sep

All numbers below come from the six standardised CSVs in `00_Master/outputs/`.

---

## Fig 3 — yes, change it. Coverage is unaffected.

The slot stays temporal and stays `orders`-only with no join, so the coverage cell needs no
edit and still reports 6/6 categories, 6/6 tables, 5 relational figures.

You were right to drop the outlier question, and there is a number that proves it. If orders
arrived at random, monthly counts would have a standard deviation of about **20.4** (the square
root of the 417 monthly mean). The observed standard deviation is **17.5** — *less* variable
than random. There is no outlier month to find, and no baseline would have shown one.

Your replacement question has a real answer. Decomposing the variance of log monthly revenue:

| Component | Share of variance |
|---|---|
| Order count | 0.46 |
| Average order value | 0.43 |
| Covariance between them | 0.11 |

`corr(log count, log AOV) = 0.13` — near zero, so the two move independently and neither
dominates. That is a genuine finding and not the obvious one.

**One caution, and it decides how you write the caption.** The whole series is narrow:
monthly revenue $1.10m–$1.36m (cv 6.1%), counts 384–443 (cv 4.2%), AOV $2,717–$3,148
(cv 4.0%). So the honest sentence is "revenue moves within a ±6% band and neither driver leads",
not "count explains 46% of revenue movement" — that would dress up noise as structure. Put the
Poisson band (417 ± 20) on the count panel and the reading becomes self-evident.

---

## Fig 4 — you are right that the join is decorative. Drop it. But the limitation is different.

**Three findings, in order of how much they change the figure.**

**1. There is no carrier or service-level effect to show.** On-time is 89.4% overall and every
one of the eight cells sits between 87.9% and 91.3%:

| Carrier | Express | n | Standard | n |
|---|---|---|---|---|
| AusPost | 90.0% | 239 | 89.7% | 1,083 |
| DHL | 87.9% | 214 | 89.6% | 1,028 |
| Direct Freight | 91.3% | 208 | 88.8% | 972 |
| StarTrack | 89.6% | 240 | 89.5% | 1,016 |

The standard error on a Standard cell is about 1 percentage point, so that whole spread is
noise. This is a null result. Under the specification a well-evidenced null is high quality —
but it has to be *presented* as one, with confidence intervals drawn, not as a ranking.

**2. Your confound is testable inside `deliveries`, and it tests as absent.**
`deliveries.shipping_distance_km` is already in the table. Mean distance is 5.4 km for Express
and 5.3 km for Standard, and 5.2–5.4 km across all four carriers. Distance does not predict
lateness either: correlation with on-time is **−0.009**, and the on-time rate across distance
quartiles is 90.2% / 89.2% / 89.4% / 89.0%. So "Express mostly runs short routes" is not true
here. Don't write it as a limitation — draw it as a second panel and it becomes a negative
control, which is worth more than a confession.

**3. Adding `nearest_warehouse` would not rescue the join.** Carrier × service level × warehouse
gives 24 cells with a minimum of 36 and a median of 125, and warehouse has no effect of its own
either (Bakers 88.9%, Nickolson 89.4%, Thompson 90.0%). You would be splitting nothing into
smaller pieces.

**Also worth knowing:** `orders.expedited_delivery` is `deliveries.service_level` re-encoded —
901 True against 901 Express, 4,099 against 4,099, no exceptions. That is the third redundant
pair we have found, after `delivery_note_clean` and `delivery_experience`. It is becoming a
finding about the source system in its own right.

### What I'd do

Keep Figure 4 in `deliveries` alone, two panels:

- **(a)** on-time rate by carrier × service level with 95% confidence intervals — eight
  overlapping intervals against a 89.4% reference line;
- **(b)** mean shipping distance for the same eight cells — flat, which rules out the routing
  explanation before anyone raises it.

Still multivariate (carrier × service level × distance) and still operational, so the category
is safe, and the figure now says "we looked, and it is not there, including for the obvious
alternative reason".

### Coverage impact — checked, not assumed

With Figure 4 at `tables={'deliveries'}, joins=0`, the coverage cell reports **8 figures,
6/6 categories, 6/6 tables, 4 relational figures** and every assertion passes. `orders` is
still covered by Figures 1, 3 and 7, and 4 relational figures is double the required 2.
The one edit needed is that line in the `COVERAGE` dict — I have not made it; it is yours to
make when you commit the figure.
