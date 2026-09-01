# Reviewing the assembled solution notebook

Fifteen minutes if it goes well. Please do it before you start your figures, because every
figure is built on what this notebook writes.

---

## 1. Get the files

From the shared drive, download into **one folder on your own machine** — not into a Drive
folder, and do not work on it in place:

```
Group001_solution.ipynb
Group001_text_functions.py
Group001_own_text_test_cases.csv
review/Group001_verify.py
review/Group001_outputs.sha256
templates/A1_public_text_test_cases.csv     (optional; without it only our own 26 cases run)
```

and beside them, the allocated package as it was delivered:

```
Group001_A1/
├── public_data_dictionary.csv
└── raw_input/
    ├── Group001_commerce.json
    └── Group001_operations.xml
```

**Why your own machine.** The notebook writes `outputs/` beside itself. Opened in Colab from the
shared drive it now mounts the drive, moves into `00_Master/` and writes the six CSVs into
`00_Master/outputs/` there — which is exactly what we want **once**, from one person, so the
shared copy is a copy the pipeline produced rather than one somebody uploaded. It is not what we
want four times: we would each overwrite the shared folder in turn and nobody could tell whose
copy survived. So run it on your own machine, in your own folder, and compare against the
manifest.

## 2. Run it

Kernel → Restart and Run All. About 40 seconds. **Every cell must run with no error.**

If a cell fails, stop and send the traceback — do not fix it locally, or we end up with four
different notebooks again.

## 3. Check it produced the right thing

```
python3 review/Group001_verify.py outputs
```

Eight files, all `match`. That is what makes "I ran it" a fact rather than an impression.

If anything says `DIFFERS`, say so in the chat rather than building figures on it.

**One cause is already fixed, and it is worth knowing about.** The first Windows run reported
all eight files differing while the notebook itself ran clean and reported 67 PASS — because
pandas writes CRLF line endings on Windows and LF everywhere else. Identical content, one extra
byte per line, every hash different. The notebook now pins `lineterminator='\n'` on every file
it writes and asserts afterwards that no carriage return reached the file, so the exported bytes
no longer depend on whose machine ran it. The manifest did not change, so if you ran it before
this fix, just re-run.

If it still differs after that, the next likely cause is an older `Group001_text_functions.py`
sitting beside the notebook.

## 4. Read your own part, and one part you did not write

The point of the review is not to re-check the numbers — those are checked by the notebook
itself, 67 times. It is to confirm that **what the notebook says it does is what your code
does**, because a marker reads the words and runs the code.

**Everyone:** read Section 2.3 and 2.4. Those two cells generate the wording of all 111 mapping
rows, and the mapping is a separate assessed deliverable. If a sentence there misdescribes your
part, that is the single most expensive kind of error in this submission.

**Jasmine** — Section 4, and the order the cells now run in (4.2 before 4.1, with the reason
stated). Also Section 7: the export now refuses to write unless the published text functions are
loaded.

**Yandu** — Section 5 and Section 6.0. Your four deferred checks run there now, against the
frame from before deduplication that Section 5 rebuilds. Confirm `find_conflicts` and
`count_overlap` are wired the way you intended, and that Section 6.0's round trip through an
in-memory CSV is a fair stand-in for reading the exported files.

**Shawn** — Section 3.1 and the ten text rows in Section 2.3. Each row names which function
produces the field and which value it reads — raw for the three extractors, cleaned for the
measures. Check the wording against what your code actually does.

**Echo** — Sections 1 and 2 are yours; read them as a stranger would.

## 4b. Where "the shared copy" is

Two things get confused here, and separating them is the whole answer.

**The six CSVs already exist.** They were produced by a verified run and they travel as files —
nobody regenerates them, and there is no "group run" anybody has to attend. They sit in **one**
folder on the shared drive, and that folder is the only copy of them that belongs there.

**Running the notebook is a review activity.** The `outputs/` folder it writes on your machine
is a by-product. Its job is to be compared against the manifest in step 3, and then ignored.

So the one rule that keeps this clean:

> **Never upload your own `outputs/` to the shared drive.**

With one copy on the drive, `Group001_EDA.ipynb` finds it without being told. With two, it
stops and asks you to choose — which is a nuisance, and is a great deal better than silently
building four figures on one set of numbers and four on another.

## 5. Then start your figures

Two ways, both tested, pick whichever you prefer:

- **On Colab** — open `Group001_EDA.ipynb` from the shared drive. Its first cell mounts the
  drive, finds the one folder holding `Group001_orders_standardised.csv` and changes directory
  to it. You do not edit a path.
- **Locally** — download the shared CSV folder once, put `Group001_EDA.ipynb` beside it, and
  run. It looks for `outputs/`, `02_Outputs/` and the current folder.

Either way, Section 0 prints a short fingerprint of every file it read. Those fingerprints
should be identical in all four of our notebooks. If yours differ, you are on a different copy.



Once you have verified, **your own `outputs/` folder has done its job — stop using it.** Build
the EDA against the one shared copy, so all eight figures are built on the same numbers.
`Group001_EDA.ipynb` prints a short fingerprint of every file it reads, so it is visible at a
glance which set is in use, and it now refuses to choose if it finds more than one copy on a
drive rather than picking one at random.

Your brief is in `eda_briefs/Group001_EDA_brief_<your name>.md`. Paste it whole into your own
AI chat as the first message. Keep that chat for this assignment only — the complete
conversation has to be exported and submitted.

---

## What to report back

One line each is enough:

- ran clean / failed at cell N
- verify: 8 match / something differs
- wording in Section 2.3 for my rows: correct / this line is wrong: ...
