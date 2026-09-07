# Group001 — AI use declaration: Echo's contribution

**From:** Echo Zhao · **To:** Yandu (owner of the group AI synthesis) · **Drafted:** 7 Sep 2026

This is a **paste-in file**, like `report/Group001_report_Echo.md`. It carries my rows only.
Do not edit `templates/A1_AI_use_declaration_template.docx` — that stays pristine. Work from a
copy named `Group001_AI_declaration.docx`.

Two things I still owe you and cannot finish alone are listed in §5. Please chase me on them.

---

## 1. What the template actually asks for

The template has four fillable parts. Mine are B and C; A needs my line; D is yours to assemble.

| Part | What goes in it | Who fills it |
|---|---|---|
| A. Signatures table | Group number, one row per member: name, student ID, signature, date | Each member signs; Yandu collects |
| B. Conversational-AI index | One row per **complete exported chat**: member + tool/model + export filename, purpose + affected submission file/section, independent verification | Each member drafts; Yandu renumbers into one list |
| C. Inline AI completion register | Editor-supplied AI code with **no chat to export** (Copilot, Colab AI tab-complete) | Each member; **mine is NIL** |
| D. Packaging | `Group001_AI_declaration.pdf`, `Group001_AI_index.pdf`, and every export in `AI_records/` inside the submission zip | Yandu |

Two rules from the template worth repeating to the group, because they are the ones that get
people in trouble:

- **Export the complete conversation.** Selected prompts, a summary or screenshots are not
  acceptable substitutes. Do not tidy a transcript.
- **Another AI response is not independent verification.** The named evidence has to be a test,
  a comparison against the allocated source, a manual calculation, an official reference, a
  join/cardinality check, or a fresh offline rerun.

---

## 2. Part A — my signature row

| # | Full Name (printed) | Student ID | Signature | Date |
|---|---|---|---|---|
| _ | Echo Zhao | *(I will write it — not recorded here)* | *(wet/e-signature at G6)* | 10 Sep 2026 |

Four-person group, so **leave row 5 blank** as the template instructs. Group Number: **001**.
Submission names on the template line: `Group001_A1_submission.zip` and `Group001_EDA.pdf`.

---

## 3. Part B — my conversational-AI index rows

**Tool for every row below:** Claude (Anthropic), used in the Claude desktop app with the
`5196-A1` folder connected. *Yandu: the template asks for tool **and model** — I will write the
model name the app reports next to each export before signing, rather than guess it here.*

I keep **one named chat per work package** (standing rule 4 in `echo_branch/HANDOVER.md`), so
these rows map one-to-one onto chats, not onto sessions.

Row IDs are `ECHO-nn` so they cannot collide with Jasmine's, Shawn's or yours. **Renumber them
into the template's single `AI-01, AI-02, …` sequence** when you merge all four members.

| ID | Member, tool/model and complete export filename | Purpose and affected submission file/section | Independent verification |
|---|---|---|---|
| ECHO-01 | Echo Zhao · Claude (desktop app) · `Group001_AI_export_Echo_01_task1_parsing.md` | Task 1 — writing and debugging `parse_json()` / `parse_xml()`, the profiling cells and the `to_snake()` naming-exception pass. Affects `Group001_solution.ipynb` §1.1–1.3 | `check_names()` re-run on a second parse pass returns a clean list. The two sources were parsed independently and their counts reconciled to the canonical union (orders 5,000 · order_items 15,685 · deliveries 5,000 · customers 500 · products 1,000 · reviews 7,000). The 500-order / 700-review cross-source overlap was compared field by field after normalisation: zero disagreements |
| ECHO-02 | Echo Zhao · Claude (desktop app) · `Group001_AI_export_Echo_02_mapping.md` | Task 1 — completing the 111-row source-to-target mapping. Affects `outputs/Group001_source_to_target_mapping.csv` | Row count, row ids, row order and column set checked against the teaching team's `A1_source_to_target_mapping_template.csv` (111 rows + header = 112 lines, confirmed). Every `json_source_path` / `xml_source_path` was re-extracted independently by `Group001_mapping_paths.py` and compared against the CSV |
| ECHO-03 | Echo Zhao · Claude (desktop app) · `Group001_AI_export_Echo_03_reviews_wp2_wp3_wp4.md` | Reviewing Jasmine's, Yandu's and Shawn's stages as the downstream consumer (decision D2). Shaped fixes that landed in `Group001_solution.ipynb` and `outputs/Group001_validation_register.csv` | Yandu's validation register re-run offline to 65 PASS. The six standardised CSVs regenerated from a clean run and compared byte-for-byte against `review/Group001_outputs.sha256` via `review/Group001_verify.py` |
| ECHO-04 | Echo Zhao · Claude (desktop app) · `Group001_AI_export_Echo_04_master_assembly.md` | Merging the four branches into the master notebooks and the de-engineering trim that removed duplicated work. Affects `Group001_solution.ipynb` and `Group001_EDA.ipynb` | Restart-and-Run-All offline with no network: every code cell runs, and the notebook's own coverage check reports 6/6 categories, 6/6 tables and 5 relational figures |
| ECHO-05 | Echo Zhao · Claude (desktop app) · `Group001_AI_export_Echo_05_eda_figures_2_and_6.md` | EDA Figures 2 and 6 and their interpretation/limitation captions. Affects `Group001_EDA.ipynb` (Figure 2 and Figure 6 cells) and the corresponding figures in `Group001_EDA.pdf` | Figure 2's arithmetic recomputed by hand from the two standardised CSVs at both grains: line total 16,467,385.48 equals `sum(orders.order_price)` exactly, and joining order totals down to lines inflates them 3.53x. **This check caught an error in an AI-drafted caption** — see §4. Figure 6's difference (+0.12 stars, late n=707 vs on-time n=6,293) was tested against the full rating distributions and across `delay_days` 1–5 before being written up as a null result, and `delivery_experience` was confirmed to agree with `on_time_in_full` on all 7,000 rows |
| ECHO-06 | Echo Zhao · Claude (desktop app) · `Group001_AI_export_Echo_06_report_sections.md` | Drafting my seven report pieces: §2 material transformation decisions, Figures 2 and 6 captions, Findings 1 and 2, MLQ-2 and MLQ-5. Affects `report/Group001_EDA_report.md` → `Group001_EDA.pdf` | All thirteen cited MAP ids were re-read from `outputs/Group001_source_to_target_mapping.csv` before being quoted. Every number in the prose was traced back to a value the merged notebook prints; nothing was recomputed in the report or carried over from a chat |
| ECHO-07 | Echo Zhao · Claude (desktop app) · `Group001_AI_export_Echo_07_ai_declaration.md` | Drafting this handover and my rows in the group AI declaration. Affects `Group001_AI_declaration.pdf` and `Group001_AI_index.pdf` | Every row above was checked against the assignment specification and the teaching team's declaration template, and every filename, section reference and figure quoted here was confirmed to exist in the repository |

