# A1 — What we're building, and who does what this week

Echo · 21 Aug 2026 · for Jasmine, Yandu, Shawn

---

## Part 1 — The project in plain terms

**The situation.** A Melbourne tech retailer has two old exports of the same 2018 business:
one JSON file from their commerce platform, one XML file from their operations ERP. The two
systems describe overlapping events in different shapes, different field names and different
formats. We turn that mess into six clean, related tables and then analyse them.

**What we hand in.** Two uploads on Moodle: a zip, and a PDF report.

```bash
Group001_A1_submission.zip          Group001_EDA.pdf
├── Group001_solution.ipynb         (max 10 assessed pages)
├── Group001_solution.py            - context & data scope
├── Group001_EDA.ipynb              - data-preparation assurance
├── Group001_text_functions.py      - 6-8 assessed figures
├── Group001_source_to_target_mapping.csv   - exactly 10 findings
├── Group001_AI_declaration.pdf     - exactly 5 ML questions
├── AI_records/                     - limitations & conclusion
└── outputs/  (the six CSVs)
```

**The six tables**, and the eight required links between them:

```bash
customers ──< orders ──< order_items >── products
     │           │            │              │
     │           └──< deliveries             │
     │           │            │              │
     └───────────┴────< product_reviews >────┘
                  (links to all four: order, order_item, product, customer)
```

orders 5,000 · order_items 15,685 · customers 500 · deliveries 5,000 · products 1,000 ·
reviews 7,000. **Derive these yourself — never hard-code them.** The spec forbids it and the
rubric penalises it. They are here so we can catch each other's mistakes.

**The six assessed tasks**, and where each of us sits:

| Task | What it demands | Owner |
|---|---|---|
| 1. Parse & profile the sources, complete the field mapping | structured parsers only, no regex on structure | Echo |
| 2. Produce the six standardised tables | grains, types, formats, arithmetic | Jasmine |
| 3. Regex & multilingual text processing | six functions in a separate importable file | Shawn |
| 4. Validate the processed data | executable checks with stable `VAL-` IDs | Yandu |
| 5. Focused EDA | 6–8 figures across six required categories | all four |
| 6. Findings & ML questions | exactly 10 and exactly 5 | all four |

**How it's marked** — 15 marks, and the split tells us where to spend effort:

| Area | Marks |
|---|---|
| EDA and finding quality | 3.5 |
| Core relational transformation | 3.0 |
| Regex, Unicode and text processing | 2.5 |
| Validation, reproducibility, efficiency | 2.0 |
| Structured parsing and source profiling | 1.5 |
| Multi-source reconciliation | 1.5 |
| ML questions and communication | 1.0 |

EDA is the single biggest block, so all four of us do two figures each. Nobody carries it.

**Three things about the data that shape everything else.** I checked these against our actual
files — please reproduce them yourselves before Saturday rather than trusting me:

1. **Two different duplicate problems.** 68 order IDs and 96 review IDs repeat *inside each
   file*. Separately, 500 orders and 700 reviews appear in *both* files. These need different
   handling and both must be demonstrated.
2. **The formats disagree by source.** XML dates are DD/MM/YYYY, booleans are Y/N, money is
   `AUD 2,765.47`, percentages are `10%`. JSON is natively typed with ISO dates. Everything
   normalises before comparison, not after.
3. **Where records overlap, the values agree** once normalised — I found zero disagreements
   across every comparable field. So we don't need a "JSON wins" rule. We *do* still need code
   that would detect a conflict, because that's what's being marked.

**The two habits that decide our grade.** First, `Restart and Run All` before any handover —
if it doesn't run from a fresh kernel it isn't done, and that's a full mark. Second, every AI
conversation about this assignment gets exported into `04_AI_records/` as we go. One named chat
per person per task, never mixed with personal chat, because we can't shorten them later.

---

## Part 2 — This week: person · input · output

Two gates: **G0 Sat 23 Aug** (we all understand the data) and **G1 Wed 27 Aug** (parsing done).
G2 Sat 30 Aug closes the text functions.

### Everyone, before Saturday 23 Aug — 1 hour

