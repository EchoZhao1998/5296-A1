# Task 1 handover — Echo → Jasmine, Shawn, Yandu

**What this is.** Section 1 of `wip_echo.ipynb` is finished. It gives you two parsers, four
normalisers, and the evidence behind six decisions you would otherwise each have to make alone.
Everything below is produced by a cell in that notebook — no number here is typed in by hand.

**How to use it.** Run `wip_echo.ipynb` top to bottom once (Restart and Run All, ~40 seconds).
After that you have `json_tables`, `xml_tables`, `KEYS`, `NORMALISERS` and `normalise()` in memory
and can lift the cells you need into your own notebook.

---

## Part 1 — Four facts that change how all of us work

Read these even if you skip the rest.

**1. Neither file is complete. The population is the union.**
Both files hold 2,750 distinct orders, but only 500 of them are the *same* orders. 1,300 reviews
in the JSON point at orders that exist only in the XML. Every foreign key resolves against the two
files pooled and fails against either one alone. So we combine first, then build.

**2. Duplicates are harmless.**
Every table repeats some keys within a single file — 68 orders, 201 or 214 items, 96 reviews.
Every repeat is exactly two copies, and the two copies are field-identical. Keeping one row needs
a *deterministic* rule, not a *justified* one.

**3. No source wins over the other.**
For all 3,259 keys that appear in both files, all 59 shared columns hold the same value once
normalised. Zero conflicts. There is no JSON-over-XML rule to argue about. (Compare *before*
normalising and you get 17 columns of fake conflicts — that is format, not disagreement.)

**4. Most of the work is renaming, not deriving.**
Of the 111 target fields in the data dictionary, **101 already exist as a source column**. Only
ten are derived, and all ten are text — they belong to Shawn.

---

## Part 2 — Jasmine: building the six tables

### Import from Section 1, don't rewrite

| What | Where |
|---|---|
| `parse_json()`, `parse_xml()` | §1.1, §1.2 — return flat DataFrames with dictionary column names and source-native values |
| `JSON_NAME_EXCEPTIONS`, `XML_NAME_EXCEPTIONS` | §1.1, §1.2 — the column renames the general rule gets wrong |
| `norm_money`, `norm_percent`, `norm_bool`, `norm_datetime` | §1.3b |
| `NORMALISERS`, `normalise()` | §1.3b — which normaliser applies to which column |
| `KEYS` | §1.3c — the six primary keys, with the scan that evidences them |

### Build in this order

Each step depends on the one before it. In particular, **normalise before deduplicating** — the
zero-conflict result in §1.3e only holds after normalisation.

```
1. parse both files          →  source-native values, dictionary column names
2. normalise per NORMALISERS →  the two sources become comparable
3. concat + drop_duplicates(key)  →  keep="first" is safe (see fact 3)
4. check the eight foreign keys   →  against the union, never one file
```

### Row counts your output must reproduce

| table | rows |
|---|---|
| orders | 5,000 |
| order_items | 15,685 |
| deliveries | 5,000 |
| customers | 500 |
| products | 1,000 |
| product_reviews | 7,000 |

These are **targets to hit, not constants to write down.** The spec bans hard-coding canonical
row counts. If your pipeline lands somewhere else, one of us is wrong and we should find out
which before the gate.

### The arithmetic already reconciles — but recompute it anyway

I checked the published sequence against the values stored in the sources, on all 5,000 canonical
orders:

- `line_revenue = round(quantity × unit_price, 2)` — 0 mismatches of 15,685
- `order_price = round(Σ line_revenue, 2)` — 0 of 5,000
- `tax_amount = round(order_price / 11, 2)` — 0 of 5,000
- `order_total` — 0 outside the 0.01 tolerance

So the sources are internally consistent. Recompute anyway: the spec prescribes the sequence and
Yandu has to check it. About 93 orders land one cent off the stored value depending on where you
round — that is inside the 0.01 tolerance. Don't chase them.

**One trap.** `coupon_discount` is a **percentage** — its values are 0, 5, 10, 15, 20, 25. Step 4
is `order_price × (1 − d/100)`, not `order_price − d`. Treating it as dollars breaks 3,906 of the
5,000 orders and every one of them looks plausible.

### Other things that will bite

- **Identifiers stay strings.** `order_id` is `HORD` + six zero-padded digits. Casting to int
  destroys the padding and the spec bans it by name. Same for `customer_id`, `product_id`, and
  the postcode.
- **`coupon_code` is the only field with missing values anywhere** — 1,767 blanks in the JSON,
  1,770 in the XML. Everything else is fully populated in both files.
- **The `NaN` sentinel is the three literal characters**, not a pandas missing value, and only in
  string fields the dictionary prescribes it for. Never in a numeric or boolean column.
- **No helper columns in the six CSVs.** `source_system` is added by the parsers for tracing —
  drop it before writing.
