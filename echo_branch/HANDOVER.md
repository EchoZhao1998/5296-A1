# HANDOVER — Echo ⇄ Claude, FIT5196 A1

**Purpose.** This file carries context between chat sessions. When Echo opens a new chat, she
attaches this file first; Claude reads it and continues without re-deriving anything. At the
end of a working session, Claude updates §7 and any section that changed.

**Last updated:** 28 Aug 2026 · Session 5 · by Claude

---

## 1. Who and what

Echo Zhao (`ezha0053@student.monash.edu`), Monash FIT5196 Data Wrangling, S2 2026.
Group of four: **Echo · Jasmine · Yandu · Shawn**. Assessment 1, 15% of unit.
**Due 23:55 Thursday 10 September 2026.** Target: HD.

**Echo's own deliverable is Task 1** — parse both sources, profile them, and complete the
111-row source-to-target mapping. Reviewed by Shawn at G1 (Wed 27 Aug).

### Standing rules for this project (from Echo, non-negotiable)

1. All four members must understand the *whole* pipeline, not just their own slice.
2. Code must be **concise, moderate, clearly annotated**. No advanced constructs the group
   cannot explain out loud. If Claude writes something Echo can't explain, it doesn't ship.
3. Suggestions should be practical and reviewable, not clever.
4. Every AI conversation about this assignment is exportable evidence — one named chat per
   work package, never mixed with unrelated material.

---

## 2. Where things live

**Echo's Mac** — `~/Documents/5196/5196-A1/` (this is the folder connected to Claude):

```
5196-A1/
├── Group001_A1/        teaching-team package (raw_input/, README, dictionary, manifest)
├── templates/          teaching-team templates, pristine
└── echo_branch/        ← Echo's own work
    ├── Admin/          spec, rubric, workflow plan, week-1 brief, DRIVE_SCHEMA.rtf
    ├── wip_echo.ipynb  Task 1, plus §2 mapping paths
    ├── outputs_wip_echo/                   personal run outputs, incl. the mapping skeleton
    ├── Group001_mapping_contributions.md   the ask to Jasmine / Shawn / Yandu
    ├── Group001_mapping_orders_draft.csv   worked example, 23 rows — not the deliverable
    ├── Group001_mapping_paths.py           path extraction as a standalone file
    └── Group001_source_to_target_mapping(claudeExample).csv   ← cross-check only, DO NOT SUBMIT
```

