# Group001 — A1 decision log

One row per settled decision. A decision enters here only once it is **settled**; open items
stay in the "Still open" table at the bottom. Never delete a row — if a decision is reversed,
add a new `DEC-` row that supersedes it and mark the old one `SUPERSEDED BY DEC-nnn`.

Columns: **ID** · **Date** · **Decision** · **Why** · **Decided by** · **Affects**

---

## Foundational decisions (agreed 20–21 Aug 2026)

These mirror D1–D9 in `Group001_A1_Workflow_and_Roles.md`. That document is the narrative
version; this table is the register.

| ID | Date | Decision | Why | Decided by | Affects |
|---|---|---|---|---|---|
| DEC-001 | 20 Aug | Work split by **pipeline stage**, not by output table | Ownership maps 1:1 onto rubric criteria; text work and validation are not duplicated four times | all four | whole project |
| DEC-002 | 20 Aug | Reviewer of each stage = owner of the **downstream** stage | Review becomes a real consumer test, not a courtesy read | all four | all gates |
| DEC-003 | 20 Aug | EDA split four ways, **two figures each** | Building a figure forces you to join tables you did not build — this is what makes everyone fluent in the whole pipeline | all four | WP5, G5 |
| DEC-004 | 21 Aug | Use the teaching team's **template section numbering verbatim** | The mapping's `notebook_evidence` column and the report both cite section names | Echo | both notebooks |
| DEC-005 | 21 Aug | Mapping CSV **opens at G1, closes at G4** | It records what the code does; Yandu's reconciliation does not exist on 27 Aug | Echo | A2, WP1–WP3 |
| DEC-006 | 21 Aug | Echo **curates** the mapping; each WP owner writes their own rows' derivation text | Consistency of phrasing from one curator, accuracy from the person who wrote the code | Echo | A2 |
| DEC-007 | 21 Aug | Shawn ships **stub text functions on day 1** | Removes Jasmine's dependency on him entirely; she builds against stubs and swaps at G2 | Shawn, Jasmine | WP2, WP4 |
| DEC-008 | 21 Aug | Claude's pre-filled mapping CSV is a **cross-check, not a deliverable** | A2 marks whether the mapping is traceable to the notebook. Derive first, compare after. | Echo | A2 |
| DEC-009 | 21 Aug | Only a **full master run** writes to `02_Outputs/` | A half-finished personal run must never clobber the shared six CSVs | all four | 02_Outputs/ |

---

## Decisions settled 22 Aug 2026

| ID | Date | Decision | Why | Decided by | Affects |
|---|---|---|---|---|---|
| DEC-010 | 22 Aug | Shared Drive project folder renamed **`G1_A1` → `Group001_A1`** (closes Q3) | Appendix A requires every submitted *filename* to start `Group001_`. Matching the folder name removes a class of last-minute renaming errors at G6 and makes the Colab `%cd` path the same string as the group alias. | Echo | everyone's Drive links and Colab paths |
| DEC-011 | 22 Aug | **Parser contract:** `parse_json()` / `parse_xml()` each return a dict of flat DataFrames keyed by output-table name, plus the file's export metadata. Column names are canonical (data-dictionary field names); **values are left exactly as they appear in the source**. Three text fields carry a `_raw` suffix: `customer_note_raw`, `review_body_raw`, `product_description_raw`. Every frame carries a `source_system` column. | Rubric A1 asks for evidence of formats and missing-value conventions. That evidence disappears if the parser silently repairs `DD/MM/YYYY`, `"AUD 2,765.47"` and `Y`/`N` on the way in. Normalisation is therefore a separate, visible step in §1.3. The `_raw` suffix makes it impossible for uncleaned text to reach an export, since every target text field is `_clean`. | Echo | A1, E2, everything WP2 builds |
| DEC-012 | 22 Aug | **Naming exceptions are discovered, not asserted.** `to_snake()` and both parsers take an `exceptions` argument. §1.1 and §1.2 each parse twice: pass 1 with the general rule alone, `check_names()` reports the mismatches, the exception table is written from that report, pass 2 confirms it is clean. | Hard-coding the exception table presupposes the answer and leaves no evidence of how it was found — a reviewer cannot tell a bug from a design choice. The two-pass form caught a real rule failure on the JSON side (`prior12MOrders` → `prior12_m_orders`, should be `prior_12m_orders`) that would otherwise have surfaced at G3 inside someone else's code. Cost is ~1 s of re-parsing. | Echo | A1, A2, §1.1–§1.2 |
| DEC-013 | 22 Aug | `check_names()` is the **standing naming check**, run after every parser and after any change to a naming rule. Its two lists mean different things: *produced but not a target field* = rule error **or** a deliberate `_raw` input; *target field with no source key* = a derived field, i.e. a `source_format = derived` row in the mapping CSV. | Turns a one-off fix into a repeatable check and produces the derived-field inventory for A2 for free. It must skip tables absent from the dictionary — the XML's `WarehouseDirectory` is not an output table and would otherwise crash the check. | Echo | A1, A2, WP1 |
| DEC-014 | 22 Aug | **Extraction runs on raw text; cleaning is destructive.** `extract_order_reference`, `extract_product_sku` and `extract_promo_code` take the `_raw` column as input. `clean_narrative_text` also takes `_raw`. Character and word counts, `contains_non_latin_script` and `build_latin_analysis` are computed **after** cleaning. The `_raw` columns must survive in the working frame until all derived text fields exist, and must not be exported. | Evidence: public test cases TXT-01 and TXT-03. `clean_narrative_text` removes `PROMO: …`, `Reference: HORD…` and `SKU: …` from the text. If extraction is run on the cleaned body, every `extracted_order_reference`, `extracted_product_sku` and `promo_code` returns the `NaN` sentinel and it will present as a regex fault for a day. One source field fans out to seven targets in `product_reviews` and two in `orders`; that fan-out is recorded in the mapping CSV, not in column names. | Echo, Shawn | D1–D3, B1, A2, WP2↔WP4 interface |
| DEC-015 | 22 Aug | **XML empty elements are read as the empty string** (`el.text or ""`), not `None`. | An empty XML element yields `None` from ElementTree while the JSON export yields `""` for the same absent value (`coupon_code`: 1,770 XML rows, 1,767 JSON rows). Without this the two sources are not comparable and every blank-count check reports a false difference. It is the single representation choice the parser makes, and it is recorded here rather than buried in the code. The prescribed literal `"NaN"` output sentinel is applied later, by WP2 — not here. | Echo | A1, C1, E1 |

