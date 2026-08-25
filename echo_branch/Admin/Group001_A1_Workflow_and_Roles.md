# FIT5196 A1 — Group001 Workflow & Role Plan

**Members:** Echo · Jasmine · Yandu · Shawn
**Due:** 23:55 Thursday 10 September 2026 · **Weight:** 15% · **Target:** HD (≥12.0 / 15)
**Prepared:** 20 August 2026 — 21 days to deadline

---

## 0. Why this plan looks like this

The rubric awards marks for *demonstration*, not for effort. Seven criteria (A–G) carry
fixed marks, and two of them (B and F, 6.5 of 15) are where groups usually lose HD. So the
plan does three things:

1. **Ownership maps 1:1 onto rubric criteria** — every criterion has exactly one name against it.
2. **Every artefact passes through a second pair of eyes** before it counts as done.
3. **All four rebuild the shared fact base themselves in week 0**, so nobody is a passenger.

---

## 1. Shared fact base

Everyone should be able to state these numbers from memory by the end of week 0. Derive them
yourself in code — **never hard-code them into the pipeline** (the spec forbids it, and the
rubric penalises hard-coded canonical counts under C1 and E1).

### 1.1 What the two sources actually contain

| Entity | JSON (`CommercePlatform`) | XML (`OperationsERP`) | Canonical (union) |
|---|---|---|---|
| Orders | 2,818 rows → 2,750 unique | 2,818 rows → 2,750 unique | **5,000** |
| Order items | 8,826 rows → 8,625 unique | 8,833 rows → 8,619 unique | **15,685** |
| Deliveries | 1 per order, nested | 1 per order, nested | **5,000** (all orders are `Completed`) |
| Customers | 500 | *absent* | **500** |
| Products | *absent* | 1,000 | **1,000** |
| Reviews | 3,946 rows → 3,850 unique | 3,946 rows → 3,850 unique | **7,000** |

**Duplication shape** — two distinct problems, both must be demonstrated (rubric C1):

- **Within-source duplicates:** 68 order IDs and 96 review IDs repeat *inside each file* —
  the same counts in both JSON and XML. Verified: every repeated record is field-identical
  to its twin, nested carts and deliveries included. (One XML review pair differs only in
  trailing whitespace outside the element — a serialisation artefact, not a data difference.
  Your comparison should be on parsed values, not raw strings, which is exactly why the spec
  bans regex on document structure.)
- **Cross-source overlap:** 500 order IDs and 700 review IDs appear in *both* files.
  Verified on every comparable field — timestamps, money, discounts, booleans, IDs, ratings,
  raw review text — after applying the published normalisation rules: zero disagreements.
  This is why the spec says no JSON-over-XML precedence rule is needed. Your code must still
  *detect and report* conflicts (rubric C2), not assume none exist.

### 1.2 Structure

```
JSON                                 XML
root                                 OperationsExport (@groupAlias @sourceSystem @period)
├── exportMetadata                   ├── Export_Metadata
├── customerProfiles[500]            ├── Orders/Order[2818]
├── orders[2818]                     │   ├── Header
│   ├── header                       │   ├── Shopping_Cart/Item[*]
│   ├── shoppingCart[*]              │   └── Delivery
│   └── delivery                     ├── ProductCatalogue/Product[1000]
└── productReviews[3946]             ├── ProductReviews/Review[3946]
                                     └── WarehouseDirectory/Warehouse[3]
```

`WarehouseDirectory` (3 warehouses with lat/long) maps to no required output field — it is
useful for EDA (distance sanity checks) but must not be added as a column to the six CSVs.

### 1.3 Format conventions per source

