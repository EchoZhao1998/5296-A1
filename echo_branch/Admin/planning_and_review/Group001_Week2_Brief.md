# A1 — Week 2: where we actually are, and what changes

Echo · 29 Aug 2026 · for Jasmine, Yandu, Shawn · 12 days to the deadline

---

## Part 1 — The plan versus reality

The week-1 plan assumed a chain: text functions, then tables, then validation, then EDA. That
chain has broken in our favour at the front and is now sagging at the back.

| Gate | Planned | Where it actually is |
|---|---|---|
| G0 shared fact base | 23 Aug | done |
| G1 parse & map | 27 Aug | §1 done. Mapping has source format, both path columns and 101 of 111 derivation rows. Two columns are still placeholders by design — they close at G4. Not signed off. |
| G2 text pipeline | 30 Aug | the code landed early and is already integrated. What is *not* done is the evidence — 18 public cases plus 12 of our own, shown — and my review of it. |
| G3 six tables | 3 Sep | **done, five days early, and independently re-checked today.** Row counts, keys, field order, all eight foreign keys and the whole arithmetic chain reproduce exactly. |
| G4 reconciliation & validation | 6 Sep | **nothing visible yet.** Two decisions Yandu owed have been made by WP2 in the meantime. This is now the critical path. |
| G5 EDA | 8 Sep | not started. 4.5 of the 15 marks. |
| G6 dry run / G7 submit | 9 / 10 Sep | untouched |

**The one structural change.** EDA was scheduled after validation because it seemed to depend on
it. It does not. The EDA notebook is only permitted to read the six exported CSVs, and those
files exist now and have been checked. So EDA starts Monday, in parallel with validation, instead
of waiting. That buys the biggest single mark block four extra working days.

**The one thing nobody owns.** The report is 10 assessed pages and carries the findings, the ML
questions and the data-preparation assurance section — roughly 2.6 marks that exist nowhere else.
It appears in the plan only at G6, as if it were a packaging step. It is not. It needs an editor
and a start date, both below.

---

> **Weekday labels in the week-1 plan are one day out.** Checked against a calendar: 23 Aug is a
> Sunday, 27 Aug and 3 Sep are Thursdays, 30 Aug and 6 Sep are Sundays. The *dates* were right and
> the deadline — Thursday 10 September — is right. Anyone scheduling by day name rather than date
> should re-check. Dates in this document are the ones that count.

## Part 2 — Revised gates

Everything moves one to two days earlier, and the submission target moves to Wednesday.

| Gate | New date | What must exist | Owner | Signed by |
|---|---|---|---|---|
| **G2 text pipeline** | Sun 30 Aug | all 18 public cases shown passing, plus ≥12 of our own edge cases. Functions importable, no file I/O. Three open questions closed (below). | Shawn | Echo |
| **G3 six tables** | **Tue 1 Sep** *(was 3 Sep)* | the six CSVs, re-run clean after the `delivery_note_clean` decision. Consumer review, not a courtesy read. | Jasmine | Yandu |
| **G4 reconciliation & validation** | **Fri 4 Sep** *(was 6 Sep)* | validation register with stable `VAL-` IDs, observed results, pass/fail, interpretation. §5 reconciliation. Mapping's overlap column filled — all 111 rows. | Yandu | Jasmine |
| **G5 EDA** | **Mon 7 Sep** *(was 8 Sep)* | 8 figures, each with question, observation unit, denominator, tables and join keys, interpretation, limitation. Join-multiplication check shown. | all four | round-robin |
| **Report draft** | **Mon 7 Sep** | 10 findings and 5 ML questions drafted, one editor passes over all of them | all four → one editor | all |
| **G6 dry run** | **Tue 8 Sep** *(was 9 Sep)* | zip built, unzipped into an empty folder, both notebooks re-run from there. AI records complete. | Echo | all |
| **G7 submit** | **Wed 9 Sep, 18:00** *(was 10 Sep)* | uploaded, four Moodle receipts checked | Echo | all |

A day of real buffer before a 23:55 Thursday deadline is worth more than a day of polish.

---

