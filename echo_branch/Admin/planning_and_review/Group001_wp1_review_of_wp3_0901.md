# WP1 review of WP3 — `wip_Yandu_Wang_8.31_update.ipynb`, 1 September 2026

Reviewed against `wip_Yandu_Wang_G1_VAL.ipynb` (31 Aug) and the six exported CSVs.
Reviewer: Echo (WP1). Read with `Group001_wp1_review_of_wp3_0831.md`.

---

## 1. Every gap raised on 31 Aug has been addressed

The register is now **65 checks, all PASS**, up from 63, and four things that were
weak points are now strengths.

| Raised 31 Aug | Now |
|---|---|
| VAL-ARITH-05 was `record(..., True, ...)` — could never fail | Builds the allowed discount set **from the raw files** and asserts the export is a subset. Prints `[0, 5, 10, 15, 20, 25]` from both sides. |
| No numeric range checks anywhere | New VAL-ARITH-08: `rating` 1–5, `quantity` ≥ 1, `helpful_votes` ≥ 0, no negative money across six columns. This is the spec's "sensible numeric ranges" bullet. |
| 63 PASS with no negative control | Two now. The planted-conflict fixture in §6.3, and the §6.4 control showing `order_price × 1.1 + delivery` reproduces **0 of 5,000** totals while the correct formula reproduces 5,000. |
| Six markdown cells still read "Replace at G2" | All six written, as observed result + status + interpretation. |
| `register` never written to CSV | Written now. |

Two more things worth naming because they are the difference between a register that
scores and one that merely exists:

- The **conflict detector is written and unit-tested here** even though it cannot run
  until assembly. Testing it on a four-row fixture with a planted disagreement, then
  on the repaired fixture, is the honest way to show a detector works when the real
  data has nothing to detect.
- `count_overlap` counts **distinct keys** on `source_system == 'both'` rather than
  halving a row count. That is the right choice and it matters: halving gives
  513 / 1,600 / 513 / 721 instead of the true 500 / 1,559 / 500 / 700, because the
  within-source duplicates inflate the row count.
- §6.6 already treats `delivery_note_clean` as a structured category with its own
  VAL-TEXT-01b, separate from the three narrative fields. That is DEC-021 implemented
  correctly, before the decision was circulated.

## 2. The one thing that still costs marks: the three gaps are invisible in the file

VAL-FLOW-09, -10 and -12 are printed as `NOT RUN` but never passed to `record()`. So
the register DataFrame — and the CSV the report will cite — says **65 of 65 PASS and
nothing else**. A reader of the file cannot tell that three required checks are
pending; only a reader of the notebook's scrollback can.

That is the wrong way round. A register whose own file admits three deferred checks is
more credible than one that silently omits them, and C2/E1 reward exactly that
honesty. Two-line fix:

```python
def record(val_id, passed, evidence, note=""):
    """Write down one check: its ID, its status, what we saw, and what it means.

    `passed` may be True, False, or None for a check that cannot run yet.
    A real gap that we name is worth more than a pass we faked.
    """
    status = "NOT RUN" if passed is None else ("PASS" if passed else "FAIL")
    RESULTS.append({"id": val_id, "status": status, "evidence": evidence, "note": note})
    print(f"{val_id:18s} {status:7s} {evidence}")
```

then replace the bare `print` loop at the end of §6.3 with:

```python
for vid, why in [
    ("VAL-FLOW-09", "find_conflicts on the combine_sources output; needs the master notebook"),
    ("VAL-FLOW-10", "compares the two copies of each within-source duplicate; needs the master"),
    ("VAL-FLOW-12", "count_overlap on <table>_marked; the CSVs correctly do not carry the marker"),
]:
    record(vid, None, why)
```

The summary then reads `{'PASS': 65, 'NOT RUN': 3}`, and the three rows carry their
own reason. Nothing else changes.

## 3. Path resolution — a G6 blocker, worth fixing now

`find_dir()` falls back to `BASE.rglob(marker)` and takes the first match. In the
saved run it resolved to:

```
raw input : 5196/assignment 1/Group001_A1/DATA/Group001_A1/raw_input
tables    : 5196/assignment 1/Group001_A1
```

Three problems, in order of how much they cost:

1. **We cannot tell which export was validated.** `rglob` returning the first match
   means a stale copy of the six CSVs sitting anywhere under `BASE` would be picked
   up silently, and every check would pass against the wrong file. The row counts look
   right, so nothing would flag it. Please confirm against these — they are the
   sha256 of the current `outputs_wip_jasmine/` files, which a fresh run of WP2's
   notebook reproduces byte for byte:

   ```
   2fe07080…  Group001_orders_standardised.csv
   f5ec4765…  Group001_order_items_standardised.csv
   3a299a08…  Group001_customers_standardised.csv
   600bbaab…  Group001_deliveries_standardised.csv
   c81738a7…  Group001_products_standardised.csv
   81294086…  Group001_product_reviews_standardised.csv
   ```

   Cheapest permanent fix: print the resolved path *and* size of each table file at
   §0.1, so the run says out loud what it read.

2. **`assignment 1` has a space in it and is not a `Group001_` name.** Appendix A
   checks the naming convention and bans student-specific paths. Any folder that is
   only on one person's machine has to be off the resolution list before G6.

3. **The register is written into the data folder.** `TABLE_DIR` is where the CSVs
   were *read* from, so `Group001_validation_register.csv` lands beside them. It
   should go to a personal outputs folder while drafting, and to the run's `outputs/`
   at assembly — the same D9 rule the rest of us are following.

## 4. Two small notes

- **VAL-ARITH-07** checks `review_length_chars` against `review_body_clean.str.len()`
  — which is how WP2 computes it, so the check confirms consistency rather than
  correctness. It passes today because no review body is the literal `NaN`. If one
  ever were, the spec says the counts must not count those three characters and both
  sides would be wrong together. Worth one sentence in the interpretation so the
  limitation is on the record rather than discovered by a marker.
- The `note` column is present but empty on all 65 rows. The interpretations live in
  the markdown, which satisfies the spec — but then the exported CSV carries a column
  that is always blank. Either drop it or put a short phrase in it; an always-empty
  column in a deliverable invites the question.

## 5. New check worth adding, from WP2's `delivery_note_clean` work

`deliveries.delivery_note_clean` turns out to be the same partition as three other
columns, row for row, across all 5,000 deliveries — zero disagreements on every pair:

- `delay_reason == 'none'`
- `on_time_in_full == True`
- `delay_days == 0`
- `delivered_date <= promised_date` (your §6.5 already prints the 528)

Four columns produced by different parts of the pipeline agreeing on one 5,000-row
split is a strong cross-field consistency check — and it fails loudly if any one of
them is ever mis-parsed, which is more than most of the register can say. Suggested as
a single new row, e.g. `VAL-FLOW-16`, built from the four columns rather than from a
number typed in.

It is also a finding for the report: the note carries no information the outcome
columns do not already carry, so it is a redundant feature that would leak the target
into any model predicting late delivery.
