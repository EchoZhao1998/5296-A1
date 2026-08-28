WP2 complete — six tables built, exported, and reconciled
All six output tables are built end to end and the notebook does Restart and Run All clean. 01_WIP/wip_jasmine.ipynb, outputs in outputs_wip_jasmine/.
Row counts, all derived from set unions — nothing hard-coded:

orders 5,000 · order_items 15,685 · customers 500 · deliveries 5,000 · products 1,000 · product_reviews 7,000
Arithmetic reconciles exactly. line_revenue, order_price, tax_amount and order_total all sit inside the published 0.01 tolerance with 0 rows outside and max diff 0.0000. Two things had to be fixed to get there, both documented in §4.0.3: pandas .round(2) uses half-even and disagrees with the Python round() the source was generated with, and > 0.01 is too strict for a tolerance that means <=.
Echo — my 101 mapping rows are in outputs_wip_jasmine/Group001_mapping_wp2_rows.csv. I filled only transformation_or_derivation and notebook_evidence; the key columns are untouched, so merging on (output_table, target_field) is safe. notebook_evidence cites section numbers, which stay valid in the merged notebook because D4 keeps the template's numbering.
Shawn — 11 rows are left as TODO-WP4 placeholders, not 100. They are yours to write, because the text has to describe your functions:

orders           customer_note_clean
orders           promo_code
deliveries       delivery_note_clean
products         product_description_clean
product_reviews  review_body_clean
product_reviews  review_body_latin_analysis
product_reviews  review_length_chars
product_reviews  review_word_count
product_reviews  contains_non_latin_script
product_reviews  extracted_order_reference
product_reviews  extracted_product_sku

Two things about that list you need to know before you start:

promo_code, extracted_order_reference and extracted_product_sku do not exist in either source file. I checked — all three columns come out 100% literal 'NaN'. They are not copy-able; they have to be extracted from narrative text. The sentinels currently in those columns are placeholders so the tables conform to the contract, not results.
delivery_note_clean is different — it is populated, with a direct copy of the raw note. Do not read "has values" as "already done". It needs clean_narrative_text like the other three *_clean fields. This settles open question Q1; the evidence is the field name plus consistency with customer_note_clean, product_description_clean and review_body_clean, which are all yours.

Please confirm the list is exactly 11 and nothing is missing or wrongly assigned. If the boundary is off, better to find out now than at G3.
Yandu — still waiting on your call on the overlap marker: do you want the JSON-only / XML-only / both key sets handed over before deduplication, or a "both" column carried on the deduplicated rows? It changes my dedup step, so the earlier the better.
Everyone — one open question for G1. In public_data_dictionary.csv all 21 product_reviews fields are nullable = False, yet four of them are produced by functions that can legitimately return the literal 'NaN'. Does nullable = False forbid the sentinel, or only forbid an empty cell? We should agree on one reading and record it as a decision, because the validation rules differ.
Correction to my earlier notes — I reported delay_reason == 'none' as 2,516. That was the JSON-only figure. The canonical count across all 5,000 deduplicated deliveries is 4,472. I'll fix 03_Docs/Group001_review_notes_jasmine_0827.md


@Yandu Wang @Siyuan Shao 

WP4 has landed and the whole pipeline has been re-run against it.
Group001_text_functions.py was picked up by §3, so §4.1, §4.4, §4.5 and §4.6 are no longer provisional. Restart and Run All is clean end to end. Row and column counts unchanged: orders 5,000×23 · order_items 15,685×6 · customers 500×20 · deliveries 5,000×20 · products 1,000×21 · product_reviews 7,000×21.
Shawn — three results for you.

extract_promo_code is cross-validated. coupon_code comes from a structured source column; promo_code comes from your regex on the free-text note. On the 5,000 canonical orders: 1,873 rows carry both and 0 disagree, 3,127 carry the sentinel in both, and 0 rows have one populated while the other is not. Independent routes, complete agreement. This is Yandu's VAL-TEXT-13 and it now has a real baseline rather than a vacuous one.
A bug on my side that would have destroyed your work silently. §4.1 called extract_promo_code and then overwrote the whole column with the 'NaN' placeholder I had added while you were still building. It has been removed. Worth flagging because it would not have raised — the column would simply have been all sentinel, and it took the all-sentinel guard to catch it.
delivery_note_clean now goes through clean_narrative_text. The source column arrives under the target name in deliveries — unlike the other three, there is no _raw in the source — so I added delivery_note_raw per DEC-014 before cleaning, rather than mapping in place. Mapping in place would have destroyed the input to your own function.

Yandu — the "both" marker is in, on all four shared tables.
source_system takes {JSON, XML, both} on <table>_marked, which is the frame immediately before conform_to_contract. It is stripped from the exported CSVs by contract selection, exactly as VAL-SCHEMA-08 requires. <table>_marked exists for all six tables, including the single-source ones, so VAL-FLOW-12 needs no special case.
The marker is written before deduplication. keep='first' retains the JSON copy of a shared key, so marking afterwards would lose the fact the column exists to record. It also keeps both copies of a duplicated key field-identical — within-source pairs are both JSON, cross-source pairs are both both — so the field-identity evidence behind DEC-017 still holds with the column present.
My own check recomputes the intersection of the two source key sets and compares it against the marker rather than trusting it, per your "checked rather than trusted". Ready for you to re-run the register.
Everyone — the all-sentinel guard now switches on whether §3 loaded the real functions or the placeholders, so it stays meaningful in both states instead of needing a hand edit at the moment WP4 lands. That edit is exactly the one that gets forgotten.

@Yandu Wang 
Heads-up: the exported filenames now carry the _standardised suffix, per spec §7 and Appendix A — Group001_orders_standardised.csv and so on. I had them without it. The old-named copies in 01_WIP/outputs_wip_jasmine/ are deleted, so anything still pointing at the old names will fail loudly rather than read a stale file.
Echo — worth checking WP1's path constants use the suffixed names too.


@Echo Zhao 
Two things from my side.
Export filenames now carry the _standardised suffix — Group001_orders_standardised.csv and so on. Spec §7 and Appendix A both require it and I had them without. Worth checking WP1's path constants match, since B1's HD descriptor starts with "present with the required filenames" and it's the cheapest possible way to lose that mark.
Group001_mapping_wp2_rows.csv has been regenerated and is back in 01_WIP/outputs_wip_jasmine/ — I deleted it by accident while clearing the old-named exports, so if you saved a link it may have broken. 111 rows, 100 written by WP2, 11 left as TODO-WP4 placeholders for Shawn. Key columns untouched, so merging on (output_table, target_field) is still safe.


@Siyuan Shao 
Your functions are integrated and the whole pipeline has been re-run against them. Three things you need before you write your 11 mapping rows.

The three previously-empty fields now have real values — promo_code, extracted_order_reference, extracted_product_sku. Write the transformation text to describe what your functions actually do, not what the plan said they would do; A2 marks a row only when all six columns are right.
delivery_note_clean is now cleaned, not copied. I call clean_narrative_text on it in §4.4, after adding a delivery_note_raw column per DEC-014 so your function's input survives. It is still your mapping row to write.
extract_promo_code is cross-validated against an independent source. coupon_code is a structured source column; your promo_code comes from regex on the free-text note. On the 5,000 canonical orders they agree on all 1,873 populated rows, and no row has one populated while the other is not. That second figure rules out both missed and spurious extractions. Worth citing in your mapping text and in the report — it is stronger evidence than any shape check, because every other text check tests your output against your own pattern.