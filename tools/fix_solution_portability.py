"""Apply portability and no-canonical-answer fixes to the solution notebook."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "00_Master" / "Group001_solution.ipynb"

DROP_CELL_MARKERS = {
    "# --- Section 5.1: negative control for the conflict detector ---",
}


REPLACEMENTS = {
    """# Where the raw JSON/XML live. The first candidate that exists wins, and the marker's
# layout is listed first, so the submitted notebook runs unchanged after an unzip.
INPUT_CANDIDATES = [
    Path('raw_input'),                        # submission unzipped, run from its root
    Path('Group001_A1/raw_input'),            # allocated package kept as delivered
    Path('../Group001_A1/raw_input'),         # notebook in a sub-folder beside the package
    Path('../DATA/Group001_A1/raw_input'),    # shared drive, run from 00_Master/
]
INPUT_DIR = next((p for p in INPUT_CANDIDATES if p.exists()), None)
assert INPUT_DIR is not None, f'No input folder found. Tried: {INPUT_CANDIDATES}'

# Outputs are written beside this notebook. The one exception is a run on Colab out of a
# mounted shared drive: several people reviewing this notebook at once would each overwrite
# the shared folder in turn, and nobody would be able to tell whose copy survived. A run
# there writes to local Colab storage instead, and says so.
OUTPUT_DIR = Path('outputs')
if '/content/drive' in str(Path.cwd()):
    OUTPUT_DIR = Path('/content/Group001_run/outputs')
    print('Shared drive detected: writing to local Colab storage, not to the shared folder.')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
""": """# A Python export may be launched from any working directory. Anchor its outputs
# beside the submitted script; a notebook uses its own working directory.
BASE_DIR = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()

INPUT_CANDIDATES = [
    BASE_DIR / 'raw_input',
    BASE_DIR / 'Group001_A1' / 'raw_input',
    BASE_DIR.parent / 'Group001_A1' / 'raw_input',
]
INPUT_DIR = next((p for p in INPUT_CANDIDATES if p.is_dir()), None)
assert INPUT_DIR is not None, f'No input folder found. Tried: {INPUT_CANDIDATES}'

OUTPUT_DIR = BASE_DIR / 'outputs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
""",
    "assert len(MAPPING_PATHS) == 111, len(MAPPING_PATHS)":
        "assert len(MAPPING_PATHS) == len(DICTIONARY), (len(MAPPING_PATHS), len(DICTIONARY))",
    """date_fields  = [("customers","signup_date"), ("deliveries","dispatch_date"),
                ("deliveries","promised_date"), ("deliveries","delivered_date"),
                ("products","launch_date")]
stamp_fields = [("orders","order_timestamp"), ("product_reviews","review_timestamp")]
""": """date_fields = list(dd.loc[dd.data_type.eq('date'),
                          ['output_table', 'field_name']].itertuples(index=False, name=None))
stamp_fields = list(dd.loc[dd.data_type.eq('datetime'),
                           ['output_table', 'field_name']].itertuples(index=False, name=None))
""",
    """PK = {"orders": "order_id", "order_items": "order_item_id", "customers": "customer_id",
      "deliveries": "delivery_id", "products": "product_id", "product_reviews": "review_id"}
""": "PK = {table: CONTRACT[table]['pk'] for table in OUTPUT_TABLES}\n",
    """# VAL-TIME-04 — only order_timestamp is held to 2018. Deliveries for orders placed
# at the end of December legitimately land in January 2019.
years = sorted(pd.to_datetime(T["orders"].order_timestamp).dt.year.unique())
record("VAL-TIME-04", years == [2018], f"order_timestamp years present: {years}")
""": """# VAL-TIME-04 — exported order years must equal the years derived from both raw sources.
years = set(pd.to_datetime(T['orders'].order_timestamp).dt.year)
raw_years = {
    norm_datetime(value, dayfirst=dayfirst).year
    for values, dayfirst in [
        ([o['header']['orderTimestamp'] for o in jdata['orders']], False),
        ([h.find('Order_Timestamp').text for h in xroot.iter('Header')], True),
    ]
    for value in values
}
record('VAL-TIME-04', years == raw_years,
       f"exported order years {sorted(years)}; raw-source years {sorted(raw_years)}")
