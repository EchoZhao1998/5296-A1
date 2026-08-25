# HANDOVER — Echo ⇄ Claude, FIT5196 A1

**Purpose.** This file carries context between chat sessions. When Echo opens a new chat, she
attaches this file first; Claude reads it and continues without re-deriving anything. At the
end of a working session, Claude updates §7 and any section that changed.

**Last updated:** 21 Aug 2026 · Session 1 · by Claude

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

All derived by Claude from the actual files on 21 Aug 2026. **Never hard-code these into the
pipeline** — the spec forbids it and rubric C1/E1 penalise it. They exist to catch mistakes.

| Entity | JSON | XML | Canonical |
|---|---|---|---|
| Orders | 2,818 → 2,750 unique | 2,818 → 2,750 unique | 5,000 |
| Order items | 8,826 → 8,625 | 8,833 → 8,619 | 15,685 |
| Deliveries | nested, 1/order | nested, 1/order | 5,000 (all orders `Completed`) |
| Customers | 500 | absent | 500 |
| Products | absent | 1,000 | 1,000 |
| Reviews | 3,946 → 3,850 | 3,946 → 3,850 | 7,000 |

- **Within-source duplicates:** 68 order IDs, 96 review IDs — same counts in each file, all
  field-identical to their twin.
- **Cross-source overlap:** 500 orders, 700 reviews — zero field disagreements after
  normalisation. No JSON-over-XML precedence rule needed; conflict *detection* still required.
- **Arithmetic:** recomputing line revenue → order price → tax → total reproduces source values
  exactly (0 mismatches at 0.01 tolerance).
- **Source structures:** JSON `{exportMetadata, customerProfiles[500], orders[2818]{header,
  shoppingCart[], delivery}, productReviews[3946]}` · XML `OperationsExport{Export_Metadata,
  Orders/Order[2818]{Header, Shopping_Cart/Item[], Delivery}, ProductCatalogue/Product[1000],
  ProductReviews/Review[3946], WarehouseDirectory/Warehouse[3]}`.
- **Formats:** XML dates DD/MM/YYYY, booleans Y/N, money `AUD 2,765.47`, percent `10%`;
  JSON natively typed, ISO dates. Empty coupon → literal `NaN`.
- `WarehouseDirectory` (3 warehouses, lat/long) maps to no required output field. Useful for
  EDA distance checks; must not become a column in the six CSVs.
- `review_title` — checked all 7,892: zero contain markup, markers, URLs or entities, and none
  contain uppercase. Direct copy is defensible; that count is the evidence.

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
| Q1 | `delivery_note_clean` — apply `clean_narrative_text` or direct copy? Source is already clean; only effect is lower-casing. Field name ends `_clean`, which argues for applying it. | Echo + Jasmine | G3 |
| Q2 | Canonical-row rule for exact duplicates — must be deterministic and documented, even though the choice is arbitrary | Yandu | G4 |
| Q3 | Whether to rename Drive folder `G1_A1` → `Group001_A1` to remove filename-prefix risk | Echo | G0 |
> Echo: already renamed, and I have changed the text above.

Every answered question becomes a `DEC-` row in `03_Docs/decision_log.md`.

---

## 7. Session log

### Session 1 — 20–21 Aug 2026
Read spec, rubric, data dictionary, both templates, and profiled both raw files.
Produced: `Group001_A1_Workflow_and_Roles.md` (full plan, definition-of-done per rubric
criterion, ten HD-losing traps), `Group001_Week1_Brief.md` (group-facing: project in plain
terms + person/input/output for week 1), `Group001_source_to_target_mapping.csv` (cross-check
copy, all 111 rows with paths), the Notion panel, and this file.
Corrected one earlier error: initial section numbering and EDA figure order did not match the
teaching team's templates. Now aligned to the templates verbatim.

**Next session should:** start Echo's Task 1 — build `wip_echo.ipynb` on the Mac with
`parse_json()` and `parse_xml()`, then the profiling that evidences §4 above. Priority is
handing Jasmine a working parser by **Mon 25 Aug**; §1 prose and the mapping columns come after.

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
