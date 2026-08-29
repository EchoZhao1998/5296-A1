# WP1 review — Shawn's and Yandu's notebooks

**From** Echo (WP1) · **Date** 28 Aug 2026
**Reviewing** `matework/wip_shawn.ipynb` and `matework/wip_Yandu_Wang.ipynb`

**Verdict.** Both are correct and both run clean. Both are the **G0 warm-up** — the three
numbers — not the WP3 and WP4 deliverables. Nothing here is wrong; the concern is what is
still missing with G2 tomorrow.

---

## What these two notebooks are

Both answer the three questions from the week-1 brief, and both get the same answers:

| | Shawn | Yandu | Independently re-derived |
|---|---|---|---|
| canonical order count | 5,000 | 5,000 | 5,000 |
| within-file duplicate `order_id` | 68 (both files) | 68 (both files) | 68 and 68 |
| cross-file overlap `order_id` | 500 | 500 | 500 |
| distinct IDs per file | 2,750 / 2,750 | 2,750 / 2,750 | 2,750 / 2,750 |

I re-ran both outside their notebooks against the real files. Both execute top to bottom with no
errors and reproduce their stored output exactly. Both close with the inclusion–exclusion check
`2,750 + 2,750 − 500 = 5,000`, which is the right way to show the union rather than assert it.

**Four people, four routes, one answer — this worked.** Shawn used BeautifulSoup over lxml,
Yandu used `xml.etree`, Jasmine and I used a third route again, and all of us land on the same
numbers. That is exactly what G0 was for.

## One fact worth taking to the group

Both files contain 68 duplicated order IDs, and **not one of them is the same ID**. The overlap
between the two duplicated-ID sets is zero. So the matching count of 68 is a property of how the
two packages were generated, not evidence that the same orders were duplicated twice. Anyone who
assumes "the same 68 orders repeat in both files" and builds a check on it will get a false pass.

Related: every duplicate is exactly a pair — the maximum multiplicity is 2 in both files. That is
why "distinct IDs appearing more than once" and "rows removed by deduplication" both give 68.
The two definitions coincide here only because of that, so whichever one we quote should say so.

---

## Shawn — three notes

**1 · BeautifulSoup is fine here and must not go into the master.** The specification says to use
an XML parser and not to parse the document as plain text with regular expressions; `lxml-xml`
under BeautifulSoup is an XML parser, so this is not a rubric problem. But two things follow:
the master's §1 is a single shared parser that everyone imports rather than rewrites, and adding
`bs4` would put a non-standard dependency into the submitted notebook, which then needs declaring.
Keep this notebook as the independent cross-check it is, and take the shared parser for anything
that ships.

**2 · The Drive path is personal and absolute.** `/content/drive/MyDrive/Group001_A1/...` is one
member's layout — the shared folder resolves through a different path for at least one of us
(a `.shortcut-targets-by-id/...` route). Harmless in a scratch notebook, fatal in a submitted one,
because Appendix A checks for exactly this. The pattern that works for everyone is to search for
the folder rather than name it.

**3 · `GROUP_ID = "001"`.** Everywhere else in the project `GROUP_ID` is the string `Group001`
and filenames are built as `f"{GROUP_ID}_..."`. Two conventions for the same constant is how a
filename ends up as `Group001_A1_...` in one file and `001_...` in another, and Appendix A checks
every submitted filename. Worth aligning now.

## Yandu — three notes

**1 · The file search can silently read the wrong copy.** `_resolve()` falls back to
`BASE.rglob(name)` and returns `matches[0]`. If the expected folder is missing, it walks the whole
Drive and takes whatever it finds first, in arbitrary order — an old copy in a backup or
submission folder would be read without a word. This is the exact failure mode we cannot detect
from the output, because the numbers would still look plausible. A short ordered candidate list
that stops with an error is safer than a search that always succeeds.

**2 · Two things asserted rather than checked.** The final cell prints "(each file: 68)" from the
JSON figure alone; the XML figure is computed but never compared. And neither notebook confirms
`groupAlias == "Group001"` before trusting the file — one line, and it is the thing that catches
reading another group's package. Shawn at least prints a warning if the two duplicate counts
differ; worth doing the same.

**3 · The prose needs a pass before any of it moves.** "teo file", "ues json", "lenth", "point
number". Completely fine in a personal notebook, which is never marked. It matters only because
markdown that reaches the master is read by a marker, and readability is assessed.

---

## What is actually outstanding

This is the part that matters more than anything above.

**Shawn — G2 is tomorrow, Saturday 30 August.** What the gate needs is
`Group001_text_functions.py` with all six functions, the 18 public test cases shown passing, and
at least 12 of our own edge cases. The module exists — WP2's notebook imports it successfully on
Colab and the whole pipeline has been re-run against it — but it is **not in this folder**, so I
cannot review it, and I am the reviewer. Please put the file and the test evidence where I can
read them today.

**Yandu — the validation register was due Wednesday 27 August as a specification**, before any
table existed, and G4 needs it executable by Thursday 4 September under the re-cut plan. Nothing
beyond G0 is here. You are now the critical path for the whole group: two decisions you owed have
been made by WP2 in the meantime, and the mapping's `overlap_or_conflict_rule` column — all 111
rows — is waiting on you. I will send it pre-grouped so most rows take one of four stock
sentences; it should be an hour rather than a day.

Everything either of you needs to write the register against already exists: the six tables are
built, exported and independently verified, so the checks can be written against real output
rather than imagined output.
