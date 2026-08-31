# WP1 review of `Group001_text_functions.py` and `wip_jasmine.ipynb`

**From** Echo (WP1) · **Date** 31 Aug 2026 · **Reviewing** Shawn's text module (29 Aug fix) and
Jasmine's notebook re-run with the real functions loaded
**Verdict** G2 passes on behaviour. Re-checked 31 Aug with every fix below applied: the six
CSVs are still byte-identical and no cell raises.

**Verdict (original)** G2 passes on behaviour. The six tables are now built from real text output and I
reproduced them byte-for-byte. Three near-match defects in the extractors and four notebook
issues below; a tested patch for all three defects is at the end and it changes none of our
current numbers.

---

## How this was checked

The notebook was copied to a scratch folder with the module beside it and run from a fresh
kernel, start to finish, on pandas 2.3.3. The six CSVs it wrote were then compared cell by cell
against the six already committed in `matework/outputs_wip_jasmine/` — **identical on all six
tables**. So the committed files are a real run, not the placeholder run that caught us on
29 August, and WP3 can safely build the validation register on them.

Every derived text field was then re-derived a second way, from the raw JSON and XML, without
reusing any code from either the module or the notebook.

## What is confirmed correct

| Check | Result |
|---|---|
| Public text cases | 18 of 18 pass |
| Placeholder guard | `WP4 placeholders in use: False`; 0 all-sentinel columns |
| Cleaning residue, all 14,656 narrative values | no surviving tag, URL, marker, entity, `Reference:`, `SKU:`, `PROMO:`, `#verified-buyer`, `@store_support` or emoji |
| Cleaning is idempotent | cleaning a cleaned value changes nothing, on every value |
| Emoji vs symbols | the So-only narrowing works: `$`, `+`, `%`, `=`, `±`, `÷` survive, emoji do not |
| `promo_code` | 1,873 of 5,000, re-derived straight from both raw files keyed by order id — **0 rows disagree**, and 0 order ids conflict between the two sources |
| `extracted_order_reference` | 7,000 of 7,000 resolve to a real `orders.order_id`, and every one equals the review's **own** `order_id` |
| `extracted_product_sku` | 7,000 of 7,000 resolve to a real `products.product_sku`, and every one equals the SKU of the review's **own** `product_id` |
| `contains_non_latin_script` | agrees with the structured `language_code` on **7,000 of 7,000** rows: every ar/hi/ja/ru/zh review True, every Latin-script language False, no exceptions |
| `review_length_chars` / `review_word_count` | recomputed from `review_body_clean`: exact match on all 7,000 |
| `review_body_latin_analysis` | built from the clean field, not the raw one, as the spec requires |
| Multilingual preservation | 271 non-Latin reviews kept intact in `review_body_clean`; none erased |
| Missing-value handling | `None`, `float('nan')`, non-strings, blanks and the literal `NaN` all return `NaN` |

**The two strongest pieces of evidence are the ones that pass through nobody's regex.** The
coupon cross-check (structured `coupon_code` and the extracted `promo_code` agree on all 1,873
populated rows, neither ever populated alone) and the language cross-check (`contains_non_latin_script`
against `language_code`, 7,000 for 7,000). Cite both in the mapping rows and in the report —
every other text check tests the output against the pattern that produced it.

**On the cleaning being more aggressive than the README.** It is, and it is right. The README
names only three markers; the specification's Task 3 publishes the *complete closed set* —
`[SYSTEM]`, `[CATALOGUE]`, `[VERIFIED_PURCHASE]`, `[SOURCE: ...]`, `[RATING: n/5]`,
`#verified-buyer`, `@store_support` — and its steps 6 and 7 require removing the whole
`Reference: ... SKU: ...` wrapper and `PROMO:` with its code. Shawn implements the
specification. Nothing to change; worth one sentence in the mapping rows so a marker sees we
read past the README.

**On the step order.** The module runs the removals in a different order from the
specification's steps 5-7 (PROMO before the reference wrapper, social markers and emoji after
both). The patterns do not overlap, so the result is the same — confirmed by the zero-residue
and idempotence checks. No behaviour change is needed, but reordering the seven `re.sub` calls
to match the published 1-9 list costs nothing and removes an argument a marker could make.