**Input:** `DATA/Group001_A1/` raw files, README, `public_data_dictionary.csv`
**Output:** three numbers, derived independently, brought to the G0 call — the canonical order
count, the within-file duplicate count, and the cross-file overlap count.

Four people, four routes, one answer. If we disagree, that conversation is worth more than any
document. Also read the spec once end to end — it's 15 pages and it is the actual brief.

### Echo — parsing and the field mapping · ~8 h

| | |
|---|---|
| **Input** | raw JSON + XML · spec Task 1 · `A1_source_to_target_mapping_template.csv` · data dictionary |
| **Output by Mon 25** | `parse_json()` / `parse_xml()` working in `wip_echo.ipynb`, handed to Jasmine — rough is fine |
| **Output by Wed 27** | §1 of `Group001_solution.ipynb`: structures, grains, candidate keys, formats, duplicate and overlap evidence, stated assumptions |
| **Output by Wed 27** | mapping columns `source_format`, `json_source_path`, `xml_source_path` complete; `transformation_or_derivation` drafted |
| **Reviewed by** | Shawn, Wed 27 — runs it from a fresh kernel |

Handing Jasmine the parser on Monday matters more than making §1 read well. Ugly and early
beats polished and late.

### Shawn — the six text functions · ~8 h

| | |
|---|---|
| **Input** | spec Task 3 (~2 pages) · `A1_public_text_test_cases.csv` (18 cases) · dictionary rows for the 8 text fields |
| **Output by Fri 22** | stub `Group001_text_functions.py` — all six functions, correct names and signatures, returning the input unchanged. This unblocks Jasmine on day one. |
| **Output by Sat 23** | a table: each of the 18 cases → which spec rule forces that answer. This *is* the design spec. |
| **Output by Sat 30** | real implementations + §3.2 showing all 18 public cases passing plus ≥12 of his own edge cases |
| **Reviewed by** | Echo, Sat 30 |

Start today — these functions depend on nobody. Watch TXT-18: the removable marker list is
closed, so `[NOTE]` must survive. A generic bracket regex passes 17 cases and fails that one.

### Jasmine — the six tables · ~6 h this week, main build next week

| | |
|---|---|
| **Input** | data dictionary (all 111 field specs) · spec Task 2 · Echo's parser from Mon 25 · Shawn's stubs from Fri 22 |
| **Output by Mon 25** | a written target contract: for each of the six tables, its grain, column list in dictionary order, dtype, nullability, and which source field feeds each column. No code. |
| **Output by Wed 27** | §4.1 `orders` and §4.2 `order_items` building end to end against stubs |
| **Output by Wed 3 Sep** | all six tables written to `02_Outputs/` |
| **Reviewed by** | Yandu |

The target contract before the code is deliberate. Writing down "field 11 is `home_postcode`,
string, and must keep its leading zero" is what stops the silent errors that cost field-value
accuracy marks later.

### Yandu — the validation register · ~5 h this week

| | |
|---|---|
| **Input** | data dictionary · spec Task 4 check list · README · rubric criterion E1 |
| **Output by Wed 27** | the register *specification*: one row per check — `VAL-` ID, what it asserts, which tables, tolerance, what a failure would mean. Written before any table exists. |
| **Output by Sat 30** | first executable checks running against Jasmine's `orders` and `order_items` |
| **Output by Sat 6 Sep** | full register + §5 reconciliation |
| **Reviewed by** | Jasmine |

This is the piece groups leave too late. Every check can be specified now from the dictionary
alone. Then G4 is running them, not inventing them.

---

## Two conventions to agree at G0

**The mapping opens at G1 and closes at G4.** It records what our code actually does, so it
can't be final before the code exists. Echo owns the file and its phrasing; each of us writes
the derivation line for the rows our own code produces — Shawn the 8 text rows, Jasmine the
arithmetic rows, Yandu all the overlap rules.

**One editor at a time in `00_Master/`.** Post "taking master" in the chat, merge, post "master
free". Everything else happens in your own `01_WIP/wip_<name>.ipynb`, which is yours, is never
marked, and can be as messy as you like.