- **`order_status` is `Completed` for every row in both files.** So "one row per completed order
  delivery" means one row per order, and `deliveries` and `orders` have the same 5,000 keys.

---

## Part 3 — Shawn: the text functions

### Your five input columns

The parsers leave the noisy narrative fields untouched and suffix them `_raw`, because each one
feeds a *cleaned* target field rather than becoming one:

| source column | in | feeds |
|---|---|---|
| `customer_note_raw` | orders (both files) | `customer_note_clean`, `promo_code` |
| `review_body_raw` | product_reviews (both files) | seven review fields, below |
| `product_description_raw` | products (XML only) | `product_description_clean` |

### The ten derived fields — all yours

- **orders:** `customer_note_clean`, `promo_code`
- **products:** `product_description_clean`
- **product_reviews:** `review_body_clean`, `review_body_latin_analysis`, `review_length_chars`,
  `review_word_count`, `contains_non_latin_script`, `extracted_order_reference`,
  `extracted_product_sku`

Nothing else in the dictionary needs deriving. That is the whole of the text scope.

### What is actually in the data

Counted on the canonical rows, so these are the volumes you will really see:

| pattern | review_body_raw (7,000) | customer_note_raw (5,000) | product_description_raw (1,000) |
|---|---|---|---|
| HTML tags | 7,000 | 5,000 | 1,000 |
| URLs | 7,000 | 5,000 | 1,000 |
| `Reference: … SKU: …` wrapper | 7,000 | — | — |
| `[SYSTEM]` | — | 5,000 | — |
| `[CATALOGUE]` | — | — | 1,000 |
| `[VERIFIED_PURCHASE]` | 3,500 | — | — |
| `[SOURCE: …]` | 2,333 | — | — |
| `[RATING: n/5]` | 1,167 | — | — |
| `#verified-buyer` | 1,167 | — | — |
| `@store_support` | 1,166 | — | — |
| HTML entities | 1,167 | — | — |
| `PROMO:` + code | — | 1,873 | — |
| non-ASCII characters | 7,000 | 0 | 0 |

Two things to notice. **The markers are field-specific in this data but your functions must not
be** — the spec says private tests may use any of the published patterns anywhere, so
`clean_narrative_text()` handles the whole set regardless of which field it is called on. And
**`PROMO:` appears only in customer notes, never in reviews** — while `Reference:`/`SKU:` appear
only in reviews. So `extract_promo_code()` will return `NaN` for every review, and that is correct,
not a bug.

### Contract points worth re-reading

- `review_body_latin_analysis` is built **from `review_body_clean`**, not from the raw review.
- `contains_non_latin_script` is about *script*, not about ASCII. Every one of the 7,000 raw
  reviews contains a non-ASCII character (emoji, `©`, curly quotes) but only a minority are
  non-Latin. `language_code` on the canonical reviews: `en` 6,350, then `ru` 62, `pl` 58, `de` 58,
  `zh` 56, `ja` 56, `fr` 55, `nl` 53, `es` 53, `it` 52, `pt` 50, `hi` 49, `ar` 48.
- Do **not** infer `language_code` from your Latin-analysis field — it is a structured source
  column and it is already populated in both files.
- When `review_body_clean` is the literal `NaN`, `review_length_chars` and `review_word_count`
  must not count those three letters as a review.
- The six functions live in `Group001_text_functions.py`, take one argument, and do no file or
  network I/O — the markers will import and test them without our notebook.

---

## Part 4 — Yandu: what Section 1 gives your validation

Your checks should reproduce these independently, not read them from here:

- **Primary keys** — the six in `KEYS`; the scan in §1.3c shows they are the only unique
  candidates, and shows `source_system_record_id` is `order_id` re-encoded, not a second identity.
- **Foreign keys** — `parent_pools()` and `foreign_keys()` in §1.3d check all sixteen candidate
  child columns. Zero unmatched against the union. Reuse the functions; the trap they avoid is
  pooling every `_id` column, which makes each check pass against itself.
- **Source coverage** — the overlap table in §1.3d is your before/after row-flow denominator.
- **Overlap handling** — §1.3e is the evidence that no field-level conflict exists. If your run
  ever finds one, it gets recorded, not silently resolved.
- **Assumptions** — §1.3f is an eight-row register (A1–A8) with the evidence cell for each and
  what breaks if it is wrong. Cite those IDs rather than restating them.

---

## What is not done yet

- **The source-to-target mapping CSV** (111 rows, six blank columns). I curate it; each of us
  writes the rows for our own fields. Opens at the first gate.
- **§1.3e onward is evidenced but the EDA report text is not written.**

Questions about anything above: ask me before working around it. If a number here disagrees with
what your own code produces, that is worth ten minutes of all four of us.

— Echo