---

## Decisions settled 23 Aug 2026

| ID | Date | Decision | Why | Decided by | Affects |
|---|---|---|---|---|---|
| DEC-016 | 23 Aug | **`order_id` is the primary key of `orders`, not `source_system_record_id`** — even though the two are unique to exactly the same degree (2,750 distinct, 0 blanks, in both files). Both columns are still exported; the dictionary requires both. | Four tests in §1.3c decide it. (1) One-to-one across the union: 0 breaks either way. (2) Stable for the same order in both files: 0 differences over the 500 shared orders. (3) `order_items`, `deliveries` and `product_reviews` all carry `order_id`; **nothing in either file carries `source_system_record_id`**. (4) `source_system_record_id` is the stem `SRC-001-H` plus the last six characters of `order_id`, for 5,636 of 5,636 rows — it is `order_id` re-packaged with the group number and a source marker, i.e. metadata about this delivery of the data, not about the order. Choosing it would build `001` into the primary key of a submitted table. | Echo | A1, A2, all six tables, every foreign key |
| DEC-017 | 23 Aug | **Canonical-row rule: normalise first, then `drop_duplicates(key, keep="first")`.** Deterministic, documented, no source precedence. *(closes Q2)* | §1.3c: every duplicated key is exactly two copies and the copies are field-identical — 68 orders, 68 deliveries, 96 reviews, 201 JSON / 214 XML items. §1.3e: for the 3,259 keys present in both files, all 59 shared columns agree once the §1.3b normalisers are applied — 0 conflicts. So no JSON-over-XML or XML-over-JSON argument is needed and the choice of copy cannot change a value. **Order matters:** deduplicating before normalising would compare `10` against `10%` and `true` against `Y`, and report 17 columns of conflicts that do not exist. | Echo, Yandu | C1, E1, §4, §6 |
| DEC-018 | 23 Aug | **`delivery_note_clean` is a direct copy — no cleaning, no lower-casing.** *(closes Q1)* | Across the 5,000 canonical deliveries the field has **two distinct values**, `Carrier scan reconciled` and `Delivered within promise`, with no HTML tags, URLs, bracketed markers, entities or non-ASCII characters. It is a structured category, not a narrative. Task 2 says not to lower-case structured categories unless a field-specific rule requires it, and no published rule designates this field. The `_clean` suffix is the source system's own naming, not an instruction to us. | Echo, Jasmine | §4, `deliveries` |
| DEC-019 | 23 Aug | **`build_latin_analysis`, `contains_non_latin_script`, `review_length_chars` and `review_word_count` all take the *cleaned* review body.** This was never an open decision — the specification states it. *(closes Q4)* | Task 3, verbatim: "Build `review_body_latin_analysis` from `review_body_clean`, not from the noisy raw review"; "`contains_non_latin_script` is based on whether the **cleaned** multilingual review contains any letter outside the Latin script"; "`review_length_chars` = number of Python characters in `review_body_clean`"; "`review_word_count` = number of whitespace-separated tokens in `review_body_clean`". Extraction of the order / SKU / promotion references still runs on the **raw** value (DEC-014, Task 3 step 2) — the two are not in tension: extract first, clean second, measure the cleaned result. | Echo, Shawn | B1, D1–D3, WP4 |
| DEC-020 | 23 Aug | **Section 1 is read-only for everyone downstream.** Jasmine, Yandu and Shawn copy §0–§1 into their own WIP notebook to get `json_tables`, `xml_tables`, `KEYS`, `NORMALISERS` and `normalise()` in memory, and never edit those cells. A needed change to §1 is requested from Echo, who makes it in `wip_echo.ipynb` and re-issues the file with a note. | Otherwise the master notebook ends up with Echo's §1 and someone else's §4 built against a privately modified §1, and the two no longer agree. The failure is silent: everything runs, the numbers are wrong. At assembly, §1 comes from Echo's file only. | all four | assembly, §1–§6 |

---

## Still open

| # | Question | Who decides | By |
|---|---|---|---|
| Q5 | Does the master notebook get assembled by pasting sections at each gate, or does each stage owner append to the previous owner's file in turn? DEC-020 assumes pasting. Decide before G2 so nobody builds on the wrong copy. | all four | G2 (30 Aug) |

## Closed

| # | Question | Closed by |
|---|---|---|
| Q1 | `delivery_note_clean` — clean or direct copy? | DEC-018 (direct copy) |
| Q2 | Canonical-row rule for exact duplicates | DEC-017 (normalise, then keep first) |
| Q4 | Does `build_latin_analysis` take raw or cleaned text? | DEC-019 (cleaned — stated in the spec) |
