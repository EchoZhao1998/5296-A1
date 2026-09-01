# WP1 review of WP2 — `wip_jasmine.ipynb`, 1 September 2026

Reviewed against the 31 Aug version, the six exported CSVs, and the raw files.
Reviewer: Echo (WP1). Read with `Group001_wp1_review_of_wp2_0829.md`.

---

## 1. What was verified, and how

A fresh-kernel run of `wip_jasmine.ipynb` (all 42 code cells, text module beside it,
raw files from `Group001_A1/raw_input/`) reproduces **all seven committed files in
`outputs_wip_jasmine/` byte for byte**. Compared by sha256, not by eye:

```
3a299a08…  Group001_customers_standardised.csv
600bbaab…  Group001_deliveries_standardised.csv
19cd44de…  Group001_mapping_wp2_rows.csv
f5ec4765…  Group001_order_items_standardised.csv
2fe07080…  Group001_orders_standardised.csv
81294086…  Group001_product_reviews_standardised.csv
c81738a7…  Group001_products_standardised.csv
```

Not a placeholder run: `promo_code` carries 1,873 real values, `customer_note_clean`
is free of `[SYSTEM]`, no column is entirely sentinel. The six tables are safe for
WP3 and for EDA as they stand.

## 2. The `delivery_note_clean` change — all four claims confirmed

| Claim | Verified |
|---|---|
| Column reads `Delivered within promise` / `Carrier scan reconciled` | 4,472 / 528, source case kept |
| Cleaning changes all 5,000 rows and nothing but case | 5,000 changed; 0 changed ignoring case; still 2 distinct values after |
| `WP4_DERIVED` is 10, not 11 | 10 entries; exported mapping has exactly 10 `TODO-SHAWN` rows |
| The assert can't go stale | `assert is_wp4.sum() == len(WP4_DERIVED)` — yes |
| The mapping row carries a reason | plain string, not the tuple that was there on 31 Aug |

The print in §4.4 is the right call, and worth stating as a general rule: a field we
chose not to clean and a field we forgot look identical in the output. The print is
what makes the choice visible.

## 3. The consistency finding is stronger than reported

`delivery_note_clean` is not merely the same *split* as `delay_reason == 'none'`. It
is the same partition as **three** other columns, row for row, with zero
disagreements on all 5,000 deliveries:

```
                          Delivered within promise   Carrier scan reconciled
delay_reason == 'none'                       4,472                         0
                                                 0                       528
```

