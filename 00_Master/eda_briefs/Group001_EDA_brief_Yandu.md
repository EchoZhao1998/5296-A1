# EDA brief — Yandu

Paste this whole file into your own AI chat as the first message, then say
"write the code cell for Figure 1". Do the second figure in
the same chat.

Keep this chat only for this assignment — the complete conversation has to be exported and
submitted, so do not mix it with anything unrelated.

Your two figures are below. They were chosen so that the eight figures together cover all six
required categories, use all six tables and include five real joins; please do not swap one for
a different question without telling the group, because the coverage check in the notebook will
fail.

### Figure 1 — Univariate distribution or composition

- **Question:** How is order value distributed across the canonical orders, and is it skewed enough that a mean would mislead?
- **Observation unit and denominator:** One order. Denominator: all orders in the table.
- **Tables and join keys:** `orders` only — no join, so `at_grain` is not needed here.
- **What this figure has to do:** A histogram or ECDF of `order_total`, with **both** the median and the mean drawn as vertical lines and labelled. The point of the figure is the gap between them: if you only report a mean, a right-skewed distribution makes the typical order look bigger than it is. Say in the interpretation which one you would plan with and why.

### Figure 7 — Segmented relationship

- **Question:** Which customer segments spend the most, and is the difference explained by how often they order or by how much they spend per order?
- **Observation unit and denominator:** One customer. Denominator: all customers in the table.
- **Tables and join keys:** `customers` joined to an aggregate of `orders` on `customer_id`. **Aggregate first, then join** — joining first and aggregating after multiplies each customer by their order count. Pass the joined frame through `at_grain(joined, len(customers), "customers + order summary")`.
- **What this figure has to do:** Pick a segment column that actually has variation — look at the customer columns below and choose one (state, loyalty tier, signup cohort, whatever is there). Then split total spend into **orders per customer** and **average order value**, and show both. That split is what makes this a segmented relationship rather than a second revenue chart: two segments can have the same total for opposite reasons.


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


### `customers` — 500 rows, one row per customer_id

```
customer_id (string) — 500 distinct, e.g. CUS00001, CUS00002
signup_date (date) — 429 distinct, e.g. 2014-08-08, 2013-09-21
loyalty_tier (string) — values: Bronze, Gold, Platinum, Silver
customer_segment (string) — values: Mainstream, Premium, Small Business, Value
age_band (string) — values: 18-24, 25-34, 35-44, 45-54, 55+
preferred_channel (string) — values: Mobile, Store, Web
home_suburb (string) — 10 distinct, e.g. Footscray, Southbank
prior_12m_orders (number) — 22 distinct, e.g. 11, 10
lifetime_value_before_period (number) — 500 distinct, e.g. 7283.87, 6091.84
marketing_consent (boolean) — values: False, True
home_postcode (string) — 10 distinct, e.g. 3011, 3006
home_state (string) — values: VIC
home_country (string) — values: Australia
preferred_language (string) — 13 distinct, e.g. ja, ja
acquisition_source (string) — values: Organic, Paid Search, Referral, Social, Store
account_status (string) — values: Active, Dormant, Review
preferred_device (string) — values: Desktop, Mobile, Tablet
email_domain (string) — values: example.net, inbox.example, mail.test
household_size_band (string) — values: 1, 2, 3-4, 5+
contact_frequency_preference (string) — values: Essential only, Monthly, Quarterly, Weekly
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

You also own findings 5, 6, 9 and 10 and ML question 4, and the report's data-preparation assurance section. Findings 9 and 10 are already drafted in the notebook from the validation register — they need magnitudes and an alternative explanation added, not new analysis.
