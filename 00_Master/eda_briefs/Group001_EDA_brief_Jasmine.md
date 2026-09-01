# EDA brief — Jasmine

Paste this whole file into your own AI chat as the first message, then say
"write the code cell for Figure 3". Do the second figure in
the same chat.

Keep this chat only for this assignment — the complete conversation has to be exported and
submitted, so do not mix it with anything unrelated.

Your two figures are below. They were chosen so that the eight figures together cover all six
required categories, use all six tables and include five real joins; please do not swap one for
a different question without telling the group, because the coverage check in the notebook will
fail.

### Figure 3 — Temporal pattern

- **Question:** How do order volume and revenue move through the year, and is any month an outlier?
- **Observation unit and denominator:** One order. Denominator: all orders, grouped by month.
- **Tables and join keys:** `orders` only — no join.
- **What this figure has to do:** Parse `order_timestamp` with `pd.to_datetime`, group by month, and plot volume and revenue together — two panels, or one axis each. Watch the ends: if the first or last month is partial, say so rather than letting it read as a fall in demand. A twelve-month series has no second cycle, so describe the shape, do not call it seasonality.

### Figure 4 — Multivariate or segmented relationship, and operational performance

- **Question:** Does the on-time rate differ by carrier and by service level, and do the two interact?
- **Observation unit and denominator:** One delivery. Denominator: all deliveries.
- **Tables and join keys:** `deliveries` joined to `orders` on `order_id` — strictly one-to-one, so `at_grain(joined, len(deliveries), "deliveries + orders")` must hold.
- **What this figure has to do:** Use `on_time_in_full` or `delay_days`. **Do not use `delivery_note_clean`** — it is the same partition as the outcome columns and adds nothing. Plot the on-time **rate** per carrier x service level, not the count, and print the number of deliveries behind each cell so a small carrier is not read as a trend. "Do they interact" means: does the gap between Express and Standard differ by carrier? Say so explicitly either way.


## The notebook you are writing for

`Group001_EDA.ipynb` is already set up and runs. Every cell below Section 0 can assume this
has already executed:

```python
GROUP_ID = 'Group001'
TABLES = ['orders', 'order_items', 'customers', 'deliveries', 'products', 'product_reviews']

# every table is loaded with keep_default_na=False, so EVERY COLUMN IS A STRING
T = {t: pd.read_csv(OUTPUT_DIR / f'{GROUP_ID}_{t}_standardised.csv', keep_default_na=False)
     for t in TABLES}
orders, order_items, customers = T['orders'], T['order_items'], T['customers']
deliveries, products, product_reviews = T['deliveries'], T['products'], T['product_reviews']

import matplotlib.pyplot as plt      # already imported and styled

def num(series):                     # already defined — cast a text column to numeric
    return pd.to_numeric(series, errors='coerce')

def at_grain(df, expected_rows, label):
    """Already defined. Asserts a join did not multiply rows, and prints that it did not."""
```

## House rules — these are what make four people's cells fit in one notebook

1. **Everything is a string.** The tables are read with `keep_default_na=False` so the literal
   three-character `NaN` sentinel stays visible. Wrap any numeric column in `num(...)` before
   arithmetic, and never call `.astype(float)` on a column that can hold `NaN` as text.
2. **Missing means the three characters `NaN`.** To count real values use `!= 'NaN'`, never
   `.isna()` — pandas sees no missing values in these frames.
3. **Every join goes through `at_grain(...)`.** State the row count you expect and let it fail
   if the join multiplied rows. This is a graded requirement, not a nicety.
4. **matplotlib only.** No seaborn, no plotly, no styling libraries — the notebook must run
   from a fresh kernel with only pandas and matplotlib installed.
5. **One code cell per figure.** It must produce exactly one figure (a coordinated set of
   subplots answering one shared question counts as one), and end with `plt.show()`.
6. **Label everything**: title, both axis labels with units, a legend when there is more than
   one series, and thousands separators on large numbers. The figure is marked on whether it is
   readable at 100% zoom.
7. **Do not modify the shared frames.** Work on a copy (`df = orders.copy()`), never assign a
   new column back onto `orders`, `deliveries` and so on — three other people are reading them.
8. **No hard-coded totals.** Do not write `5000` or `15,685` in your code; compute counts from
   the frame. The whole notebook is marked on not hard-coding certified answers.

## What to hand back

Two things, nothing else:

**(a) one code cell** that runs top to bottom against the frames above, and

**(b) two sentences of prose** — one saying what the figure shows with a number in it, one
naming a material limitation. These go into the markdown cell that is already in the notebook
under the heading `**Interpretation and limitation:**`.

Ask your assistant to keep the code short and plain. If you cannot explain a line of it out
loud, ask for a simpler version — the group's rule is that nothing ships that we cannot explain.


