# %% [markdown]
# # FIT5196 Assessment 1 — EDA Notebook
# 
# **Group:** Group001
# **Members:** Echo Zhao · Congyi Wang · Yandu Wang · Siyuan Shao
# 
# This notebook reads the six standardised CSVs produced by `Group001_solution.ipynb` and
# nothing else. It does not re-run any cleaning: every value here is a value that was exported,
# validated and shipped. It is the reproducibility evidence for `Group001_EDA.pdf`.

# %% [markdown]
# ## 0. Configuration and data loading
# 
# Load the six standardised CSVs produced by the solution notebook. Keep paths
# relative/configurable and use explicit read options where the literal string
# `NaN` must remain visible.
# 

# %% [markdown]
# Two cells. The first mounts Google Drive and does nothing anywhere else, so the configuration
# cell below stays free of environment-specific code. The second finds the six CSVs from a short
# list of candidate folders — the first entry is the layout produced by unzipping the submission.
# 
# **This notebook needs only the six CSVs.** It never re-runs the cleaning pipeline, so nobody has
# to run the solution notebook to work here.

# %%
# Colab only. Does nothing elsewhere.
try:
    from google.colab import drive
    from pathlib import Path as _Path
    import os as _os

    drive.mount('/content/drive')
    _root = _Path('/content/drive/MyDrive')
    _found = sorted({p.parent for p in _root.rglob('Group001_orders_standardised.csv')})
    if len(_found) == 1:
        _os.chdir(_found[0])
        print('cwd:', _found[0])
    elif len(_found) > 1:
        # Never guess. Several copies of the six CSVs means someone re-ran the pipeline into
        # their own folder, and picking the first would silently analyse the wrong set.
        print('Several folders on this drive hold the six CSVs:')
        for _p in _found:
            print('   ', _p)
        raise SystemExit('Pick one: set OUTPUT_DIR by hand in the next cell, or leave only '
                         'the shared copy on the drive.')
    else:
        print('Six CSVs not found under MyDrive. Put them in a folder there, or upload them.')
except ImportError:
    pass   # not on Colab

# %%
# --- Section 0: configuration ---
from pathlib import Path

GROUP_ID = 'Group001'
CSV_NAME = f'{GROUP_ID}_orders_standardised.csv'

# The six CSVs, wherever they are. The first candidate is the layout produced by
# unzipping the submission; the rest cover the shared-drive folders.
OUTPUT_CANDIDATES = [Path('outputs'), Path('.'), Path('../outputs'),
                     Path('02_Outputs'), Path('../02_Outputs'),
                     Path('../00_Master/outputs')]
OUTPUT_DIR = next((p for p in OUTPUT_CANDIDATES if (p / CSV_NAME).exists()), None)
if OUTPUT_DIR is None:                       # last resort: search downwards from here
    hit = next(Path('.').rglob(CSV_NAME), None)
    OUTPUT_DIR = hit.parent if hit else None
assert OUTPUT_DIR is not None, (
    f'{CSV_NAME} not found. Put the six CSVs in an "outputs" folder beside this notebook. '
    f'Tried: {[str(p) for p in OUTPUT_CANDIDATES]}')
print('reading from', OUTPUT_DIR.resolve().name)

# Which copy of the six CSVs is this? Four people can each produce a set; a short fingerprint
# makes it visible at a glance that every figure in this notebook was built on the same one.
import hashlib
print()
for _p in sorted(OUTPUT_DIR.glob(f'{GROUP_ID}_*_standardised.csv')):
    _h = hashlib.sha256(_p.read_bytes()).hexdigest()[:12]
    print(f'   {_h}  {_p.name}')

# %%
# --- Section 0: load the six tables ---
import pandas as pd
import matplotlib.pyplot as plt

# TEMPORARY - export the eight figures for the report. Delete before submitting.
FIG_DIR = Path('figures'); FIG_DIR.mkdir(exist_ok=True)
_fig_n = 0
# Capture the REAL plt.show only once. Without this guard, re-running this cell
# makes _orig_show point at our own wrapper, so it calls itself forever.
if not getattr(plt.show, '_is_fig_saver', False):
    _orig_show = plt.show

def _save_then_show(*a, **k):
    global _fig_n
    _fig_n += 1
    plt.gcf().savefig(FIG_DIR / f'{GROUP_ID}_Figure{_fig_n}.png', dpi=200, bbox_inches='tight')
    _orig_show(*a, **k)

_save_then_show._is_fig_saver = True
plt.show = _save_then_show
pd.set_option('display.max_columns', 60)
pd.set_option('display.width', 200)
plt.rcParams.update({'figure.dpi': 110, 'figure.figsize': (7.5, 4.2),
                     'axes.grid': True, 'grid.alpha': 0.25, 'axes.spines.top': False,
                     'axes.spines.right': False, 'font.size': 10})

TABLES = ['orders', 'order_items', 'customers', 'deliveries', 'products', 'product_reviews']

# keep_default_na=False so the literal three-character 'NaN' sentinel stays visible as text
# rather than becoming a missing value, which would silently change every denominator.
T = {t: pd.read_csv(OUTPUT_DIR / f'{GROUP_ID}_{t}_standardised.csv', keep_default_na=False)
     for t in TABLES}

orders          = T['orders']
order_items     = T['order_items']
customers       = T['customers']
deliveries      = T['deliveries']
products        = T['products']
product_reviews = T['product_reviews']

for t in TABLES:
    print(f'{t:16s} {len(T[t]):>7,} rows x {T[t].shape[1]:>2} cols')

n_orders_with_review = T['product_reviews']['order_id'].nunique()
print(f'{n_orders_with_review:,} of {T["orders"].shape[0]:,} orders have at least one review')

# %% [markdown]
# ### 0.1 The grain of each table, and the join guard
# 
# Every metric in this notebook is calculated at its intended grain. The tables are one-to-many
# in three places, so a join made in the wrong order multiplies rows and inflates any sum taken
# afterwards:
# 
# | Table | One row per | Rows |
# |---|---|---|
# | `orders` | order | 5,000 |
# | `order_items` | item within an order (1–5 per order) | 15,685 |
# | `customers` | customer | 500 |
# | `deliveries` | order | 5,000 |
# | `products` | product | 1,000 |
# | `product_reviews` | reviewed order item | 7,000 |
# 
# `at_grain()` below is used on every join in this notebook. It states the row count expected
# after the join and fails if the join changed it, so an inflated revenue figure cannot survive
# to a chart. The cell also prints, for each table, whether its first column really is
# unique, so the grain in the table above is checked rather than assumed.

# %%
# --- Section 0.1: the guard every join in this notebook passes through ---

def at_grain(df, expected_rows, label):
    """Assert a join did not multiply rows, and say so in the output.

    A one-to-many join is not wrong in itself; summing a parent column after one is.
    Naming the expected row count at the join is what makes the difference visible.
    """
    assert len(df) == expected_rows, (
        f'{label}: {len(df):,} rows after the join, expected {expected_rows:,} — '
        f'the join multiplied rows, so any sum taken now is inflated')
    print(f'{label}: {len(df):,} rows, grain preserved')
    return df


# Numeric columns arrive as text because of keep_default_na=False. Cast where needed.
def num(series):
    return pd.to_numeric(series, errors='coerce')


for t in TABLES:
    key = T[t].columns[0]
    print(f'{t:16s} one row per {key:<16s} {T[t][key].is_unique}')

# %% [markdown]
# ## 1. Context and data-preparation assurance
# 
# Briefly define the business context and data scope. Summarise 3-5 material
# transformation decisions and 4-6 material validation results by citing stable
# `MAP-...` and `VAL-...` IDs. Do not repeat the complete mapping or notebook.
# 

