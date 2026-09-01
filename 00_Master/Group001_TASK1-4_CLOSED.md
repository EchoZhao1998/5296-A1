# Tasks 1–4 are closed — 1 September 2026

**Read the whole thing, not just your own section.** It is four short sections and it is
the only document that describes the whole pipeline as it now stands.

Nothing here needs a reply and nothing here needs you to revise your notebook. Your work
has been assembled into the master notebook, the small defects were fixed in the assembled
copy, and this note tells you exactly what was changed in your part and why. If you disagree
with a change, say so and we change it back — but do not re-do work.

---

## What now exists

`00_Master/` in the shared folder:

```
00_Master/
├── Group001_solution.ipynb    the whole workflow, one file, 184 cells
├── Group001_solution.py       exported from it, parses cleanly
├── Group001_EDA.ipynb         scaffold: loads the six CSVs, 8 figure slots with owners
├── Group001_text_functions.py the six published functions
├── Group001_own_text_test_cases.csv
├── requirements.txt
├── templates/A1_public_text_test_cases.csv
└── outputs/
    ├── the six standardised CSVs
    ├── Group001_source_to_target_mapping.csv     111 rows, complete
    └── Group001_validation_register.csv          68 checks
```

**The master notebook runs Restart-and-Run-All from a fresh kernel with zero errors, in about
40 seconds, and writes all eight files.** It follows the teaching team's template numbering
exactly: 0 configuration · 1 parse and profile · 2 mapping · 3 text functions · 4 the six
tables · 5 reconciliation · 6 validation register · 7 export · 8 reproducibility record.

**The six CSVs it produces are byte-for-byte identical to the ones we have been working
against** — compared by sha256, all six. So no figure, no check and no number anyone has
already derived needs recalculating.

**Validation: 68 checks, 68 PASS, 0 FAIL, 0 deferred.**

---

## Jasmine — Task 2, and thank you for the `delivery_note_clean` call

Your six tables went into the master **unchanged**. Every number reproduces: 5,000 / 15,685 /
500 / 5,000 / 1,000 / 7,000, all six primary keys unique and complete, all eight foreign keys
with no orphans, the whole monetary chain inside 0.01 on every row, and the six exported files
identical to yours to the byte.

You were right about `delivery_note_clean`, and the evidence is stronger than either of us
said. It is not only the same split as `delay_reason == 'none'` — it is the same partition,
**row for row with zero disagreements across all 5,000 deliveries**, as `delay_reason`,
`on_time_in_full`, `delay_days == 0` *and* `delivered_date <= promised_date`. Four columns
built by different parts of the pipeline agreeing on one split. That is now finding 10 in the
report and it is also why it must never be a predictor.

Four things were changed in the assembled copy:

1. **The raw-byte diagnostic now runs.** The lower-casing fix was right; the indentation broke
   it, so the cell was raising `IndentationError` and printing nothing. It is now Section 1.6,
   and it searches both spellings — the JSON writes `couponCode`, the XML writes `Coupon_Code`,
   so a single spelling gives a column of zeros that reads as absence.
   It produces something better than we expected: `<Coupon_Code>` appears 1,048 times paired
   against 1,770 self-closing, and there are exactly 1,048 `promo` markers in the same file;
   the JSON says 1,051 and 1,051. **In each file separately, every populated coupon code has a
   promotion marker in its note and no marker exists without one** — read straight from the
   bytes, by neither parser. That is what makes VAL-TEXT-13 a real test of Shawn's extractor.
2. **The B1/B2 coverage cell is now Section 7.1 and reads the exported files.** It was printing
   "before WP4 lands: 92.20%" from a static list. Asked properly — a field is unfilled only if
   it is sentinel or blank on *every* row — the answer is **100.00% on all six tables**. It was
   understating your own work. The rubric reference was also wrong: the 95 / 90 thresholds are
   real but they sit under B1 and B2, not "section 4.2".
3. **The export is guarded** (Section 7). It asserts the six text functions are the published
   module before writing, so a run built on anything else cannot reach `outputs/` silently.
4. **`§4` cells were reordered to 4.2 → 4.1 → 4.3 → 4.4 → 4.5 → 4.6**, with a short markdown
   cell saying why: `order_price` is the sum of the canonical line revenues, so `order_items`
   has to exist first. Your build order, just tightened, and now explained to a marker.

Your Section 2 mapping rows were not merged as a file — the marker will not have
`outputs_wip_jasmine/`. The same wording is generated inside the master at Section 2.3.