---

## 4. One thing my verification caught — please keep this visible

Figure 2's caption said the gross-to-invoiced gap was **"$3.12m of order-level coupon discount"**.
It is wrong. Recomputing from the standardised CSVs gives:

```
sum(line_revenue)     16,467,385.48   == sum(order_price), exactly
coupon discount        1,622,547.65   = sum(order_price x coupon_discount/100)
delivery_charges          71,048.88
sum(order_total)      14,915,886.94
```

$3.12m looks like a misreading of **3,127** — the count of orders carrying the `NaN` coupon
sentinel, which appears all over the briefs as a row count. The corrected sentence is already in
`report/Group001_report_Echo.md`. **The wrong number is still in `Group001_EDA.ipynb` and
`Group001_EDA_merged_0906.ipynb` and must be fixed before the notebooks are exported.**

I mention it here on purpose: it is the concrete evidence that the verification column above is
real work and not a formality.

---

## 5. Part C — inline AI completion register

**NIL for me.** I used no editor-based inline completion (no Copilot, no Colab AI
tab-complete, no Cursor). Everything I used is a conversation that can be exported in full, so
all of my work belongs in Part B. Please leave my name out of the inline register rather than
writing "N/A" into a row.

---

## 6. What I still owe you

| # | Item | Status | By when |
|---|---|---|---|
| 1 | The seven complete chat exports, in English, named as in §3 | **Not yet exported** — `AI_records/` does not exist in the repo yet | G6, 9 Sep |
| 2 | The exact model name for each export | Pending — I will read it off each chat when I export | with item 1 |
| 3 | My student ID and signature on the Part A row | At signing | 10 Sep |

If any chat of mine turns out to cover two work packages, I will **not** split the export. I
will submit the one complete export and cite it in both rows — the template explicitly allows
one conversation to support several purposes.

### How the export is actually produced (no copy-pasting)

There is a whole-account data export. In the Claude desktop app or on claude.ai:
**initials, bottom left → Settings → Privacy → Export data**. The download link arrives by
email at `ezha0053@student.monash.edu` and **expires 24 hours after it is sent**, so this is
done on 8-9 Sep, not on submission night. Not available from the mobile app.

The download is a zip of JSON, not readable transcripts. The step after it is to split
`conversations.json` into one readable file per chat, named as in §3. That conversion is
scripted and reproducible; the verbatim message text is carried through unaltered, which is
what "complete export" requires — nothing is summarised, reordered or trimmed.

**Check on receipt:** that all seven A1 chats are present in the export. Anything missing gets
handled separately rather than reconstructed from memory — the template is explicit that a
transcript is never invented.

---

## 7. Notes for you assembling the group file

1. **Everyone declares, including anyone who used nothing.** The template says the declaration
   is completed and signed even when no member used generative AI.
2. Renumber all four members' rows into one `AI-01…` sequence. The template ships with three
   blank rows — add rows rather than dropping anyone's.
3. Check that every export filename in the index actually exists in `AI_records/`, and that
   every file in `AI_records/` is cited by some row. A mismatch either way is what a marker
   notices first.
4. Watch the verification column for the four of us: if any row's evidence is "Claude checked
   it" or "I asked another model", that row fails the template's own definition and needs
   real evidence substituted.
5. Final packaging: signed declaration → `Group001_AI_declaration.pdf`; the index →
   `Group001_AI_index.pdf`; both plus `AI_records/` inside `Group001_A1_submission.zip`.
6. All four of us should be able to explain any AI-assisted item we submit — that is one of the
   things the signature block asserts, and it is also our own standing rule 1.
