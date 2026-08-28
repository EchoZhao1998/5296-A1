# WP1 review of `wip_jasmine_0829.ipynb`

**From** Echo (WP1) · **Date** 28 Aug 2026 · **Reviewing** the combined WP2 + WP4 notebook
**Verdict** The six tables are correct. Nine issues below; one needs a group decision, the
rest are prose or housekeeping.

---

## How this was checked

Every code cell was extracted and run against the real JSON and XML outside the notebook, on
pandas 2.3.3 (the stored run is 2.2.3). All cells executed and every assert passed. The numbers
were then re-derived a second way, without reusing any of the notebook's own code.

Shawn's `Group001_text_functions.py` is not in this folder, so the local run used the
placeholder branch. Everything below that depends on the real functions is read from the stored
Colab outputs instead.

## What is confirmed correct

| Check | Result |
|---|---|
| Row counts | 5,000 · 15,685 · 500 · 5,000 · 1,000 · 7,000 — equal to the union of business keys, derived not written in |
| Primary keys | unique and non-blank on all six tables |
| Field order | matches the dictionary's `position` on all six; no helper column survives export |
| Foreign keys | all eight resolve with zero orphans |
| `line_revenue` | recomputed independently: 0 of 15,685 differ, and they are *exactly* equal, not merely inside tolerance |
| `order_price` / `tax_amount` / `order_total` | 0 of 5,000 differ, exactly equal |
| Tax not added twice | a formula that adds tax again matches 0 of 5,000 rows |
| Discount is a percentage | read as dollars it matches 1,094 of 5,000, and 1,093 of those are the zero-discount rows |
| Formats | dates `YYYY-MM-DD`, timestamps with time, booleans `True`/`False`, postcodes four characters, no empty cell anywhere in the six files |
| `delay_days` | equals `max(0, delivered − promised)` on 5,000 of 5,000; the raw difference matches only 2,015, which is where the 2,985 false mismatches came from |
| `delivered_date` | runs past the period end, 76 rows, latest 2019-01-12 |
| `delay_reason == 'none'` | 4,472 — the correction to 2,516 is right |

**The promo cross-check stands up from a third direction.** Counting raw bytes, the XML carries a
populated `Coupon_Code` on 1,048 of its 2,818 orders and the `PROMO:` marker appears 1,048 times;
the JSON marker count is 1,051. So "structured coupon present" and "marker present in the note"
match before either the parser or the extractor touches them. That is independent of both WP2's
code and WP4's.

---

## 1 · `delivery_note_clean` — needs a group decision, not a preference

§4.4 now runs `clean_narrative_text` on this field. DEC-018 (23 Aug) says it is a direct copy.
One of the two has to be withdrawn.

The field holds exactly two values in both sources — `Carrier scan reconciled` and
`Delivered within promise`. No tags, markers, URLs, entities or non-ASCII. So cleaning it does
exactly one thing: it lower-cases it.

- The spec's normalisation list says *"preserve identifier leading zeros and do not lower-case
  identifiers or structured categories unless a field-specific rule requires it"*. No published
  rule designates this field.
- Step 8 of the text-processing order lower-cases *"the designated cleaned narrative"* — the
  designations in the spec are for the review body and the fields built from it.
- The argument the other way is consistency of the `_clean` suffix across four target fields.

**Recommendation: keep DEC-018 — direct copy.** The suffix is the source system's own field name
(it arrives as `deliveryNoteClean` / `Delivery_Note_Clean`), and the only observable effect of
cleaning is the one thing the spec names. Whoever decides, it needs a `DEC-` row, because it also
answers Jasmine's question: **the WP4 list is 10, not 11**, and this row stays with WP2.

## 2 · §4.3 markdown: "497 of 500 customers have orders"

At canonical scale all 500 do. 497 is the JSON-only figure; XML-only is 499. Same shape as the
`delay_reason` correction — a per-source number quoted as a canonical one. Worth a sweep of the
other markdown numbers for the same pattern.

