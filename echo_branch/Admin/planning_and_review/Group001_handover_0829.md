# Group001 A1 — handover, Saturday 29 August

Echo · for Jasmine, Yandu, Shawn · **12 days to the deadline**

Three minutes to read. Everything below is either a decision we owe each other, a date that
moved, or a thing to do.

---

## 0. Read this first — the exported CSVs are provisional

The six files currently in `outputs_wip_jasmine/` come from a run where the text-functions module
was not found. The notebook was honest about it — the banner fired and the guard reported
`WP4 placeholders in use: True` — but **the CSVs themselves carry no marker**. In them,
`customer_note_clean` still holds `[SYSTEM] <p>…</p> https://…`, `product_description_clean` still
carries `[CATALOGUE]`, review bodies are uncleaned and `promo_code` is empty on all 5,000 rows.

**Nobody should build against those files until they are re-exported from a run where the module
loads.** Yandu especially — a register written against them would be testing uncleaned text and
three dead columns.

Fix agreed as DEC-022: a placeholder run must not write the six CSVs at all, or must write them to
a separate `provisional/` folder. One `if` in the export section. This has happened once; it will
happen again the night before submission if it is not blocked in code.

---

## 1. Where we are

**WP2 is done and it is right.** Jasmine's notebook, with Shawn's text functions integrated, was
walked through cell by cell and re-checked against the raw files by a second route. Row counts,
primary keys, field order, all eight foreign keys and the whole arithmetic chain reproduce —
**exactly**, not merely inside the 0.01 tolerance. That is five days ahead of the plan.

**WP4's code has landed** and the pipeline has been re-run against it. What is missing is the
*evidence*: the 18 public cases shown passing plus ≥12 of our own. The module also is not in a
place I can open, and I am its reviewer.

**WP3 has nothing past G0.** The register specification was due 27 August. Two decisions Yandu
owed — the source-overlap marker and the precedence rule — were made by WP2 in the meantime.

**EDA has not started.** It is 4.5 of the 15 marks, the largest single block.

Shawn's and Yandu's G0 notebooks were both checked: correct, they run clean, and between the four
of us we now have four independent routes to 5,000 / 68 / 500. That is exactly what G0 was for.

## 2. Decisions — one settled, two still owed

The two open ones are each blocking somebody.

**a. ~~`deliveries.delivery_note_clean`~~ — SETTLED, see DEC-021.** Direct copy; DEC-018 stands.
The values keep their source case, `Carrier scan reconciled` and `Delivered within promise`. With
the real text functions loaded, lower-casing is the only thing cleaning does to this field, and the
specification's normalisation list names that directly. **Shawn's mapping list is 10 rows, not 11.**

**b. How the master notebook gets assembled** — sections pasted in at each gate, or the file passed
hand to hand. Blocks where everyone's finished cells go.

**c. What the mapping's evidence column cites** — a section number or a cell heading. It must point
at the master, never at a personal notebook. Depends on (b), and blocks the last 111 rows of the
mapping.

**Already resolved, for the record:** `nullable = False` versus the `'NaN'` sentinel. With the real
text functions loaded, no `nullable = False` field carries the sentinel anywhere in the six tables.
Both readings agree on this data, so we adopt the stricter one as a check — assert that no
`nullable = False` field contains `'NaN'` — and the question closes.

## 3. Dates have moved — and the old day names were wrong

**Check your calendar, not the day names in the week-1 plan.** They are one day out: 23 Aug is a
Sunday, 27 Aug and 3 Sep are Thursdays, 30 Aug and 6 Sep are Sundays. The dates were right and the
deadline is right. Go by dates.

WP2 landing five days early breaks the old chain, so the plan is re-cut. The full version is in
`Admin/Group001_Week2_Brief.md`; the dates that matter:

| Gate | New date | Owner |
|---|---|---|
| G2 text pipeline | **Sun 30 Aug** (unchanged) | Shawn |
| **EDA starts** | **Mon 31 Aug** | all four |
| G3 six tables | **Tue 1 Sep** *(was 3 Sep)* | Jasmine |
| G4 reconciliation & validation | **Fri 4 Sep** *(was 6 Sep)* | Yandu |
| G5 EDA + report draft | **Mon 7 Sep** *(was 8 Sep)* | all four |
| G6 dry run | **Tue 8 Sep** *(was 9 Sep)* | Echo |
| G7 submit, 18:00 | **Wed 9 Sep** *(was 10 Sep)* | Echo |

**Why EDA moves to Monday.** The EDA notebook is only allowed to read the six exported CSVs. Those
exist now and have been verified, so EDA never depended on validation and should run beside it, not
after it. This is the single biggest change and it is worth four working days on the largest mark
block.

**One gap in the old plan:** the report appears only at G6, as if it were packaging. It is 10
assessed pages carrying the 10 findings, the 5 ML questions and the assurance section. I will edit
it unless someone else wants the role.

## 4. What each of us does next

**Shawn** — by **Sun 30 Aug**: `Group001_text_functions.py` plus the test evidence, somewhere I can
open it. Watch the case where the removable marker list is closed: a generic bracket regex passes 17
of the 18 and fails that one. Then by **Tue 1 Sep**, your mapping rows. Your figures are 6 and 8.

**Yandu** — you are the critical path. By **Tue 1 Sep**: review the six tables as a consumer, from a
fresh kernel. By **Fri 4 Sep**: the executable register, and the mapping's `overlap_or_conflict_rule`
for all 111 rows — I will send it pre-grouped, most rows take one of four stock sentences, so it is
an hour. Your figures are 5 and 7.

**Jasmine** — by **Tue 1 Sep**: re-run after the `delivery_note_clean` decision plus the small
corrections in my review note. Then EDA from Monday — figures 2 and 3. You are ahead; the most
useful thing now is being quick to answer questions about the tables everyone else is building on.

**Echo** — by **Sun 30 Aug**: review Shawn's functions, close the three decisions, fresh-kernel run
on Colab. From Monday, figures 1 and 4. By **Fri 4 Sep**, the mapping's evidence column.

## 5. Five facts worth knowing before you write a check

1. **The 68 duplicated order IDs in the JSON and the 68 in the XML share nothing.** Zero overlap
   between the two sets. Matching counts, different records — a check assuming otherwise passes
   falsely. Every duplicate is exactly a pair, which is why "IDs appearing twice" and "rows removed"
   both give 68.
2. **`delay_days` is `max(0, delivered − promised)`**, not the raw difference — the raw difference
   gives 2,985 false mismatches. And `delay_reason == 'none'` is a real category on **4,472** rows
   (the earlier 2,516 was the JSON-only figure); it must never be mapped to the `NaN` sentinel.
3. **Write tolerances as `≤ 0.01`, not `<`.** A strict `>` reported 23 false failures on
   `order_total`. Use `np.isclose(a, b, rtol=0, atol=0.01, equal_nan=True)`.
4. **Round money with Python's `round()`, not pandas `.round(2)`.** Python reproduces the source on
   all 5,000 orders; pandas misses 93 by a cent. Inside tolerance, so nothing fails — but our six
   CSVs would stop being identical between our machines.
5. **`order_status`, `delivery_status` and `verified_purchase` are single-valued**, so a
   "both values present" check raises a false failure, and none of them can carry an EDA figure.

## 6. Two standing rules, unchanged

**Restart and Run All from a fresh kernel before any handover**, or it is not done — that is a full
mark of pure process. And **no personal path goes into the master.** Our Colab paths genuinely
differ: the shared folder sits under `MyDrive/Group001_A1` for whoever owns it and resolves through
a `.shortcut-targets-by-id/…` route for everyone else. Use whatever works in your own notebook; the
submitted one defaults to `raw_input` and `outputs` beside itself, and we prove it at the dry run by
unzipping into an empty folder. One warning — a path fallback that searches the whole Drive and takes
the first match will read a stale copy without telling you. An ordered list that raises a clear
error is safer than a search that always succeeds.