**Nothing to do.** For the rest of the week: Figures 3 and 4, findings 3–4, ML question 1, and
the report's limitations and conclusion.

---

## Yandu — Task 4, and the four checks that were deferred now run

Your register went into the master as Section 6, essentially unchanged, and it is the strongest
part of the notebook. What you did that the rubric explicitly rewards: every expected number is
worked out from the raw files in the same cell that checks it, nothing is typed in, and the two
negative controls prove the checks have teeth rather than asserting it.

**VAL-FLOW-09, -10, -11 and -12 now run.** You were right that they need the frame from before
deduplication and that no personal notebook has it. The master does: Section 5 rebuilds it, and
your `find_conflicts` and `count_overlap` are wired to the real frames. Results:

- **VAL-FLOW-09** — 8,098 rows carry a key that appears more than once; **0 field disagreements**
  after normalisation, across all six tables.
- **VAL-FLOW-10** — within-source repeated keys are 68/68 for orders and deliveries, 201/214 for
  items, 96/96 for reviews, and there are **0 field differences** between the two copies of any
  of them. This is what makes `keep="first"` safe rather than lossy.
- **VAL-FLOW-11** — your planted-conflict fixture, kept as the negative control.
- **VAL-FLOW-12** — keys carried by both files: 500 orders, 1,559 items, 500 deliveries, 700
  reviews, matching the raw key-set intersections. Your point about counting distinct keys
  rather than halving a row count is why these are right: halving reads 513 / 1,600 / 513 / 721.

The register is **68 PASS, 0 FAIL, 0 NOT RUN**, and it is written to
`outputs/Group001_validation_register.csv` so the report can cite `VAL-` IDs from a file.

Two other changes: `record()` now accepts `None` for a check that cannot run, so a future gap
appears in the exported file as `NOT RUN` instead of vanishing; and the path resolution was
replaced — the `rglob` fallback could silently read a stale copy of the six CSVs, and Section 6
now validates the tables **as they are about to be written**, through an in-memory round trip
with the exact export formatting, so a formatting fault is caught before export rather than
after.

**Nothing to do.** For the rest of the week: Figures 1 and 7, findings 5–6 and 9–10, ML
question 4, and the report's data-preparation assurance section — the one that cites `MAP-` and
`VAL-` IDs. That section is yours because you are the only one who can write it quickly.

---

## Shawn — Task 3, and the three near-match defects are fixed

Your six functions are in the master as Section 3.1, imported from the module rather than
redefined, so the module the marker imports is the module the notebook used.

**All 44 test cases pass — 18 public and 26 of our own.** Three small defects were fixed, all
in the boundary handling, and **not one value on the real data changed**: the six exported CSVs
are byte-identical before and after the patch. These are the cases a private test probes:

| Input | Before | After |
|---|---|---|
| `ORDER-HORD001451` | `HORD001451` | `NaN` |
| `HORD१२३४५६` | `HORD१२३४५६` accepted | `NaN` |
| `SKU-VEL१२३` | `SKU-VEL` (silently truncated) | `NaN` |
| `SKU-VEſ00` | `SKU-VES00` | `NaN` |

The change is two lines per extractor. The boundary went from `(?<![A-Z0-9])` to `(?<![\w-])`
on both sides — `\w` is Unicode-aware, so a Devanagari digit next to the token now rejects it
instead of letting the match end early — and each extractor returns the token only if it is
ASCII. `\d` and `[A-Z]` match non-ASCII digits and letters under `IGNORECASE`, which is what
let all three through.

**Your ten mapping rows are written**, from your code rather than from a description of it —
each names which function produces the field and which value it reads, because that is the
distinction that matters: extraction runs on the **raw** text before cleaning removes the
wrapper it looks for, and the measure and analysis fields run on the **cleaned** text. Check
Section 2.3 of the master and tell me if any wording misstates what your code does.

**Nothing to do.** For the rest of the week: Figures 5 and 8, findings 7–8, ML question 3, the
AI declaration and the chat-export index, and reviewing the master notebook.

---

## Echo — what is actually left

Tasks 1–4 are closed. What remains:

1. **Read Section 1's markdown.** Several cells still carry working prompts — "READ ITS
   OUTPUT", "Write the reading here from the two outputs above". They are yours and they are
   the last unfinished prose in the notebook. A marker reads them.
2. **Q5 and Q6 are closed** as DEC-025 and DEC-026, and the mapping is finished: 111 rows, no
   blanks and no placeholders in any of the nine columns, checked by re-reading the written
   file rather than the frame in memory. **A2 is done.**