## 3 · §4.6 length and word count don't implement the sentinel rule

`review_length_chars` and `review_word_count` are `clean.str.len()` and
`clean.str.split().str.len()`. The spec says that when `review_body_clean` is the literal `NaN`,
the published sentinel behaviour is preserved rather than counted — as written, a sentinel row
would report 3 characters and 1 word.

It does not bite on this data: no review cleans to the sentinel, which is also why the stored run
shows no `nullable = False` field carrying `'NaN'`. But the teaching team may test the pipeline
shape, so it is worth a two-line guard rather than a note.

## 4 · The raw-byte diagnostic reads backwards

The cell prints zero for `promo_code`, `customer_note`, `delivery_note` and `coupon_code` in both
files, which reads as "these fields are absent from the sources". It is case and spelling
sensitivity. Lower-cased:

| pattern | JSON | XML |
|---|---|---|
| `customernote` / `customer_note` | 2,818 | 5,636 |
| `delivery_note` | 0 | 5,636 |
| `couponcode` / `coupon_code` | 2,818 | 3,866 |
| `promo` | 1,051 | 1,048 |

The `promo` figure is the stronger version of the point the cell was reaching for: it gives WP4 an
expected marker count derived from the raw file rather than from its own regex. Either fix the
cell or drop it — as printed it argues against a fact that is true.

## 5 · The B2 ceiling self-check is stale

It counts the eleven WP4 fields as pending whatever `WP4_PLACEHOLDER` says, so a notebook that has
been re-run *with* the real functions still reports "91.37% before WP4 lands". Switch it on
`WP4_PLACEHOLDER`, the way the all-sentinel guard already does.

## 6 · Two monetary roundings bypass `money_round()`

§4.0.3 states that every monetary rounding goes through `money_round()`, then §4.2 uses
`(quantity * unit_price).round(2)` and §4.1 uses `.sum().round(2)`. I checked both: zero rows
differ on this data, so nothing is wrong in the output — but the notebook contradicts its own
stated rule in the two places the rule was written for.

## 7 · Housekeeping before anything moves to master

- the `globals()` scan prints notebook internals (`__`, `_21`, `_26`) alongside the real frames;
- the `verified_purchase` cell reads `combined`, which is whatever the last table built left
  behind — it works only in run order and says nothing if that changes;
- the WP2 mapping CSV is written twice, in two different cells;
- `"0 of 15,685 rows outside"` is a literal inside a code cell. Better as an f-string from the
  computed value, since hard-coded counts are named in the fail descriptors.

## 8 · Two small prose corrections

- §4.6 says `review_title` was checked across "all 7,892" — that is the concatenated count; the
  canonical figure is 7,000, of which 479 carry non-ASCII characters.
- §4.1 says the 640 dollar-reading matches "are exactly the rows where the discount is 0" —
  639 are, and one more matches by coincidence.

## 9 · The path candidate list misses one layout

`INPUT_CANDIDATES` covers the marker's folder and two Drive layouts but not
`Group001_A1/raw_input`, which is the repo-root layout. The notebook asserts and stops if run
from there. One extra line.

---

## Answers to the three questions addressed to WP1

**Do the WP1 path constants use the `_standardised` names?** Nothing to change. `wip_echo.ipynb`
writes one file, `Group001_source_to_target_mapping.csv`, which matches the specification. The
six CSV names live in the export cell, and that cell is already correct. Note for assembly: the
export section belongs to WP1 in the role plan, so that cell transfers as written.

**The regenerated `Group001_mapping_wp2_rows.csv`.** Diffed against the copy already merged —
identical, all 111 rows. No re-merge needed.

**`nullable = False` versus the `'NaN'` sentinel.** With the real functions loaded, no
`nullable = False` field carries the sentinel anywhere in the six tables. Both readings therefore
agree on this data, so adopt the stricter one as a check — assert that no `nullable = False` field
contains `'NaN'` — and the question closes as a decision rather than staying open.
