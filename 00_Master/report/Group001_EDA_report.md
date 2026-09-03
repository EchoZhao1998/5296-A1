# Group001 — FIT5196 A1 EDA report (assembly draft)

**Hard limit: 10 pages, introduction to conclusion.** Cover, contents and references sit
outside the limit; appendices are not marked. The budget below is what makes 10 pages
achievable without a trimming crisis on 9 September. Write to the cap, not past it.

| § | Section | Owner | Pages | Word cap |
|---|---|---|---|---|
| 1 | Problem context and data scope | Echo | 0.5 | 300 |
| 2 | Data-preparation assurance | Yandu | 1.0 | 550 (a compact table beats prose) |
| 3 | Eight assessed visualisations | each owner | 4.5 | **≈130 per figure** |
| 4 | Ten numbered findings | each owner | 1.75 | **≈90 per finding** |
| 5 | Five ML questions | each owner | 1.75 | **80–120 per question**, or one compact table |
| 6 | Limitations | Jasmine | 0.3 | 180 |
| 7 | Conclusion | Jasmine | 0.2 | 120 |
|   | **Total** | | **10.0** | ≈3,900 |

Per figure, half a page means roughly a 7 cm image plus about 130 words. Those 130 words
must carry all six required elements: the analytical question, the observation unit and
denominator, the tables and join keys, the result, and one material limitation. The chart
choice and the labelling are judged from the figure itself, so they cost no words.

**No code listings in the report.** The specification allows a short expression only where
it is needed to explain an assessed decision — for example naming `round(order_price / 11, 2)`
when justifying that GST was divided out rather than added. Screenshots of cells, function
definitions and `df.head()` dumps do not belong here. This says nothing about the notebooks:
those must still show their code and their output.

---

## 1. Problem context and data scope

*(Echo — 300 words)*

This report analyses one year of transactional records from an Australian online electronics
retailer. The retailer's operational history arrived as two exports of the same underlying
system: a JSON file and an XML file, each describing orders, their shopping carts, their
deliveries and their product reviews, with the JSON additionally carrying a customer directory
and the XML a product catalogue and a three-site warehouse directory. Neither file is complete
on its own. Only 500 order identifiers appear in both, so the customer records exist in one
file, the product records in the other, and several foreign keys resolve only against the
union of the two. The matching row counts between the files are a coincidence of how the
exports were generated, not evidence that they describe the same records.

Consolidating the two exports yields six standardised tables: 5,000 orders, 15,685 order
items, 500 customers, 5,000 deliveries, 1,000 products and 7,000 product reviews. Every order
carries exactly one delivery and between one and five items, and each reviewed item carries
one review. All 5,000 orders were placed between 1 January and 31 December 2018, at a steady
384 to 443 orders a month.

The analysis that follows addresses three commercial questions the retailer can act on: where
revenue actually comes from once it is measured at the right grain, whether delivery
performance shows up in what customers say, and what the data can and cannot support as a
basis for prediction. Each is answered against the six standardised tables rather than the
raw exports, so every figure in this report is reproducible from the submitted CSVs alone.

Two constraints shape everything below. The data covers a single year and a single market, so
no seasonal claim survives a second cycle it has never seen; and reviews are self-selected, so
review-based results describe reviewers rather than customers.

---

## 2. Data-preparation assurance

*(Yandu — 550 words; 3–5 transformation decisions and 4–6 validation results, citing MAP- and
VAL- IDs. Do not reproduce the mapping CSV or the register.)*

## 3. Assessed visualisations

*(Figures 1–8, ≈130 words each. Figures 2 and 6 are drafted in the notebook and are at cap.)*

## 4. Findings

*(Ten numbered, ≈90 words each. Findings 1 and 2 are drafted in the notebook and are at cap.)*

## 5. Machine-learning questions

*(Five numbered, 80–120 words each. MLQ-2 and MLQ-5 are drafted in the notebook and are at cap.)*

## 6. Limitations

*(Jasmine — 180 words)*

## 7. Conclusion

*(Jasmine — 120 words)*
