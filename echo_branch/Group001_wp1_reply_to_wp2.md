# WP1 → WP2 · reply to the §2 handover

**From** Echo (WP1) · **To** Jasmine (WP2) · 28 Aug 2026  
**Re** `outputs_wip_jasmine/Group001_mapping_wp2_rows.csv` and related checks

Thanks — the handover merged cleanly. All 111 `(output_table, target_field)` pairs matched my skeleton, so no manual CSV editing was needed. The mapping now has 101 rows written, 10 waiting on Shawn, and two columns owned elsewhere.

The merge is in **§2.4 of `wip_echo.ipynb`**, so the same file can be reproduced by re-running both notebooks.

Three points need attention.

---

## 1. `deliveries.delivery_note_clean` should not be in `WP4_DERIVED`

Your `WP4_DERIVED` set has 11 entries, while my §2.1 derives 10. The extra row is:

`('deliveries', 'delivery_note_clean')`

This is a real field at the delivery grain in **both** source files:

- JSON: `orders[].delivery.deliveryNoteClean`
- XML: `Orders/Order/Delivery/Delivery_Note_Clean`

**DEC-018** confirmed on 23 August that this is structured data, not narrative text. Across the 5,000 canonical deliveries, it has only two values: `Carrier scan reconciled` and `Delivered within promise`. There is no markup, URL, entity, or non-ASCII content. The `_clean` suffix is simply the source system's field name.

I added this row myself because assigning it to WP4 meant that nobody would write it.

**Action:** Please remove `('deliveries', 'delivery_note_clean')` from `WP4_DERIVED` in your §2 and re-run it before G3.

The mismatch happened because the two sets are built differently:

- Your set is a manually declared list.
- My set is calculated from the fields left after checking the source data.

The two approaches have different strengths. The declared list can capture a judgement; the calculated set follows the data. Keeping both and checking that they agree is useful because it catches mismatches like this.

## 2. `notebook_evidence` — no change needed yet

Your `§4.1`–`§4.6` references are correct for `wip_jasmine.ipynb`. However, the final deliverable must reference the **master notebook**.

Q6 is still open and depends on Q5, which we will settle at G2. Therefore, I have kept `TODO-EVIDENCE` for now and saved your section numbers in `wp2_section_hint` in `outputs_wip_echo/Group001_mapping_working.csv`.

Nothing is lost. I will update the final evidence references from the master notebook after Q5 and Q6 are settled.

**No action needed from you.**

## 3. Two checks need their prose corrected

These do not affect the six tables; the tables are correct. The issue is that the notebook prose does not match what the cells actually show.

### A. `coupon_code` / `promo_code` cross-check

The current markdown says:

> “1,873 rows carry both and disagree on none, 3,127 rows carry the sentinel in both, and no row has one populated while the other is not.”

But the cell actually prints:

```text
rows where the populated/sentinel pattern differs: 1873
0 rows carry both, 0 disagree