# %% [markdown]
# **Business context and scope.** This EDA examines one year of Australian e-commerce activity
# standardised from the allocated JSON and XML inputs. The canonical data contains 5,000 orders,
# 15,685 order items, 500 customers, 5,000 deliveries, 1,000 products and 7,000 product reviews.
# Each exported table retains one row per published business key, so the figures can use an
# explicit order, order-item, customer, delivery, product or review grain.
# 
# **Material transformation decisions.** Four decisions govern the analytical data. First, source
# values are normalised before one row is retained per business key (`MAP-orders-01`); deduplicating
# before normalising would treat `25/12/2018` and `2018-12-25` as separate orders and keep both.
# Second, the monetary chain is rebuilt rather than copied: `line_revenue`, `order_price`,
# `order_total` and `tax_amount` are derived in sequence, the coupon is treated as percentage points
# before delivery charges, and included GST is divided out rather than added again
# (`MAP-order_items-06`, `MAP-orders-10`, `MAP-orders-13` to `MAP-orders-15`). Third, text is cleaned
# in a fixed order: review text is cleaned while preserving non-Latin characters
# (`MAP-product_reviews-10`), embedded identifiers are extracted before cleaning strips formatting
# wrappers (`MAP-product_reviews-17`, `MAP-product_reviews-18`), and Latin-only length metrics are
# calculated post-cleaning (`MAP-product_reviews-11`). Fourth, `delivery_note_clean` is deliberately
# not transformed (`MAP-deliveries-20`): it holds only two structured values, `Delivered within
# promise` (4,472 rows) and `Carrier scan reconciled` (528 rows), across all 5,000 canonical
# deliveries, so the narrative cleaner would alter text case on every row without adding analytical
# value.
# 
# **Validation assurance.** Six grouped results support those decisions. Grain and relationships
# hold: all six primary keys are unique with no blanks, each table's row count equals the number of
# different keys the two files hold between them, and all nine foreign keys return zero unmatched
# values (`VAL-PK`, `VAL-FLOW-01` to `VAL-FLOW-06`, `VAL-FK-01` to `VAL-FK-09`). First-wins
# deduplication loses nothing: it removes 68 rows from each allocated source (`VAL-FLOW-07`), and
# across 8,098 rows whose key appears more than once, normalised values have zero field
# disagreements, with repeated keys within a source also matching (`VAL-FLOW-09`, `VAL-FLOW-10`).
# The four monetary reconciliations find zero values outside the 0.01 tolerance across all 15,685
# order lines and 5,000 orders (`VAL-ARITH-01` to `VAL-ARITH-04`). Extraction ran before cleaning:
# all 7,000 review references were found with none left in the cleaned text, and there are zero
# order-reference or SKU mismatches (`VAL-TEXT-06`, `VAL-TEXT-14`, `VAL-TEXT-15`). The delivery note
# needed no cleaning: it holds two values across all 5,000 deliveries and neither carries noise
# (`VAL-TEXT-01b`). Finally, the literal `NaN` is a sentinel rather than a gap: `coupon_code` and
# `promo_code` contain it on the same 3,127 orders, no checked field mixes it with empty cells
# (`VAL-TEXT-11`), and the real word `none` in `delay_reason` survives on 4,472 rows instead of being
# read as missing (`VAL-TEXT-09`).

# %% [markdown]
# ## 2. Assessed EDA visualisations
# 
# Submit 6-8 clearly labelled assessed figures. Across the set, cover all six
# published categories, at least four tables and at least two valid relational
# analyses. For each figure state the question, observation unit, denominator,
# tables/join keys, interpretation and material limitation.
# 

# %% [markdown]
# ### Figure 1: Univariate distribution or composition
# **Owner:** Yandu Wang
# 
# **Question:** How is order value distributed across the canonical orders, and is it skewed enough that a mean would mislead?
# 
# **Observation unit and denominator:** One order. Denominator: all 5,000 canonical orders.
# 
# **Tables and join keys:** `orders` only — no join.
# 
# **How to build it:** A 60-bin histogram of order_total with the median and mean drawn as vertical lines and labelled, so the skew is visible rather than asserted. A histogram rather than a boxplot, because the point is the shape of the tail and where the mean falls inside it.
# 
# **Interpretation and limitation:** Order value is strongly right-skewed. The median order is AUD 2,502 but the mean is AUD 2,983 — 19% higher — and the mean sits above 59% of all 5,000 orders. Values run from AUD 22 to AUD 17,720, and the top 5% exceed AUD 7,135, nearly three times the median. For anything describing a typical order, plan with the median; the mean is the right summary only when the question is about totals, since mean x order count is revenue.
# 
# order_total is not basket size: it is net of the coupon discount and includes delivery_charges, so it mixes what the customer paid with a shipping component that does not scale with the goods. A question about typical basket size would want order_price instead, and the skew there may differ.

# %%
# --- Figure 1---
t = num(orders['order_total'])
mean, median = t.mean(), t.median()
below = (t < mean).mean() * 100

fig, ax = plt.subplots(figsize=(10, 5.5))
ax.hist(t, bins=60, color='tab:blue', edgecolor='white', linewidth=.4)
ax.axvline(median, color='tab:green', lw=2, label=f'median  {median:,.0f}')
ax.axvline(mean, color='tab:red', lw=2, ls='--', label=f'mean  {mean:,.0f}')

ax.set_xlabel('Order total (AUD)')
ax.set_ylabel('Number of orders')
ax.set_title('Figure 1 - Distribution of order value\n'
             f'{len(t):,} orders, one row per order; skew {t.skew():.2f}, '
             f'and the mean sits above {below:.0f}% of them')
ax.legend()
ax.grid(axis='y', alpha=.3)
plt.tight_layout()
plt.show()

print(t.describe(percentiles=[.05, .25, .5, .75, .95]).round(2).to_string())
print(f'mean is {(mean/median - 1)*100:.1f}% higher than median')

# %% [markdown]
# ### Figure 2: Bivariate relationship or group comparison
# **Owner:** Echo Zhao
# 
# **Question:** Which product categories earn the most revenue, and does the ranking change when the same categories are ranked by units sold?
# 
# **Observation unit and denominator:** One order line; all 15,685 canonical order lines. Units sold = sum(quantity) = 20,154 units.
# 
# **Tables and join keys:** `order_items` joined to `products` on `product_id`, many lines to one product. Revenue is summed at line grain.
# 
# **How to build it:** Two horizontal bar charts showing gross line revenue and units sold, using the same category order ranked by revenue.
# 
# **Interpretation and limitation:** Revenue and volume rankings differ substantially. Laptops generate the highest revenue ($2.75m) but rank 9th in units sold (1,397), while Accessories rank 1st in units (3,051) but last in revenue ($0.56m). This suggests category price differences strongly affect revenue. Do not sum `order_total` after the line-level join: this produces $52.7m instead of $14.9m because order totals are repeated across item lines. Revenue is also gross: the $1.62m order-level coupon discount cannot be reliably assigned to individual categories.

# %%
# --- Figure 2 ---

# Step 1: Add each product's category to the order-item table.
# many_to_one means many order lines may use one product, but each product ID
# must have only one matching row in the products table.
lines = order_items.merge(products[['product_id', 'category']],
                          on='product_id', validate='many_to_one')
# Check that the join did not add or remove any of the 15,685 order lines.
at_grain(lines, len(order_items), 'order_items + products')
lines[['quantity', 'line_revenue']] = lines[['quantity', 'line_revenue']].apply(num)

# Step 2: Show why order totals must not be summed after an item-level join.
# An order with several items appears several times after this join.
repeated = lines.merge(orders[['order_id', 'order_total']], on='order_id')
at_grain(repeated, len(lines), 'items + orders')
correct = num(orders['order_total']).sum()
wrong = num(repeated['order_total']).sum()
print(f'Correct order total: ${correct:,.2f}')
print(f'After item join:     ${wrong:,.2f} ({wrong / correct:.2f}x; orders repeat per item)')

# Step 3: Calculate the two category totals used in the figure.
# Revenue numerator = sum of line_revenue within each category.
# Units numerator = sum of quantity within each category. This includes repeat
# purchases and quantity > 1; it is not a distinct count.
cat = lines.groupby('category').agg(
    revenue=('line_revenue', 'sum'), units_sold=('quantity', 'sum'))
