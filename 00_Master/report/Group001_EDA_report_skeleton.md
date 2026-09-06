FIT5196 Assessment 1

**Exploratory Data Analysis Report**

Group 001

Wanting Zhao   ·   Congyi Wang   ·   Yandu Wang   ·   Siyuan Shao

Semester 2, 2026   ·   Monash University

# **How to use this document**

*Delete this page before exporting the PDF.*

Ten pages maximum, counted from section 1 to section 7\. The cover page, contents page and references do not count towards the limit.

Write only in your own section. If you think another section is wrong, say so in the chat rather than editing it.

Everything here already exists in Group001\_EDA\_merged\_0905.ipynb. This is a rewrite, not new analysis, so please do not recompute anything — the numbers are settled.

**The word budgets are tight and they are not suggestions.** The findings run 150 to 250 words each in the notebook; here they need to be about 90\. Cut the wording, never the evidence. If a section genuinely will not fit, tell Jasmine and the space comes out of section 6 or 7 instead.

Figures are already exported as PNGs in 00\_Master/review/figures\_0905/ as Group001\_Figure1.png to Group001\_Figure8.png. Insert the image and refer to it by number. No code anywhere in the report.

| Section | Words | Who |
| :---- | :---- | :---- |
| 1\. Context and data scope | 250 | Yandu |
| 2\. Data-preparation assurance | 650 | Echo 400 · Yandu 250 |
| 3\. Eight figures | 90 each | each figure owner |
| 4\. Ten findings | 90 each | each finding owner |
| 5\. Five ML questions | 110 each | each question owner |
| 6\. Limitations | 220 | Jasmine — done |
| 7\. Conclusion | 110 | Jasmine — done |
| References | not counted | Jasmine — drafted |

Draft due Monday, which leaves two days to fix things before the deadline on the 10th.

# **1\. Context and data scope**

*Yandu · about 250 words*

What business this data describes, what period and population it covers, and what the six tables are. Prose, not a list of candidates.

# **2\. Data-preparation assurance**

*Echo about 400 words · Yandu about 250 words*

The specification asks for **three to five material transformation decisions** (Echo) and **four to six material validation results** (Yandu), citing MAP- and VAL- ids where they help.

Do not reproduce the mapping CSV or the validation register here. Those files are the complete record already, and repeating them costs pages we do not have.

# **3\. Assessed visualisations**

*About 90 words of interpretation per figure. Insert the PNG above each one.*

Each figure needs four things: the question it answers, the observation unit and denominator, what it shows stated with a number, and one real limitation.

* Figure 1 — Univariate distribution — Yandu

* Figure 2 — Bivariate relationship — Echo

* Figure 3 — Temporal pattern — Jasmine

* Figure 4 — Multivariate and operational — Jasmine

* Figure 5 — Review and text behaviour — Shawn

* Figure 6 — Delivery performance — Echo

* Figure 7 — Segmented relationship — Yandu

* Figure 8 — Multivariate relationship — Shawn

# **4\. Ten findings**

*About 90 words each · Findings 1–2 Echo · 3–4 Jasmine · 5–6 and 9–10 Yandu · 7–8 Shawn*

* Finding 1 — Echo

* Finding 2 — Echo

* Finding 3 — Jasmine

* Finding 4 — Jasmine

* Finding 5 — Yandu

* Finding 6 — Yandu

* Finding 7 — Shawn

* Finding 8 — Shawn

* Finding 9 — Yandu

* Finding 10 — Yandu

# **5\. Five machine-learning questions**

*About 110 words each*

Keep the leakage note in every one — that is the part the rubric rewards.

* MLQ-1 Will this order be delivered later than promised? — Jasmine

* MLQ-2 What will this basket be worth at checkout? — Echo

* MLQ-3 Which delivered items will attract a rating of 2 or below? — Shawn

* MLQ-4 What natural customer segments exist? — Yandu

* MLQ-5 What order volume should be planned for next month? — Echo

# **6\. Limitations**

*Jasmine · written*

**One merchant, one year, one state.** 5,000 orders placed in 2018 by 500 customers, all in Victoria, all in AUD. Seven columns hold the same value in every row — currency, order\_status, delivery\_status, tax\_category, verified\_purchase, home\_state and home\_country. One year also means seasonality cannot be separated from trend. Nothing here transfers to another region or year.

**The two source files probably came from the same system.** They never disagree on value across 3,259 shared records, but 3,500 of the 10,000 values compared differed in format and none in content. Two systems recording separately would slip somewhere. The match proves nothing was damaged in transit; it does not prove either file is right, and we should not describe this as cross-validated.

**Where we found no difference, that has a size.** Figures 3, 4 and 7 all report something that does not vary. No Express group holds more than 100 deliveries, so a gap under about five percentage points would be invisible to us. That is a good reason not to spend money on a change — it is not proof the change would do nothing.

**Ratings only cover people who chose to write.** 7,000 reviews from 15,685 delivered items, at item grain, so one order can appear three times. Findings 2, 7 and 8 describe reviewers, not customers, and the silent ones are exactly who a service-recovery programme would target.

**Nothing here shows cause.** Late deliveries score higher than on-time ones, 3.82 against 3.70. That is backwards, and it is the clearest sign that something unobserved sits behind both. A seller who ships slowly may also be one people rate generously, and we cannot hold that constant.

**Three pairs of columns say the same thing twice.** delivery\_note\_clean reproduces the delivery outcome; expedited\_delivery is service\_level re-encoded; delivery\_experience matches on\_time\_in\_full on all 7,000 rows. Each would hand a model the answer it is meant to predict, so every machine-learning question has to drop them deliberately rather than by luck.

# **7\. Conclusion**

*Jasmine · written*

These tables are consistent, reconciled and reproducible, and that is what they are good for — describing this year accurately. The descriptive results are the usable ones: order value is skewed enough that the average misleads, and category revenue and unit volume rank almost opposite. The operational results are mostly nulls, and they earn their place by showing where money goes on distinctions the data cannot support. Cause and forecast stay out of reach until there is a second year and cost data.

# **References**

*Not counted towards the ten pages. Jasmine has drafted this — add anything from your own sections.*

All analysis uses the six standardised CSVs produced by Group001\_solution.ipynb from the allocated package (Group001\_commerce.json, Group001\_operations.xml) and the field definitions in public\_data\_dictionary.csv, supplied for FIT5196 Assessment 1, Semester 2 2026, Monash University. No external data or literature was used.

* The pandas development team (2024) pandas (version 2.3.3) \[Python library\]. https://pandas.pydata.org

* Hunter, J. D. (2007) “Matplotlib: A 2D graphics environment”, Computing in Science & Engineering, 9(3), pp. 90–95. https://matplotlib.org

* Wilson, E. B. (1927) “Probable inference, the law of succession, and statistical inference”, Journal of the American Statistical Association, 22(158), pp. 209–212. Used for the binomial confidence intervals in Figures 4 and 6\.