| Concern | JSON | XML | Target |
|---|---|---|---|
| Dates | `2019-01-08` | `08/01/2019` (**DD/MM/YYYY** — confirmed, day component reaches 31) | `YYYY-MM-DD` |
| Timestamps | `2018-12-31 13:52:00` | `02/11/2018 08:50:00` | `YYYY-MM-DD HH:MM:SS` |
| Booleans | native `true` / `false` | `Y` / `N` | `True` / `False` |
| Currency | native float `1189.23` | `AUD 2,765.47` | number, tolerance 0.01 |
| Percent | native int `10` | `10%` | number `10` (percentage points) |
| Empty coupon | `""` | `<Coupon_Code />` | literal `NaN` |
| Markers in narrative | `[SYSTEM]`, `[SOURCE: …]`, `[CATALOGUE]`, `[VERIFIED_PURCHASE]` | same, HTML-entity-encoded | stripped |

### 1.4 Arithmetic — already internally consistent

Recomputing `line_revenue`, `order_price`, `tax_amount` and `order_total` with the published
sequence reproduces the source values exactly across all 2,818 JSON orders (0 mismatches at
0.01 tolerance). **Still derive them in code** — the rubric marks the derivation (B3), and
your validation checks (E1) should confirm agreement rather than assume it.

The published sequence, in order, no shortcuts:
1. `line_revenue = round(quantity * unit_price, 2)`
2. `order_price = round(sum(line_revenue), 2)`
3. `tax_amount = round(order_price / 11, 2)` ← GST-inclusive, computed **before** discount
4. apply `coupon_discount` to `order_price`
5. add `delivery_charges`
6. `order_total = round(result, 2)` ← `tax_amount` is **not** added again

---

## 2. Work packages and owners

Five deliverable streams, four owners. Stream E (EDA) is split four ways on purpose: building
a figure forces you to join tables you did not personally build, which is the mechanism that
makes all four members fluent in the whole pipeline.

| WP | Scope | Rubric | Marks | Owner | Reviewer |
|---|---|---|---|---|---|
| **WP1** | Structured parsing, source profiling, source-to-target mapping, repo/notebook integration | A1, A2, E2 | 1.5 (+1.0 shared) | **Echo** | Shawn |
| **WP2** | Six relational tables: flattening, grains, types, dates, booleans, currency, arithmetic | B1, B2, B3 | 3.0 | **Jasmine** | Yandu |
| **WP3** | Duplicate & overlap reconciliation, conflict register, FK integrity, validation register | C1, C2, E1 | 2.5 | **Yandu** | Jasmine |
| **WP4** | Regex/Unicode text pipeline, `text_functions.py`, public + student-designed tests | D1, D2, D3 | 2.5 | **Shawn** | Echo |
| **WP5** | EDA figures, 10 findings, 5 ML questions, report | F1, F2, F3, G1 | 4.5 | **all four** | round-robin |

Swap owners freely in week 0 if the strengths sit differently — but lock it by 23 Aug and
record the change in the decision log. The *reviewer* column matters as much as the owner
column: WP2's reviewer is WP3's owner because WP3 consumes WP2's output, so the review is a
real consumer test rather than a courtesy read.

### WP5 split — 8 figures, 2 each

The rubric requires 6–8 assessed figures spanning six categories, ≥4 tables, ≥2 correct
relational joins. **Only the first 8 are marked.** `A1_EDA_template.ipynb` fixes the figure
order and category for Figures 1–6 — keep it, and use 7–8 for the two optional slots:

| Fig | Category (fixed by template) | Tables | Owner |
|---|---|---|---|
| 1 | Univariate distribution or composition | orders | Echo |
| 2 | Bivariate relationship / group comparison | orders × customers **(join)** | Jasmine |
| 3 | Multivariate or segmented relationship | orders × customers × order_items **(join)** | Jasmine |
| 4 | Temporal pattern | orders × deliveries **(join)** | Echo |
| 5 | Review or text behaviour | product_reviews | Yandu |
| 6 | Delivery or operational performance | deliveries × orders **(join)** | Shawn |
| 7 | *optional* — review × product | product_reviews × products **(join)** | Yandu |
| 8 | *optional* — delivery × customer segment | deliveries × customers **(join)** | Shawn |

