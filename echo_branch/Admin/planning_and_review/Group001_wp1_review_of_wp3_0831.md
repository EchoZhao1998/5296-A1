# WP1 review of `wip_Yandu_Wang_G1_VAL.ipynb`

**From** Echo · **31 Aug 2026** · **Verdict** It runs clean and it is good work. 63 checks, all
PASS, no errors. Four things to add, all small. Nothing needs rewriting.

## How this was checked

Run from a fresh kernel against the six CSVs and both raw files. Every cell executed. I then
spot-tested whether the checks can actually fail by planting errors in a copy of the data.

## What is solid

- Every expected number is worked out from the raw files in the same cell that checks it —
  5,000 orders, 68 duplicates, 500 overlap, biggest cart of 5. Nothing typed in. This is the
  thing the rubric penalises hardest and it is done right throughout.
- Ten of the specification's twelve required check areas are covered: table/column presence,
  types and the `NaN` sentinel, primary keys, all eight foreign keys, source coverage and row
  counts, order-price and order-total reconciliation, the tax-not-added-twice check, temporal
  ordering, extracted references, and multilingual preservation.
- The checks are real, not decorative. I planted a blank `order_id` and VAL-SCHEMA-10 caught it.
- VAL-TEXT-14 and VAL-TEXT-15 are the strongest checks in the register: every extracted
  reference matches the review's own `order_id`, every extracted SKU matches its own product.
  Those test the extractor through referential integrity rather than through its own pattern.

## Four things to add

**1. The four SKIPs are the one real gap.** VAL-FLOW-09/10/11/12 are cross-source conflict
detection — the specification asks for it directly ("If your code detects different non-missing
values for the same target field and key, record the conflict in validation"), and it is the
reconciliation half of C2. Your reason for skipping is right: the checks need the combined frame
before deduplication, which only exists in the master notebook. So write the function now and
test it now, and let it run against the real frames at assembly.

```python
def find_conflicts(combined, key):
    """Keys where the two sources give different non-missing values for the same field."""
    shared = combined[combined.duplicated(key, keep=False)]
    out = []
    for field in shared.columns.drop([key, 'source_system']):
        n_values = shared.groupby(key)[field].nunique(dropna=True)
        for k in n_values[n_values > 1].index:
            out.append({'key': k, 'field': field})
    return pd.DataFrame(out, columns=['key', 'field'])
```

Tested against WP2's `combine_sources` + `mark_overlap`: **0 conflicts** on orders, order_items,
deliveries and product_reviews, and it catches a planted one. Count the overlap with
`combined.loc[combined.source_system == 'both', key].nunique()` — 500 orders, 1,559 order_items,
500 deliveries, 700 reviews. Do not use `(source_system == 'both').sum() / 2`; the within-source
duplicates make it read 513 and 721.

**2. VAL-ARITH-05 can never fail.** It is `record("VAL-ARITH-05", True, ...)` — it prints the
values but passes unconditionally. Compare against a set worked out from the source instead, the
same way every other check does.

While you are in that cell, the specification's fifth area is "allowed categorical values and
**sensible numeric ranges**", and the register has no range checks at all. Three lines covers it:
`rating` in 1..5, `quantity` at least 1, and no negative money or `helpful_votes`.

**3. Every `note` is empty and six markdown cells still say "Replace at G2".** Task 4 asks for
three things per check: observed result, PASS/FAIL, **and resolution or interpretation**. Two of
the three are done. One short paragraph per section — six paragraphs, not sixty — closes it. Say
what the section establishes and what would have made it fail.

**4. 63 of 63 PASS, with no failure anywhere.** Your own markdown says an all-green register is
not the goal, and it is right. The data genuinely is clean, so do not manufacture a failure —
instead show the checks have teeth. The planted-conflict demo in item 1 is one negative control;
a second cheap one is the tax formula: show that `order_price * 1.1 + delivery` matches 0 of
5,000 rows, which is what makes VAL-ARITH-04 mean something.

## Two small ones

- `register` is built in the last cell but never saved. Add
  `register.to_csv(OUTPUT_DIR / f"{GROUP_ID}_validation_register.csv", index=False)` so the
  report can cite `VAL-` IDs from a file rather than from a screenshot.
- VAL-TIME's 528 late deliveries are recorded as INFO rather than a check. That is the right
  call and worth one sentence in the interpretation — a business outcome is not a data defect.

## Order I would do it in

Items 2 and 3 today (an hour, and they are yours alone). Item 1 written and unit-tested today
against a small planted frame, then wired to the real frames when the master is assembled.
Item 4 falls out of item 1. That leaves G4 on Friday as a merge, not a build.