""",
    """accented = rv[rv.language_code.isin(["pl", "de", "fr", "it", "es", "nl", "pt"])]
false_alarms = int(accented.contains_non_latin_script.map({"True": True, "False": False}).sum())
record("VAL-TEXT-08", wrong == 0 and false_alarms == 0,
       f"{wrong} rows disagree; flag is True on {int(flag.sum())}, text says {int(actual.sum())}; "
       f"{false_alarms} of {len(accented):,} accented-Latin reviews wrongly flagged")
""": """record('VAL-TEXT-08', wrong == 0,
       f"{wrong} rows disagree; flag is True on {int(flag.sum())}, "
       f"cleaned text contains non-Latin letters on {int(actual.sum())}")
""",
    """TEXT_FN_CANDIDATES = [
    Path(f'{GROUP_ID}_text_functions.py'),          # beside this notebook, as submitted
    Path('..') / f'{GROUP_ID}_text_functions.py',
]
""": """TEXT_FN_CANDIDATES = [
    BASE_DIR / f'{GROUP_ID}_text_functions.py',
    BASE_DIR.parent / f'{GROUP_ID}_text_functions.py',
]
""",
    """CASE_FILES = [Path('A1_public_text_test_cases.csv'),
              Path('templates/A1_public_text_test_cases.csv'),
              Path(f'{GROUP_ID}_own_text_test_cases.csv')]
""": """CASE_FILES = [
    BASE_DIR / 'A1_public_text_test_cases.csv',
    BASE_DIR / 'templates' / 'A1_public_text_test_cases.csv',
    BASE_DIR / f'{GROUP_ID}_own_text_test_cases.csv',
]
""",
    """# VAL-FLOW-11 — the negative control from Section 5.1. A detector that never fires and
# data with nothing to find produce the same output, so the detector is shown working.
record("VAL-FLOW-11", len(planted) == 1 and len(clean) == 0,
       f"planted conflict detected: {planted.to_dict('records')}; "
       f"same frame with the conflict repaired: {len(clean)} conflicts")

""": "",
    """# Negative control for VAL-ARITH-04. The tax check only means something if the
# wrong formula fails. Adding GST on top instead of dividing it out should match
# almost nothing.
wrong_tax = money_round(order_price * 1.1 + delivery)
n_wrong = int(same_number(total, wrong_tax).sum())
print(f"{'(control)':18s} INFO  adding GST on top instead of dividing it out reproduces "
      f"{n_wrong:,} of {len(o):,} order totals — the correct formula reproduces "
      f"{int(same_number(total, money_round(order_price * (1 - discount / 100) + delivery)).sum()):,}")

""": "",
}

WITHIN_CHECK = """

# Confirm that repeated copies within each individual source are field-identical.
WITHIN_DIFFS = 0
for table in OUTPUT_TABLES:
    key = CONTRACT[table]['pk']
    for source, tables in (('JSON', json_tables), ('XML', xml_tables)):
        if table not in tables:
            continue
        frame = normalise_frame(tables[table], table, dayfirst=(source == 'XML'))
        repeated = frame[frame[key].duplicated(keep=False)]
        WITHIN_DIFFS += len(find_conflicts(repeated, key)) if not repeated.empty else 0
print('within-source duplicate field differences:', WITHIN_DIFFS)
"""


def main() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    notebook["cells"] = [
        cell for cell in notebook["cells"]
        if not any(marker in "".join(cell.get("source", [])) for marker in DROP_CELL_MARKERS)
    ]
    replaced = {old: 0 for old in REPLACEMENTS}
    for cell in notebook["cells"]:
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        if "Precedence: rows are concatenated" in source and "WITHIN_DIFFS = 0" not in source:
            source += WITHIN_CHECK
        for old, new in REPLACEMENTS.items():
            if old in source:
                source = source.replace(old, new)
                replaced[old] += 1
        cell["source"] = source.splitlines(keepends=True)
        cell["execution_count"] = None
        cell["outputs"] = []

    combined = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    missing = [
        old.splitlines()[0]
        for old, count in replaced.items()
        if count != 1 and not (count == 0 and REPLACEMENTS[old] in combined)
    ]
    if missing:
        raise SystemExit(f"replacement count was not exactly one: {missing}")
    NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"updated {NOTEBOOK.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