That covers all six tables and five joins — comfortably above the HD floor. Two figures each,
and every member owns at least one join, which is the point of splitting EDA this way.

Findings and ML questions: draft 2–3 findings each from your own figures, then **one person
edits all ten for consistency** so they read as one voice — F3 is 1.6 marks and rewards a
coherent set, not four separate styles. Same for the five ML questions (template §4 has a fixed
seven-row table per question; fill every row).

---

## 3. How the four of you work in Colab without destroying each other's work

Colab shows co-editors, but two people editing the same notebook cell will overwrite each
other. The rule set below is the whole reason this stays manageable.

### 3.1 Folder layout (shared Drive folder `5196/G1_A1/`)

Keep the two folders you already have and add five. Numbered prefixes keep them in run order
rather than alphabetical scatter.

```
5196/G1_A1/                          ← shared with all four
├── Admin/                           ← KEEP AS IS. spec, rubric, templates/ (read-only)
├── DATA/                            ← KEEP AS IS. read-only, never edited, never submitted
│   └── Group001_A1/  (README, manifest, dictionary, raw_input/)
├── 00_Master/                       ← one editor at a time
│   ├── Group001_solution.ipynb      (renamed from A1_solution_template.ipynb)
│   ├── Group001_EDA.ipynb           (renamed from A1_EDA_template.ipynb)
│   └── Group001_text_functions.py   (Shawn only)
├── 01_WIP/                          ← personal scratch, edit freely, never marked
│   └── wip_echo.ipynb  wip_jasmine.ipynb  wip_yandu.ipynb  wip_shawn.ipynb
├── 02_Outputs/                      ← the six CSVs, only ever written by a full master run
├── 03_Docs/
│   ├── Group001_source_to_target_mapping.csv
│   ├── Group001_A1_Workflow_and_Roles.md
│   └── decision_log.md
├── 04_AI_records/                   ← see §5
└── 05_Submission/                   ← built at G6 only, from copies
```

Note the folder is named `G1_A1` but your allocated alias is **`Group001`**. Every *file* name
must use `Group001`, not `G1` — Appendix A checks this explicitly. Renaming the folder to
`Group001_A1` removes the chance of anyone copying the wrong prefix, but is optional.

`Admin/templates/` stays untouched as the pristine reference. You work on *renamed copies* in
`00_Master/`, never on the originals.

### 3.2 The three rules

1. **Develop in `01_WIP/`, integrate in `00_Master/`.** You write and debug in your own notebook.
   Nothing enters `00_Master/` except through an integration slot.
2. **One editor at a time in `00_Master/`.** Post "taking master" in the group chat, do the merge,
   post "master free". Echo (WP1) runs integration at each gate; anyone can take a slot
   between gates by claiming it in chat.
3. **`Restart and Run All` before you hand anything over.** If it does not run clean from a
   fresh kernel, it is not done. This is rubric E2 and it is 1.0 mark of pure process.

### 3.3 Notebook section ownership

**Use the teaching team's template structure exactly.** `A1_solution_template.ipynb` already
defines the sections; renaming it to `Group001_solution.ipynb` is step one. Do not invent your
own numbering — the mapping CSV's `notebook_evidence` column and the report both cite section
names, so a stable structure is worth marks under A2 and E1.