## Facts about this data that will save you an hour

- `order_status` is `Completed` and `delivery_status` is `Delivered` on every row, and
  `verified_purchase` is `True` on every review. Three columns with zero variance — none can
  carry a visualisation.
- `order_timestamp` is entirely 2018. `delivered_date` runs into January 2019 for orders placed
  late in December, so a "2018 only" filter belongs on the order timestamp, never on the
  delivery date.
- `coupon_discount` is a **percentage** (0, 5, 10, 15, 20, 25), not a dollar amount.
- `coupon_code` and `promo_code` hold the sentinel on the same 3,127 orders — those orders used
  no promotion. Every other column is fully populated.
- `delivery_note_clean` has two values and is **exactly** the same split as `delay_reason ==
  'none'`, `on_time_in_full`, `delay_days == 0` and `delivered_date <= promised_date` — zero
  disagreements on all 5,000 rows. Use the outcome columns; the note adds nothing.
- 271 of the 7,000 reviews are in a non-Latin script. Plot rates, not counts, or the group
  disappears.
- Only 3,993 of the 5,000 orders carry a review, and reviews sit at **order-item** grain, so an
  order with three reviewed items contributes three rows.


## The columns you have (real names and values, do not guess)


### `deliveries` — 5,000 rows, one row per delivery_id

```
delivery_id (string) — 5,000 distinct, e.g. HDEL000879, HDEL000537
order_id (string) — 5,000 distinct, e.g. HORD000879, HORD000537
dispatch_date (date) — 368 distinct, e.g. 2019-01-01, 2018-08-26
promised_date (date) — 370 distinct, e.g. 2019-01-07, 2018-09-02
delivered_date (date) — 373 distinct, e.g. 2019-01-08, 2018-09-01
carrier (string) — values: AusPost, DHL, Direct Freight, StarTrack
service_level (string) — values: Express, Standard
delivery_status (string) — values: Delivered
delay_days (number) — values: 0, 1, 2, 3, 4, 5
on_time_in_full (boolean) — values: False, True
fulfilment_hours (number) — 72 distinct, e.g. 24, 67
delivery_cost (number) — 1,426 distinct, e.g. 19.13, 24.62
delay_reason (string) — values: carrier_capacity, none, warehouse_congestion, weather
promised_days (number) — values: 3, 4, 5, 6, 7
tracking_event_count (number) — values: 3, 4, 5, 6, 7, 8, 9
delivery_window (string) — values: Afternoon, Anytime, Morning
shipping_distance_km (number) — 497 distinct, e.g. 5.5105, 5.9347
signature_required (boolean) — values: False, True
estimated_carbon_kg (number) — 988 distinct, e.g. 0.421, 0.374
delivery_note_clean (string) — values: Carrier scan reconciled, Delivered within promise
```

### `orders` — 5,000 rows, one row per order_id

```
order_id (string) — 5,000 distinct, e.g. HORD000879, HORD000537
source_system_record_id (string) — 5,000 distinct, e.g. SRC-001-H-000879, SRC-001-H-000537
customer_id (string) — 500 distinct, e.g. CUS00481, CUS00242
order_timestamp (datetime) — 4,963 distinct, e.g. 2018-12-31 13:52:00, 2018-08-23 14:56:00
sales_channel (string) — values: Mobile, Store, Web
payment_method (string) — values: Bank Transfer, Card, Gift Card, PayPal
currency (string) — values: AUD
nearest_warehouse (string) — values: Bakers, Nickolson, Thompson
order_status (string) — values: Completed
order_price (number) — 4,925 distinct, e.g. 1189.23, 1554.14
delivery_charges (number) — 1,255 distinct, e.g. 21.86, 28.04
coupon_code (string) — 81 distinct, e.g. NaN, B1SAVE-66
coupon_discount (number) — values: 0.0, 10.0, 15.0, 20.0, 25.0, 5.0
tax_amount (number) — 4,738 distinct, e.g. 108.11, 141.29
order_total (number) — 4,981 distinct, e.g. 1092.17, 1193.64
season (string) — values: Autumn, Spring, Summer, Winter
expedited_delivery (boolean) — values: False, True
customer_lat (number) — 500 distinct, e.g. -37.853022, -37.871966
customer_long (number) — 500 distinct, e.g. 145.026366, 144.970039
device_type (string) — values: Desktop, Mobile, Tablet
referral_source (string) — values: Organic, Paid Search, Referral, Social, Store
customer_note_clean (string) — values: call before delivery, gift purchase for a family member, no special instruction, please leave at reception, ple
promo_code (string) — 81 distinct, e.g. NaN, B1SAVE-66
```

## Your other pieces this week

You also own findings 3 and 4, ML question 1, and the report's limitations and conclusion. For ML question 1 the important sentence is the leakage one: four columns record the outcome after the fact.