# Step 4: Rank each measure separately (1 means the largest category).
cat['revenue_rank'] = cat['revenue'].rank(method='min', ascending=False).astype(int)
cat['units_rank'] = cat['units_sold'].rank(method='min', ascending=False).astype(int)
print(f"Gross line revenue denominator: ${cat['revenue'].sum():,.2f}")
print(f"Units sold: {cat['units_sold'].sum():,} across "
      f"{lines['order_item_id'].nunique():,} distinct order lines "
      '(repeat purchases included)')
print(cat.sort_values('revenue', ascending=False)
      [['revenue', 'revenue_rank', 'units_sold', 'units_rank']].to_string())
# Step 5: Draw both measures in the same revenue-sorted category order.
# Keeping one order makes differences between the two rankings easy to see.
cat = cat.sort_values('revenue')
fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
cat.revenue.div(1e6).plot.barh(ax=axes[0], title='Gross line revenue', color='#4C72B0')
cat.units_sold.plot.barh(ax=axes[1], color='#C4622D',
                         title='Purchased units (same category order)')
axes[0].set(xlabel='AUD millions', ylabel='Product category')
axes[1].set(xlabel='Units sold = sum(quantity)', ylabel='')
fig.suptitle('Figure 2 - Category revenue rank versus unit-sales rank\n'
             f'{len(lines):,} order lines, one row per order line')
fig.tight_layout()
plt.show()

# %% [markdown]
# ### Figure 3: Temporal pattern
# **Owner:** Congyi Wang
# 
# **Question:** Does monthly revenue move because there are more orders, or because orders get bigger?
# 
# **Observation unit and denominator:** One order. Denominator: all 5,000 canonical orders, grouped by month.
# 
# **Tables and join keys:** `orders` only — no join.
# 
# **How to build it:** Group the 5,000 orders by month of `order_timestamp` and draw three stacked panels sharing one x-axis — total revenue, order count, and mean order value. The top panel is the product of the other two, so stacking them shows which component moves when revenue moves. All three panels start at zero, which is what makes the flatness of the series visible instead of magnifying it with a cropped axis.
# 
# **Interpretation and limitation:** Monthly revenue varies by only 6.1% across 2018 (coefficient of variation), and neither component drives it — order count varies 4.2% and mean order value 4.0%, so the two contribute roughly equally rather than one masking the other. Volume stays between 384 and 443 orders a month, and revenue between AUD 1.10m and 1.36m.
# 
# A single calendar year gives no second cycle, so the shape can be described but not called seasonal.
# 
# Month is taken from `order_timestamp`, never from a delivery date: 76 deliveries land in January 2019 against orders placed in late December 2018, so grouping on the delivery date would invent a thirteenth month that has no orders of its own.

# %%
# --- Figure 3 ---

from matplotlib.ticker import FuncFormatter

df = orders.copy()
df['ts']    = pd.to_datetime(df['order_timestamp'])
df['total'] = num(df['order_total'])
df['month'] = df['ts'].dt.to_period('M')

m = df.groupby('month').agg(revenue=('total', 'sum'),
                            orders=('order_id', 'size'),
                            mean_value=('total', 'mean'))
m.index = m.index.to_timestamp()

fig, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
panels = [('revenue',    'Revenue (AUD)',          'tab:blue'),
          ('orders',     'Orders placed',          'tab:green'),
          ('mean_value', 'Mean order total (AUD)', 'tab:orange')]

for a, (col, label, colour) in zip(ax, panels):
    a.plot(m.index, m[col], marker='o', color=colour)
    a.set_ylabel(label)
    a.set_ylim(bottom=0)
    a.grid(alpha=.3)
    a.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f'{v:,.0f}'))

ax[0].set_title('Figure 3 - Monthly revenue decomposed into order count and order size\n'
                f'{len(df):,} orders, one row per order, grouped by month of order_timestamp')
ax[-1].set_xlabel('Month of order_timestamp')

plt.tight_layout()
plt.show()

# Numbers for the interpretation sentence.
cols = ['revenue', 'orders', 'mean_value']
cv = m[cols].std() / m[cols].mean() * 100
print('variation across the 12 months (coefficient of variation, %)')
print(cv.round(1).to_string(), '\n')
print(f"first order {df['ts'].min():%Y-%m-%d}   last order {df['ts'].max():%Y-%m-%d}")
print(f"orders per month  min {m['orders'].min():,}  max {m['orders'].max():,}")

# %% [markdown]
# ### Figure 4: Multivariate or segmented relationship (also: operational)
# **Owner:** Congyi Wang
# 
# **Question:** Does the on-time rate differ by carrier, service level or dispatching warehouse, and do they interact?
# 
# **Observation unit and denominator:** One delivery. Denominator: all 5,000 deliveries.
# 
# **Tables and join keys:** `deliveries` joined to `orders` on `order_id`, one-to-one, verified by `at_grain()` — the join supplies `nearest_warehouse` and `delivery_charges`; `delivery_cost` and `shipping_distance_km` come from deliveries.
# 
# **How to build it:** The outcome is `on_time_in_full`; `delivery_note_clean` is the same partition and adds nothing. Dot-and-interval with a 95% Wilson interval per cell, and n printed beside each row. The cell also prints mean `promised_days`, `delivery_charges`, `delivery_cost` and `shipping_distance_km` by service level, and the range of cell sizes, because the interpretation below turns on all of them.
# 
# **Interpretation and limitation:** On-time performance is 89.4% across all 5,000 deliveries and barely moves. All 24 carrier x service x warehouse cells fall between 81.8% and 95.8%, and pooled across warehouses Express reaches 89.7% against Standard's 89.4% — 0.3 percentage points on 901 Express deliveries, well within one standard error. Express also buys no shorter promise: mean promised_days is 5.03 against 4.99. Nor does anything else observable follow the service level: mean shipping_distance_km is 5.4 on Express against 5.3 on Standard. What differs is money — mean delivery_charges is AUD 23.48 against AUD 12.17 and mean delivery_cost AUD 18.33 against AUD 9.55, so both are priced at about a 22% markup while Express costs 92% more to run for the same measured outcome. What makes up delivery_cost is not recorded, so the premium cannot be attributed further.
# 
# The apparent interaction is not evidence of one. The Express-minus-Standard gap swings from -10.0 to +7.0 points, but no Express cell holds more than 100 deliveries — they run 36 to 100 against 151 to 470 for Standard — so no cell in this design can resolve a gap of the size the chart appears to show. Express is 18% of deliveries, so this design cannot resolve an interaction that would matter operationally.

# %%
# --- Figure 4 ---
joined = deliveries.merge(
    orders[['order_id', 'nearest_warehouse', 'delivery_charges']], on='order_id')
at_grain(joined, len(deliveries), 'deliveries + orders')
joined['on_time'] = joined['on_time_in_full'].astype(str).str.lower() == 'true'

g = (joined.groupby(['nearest_warehouse', 'carrier', 'service_level'])['on_time']
           .agg(rate='mean', n='size').reset_index())
g['pct'] = g['rate'] * 100

# Wilson interval - stays inside 0-100 where the normal approximation does not.
z, p, n = 1.96, g['rate'], g['n']
centre = (p + z**2 / (2*n)) / (1 + z**2 / n)
half   = z * (p*(1-p)/n + z**2/(4*n**2)) ** .5 / (1 + z**2 / n)
g['lo'], g['hi'] = (centre - half) * 100, (centre + half) * 100

g['y']   = g.groupby(['nearest_warehouse', 'carrier']).ngroup()
g['y']  += g['service_level'].map({'Express': .18, 'Standard': -.18})

overall = joined['on_time'].mean() * 100
fig, ax = plt.subplots(figsize=(9, 7))

for lv, colour in [('Express', 'tab:blue'), ('Standard', 'tab:orange')]:
    s = g[g['service_level'] == lv]
    ax.errorbar(s['pct'], s['y'], xerr=[s['pct'] - s['lo'], s['hi'] - s['pct']],
                fmt='o', color=colour, capsize=3, label=lv)