## Part 3 — Three questions that have to close on Saturday

These are cheap to answer and expensive to leave open, because other people's work is queued
behind each one.

1. **`deliveries.delivery_note_clean` — cleaned, or copied?** DEC-018 says copied; the current
   WP2 notebook cleans it. The field has two values and no markup, so cleaning it only
   lower-cases it, which the specification's normalisation list names directly. My
   recommendation is to keep DEC-018. *Blocks:* whether Shawn writes 10 mapping rows or 11.
2. **How the master notebook gets assembled** — sections pasted in at each gate, or the file
   passed hand to hand. *Blocks:* where everyone's finished cells go, and question 3.
3. **What the mapping's evidence column cites** — a section number or a cell heading. It must
   point at the master, never at a personal notebook. *Blocks:* the last 111 rows of the mapping,
   which is the remaining half of my own deliverable.

---

## Part 4 — Next week, person by person

### Shawn — close G2, then write your mapping rows

| | |
|---|---|
| **By Sun 30 Aug** | the test evidence, not just the code: 18 public cases shown, ≥12 of our own. Watch the case where the removable marker list is closed — a generic bracket regex passes 17 and fails that one. |
| **By Tue 1 Sep** | your 10 (or 11) mapping rows: `transformation_or_derivation` and `notebook_evidence`, describing what the functions actually do. Send to me. |
| **Then** | figures 6 and 8 — deliveries × orders, and deliveries × customer segment. |

The coupon cross-check is the strongest evidence you have and it is worth citing in both your
mapping rows and the report: the structured coupon column and your extracted code agree on all
1,873 populated rows, and no row has one populated while the other is not. Every other text check
tests your output against your own pattern; this one does not.

### Yandu — you are the critical path now

| | |
|---|---|
| **By Tue 1 Sep** | consume the six tables as a reviewer: re-run them from a fresh kernel and try to break them. This is G3's signature. |
| **By Fri 4 Sep** | the validation register, executable, with the `VAL-` prefixes the template prescribes. |
| **By Fri 4 Sep** | the mapping's `overlap_or_conflict_rule` for all 111 rows. I will send it grouped — most rows take one of four stock sentences, so it is an hour, not a day. |
| **Then** | figures 5 and 7 — reviews, and reviews × products. |

Four things to save you time, already established: write tolerances as `<=` 0.01 and not `<`;
`delay_days` is `max(0, delivered − promised)` and the raw difference gives 2,985 false
mismatches; `delay_reason == 'none'` is a real category on 4,472 rows, not a missing value; and
`order_status`, `delivery_status` and `verified_purchase` are single-valued, so a
"both values present" check would raise a false failure.

### Jasmine — you are ahead; spend it on EDA

| | |
|---|---|
| **By Tue 1 Sep** | re-run after the `delivery_note_clean` decision, plus the corrections in my review note |
| **From Mon 31 Aug** | figures 2 and 3 — orders × customers, and orders × customers × order_items |
| **By Sat 5 Sep** | both figures drafted with their question, denominator and join check |

Your tables are the input everyone else now works from, so the useful thing is not more table
work — it is being the person who answers questions about them quickly this week.

### Echo — G2 review, three decisions, then the mapping's last two columns

| | |
|---|---|
| **By Sun 30 Aug** | review Shawn's functions against the specification's nine-step order and the public cases; close the three questions above |
| **By Sun 30 Aug** | fresh-kernel run of my notebook locally and on Colab; clear the stored output that prints a personal path |
| **From Mon 31 Aug** | figures 1 and 4 — orders, and orders × deliveries |
| **By Fri 4 Sep** | mapping evidence column, once the assembly question is settled |
| **From Sat 5 Sep** | assemble the master notebook; take the report editor role unless someone else wants it |

---

## Part 5 — What has not changed

Restart and Run All before every handover, from a fresh kernel, or it is not done. One editor at a
time in the master. Every AI conversation exported as we go, one chat per work package, because
we cannot shorten them afterwards. And the numbers stay derived in code — the counts we all know
by heart exist to catch mistakes, never to be typed into the pipeline.
