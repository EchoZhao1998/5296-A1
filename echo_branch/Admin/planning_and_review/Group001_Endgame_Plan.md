# Group001 A1 — endgame plan

**Written 1 Sep 2026. Due Thu 10 Sep 23:55; we upload Thu 10 Sep 18:00.**
This plan does not change again. What changes is which lines are ticked.

---

## 1. Where the 15 marks stand

| Criterion | Marks | State | What is left |
|---|---|---|---|
| A1 Parsing & profiling | 0.9 | done | — |
| A2 Source-to-target mapping | 0.6 | at risk | 111 evidence cells, blocked on one decision |
| B1 Filenames, grains, fields | 1.0 | done | reproduces byte-for-byte |
| B2 Field-value accuracy | 1.2 | done | — |
| B3 Types, formulas, relations | 0.8 | done | — |
| C1 Reconciliation without double counting | 0.9 | at assembly | wire the conflict detector |
| C2 Conflict handling | 0.6 | at assembly | same, plus 3 register rows |
| D1–D2 Regex, Unicode, text pipeline | 1.8 | done | — |
| D3 Public + own + private tests | 0.7 | one patch | near-match fix, already tested |
| E1 Validation coverage | 1.0 | 65 PASS | 3 deferred rows must appear in the CSV |
| E2 Fresh rerun, paths, dependencies | 1.0 | at assembly | both notebooks Restart-and-Run-All |
| **F1 Coverage, grain, joins, metrics** | **1.3** | **not started** | 8 figures |
| **F2 Visual design and readability** | **0.6** | **not started** | labels, units, legends |
| **F3 Ten evidence-based findings** | **1.6** | **not started** | writing |
| **G1 Five ML questions** | **1.0** | **not started** | writing |
| Total | 15.0 | | |

**The number that should decide how we spend the week: F3 + G1 = 2.6 marks and
neither needs a chart.** All eight figures together are worth 1.9. Build the figures
fast, plainly and correctly labelled; the prose is where the marks are.

---

## 2. Tonight: freeze the pipeline

Six items, all tested, all paste-in. After tonight, Tasks 1–4 are closed and nobody
touches them again unless a defect changes an exported value.

| # | Item | Owner |
|---|---|---|
| 1 | Paste the three tested cell replacements from `Group001_wp1_review_of_wp2_0901.md`: raw-byte diagnostic (raises `IndentationError` today), B1/B2 self-check (prints 92.20%, true answer is 100%), placeholder guard on the export | Jasmine |
| 2 | `record()` accepts `None` → status `NOT RUN`, then record VAL-FLOW-09/10/12 so the exported register admits its own gaps | Yandu |
| 3 | Drop the `rglob` fallback and the personal folder from the path list; write the register to a personal outputs folder, not the data folder | Yandu |
| 4 | Apply the near-match extractor patch and send the 10 `TODO-SHAWN` mapping rows | Shawn |
| 5 | Write DEC-024, DEC-025, DEC-026 (below) | Echo |
| 6 | Everyone confirms which six CSVs they are working against, by size or hash | all four |

**Q5 and Q6 close by decision, not by meeting.**
DEC-025 — the master is assembled by **pasting**, once, by Echo.
DEC-026 — `notebook_evidence` cites the **master's section numbers**. It stayed open
because those numbers were not fixed yet; assembly fixes them, so the answer is a
consequence of ordering the work, not a preference. All 111 cells then fill in one
pass from a six-entry lookup.

---

## 3. The nine days

| When | What | Who |
|---|---|---|
| **Tue 1 Sep** | Patch window, then code freeze. Two hours, parallel, no meeting. | all four |
| **Wed 2 Sep** | Echo assembles the solution notebook and wires the conflict detector into the pre-deduplication frame (this is C1/C2 and it only exists here). Everyone else starts their two figures the same day — the EDA notebook reads the CSVs, not the master, so nobody waits. | Echo assembles; others start figures |
| **Thu 3 Sep — gate** | Solution notebook runs Restart-and-Run-All from a fresh kernel, offline, no absolute path. Section numbers now fixed → Echo fills all 111 evidence cells. **A2, C1, C2 and E2 land here.** | Echo; Shawn reviews |
| **Fri 4 – Sun 6 Sep** | Eight figures, two each. Each person works in their own copy and sends Echo one code cell plus one markdown block in the six-part shape. Nobody edits a shared notebook. | all four |
| **Mon 7 Sep — gate** | EDA notebook assembled, reads only the six submitted CSVs, runs Restart-and-Run-All. Verify coverage: six categories, ≥4 tables, ≥2 real joins, visible check against row multiplication. | Echo assembles; Jasmine reviews |
| **Mon 7 – Tue 8 Sep** | Ten findings, five ML questions. The 2.6-mark block. Everyone reads everyone's. | all four |
| **Wed 9 Sep — dry run** | Report to PDF, cut to ten pages. Build the ZIP, unzip into an empty folder, run both notebooks from there with nothing else on the path. Whatever breaks, breaks today. | Echo builds; all four verify |
| **Thu 10 Sep** | Upload by 18:00. Two files: the ZIP, and the PDF **outside** it. Every member checks the receipt — the spec makes that individually everyone's responsibility. | all four |

---

## 4. The eight figures

Chosen so the coverage rules are satisfied without anyone reasoning about coverage:
all six required categories, all six tables, five genuine joins where two are required.
Take your two. Do not substitute one without checking what it breaks.