for _, r in g.iterrows():
    ax.text(104, r['y'], f"n={int(r['n']):,}", va='center', fontsize=7, color='grey')

ax.axvline(overall, color='grey', ls='--', lw=1)
ax.text(overall + .3, g['y'].max() + .4, f'overall {overall:.1f}%', color='grey', fontsize=9)

labels = g.sort_values('y').drop_duplicates(['nearest_warehouse', 'carrier'])
ax.set_yticks(labels['y'].round())
ax.set_yticklabels(labels['nearest_warehouse'] + '  ·  ' + labels['carrier'])
ax.set_xlim(63, 112)
ax.set_xticks(range(65, 101, 5))
ax.set_xlabel('Delivered on time in full (% of deliveries), with 95% confidence interval')
ax.grid(axis='x', alpha=.3)
ax.legend(title='Service level', loc='upper left')
ax.set_title('Figure 4 - On-time rate by carrier, service level and dispatching warehouse\n'
             f'{len(joined):,} deliveries; intervals are 95% Wilson on each cell')
plt.tight_layout()
plt.show()

# Numbers for the interpretation sentence.
gap = g.pivot_table(index=['nearest_warehouse', 'carrier'], columns='service_level', values='pct')
gap['Express - Standard'] = gap['Express'] - gap['Standard']
print(gap.round(1).to_string())
print(f"\noverall {overall:.1f}% of {len(joined):,}")
print(joined.groupby('service_level')['on_time'].agg(['mean', 'size']).round(3).to_string())

# The interpretation rests on cell size and on Express buying no shorter promise,
# so both are printed rather than asserted.
for lv in ['Express', 'Standard']:
    n = g[g['service_level'] == lv]['n']
    print(f'{lv:9s} cells hold {n.min()} to {n.max()} deliveries')
print('\nmean promised_days by service level')
print(num(deliveries['promised_days']).groupby(deliveries['service_level'])
      .mean().round(2).to_string())

# Express is claimed to cost more; print the number instead of assuming it.
print(joined.groupby('service_level')['delivery_charges']
            .agg(['size', 'mean', 'median']).round(2).to_string())

for col in ['delivery_charges', 'delivery_cost']:
    joined[col] = num(joined[col])
joined['margin'] = joined['delivery_charges'] - joined['delivery_cost']

print('\nper delivery by service level: charged, cost, margin')
print(joined.groupby('service_level')[['delivery_charges', 'delivery_cost', 'margin']]
      .mean().round(2).to_string())
print('\nmean shipping_distance_km by service level')
print(num(joined['shipping_distance_km']).groupby(joined['service_level'])
      .agg(['mean', 'median']).round(1).to_string())

# %% [markdown]
# ### Figure 5: Review or text behaviour
# 
# **Owner:** Siyuan Shao
# 
# **Question:** Do rating, review length and script relate to one another — do longer reviews rate lower, and do non-Latin reviews differ?
# 
# **Observation unit and denominator:** One review. Denominator: all 7,000 canonical reviews.
# 
# **Tables and join keys:** `product_reviews` only — no join.
# 
# **How to build it:** One boxplot of `review_length_chars` per rating, drawn twice — once for each script group — so the two can be compared side by side. Group sizes are printed on the x-axis, and a log length scale is used because review lengths span 180–2,492 characters. The cell prints the median length per rating for each group, so the pattern in the boxes can be read as numbers.
# 
# **Interpretation and limitation:** The two script groups differ in length: the 271 reviews containing non-Latin script have a median cleaned length of 607 characters against 927 for the 6,729 Latin-only reviews. Length also moves with rating, but only in the larger group and only slightly — Latin-only medians fall from 980 characters at 2 stars to 907 at 5 stars, about 7% — while the non-Latin medians swing between 498 and 746 with no order at all, which is what 271 reviews split five ways looks like. Neither pattern is strong enough to treat review length as a proxy for satisfaction.
# 
# The non-Latin group is small and language-specific writing conventions may explain the length difference on their own, so this is descriptive and not causal. Length is also measured on the cleaned text, so it reflects the cleaning rules as well as what the customer wrote.
# 

# %%
# --- Figure 5  ---
f5 = product_reviews[
    ["review_id", "rating", "review_length_chars", "contains_non_latin_script"]
].copy()
f5["rating"] = num(f5["rating"])
f5["review_length_chars"] = num(f5["review_length_chars"])

script_values = f5["contains_non_latin_script"].astype(str).str.lower()
assert script_values.isin(["true", "false"]).all()
assert f5[["rating", "review_length_chars"]].notna().all().all()
f5["script_group"] = script_values.map(
    {"false": "Latin only", "true": "Contains non-Latin"}
)

summary5 = (
    f5.groupby("script_group", observed=True)["review_length_chars"]
    .agg(n="size", median_chars="median")
    .reset_index()
)
print(summary5.to_string(index=False))

# The question asks about rating as well as script, so print the rating axis too
# rather than leaving it to be read off the boxes.
by_rating = f5.pivot_table(index="rating", columns="script_group",
                           values="review_length_chars", aggfunc="median")
print("\nmedian cleaned length (characters) by rating")
print(by_rating.round(0).to_string())
print(f"\nlengths run {f5['review_length_chars'].min():,.0f} to "
      f"{f5['review_length_chars'].max():,.0f} characters")

ratings = sorted(f5["rating"].astype(int).unique())
fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)

for ax, group in zip(axes, ["Latin only", "Contains non-Latin"]):
    group_data = f5[f5["script_group"] == group]
    lengths = [
        group_data.loc[group_data["rating"] == rating, "review_length_chars"]
        for rating in ratings
    ]
    counts = [len(values) for values in lengths]
    ax.boxplot(lengths, showfliers=False)
    ax.set_xticks(range(1, len(ratings) + 1))
    ax.set_xticklabels(
        [f"{rating}\n(n={count:,})" for rating, count in zip(ratings, counts)]
    )
    ax.set_yscale("log")
    ax.set_title(f"{group} (n={len(group_data):,})")
    ax.set_xlabel("Rating (1–5 stars)")
    ax.set_ylabel("Cleaned review length (characters, log scale)")

fig.suptitle("Figure 5 - Review length by rating and script group\n"
             f"{len(f5):,} reviews, one row per review")
plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.show()


# %% [markdown]
# ### Figure 6: Delivery or operational performance
# 
# **Owner:** Echo Zhao
# 
# **Question:** Do late deliveries attract lower ratings?
# 
# **Observation unit and denominator:** One review; all 7,000 canonical reviews. This is item grain, not order grain.
# 
# **Tables and join keys:** `product_reviews` joined to `deliveries` on `order_id` (many-to-one). The join preserves all 7,000 reviews.
# 
# **How to build it:** Mean rating by delivery outcome, shown as dots with 95% confidence intervals. This displays both the small difference in ratings and the greater uncertainty for the smaller late-delivery group (707 vs 6,293 reviews).
# 
# **Interpretation and limitation:** Late deliveries average 3.82 stars versus 3.70 for on-time deliveries, a small +0.12-star difference in the opposite direction to the expected effect. The data therefore provides no evidence of a rating penalty for late delivery; it should not be interpreted as evidence that lateness improves ratings.
# 
# Only reviewed items are included, so the results represent reviewers rather than all customers. The late-delivery group is also much smaller. `delivery_experience` and `on_time_in_full` agree across all 7,000 reviews, so they do not provide independent measures of delivery performance.
# 

# %%
# --- Figure 6 ---
f6 = product_reviews[['order_id', 'rating']].merge(
    deliveries[['order_id', 'on_time_in_full']], on='order_id', how='left')
at_grain(f6, len(product_reviews), 'reviews + deliveries')
f6['rating'] = num(f6['rating'])
f6['delivery'] = f6['on_time_in_full'].astype(str).map({'True': 'On time', 'False': 'Late'})

