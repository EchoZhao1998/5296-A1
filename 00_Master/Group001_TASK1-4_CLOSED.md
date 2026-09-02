# Tasks 1–4 — current state, 2 September 2026

"bababa" previous one was over-engineered, 
now removed the parts that were not evidence for a
specification requirement, 
folded in Jasmine's and Yandu's revisions, 
and re-ran everything. **No exported value changed.**

## What the notebook is now

`Group001_solution.ipynb` — **91 cells, 61 code**, runs Restart-and-Run-All from a
fresh kernel in about 30 seconds with 0 errors, and writes all eight files.

| | |
|---|---|
| Six standardised CSVs + mapping | byte-identical (sha256) to the set we validated on 1 Sep |
| Validation register | **67 checks, 67 PASS, 0 FAIL, 0 NOT RUN** |
| Mapping | 111 rows, no blank and no placeholder in any of the nine columns |
| Text functions | **44 / 44** cases pass (18 public + 26 our own) |
| Tested on | pandas 2.3.3 and 3.0.2 — identical bytes |
| Absolute paths | none, in any cell or in any stored output |

`Group001_solution.py` is regenerated from the notebook, and was run from a
different working directory to confirm it reproduces the same eight files.

## What was cut, and why

Everything cut was work the notebook did **twice**, not evidence the marker wants.

1. **The normalisation plan was built three times** — by hand in Section 1.3,
   cross-checked against the dictionary, then derived from the dictionary again in
   Section 4.0. It is now derived **once**, in Section 1.3, and Section 4 applies
   that same plan. This is also the honest version: the plan is read from
   `public_data_dictionary.csv`, never typed out.
2. **The money / percent / boolean / date normalisers were defined twice** (once in
   each of those places). Now once.
3. **The target contract was printed three times** in Section 4.0. Now once, as the
   full per-table table, which is the part that is actual evidence.
4. Teaching comments left in Section 1 about how f-string padding works.
5. `VAL-FLOW-11`, Yandu's planted-conflict fixture. It proved the conflict detector
   fires, which is good practice, but the specification asks for the overlap result,
   not a negative control — and `VAL-FLOW-09/10/12` already report it on the real
   data. That is why the register is 67 and not 68.

## What was merged in from your revisions

- **Shawn / text functions.** The refactor into one shared `_extract_reference`
  helper is in. It was checked against 78,442 real string values from both raw files
  plus a boundary set (`HORD1234567`, `xHORD123456`, `SKU-`, `B6SAVE-24`, Devanagari
  digits, …): **behaviour is identical to the previous version on every one**, in
  25 fewer lines. `matework/` and `00_Master/` now hold the same file.
- **Yandu / VAL-TEXT-08.** Your extra arm is in — the flag must be `False` on
  reviews that contain non-ASCII characters but no non-Latin letter. It is derived
  rather than driven by a language list, so it now reads *0 of 430 accented-Latin
  reviews wrongly flagged*. This is the check for the specification sentence "a
  non-ASCII character is not automatically non-Latin".
- Where your notebook and the master differ elsewhere (Sections 6.1, 6.3, 6.5), the
  master version is kept, because it derives its expected values from the dictionary
  or the raw files instead of naming them. `VAL-TIME-04` is the clearest example:
  yours asserted `years == [2018]`, the master compares the exported years against
  the years actually present in both raw files. The specification says not to write
  an assertion that only confirms a hard-coded answer.
- **Jasmine / Section 4.** Nothing was missing — every difference between
  `wip_jasmine.ipynb` and the master is the master already being ahead (the export
  cell now pins LF line endings, refuses to write unless the published text
  functions are the ones imported, and reads each file back to compare it against
  the frame Section 6 validated).

## On the normalisation plan — whose version survived

Both. The record is `wip_jasmine.ipynb` cell 19, "bababa"

- **`percent` cannot be derived** and must stay — the dictionary describes the target
  type, not how each file spells it. `PERCENT_FIELDS = {'coupon_discount'}` is still
  there, and the mapping row still says so.
- **`date` and `datetime` must stay apart** — they parse the same but export
  differently, and merging them appends `00:00:00` to the five `date` fields. The plan
  still prints them as separate categories.

So the mechanism is Jasmine's `normalisation_plan()`, reading `data_type` and
`comparison_rule` from the dictionary, carrying the two facts no dictionary scan can
recover. What was deleted was the *hand-typed second copy* of the same map and the cell
that asserted the two routes agree — with one route left there is nothing to
cross-check, and that was the clearest case of the notebook doing the same work twice.
The source-format evidence Task 1 asks for is untouched: Sections 1.2 and 1.3 still
print `'AUD 2,765.47'` against `2765.47`, `'10%'`, `Y`/`N` and the day-first dates side
by side, and the before/after table still shows 7 conflicting columns going to 0.

## Line lengths, for reading on a laptop

Three of us work on 13-inch Macs, so long lines were wrapped. **Nothing but whitespace
moved** — every re-split f-string joins to the same characters, and all eight files are
still byte-identical.

| | longest line | before |
|---|---|---|
| `Group001_solution.ipynb` (code) | 98 | 119 |
| `Group001_text_functions.py` | 95 | 127 |
| `Group001_solution.py` | 98 | 119 |

The worst offender was the `clean_narrative_text` block, where eight `re.sub` calls were
padded out to 127 characters to line up the `" ", text` column. One call per line now,
each with its own short comment. The only lines still over 96 are eleven prose strings
in Section 2.3 at 97–98 characters — those strings become the mapping CSV's
`transformation_or_derivation` column, so they were left alone rather than risk the
bytes for one character of width.

## Two defects fixed while we were in there

- The validation register was written without a fixed line terminator, so a run on
  Windows would have written CRLF and then failed Section 8's own check. Pinned.
- The `### 4.0 Shared transformation rules` heading sat *after* all the 4.0 code.
  Moved to where it belongs — it is also the cell that explains why 4.2 runs before
  4.1 (`order_price` is the sum of the rounded line revenues).

## Running it in Colab from the shared drive

The notebook now has a first cell that does nothing at all off Colab. Opened in Colab it
mounts Drive, **finds** the allocated package by searching `MyDrive` for
`Group001_commerce.json` rather than having anyone's folder path typed into it, moves into
`00_Master/`, and writes the eight files into `00_Master/outputs/` on the drive. It stops
with a clear message rather than guessing if the drive holds two copies of the package.

Tested against a copy of our drive layout (`5196/Group001_A1/` with `DATA/`, `00_Master/`,
`02_Outputs/`) and against the two layouts a marker might use — package kept whole, and the
submission unzipped flat. **All three produce the identical eight files**, and the Colab run
leaves nothing behind in the session folder.

So the shared CSVs will be a set the pipeline produced on the drive, not a set uploaded by
hand. Please still run your own review copy on your own machine and check it against
`review/Group001_outputs.sha256` — that is what makes "I ran it" a fact.

## What this means for you

Nothing you have to redo. Tasks 1–4 are closed and the outputs are unchanged, so
any figure already built on `outputs/` is still correct.

**Only one person runs the solution notebook.** The EDA notebook reads the six CSVs
and nothing else — see `review/Group001_HOW_TO_REVIEW.md`. Read your own section
and one you did not write, so all four of us can explain the whole thing.

The marks that are still open are the EDA, the ten findings and the five ML
questions. That is where the remaining time goes.
