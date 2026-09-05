# EDA notebook — what changed on 4 Sep, and what each of us owes next

`00_Master/Group001_EDA_merged_0905.ipynb` · re-run end to end after every edit:
**13/13 code cells, 0 errors**, all eight figures regenerated. The eight PNGs are exported
to `00_Master/review/figures_0905/` as `Group001_Figure1.png` … `Figure8.png` for the report.

**The figures are done. Findings and the MLQ tables are not, and they are the whole
remaining mark.** Nothing below asks anyone to redraw a chart.

---

## Everyone

Three things changed across the whole notebook, so your figure will look slightly
different from the version you sent:

1. **Every figure title now starts `Figure N - `** and carries its row count. Figures 2 and
   6 previously had no number at all. Jasmine is cropping these eight PNGs into the report
   and referencing them by number, so this had to be uniform.
2. **Every figure header now uses the same six labels** — Owner · Question · Observation
   unit and denominator · Tables and join keys · How to build it · Interpretation and
   limitation. Some figures had said *Method*, some had said *Result and limitation*, and
   two had no build note at all.
3. **Every number quoted in a figure's prose is now printed by that figure's cell.** Four
   were not: `promised_days` 5.03 vs 4.99, the cell-size ranges, Figure 6's 2.55 standard
   errors, and the `delivery_experience` agreement. If a marker cannot see where a number
   came from, it does not count as evidence.

I re-derived every number in every figure's narrative straight from the six CSVs, without
using the notebook's own code. **They were all correct.** The changes below are about
clarity and two genuine errors, not about anyone's arithmetic.

---

## Jasmine — Figures 3, 4, and §5

Your figures were right. Three edits:

- **Figure 3's "How to build it" described the wrong thing.** It held a note about
  `delivered_date` running into January 2019. That is a data-preparation point, so I moved
  it into the limitation paragraph where it belongs, and wrote a real build note (three
  stacked panels, all starting at zero, which is what makes the flat series visible).
- **Monthly revenue tops out at 1.36m, not 1.35m** (1,355,379). You will be copying that
  number into the report, so it is fixed at source.
- **Figure 4's "every large swing sits in an Express cell of 36 to 100" was circular** —
  *every* Express cell is 36 to 100. It now reads: no Express cell holds more than 100
  deliveries (36–100, against 151–470 for Standard), so no cell in this design can resolve
  a gap of the size the chart appears to show. Same argument, and it now actually works.
  The title said "95% binomial" while the prose said "Wilson"; both now say Wilson.
- **§5 said three columns have no variance. There are seven.** `orders.currency`,
  `orders.order_status`, `deliveries.delivery_status`, `products.tax_category`,
  `product_reviews.verified_purchase`, `customers.home_state`, `customers.home_country`.
  A marker can check that in one line. Fixed in the brief you will write §5 from.

**Next:** Findings 3 and 4, MLQ-1's evidence and business-decision rows, §5 as prose.

## Yandu — Figures 1, 7, and §1

Nothing was wrong with either figure. Figure 7 is the best-evidenced figure in the set —
it is the only one whose narrative can be checked entirely from its own printed output,
because you printed the standard errors. That is the standard the rest were brought up to.

Two cosmetic edits: two over-long lines wrapped, and `set_yticklabels([])` replaced with
`tick_params(labelleft=False)` on the two right-hand panels.

**Next:** §1 as prose (it is still a list of candidates), Findings 5, 6, 9 and 10, and
MLQ-4's evidence and business-decision rows. That is four findings against everyone else's
two — if that is too much, Finding 9 or 10 can move.

**One finding is already verified and free to write:** `orders.expedited_delivery` **is**
`deliveries.service_level` re-encoded — 901 True / 901 Express, 4,099 / 4,099, zero
exceptions. With `delivery_note_clean` (Finding 10) and `product_reviews.delivery_experience`
(Figure 6's limitation) that is the **third** redundant column pair across the two source
systems. Three is a finding in its own right, and a standing leakage warning for every MLQ.

## Shawn — Figures 5 and 8

Both cells were correct and both narratives needed work. Your two are the only figures that
had a real reading problem.

- **Figure 8 was underselling a real result.** Per-quintile standard errors are ~0.033, so
  the fall from 3.879 (Q1) to 3.548 (Q4) is about **seven standard errors** — that is not
  noise. What is not monotonic is the rebound to 3.684 in Q5. "No clear monotonic price
  relationship" reads as a null, and it isn't one. The rating panel now shows points with
  95% intervals instead of bars from zero, and the decline is visible.
- **Figure 8's helpful-votes panel needed the opposite fix.** Once the bars came off, the
  auto axis made a 1.5-vote difference look like a rising trend. It now shows the median
  with the middle half of each quintile (roughly 21 to 68 votes) on a 0–90 axis, so it is
  obvious the within-quintile spread swamps the between-quintile difference. That panel is
  a genuine null and now looks like one.
- **Figure 5's main claim was half wrong.** "Neither group showed a clear monotonic
  rating–length pattern" is right for the non-Latin group and wrong for the Latin one. The
  cell now prints median length by rating: Latin-only runs 955 / 980 / 928 / 919 / 907 — an
  orderly ~7% decline from 2 stars to 5 — while non-Latin swings 746 / 659 / 513 / 659 /
  498 with no order, which is what 271 reviews split five ways looks like. Those are two
  different statements and the narrative now makes them separately.

**Next:** Findings 7 and 8, MLQ-3's evidence and business-decision rows.

## Echo — Figures 2 and 6

- **Figure 6 was a bar chart of 3.70 against 3.82 on a 0–5 axis** — the finding was
  invisible and the reader had to take the caption on trust. It is now a dot-and-interval
  with 95% confidence intervals, matching Figure 4. The cell also prints the gap in
  standard errors (2.55) and checks `delivery_experience` against `on_time_in_full`
  (agrees on 100.0% of 7,000 reviews), both of which the prose had been asserting.
- **Watch this one:** the two intervals do *not* quite overlap (3.733 against 3.730). The
  gap is statistically detectable. It is still 0.12 stars on a 1–5 scale and in the wrong
  direction, so the conclusion is unchanged — but do not write "the intervals overlap".
- Figure 2 gained its figure number and a build note; two long lines wrapped. No change to
  any number.

**Next:** Findings 1 and 2 are the only two already written. MLQ-2 and MLQ-5 are the only
two MLQ tables already complete.

---

## Left alone on purpose

- **Quote style.** Figures 5 and 8 are double-quoted and wrapped; the other six cells are
  single-quoted and compact. It is visible at a glance that two people wrote this, but
  converting it risks breaking working code for zero marks. Say if you want it done.
- **Nine long lines in the coverage cell** are deliberate column alignment. Kept.
- **Owner tags** (`**Owner:** Yandu`, `# --- Figure 4 (Jasmine) ---`) are still there. They
  help us and look slightly odd in a submitted artefact. Decide once, before the ZIP.

## Before anyone writes the report

One person runs the notebook top to bottom on the shared `outputs/` and confirms 13 cells,
0 errors, and the coverage cell still asserting 8 figures / 6 categories / 6 tables /
5 relational. Only then does it go to Jasmine.