# Mean, and the uncertainty around it, so a 707-review group is visibly less
# certain than a 6,293-review one.
g6 = f6.groupby('delivery')['rating'].agg(['mean', 'std', 'size']).loc[['On time', 'Late']]
g6['se'] = g6['std'] / g6['size'] ** .5
print(g6.round(3).to_string())

# The interpretation quotes this ratio, so the cell prints it rather than asserting it.
diff = g6.loc['Late', 'mean'] - g6.loc['On time', 'mean']
se_diff = (g6['se'] ** 2).sum() ** .5
print(f'\nLate minus On time: {diff:+.3f} stars = {diff / se_diff:.2f} standard errors')

# The review table carries its own lateness field. If it never disagrees with the
# delivery table, the review text is not an independent record of lateness.
chk = product_reviews[['order_id', 'delivery_experience']].merge(
    deliveries[['order_id', 'on_time_in_full']], on='order_id', how='left')
agree = (chk['delivery_experience'].eq('on_time')
         == chk['on_time_in_full'].astype(str).eq('True')).mean()
print(f"the reviews' own delivery_experience agrees with on_time_in_full on "
      f'{agree:.1%} of {len(chk):,} reviews')

fig, ax = plt.subplots(figsize=(7.5, 3.2))
y = range(len(g6))
ax.errorbar(g6['mean'], y, xerr=1.96 * g6['se'], fmt='o', color='tab:blue', capsize=4)
for i, r in enumerate(g6.itertuples()):
    ax.text(r.mean, i + .22, f'{r.mean:.2f}   n = {r.size:,}', ha='center', fontsize=9)
ax.set_yticks(list(y))
ax.set_yticklabels(g6.index)
ax.set_ylim(-.6, len(g6) - .3)
ax.set_xlim(3.5, 4.0)
ax.set_xlabel('Mean rating on the 1-5 star scale, with 95% confidence interval')
ax.set_title('Figure 6 - Mean rating by delivery outcome\n'
             f'{len(f6):,} reviews, one row per review; '
             'the gap is 0.12 stars and runs the wrong way')
ax.grid(axis='x', alpha=.3)
plt.tight_layout()
plt.show()


# %% [markdown]
# ### Figure 7: Segmented relationship
# 
# **Owner:** Yandu Wang
# 
# **Question:** Which customer segments spend the most, and is the difference explained by order count or by order size?
# 
# **Observation unit and denominator:** One customer. Denominator: all 500 customers.
# 
# **Tables and join keys:** `customers` joined to an aggregate of `orders` by `customer_id`. Aggregate first, then join — the other order multiplies customers by their order count. Verified with `at_grain(joined, len(customers), "customers + order summary")`; all 500 customers have at least one order, so the denominator is the full table.
# 
# **How to build it:** Aggregate `orders` to one row per customer, then join. Three horizontal-bar panels sharing one question — total spend, orders per customer, and average order value — so the left panel is the product of the other two and the reader can see which factor carries it. Splitting total spend this way is what makes this a segmented relationship rather than a second revenue chart.
# 
# **Interpretation and limitation:** Total spend does not separate the segments. The widest gap is Mainstream at AUD 31,360 against Small Business at AUD 28,897, which is 1.5 standard errors of the difference — indistinguishable on 110 to 139 customers per segment. The labels also do not rank as they read: Premium is third and Value second.
# 
# The components do differ, in opposite directions. Value customers order most often and spend least per order (10.4 orders, AUD 2,846); Small Business customers order least often and spend most per order (9.4 orders, AUD 3,062). Each gap is about 2.4 standard errors, and because they pull opposite ways the totals converge. Reading only the left panel would say these segments behave alike; they do not.
# 
# Two cautions. 2.4 standard errors is the largest of twelve comparisons across three measures, so the component gaps are suggestive rather than established. And `customer_segment` is a pre-existing label whose rule we do not have — `customers` also carries `prior_12m_orders` and `lifetime_value_before_period`, so if the segment was assigned from earlier behaviour, part of what this figure shows is the assignment rule rather than a finding about 2018.

# %%
# --- Figure 7 ---
SEG = 'customer_segment'

# Aggregate first, then join - joining first multiplies each customer by their order count.
per_customer = (orders.assign(total=num(orders['order_total']))
                      .groupby('customer_id')
                      .agg(orders_placed=('order_id', 'size'), spend=('total', 'sum')))

joined = customers[['customer_id', SEG]].merge(per_customer, on='customer_id', how='left')
at_grain(joined, len(customers), 'customers + order summary')
joined['avg_order'] = joined['spend'] / joined['orders_placed']

seg = (joined.groupby(SEG)
             .agg(customers=('customer_id', 'size'),
                  spend=('spend', 'mean'),
                  freq=('orders_placed', 'mean'),
                  size_=('avg_order', 'mean'))
             .sort_values('spend', ascending=False))

fig, ax = plt.subplots(1, 3, figsize=(13, 4.5))
panels = [('spend', 'Total spend per customer (AUD)'),
          ('freq',  'Orders per customer'),
          ('size_', 'Average order value (AUD)')]

for a, (col, label) in zip(ax, panels):
    a.barh(seg.index, seg[col], color='tab:blue')
    a.set_xlabel(label)
    a.grid(axis='x', alpha=.3)
    for y, v in enumerate(seg[col]):
        a.text(v, y, f' {v:,.0f}' if v > 20 else f' {v:.1f}', va='center', fontsize=9)

ax[0].set_ylabel('Customer segment')
ax[1].tick_params(labelleft=False)
ax[2].tick_params(labelleft=False)
fig.suptitle('Figure 7 - Spend per customer, split into how often they order\n'
             'and how much they spend each time; '
             f'{len(joined):,} customers over {len(orders):,} orders; bars are segment means')
plt.tight_layout()
plt.show()

print(seg.round(1).to_string())
for col, label in [('spend', 'spend per customer'), ('orders_placed', 'orders'),
                   ('avg_order', 'avg order')]:
    s = joined.groupby(SEG)[col].agg(['mean', 'std', 'size'])
    s['se'] = s['std'] / s['size'] ** .5
    print(f'\n{label}')
    print(s.round(1).to_string())

# %% [markdown]
# ### Figure 8: Multivariate relationship
# 
# **Owner:** Siyuan Shao
# 
# **Question:** Does unit price relate to rating and to helpful votes, or are highly rated products simply the cheap ones?
# 
# **Observation unit and denominator:** One reviewed order item. Denominator: all 7,000 reviews.
# 
# **Tables and join keys:** `product_reviews` joins to `order_items` on `order_item_id`, then to `products` on `product_id`. `at_grain()` checks that both joins preserve the review grain.
# 
# **How to build it:** Divide the reviewed items into five equal-frequency `unit_price` bins, print and label every bin size, and use two coordinated panels — mean rating with its 95% confidence interval, and median helpful votes with the middle half of each quintile drawn around it. Points with intervals rather than bars from zero, because the whole question is whether the differences between quintiles are larger than their own uncertainty.
# 
# **Interpretation and limitation:** Mean rating falls steadily across the first four price quintiles, from 3.879 to 3.548 — a 0.33-star drop, roughly seven standard errors, and clearly wider than the 95% intervals — then rebounds to 3.684 in the top quintile. The relationship is real but not monotonic, so it cannot be summarised as "dearer products rate worse". Median helpful votes stay between 44.0 and 45.5 across all five quintiles — a 1.5-vote spread against a middle-half range of roughly 21 to 68 votes inside every quintile, so that panel carries no signal at all.
# 
# Only reviewed purchases are observed — 7,000 of 15,685 order lines — so this describes reviewers, not buyers. Category mix moves with price, so the quintiles are partly a category comparison in disguise, and review age and exposure are unobserved. Nothing here establishes a causal price effect.

# %%
# --- Figure 8  ---
f8 = product_reviews[
    ["review_id", "order_item_id", "product_id", "rating", "helpful_votes"]
].rename(columns={"product_id": "review_product_id"}).copy()

