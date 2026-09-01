# EDA brief — Echo

Paste this whole file into your own AI chat as the first message, then say
"write the code cell for Figure 2". Do the second figure in
the same chat.

Keep this chat only for this assignment — the complete conversation has to be exported and
submitted, so do not mix it with anything unrelated.

Your two figures are below. They were chosen so that the eight figures together cover all six
required categories, use all six tables and include five real joins; please do not swap one for
a different question without telling the group, because the coverage check in the notebook will
fail.

### Figure 2 — Bivariate relationship or group comparison

- **Question:** Which product categories earn the most revenue, and does the ranking change between revenue and units sold?
- **Observation unit and denominator:** One order line. Denominator: all order items.
- **Tables and join keys:** `order_items` joined to `products` on `product_id`. Revenue is summed at **line** grain. Pass the join through `at_grain(joined, len(order_items), "order_items + products")`.
- **What this figure has to do:** **This figure carries the double-counting demonstration, which is a graded requirement.** Compute the category revenue two ways: correctly, by summing `line_revenue` at line grain; and wrongly, by joining up to `orders` and summing `order_total`. Print both totals side by side, show the ratio, and say in one line why the second is inflated — every order is counted once per item in its cart. Then plot only the correct one, with units sold as a second panel or a second axis so the ranking comparison is visible.

### Figure 6 — Delivery or operational performance

- **Question:** Do late deliveries attract lower ratings, and how large is the difference?
- **Observation unit and denominator:** One review. Denominator: all reviews — **not** the number of orders.
- **Tables and join keys:** `product_reviews` joined to `deliveries` on `order_id`. Pass it through `at_grain(joined, len(product_reviews), "reviews + deliveries")`.
- **What this figure has to do:** **The grain trap.** Reviews sit at order-item grain, so an order with three reviewed items contributes three rows, and only some orders carry a review at all. Print the row count before and after the join in the same cell, and state the denominator explicitly in the axis label. Compare mean rating for on-time against late deliveries, and show the count behind each group — a difference of 0.2 stars on thousands of rows means something different from the same difference on forty.


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

### `order_items` — 15,685 rows, one row per order_item_id

```
order_item_id (string) — 15,685 distinct, e.g. HITM0002731, HITM0002732
order_id (string) — 5,000 distinct, e.g. HORD000879, HORD000879
product_id (string) — 1,000 distinct, e.g. PRD0045, PRD0183
quantity (number) — values: 1, 2, 3
unit_price (number) — 998 distinct, e.g. 180.47, 1008.76
line_revenue (number) — 2,367 distinct, e.g. 180.47, 1008.76
```

### `product_reviews` — 7,000 rows, one row per review_id

```
review_id (string) — 7,000 distinct, e.g. HREV002000, HREV002727
order_id (string) — 3,993 distinct, e.g. HORD001451, HORD001981
order_item_id (string) — 7,000 distinct, e.g. HITM0004524, HITM0006194
product_id (string) — 1,000 distinct, e.g. PRD0108, PRD0173
customer_id (string) — 500 distinct, e.g. CUS00500, CUS00186
review_timestamp (datetime) — 6,051 distinct, e.g. 2018-05-23 10:20:00, 2018-06-16 17:27:00
language_code (string) — 13 distinct, e.g. en, en
rating (number) — values: 1, 2, 3, 4, 5
review_title (string) — 5,935 distinct, e.g. useful daily tracking, useful for forms and visits
review_body_clean (string) — 7,000 distinct, e.g. vela spark 207 has become part of my morning and evening routine because it records activity and sle
review_body_latin_analysis (string) — 7,000 distinct, e.g. vela spark 207 has become part of my morning and evening routine because it records activit
verified_purchase (boolean) — values: True
helpful_votes (number) — 90 distinct, e.g. 33, 61
review_length_chars (number) — 1,332 distinct, e.g. 982, 457
review_word_count (number) — 334 distinct, e.g. 161, 73
contains_non_latin_script (boolean) — values: False, True
extracted_order_reference (string) — 3,993 distinct, e.g. HORD001451, HORD001981
extracted_product_sku (string) — 1,000 distinct, e.g. SKU-VEL00108, SKU-CAN00173
delivery_experience (string) — values: delayed, on_time
value_experience (string) — values: good_value, poor_value
writing_style (string) — values: comparison, concise, detailed, narrative
```

### `products` — 1,000 rows, one row per product_id

```
product_id (string) — 1,000 distinct, e.g. PRD0001, PRD0002
product_name (string) — 1,000 distinct, e.g. Candle Bloom 100, Vela Halo 101
category (string) — 10 distinct, e.g. Laptop, Smartphone
brand (string) — values: Candle, Vela
unit_price (number) — 998 distinct, e.g. 2765.47, 455.28
unit_cost (number) — 998 distinct, e.g. 1681.81, 310.78
launch_year (number) — values: 2012, 2013, 2014, 2015, 2016, 2017
warranty_months (number) — values: 12, 24
weight_kg (number) — 725 distinct, e.g. 1.209, 0.28
product_sku (string) — 1,000 distinct, e.g. SKU-CAN00001, SKU-VEL00002
subcategory (string) — 10 distinct, e.g. Ultrabook, 5G Smartphone
model_family (string) — 18 distinct, e.g. Arc, Atlas
colour (string) — values: Black, Blue, Gold, Graphite, Green, Red, Silver, White
supplier_id (string) — 37 distinct, e.g. SUP001, SUP002
supplier_country (string) — values: Australia, China, Japan, Korea, Malaysia, Vietnam
launch_date (date) — 785 distinct, e.g. 2017-07-01, 2014-01-12
tax_category (string) — values: GST_STANDARD
package_type (string) — values: Box, Protective case, Recycled box
recyclable_packaging (boolean) — values: False, True
active_flag (boolean) — values: False, True
product_description_clean (string) — 450 distinct, e.g. ultrabook designed for portable document work and video meetings, in the arc family and suppli
```

## Your other pieces this week

You also own findings 1 and 2, ML questions 2 and 5, and the report's context section — plus assembling the EDA notebook and the report itself.