Section ownership in `Group001_solution.ipynb` (template's own numbering):

| § | Section | Owner |
|---|---|---|
| 0 | Configuration and reproducibility | Echo |
| 1 | Parse and profile the two sources (1.1 JSON, 1.2 XML, 1.3 comparison) | Echo |
| 2 | Source-to-target mapping | Echo |
| 3 | Text and regex functions (3.1 implementation, 3.2 tests) | Shawn |
| 4 | Build the six tables (4.1 orders … 4.6 product_reviews) | Jasmine |
| 5 | Reconcile overlap and verify relationships | Yandu |
| 6 | Validation register (6.1 schema … 6.7 NaN reminder) | Yandu — **6.6 text checks co-owned with Shawn** |
| 7 | Export the six CSV files | Echo |
| 8 | Final reproducibility record | Echo |

Config cell must define `GROUP_ID`, `INPUT_DIR`, `OUTPUT_DIR` and use **no absolute personal
paths** — the marker runs it on their machine (Appendix A, explicit checklist item). See §3.4
for how to satisfy this in Colab, where the obvious approach breaks the rule.

### 3.4 The Colab path trap

The template's config uses relative paths (`INPUT_DIR = Path("raw_input")`). In Colab you must
mount Drive first, and a mount path like `/content/drive/MyDrive/5196/G1_A1/…` is exactly the
"student-specific absolute path" Appendix A prohibits.

Fix: mount and `%cd` into the project root in a **guarded** cell, then let every other path stay
relative. The notebook is then correct in Colab *and* on the marker's machine.

```python
# Section 0 — runs in Colab, no-ops everywhere else
from pathlib import Path
try:
    from google.colab import drive
    drive.mount("/content/drive")
    %cd /content/drive/MyDrive/5196/G1_A1/00_Master
except ImportError:
    pass          # not in Colab — already in the project folder

GROUP_ID   = "Group001"
INPUT_DIR  = Path("../DATA/Group001_A1/raw_input")
OUTPUT_DIR = Path("../02_Outputs")
```

Two things to remember at G6: the marker's unzipped folder has a different shape from your Drive
(`outputs/` sits beside the notebook, and they supply `raw_input/` themselves — you must not ship
the raw files). So the submitted config must default to `Path("raw_input")` and `Path("outputs")`.
Change those two lines during the dry run and re-run from a clean folder to prove it works.

Also note: template cell 13 reads the mapping from `TEMPLATE_DIR`. Repoint it at your own
completed `Group001_source_to_target_mapping.csv`, since `templates/` is not in the submission.

---

## 4. Stage gates and timeline

A gate is not "I finished my bit", it is "my reviewer ran it from a fresh kernel and signed
it off in the decision log". Nothing moves to the next gate until it is signed.

| Gate | Date | What must exist | Owner | Signed by |
|---|---|---|---|---|
| **G0 — Shared fact base** | Sat 23 Aug | All four have independently run a profiling notebook and reproduced the §1 numbers. Roles locked. Drive folder + AI-records convention live. | Echo | all |
| **G1 — Parse & map** | Wed 27 Aug | Both sources parsed with structured parsers. All 111 mapping rows have source_format + paths + derivation + overlap rule + notebook evidence. Profiling section written. | Echo | Shawn |
| **G2 — Text pipeline** | Sat 30 Aug | `Group001_text_functions.py` with all six functions. All 18 public test cases pass + ≥12 student-designed edge cases (near-miss references, empty result → `NaN`, non-Latin, diacritics, emoji-only). | Shawn | Echo |
| **G3 — Six tables** | Wed 3 Sep | Six CSVs written to `outputs/`, correct grains, field order matching the data dictionary, types and formats per §1.3, arithmetic per §1.4. | Jasmine | Yandu |
| **G4 — Reconciliation & validation** | Sat 6 Sep | Duplicate/overlap handled data-driven. Validation register with stable `VAL-…` IDs, observed results, PASS/FAIL, interpretation. Full `Restart and Run All` clean. | Yandu | Jasmine |
| **G5 — EDA complete** | Tue 8 Sep | 8 labelled figures, each with question / observation unit / denominator / tables & join keys / interpretation / limitation. Join-multiplication check demonstrated. EDA notebook loads the six CSVs only. | all | round-robin |
| **G6 — Submission dry run** | Wed 9 Sep | Full zip built, unzipped into a clean folder, both notebooks re-run from that folder. Report PDF ≤10 assessed pages. AI records complete. | Echo | all |
| **G7 — Submit** | Thu 10 Sep, target 18:00 | Uploaded, all four have checked the Moodle receipt. | Echo | all |

Note G7's 18:00 target against a 23:55 deadline. That ~6h buffer is deliberate; treat 23:55
as the disaster line, not the plan.

---

## 5. Working with AI — the compliance-critical part

Spec §8 is not optional and it is easy to fail *after* doing good work. If any member uses a
conversational AI tool, the group must submit a **complete, unedited** export of every
assignment-related conversation.

**Rules for this group:**

1. **One chat per work package.** Name it `A1_WP<n>_<yourname>`. Never mix A1 work into a
   chat that also contains personal or other-unit material — you cannot shorten it later.
2. **Export at every gate**, not at the end. Exports go to `04_AI_records/` as PDF or HTML.
3. **Maintain `04_AI_records/Group001_AI_index.pdf`** with one row per conversation:
   purpose · member · date · where the output was used in the submission · how it was
   independently verified.
4. **Independent verification is a rubric expectation** (rubric §5: "material AI-generated
   code and claims have independent checks"). For every AI-suggested transformation, the
   reviewer re-derives the result a second way — a different pandas expression, a spot check
   on 10 rows by hand, or a validation check with its own `VAL-` ID.
5. **Inline code completion still gets declared**, even with no chat to export.
6. All four sign `Group001_AI_declaration.pdf`.

**Working with me (Claude) in this session:** treat me as a fifth reviewer, not a fifth
author. Ask me to critique a section, propose a check you have not thought of, or explain why
something in the spec means what it means. When I produce code, the owner of that WP must be
able to explain every line — per your own project rule, if you cannot explain it, do not ship
it. This whole session is one exportable A1 conversation; keep it that way.

---

## 6. Definition of done — per criterion

Print this. A WP is done when its rows are all ticked.

| ID | Marks | Done means |
|---|---|---|
| A1 | 0.9 | JSON parsed with `json`, XML with `xml.etree`/`lxml`. Zero regex used on document structure. Objects, nesting, repeated elements, candidate keys, grains, formats and assumptions all profiled with visible output. |
| A2 | 0.6 | ≥95% of the 111 mapping rows complete: source_format, paths, derivation, overlap rule and notebook evidence all accurate. `N/A` used only where genuinely justified (customers absent from XML; products absent from JSON). |
| B1 | 1.0 | Six files, exact filenames, exact field order from the data dictionary, no extra helper columns, PKs complete and unique. |
| B2 | 1.2 | Values match the published normalisation rules — literal `NaN` for missing strings, leading zeros preserved (postcodes like `3011`), identifiers not lower-cased, numeric within 0.01. |
| B3 | 0.8 | Dates/timestamps/booleans/numerics per §1.3; arithmetic per §1.4 in that exact order; one-to-many relationships kept relational (no flattening into one wide table). |
| C1 | 0.9 | Both within-source duplicates and cross-source overlap detected via stable business keys and field evidence. One canonical row per key. No double counting. No hard-coded duplicate ID lists. |
| C2 | 0.6 | Fields normalised *before* comparison. Any field-level disagreement recorded in the validation register instead of silently overwritten. All 8 required FK relationships valid and non-null. |
| D1 | 1.2 | Full 9-step published cleaning order implemented. All listed markers, HTML entities, tags, URLs, emoji, whitespace handled. Order/SKU/promo extraction rejects near-matches and malformed boundaries. |
| D2 | 0.6 | `review_body_clean` preserves multilingual UTF-8. `review_body_latin_analysis` built *from* the clean field, retains European diacritics, returns `NaN` when no Latin letters remain. `contains_non_latin_script` is script-based, not "is it ASCII". |
| D3 | 0.7 | All 18 public cases run and shown. ≥12 additional student-designed tests. Functions live in `Group001_text_functions.py`, importable, no file I/O or network. |
| E1 | 1.0 | Executable checks with stable `VAL-` IDs covering: schema, types, missing-value representation, PK uniqueness, all 8 FKs, categorical domains, numeric ranges, row flow before/after transforms, overlap handling, price reconciliation, total reconciliation *plus* separate tax-not-double-added check, temporal ordering, extraction, multilingual preservation. Explicit tolerances. |
| E2 | 1.0 | Both notebooks `Restart and Run All` clean, offline, from configurable paths. `solution.py` reflects the notebook. `requirements.txt` if anything non-standard. Vectorised where it matters. |
| F1 | 1.3 | 8 figures, all six categories, ≥4 tables, ≥2 correct joins, each with stated question, observation unit, denominator, tables and join keys, plus an explicit join-multiplication check. |
| F2 | 0.6 | Chart form fits the data. Readable titles, axes, units, legends at 100% zoom. No misleading scales or truncated axes. |
| F3 | 1.6 | Exactly 10 numbered findings. Each cites a figure or statistic and states magnitude, denominator, retail relevance, an alternative explanation, and a proportionate next step. No causal claims from association. |
| G1 | 1.0 | Exactly 5 ML questions covering ≥2 problem types. Each states decision, unit, target, decision-time predictors, validation split, ≥1 metric, and leakage/fairness/deployment risk. 80–120 words each. |

---

## 7. Traps that cost HDs on this specific assignment

Read these once a week.

1. **`NaN` is a three-character string, not a null.** Writing pandas `NaN` produces an empty
   CSV cell and fails B2. Read back with `keep_default_na=False` to see what you actually wrote.
2. **Leading zeros.** `home_postcode`, and any ID, must stay strings end-to-end. One
   `pd.read_csv` without `dtype=str` will silently eat them.
3. **Don't add columns to the six CSVs.** Helper columns are fine inside the code, fatal in
   the output. Field order must match the dictionary exactly.
4. **`deliveries` grain is "one row per completed order".** Every order in your data has
   status `Completed`, so the count should equal the order count — verify it, don't assume it.
5. **Tax is computed before the discount and is never added to the total.** The most common
   arithmetic slip in this spec.
6. **Only the first 8 figures, 10 findings and 5 ML questions are marked.** A 9th figure does
   not replace a weak one — it is simply ignored. Make the first eight your best eight.
7. **The EDA notebook must load the six CSVs.** Re-running a hidden cleaning pipeline inside
   the EDA notebook is explicitly non-compliant.
8. **Joins multiply rows.** Any revenue or order metric computed after joining `order_items`
   to `orders` will be inflated. Compute at the intended grain and *show* the check — the
   rubric asks for it by name.
9. **Do not put the raw JSON/XML in the zip. Do not put the EDA PDF in the zip.**
10. **The report is 10 assessed pages.** Cover, contents and references are excluded;
    appendices are not assessed unless the main text cites them as validation evidence.

---

## 8. Decision log — start it today

One append-only file, `03_Docs/decision_log.md`. Every non-obvious choice goes in with a date and
a name. Format:

```
### 2026-08-23 — DEC-01 — Canonical row selection for exact duplicates
Decision: retain first occurrence after sorting by (order_id, source_system_record_id).
Why: duplicates verified byte-identical, so choice is arbitrary but must be deterministic.
Who: Yandu. Reviewed: Jasmine. Evidence: VAL-DUP-02.
```

The report's "data-preparation assurance" section needs 3–5 material transformation decisions
and 4–6 validation results. If you keep this log, that section writes itself on 8 September.
If you don't, you will be reconstructing reasoning at midnight.

---

## 9. First three actions

1. **Echo** — create the Drive folder, upload the mapping starter, book the G0 meeting.
2. **All four** — before G0, open the raw files yourself and reproduce three numbers from §1:
   the canonical order count, the within-source duplicate count, and the cross-source overlap.
   Do it independently. Compare answers at G0.
3. **Shawn** — read the 18 public text test cases and write down which spec rule each one is
   testing. That reading *is* the D1 specification.