| # | Category | Question | Tables and join key | Owner |
|---|---|---|---|---|
| 1 | univariate | How is order value distributed across all orders? | `orders` | Yandu |
| 2 | bivariate | Which product categories earn the most revenue? | `order_items ⋈ products` on `product_id` | Echo |
| 3 | temporal | How do order volume and revenue move through the year? | `orders` | Jasmine |
| 4 | multivariate + operational | Does the on-time rate differ by carrier and service level? | `deliveries ⋈ orders` on `order_id` | Jasmine |
| 5 | review / text | Do rating, review length and script relate to each other? | `product_reviews` | Shawn |
| 6 | operational | Do late deliveries attract lower ratings? | `product_reviews ⋈ deliveries` on `order_id` | Echo |
| 7 | segmented | Which customer segments spend the most? | `customers ⋈ orders` on `customer_id` | Yandu |
| 8 | multivariate | Does unit price relate to rating and helpful votes? | `products ⋈ order_items ⋈ product_reviews` | Shawn |

**The double-counting demonstration is a figure, not a footnote.** The top band asks
for an *explicit check against row multiplication*. Figures 2 and 6 are the two that
can go wrong, and both are Echo's because grain is her part of the pipeline.

- **Figure 2** sums revenue at line grain. Joining up to `orders` and summing
  `order_total` would multiply every order by its cart size. Show both numbers, say
  which is right and why.
- **Figure 6** is worse: reviews sit at item grain, so the denominator is reviews,
  not orders. Print the row count before and after each join in the same cell.

### Every figure ships with these six, in this order

1. the analytical question
2. the observation unit and denominator
3. the tables and join keys used
4. a chart form that fits the variables
5. readable title, axes, legend, units
6. the result, and one material limitation

### Every finding ships with these five

1. what was observed, and at what grain
2. magnitude, denominator or sample size
3. why it matters in a retail context
4. an alternative explanation or uncertainty
5. a proportionate implication or next step

Both come straight from the specification. Writing to them is the difference between
the top band and the one below, and it makes eight figures by four people read as one
document.

---

## 5. Who owns what, end to end

Two figures, two or three findings, one ML question and one report section each.
Everyone's second figure joins into a table someone else built — that is deliberate.

**Echo** (curator, WP1) — assembles the solution notebook, then the EDA notebook, then
the report · 111 mapping evidence cells · Figures 2 and 6 · Findings 1–2 · ML questions
2 and 5 · Report §1 context and data scope. *Heaviest load; hand her nothing else.*

**Jasmine** (WP2) — three cell replacements tonight, then code frozen · Figures 3 and 4
(she knows the date traps: clipped delay days, the January spill-over) · Findings 3–4 ·
ML question 1 · Report §6 limitations and §7 conclusion · reviews the EDA notebook.

**Yandu** (WP3) — register status fix and path fix tonight · Figures 1 and 7 ·
Findings 5–6 and 9–10 · ML question 4 · Report §2 data-preparation assurance
(3–5 decisions, 4–6 validation results, citing stable IDs).

**Shawn** (WP4) — extractor patch and 10 mapping rows tonight · Figures 5 and 8 ·
Findings 7–8 · ML question 3 · reviews the assembled solution notebook · owns the AI
declaration and the chat-export index.

### Findings 9 and 10 are already written, in effect

Both cite reported statistics rather than figures, which the spec explicitly allows.

- **The delivery note carries no information.** `delivery_note_clean` is the same
  partition, row for row with zero disagreements across all 5,000 deliveries, as
  `delay_reason == 'none'`, `on_time_in_full`, `delay_days == 0` and
  `delivered_date <= promised_date`. A redundant feature that would leak the outcome
  into any late-delivery model — which ties finding 10 straight to ML question 1.
- **The promotion codes corroborate across sources and formats.** In each raw file
  separately, the number of populated coupon codes equals the number of promotion
  markers in the free-text notes — 1,048 in the XML, 1,051 in the JSON. The extractor
  is checked against the bytes, not against its own pattern.

---

## 6. The five ML questions

Four problem types where two are required. No models are trained in A1.

| # | Type | Question | The risk to name | Owner |
|---|---|---|---|---|
| 1 | classification | Will this order be delivered late? | Four columns leak the answer outright | Jasmine |
| 2 | regression | What will this basket be worth at checkout? | Discount and total are known only afterwards | Echo |
| 3 | classification | Which items will attract a rating of 2 or below? | Only reviewed items are observed | Shawn |
| 4 | clustering | What natural customer segments exist? | No target; validation is qualitative | Yandu |
| 5 | forecasting | What order volume should be planned for next month? | One year only; the split must be temporal | Echo |

Each is ~80–120 words or one compact table, stating the decision, the unit, the target,
predictors available **at decision time**, a validation split, a metric, and the
leakage or fairness risk. The risk line is the one most people forget and the one the
top band is written around.

---

## 7. Before uploading

Two uploads. The PDF sits **outside** the ZIP; the raw JSON and XML are **not** in it.

- [ ] `Group001_A1_submission.zip` and `Group001_EDA.pdf`, uploaded separately — Echo
- [ ] Inside the ZIP: solution notebook, its `.py` export, EDA notebook, text functions,
      mapping CSV, AI declaration, `requirements.txt`, `AI_records/`, and `outputs/`
      with the six CSVs — Echo
- [ ] Every filename starts `Group001_`, and no absolute personal path survives in
      either notebook — including in a saved cell **output**, which a human reads — Echo
- [ ] Both notebooks Restart-and-Run-All from the unzipped folder, offline, with the
      marker's layout resolving first — Shawn
- [ ] Report is at most ten pages introduction to conclusion; every table and figure
      readable at 100% zoom — Jasmine
- [ ] Complete chat exports, one per work package, with the English index recording
      purpose, location and independent verification — Shawn
- [ ] All four have seen the submission receipt — all four

---

**If something has to give, it gives from the figures — never from the ten findings or
the five questions.**