---

## Three defects in the extractors

All three are near-match handling. The specification is explicit: *"a longer, malformed or
embedded near-match must not be accepted as a valid reference"*, and the published formats are
ASCII. None of the three affects a single row of our current data — they are what a private
test would probe.

**WP4-1 — the boundary rule is not the same in all three extractors.**
`extract_product_sku` and `extract_promo_code` reject a neighbouring `-` or `_`;
`extract_order_reference` does not.

```
extract_order_reference('ORDER-HORD001451')  ->  'HORD001451'   should be NaN
extract_order_reference('ref_HORD001451')    ->  'HORD001451'   should be NaN
```

**WP4-2 — `\d` and `[A-Z]` are Unicode, so other-script look-alikes are accepted.**
This matters precisely because the reviews are multilingual.

```
extract_order_reference('HORD१२३४५६')  ->  'HORD१२३४५६'   should be NaN  (Devanagari digits)
extract_product_sku('SKU-VEſ00')        ->  'SKU-VES00'    should be NaN  (long s, U+017F, folds to s under IGNORECASE)
```

**WP4-3 — a malformed SKU is silently truncated rather than rejected.**

```
extract_product_sku('SKU-VEL१२३')  ->  'SKU-VEL'   should be NaN
```

### The patch, tested

The three functions differ only in their pattern, so the boundary rule and the ASCII check move
into one shared helper and cannot drift apart again. This replaces the three extractor bodies;
nothing else in the module changes.

```python
def _extract_reference(value, pattern):
    """Search for one bounded business reference and return it in upper case.

    The three extractors differ only in their pattern, so the boundary rule and
    the ASCII check live here and cannot drift apart between them.
    """
    if _missing(value):
        return NAN

    # A reference must stand alone: no letter, digit, underscore or hyphen may
    # touch either end, so a longer or embedded near-match is rejected.
    match = re.search(r"(?<![\w-])" + pattern + r"(?![\w-])", value, flags=re.IGNORECASE)
    if match is None:
        return NAN

    # The published formats are ASCII. A look-alike built from other-script
    # digits or letters is a near-match, not a reference.
    token = match.group(0)
    return token.upper() if token.isascii() else NAN


def extract_order_reference(value):
    """Extract a valid HORD/CORD order reference from raw text."""
    return _extract_reference(value, r"[HC]ORD\d{6}")


def extract_product_sku(value):
    """Extract a valid product SKU from raw text."""
    return _extract_reference(value, r"SKU-[A-Z0-9]+")


def extract_promo_code(value):
    """Extract a valid promotion code from raw text."""
    return _extract_reference(value, r"B[1-5]SAVE-\d{2}")
```

Verified with the patch applied: **18 of 18 public cases pass, 26 of 26 of our own cases pass,
and every extracted value on the real data is unchanged** — so the six CSVs do not move and
nobody downstream has to re-run for this. Keep the bilingual docstrings; they were trimmed above
only to keep the diff readable.

**WP4-4 — the `__main__` self-test cannot find the cases on my layout.** It looks in
`Admin/templates/`, which exists only under `echo_branch/`. Running the module from `matework/`
raises `FileNotFoundError`. Use the same first-existing-candidate pattern the notebook already
uses for `INPUT_CANDIDATES`, and add the second file below to the same runner.

## Your own edge cases for G2

G2 asks for at least 12 of our own alongside the 18 public. I wrote 26 while checking and left
them in `matework/Group001_own_text_test_cases.csv`, same five columns as the public file so
one runner reads both. They cover matched, unmatched, missing, multilingual and near-match, as
the specification asks. Against the module as it stands today, 23 pass and OWN-14, OWN-15 and
OWN-18 fail — those three are exactly WP4-1, WP4-2 and WP4-3, so the file doubles as the
regression test for the patch. Take them over, add or cut as you see fit; the evidence is yours
to present.

---

## Four issues in the notebook

**NB-1 — the last cell raises.** `KeyError: 'delivery_note_raw'`. The cell asks whether
`delivery_note_clean` is narrative text or a closed set, but DEC-021 settled that as a direct
copy, so no `_raw` column is built any more. It is the only failing cell in the notebook. A
Restart-and-Run-All that ends in a traceback is not a handover — delete the cell, or point it at
`deliveries_marked['delivery_note_clean']` and keep it as the evidence for DEC-021.