- `delay_reason == 'none'`      — 0 rows disagree
- `on_time_in_full == True`     — 0 rows disagree
- `delay_days == 0`             — 0 rows disagree
- `delivered_date <= promised_date` — 0 rows disagree (WP3's §6.5 already prints 528)

The 528 break down as `warehouse_congestion` 185, `weather` 177,
`carrier_capacity` 166 — so the note carries **no information the delivery outcome
columns do not already carry**. Two consequences:

1. **For WP3.** This is a real cross-field consistency check with teeth, not a
   restatement: four independently produced columns agreeing on the same 5,000-row
   partition would break loudly if any one of them were mis-parsed.
2. **For the report and the ML question.** It is a textbook redundant feature — it
   would leak the delivery outcome into any model predicting lateness. Worth one
   sentence in the findings; it is the kind of observation F3 and G1 reward.

## 4. Still open from 31 Aug

**A. The raw-byte diagnostic does not run.** This is the one cell that fails, and it
is why "Restart and Run All, all good" is not what the saved file records. The
lower-casing fix went in, but with the indentation broken:

```
for path in (JSON_PATH, XML_PATH):
      blob = path.read_bytes().lower()     <- 6 spaces
    print(path.name)                       <- 4 spaces
```

`IndentationError` at parse time, so the cell produces nothing. (The stored execution
counts tell the same story: 1–42 in order, then 43 and 45 as one-off re-runs, and the
config cell shows no count at all.)

Tested replacement — the JSON spells these keys in camelCase, so both spellings have
to be in the list or the JSON column stays misleadingly at zero:

```python
# Diagnostic only: an existence count on the raw bytes. This is NOT structural
# parsing — it never decides field boundaries, it only answers "does this key
# appear in the source at all". Lower-cased, because the two files disagree on
# spelling: the JSON writes couponCode, the XML writes Coupon_Code.
for path in (JSON_PATH, XML_PATH):
    blob = path.read_bytes().lower()
    print(path.name)
    for key in (b'promo', b'coupon_code', b'couponcode',
                b'customer_note', b'customernote'):
        print(f'   {key.decode():<16} {blob.count(key):>8}')
```

Prints (verified):

```
Group001_commerce.json          Group001_operations.xml
   promo            1051           promo            1048
   coupon_code         0           coupon_code      3866
   couponcode       2818           couponcode          0
   customer_note       0           customer_note    5636
   customernote     2818           customernote        0
```

Three things fall out of that, and none of them comes from our own parser:

- `promo` 1,051 / 1,048 is the `PROMO:` marker inside the customer note, so Shawn has
  an expected extraction count from the raw bytes rather than from his own pattern.
- The camelCase / snake_case split is now visible in the output instead of hidden in a
  column of zeros — which is the point the diagnostic was reaching for.
- `Coupon_Code` appears 3,866 times over 2,818 XML orders. A populated element writes
  an open and a close tag, an empty one is self-closing, so 2p + (2818 - p) = 3866
  gives **p = 1,048 populated coupon codes**. Counted directly: `<Coupon_Code>` 1,048,
  `<Coupon_Code />` 1,770. That is the 1,048 / 1,770 split we already have from the
  parsed frame — and it is also, exactly, the number of `promo` markers in the same
  file. The JSON says the same thing with its own numbers: 1,051 markers, 1,051
  populated codes (2,818 − 1,767 blank). **In each file separately, every populated
  coupon code has a promotion marker in its customer note and no marker exists
  without one** — which is what makes VAL-TEXT-13 a real test of Shawn's extractor
  rather than a comparison of two parses of the same column.

**B. The B1/B2 self-check now understates our own work.** It still prints
*"before WP4 lands: 92.20%"* with WP4 loaded and every field populated. `wp4_pending`
counts a static set instead of asking what is actually unfilled. Asked properly, the
answer is **100.00% on all six tables** — nothing is a placeholder column, and the
only sentinel-bearing fields are `coupon_code` / `promo_code` at the same 3,127 rows,
which is a genuine absence of a promotion, not a gap.

Also, the citation is wrong: the thresholds are in the rubric's performance-standard
table under **B1 and B2**, not "section 4.2". The numbers themselves are right —
B1 HD is 95.00–100% equal-weight mean key coverage, D is 90.00% to below 95.00%; B2
HD is 95.00–100% certified field-value accuracy. Worth getting right, because a
misquoted rubric reference in a submitted notebook is read as carelessness.

Tested replacement:

```python
# --- B1/B2 self-check: ask the exported files what is filled in, don't count a list ---
rows = []
for t in OUTPUT_TABLES:
    df, c = globals()[f'{t}_final'], CONTRACT[t]
    pk, fields = c['pk'], c['fields']
    # A field is unfilled only if it is the sentinel (or blank) on every single row.
    unfilled = [f for f in fields
                if (df[f].astype(str) == 'NaN').all() or (df[f].astype(str) == '').all()]
    rows.append({'table': t, 'rows': len(df), 'fields': len(fields),
                 'pk_unique': df[pk].is_unique,
                 'pk_complete': (df[pk].astype(str).str.strip() != '').all(),
                 'grain_holds': len(df) == df[pk].nunique(),
                 'unfilled': len(unfilled),
                 'coverage': (len(fields) - len(unfilled)) / len(fields)})

b = pd.DataFrame(rows)
print(b.to_string(index=False))
print(f"\nequal-weight mean field coverage: {b['coverage'].mean():.2%}")
print("Sentinel is not the same as unfilled: coupon_code and promo_code carry it on")
print("the same 3,127 orders, which is an absent promotion, not a missing value.")
```

**C. DEC-022 is still not implemented.** §7 writes the six CSVs unconditionally. Two
lines is enough — gate the write on `WP4_PLACEHOLDER`, or send it to `provisional/`.
This is the decision that exists because a placeholder run once overwrote the shared
folder, and it is an E1/E2 point, not housekeeping.

## 5. Two small things for the master merge, not for now

- The §4.4 code comment ends `... (DEC-018).` and the §4.4 markdown addresses
  `→ YANDU` by name. Both are right for a WIP file and both have to go before the
  master: notebook prose has to stand on its own for a marker who has never seen our
  decision log.
- The exported mapping row for `deliveries.delivery_note_clean` also ends `(DEC-018)`.
  That one is deliverable-facing. Either the decision log is submitted alongside and
  the reference resolves, or the row should carry the reason without the code — the
  reason is already written out in full, so dropping the four characters costs
  nothing.

## 6. Nothing downstream needs to re-run

Byte-identical output means WP3's register and the EDA can keep working against the
files already in `outputs_wip_jasmine/`. Fixing A, B and C above changes no exported
value — A and B are diagnostics, C is a guard.
