"""Create a submission-focused version of Group001_solution.ipynb.

This is a mechanical notebook editor: it keeps the working transformation and
validation code, removes development-only cells, and replaces long internal
commentary with concise assignment-facing section notes.
"""

from __future__ import annotations

import json
import shutil
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "00_Master" / "Group001_solution.ipynb"
TARGET = ROOT / "00_Master" / "Group001_solution_minimal.ipynb"


# Development conveniences that are not part of the assessed workflow.
DROP_CODE = {
    3,    # Google Drive mounting and recursive path search
    65,   # raw-byte diagnostic duplicating parsed-source evidence
    88,   # worked text demonstration (the actual tests are retained)
    165,  # post-export coverage display duplicating schema/PK validation
}


# Concise narrative aligned to the supplied school template. Code, displayed
# results, mapping IDs and validation IDs provide the detailed evidence.
MARKDOWN = {
    0: """# FIT5196 Assessment 1 - Solution Notebook

**Group:** Group001

This notebook parses the allocated JSON and XML files, creates the six required
tables, tests the published text interface, reconciles overlap, validates the
results, and exports the assessed CSV files.
""",
    1: """## 0. Configuration and reproducibility

All paths are relative or configurable. The workflow runs offline from a fresh
kernel and writes generated files to `OUTPUT_DIR`.
""",
    5: """## 1. Parse and profile the two sources

JSON and XML are read with structured parsers. The following evidence covers
source structure, grain, formats, keys, missing values and overlap.
""",
    6: "### 1.1 JSON structure and profile\n",
    17: "### 1.2 XML structure and profile\n",
    33: """### 1.3 Source comparison and assumptions

Comparable values are normalised before overlap is assessed. Required keys come
from the public dictionary and are checked against the observed data.
""",
    59: """#### Assumptions

- Customer records occur only in JSON and product records only in XML.
- Shared records are reconciled by business key after field normalisation.
- Different non-missing values for a shared key are reported as conflicts.
- Dates use the source-specific formats demonstrated above.
- Monetary and derived fields follow the published formulas and tolerance.
""",
    60: "### 1.4 Source grain and requirement coverage\n",
    66: """## 2. Source-to-target mapping

The supplied mapping structure is completed from observed source paths and the
public dictionary. The final checks require every target row, preserve dictionary
order and reject blank or placeholder entries.
""",
    81: """## 3. Text and regex functions

The six required functions are imported from `Group001_text_functions.py` and
tested against both public and group-designed cases, including missing,
multilingual and malformed near-match inputs.
""",
    89: """## 4. Build the six standardised relational tables

Shared helpers normalise source values, compare duplicate records, retain one
canonical row per key, and conform each result to the dictionary. Helper columns
are removed before export.
""",
    106: """### 4.0 Shared transformation rules

Money uses decimal-style half-up rounding. Order items are built before orders
because canonical `order_price` is calculated from rounded line revenue.
""",
    109: "### 4.2 `order_items`\n",
    114: "### 4.1 `orders`\n",
    118: "### 4.3 `customers`\n",
    120: "### 4.4 `deliveries`\n",
    122: "### 4.5 `products`\n",
    125: "### 4.6 `product_reviews`\n",
    129: """## 5. Reconcile overlap and verify relationships

The pre-deduplication frames show within-source repetition, cross-source overlap
and any non-missing field conflicts after normalisation.
""",
    134: """## 6. Validation register

Every executable check records a stable ID, PASS/FAIL status, observed result and
interpretation. Expected quantities are derived from the source or dictionary,
not hard-coded canonical answers.
""",
    138: "### 6.1 Schema, type and missing-value checks\n",
    141: "### 6.2 Primary- and foreign-key checks\n",
    144: "### 6.3 Source coverage and reconciliation checks\n",
    147: "### 6.4 Arithmetic and numeric-range checks\n",
    150: "### 6.5 Temporal checks\n",
    153: "### 6.6 Text and multilingual checks\n",
    156: "### 6.7 Literal `NaN` checks\n",
    161: """## 7. Export the six CSV files

Each table is written in dictionary field order and read back to confirm its
schema, grain, primary key, values and platform-independent line endings.
""",
    166: """## 8. Final reproducibility record

The final cell reports versions, validation totals and generated artifacts.
""",
}


def main() -> None:
    if sys.argv[1:] == ["--install"]:
        if not TARGET.exists():
            raise SystemExit(f"run without --install first: {TARGET} does not exist")
        shutil.copyfile(TARGET, SOURCE)
        print(f"installed verified notebook -> {SOURCE.relative_to(ROOT)}")
        return

    notebook = json.loads(SOURCE.read_text(encoding="utf-8"))
    cells = []
    for index, original in enumerate(notebook["cells"]):
        if original["cell_type"] == "code":
            if index in DROP_CODE:
                continue
            cell = deepcopy(original)
            cell["execution_count"] = None
            cell["outputs"] = []
            cells.append(cell)
        elif index in MARKDOWN:
            cell = deepcopy(original)
            cell["source"] = MARKDOWN[index].splitlines(keepends=True)
            cells.append(cell)

    notebook["cells"] = cells
    TARGET.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {TARGET.relative_to(ROOT)}: {len(cells)} cells")


if __name__ == "__main__":
    main()
