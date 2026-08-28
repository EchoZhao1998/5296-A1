# Review notes — Echo's Task 1 notebook

**Reviewer:** Jasmine (WP2) · **Reviewed:** `01_WIP/wip_echo_0823.ipynb`, 23 Aug 2026
**Scope:** §0 through §1.5. §2 (mapping) is not started — opens at G1 per D5.

Every number below was re-derived independently from `DATA/Group001_A1/raw_input/`, not copied
from the notebook. Where a figure disagrees with the notebook, both are given.

---

## Contents

1. [What is working](#0)
2. [For Echo — WP1](#echo)
3. [For Yandu — WP3](#yandu)
4. [For me — WP2](#jasmine)
5. [Open questions for G0 / G1](#open)
6. [Addendum — for Shawn, WP4](#wp4)

---

<a id="0"></a>
## 1. What is working

Recorded because a review that only lists defects is not a fair account of the section.

- **The pass-1 / pass-2 structure.** Running the naming rule with no exceptions, reading the
  report, and only then encoding exceptions — with the comment "written from the report above,
  not before it" — makes the exception list an outcome rather than an assumption. Formalised as
  DEC-012.
- **`check_names` reused, not rewritten**, so JSON and XML are judged by identical criteria. A
  second checker would let differences in the checker masquerade as differences in the data.
- **§1.3a compares the same order in both files** rather than two unrelated samples. Differences
  can then only come from representation. `sorted(shared)[0]` keeps the pick deterministic
  across reruns.
- **§1.3e runs the comparison twice**, un-normalised and normalised. On data with zero conflicts
  this is the only thing that shows the detector is sensitive rather than silent.
- **The §1.3f register requires an evidence cell per assumption** — "an assumption with no
  evidence cell is not an assumption, it is a guess."
- **§1.5 flags its own gap** (`the completed source-to-target mapping — not started`) rather
  than leaving it silent.

---

<a id="echo"></a>
## 2. For Echo — WP1

### E1 · §1.4 grain: `order_items` is 1–5 per order, not 1–10

The `max 10` is the same duplication artefact corrected for `deliveries` two bullets earlier.

| | min | median | max |
|---|---|---|---|
| as measured (raw) | 1 | 3 | **10** |
| after dedup on `order_item_id` | 1 | 3 | **5** |
| actual cart sizes in the file | 1 | — | **5** |

The orders hitting 10 — `HORD000395`, `HORD000480`, `HORD001916` — each appear twice in the file
with a 5-item cart.

Grain has to be measured after dedup, otherwise it measures grain plus duplication:

```python
per = df.drop_duplicates(KEYS[name]).groupby("order_id").size()
```

Only `max` is affected; `min` and `median` survive because 68 orders cannot move the median of
2,818. But `max` is exactly the number that becomes a range check — one written against 1–10
could never fire.

The same artefact was caught for `deliveries` ("the max 2 … is the duplicate pair, not a second
delivery") and missed here. The difference is that `max 2` is obviously wrong for a delivery,
while `max 10` reads as a plausible cart size.

### E2 · The XML profile table never renders

In §1.2's profile cell:

```python
pd.DataFrame(profile_xml)          # computed, then discarded
for name, df in xml_tables.items():
    ...                            # only this displays
```

Jupyter auto-displays the last expression only. The §1.1 equivalent renders because
`pd.DataFrame(profile)` is the final line there.

Net effect: XML key-uniqueness and duplicate evidence is absent from the page, while §1.3c's
introduction says these are "shown rather than claimed". `display(...)` or a cell split fixes it.

### E3 · `NORMALISERS` does not cover `products` or `customers`

§1.3b asks WP2 to import these rather than write its own, which is the right call — two
implementations of "what is a valid date" is how C1 and E1 diverge. But the dict covers only the
four shared tables.

`products` is XML-only, so every value is a string, and eight fields need conversion:

| category | fields |
|---|---|
| money | `unit_price`, `unit_cost` |
| datetime | `launch_date` |
| bool | `recyclable_packaging`, `active_flag` |
| number | `weight_kg`, `launch_year`, `warranty_months` |

`customers` is JSON-native and needs only `signup_date`.

**Proposed:** WP2 extends the dict in the same structure and returns it for confirmation, so the
canonical set stays one object.

### E4 · `norm_datetime` is ~100× slower than it needs to be

`series.map(lambda v: norm_datetime(v, dayfirst))` pays the parser's start-up cost per element.

```
2,818 rows, one column
  element-wise .map()   960 ms
  vectorised              9 ms      (.equals() → True)
```

`pd.to_datetime(series, dayfirst=dayfirst, errors="coerce")` is a drop-in. It matters more in §4,
where the frames are the concatenated 5,636 / 7,892 rows across several date columns. Rubric E2
names "methods appropriate to scale".

### E5 · A6's zero-padding warning names the wrong field

> "Identifiers stay strings; the zero padding is significant … casting it to an integer destroys
> the padding"

All six identifiers carry alpha prefixes — `HORD000879`, `HITM0002731`, `PRD0001`, `CUS00001`,
`HDEL000879`, `HREV002000`. `int()` on any of them raises, loudly. Nothing is lost silently.

The field that does convert silently is **`home_postcode`** — pure digits, `'3011'`. No postcode
in this package starts with a zero, so no value is visibly damaged, but the dtype would breach
the dictionary and B3 assesses exactly that. Worth naming it in A6.

### E6 · Two assumptions missing from A1–A8

**A9 (proposed): `delay_reason == 'none'` is a real value, not a missing marker.** 4,472 rows
(canonical, i.e. across the 5,000 deduplicated deliveries; an earlier version of this note said
2,516, which was the JSON-only figure).
Read next to A8 ("missing means an empty string in the JSON and an empty element in the XML"),
someone could reasonably write `replace(['none', ''], 'NaN')` and destroy the column. Nothing in
the register currently prevents that.

**A10 (proposed): `order_status` and `delivery_status` are single-valued.** 100% `Completed` /
`Delivered`, both files, 5,636 rows, no exceptions. This matters twice:

- the dictionary's deliveries grain is "one row per **completed** order delivery", so §4 will
  write a filter that removes zero rows — without a note, a reviewer reads that as a broken
  filter;
- neither field can carry an EDA figure, since the chart is one bar.

### E7 · A7 puts a value list inside an assumption

"`coupon_discount` is a percentage" is a format fact and safe to depend on. "values
0/5/10/15/20/25" is an observation of this package. Coding against an enumerated value set is
close to hard-coding, which the spec forbids. It belongs in Yandu's allowed-value checks, not in
the transformation's preconditions.

### E8 · A8's scope is source-side only

True of the raw files — `coupon_code` is the only field with any missing values, 1,767 blank
strings in JSON and 1,770 empty elements in XML.

Not true of the outputs. These target fields can all carry the literal `NaN` sentinel:
`orders.promo_code`, `orders.coupon_code`, `orders.customer_note_clean`,
`products.product_description_clean`, `product_reviews.review_body_clean`,
`review_body_latin_analysis`, `extracted_order_reference`, `extracted_product_sku`.

One clause would stop A8 being read as "only one column needs sentinel handling".

### E9 · A5 wording

"no precedence rule is needed" is right in substance — the values agree, so any deterministic
choice gives the same row. But `pd.concat([json, xml])` followed by `drop_duplicates(key,
keep="first")` **is** a precedence: JSON always wins.

C2 marks whether assumptions are recorded rather than silently applied. Safer phrasing: *any
deterministic choice is equivalent; we keep the first (JSON) copy, and §1.3e evidences that the
choice does not affect output.*

### E10 · The Colab cell breaks Run All for anyone else

```python
try:
    from google.colab import drive
    drive.mount("/content/drive")
    %cd /content/drive/MyDrive/26S2/5196/Group001_A1/01_WIP
except ImportError:
    pass
```

`%cd` to a non-existent directory raises something other than `ImportError`, so the handler does
not catch it. A marker opening the submitted notebook **on Colab** would authorise their own
Drive, then hit a path they do not have, and Run All stops at the first cell.

HANDOVER §5's G6 check reads "the Colab cell is harmless off Colab" — the exposure is *on* Colab,
for someone who is not us. Low priority while this is WIP, but the checklist item points the
wrong way.

A candidate-list version removes the per-person edit as well:

```python
try:
    from google.colab import drive
    from pathlib import Path
    import os
    drive.mount("/content/drive")
    hit = next((p for p in Path("/content/drive/MyDrive").rglob("Group001_A1/01_WIP")
                if p.is_dir()), None)
    if hit:
        os.chdir(hit)
except ImportError:
    pass
```

### E11 · Both §1.2 hand-off questions, answered

**"`order_items` counts differ (8,826 vs 8,833) — genuine extra items or a duplicate pattern?"**

Neither. The 500 shared orders carry **identical cart sizes on both sides — 0 disagreements**.
The difference comes entirely from the orders unique to each file.

```
JSON-only  2,250 orders → 7,066 items
XML-only   2,250 orders → 7,060 items
shared       500 orders → 1,559 items   (identical both sides)

JSON deduped  7,066 + 1,559 =  8,625   + 201 duplicate rows = 8,826
XML  deduped  7,060 + 1,559 =  8,619   + 214 duplicate rows = 8,833
```

Zero cart-size disagreement across the shared orders is a stronger consistency result than
field-level agreement alone, because it verifies structure as well as values.

**"Are the within-source duplicates field-identical?"**

Yes on both sides. XML re-derived independently: 68 duplicate `order_id` groups, 68
field-identical, 0 conflicting — matching the JSON result. Every duplicate group in every
affected table is exactly two copies (`copies_per_key = [2]`), so no key appears three times.

### E12 · One design consequence to settle before §5

After dedup the 500 shared orders collapse to a single row carrying `source_system = "JSON"`. The
signal "this record appeared in both files" disappears at exactly the point Yandu needs it — §1
describes `source_system` as required "for the overlap and reconciliation work in §5, and for
row-flow evidence in §6".

Two workable shapes: hand the overlap key sets to WP3 before dedup, or write `"both"` into the
marker during dedup. Either is a WP2 change; it needs deciding, not discovering at G4.

---

<a id="yandu"></a>
## 3. For Yandu — WP3

### Y1 · 302 orders have `delivered_date > promised_date` — this is not a data error

`delay_days` and `delay_reason` sit alongside it, populated with `warehouse_congestion`,
`carrier_capacity`, `weather`. A `delivered <= promised` check marked FAIL flags normal late
deliveries as defects.

The temporal chain that is genuinely invariant: `order_timestamp ≤ dispatch_date ≤
delivered_date` — **0 violations**. Late-delivery rate is a good EDA figure, not a validation
failure.

### Y2 · The template prescribes the VAL prefixes — use them verbatim

`A1_solution_template.ipynb` §6 gives one subsection each for `VAL-SCHEMA-`, `VAL-PK-`,
`VAL-FK-`, `VAL-FLOW-`, `VAL-ARITH-`, `VAL-TIME-`, `VAL-TEXT-`, plus §6.7's literal-`NaN`
reminder. D4 commits the group to the template's numbering verbatim, and the mapping's
`notebook_evidence` column cites section names — inventing prefixes breaks both.

### Y3 · Q2 is easier than it looks

Every duplicate group is exactly two field-identical copies, in both files, across all five
affected tables, with zero conflicting groups. Any deterministic keep rule produces the same row.

The decision only has to record *that* the choice is fixed and *why* it is safe (the rows are
identical), not to justify preferring one source.

### Y4 · The conflict detector needs a positive test

Cross-source comparison gives **0 conflicts across 3,259 shared keys and 59 compared columns**.
On that data a broken detector and a correct one produce identical output.

Echo's `duplicate_shape` cell has the pattern worth copying — a four-row constructed fixture with
a planted conflict, shown being detected, then the real run showing zero. C2 marks whether
conflicts *would* be recorded; "we found none" is only credible with a demonstrated detector.

### Y5 · `pd.NaT != pd.NaT` is `True`

Both-sides-missing registers as a conflict unless handled explicitly. Same for `np.nan`. Use
`np.isclose(a, b, atol=0.01, equal_nan=True)` for numerics and an explicit both-null branch
elsewhere.

### Y6 · Use the published 0.01 tolerance, not exact equality

§1.3e compares money with `!=`, which is stricter than the spec's absolute tolerance of 0.01.
Fine there because the result is zero — a stricter test passing implies the looser one passes —
but the register's own checks should use the published rule.

### Y7 · `order_items` grain is 1–5 per order, not 1–10

See E1. A range check written against 1–10 could never fire. Better still, derive the bound:

```python
expected_max = max(len(o["shoppingCart"]) for o in raw_json["orders"])
```

### Y8 · `delay_reason == 'none'` is a valid category on 4,472 rows

Not a missing value. Allowed-value checks should include it, and no cleaning step should map it
to the `NaN` sentinel.

The count is the canonical one — 4,472 of the 5,000 deduplicated deliveries. An earlier version
of this note said 2,516, which was the JSON-only figure and would not have matched anything
Yandu computed on the combined table.

### Y9 · `order_status` and `delivery_status` are single-valued

100% `Completed` / `Delivered` across both files. Any distribution check on them is trivially
satisfied, and the deliveries "completed" filter removes zero rows — worth a note so the
no-op reads as expected rather than broken.

### Y10 · Derive expected counts, never write them in

Rubric E1's Fail descriptor names "hard-coded certified counts/answers"; the spec forbids
hard-coding canonical row counts.

```python
assert len(orders) == 5000                                    # fails E1
expected = len(json_ids | xml_ids); assert len(orders) == expected   # passes
```

The second is a real check because the expectation reaches the same number by an independent
route.

### Y11 · A genuine FAIL is worth marks

Rubric §5: *"A genuine failed validation check can receive validation and interpretation credit
when it correctly identifies the issue and proposes a justified treatment. Fabricating a value to
make a check pass receives no such credit."* An all-green register is not the goal.

### Y12 · The eight required FKs have to be checked on the output tables

§1.3d proves the **source union** is referentially sound — 16 candidate child columns, 0
unmatched, and no blank FK values. That is a different claim from "the six submitted CSVs satisfy
the eight relationships the spec lists". Both are needed; the second is what B1 and C2 assess.

The eight, for reference:

| child | parent |
|---|---|
| `orders.customer_id` | `customers.customer_id` |
| `order_items.order_id` | `orders.order_id` |
| `order_items.product_id` | `products.product_id` |
| `deliveries.order_id` | `orders.order_id` |
| `product_reviews.order_id` | `orders.order_id` |
| `product_reviews.order_item_id` | `order_items.order_item_id` |
| `product_reviews.product_id` | `products.product_id` |
| `product_reviews.customer_id` | `customers.customer_id` |

### Y13 · Decision needed from WP3

After WP2's dedup, the 500 shared orders become one row tagged `source_system = "JSON"` — the
overlap signal is gone before the tables reach §5. Overlap key sets handed over pre-dedup, or a
`"both"` marker? Either is a WP2 change; WP3 should pick the shape it needs.

---

<a id="jasmine"></a>
## 4. For me — WP2

### Pipeline order is a hard constraint

```
concat both sources → normalise → dedupe → derive → order columns by position → export
```

Not a preference. JSON's reviews reference **1,813 `order_item_id` values JSON does not contain**;
XML's reference 1,724 it does not contain. Neither export is referentially self-consistent.
Building per-source and unioning last breaks every intermediate integrity check.

No fan-out and no roll-up anywhere — source grain equals target grain for all six tables. The
only cross-table calculation is `order_price` summing `line_revenue`, and that changes neither
table's grain.

### Section numbering (template, verbatim per D4)

```
§4.1 orders    §4.2 order_items    §4.3 customers
§4.4 deliveries    §4.5 products    §4.6 product_reviews
§7 Export the six CSV files
```

### Interface facts

| | |
|---|---|
| `parse_json` returns | 5 tables |
| `parse_xml` returns | 6 — includes `warehouses`, **exclude it** |
| shared-table column sets | **identical across sources** (verified) — concat produces no alignment NaN |
| values | source-native, **not normalised** |
| `source_system` | inserted at position 0 — **drop before export** |
| exception dicts | keyed on original tags, not interchangeable, and a wrong dict fails silently |

Guard the precondition rather than assuming it:

```python
for t in ["orders", "order_items", "deliveries", "product_reviews"]:
    assert set(json_tables[t].columns) == set(xml_tables[t].columns), t
```

### Arithmetic chain — verified against all 2,818 rows in both sources

```python
line_revenue = round(quantity * unit_price, 2)
order_price  = round(sum(line_revenue), 2)                              # 2818/2818 both sources
tax_amount   = round(order_price / 11, 2)                               # before the discount
order_total  = round(order_price * (1 - coupon_discount/100)
                     + delivery_charges, 2)
```

- **`coupon_discount` is a percentage, not a dollar amount.** Reading it as dollars reproduces
  only 640 of 2,818 order totals — and those 640 are exactly the rows where the discount is 0.
- **Python's built-in `round()` reproduces the source exactly, 2,818/2,818.** `Decimal` with
  `ROUND_HALF_UP` matches 2,758 exactly and the remaining 60 differ by 0.01 — inside the
  published tolerance, so both are safe, but `round()` avoids the argument.
- **`tax_amount` is reported separately and never added to `order_total`.**

### Six traps

1. **`.astype(str)` on `NaN` is version-dependent.** pandas 2.x yields the string `'nan'`
   (lowercase — not the `'NaN'` sentinel); pandas 3.x keeps `NaN`. Fill the sentinel *before*
   casting, never rely on the cast to produce it.
2. **`home_postcode` must stay `str`.** Pure digits, so pandas converts it silently. The six
   identifiers have alpha prefixes and raise instead.
3. **`delay_reason == 'none'` is a real value** on 4,472 rows (canonical). Keep it out of any
   replace list.
4. **`set_index(key).loc[value]` on an undeduped table returns a DataFrame, not a Series.**
   `drop_duplicates` first. 27 of the 500 shared order ids are duplicated in one file or the
   other.
5. **XML strings compare lexicographically and silently give wrong answers.**
   `'AUD 155.15' > 'AUD 1,827.30'` evaluates `True`. No comparison, sort or aggregation before
   normalisation.
6. **`order_status` / `delivery_status` are single-valued.** The deliveries "completed" filter
   removes zero rows — write it anyway, and comment that it is a no-op on this package.

### Row-flow baselines — derive these, never write them in

| table | JSON | XML | concat | canonical | removed |
|---|---|---|---|---|---|
| orders | 2,818 | 2,818 | 5,636 | 5,000 | 636 |
| order_items | 8,826 | 8,833 | 17,659 | 15,685 | 1,974 |
| deliveries | 2,818 | 2,818 | 5,636 | 5,000 | 636 |
| customers | 500 | — | 500 | 500 | 0 |
| products | — | 1,000 | 1,000 | 1,000 | 0 |
| product_reviews | 3,946 | 3,946 | 7,892 | 7,000 | 892 |

Printing this chain per table satisfies the template's §4 row-flow evidence and rubric E1's
"source coverage and row counts before and after major transformations" in one move.

### Free cross-checks

- Within-source dedup should remove: orders 68, `order_items` 201 (JSON) / 214 (XML),
  deliveries 68, reviews 96 — per source. The `order_items` figures are a *consequence* of the
  order duplication (68 duplicated orders carrying 402 item rows), so they must move together.
- `deliveries` is 1:1 with `orders` — same row count, `order_id` unique.
- `product_reviews.order_item_id` is unique (3,850) — 1:1 with `order_items`, so that join
  cannot multiply rows.
- Maximum cart size is 5 — derive it from the source rather than writing 5.
- 497 of 500 customers have orders. Three have none. Relevant to EDA denominators.

### Data dictionary — columns known so far

`output_table` · `field_name` · `position` · `nullable`. `position = 1` marks the primary key.

```python
order = dd.loc[dd.output_table == t].sort_values("position")["field_name"].tolist()
pk    = dd.loc[(dd.output_table == t) & (dd.position == 1), "field_name"].iloc[0]

df = df[order]
assert list(df.columns) == order                    # B1 field order
assert df[pk].is_unique                             # unique
assert df[pk].notna().all() and (df[pk] != "").all()   # and complete
```

Free cross-check: the XML element order matches the mapping's target field order for the shared
fields of **all five** XML collections. If the order derived from the dictionary disagrees with
the XML element order, the dictionary is being read wrong.

### Schedule

| when | deliverable |
|---|---|
| Mon 25 Aug | target contract — grain, field list in `position` order, dtype, nullability, source field per column. Needs the dictionary only. |
| Wed 27 Aug (G1) | §4.1 `orders` and §4.2 `order_items` end to end |
| Wed 3 Sep (G3) | all six tables written to `02_Outputs/` |
| Sat 6 Sep (G4) | review WP3 |
| Tue 8 Sep (G5) | two EDA figures |

Build order: start with `order_items` or `deliveries` — zero naming exceptions, zero derived
fields, no dependency on WP4 — and get normalise → dedupe → order → export working end to end.
Leave `product_reviews` last: 7 of its 21 fields are derived and all of them depend on WP4.

---

<a id="open"></a>
## 5. Open questions for G0 / G1

| # | Question | Who decides | By |
|---|---|---|---|
| 1 | The ~97 mapping rows with no owner for `transformation_or_derivation` — text 10 → WP4, arithmetic 4 → WP2, the remainder unassigned. A2 counts a row only when all six columns are right. | all four | G1 |
| 2 | Arithmetic fields — `source_format = derived` or `both`? The source carries the values but the pipeline recomputes them. | Echo + Jasmine | G1 |
| 3 | Confirm §4 outputs the final deduplicated tables and WP3 validates them. Worth a `DEC-` row. | Jasmine + Yandu | G0 |
| 4 | `NORMALISERS` extended to `products` and `customers` by WP2, confirmed by WP1. | Echo + Jasmine | G1 |
| 5 | ~~Q1 — does `delivery_note_clean` get `clean_narrative_text` or a direct copy?~~ **Resolved — see the addendum, §6.1.** | Echo + Jasmine | closed |
| 6 | `decision_log.md` — my copy stops at DEC-009 but DEC-011/012/014/015 are cited in the notebook. Is the Drive copy current? | Echo | G0 |
| 7 | `requirements.txt` — do we submit one? pandas now, matplotlib at EDA. | all four | G0 |
| 8 | EDA category assignment. Four people × two figures = eight, and HD requires all six categories covered. `order_status` and `delivery_status` are single-valued and cannot carry a figure. | all four | G0 |

---

<a id="wp4"></a>
## 6. Addendum — for Shawn, WP4

Added after WP2 finished building all six tables. Two findings change what WP4 receives, and one
of them closes open question Q1. Everything here was checked against the exported tables and the
raw source files, not inferred from the field names alone.

### 6.1 Q1 is closed: `delivery_note_clean` gets `clean_narrative_text`, and it is a WP4 row

The mapping row for `deliveries.delivery_note_clean` has moved from WP2 to WP4. There are now
**11** `TODO-WP4` placeholders in `Group001_mapping_wp2_rows.csv`, not 10.

The argument is consistency rather than anything found in the data. Four target fields carry a
`_clean` suffix — `customer_note_clean`, `product_description_clean`, `review_body_clean` and
`delivery_note_clean`. The first three were already WP4's. Handing the fourth to WP2 as a direct
copy would mean the same suffix means two different things in the same deliverable, which is
exactly the kind of inconsistency A2 and B1 are marked on.

**The trap:** unlike the other WP4 fields, this column is **already populated** in
`Group001_deliveries.csv`. WP2 copies the raw note through so the table conforms to the contract
and the row counts reconcile. Do not read "has values" as "already done" — the column holds
uncleaned source text and needs to be overwritten.

### 6.2 Three target fields do not exist in either source file

`orders.promo_code`, `product_reviews.extracted_order_reference` and
`product_reviews.extracted_product_sku` come out **100% literal `'NaN'`** — 5,000 of 5,000 and
7,000 of 7,000 respectively. They are not sparse columns; they are absent columns.

This was not obvious. `'promo_code' in orders_final.columns` returns `True`, because
`conform_to_contract` creates every field the contract requires whether or not a source supplied
it. Column presence proves nothing. The check that settles it is `(series != 'NaN').sum()`.

So these three cannot be copied or normalised — they have to be **extracted from narrative
text**, which puts them squarely in Task 3 and squarely with WP4. The sentinels sitting in those
columns now are placeholders that keep the tables contract-conformant; they are not results, and
WP4 will overwrite them.

The same check confirmed that nothing else is missing: exactly three columns across all six
tables are all-sentinel, and they are these three. Source field names differ from target field
names throughout (a byte-level search for `coupon_code`, `customer_note` and `delivery_note`
returns zero hits in both files), but the data itself came through intact — `coupon_code`, for
instance, has 1,873 real values across the 5,000 canonical orders.

### 6.3 A guard is now in the WP2 notebook

`wip_jasmine.ipynb` asserts, immediately before export, that the set of all-sentinel columns is
exactly those three. If a fourth ever appears, a real source column has been dropped somewhere
upstream — parsing, normalisation or contract conformance — and the export would otherwise ship
a dead column silently. Worth mirroring in WP3's validation suite once WP4 lands, at which point
the expected set should shrink to zero.

### 6.4 What WP4 owes the mapping

Eleven rows, two columns each: `transformation_or_derivation` and `notebook_evidence`. WP2 left
the key columns untouched, so Echo can merge on `(output_table, target_field)`. The transformation
text has to describe the actual function applied, not the intent — A2 marks a row only when all
six columns are right.

| output_table | target_field | current state in the exported table |
|---|---|---|
| orders | customer_note_clean | populated, raw text |
| orders | promo_code | all `'NaN'` — no source column |
| deliveries | delivery_note_clean | populated, raw text |
| products | product_description_clean | populated, raw text |
| product_reviews | review_body_clean | populated, raw text |
| product_reviews | review_body_latin_analysis | populated |
| product_reviews | review_length_chars | populated |
| product_reviews | review_word_count | populated |
| product_reviews | contains_non_latin_script | populated |
| product_reviews | extracted_order_reference | all `'NaN'` — no source column |
| product_reviews | extracted_product_sku | all `'NaN'` — no source column |

Please confirm this is exactly your set. If a field is missing or wrongly assigned, the boundary
between WP2 and WP4 has a hole in it, and G3 is a worse place to find that out than now.

---

*All figures independently re-derived from the allocated package. Method: `json.load` and
`xml.etree.ElementTree`, no regex applied to document structure. AI assistance was used in
preparing this review and is declared per spec §8; the underlying counts were reproduced from
the source files rather than taken from any summary.*