item_prices = order_items[
    ["order_item_id", "product_id", "unit_price"]
].rename(columns={"unit_price": "item_unit_price"})
f8 = f8.merge(item_prices, on="order_item_id", how="left", validate="one_to_one")
at_grain(f8, len(product_reviews), "reviews + order items")
assert f8["review_product_id"].eq(f8["product_id"]).all()

catalogue_prices = products[["product_id", "unit_price"]].rename(
    columns={"unit_price": "catalogue_unit_price"}
)
f8 = f8.merge(catalogue_prices, on="product_id", how="left", validate="many_to_one")
at_grain(f8, len(product_reviews), "reviews + order items + products")

for column in ["item_unit_price", "catalogue_unit_price", "rating", "helpful_votes"]:
    f8[column] = num(f8[column])
price_cols = ["item_unit_price", "catalogue_unit_price", "rating", "helpful_votes"]
assert f8[price_cols].notna().all().all()
assert f8["item_unit_price"].sub(f8["catalogue_unit_price"]).abs().le(0.01).all()

f8["price_quintile"] = pd.qcut(f8["item_unit_price"], q=5)
summary8 = (
    f8.groupby("price_quintile", observed=True)
    .agg(
        n=("review_id", "size"),
        min_price=("item_unit_price", "min"),
        max_price=("item_unit_price", "max"),
        mean_rating=("rating", "mean"),
        sd_rating=("rating", "std"),
        q1_helpful=("helpful_votes", lambda s: s.quantile(.25)),
        median_helpful_votes=("helpful_votes", "median"),
        q3_helpful=("helpful_votes", lambda s: s.quantile(.75)),
    )
    .reset_index(drop=True)
)
# Standard error of each quintile mean, so the panel can show whether the
# differences between quintiles are larger than their own uncertainty.
summary8["se"] = summary8["sd_rating"] / summary8["n"] ** .5
print(summary8.round(3).to_string(index=False))

labels = [
    f"Q{i + 1}\n${row.min_price:,.0f}–${row.max_price:,.0f}\n(n={int(row.n):,})"
    for i, row in enumerate(summary8.itertuples(index=False))
]
x = range(len(summary8))
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].errorbar(x, summary8["mean_rating"], yerr=1.96 * summary8["se"],
                 fmt="o", color="#4C72B0", capsize=4)
axes[0].set_title("Mean rating, with 95% confidence interval")
axes[0].set_ylabel("Mean rating on the 1-5 star scale")

# The median moves by 1.5 votes between quintiles. Drawing the middle half of each
# quintile as a bar shows that spread against a within-quintile range of about 45,
# which is what stops a 1.5-vote wobble from being read as a trend.
axes[1].errorbar(x, summary8["median_helpful_votes"],
                 yerr=[summary8["median_helpful_votes"] - summary8["q1_helpful"],
                       summary8["q3_helpful"] - summary8["median_helpful_votes"]],
                 fmt="o", color="#C4622D", capsize=4)
axes[1].set_ylim(0, 90)
axes[1].set_title("Median helpful votes, with the middle half of each quintile")
axes[1].set_ylabel("Helpful votes per review")

for ax in axes:
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_xlabel("Order-item unit-price quintile (AUD)")
    ax.grid(axis="y", alpha=.3)

fig.suptitle("Figure 8 - Rating and helpful votes by unit-price quintile\n"
             f"{len(f8):,} reviewed order items, one row per review")
plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.show()


# %% [markdown]
# #### Coverage check
# 
# The specification requires the assessed set to cover all six published categories, use evidence
# from at least four of the six output tables, and include at least two correct relational
# analyses. This cell states which figure covers what, so the requirement is checked rather than
# assumed.

# %%
# --- Coverage of the assessed set, checked rather than assumed ---
COVERAGE = {
    1: dict(categories={'univariate'},                 tables={'orders'},                            joins=0),
    2: dict(categories={'bivariate'},                  tables={'order_items', 'products'},           joins=1),
    3: dict(categories={'temporal'},                   tables={'orders'},                            joins=0),
    4: dict(categories={'multivariate', 'operational'},tables={'deliveries', 'orders'},              joins=1),
    5: dict(categories={'text'},                       tables={'product_reviews'},                   joins=0),
    6: dict(categories={'operational', 'bivariate'},   tables={'product_reviews', 'deliveries'},     joins=1),
    7: dict(categories={'multivariate'},               tables={'customers', 'orders'},               joins=1),
    8: dict(categories={'multivariate'},               tables={'product_reviews', 'order_items', 'products'}, joins=2),
}

REQUIRED = {'univariate', 'bivariate', 'multivariate', 'temporal', 'text', 'operational'}
seen_categories = set().union(*(f['categories'] for f in COVERAGE.values()))
seen_tables     = set().union(*(f['tables'] for f in COVERAGE.values()))
join_count      = sum(1 for f in COVERAGE.values() if f['joins'] > 0)

print(f'figures            {len(COVERAGE)}   (6 to 8 required)')
print(f'categories covered {len(seen_categories)}/6  missing: {sorted(REQUIRED - seen_categories) or "none"}')
print(f'tables used        {len(seen_tables)}/6  ({", ".join(sorted(seen_tables))})')
print(f'relational figures {join_count}     (at least 2 required)')

assert 6 <= len(COVERAGE) <= 8
assert REQUIRED <= seen_categories
assert len(seen_tables) >= 4
assert join_count >= 2
print('\ncoverage requirements met')

# %% [markdown]
# ## 3. Ten evidence-based findings
# 
# Write exactly ten numbered findings. Keep each concise and decision-focused.
# Each must identify the evidence, grain, magnitude/denominator, business meaning,
# an alternative explanation or uncertainty, and a proportionate implication.
# One figure may support more than one genuinely distinct finding.
# 