3. **Everything else is EDA and the report**, per the endgame plan.

---

## The mapping, and the rules it was closed on

All 111 rows are complete. The two judgement columns were written as general rules rather than
111 individual sentences, because the rule genuinely is a property of the table and 111
sentences would invite a reader to look for a distinction that does not exist.

**`transformation_or_derivation`** takes one of four shapes, and which one is looked up, never
decided by hand: a **cast** where the dictionary types the field and the two sources spell it
differently (59 direct copies, 15 numeric casts, 7 datetime, 7 boolean, 6 money, 1 percent); a
**direct copy**; a **recomputation** for the five monetary fields the specification defines by
formula; and a **text derivation** for the ten fields with no source column of that name. Money
is identified by the dictionary's own `comparison_rule`, which is the same fact Section 4 reads,
so the two cannot drift apart.

**`overlap_or_conflict_rule`** has three shapes:

- **61 rows, four tables from both files** — concatenate, normalise, then one row per business
  key with `keep="first"`. Deduplication *after* normalisation, so `10` against `10%` and
  `true` against `Y` are not read as disagreements. A key whose two sources give different
  non-missing values is recorded as a conflict in the register rather than resolved by a silent
  precedence rule.
- **40 rows, two single-source tables** — customers exist only in the JSON and products only in
  the XML, so no cross-source overlap is possible. Saying so is the honest entry.
- **10 rows, computed fields** — derived after deduplication from the canonical row, so they
  inherit the rule of the raw field they are computed from and are never compared in their own
  right.

**`notebook_evidence`** cites the master's section numbers — Section 4.1 through 4.6 by table,
plus "(functions Section 3.1)" for the ten derived fields. Section numbers rather than headings,
because the numbering comes from the supplied template and is now fixed.

Two independent checks guard it: the ten text-derived rows must be exactly the ten rows the path
search found sourceless, and the row order must still match the dictionary's own field
positions. Both are asserted in Section 2.5, and the file is re-read from disk to check it.

---

## One thing worth knowing about the whole pipeline

The notebook is written so that its claims are *derived* rather than declared, and that is the
single thing that separates it from a notebook that merely works:

- `derived` is not a list anyone wrote — it is what is left when no field of that name exists at
  that grain in either file, and it lands on exactly the ten text fields by a second route.
- The canonical row counts are the union of business keys read from the raw files, not numbers
  typed into an assert.
- The conflict detector is shown finding a planted conflict before it is trusted to report zero.
- The wrong tax formula is shown reproducing 0 of 5,000 order totals, which is what makes the
  right one mean something.

If anyone is asked in a demo "how do you know this is right?", that is the answer: nothing in
the notebook is asserted, everything is checked against the files.

---

## Addendum, later on 1 Sep — how to actually run this

**Only one person needs to run `Group001_solution.ipynb`.** It has already been run; the six
CSVs in `outputs/` are its output. The EDA notebook reads those CSVs and nothing else, so three
of us never need to touch the pipeline. Four people running it in four environments is four
chances for the outputs to diverge, for no benefit.

**So the working set for the week is three things:**

1. `outputs/` — the six CSVs
2. `Group001_EDA.ipynb` — already loads them, already has your two figure slots
3. `eda_briefs/Group001_EDA_brief_<your name>.md` — paste it into your own AI chat

**On Colab.** Put `00_Master/` in the shared Drive folder and open `Group001_EDA.ipynb` from
there. Its first cell mounts Drive, searches for `Group001_orders_standardised.csv` and changes
directory to wherever it finds it, so you do not have to edit a path. If you would rather work
locally, download `outputs/` and the notebook into one folder and it will find them there too.

**If you do want to run the solution notebook**, it needs the allocated package. Put
`raw_input/` beside the notebook, or keep `Group001_A1/` next to it — both layouts work, both
have been tested from a clean folder. It takes about 40 seconds and writes everything in
`outputs/` from scratch.

**The notebook was trimmed for submission.** 184 cells down to 168: the coloured notes addressed
to each of us by name, the pasted screenshot, the working prompts and the teaching examples are
gone, along with every decision-log code and every `→ YANDU` hand-off. Six groups of adjacent
code cells were merged. The explanatory markdown stays, because that is precisely what the top
band asks for — "profiling assumptions accurately profiled with traceable evidence" — and
cutting it would cost marks rather than save them.

**The six CSVs are unchanged after all of that.** Verified by hash again after the trim.