**Shared Google Drive** — `5196/Group001_A1/` (Echo's personal `5196`, `Group001_A1` shared with the group):

```
Group001_A1/
├── Admin/          spec, rubric, templates/ — pristine, never edited
├── DATA/           Group001_A1/ raw package — read-only
├── 00_Master/      Group001_solution.ipynb, Group001_EDA.ipynb, Group001_text_functions.py
├── 01_WIP/         wip_echo, wip_jasmine, wip_yandu, wip_shawn — personal, never marked
├── 02_Outputs/     the six CSVs — written ONLY by a full master run
├── 03_Docs/        mapping CSV, workflow plan, decision_log.md
├── 04_AI_records/
└── 05_Submission/  built at G6 only
```

**Notion — "FIT5196 A1 — Group001 Hub"** (https://app.notion.com/p/3c28dcda26c58179a52ed259f4ff89a2)
This is **Echo's personal instrument panel**, not a group tool — the others aren't Notion users.
Group-facing documents are the markdown files in Drive. Claude updates the Notion page; Echo
reads it to see where things stand.

**Naming.**  Every *filename* must start `Group001_`. Appendix A of the spec checks this.

---

## 3. Decisions already made

| # | Decision | Why |
|---|---|---|
| D1 | Work split by **pipeline stage**, not by output table | Ownership maps 1:1 onto rubric criteria; text work and validation aren't duplicated four times |
| D2 | Reviewer = owner of the **downstream** stage | Review becomes a real consumer test, not a courtesy read |
| D3 | EDA split four ways, **two figures each** | Building a figure forces you to join tables you didn't build — this is what makes everyone fluent |
| D4 | Use the teaching team's **template section numbering verbatim** | The mapping's `notebook_evidence` column and the report both cite section names |
| D5 | Mapping **opens at G1, closes at G4** | It records what the code does; Yandu's reconciliation doesn't exist on 27 Aug |
| D6 | Echo **curates** the mapping; each WP owner writes their own rows' derivation | Consistency of phrasing from one curator, accuracy from the person who wrote the code |
| D7 | Shawn ships **stub text functions on day 1** | Removes Jasmine's dependency on him entirely; she builds against stubs and swaps at G2 |
| D8 | Claude's pre-filled mapping is a **cross-check, not a deliverable** | A2 marks whether the mapping is traceable to the notebook. Derive first, compare after. |
| D9 | Only a **full master run** writes to `02_Outputs/` | A half-finished personal run must never clobber the shared six CSVs |

### Owners

| WP | Scope | Rubric | Marks | Owner | Reviewer |
|---|---|---|---|---|---|
| WP1 | Parsing, profiling, mapping, integration | A1, A2, E2 | 1.5 (+1.0) | Echo | Shawn |
| WP2 | Six relational tables | B1–B3 | 3.0 | Jasmine | Yandu |
| WP3 | Reconciliation, conflicts, validation register | C1, C2, E1 | 2.5 | Yandu | Jasmine |
| WP4 | Regex/Unicode text pipeline | D1–D3 | 2.5 | Shawn | Echo |
| WP5 | EDA, findings, ML questions | F1–F3, G1 | 4.5 | all four | round-robin |

### Gates

G0 Sat 23 Aug (shared fact base) · **G1 Wed 27 Aug (Echo's gate)** · G2 Sat 30 Aug (text) ·
G3 Wed 3 Sep (six tables) · G4 Sat 6 Sep (reconciliation + validation) · G5 Tue 8 Sep (EDA) ·
G6 Wed 9 Sep (dry run) · G7 Thu 10 Sep 18:00 (submit)

---

## 4. Verified data facts

All derived from the actual files, most recently re-verified 23 Aug 2026 by building the six
tables end to end. **Never hard-code these into the pipeline** — the spec forbids it and rubric
C1/E1 penalise it. They exist to catch mistakes.

### Counts

| Entity | JSON | XML | Canonical |
|---|---|---|---|
| Orders | 2,818 rows → 2,750 unique | 2,818 → 2,750 | **5,000** |
| Order items | 8,826 → 8,625 | 8,833 → 8,619 | **15,685** |
| Deliveries | nested, 1 per order | nested, 1 per order | **5,000** |
| Customers | 500 | absent | **500** |
| Products | absent | 1,000 | **1,000** |
| Reviews | 3,946 → 3,850 | 3,946 → 3,850 | **7,000** |

Only 500 of the 2,750 order IDs appear in *both* files. Matching row counts are a coincidence,
not overlap — the two files describe mostly different records.

### Structure and grain

- **JSON** `{exportMetadata, customerProfiles[500], orders[2818]{header, shoppingCart[],
  delivery}, productReviews[3946]}`
- **XML** `OperationsExport{Export_Metadata, Orders/Order[2818]{Header, Shopping_Cart/Item[],
  Delivery}, ProductCatalogue/Product[1000], ProductReviews/Review[3946],
  WarehouseDirectory/Warehouse[3]}`
- `order_items` is **1 to 5 rows per order** (median 3). The raw file shows up to 10 because a
  duplicated order carries a duplicated cart; deduplicate on `order_item_id` first. *(Corrected
  23 Aug after Jasmine's review — the earlier 1–10 figure was a duplication artefact.)*
- One delivery per order; every order has one. `order_status` is `Completed` for all 2,818 rows
  in both files.
- One review per reviewed order item — 3,850 distinct `review_id` and 3,850 distinct
  `order_item_id` in each file.
- `WarehouseDirectory` (3 warehouses, lat/long) maps to no required output field. Useful for an
  EDA distance figure; must never become a column in the six CSVs.

### Keys and reconciliation

- **Primary keys** are the dictionary's `position = 1` fields. `order_id` was chosen over
  `source_system_record_id`, which is the same identifier re-encoded — see DEC-016.
- **Within-source duplicates:** 68 order IDs, 68 delivery IDs, 96 review IDs (identical counts in
  each file); 201 item IDs in the JSON, 214 in the XML. Every duplicate is exactly two copies and
  the copies are field-identical.
- **Cross-source overlap:** 500 orders, 500 deliveries, 1,559 items, 700 reviews. Across all
  3,259 shared keys and 59 shared columns there are **zero** field disagreements once normalised.
  No precedence rule needed; conflict *detection* is still required — see DEC-017.
- **All eight required foreign keys resolve with zero orphans** against the union, and several
  fail badly against a single file (1,300 JSON review pointers, 499 XML customer pointers).

### Formats and values

- XML: dates `DD/MM/YYYY`, timestamps `DD/MM/YYYY HH:MM:SS`, booleans `Y`/`N`, money
  `AUD 2,765.47`, percent `10%`, every value arrives as text.
- JSON: natively typed, ISO dates, `true`/`false`.
- `coupon_discount` is a **percentage** — values 0, 5, 10, 15, 20, 25. Treating it as a dollar
  amount breaks 3,906 of 5,000 order totals and every result looks plausible.
- `coupon_code` is the **only** field with missing values anywhere: 1,767 blank in the JSON,
  1,770 in the XML. Everything else is fully populated in both files.
- **Arithmetic verified on all 5,000 canonical orders**: `line_revenue = round(qty × unit_price,
  2)` 0 mismatches of 15,685; `order_price = round(Σ lines, 2)` 0 of 5,000; `tax_amount =
  round(price/11, 2)` 0 of 5,000; `order_total = round(price × (1 − d/100) + delivery, 2)` 0
  outside the 0.01 tolerance. Zero of 5,000 orders match a formula that adds tax again.
- `review_title` — checked across all 7,000 canonical reviews: no markup, markers, URLs, entities
  or uppercase, but **479 contain non-ASCII characters** (multilingual titles). Direct copy is
  correct; it must not be passed through a Latin-only filter.
- Only **ten** target fields are derived rather than renamed, and all ten are text:
  `orders.customer_note_clean`, `orders.promo_code`, `products.product_description_clean`, and
  seven in `product_reviews`.

### Independent build check (23 Aug)

Building all six tables by the documented recipe — parse, normalise, concat,
`drop_duplicates(key)` — gives 6/6 correct row counts, 6/6 unique non-null primary keys, 8/8
foreign keys with zero orphans, correct grain on every table, and all five arithmetic identities
inside tolerance.

---

## 5. Environment: drafting on Mac, running everywhere

**GPU is irrelevant here.** Nothing in A1 needs a T4 — it's ~32 MB of JSON/XML and pandas. Use
Colab's **CPU runtime**, which has no meaningful quota pressure. Don't let GPU limits drive the
plan. Drafting on the Mac is a good choice for a different reason: fast local iteration.

**The reproducibility risk of drafting locally** is version drift — Echo's pandas may differ
from Colab's. Mitigation: each gate, the reviewer runs the notebook **on Colab** from a fresh
kernel. If it only works on Echo's Mac, it isn't done.

### Path strategy

Three environments must produce identical results, and the spec bans student-specific absolute
paths (Appendix A). Resolve paths once, in the config cell, with a short candidate list:

```python
from pathlib import Path

GROUP_ID = "Group001"

# Where the raw JSON/XML live. First existing candidate wins.
# Marker's layout is first, so the submitted notebook works unchanged for them.
INPUT_CANDIDATES = [
    Path("raw_input"),                                  # marker's unzipped folder
    Path("Group001_A1/raw_input"),                      # Echo's Mac
    Path("../DATA/Group001_A1/raw_input"),              # Drive, run from 00_Master/
]
INPUT_DIR = next(p for p in INPUT_CANDIDATES if p.exists())

OUTPUT_DIR = Path("outputs")        # master run only; see D9
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Reading from:", INPUT_DIR.resolve())
```

Six lines, no magic, every line explainable — which is rule 2 above.

For Colab, mount Drive and `%cd` into `00_Master/` in a **separate** cell, so the config cell
itself stays path-neutral:

```python
# Colab only. Does nothing elsewhere.
try:
    from google.colab import drive
    drive.mount("/content/drive")
    %cd /content/drive/MyDrive/5196/Group001_A1/00_Master
except ImportError:
    pass
```

**Where do results go?** Personal while drafting, shared only when integrated:

- Drafting in `01_WIP/` or `echo_branch/` → write outputs to your own scratch folder.
- Only a full, clean run of `00_Master/Group001_solution.ipynb` writes to `02_Outputs/`.
- The submitted default must be `Path("outputs")` beside the notebook. Verify this at G6 by
  unzipping into an empty folder and running from there.

**At G6, check:** `INPUT_CANDIDATES[0]` is the marker's layout, the Colab cell is harmless off
Colab, and no absolute personal path survives anywhere in either notebook.

---

## 6. Open questions

| # | Question | Who decides | By |
|---|---|---|---|
| Q5 | Is the master notebook assembled by **pasting** finished sections at each gate, or does each stage owner **append** to the previous owner's file in turn? DEC-020 assumes pasting. Everyone's file layout depends on the answer. | all four | G2 (30 Aug) |
| Q6 | Does the mapping's `notebook_evidence` column cite a section number (`§1.3d`) or a cell heading? Section numbers are stable under DEC-004 but only if nobody renumbers. **Depends on Q5:** if the master is assembled by pasting, numbering is assigned at paste time and headings are the safer citation. Either way the column cites the *master*, never `wip_echo.ipynb` — a citation into a personal file goes stale silently. | Echo | G1 (27 Aug) |

**Closed since Session 1:** Q1 → DEC-018 (`delivery_note_clean` is a direct copy, no cleaning) ·
Q2 → DEC-017 (normalise, then `drop_duplicates(key, keep="first")`) · Q3 → DEC-010 (folder
renamed) · Q4 → DEC-019 (the latin-analysis and measure fields take the *cleaned* body; the
specification states this, it was never a judgement call).

Every answered question becomes a `DEC-` row in `Admin/decision_log.md`, which now runs to
DEC-020 and carries a **Closed** table.

---

## 7. Session log

### Session 5 — 28 Aug 2026 · WP2+WP4 notebook validated; the plan re-cut around EDA

`templates/wip_jasmine_0829.ipynb` — Jasmine's notebook with Shawn's real text functions
integrated — was walked through cell by cell, executed against the real files outside the
notebook, and its numbers re-derived independently.

- **The six tables are correct.** Row counts, primary keys, field order, all eight foreign keys
  and the entire arithmetic chain reproduce exactly, not merely inside tolerance. Formats,
  sentinels and the absence of helper columns all check out. Every assert in the notebook passes.
- **One decision is in conflict.** §4.4 now runs `clean_narrative_text` over
  `delivery_note_clean`, which DEC-018 closed on 23 Aug as a direct copy. The field has two
  values and no markup, so cleaning it does exactly one thing — lower-case it — and the spec's
  normalisation list names that. Recommendation: keep DEC-018, which also settles Shawn's list
  at 10 rows rather than 11. Needs a `DEC-` row either way.
- **Eight smaller findings**, written up in `Group001_wp1_review_of_wp2_0829.md`: a canonical /
  per-source number confusion in §4.3 ("497 of 500 customers have orders" — it is 500 of 500),
  the length and word counts not implementing the sentinel rule, the raw-byte diagnostic still
  reading backwards, a stale B2 self-check, two monetary roundings bypassing `money_round()`,
  and four housekeeping items to clear before anything reaches master.
- **Three answers back to Jasmine.** WP1's path constants need no change. Her regenerated
  `Group001_mapping_wp2_rows.csv` is byte-identical to the copy already merged. And the
  `nullable = False` / `'NaN'` question can close as a decision: with the real functions loaded,
  no such field carries the sentinel anywhere, so both readings agree and the stricter one
  becomes a check.
- **The promo cross-check was corroborated a third way**, from raw byte counts rather than from
  either notebook: 1,048 populated `Coupon_Code` elements in the XML against 1,048 `PROMO:`
  markers, and 1,051 markers in the JSON.

**The schedule was re-cut** in `Admin/Group001_Week2_Brief.md`. WP2 landed five days early and
WP4's code is already integrated, so the original chain no longer binds. The constraint is now
WP3, which has no visible artefact, and EDA, which is 4.5 marks and had not started. EDA moves to
Monday 31 Aug — the EDA notebook may only read the six CSVs, and those exist and are verified, so
it never needed to wait for G4. Gates pull forward by one to two days and submission targets
Wednesday 9 Sep.

**Next session:**

1. Review Shawn's `Group001_text_functions.py` against the nine-step order and the 18 public
   cases — it is not in this folder yet, and G2 is Saturday.
2. Close Q1 (write DEC-021), Q5 and Q6. Q6 blocks the mapping's last 111 rows.
3. Re-issue `Group001_wp1_reply_to_wp2.md` — the file is truncated mid-sentence, and its point 3A
   is now stale because WP4 landed and that check is real.
4. Restart-and-Run-All on `wip_echo.ipynb`, locally and on Colab; clear the stored config output.
5. Send Yandu the 111 overlap rows grouped into stock rules, and start figures 1 and 4.

### Session 4 — 28 Aug 2026 · WP2's handover merged; the mapping is 101 of 111 written

Jasmine's `wip_jasmine.ipynb` was reviewed end to end and her §2 handover merged into the mapping.
Her six tables are correct: 5,000 / 15,685 / 500 / 5,000 / 1,000 / 7,000, PKs unique and complete
on all six, matching §4 exactly.

- **§2.3 of `wip_echo.ipynb`** (new) fills the source paths for the ten `derived` rows. `derived`
  means computed rather than copied, not sourceless, and DEC-014 requires the fan-out to be legible
  in the CSV: `reviewText` / `Review_Text` → 7 `product_reviews` targets, `customerNote` /
  `Customer_Note` → 2 `orders` targets, `Product_Description` → 1 (XML only). Only the feeder
  *name* is declared; the paths are looked up through the same index and `ANCHOR` as §2.1, so a
  moved field blanks the row rather than keeping a stale path.
- **§2.4** (new) merges `matework/outputs_wip_jasmine/Group001_mapping_wp2_rows.csv` on
  `(output_table, target_field)` with `validate="one_to_one"`. All 111 pairs matched. Done in code,
  never as a CSV hand-edit, so re-running either notebook reproduces the file.
- **The mapping now reads 101 written / 10 `TODO-SHAWN` / 111 `TODO-YANDU` / 111 `TODO-EVIDENCE`.**
  Deliverable at `outputs_wip_echo/Group001_source_to_target_mapping.csv`; a second working copy
  `Group001_mapping_working.csv` carries an extra `handover_section` column.

**One classification disagreement, and it was Jasmine's.** She declares an 11-entry `WP4_DERIVED`
list by hand; §2.1 derives 10 as a residue. Her extra row is `deliveries.delivery_note_clean` —
which sits at the delivery grain in *both* files and which DEC-018 closed on 23 Aug as a direct
copy of a two-valued structured category. The consequence was that nobody wrote the row, so WP1
curated it. The `CURATED` dict is applied last and only over a surviving placeholder, so when she
corrects her list at G3 her own wording wins and the curation stops firing on its own.

**Jasmine's `notebook_evidence` was parked, not used.** Her `§4.1`–`§4.6` are correct section
numbers in *her* WIP file. The column must cite the master, and Q6 is still open. Values preserved
in `handover_section` in the working copy; the deliverable keeps `TODO-EVIDENCE`.

**Two of her cells contradict their own output** — written up in
`echo_branch/Group001_wp1_reply_to_wp2.md`, to send before G3:

1. VAL-TEXT-13's markdown claims 1,873 rows carry both `coupon_code` and `promo_code` and agree.
   The cell prints *0 rows carry both* and *1,873 rows where the populated/sentinel pattern
   differs*. `promo_code` is 100% sentinel until WP4 lands, so the check is **vacuous, not
   passing**. It becomes real evidence after G2.
2. The raw byte-count diagnostic is case-sensitive, so four of its five zeros are artefacts.
   Lower-cased, `promo` appears **1,051 times in the JSON and 1,048 in the XML** — as the `PROMO:`
   marker inside the customer note — while `promo_code` and `promocode` stay 0 in both. That is a
   much stronger statement of the point it was reaching for, and gives Shawn an independent
   expected count (~1,050 markers over 2,818 raw JSON orders) rather than testing his regex
   against his own pattern.

**Notebook prose rule applied.** No `DEC-`, `Q`, `WP`, `§`-of-another-file or teammate names appear
in the new markdown or comments — only in the CSV text, where the existing draft already uses them.

**Verification.** All 40 code cells were executed against the real files outside the notebook and
pass, including the new asserts: 111 rows, column order matches the template, `mapping_id` order
preserved against the dictionary's positions, no `TODO-JASMINE` left, exactly 10 `TODO-SHAWN` and
all 10 are `source_format == "derived"`, and no row is pathless. A **Restart-and-Run-All inside the
notebook is still outstanding**, as is the Colab fresh-kernel run. Backup at `wip_echo.ipynb.bak2`.

**Next session:**

1. Restart-and-Run-All on `wip_echo.ipynb`, then the same on Colab from a fresh kernel.
2. Send `Group001_wp1_reply_to_wp2.md` to Jasmine; still waiting on her `ANCHOR` confirmation.
3. Chase Shawn for the 10 `TODO-SHAWN` rows and Yandu for `overlap_or_conflict_rule`.
4. Close Q6 — it is now the only thing standing between the mapping and its evidence column.
5. Minor, for G6: the config cell's *stored output* still prints the resolved
   `/Users/ez_us/...` paths. The code is path-neutral, but the saved output is not, and Appendix A
   is read by a human. Clear outputs or re-run from a neutral cwd before submission.

---

### Session 3 — 25 Aug 2026 · Mapping opened: paths derived, skeleton written, team asked

The mapping moved from "not started" to "three of six columns complete for all 111 rows, the other
three assigned". Nothing was copied from the pre-filled cross-check file; it is still unopened.

- **§2 of `wip_echo.ipynb`** is now written (the stub at the end of the file is filled, 8 cells).
  Two leaf-path walkers list every place a scalar sits — **86 paths in the JSON, 89 in the XML** —
  and match them against the dictionary with casing removed, so `orderID` / `Order_ID` / `order_id`
  resolve to one key. Output: `source_format`, `json_source_path`, `xml_source_path` for all 111
  rows, written to `outputs_wip_echo/Group001_source_to_target_mapping.csv`.
- **The grain anchor is the one declared thing.** Name matching alone is wrong: `order_id` occurs in
  four JSON blocks and `customer_id` in three, so an unanchored run reports `customers.customer_id`
  and `products.product_id` as `both` — the XML carries a customer *pointer* in every order header,
  not a customer record. Six lines of `ANCHOR` (which block holds one record per output row) fix it.
  **Jasmine must confirm this table matches how she builds each grain** — if it doesn't, those path
  rows are wrong.
- **Two checks, both passing.** `derived` is not declared anywhere — it is what is left when no
  field of that name exists at that grain in either file — and it lands on exactly the ten text
  fields §4 already names, by a completely different route. And the number in each `mapping_id`
  equals the dictionary's `position`, verified on all 111 rows, so mapping / dictionary / output
  column order are one ordering rather than three.
- **Placeholders, not blanks.** The three judgement columns carry `TODO-JASMINE` (101 rows),
  `TODO-SHAWN` (10), `TODO-YANDU` (111) and `TODO-EVIDENCE` (111), so a half-finished mapping cannot
  be mistaken for a finished one and each owner filters to their own rows.

Also produced:

- `Group001_mapping_orders_draft.csv` — the 23 `orders` rows written out in full, as a worked
  example of the level of detail expected. Not the deliverable.
- `Group001_mapping_contributions.md` — the team-facing ask, one section each for Jasmine, Shawn
  and Yandu, with row IDs, the two things each row needs (method + section), and gate dates.
- `Group001_mapping_paths.py` — the same path code as a standalone file.
- `wip_echo.ipynb.bak` — pre-edit backup, safe to delete once §2 has been run in the notebook.

**Verification.** The four new code cells were executed against the real files outside the notebook
and all pass; a full Restart-and-Run-All has **not** been done since the edit and is the first thing
to do next session. No absolute personal path appears anywhere in the notebook.

**Reframing worth keeping.** The mapping is not a separate work package that the four of us
contribute to. It is a *cross-section* of the four work packages: each of its columns belongs to the
owner of the stage it describes. That is the reason it opens now and closes at G4 — and the reason
Echo's G1 deliverable is honestly three columns plus a first pass at evidence, not a filled CSV.

**Next session:**

1. Restart-and-Run-All on `wip_echo.ipynb`, then the same on Colab from a fresh kernel.
2. Send `Group001_mapping_contributions.md` to the group; get Jasmine's confirmation of `ANCHOR`
   before G1 rather than after.
3. Close Q6 at G1, and note that its answer depends on Q5 — see §6.

---

*(Session 2, 22–23 Aug — Task 1 built and closed except the mapping — retired from this log; its decisions are DEC-011 to DEC-020 in `Admin/decision_log.md`.)*

---

## 8. How to use this file

**Opening a new chat:** attach this file and say what you're working on. Claude reads §1–§6 for
context and §7 for where you left off.

**Closing a session:** ask Claude to update the handover. It should append a Session entry to
§7, revise §3 if a decision was made, §4 if a new data fact was verified, and §6 if a question
opened or closed. Keep §7 to the last three sessions — older entries move to the decision log.

**Keep this file in `echo_branch/`, not in the shared Drive.** It's Echo's working context and
mentions Claude throughout; the group-facing documents are the two markdown files in Admin.
It is *not* a substitute for the AI chat exports required by spec §8 — those are the complete
conversations themselves, in `04_AI_records/`.