**NB-2 — the raw-byte diagnostic still prints all zeros.** I flagged this on 28 August and it is
unchanged. The cell searches for `b'promo'`, `b'customer_note'` and so on against bytes that
spell `PROMO:`, `customerNote` and `Customer_Note`, so every count is 0 and the cell proves
nothing. Lower-case the blob first and it becomes the strongest line in the section: `promo`
appears 1,051 times in the JSON and 1,048 in the XML, matching the populated `Coupon_Code`
elements exactly, with `promo_code` and `promocode` genuinely at 0.

```python
blob = path.read_bytes().lower()
```

**NB-3 — the B1/B2 self-check prose is now stale.** It prints "B2 equal-weight mean ceiling
before WP4 lands: 92.20%" whether or not WP4 has landed, because `wp4_pending` counts a fixed
`WP4_DERIVED` set instead of asking what is actually sentinel. With the real functions loaded
the ceiling is 100%. Gate it on `WP4_PLACEHOLDER` so the number and the sentence agree — this is
the same class of error as the VAL-TEXT-13 wording, and that one is now genuinely true: 1,873
rows carry both, 0 disagree.

**NB-4 — DEC-022 is still not implemented.** §7 writes the six CSVs unconditionally. It did no
harm this time because the module was present, but the whole point of DEC-022 is the run where
it is not. Two lines at the top of the export cell:

```python
OUTPUT_DIR = Path('outputs_wip_jasmine') / ('provisional' if WP4_PLACEHOLDER else '')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
```

**One latent defect worth two lines.** The specification says that when `review_body_clean` is
the literal `NaN`, the measures must "preserve the published sentinel behaviour rather than
counting the three letters as an ordinary review". §4.6 computes `clean.str.len()` and
`clean.str.split().str.len()`, which would give 3 and 1. No review in our data cleans to `NaN`,
so no row is affected — but a private test or a marker's re-run could produce one, and the fix
is cheap:

```python
is_sentinel = clean.eq('NaN')
deduped['review_length_chars'] = clean.str.len().mask(is_sentinel, 0)
deduped['review_word_count']   = clean.str.split().str.len().mask(is_sentinel, 0)
```

Agree the sentinel value as a group before shipping it — 0 is the reading I would defend, but it
is a decision, so it should get a `DEC-` row rather than appear in code.

**One judgement call to note, not to fix.** `build_latin_analysis` keeps non-Latin *punctuation*
— a Chinese review comes back as `candle edge 716 ， 。 ， 。`. The specification says the field
retains Latin letters "together with applicable digits and punctuation" and only requires
non-Latin *letters* to be removed, so the current behaviour is defensible and I would leave it.
Say so in one sentence in the mapping row, so it reads as a decision rather than an oversight.

**NB-5 — the new `delivery_note_clean` mapping entry is written as a tuple, not a sentence.**
Every other value in that dict is a plain string; this one is `(text, '§4.4')`, so the exported
`transformation_or_derivation` cell literally reads
`"('Direct copy from the source column of the same name. ...', '§4.4')"` — brackets, quotes and
all. The `§4.4` was meant for the evidence column, which is filled from `SECTION` anyway. Drop
the outer parentheses and the trailing `, '§4.4'`.

This also means **the committed `outputs_wip_jasmine/Group001_mapping_wp2_rows.csv` is stale**:
it still carries `TODO-SHAWN` on that row, so it has 11 TODO rows where the current notebook
produces 10. Re-export it with the fix before I merge — §2.4 of my notebook joins on
`(output_table, target_field)` and would carry the tuple text straight into the deliverable.

---

## What is still outstanding for G2 / G3

- Shawn: the patch above, the two test files shown running in the notebook, and the 10 mapping
  rows (`transformation_or_derivation` + `notebook_evidence`) — DEC-021 keeps it at 10, not 11.
- Jasmine: NB-1 to NB-4, then a fresh-kernel Restart-and-Run-All. The tables themselves need no
  further work.