# %% [markdown]
# *Each finding cites an assessed figure or a reported statistic, and carries all five parts:
# what was observed and at what grain · magnitude, denominator or sample size · why it matters ·
# an alternative explanation or uncertainty · a proportionate implication.*
# 
# 1. **Finding 1** *(Echo Zhao, from Figure 2)* — At the line-item level (15,685 lines), high sales volume does not necessarily mean high revenue. Laptops generate the most revenue (AUD 2.75m) despite ranking only 9th in units sold (1,397). In contrast, Accessories sell the most units (3,051) but generate the lowest revenue (AUD 0.56m). Therefore, inventory and marketing decisions should not be based on sales volume alone. Maybe price level restated rather than any demand effect. Once cost data is available, categories should also be compared by profit margin.
# 2. **Finding 2** *(Echo Zhao, from Figure 6)* — At review grain across all 7,000 reviews, late deliveries do not rate lower: 707 late reviews average 3.82 stars against 3.70 for 6,293 on-time ones. The 0.12-star gap is detectable at 2.55 standard errors, but it runs the wrong way and is negligible on a 1–5 scale. This does not show that delays improve ratings or are harmless — only reviewed items are observed, and unmeasured differences between orders or customers may explain the direction. So ratings will not measure what lateness costs. Justify any spending on delivery reliability from repeat purchase or contact volume instead.
# 3. **Finding 3** (Congyi Wang, from Figure 3) — At order grain across all 5,000 orders of 2018, monthly revenue stays between AUD 1.10m and 1.36m, varying only 6.1%, and neither component drives it: order count varies 4.2% (384 to 443 a month) and mean order value 4.0%. Nothing in the twelve months reads as a peak to staff for or a trough to discount into. The figure cannot rule seasonality out, though: one year gives no second cycle to compare against, and 5,000 orders over twelve months is thin. Keep monthly targets flat until a second year exists.
# 4. **Finding 4** *(Congyi Wang, from Figure 4)* — 89.4% of 5,000 deliveries arrive on time, and nothing we can group by changes that: all 24 carrier × service × warehouse groups land between 81.8% and 95.8%. Express and Standard differ only in money. Express is charged AUD 23.48 a delivery and costs AUD 18.33 to run, Standard AUD 12.17 and AUD 9.55 — both about a 22% markup — while the promise (5.03 days against 4.99), the distance (5.4 km against 5.3) and the on-time rate (89.7% on 901 Express against 89.4%) are the same. The extra AUD 8.78 per Express delivery, about AUD 7,900 a year, buys nothing observable here. Distance rules out the obvious explanation, but what makes up delivery_cost is unrecorded — ask what the premium buys before renewing Express.
# 5. **Finding 5** *(Yandu Wang, from Figure 1)* — Order value is heavily skewed. The median order is AUD 2,502 but the average is AUD 2,983, and that average is higher than 59% of all 5,000 orders. Values run from AUD 22 to AUD 17,720, with the top 5% above AUD 7,135. So quoting the average makes the typical order look about 19% bigger than it is — anyone sizing packaging, delivery cost or a free-shipping threshold off the average will size it for a customer who mostly does not exist. Use the median for that. One caveat: order_total is not the basket. It is net of the coupon and includes delivery charges, so part of this spread is shipping rather than goods, and order_price would give a cleaner picture.
# 6. **Finding 6** *(Yandu Wang, from Figure 7)* — The four customer segments spend almost the same. The widest gap is Mainstream at AUD 31,360 against Small Business at AUD 28,897 per customer — only 1.5 standard errors apart on 110 to 139 customers each, so not a real difference. The labels do not even rank in the order they read: Premium is third. But the two halves of that total do differ, in opposite directions. Value customers order most often and spend least each time (10.4 orders, AUD 2,846); Small Business order least often and spend most (9.4, AUD 3,062). They cancel out. So a campaign aimed at "high-spending segments" has nothing to aim at, while one aimed at frequency or basket size does. Both gaps are around 2.4 standard errors and they are the largest of twelve comparisons, so treat them as a lead rather than a fact. Worth checking too whether customer_segment was assigned from prior_12m_orders or lifetime_value_before_period — if so, part of this is the assignment rule showing through.
# 7. **Finding 7** *(Siyuan Shao, from Figure 5)* — At review grain across all **7,000** reviews, the **271** containing non-Latin script had a median cleaned length of **607 characters**, against **927** for the 6,729 Latin-only reviews. Within the Latin-only group, the median fell about **7%**, from 980 characters at 2 stars to 907 at 5 stars; the much smaller non-Latin group moved 746 / 659 / 513 / 659 / 498 across ratings 1–5 with no ordered pattern. Review length is therefore too inconsistent across scripts to use alone as a satisfaction proxy. Language-specific writing conventions, the cleaning rules and only 271 non-Latin observations may explain the difference, so the next step is a larger within-language comparison rather than a causal claim.
# 8. **Finding 8** *(Siyuan Shao, from Figure 8)* — At reviewed-order-item grain across all **7,000** reviews, mean rating fell from **3.879** in the lowest price quintile to **3.548** in the fourth—a **0.331-star** difference of roughly **seven standard errors**—before rebounding to 3.684 in the highest quintile. This is a real but non-monotonic association, while median helpful votes remained between **44.0 and 45.5**, small beside each quintile’s middle-half range of roughly 21–68 votes. Price alone is therefore not a reliable rule for review intervention. Only reviewed lines are observed (7,000 of 15,685), and category mix, review age and exposure may confound the result, so a within-category follow-up is needed before inferring a price effect.
# 9. **Finding 9** *(Yandu Wang, from the validation register — no figure needed)* — Where both files hold the same record, they never disagree. Across the six tables 8,098 rows carry a key that shows up more than once, and 3,259 keys sit in both files (500 orders, 1,559 order items, 500 deliveries, 700 reviews). Once both files are put in the same format there are 0 field disagreements, and the two copies of a repeated key inside one file match each other too (`VAL-FLOW-09`, `VAL-FLOW-10`, `VAL-FLOW-12`). The check is shown to work, not just trusted: before the formats are matched the same comparison reports 7 columns disagreeing in orders, 6 in deliveries and 2 each in order items and reviews, and every one drops to 0 after (Section 1.3 in the solution notebook). So keeping the first copy is safe, because no exported value depends on which file we kept. But this is too clean to call it two files agreeing. Those 7 columns are 500 rows each, so 3,500 of the 10,000 values compared differed — every one a format difference (`25/12/2018` against `2018-12-25`, `AUD 2,765.47` against `2765.47`, `Y` against `True`), and not one a difference in the value. Two systems that recorded these orders on their own would slip somewhere in 10,000 values. The simpler explanation is one system exported twice. So the match tells us neither file was damaged on the way out; it does not tell us either file is right. Use one file on its own if you want, but do not use the second as proof of the first.
# 10. **Finding 10** *(Yandu Wang, from the validation register — no figure needed)* — `deliveries.delivery_note_clean` has only two values, and they split the 5,000 deliveries exactly the same way as four other columns: `delay_reason == 'none'`, `on_time_in_full`, `delay_days == 0` and `delivered_date <= promised_date`. Not one row disagrees on any of the four. 528 deliveries, 10.6%, land on the late side of all five at once. So the note says nothing the other columns do not already say. It matters because it looks like a written note rather than a result, which makes it the column most likely to be left in a model by mistake, and in ML question 1 it would hand the model the answer. It may also be that this is just how this one extract came out: two note values over one year cannot show whether the note is written from the result or only happens to match it, and the real system may write notes that say something useful. Either way, leave it out of any lateness model, and check what notes the source system actually writes before using the field.

# %% [markdown]
# ## 4. Five future machine-learning questions
# 
# Write exactly five numbered questions covering at least two problem types.
# Model training is not required. Keep each response compact enough for the
# ten-page report.
# 

# %% [markdown]
# ### MLQ-1 (Congyi Wang): Will this order be delivered later than promised?
# 
# | Element | Response |
# |---|---|
# | EDA evidence | Figure 4: 528 of 5,000 deliveries arrive late (10.6%), and none of the obvious levers separates them — all 24 carrier x service level x warehouse groups sit between 81.8% and 95.8%, and Express is no better than Standard. So the features anyone would reach for first do not predict lateness, and a model has to find something subtler or there may be nothing to find. |
# | Business decision | Which orders to flag at dispatch — whether to warn the customer early, upgrade the shipment, or hold buffer capacity at the warehouse. Only worth doing on orders likely to be late; alerting on all 5,000 is not proportionate to 528 failures. |
# | Problem type and analysis unit | classification · one order at the point of dispatch |
# | Target or unsupervised objective | `on_time_in_full`, or `delivered_date > promised_date` |
# | Decision-time predictors | Order timestamp, sales channel, service level, carrier, promised days, `shipping_distance_km`, `delivery_cost`, `fulfilment_hours` (order to dispatch, so complete at decision time), cart size and value, customer history. |
# | Validation split | Temporal split — train on earlier months, test on later, because a random split lets the model see the future of the same period |
# | Evaluation metric | Recall at a fixed alert budget, since the decision is which orders to intervene on |
# | Leakage, fairness or deployment risk | **Target leakage is the whole problem here. `delay_days`, `delay_reason`, `delivery_note_clean` and `tracking_event_count` are all recorded after delivery and all encode the target — Finding 10 shows the note alone reproduces the outcome exactly, and the tracking count accumulates in transit. delivered_date is equally unavailable at decision time.**|

# %% [markdown]
# ### MLQ-2 (Echo Zhao): How much will a returning customer spend on their next order?
# 
# | Element | Response |
# |---|---|
# | EDA evidence | Figure 2 shows that order value varies strongly with product mix: Laptops generate AUD 2.75m from 1,397 units, while Accessories generate AUD 0.56m from 3,051. This suggests that a customer’s previous category mix, together with past spending behaviour, may help predict the value of their next order.|
# | Business decision | Which returning customers to target with higher-value product recommendations or promotions before their next purchase. |
# | Problem type and analysis unit | Regression · one returning customer’s next order, predicted before that order is placed. |
# | Target or unsupervised objective | `order_total` of the customer’s next order.|
# | Decision-time predictors | Previous order count, recency, average and most recent order value, historical category mix, channel history, customer segment |
# | Validation split | Temporal split: train on earlier orders and test on later orders. All history features must be calculated using only transactions before the target order.|
# | Evaluation metric | Mean absolute error in AUD, compared with a simple baseline such as the customer’s historical mean order value. |
# | Leakage, fairness or deployment risk |The target order itself cannot contribute to any predictor.  `coupon_discount`, `tax_amount` and `order_price` current order items and other fields created from the target transaction must be excluded. Customers with insufficient prior history cannot be scored reliably. |

# %% [markdown]
# ### MLQ-3 (Siyuan Shao): Which delivered items are likely to receive a rating of 2 or below if reviewed?
# 
# | Element | Response |
# |---|---|
# | EDA evidence | Figure 8 shows rating varies non-monotonically across price quintiles; price alone cannot identify low-rating purchases. |
# | Business decision | Prioritise proactive support after delivery but before a review is written. |
# | Problem type and unit | Binary classification; one delivered order item. |
# | Target | `rating <= 2`, conditional on a subsequent review. |
# | Predictors | Category, price, carrier, service level, lateness, channel and earlier customer history. |
# | Validation | Train on earlier orders and test on later orders. |
# | Metric | Precision and recall against the 17.86% low-rating base rate. |
# | Risk | Only 7,000 of 15,685 items were reviewed, so predictions apply conditionally to reviewed items. A separate review-propensity model is required for all deliveries. Exclude review-derived fields. |

# %% [markdown]
# ### MLQ-4 (Yandu Wang): What natural customer segments exist in purchasing behaviour?
# 
# | Element | Response |
# |---|---|
# | EDA evidence |  Figure 7 and Finding 6: the four labels in `customer_segment` do not separate customers by spend. The widest gap is AUD 31,360 against AUD 28,897 per customer, which is 1.5 standard errors on 110 to 139 customers each — too small to call a real difference. The two parts of that total do differ, and in opposite directions: Value customers order 10.4 times a year at AUD 2,846 each time, Small Business 9.4 times at AUD 3,062, about 2.4 standard errors apart on both. So customers do behave differently; they just do not behave differently along the lines the existing labels draw. That is the case for asking the data for its own groups. |
# | Business decision | Whether to keep aiming campaigns at the four labels we already have, or to group customers by how they actually buy. The groups decide who gets an offer meant to make them order more often and who gets one meant to make each order bigger — two different campaigns, and Figure 7 shows the current labels cannot tell those two kinds of customer apart. |
# | Problem type and analysis unit | clustering · one customer |
# | Target or unsupervised objective | No target. Objective: compact, well-separated groups on spend, frequency, recency, category mix and channel |
# | Decision-time predictors | Order count, total and average order value, category shares, channel shares, signup recency, marketing consent |
# | Validation split | No train/test split; stability is assessed by re-clustering bootstrap resamples and comparing assignments |
# | Evaluation metric | Silhouette score for separation, plus a stability score across resamples |
# | Leakage, fairness or deployment risk | With 500 customers the clusters may not be stable; features on different scales will dominate the distance unless standardised. **Fairness:** if a segment is used to price or to allocate service, check it is not a proxy for postcode. |

# %% [markdown]
# ### MLQ-5 (Echo Zhao): Which customers will place another order within the next 30 days?
# 
# | Element | Response |
# |---|---|
# | EDA evidence | The dataset contains 5,000 orders from 500 customers across 2018, providing repeated purchase histories that can be ordered over time. This makes it possible to examine whether recent customer behaviour predicts another purchase. |
# | Business decision | Which customers to prioritise for retention messages or promotions after a purchase. |
# | Problem type and analysis unit | Binary classification · one customer immediately after an order. |
# | Target or unsupervised objective | Whether the customer places another order within the next 30 days. |
# | Decision-time predictors | Previous order count, days since previous order, historical purchase frequency, average and most recent order value, historical category mix, channel history and customer segment. |
# | Validation split | Temporal split: train on earlier orders and test on later orders, with all behavioural features calculated only from information available at the prediction date. |
# | Evaluation metric | Precision-recall AUC, with recall at a fixed campaign budget as an operational metric.|
# | Leakage, fairness or deployment risk | Predictors must use only purchase history available at the prediction date. Orders in the final 30 days are excluded because their 30-day repurchase outcome cannot be fully observed. |

# %% [markdown]
# ## 5. Limitations and conclusion
# **One merchant, one year, one state.** All 5,000 orders were placed in 2018, by 500 customers, all in Victoria, all in Australian dollars. Seven columns hold the same value in every single row — `currency`, `order_status`, `delivery_status`, `tax_category`, `verified_purchase`, `home_state` and `home_country`. That is how narrow this slice of the business is. With only one year we also cannot tell a seasonal pattern from a longer trend. None of these results should be assumed to hold for another region or another year.
# 
# **The two files most likely came from the same system.** They never disagree. 3,259 keys appear in both files across the six tables, and not one field differs. In `orders`, 3,500 of the 10,000 values we compared were written differently — 25/12/2018 against 2018-12-25 — but none of them meant anything different. Two systems keeping their own records would disagree somewhere. So the match tells us nothing was damaged on the way out. It does not tell us either file is correct, and we should not call it cross-validation.
# 
# **A difference this small would be invisible anyway.** Figure 3, the on-time rate in Figure 4, and Figure 7 all report that nothing varies. But no Express group holds more than 100 deliveries, and with groups that small the on-time rate moves three to five percentage points on its own. A real difference of that size would not show up here. That is a reason not to spend money on the change — it is not proof the change would do nothing.
# 
# **Only some customers wrote reviews.** 7,000 of the 15,685 delivered items have a review, counted per item, so one order can appear more than once. Findings 2, 7 and 8 are therefore about people who write reviews, not about customers in general. The ones who said nothing are exactly the people a service-recovery programme would be aimed at.
# 
# **Nothing here shows cause.** The most tempting reading is Finding 2 — late deliveries are rated *higher* than on-time ones, 3.82 against 3.70. That is the wrong way round, which usually means something we cannot see sits behind both. A seller who ships slowly might also be one people are generous to, and we have no way to hold that constant. The same caution applies to price and rating in Figure 8.
# 
# **Some columns give away the answer.** Three of them repeat what another column already says: `delivery_note_clean` records whether the delivery was late, `expedited_delivery` is `service_level` under a different name, and `delivery_experience` matches `on_time_in_full` on all 7,000 rows. Any of the three would hand a model the answer it is meant to predict, so every ML question has to remove them on purpose rather than by accident.
# 
# **Conclusion.** These tables are consistent, reconciled and reproducible, and that is what they are good for: describing this year accurately. The results worth using are the descriptive ones — order value is skewed enough that the average misleads, and the categories earning the most money are not the ones selling the most units. Most of the operational results found nothing. The one that did — Express costs 92% more to run for the same promise, the same distance and the same on-time rate — is useful for the same reason: it shows money going into a difference the data cannot otherwise justify. Anything about cause, or about next year, needs a second year of data and the cost of the goods themselves.

# %% [markdown]
# ## References
# 
# All analysis in this notebook uses the six standardised CSVs produced by `Group001_solution.ipynb` from the allocated package (`Group001_commerce.json`, `Group001_operations.xml`) and the field definitions in `public_data_dictionary.csv`, all supplied for FIT5196 Assessment 1, Semester 2 2026, Monash University.
# 
# No other data was used. The only outside sources are the software libraries and the interval method listed below.
# 
# Software:
# 
# - The pandas development team (2024) *pandas* (version 2.3.3) [Python library]. https://pandas.pydata.org
# - Hunter, J. D. (2007) 'Matplotlib: A 2D graphics environment', *Computing in Science & Engineering*, 9(3), pp. 90–95. https://matplotlib.org
# 
# Statistical method:
# 
# - Wilson, E. B. (1927) 'Probable inference, the law of succession, and statistical inference', *Journal of the American Statistical Association*, 22(158), pp. 209–212. Used for the binomial confidence interval in Figure 4.
# 


