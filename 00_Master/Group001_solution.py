#!/usr/bin/env python
# coding: utf-8

# Group001_solution.py — exported from Group001_solution.ipynb.
# This file reflects the submitted notebook workflow cell for cell. The six required
# text functions are imported from Group001_text_functions.py and not duplicated here.


# # FIT5196 Assessment 1 — Solution Notebook
#
# **Group:** Group001
# **Members:** Echo Zhao · Jasmine · Yandu Wang · Shawn
#
# This notebook contains the complete transformation and validation workflow: it parses the
# two allocated source files, completes the source-to-target mapping, implements and tests the
# required text functions, builds the six standardised relational tables, reconciles the two
# sources, runs the validation register and exports the six CSV files.
#
# Section numbering follows the supplied template. The exploratory data analysis is in
# `Group001_EDA.ipynb`, which reads the six exported CSVs and nothing else.


# ## 0. Configuration and reproducibility
#
# Keep all configurable paths in this section. The final notebook must run with
# **Restart and Run All** without manual file edits or network access.


# Two cells. The first mounts Google Drive and is inert anywhere else, so the configuration
# cell below stays free of any environment-specific code. The second resolves every path from
# a short candidate list: the first entry is the layout produced by unzipping the submission,
# so the notebook runs unchanged for a marker who does exactly that.


# In[1]:

# Colab only. Does nothing elsewhere, and nothing if the folder is not found.
try:
    from google.colab import drive
    from pathlib import Path as _Path
    import os as _os

    drive.mount('/content/drive')
    _hit = next((p for p in _Path('/content/drive/MyDrive').rglob('Group001_A1/00_Master')
                 if p.is_dir()), None)
    if _hit:
        _os.chdir(_hit)
        print('cwd:', _hit)
except ImportError:
    pass   # not on Colab


# In[2]:

# --- Section 0: configuration ---
from pathlib import Path

GROUP_ID = 'Group001'

# Where the raw JSON/XML live. The first candidate that exists wins, and the marker's
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

JSON_PATH = INPUT_DIR / f'{GROUP_ID}_commerce.json'
XML_PATH  = INPUT_DIR / f'{GROUP_ID}_operations.xml'
DICT_PATH = INPUT_DIR.parent / 'public_data_dictionary.csv'

for label, path in [('input', INPUT_DIR), ('output', OUTPUT_DIR)]:
    print(f'{label:7s} {path}')


# ### 0.1 Environment and dependencies
#
# Import the libraries used by your submitted workflow. Record non-standard
# dependencies in `requirements.txt`.


# In[3]:

# --- Section 0.1: environment ---
import json
import re                            # field values only, never document structure
import sys
import xml.etree.ElementTree as ET   # structured parser; the specification forbids regex on structure
from io import StringIO

import pandas as pd

pd.set_option('display.max_columns', 60)
pd.set_option('display.width', 200)

print('python', sys.version.split()[0])
print('pandas', pd.__version__)

# The published data dictionary is the contract for every output table. Read once, here,
# with keep_default_na=False so the literal three-character 'NaN' stays visible as text.
dd = pd.read_csv(DICT_PATH, keep_default_na=False)
DICTIONARY = dd                      # the profiling code in Section 1 uses this name

# Every file this notebook writes uses LF line endings, whatever the operating system.
# Left to pandas, the same code produces CRLF on Windows and LF elsewhere, so the exported
# bytes would depend on whose machine ran the notebook — one extra byte per line, identical
# content, and no two runs comparable. It is pinned here and checked in Section 7.
LINE_ENDING = '\n'
print('dictionary', len(dd), 'target fields across', dd.output_table.nunique(), 'tables')


# ## 1. Parse and profile the two sources
#
# Use structured JSON and XML parsers. Record source grains, nested/repeated
# structures, candidate keys, formats, missing-value conventions and evidence of
# within-source or cross-source overlap.


# ### 1.1 JSON structure and profile
#
# **Structure**
# 1. what the top-level keys are, 
# 2. how many records sit under each, 
# 3. and which parts are nested. 
# This is the evidence behind the "source grains and nested structures" requirement in A1.


# In[4]:

with open(JSON_PATH, "r", encoding="utf-8") as f:
    raw_json = json.load(f)

print("Top-level keys :", list(raw_json.keys()))
print("Export metadata:", raw_json["exportMetadata"])

for key in ["customerProfiles", "orders", "productReviews"]:
    # print(f"{key} {len(raw_json[key])} records")
    print(f"{key:18s} {len(raw_json[key]):,} records")
    # ":18s" means "left-justify in a field 18 characters wide", and ">6," means "right-justify in a field 6 characters wide, with commas as thousands separators"
    # why not just use f"{len(raw_json[key]):,}"? Because that would right-justify in a field only as wide as the number itself, which is less readable when the numbers have different lengths. This way, the numbers line up nicely in a column.

# One order shows the nesting: a flat header, a repeated cart, a single delivery.
# "grain" comes from 'public_data_dictionary.csv' and means "the level of detail represented by one row of the table".
first_order = raw_json["orders"][0]
print("\nAn order contains:", list(first_order.keys()))
print("  header       ->", len(first_order["header"]), "fields  (grain: one row per order)")
print("  shoppingCart ->", len(first_order["shoppingCart"]), "items   (grain: one row per order item)")
print("  delivery     ->", len(first_order["delivery"]), "fields  (grain: one row per order)")


# #### **Naming helper.** 
# JSON keys are camelCase; the data dictionary is snake_case.


# In[5]:

def to_snake(name, exceptions=None):
    """camelCase -> snake_case. 'ID' is treated as one word, so customerID -> customer_id.
    `exceptions` maps a source key straight to its final name, bypassing the rule."""
    exceptions = exceptions or {}
    if name in exceptions:
        return exceptions[name]
    name = name.replace("ID", "Id")
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name)
    return name.lower()

def check_names(tables, dictionary_path):
    """Every column we produce must be a dictionary field, or be explained.

    Prints two lists per table, which mean different things:
      produced but not a target field -> either the naming rule is wrong,
                                         or it is a raw text input to a derived field
      target field with no source key -> a derived field (mapping source_format = 'derived')
    """
    d = pd.read_csv(dictionary_path, keep_default_na=False)
    target = {t: set(g.field_name) for t, g in d.groupby("output_table")}
    for name, df in tables.items():
        if name not in target:
            print(f"-- {name}: not an output table (kept for analysis only)")
            continue
        cols = set(df.columns) - {"source_system"}
        print(f"-- {name}")
        print("   produced but not a target field:", sorted(cols - target[name]) or "none")
        print("   target field with no source key:", sorted(target[name] - cols) or "none")


# ### **The parser.** 
# Walk the orders once, appending to three lists; 
#
# the two stand-alone arrays go straight to DataFrames.
#
# `customers` and `product_reviews` come only from this file — there are no products here.


# In[6]:

def parse_json(path, exceptions=None):
    """Read the commerce JSON export and return flat tables with source-native values.

    Returns
    -------
    tables : dict of str -> DataFrame   keys: orders, order_items, deliveries,
                                              customers, product_reviews
    metadata : dict                     the file's exportMetadata block
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    def rename(record):
        return {to_snake(k, exceptions): v for k, v in record.items()}

    orders, order_items, deliveries = [], [], []
    for order in raw["orders"]:
        orders.append(rename(order["header"]))
        deliveries.append(rename(order["delivery"]))
        order_items.extend(rename(item) for item in order["shoppingCart"])

    tables = {
        "orders":          pd.DataFrame(orders),
        "order_items":     pd.DataFrame(order_items),
        "deliveries":      pd.DataFrame(deliveries),
        "customers":       pd.DataFrame([rename(c) for c in raw["customerProfiles"]]),
        "product_reviews": pd.DataFrame([rename(r) for r in raw["productReviews"]]),
    }
    for df in tables.values():
        df.insert(0, "source_system", "JSON")

    return tables, raw["exportMetadata"]


# In[7]:

# Two passes: the general naming rule alone, then the exceptions its output justifies.
# Pass 1 — the general rule alone. Nothing assumed about exceptions.
naive_tables, _ = parse_json(JSON_PATH)
check_names(naive_tables, DICT_PATH)

# Written from the report above, not before it.
NAME_RULE_FIXES = {"prior12MOrders": "prior_12m_orders"}   # regex splits on capitals, not digits
RAW_TEXT_FIELDS = {"customerNote": "customer_note_raw",    # target field is the *clean* version
                   "reviewText":   "review_body_raw"}
JSON_NAME_EXCEPTIONS = {**NAME_RULE_FIXES, **RAW_TEXT_FIELDS}

# Pass 2 — corrected rule. What remains is expected, not an error.
json_tables, json_meta = parse_json(JSON_PATH, JSON_NAME_EXCEPTIONS)
check_names(json_tables, DICT_PATH)
del naive_tables

for name, df in json_tables.items():
    print(f"{name:16s} {df.shape[0]:,} rows x {df.shape[1]:>2} cols")


# **Profile.** 
#
# Three questions per table: 
#
# - is the intended business key unique, 
# - what is missing,
# - and what do the values actually look like. 
#
# These answers become Section 1.3's assumptions and feed the `overlap_or_conflict_rule` column of the mapping.


# In[8]:

# The dictionary declares the primary key of every output table: the field at position 1.
# Read it rather than retyping it, so the notebook and the dictionary cannot drift apart.
# Whether each declared key is *actually* unique in the data is tested in Section 1.3c.
DICTIONARY = pd.read_csv(DICT_PATH, keep_default_na=False)
DECLARED_KEYS = (DICTIONARY[DICTIONARY.position == 1]
                 .set_index("output_table")["field_name"].to_dict())
print(DECLARED_KEYS)

def profile(tables, source):
    """Per table: is the declared key unique, and how many columns hold a blank or null."""
    rows = []
    for name, key in DECLARED_KEYS.items():
        if name not in tables:
            continue
        df = tables[name]
        rows.append({"source": source, "table": name, "rows": len(df), "key": key,
                     "unique_keys": df[key].nunique(),
                     "duplicate_key_rows": len(df) - df[key].nunique(),
                     "cols_with_blank_or_null": int(((df == "") | df.isna()).any().sum())})
    return pd.DataFrame(rows)

profile(json_tables, "JSON")

# What do the "missing" values actually look like? The spec cares about the exact convention.
for name, df in json_tables.items():
    blanks = ((df == "") | df.isna()).sum()
    blanks = blanks[blanks > 0]
    if len(blanks):
        print(f"{name}:")
        for col, n in blanks.items():
            sample = df.loc[(df[col] == "") | df[col].isna(), col].iloc[0]
            print(f"   {col:10s} {n:>5,} rows   example value: {sample!r}")

# Value shapes, so Section 1.3 can compare JSON against XML field by field.
print(json_tables["orders"][["order_timestamp", "order_price", "coupon_discount",
                             "expedited_delivery", "currency"]].head(3).to_string(index=False))
print()
print(json_tables["deliveries"][["dispatch_date", "delivered_date", "on_time_in_full"]].head(3).to_string(index=False))
print()
print("dtypes (orders):")
print(json_tables["orders"].dtypes.to_string())


# ### 1.2 XML structure and profile
#
# **Why I need it.** 
#
# Task 1 requires the grain, nesting and key structure of *both* sources. The
# XML is the harder half: it carries two tables the JSON does not have (`products`, and a
# warehouse directory), and every value arrives as text.
#
# **What it is.** 
#
# The same contract as Section 1.1 — `parse_xml()` returns flat DataFrames keyed by
# output-table name, canonical column names, source-native values
#
# **How I get it.
#
# ** `xml.etree.ElementTree`, a structured parser. 
#
# The spec forbids treating either document as plain text for regex, so no string scraping anywhere in this section.
#
# **Why the others care.** 
#
# This is the only source of `products`, which cannot be built
# without it, and the only place the `DD/MM/YYYY`, `AUD 2,765.47`, `Y/N` and `10%` formats appear
# — every one of which becomes a normalisation rule applied in Section 4 and checked in Section 6.


# #### Structure survey
#
# **Why** 
#
# State the shape before flattening it, so the flattening is a consequence of evidence rather than of my assumptions about the file.
#
# **What** 
#
# The root element and its attributes, the five collections beneath it and their
# sizes, and the internal shape of one `Order`.
#
# **How**
#
# `.findall()` with a path, then count. No DataFrames yet — this is inspection.
#
# **So what** 
#
# The counts here are the denominator for every row-flow check in Section 6.
# If 2,818 orders go in and 2,750 come out, this is the cell that has to account for it.


# In[9]:

root = ET.parse(XML_PATH).getroot()

print("Root element   :", root.tag)
print("Root attributes:", root.attrib)          # groupAlias / sourceSystem / period

for child in root:
    print(f"  {child.tag:20s} {len(list(child)):>6,} children")

# One order, to show the nesting. Compare with the JSON: same three parts, different names.
order = root.find("Orders/Order")
print("\nAn Order contains:", [part.tag for part in order])
print("  Header        ->", len(list(order.find("Header"))), "fields  (grain: one row per order)")
print("  Shopping_Cart ->", len(order.findall("Shopping_Cart/Item")), "Item(s) (grain: one row per order item)")
print("  Delivery      ->", len(list(order.find("Delivery"))), "fields  (grain: one row per order)")

# WarehouseDirectory has no matching output table. Noted now so it is not silently dropped.
print("\nWarehouse fields:", [f.tag for f in root.find("WarehouseDirectory/Warehouse")])


# #### Naming rule and the parser
#
# **Why I need it.** The XML uses `Title_Case_With_Underscores`; the data dictionary uses
# `snake_case`. A rule is needed.
#
# **What it is.** 
# 1. `Order_ID` → `order_id` use `.lower()` — RECALL the JSON's
# camelCase regex.
# 2. `element_to_record` turns one element's children into a dict; 
# 3. `parse_xml` walks the tree and stacks those dicts.
#
# **How I get it.** 
# `(child.text or "")` reads each leaf. The `or ""` is: an empty XML
# element gives `None`, while the JSON export gives `""` for the same absent value.
# Without it the
# two sources are not comparable and every blank count reports a false difference.
#
# **Why the others care.** `exceptions` is keyed on the **original tag**, not the lowered name, so
# the JSON and XML exception tables are not interchangeable, and passing the wrong one fails silently.
# And `warehouses` is returned but is *not* an output table: it must never become a column in the
# six CSVs. It is kept because it carries lat/long, which is useful for an EDA distance figure.


# In[10]:

def element_to_record(element, exceptions=None):
    """One XML element -> one dict. Child tag becomes the column, child text becomes the value.

    `exceptions` maps an original tag (e.g. "Review_Text") straight to its final column name,
    bypassing the .lower() rule. Text is read as `child.text or ""` —
    """
    exceptions = exceptions or {}
    return {exceptions.get(child.tag, child.tag.lower()): (child.text or "")
            for child in element}

def parse_xml(path, exceptions=None):
    """Read the operations XML export and return flat tables with source-native values.

    Returns
    -------
    tables : dict of str -> DataFrame   orders, order_items, deliveries, products,
                                        product_reviews, warehouses (not an output table)
    metadata : dict                     root attributes plus the Export_Metadata block
    """
    root = ET.parse(path).getroot()

    orders, order_items, deliveries = [], [], []
    for order in root.findall("Orders/Order"):
        orders.append(element_to_record(order.find("Header"), exceptions))
        deliveries.append(element_to_record(order.find("Delivery"), exceptions))
        order_items.extend(element_to_record(item, exceptions)
                           for item in order.findall("Shopping_Cart/Item"))

    tables = {
        "orders":          pd.DataFrame(orders),
        "order_items":     pd.DataFrame(order_items),
        "deliveries":      pd.DataFrame(deliveries),
        "products":        pd.DataFrame([element_to_record(p, exceptions)
                                         for p in root.findall("ProductCatalogue/Product")]),
        "product_reviews": pd.DataFrame([element_to_record(r, exceptions)
                                         for r in root.findall("ProductReviews/Review")]),
        "warehouses":      pd.DataFrame([element_to_record(w, exceptions)
                                         for w in root.findall("WarehouseDirectory/Warehouse")]),
    }
    for df in tables.values():
        df.insert(0, "source_system", "XML")

    metadata = dict(root.attrib)
    metadata.update(element_to_record(root.find("Export_Metadata")))
    return tables, metadata


# #### Pass 1 — the general rule alone
#
# **Why I need it.** Encoding the exceptions before running the rule would leave no
# evidence of how they were found, and a reviewer could not tell a bug from a design choice.
#
# **What it is.** `parse_xml` with no exceptions, checked against the data dictionary.
#
# **How I get it.** The same `check_names` defined in Section 1.1 — reused, not rewritten, so the JSON
# and XML sides are judged by identical criteria.
#
# **Why the others care.** The right-hand list of this output is the derived-field inventory for
# the XML side. Those are the `source_format = derived` rows of the mapping.


# In[11]:

naive_xml, _ = parse_xml(XML_PATH)
check_names(naive_xml, DICT_PATH)


# #### Reading pass 1, and the exceptions it justifies
#
# Three tags convert cleanly but land on the wrong side of the raw/clean boundary, and **no tag
# breaks the `.lower()` rule** — unlike the JSON side, where `prior12MOrders` did. That asymmetry
# is itself a finding: the XML's explicit underscores leave nothing for a rule to guess wrong.
#
# | Tag | `.lower()` gives | Dictionary wants | Why an exception |
# |---|---|---|---|
# | `Customer_Note` | `customer_note` | `customer_note_clean`, `promo_code` | one field, two targets |
# | `Review_Text` | `review_text` | seven(see the outcome last cell!) `product_reviews` fields | one field, seven targets |
# | `Product_Description` | `product_description` | `product_description_clean` | one field, one cleaned target |
#
# The left list is never renamed to a target — a source field that fans out to several targets has
# no single correct target name. It is suffixed `_raw` to mark it as an *input* to derivation, and
# the fan-out is recorded in the mapping CSV


# In[12]:

# Written from the pass-1 report above, not before it. Keys are original tags.
XML_NAME_EXCEPTIONS = {
    "Customer_Note":       "customer_note_raw",
    "Review_Text":         "review_body_raw",
    "Product_Description": "product_description_raw",
}


# #### Pass 2 — the corrected rule
#
# **Why I need it.** To show the fix worked, and to leave the clean run as the notebook's evidence.
#
# **What it is.** `xml_tables` — the frames every later section uses.
#
# **How I get it.** Re-parse with the exception table, re-run the same check, drop the pass-1 copy.
#
# **Why the others care.** After this cell the two sources have identical column names for shared
# tables, which is the precondition for the overlap work in Section 1.3 and the reconciliation in Section 5.


# In[13]:

xml_tables, xml_meta = parse_xml(XML_PATH, XML_NAME_EXCEPTIONS)
check_names(xml_tables, DICT_PATH)
del naive_xml

print("\nExport metadata:", xml_meta)
for name, df in xml_tables.items():
    print(f"{name:16s} {df.shape[0]:,} rows x {df.shape[1]:>2} cols")


# #### Profile
#
# **Why I need it.** Task 1 asks for candidate keys, duplicate evidence and the date, boolean,
# currency, percentage and missing-value formats. This is where each is shown rather than claimed.
#
# **What it is.** Three checks: is the intended key unique, what is blank, and what do the values
# literally look like.
#
# **How I get it.** The same three cells as Section 1.1, run against `xml_tables` — deliberately identical
# so Section 1.3 can put the two profiles side by side.
#
# **Why the others care.** Every row of this output turns into work for someone: the duplicate
# counts are the canonical-row problem Section 5 settles, and each format below is a conversion
# applied in Section 4 and a `VAL-SCHEMA-` check run in Section 6.


# In[14]:

# The same profile function as Section 1.1, run on the XML — deliberately identical so Section 1.3 can put
# the two profiles side by side. `warehouses` is absent because it is not an output table.
profile(xml_tables, "XML")

for name, df in xml_tables.items():
    blanks = (df == "").sum()
    blanks = blanks[blanks > 0]
    for col, n in blanks.items():
        print(f"{name}.{col:10s} {n:>6,} blank rows")

# The formats themselves — the evidence behind every normalisation rule in Section 1.3.
print(xml_tables["orders"][["order_timestamp", "order_price", "delivery_charges",
                            "coupon_discount", "expedited_delivery"]].head(3).to_string(index=False))
print()
print(xml_tables["products"][["unit_price", "launch_date", "recyclable_packaging"]].head(3).to_string(index=False))
print()
print("Every XML column arrives as text:", xml_tables["orders"].dtypes.unique())


# #### Hand-off note for Section 1.3
#
# Two things Section 1.2 could not answer on its own. Both are settled below — this note stays so the
# question and its answer sit together rather than the answer appearing without a question.
#
# 1. **Why do the `order_items` row counts differ (JSON 8,826, XML 8,833) when `orders` and
#    `product_reviews` match exactly?**
#    Answered in Section 1.3c and Section 1.3d. The counts differ because the two files carry different numbers
#    of duplicated keys (201 JSON, 214 XML), and the matching counts elsewhere are a coincidence —
#    the two files describe mostly *different* records. 15,685 distinct items exist across both.
# 2. **Are the duplicate rows field-identical?**
#    Answered in Section 1.3c. Yes — every duplicated key is exactly two copies, and the copies match on
#    every column. That is what makes the canonical-row rule deterministic rather than arbitrary.


# #### Both parsers, checked before anything is built on them
#
# Three preconditions. The allocation marker inside each file must be this group's, or the
# whole submission describes someone else's data; and the four tables that exist in both files
# must agree on column names after the naming rules above, because every concatenation in
# Section 4 depends on it. A mismatch here would otherwise appear much later as a column full
# of missing values.


# In[15]:

# --- Section 1.2: preconditions on the two parsed sets ---
assert json_meta['groupAlias'] == GROUP_ID, json_meta
assert xml_meta['groupAlias']  == GROUP_ID, xml_meta

BOTH_SOURCES = ['orders', 'order_items', 'deliveries', 'product_reviews']
for t in BOTH_SOURCES:
    j, x = set(json_tables[t].columns), set(xml_tables[t].columns)
    assert j == x, (t, sorted(j ^ x))

print('allocation marker :', json_meta['groupAlias'], '/', xml_meta['groupAlias'])
print('shared tables align on column names:', ', '.join(BOTH_SOURCES))
for source, tabs in (('JSON', json_tables), ('XML', xml_tables)):
    for name, df in tabs.items():
        print(f'{source:5s} {name:16s} {df.shape[0]:>7,} rows x {df.shape[1]:>2} cols')


# ### 1.3 Source comparison and assumptions
#
# *(next working session — format table, within-source duplicates, cross-source overlap)*


# ### Why this section exists
#
# Task 1 asks four questions: which fields appear in one or both sources, what the format
# conventions are, where records duplicate within a source and overlap across sources, and which
# assumptions must hold before any transformation. Everything below answers one of them.
#
# No output table is built here. This section produces the format rules and normalisers that
# Section 4 applies, the duplicate and overlap counts that Section 5 must reproduce, and the
# confirmation that the raw text fields agree across sources.
#
# The method is the same throughout: compare the two sets of frames produced above, using a small
# set of normalisers that exist only to make values comparable.


# #### 1.3a Field coverage and format conventions
#
# **Why** 
#
# table means Section 4 does not have to rediscover them from the raw files.
#
# **What** 
#
# Which tables exist in which source, then the same value shown as each source writes it.
#
# **How** 
#
# Set arithmetic on the table keys, then one shared order printed from both frames.
#
# **So what** 
#
# Every row of the format table becomes exactly one conversion in Section 4 and one
# `VAL-SCHEMA-` check in Section 6. If a row here has no matching check there, something was missed.


# In[16]:

print("JSON tables:", sorted(json_tables))
print("XML  tables:", sorted(xml_tables))
print("JSON only  :", sorted(set(json_tables) - set(xml_tables)))
print("XML only   :", sorted(set(xml_tables) - set(json_tables)))

# Column coverage for the four tables both sources carry.
for name in sorted(set(json_tables) & set(xml_tables)):
    j, x = set(json_tables[name].columns), set(xml_tables[name].columns)
    print(f"\n{name}: {len(j & x)} shared columns")
    if j - x: print("   JSON only:", sorted(j - x))
    if x - j: print("   XML only :", sorted(x - j))

# The same order, as each source writes it. 
# This is the format evidence for A1.

sample_id = sorted(set(json_tables["orders"].order_id) & set(xml_tables["orders"].order_id))[0]
fields = ["order_timestamp", "order_price", "coupon_discount", "expedited_delivery", "coupon_code"]

side_by_side = pd.DataFrame({
    "JSON": json_tables["orders"].set_index("order_id").loc[sample_id, fields],
    "XML":  xml_tables["orders"].set_index("order_id").loc[sample_id, fields],
})
print("Order", sample_id)
side_by_side


# The pattern, stated once so Section 4 can be written from it:
#
# | Field type | JSON | XML | Rule for Section 4 |
# |---|---|---|---|
# | timestamp | `2018-04-03 09:45:00` | `03/04/2018 09:45:00` (day first) | parse with `dayfirst=True` for XML only |
# | date | `2019-01-08` | `10/11/2018` | same |
# | money | `1189.23` (number) | `AUD 2,765.47` (string) | strip `AUD` and `,`, cast to float, round to 2dp |
# | percent | `10` (number) | `10%` (string) | strip `%`, cast to float |
# | boolean | `true` / `false` | `Y` / `N` | map to Python `bool` |
# | missing string | `""` | empty element → `""` by | becomes the literal `"NaN"` at export, in Section 4 |
#
# Every XML column arrives as text; every JSON column arrives natively typed. That single
# sentence is the reason Section 1.3 exists.


# #### 1.3b Normalisers
#
# **Why** 
#
# Need to compare 2 table later  
# and apply the format rules above become code.
#
# **What** 
#
# Four functions, each one line of real work.
#
# **How** 
#
# use `pd.to_Datetime` 
#
# **So what.** These are the canonical implementations. Section 4 uses them rather than
# writing her own; two implementations of "what is a valid date" is how C1 and E1 get lost. If
# they move into `Group001_text_functions.py` or a shared cell, they move as a set.


# In[17]:

def norm_money(value):
    """'AUD 2,765.47' or 2765.47 -> 2765.47"""
    return round(float(str(value).replace("AUD", "").replace(",", "").strip()), 2)

def norm_percent(value):
    """'10%' or 10 -> 10.0"""
    return float(str(value).replace("%", "").strip())

def norm_bool(value):
    """'Y' / 'N' / True / False -> bool"""
    return str(value).strip().lower() in {"y", "yes", "true"}

def norm_datetime(value, dayfirst):
    """Text date or timestamp -> pandas Timestamp. `dayfirst` is True for XML, False for JSON."""
    return pd.to_datetime(str(value).strip(), dayfirst=dayfirst, errors="coerce")

# Which normaliser applies to which column, used by the comparison below.
# `date` and `datetime` parse identically but are written out differently, so they are
# separate categories here rather than one.
NORMALISERS = {
    "orders":      {"money":   ["order_price", "delivery_charges", "tax_amount", "order_total"],
                    "percent": ["coupon_discount"],
                    "bool":    ["expedited_delivery"],
                    "datetime":["order_timestamp"],
                    "number":  ["customer_lat", "customer_long"]},
    "order_items": {"money":   ["unit_price", "line_revenue"],
                    "number":  ["quantity"]},
    "deliveries":  {"money":   ["delivery_cost"],
                    "bool":    ["on_time_in_full", "signature_required"],
                    "date":    ["dispatch_date", "promised_date", "delivered_date"],
                    "number":  ["delay_days", "fulfilment_hours", "promised_days",
                                "tracking_event_count", "shipping_distance_km",
                                "estimated_carbon_kg"]},
    "product_reviews": {"bool":    ["verified_purchase"],
                        "datetime":["review_timestamp"],
                        "number":  ["rating", "helpful_votes"]},
}

def normalise(series, column, spec, dayfirst):
    """Apply the right normaliser to one column. Anything unlisted is compared as text."""
    if column in spec.get("money", []):     return series.map(norm_money)
    if column in spec.get("percent", []):   return series.map(norm_percent)
    if column in spec.get("bool", []):      return series.map(norm_bool)
    if column in spec.get("date", []) or column in spec.get("datetime", []):
        return series.map(lambda v: norm_datetime(v, dayfirst))
    if column in spec.get("number", []):    return series.astype(float)
    return series.astype(str)


# **Coverage check.** `NORMALISERS` is hand-written, so it can silently miss a field. The dictionary
# already says which fields are typed — every row whose `data_type` is not `string` needs a
# normaliser. Check the map against the dictionary rather than trusting it.


# In[18]:

def normaliser_gaps():
    """Every typed dictionary field that no normaliser covers.

    `in_source = False` means the field is derived by the text functions and is correctly
    absent here. `in_source = True` is a real gap.
    """
    source_columns = {}
    for tables in (json_tables, xml_tables):
        for name, df in tables.items():
            source_columns.setdefault(name, set()).update(df.columns)

    rows = []
    for _, field in DICTIONARY[DICTIONARY.data_type != "string"].iterrows():
        spec = NORMALISERS.get(field.output_table, {})
        covered = any(field.field_name in cols for cols in spec.values())
        if not covered:
            rows.append({"table": field.output_table, "field": field.field_name,
                         "type": field.data_type,
                         "in_source": field.field_name in source_columns.get(field.output_table, set())})
    return pd.DataFrame(rows)

normaliser_gaps()


# Twelve real gaps, all in `products` and `customers` — the two tables that appear in only one
# source, which is exactly why they were missed. The three `product_reviews` rows with
# `in_source = False` are the derived text measures and belong nowhere in this map.
#
# The extension below is written from that output. Re-run the check after it: it should return an
# empty frame.


# In[19]:

# Written from the gap report above, not before it.
NORMALISERS["products"] = {
    "money":    ["unit_price", "unit_cost"],
    "bool":     ["recyclable_packaging", "active_flag"],
    "date":     ["launch_date"],
    "number":   ["launch_year", "warranty_months", "weight_kg"],
}
NORMALISERS["customers"] = {
    "money":    ["lifetime_value_before_period"],
    "bool":     ["marketing_consent"],
    "date":     ["signup_date"],
    "number":   ["prior_12m_orders"],
}

gaps = normaliser_gaps()
print("remaining gaps in a source column:", int(gaps.in_source.sum()) if len(gaps) else 0)
print(gaps.to_string(index=False) if len(gaps) else "none")


# **The same plan, derived a second way.** The map above is hand-written, so it carries the risk
# every hand-written list carries: a field can sit in the wrong category, or be missing, and nothing
# says so. The data dictionary can produce the same plan independently — `data_type` names the date,
# datetime and boolean fields, and `comparison_rule` is what separates money from ordinary numbers,
# since the dictionary has no money type of its own.
#
# Two things the dictionary cannot know, which is why this is a comparison rather than a replacement.
# A field can carry a target type and have no source column at all, because it is produced by the
# text functions rather than read from a file. And the dictionary describes the target, not how each
# file spells the value: the coupon discount is simply a number there, while one source writes it
# with a percent sign. Both corrections are applied below and stated rather than hidden.
#
# Date and datetime stay separate categories even though they parse identically, because they are
# written out differently — one as a plain date, the other with a time. Merging them would append a
# zero time to five fields at export.


# In[20]:

# --- 1.3b Cross-check: the same plan, derived from the dictionary ---

MONEY_RULE     = "numeric tolerance 0.01"
PERCENT_FIELDS = {"coupon_discount"}   # one source writes '10%'; the dictionary only says 'number'

def plan_from_dictionary(table):
    """The normalisation plan the data dictionary implies for one table."""
    plan = {"money": [], "number": [], "date": [], "datetime": [], "bool": []}
    for _, field in DICTIONARY[DICTIONARY.output_table == table].iterrows():
        if field.data_type == "number":
            bucket = "money" if field.comparison_rule == MONEY_RULE else "number"
            plan[bucket].append(field.field_name)
        elif field.data_type == "boolean":
            plan["bool"].append(field.field_name)
        elif field.data_type in plan:
            plan[field.data_type].append(field.field_name)

    # The dictionary has no percent type: it describes the target, not the source spelling.
    plan["percent"] = [f for f in plan["number"] if f in PERCENT_FIELDS]
    plan["number"]  = [f for f in plan["number"] if f not in PERCENT_FIELDS]

    # A derived field has a target type but no source column to normalise.
    in_source = set().union(*(set(t[table].columns)
                              for t in (json_tables, xml_tables) if table in t))
    return {kind: sorted(f for f in fields if f in in_source)
            for kind, fields in plan.items() if any(f in in_source for f in fields)}

for table, hand_written in NORMALISERS.items():
    derived = plan_from_dictionary(table)
    assert {k: sorted(v) for k, v in hand_written.items()} == derived, (table, derived)

print("hand-written map and dictionary-derived plan agree on all",
      len(NORMALISERS), "tables")


# #### 1.3c Candidate keys and duplicates within each source
#
# The data dictionary names the primary key of each output table (`position = 1`,
# `nullable = False`). It does **not** say which source column carries that key, or whether
# the column is actually unique. Both have to be shown.
#
# The scan below ranks *every* column by distinct values, so the key comes out of the scan
# instead of going into it. Read three things from the output: which column tops each table,
# whether a second column ties it, and how far short of unique the top column falls.


# In[21]:

def candidate_keys(tables, top=3):
    """Rank every column by how close it is to being a primary key.

    A key candidate has one distinct value per row and no blanks. Ranking all columns,
    rather than naming the key first, is what makes the key a result.
    """
    rows = []
    for name, df in tables.items():
        n = len(df)
        scored = [(c, df[c].astype(str).nunique(), int((df[c].astype(str) == "").sum()))
                  for c in df.columns if c != "source_system"]
        scored.sort(key=lambda r: -r[1])
        for col, distinct, blank in scored[:top]:
            rows.append({"table": name, "column": col, "rows": n,
                         "distinct": distinct, "blank": blank,
                         "duplicate_key_rows": n - distinct,
                         "unique_key": distinct == n and blank == 0})
    return pd.DataFrame(rows)

print("JSON"); print(candidate_keys(json_tables).to_string(index=False))
print()
print("XML");  print(candidate_keys(xml_tables).to_string(index=False))


# **Read from the scan.** The top-ranked column in every table is the dictionary's
# `position = 1` field, so the declared key and the observed key agree — the key was not chosen,
# it was confirmed.
#
# Three things follow:
#
# - In the JSON, `orders.source_system_record_id` ties `order_id` exactly, so it is an equally
#   unique candidate. The next cell decides between them.
# - Only `customers` (JSON), `products` and `warehouses` (XML) have a key that is unique inside a
#   single file. Every other table repeats keys.
# - A repeated key is not yet a problem. What matters is whether the repeated rows are identical
#   in every column, which is what the next cell asks.


# #### Choosing between two equally unique columns
#
# The scan ranked `order_id` and `source_system_record_id` identically, so it cannot separate them.
# Four questions can. Ask them *before* writing `KEYS`, not after.
#
# 1. **One-to-one?** If one value maps to several of the other, they are not interchangeable.
# 2. **Stable across sources?** A key whose value changes between the two files cannot join them.
# 3. **Referenced by other tables?** The column other tables point at is the join key, whatever
#    else happens to be unique.
# 4. **Derived?** A column computed from another carries no separate identity — it only re-encodes
#    whatever produced it, plus whatever else got baked in.


# In[22]:

# Four questions decide between two columns that are unique to the same degree.
orders_all = pd.concat([json_tables["orders"], xml_tables["orders"]], ignore_index=True)
A, B = "order_id", "source_system_record_id"

print(f"1. one-to-one across the union ({len(orders_all):,} rows)")
print(f"   one {A} -> many {B}: {int(orders_all.groupby(A)[B].nunique().gt(1).sum())}")
print(f"   one {B} -> many {A}: {int(orders_all.groupby(B)[A].nunique().gt(1).sum())}")

shared = sorted(set(json_tables["orders"][A]) & set(xml_tables["orders"][A]))
j = json_tables["orders"].drop_duplicates(A).set_index(A).loc[shared]
x = xml_tables["orders"].drop_duplicates(A).set_index(A).loc[shared]
print(f"\n2. stable for the same order in both files ({len(shared)} shared orders)")
print(f"   {B} differs between the files: {int((j[B].values != x[B].values).sum())}")

print("\n3. which column do the other tables point at?")
for source, tabs in (("JSON", json_tables), ("XML", xml_tables)):
    for name, df in tabs.items():
        if name == "orders":
            continue
        pointers = [c for c in (A, B) if c in df.columns]
        if pointers:
            print(f"   {source} {name:16s} {pointers}")

print("\n4. is either column derived from the other?")
stem = orders_all[B].str.rsplit("-", n=1).str[0]
print(f"   distinct {B} stems: {sorted(stem.unique())}")
rebuilt = stem + "-" + orders_all[A].str[4:]
print(f"   rows where {B} == stem + {A}[4:]: {int((rebuilt == orders_all[B]).sum()):,} of {len(orders_all):,}")


# The four answers, read together.
#
# 1. Perfectly one-to-one — zero breaks in either direction.
# 2. Identical in both files for all 500 shared orders. Both columns are stable.
# 3. `order_items`, `deliveries` and `product_reviews` all carry `order_id`. Nothing, in either
#    file, carries `source_system_record_id`.
# 4. `source_system_record_id` is the stem `SRC-001-H` plus the last six characters of `order_id`,
#    for every row of both files.
#
# Test 4 settles it. `source_system_record_id` is not a second identity — it is `order_id`
# re-packaged with the group number (`001`) and a source marker (`H`). That is metadata about
# *this delivery of the data*, not about the order, so choosing it would build the group number
# into the primary key of a submitted table. Tests 1 and 2 say the choice is safe either way;
# test 3 says only one of them is usable for joins; test 4 says only one of them is an identity.
#
# `order_id` is the key. Both columns still go into `orders` — the dictionary requires both.
#
# One consequence worth carrying forward: `order_id` is ten characters and the numeric part is
# zero-padded in every row. It stays a string. Casting it to an integer destroys the padding,
# which the specification bans by name.


# In[23]:

# The scan above confirms every declared key, so KEYS is the dictionary's own list.
# One definition of "what is the key", read from the dictionary in Section 1.1.
KEYS = dict(DECLARED_KEYS)

def duplicate_shape(tables):
    """Summarise duplicated keys and whether each duplicate group is identical."""
    rows = []

    for name, key in KEYS.items():
        if name not in tables:
            continue

        df = tables[name].drop(columns="source_system")
        duplicate_rows = df[df.duplicated(key, keep=False)]

        identical_keys = 0
        conflicting_keys = 0

        for _, group in duplicate_rows.groupby(key, dropna=False):
            if len(group.drop_duplicates()) == 1:
                identical_keys += 1
            else:
                conflicting_keys += 1

        rows.append({
            "table": name,
            "rows": len(df),
            "duplicate_keys": duplicate_rows[key].nunique(),
            "copies_per_key": sorted(
                duplicate_rows[key].value_counts().unique().tolist()
            ),
            "field_identical_keys": identical_keys,
            "conflicting_keys": conflicting_keys,
        })

    return pd.DataFrame(rows)

print("JSON"); print(duplicate_shape(json_tables).to_string(index=False))
print()
print("XML");  print(duplicate_shape(xml_tables).to_string(index=False))


# #### 1.3d Foreign keys and cross-source overlap
#
# The dictionary lists no foreign keys; the specification lists eight required ones. A foreign
# key can only be checked against the table that owns the parent key — and that owner may sit in
# the *other* file. `products` exists only in the XML, `customers` only in the JSON.
#
# So each child column is checked twice: against its own source, and against both sources pooled.
# The gap between those two numbers answers the question "must the sources be combined before the
# six tables are built".


# In[24]:

def parent_pools(*table_sets):
    """Parent side of a foreign key = the primary-key column of the table that owns it.

    Pooling every id column instead would make each check trivially pass, because a child
    column would be compared against a pool containing itself.
    """
    pools = {}
    for tables in table_sets:
        for name, key in KEYS.items():
            if name in tables:
                pools.setdefault(key, set()).update(tables[name][key].astype(str))
    return pools

POOL = {"JSON": parent_pools(json_tables),
        "XML":  parent_pools(xml_tables),
        "both": parent_pools(json_tables, xml_tables)}

def foreign_keys(tables, source):
    """Every id column that is not its own table's key is a candidate foreign key."""
    rows = []
    for name, df in tables.items():
        for col in df.columns:
            if col not in POOL["both"] or col == KEYS.get(name):
                continue
            vals = set(df[col].astype(str))
            rows.append({"source": source, "child": f"{name}.{col}", "parent": col,
                         "distinct": len(vals),
                         "unmatched_in_own_source": len(vals - POOL[source].get(col, set())),
                         "unmatched_in_both":       len(vals - POOL["both"][col])})
    return rows

pd.DataFrame(foreign_keys(json_tables, "JSON") + foreign_keys(xml_tables, "XML"))

# How many canonical rows each table really has: the union of the two sources, per key.
overlap = []
for name, key in KEYS.items():
    j = set(json_tables[name][key].astype(str)) if name in json_tables else set()
    x = set(xml_tables[name][key].astype(str))  if name in xml_tables  else set()
    overlap.append({"table": name, "json_only": len(j - x), "in_both": len(j & x),
                    "xml_only": len(x - j), "canonical_rows": len(j | x)})

pd.DataFrame(overlap)


# **Read from the two outputs.** Three things they settle:
#
# 1. Every candidate foreign key resolves against the pooled sources, and several do not resolve
#    inside their own file — so neither export is self-consistent and the union is required.
# 2. Matching row counts between the two files are not overlap. The counts are equal and the
#    intersection is small.
# 3. `canonical_rows` is the row count each output table must have after reconciliation, derived
#    here rather than assumed in Section 4.
#
# What remains for 1.3e: do the *shared* keys agree field by field once normalised?


# #### 1.3e Do the shared records agree?
#
# 3,259 keys appear in both files. If any field disagrees for the same key, Section 4 needs a documented
# conflict rule. If nothing disagrees, keeping either copy is safe and the rule only has to be
# deterministic.
#
# The comparison runs twice on purpose. Un-normalised, the two files differ on every formatted
# column — `10` against `10%`, `true` against `Y`, ISO against day-first — and the output looks
# like a catastrophic conflict register. Normalised, that noise disappears. Comparing before
# normalising is the mistake this cell exists to make visible.


# In[25]:

def compare_shared_records(name, key, normalised=True):
    """For keys present in both files: does every shared column hold the same value?

    `normalised=False` compares the raw strings, which is the wrong way round and is shown
    only so the difference between a format difference and a real conflict is on the page.
    """
    spec = NORMALISERS.get(name, {})
    j = json_tables[name].drop_duplicates(key).set_index(key)
    x = xml_tables[name].drop_duplicates(key).set_index(key)
    shared = sorted(set(j.index) & set(x.index))
    columns = sorted((set(j.columns) & set(x.columns)) - {"source_system"})

    conflicts = {}
    for col in columns:
        if normalised:
            a = normalise(j.loc[shared, col], col, spec, dayfirst=False)
            b = normalise(x.loc[shared, col], col, spec, dayfirst=True)
        else:
            a, b = j.loc[shared, col].astype(str), x.loc[shared, col].astype(str)
        rows = int((a.values != b.values).sum())
        if rows:
            conflicts[col] = rows

    return {"table": name, "shared_keys": len(shared), "columns_compared": len(columns),
            "conflicting_columns": len(conflicts), "detail": conflicts or "none"}

in_both = [(n, k) for n, k in KEYS.items() if n in json_tables and n in xml_tables]
print("BEFORE normalisation")
print(pd.DataFrame([compare_shared_records(n, k, normalised=False) for n, k in in_both]).to_string(index=False))
print("\nAFTER normalisation")
print(pd.DataFrame([compare_shared_records(n, k, normalised=True) for n, k in in_both]).to_string(index=False))


# Zero conflicts, across 3,259 shared keys and 59 compared columns.
#
# Every column flagged in the first table was a format difference, not a value difference. This is
# the result Section 4 depends on: **no JSON-over-XML or XML-over-JSON precedence rule is needed.** Any
# deterministic choice of copy — normalise first, then `drop_duplicates(key, keep="first")` —
# produces the same row.
#
# The check stays in the notebook rather than being replaced by that sentence, because the
# specification requires a conflict to be *recorded* if one is ever found. Run on different data,
# this cell reports it instead of hiding it.


# #### 1.3f Assumptions register
#
# Everything the later sections are allowed to rely on, with the cell that evidences it. An
# assumption with no evidence cell is not an assumption, it is a guess.
#
# | ID | Assumption | Evidence | If it is wrong |
# |---|---|---|---|
# | A1 | The six primary keys are `order_id`, `order_item_id`, `delivery_id`, `customer_id`, `product_id`, `review_id` | Section 1.3c candidate-key scan; each is the dictionary's `position = 1`, `nullable = False` field | every grain and every foreign key is wrong |
# | A2 | `source_system_record_id` re-encodes `order_id`; it is not a second identity | Section 1.3c key-choice cell, test 4 | the group number ends up inside a primary key |
# | A3 | Every duplicated key is exactly two field-identical copies | Section 1.3c `duplicate_shape` | dedup needs a real precedence argument, not a deterministic one |
# | A4 | The population is the union of the two files, not either file alone | Section 1.3d foreign keys and overlap | row counts are ~45% short and foreign keys fail |
# | A5 | Shared keys agree on every field once normalised, so no precedence rule is needed | Section 1.3e | Section 4 must record field-level conflicts in validation |
# | A6 | Identifiers stay strings; the zero padding is significant | Section 1.3c key-choice cell; spec Task 2 | keys stop matching across tables |
# | A7 | `coupon_discount` is a percentage, values 0/5/10/15/20/25 | Section 1.3a format table | `order_total` breaks for ~78% of orders |
# | A8 | Missing means an empty string in the JSON and an empty element in the XML; `coupon_code` is the only field that has any | Section 1.1 and Section 1.2 blank scans | the `NaN` sentinel is written in the wrong places |


# ### 1.4 Grain of each source collection
#
# Grain is what one row represents. It is the one Task 1 requirement the sections above answer only
# in passing, so it gets its own cell rather than a sentence. The evidence is rows-per-parent: if a
# collection holds one row per order, every order has exactly one; if it holds one row per line item,
# orders carry several.


# In[26]:

def grain(tables, source):
    """Rows per parent entity, before and after removing duplicate keys.

    The raw number is what the file contains; the deduplicated number is the real grain.
    Reporting only the raw number would put a duplication artefact into a range check.
    """
    rows = []
    for name, df in tables.items():
        if name in ("order_items", "deliveries") and "order_id" in df.columns:
            raw = df.groupby("order_id").size()
            deduped = df.drop_duplicates(DECLARED_KEYS[name]).groupby("order_id").size()
            shape = (f"raw {raw.min()}-{raw.max()} (median {int(raw.median())})"
                     f"   deduplicated {deduped.min()}-{deduped.max()}")
        else:
            shape = "not a child of orders"
        rows.append({"source": source, "collection": name, "rows": len(df),
                     "rows per order": shape})
    return pd.DataFrame(rows)

print(grain(json_tables, "JSON").to_string(index=False))
print()
print(grain(xml_tables, "XML").to_string(index=False))

# Where the raw maximum comes from: the sizes above 5 are each double a size at or below 5.
print("\nraw rows per order, JSON:")
print(json_tables["order_items"].groupby("order_id").size().value_counts().sort_index().to_string())

print()
for source, tabs in (("JSON", json_tables), ("XML", xml_tables)):
    r = tabs["product_reviews"]
    print(f"{source} reviews: {len(r):,} rows · {r.review_id.nunique():,} review_id"
          f" · {r.order_item_id.nunique():,} order_item_id")


# Read from the output:
#
# - `orders` and `deliveries` are **one row per order**.
# - `order_items` is **one row per line item, 1 to 5 per order**. The raw maximum of 10 is not a
#   large cart — it is a duplicated one. The raw distribution has no order with 7 or 9 items, and
#   the sizes 6, 8 and 10 are each exactly double a real size (3, 4, 5): when an order is
#   duplicated, its whole cart is duplicated with it. 46 JSON orders and 51 XML orders sit above 5
#   raw; after deduplication none do. *(An earlier version of this cell reported the raw range only, and a `1-10` range check
#   would never have fired.)*
# - `customers`, `products` and `warehouses` are one row per customer, product and warehouse.
# - `product_reviews` has as many distinct `order_item_id` as `review_id` (3,850 either way), so
#   its grain is **one row per reviewed order item**, and no order item is reviewed twice.
#
# All six match the grains the data dictionary prescribes — worth confirming rather than assuming,
# because a source whose grain disagreed with the target grain would force a fan-out or a roll-up
# in Section 4, and none does.


# ### 1.5 Task 1 requirement coverage
#
# Every investigation Task 1 names, and the cell that answers it. This exists so a reviewer does not
# have to search, and so a gap is visible rather than silent.
#
# | Task 1 requires | Answered in | Status |
# |---|---|---|
# | major objects, nested arrays, repeated XML elements, source-specific representations | Section 1.1 and Section 1.2 structure surveys; Section 1.3a format table | done |
# | candidate primary keys | Section 1.3c candidate-key scan, and the four-question key-choice cell | done |
# | foreign keys | Section 1.3d `parent_pools()` / `foreign_keys()` — 16 candidate child columns, 0 unmatched against the union | done |
# | the grain of each source collection | Section 1.4 | done |
# | date, timestamp, boolean, currency, percentage and missing-value formats | Section 1.3a format table; Section 1.1 and Section 1.2 blank scans | done |
# | fields that appear in one or both sources | Section 1.3a field coverage | done |
# | duplicate records within a source | Section 1.3c `duplicate_shape()` | done |
# | overlapping records across sources | Section 1.3d overlap table; Section 1.3e field-level agreement | done |
# | assumptions needed before transformation | Section 1.3f register, A1–A8 | done |
# | the completed source-to-target mapping | Section 2 | done |
#
# The mapping is the only outstanding item in Task 1.


# #### 1.6 An existence count taken straight from the bytes
#
# This is a diagnostic, not parsing: it never decides a field boundary, it only answers
# whether a key appears in the source at all. It is lower-cased because the two files spell
# the same field differently — the JSON writes `couponCode`, the XML writes `Coupon_Code` —
# and a case-sensitive count reports zeros that look like absence but are spelling.
#
# The value of counting bytes rather than parsed columns is that it is independent of every
# assumption made above.


# In[27]:

# --- Section 1.6: byte-level existence counts ---
for path in (JSON_PATH, XML_PATH):
    blob = path.read_bytes().lower()
    print(path.name)
    for key in (b'promo', b'coupon_code', b'couponcode',
                b'customer_note', b'customernote'):
        print(f'   {key.decode():<16} {blob.count(key):>8}')

# A populated XML element writes an open and a close tag; an empty one is self-closing.
xml_bytes = XML_PATH.read_bytes()
populated = xml_bytes.count(b'<Coupon_Code>')
empty     = xml_bytes.count(b'<Coupon_Code />')
print(f'\nXML coupon codes: {populated:,} populated, {empty:,} empty, {populated + empty:,} orders')
print('The promotion markers counted above match the populated codes in the same file,')
print('which is an expected extraction count for Section 3 taken from neither parser.')


# ## 2. Source-to-target mapping
#
# The mapping is one row per column of the six output tables — 111 rows in all. Each row answers
# three questions about that column: where in the raw files the value comes from, what happened
# to it on the way, and what happens when both files supply it.
#
# It is placed here, before the tables are built, because the marker reads it as the plan; but
# every one of its columns is *derived* below rather than declared. The two source paths are read
# out of the files, the transformation text is written from the code in Sections 3 and 4, and the
# overlap rule is the rule Section 5 actually applies. Nothing in this section is typed from
# memory, and the checks at the end fail if any column drifts from what the notebook does.


# ### 2.1 Reading the source paths out of the files
#
# **Why.** There are 111 paths to record. Typing them by hand is 111 chances to make a quiet typo,
# and this is the one document a marker checks *against* the raw files.
#
# **What.** Two short walkers list every leaf path in each source — every place a scalar value
# actually sits. The JSON walker collapses lists to `[]`, because a path describes the shape of a
# record, not the position of one row.
#
# **How.** The same field is spelled three ways: `orderID` in the JSON, `Order_ID` in the XML,
# `order_id` in the dictionary. Lowercasing and dropping underscores makes all three one key, so
# each dictionary field can be looked up in both files at once.
#
# **The catch.** A name on its own is ambiguous. `order_id` sits in four different JSON blocks and
# `customer_id` in three. Matching on the name alone reports that the customers table exists in the
# XML — it does not; what exists there is a *pointer* to a customer. So one thing is declared by
# hand: which block of each file holds one record per output row. That is the grain evidenced
# earlier in this notebook, and it is six lines rather than 111.


# In[28]:

# Every place a scalar value actually sits, in each file.

def json_leaves(node, path=""):
    """Dotted path of every scalar. Lists collapse to '[]': a path describes the
    shape of a record, not the position of one row."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from json_leaves(value, f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for item in node[:50]:        # 50 samples is enough to catch optional keys
            yield from json_leaves(item, path + "[]")
    else:
        yield path

def xml_leaves(element, path=""):
    """Path of every childless element."""
    path = f"{path}/{element.tag}" if path else element.tag
    if len(element) == 0:
        yield path
    else:
        for child in element:
            yield from xml_leaves(child, path)

json_paths = set(json_leaves(raw_json))
xml_paths = set(xml_leaves(root))

print(f"leaf paths — JSON {len(json_paths)}, XML {len(xml_paths)}")


# In[29]:

def flat_name(name):
    """orderID, Order_ID and order_id are one field in three casings."""
    return name.lower().replace("_", "")

def index_by_leaf(paths, separator):
    """Group paths by their last segment, since one name occurs in several blocks."""
    index = {}
    for path in paths:
        index.setdefault(flat_name(path.split(separator)[-1]), []).append(path)
    return index

json_index = index_by_leaf(json_paths, ".")
xml_index = index_by_leaf(xml_paths, "/")

# Which block of each file holds one record per output row. This is the grain
# evidenced above, and it is the only declared part of the mapping's paths.
ANCHOR = {
    "orders":          ("orders[].header.",         "Orders/Order/Header/"),
    "order_items":     ("orders[].shoppingCart[].", "Orders/Order/Shopping_Cart/Item/"),
    "deliveries":      ("orders[].delivery.",       "Orders/Order/Delivery/"),
    "customers":       ("customerProfiles[].",      None),   # no customer records in the XML
    "products":        (None,                       "ProductCatalogue/Product/"),
    "product_reviews": ("productReviews[].",        "ProductReviews/Review/"),
}

def path_under(candidates, prefix):
    """Keep the single candidate sitting under this table's anchor."""
    if prefix is None:
        return ""
    matches = [path for path in candidates if prefix in path]
    return matches[0] if len(matches) == 1 else ""

rows = []
for _, field in DICTIONARY.iterrows():
    json_prefix, xml_prefix = ANCHOR[field.output_table]
    candidates = flat_name(field.field_name)
    json_path = path_under(json_index.get(candidates, []), json_prefix)
    xml_path = path_under(xml_index.get(candidates, []), xml_prefix)

    rows.append({
        "mapping_id": f"MAP-{field.output_table}-{field.position:02d}",
        "output_table": field.output_table,
        "target_field": field.field_name,
        "source_format": ("both" if json_path and xml_path
                          else "JSON" if json_path
                          else "XML" if xml_path
                          else "derived"),
        "json_source_path": json_path,
        "xml_source_path": xml_path.replace("OperationsExport/", ""),
    })

MAPPING_PATHS = pd.DataFrame(rows)

MAPPING_PATHS.pivot_table(index="output_table", columns="source_format",
                          values="target_field", aggfunc="count", fill_value=0)


# Read from the output: no table mixes its sources. Customers come only from the JSON, products only
# from the XML, and the four order-shaped tables from both. The ten fields left over are the ones
# with no field of that name in either file — which is what a derived field looks like from the
# outside, and is the same ten the field-coverage check named earlier by a completely different
# route.


# In[30]:

# "derived" is not declared anywhere above: it is simply what is left when no field of
# that name exists at that table's grain in either file. If an anchor were wrong, this
# list would move — which is what makes it a check rather than a restatement.
assert len(MAPPING_PATHS) == 111, len(MAPPING_PATHS)

derived = MAPPING_PATHS[MAPPING_PATHS.source_format == "derived"]
print(f"{len(derived)} fields with no source path:")
print(derived[["output_table", "target_field"]].to_string(index=False))

# The number in each mapping_id is the dictionary's own position, so the mapping, the
# dictionary and the column order of the output CSVs remain one ordering, not three.
positions = MAPPING_PATHS.mapping_id.str.extract(r"-(\d+)$")[0].astype(int)
assert (positions.values == DICTIONARY.position.values).all()
print("\nrow numbers match the dictionary's field positions")


# ### 2.2 A derived field still has a source
#
# `derived` means *computed rather than copied*. It does not mean the value appears from nowhere,
# and a mapping that leaves those ten rows pathless hides the one thing a reader most needs: that
# several of them are different readings of the same piece of text.
#
# The cell below asks which raw field each derived target is computed from, and looks its path up
# through the same index and the same anchors used above — so if a field moved in the source, these
# rows would go blank rather than quietly keep an old path.


# In[31]:

# The one declared thing: which raw field feeds each derived target. Everything below is
# looked up, not typed. The choice of feeder is a real judgement - the extraction fields read
# the note and the review body before cleaning, the measure fields read them after - and it is
# recorded here because no scan can recover it from the source alone.
DERIVED_SOURCE = {
    "customer_note_clean":        "customerNote",
    "promo_code":                 "customerNote",
    "product_description_clean":  "productDescription",
    "review_body_clean":          "reviewText",
    "review_body_latin_analysis": "reviewText",
    "review_length_chars":        "reviewText",
    "review_word_count":          "reviewText",
    "contains_non_latin_script":  "reviewText",
    "extracted_order_reference":  "reviewText",
    "extracted_product_sku":      "reviewText",
}

# Same lookup as Section 2.1: flatten the casing, then keep the candidate under this table's anchor.
for position, row in MAPPING_PATHS.iterrows():
    if row.source_format != "derived":
        continue
    feeder = flat_name(DERIVED_SOURCE[row.target_field])
    json_prefix, xml_prefix = ANCHOR[row.output_table]
    MAPPING_PATHS.at[position, "json_source_path"] = path_under(
        json_index.get(feeder, []), json_prefix)
    MAPPING_PATHS.at[position, "xml_source_path"] = path_under(
        xml_index.get(feeder, []), xml_prefix).replace("OperationsExport/", "")

derived = MAPPING_PATHS[MAPPING_PATHS.source_format == "derived"]

# Every derived row must now name at least one source. A blank here means the feeder field
# is not where DERIVED_SOURCE says it is, which is a fault in this cell, not in the data.
assert (derived.json_source_path.ne("") | derived.xml_source_path.ne("")).all()

print(derived[["output_table", "target_field",
               "json_source_path", "xml_source_path"]].to_string(index=False))
# How many targets each raw field feeds. This is the fan-out the mapping has to make
# visible: it appears nowhere in the column names.
print("\nfan-out, raw field -> number of derived targets:")
print(derived.target_field.map(DERIVED_SOURCE).value_counts().to_string())


# Read from the output: three raw fields feed all ten derived targets. One review body becomes
# seven columns of `product_reviews`; one customer note becomes two columns of `orders`; one
# product description becomes one column of `products`. The description has no JSON path because
# product records exist only in the XML, which matches the survey above.


# ### 2.3 The transformation column
#
# Four shapes cover all 111 rows, and which shape a row takes is looked up rather than decided
# by hand:
#
# - **a cast**, when the dictionary types the field and the two sources spell it differently —
#   money, percent, boolean, date, datetime, plain number;
# - **a direct copy**, when the value is carried through unchanged after deduplication;
# - **a recomputation**, for the five monetary fields the specification defines by formula, which
#   are rebuilt from the canonical rows rather than copied and then reconciled against the source;
# - **a text derivation**, for the ten fields with no source column of that name, each produced by
#   one of the published functions in Section 3.
#
# The category comes from the dictionary's own `data_type`, so a field cannot be described as a
# date here and parsed as text in Section 4 without this cell changing too.


# In[32]:

# --- Section 2.3: the transformation column ---

# Which of the four shapes a row takes. Categories come from the dictionary, not from a
# hand-written list, so this cell cannot disagree with the contract Section 4 conforms to.
CATEGORY_TEXT = {
    'money':    'Strip the AUD label and thousands separator, cast to float, round to two '
                'decimals (Section 4.0.1 norm_money, Section 4.0.3 money_round). The JSON '
                'arrives numeric; one function accepts both spellings.',
    'percent':  'Strip the per-cent sign and cast to float. Held as percentage points, not a '
                'fraction — the arithmetic in Section 4.1 divides by 100 (Section 4.0.1).',
    'boolean':  "XML 'Y'/'N' and JSON native true/false both become a Python bool "
                '(Section 4.0.1 norm_bool).',
    'date':     'Parsed day-first for the XML and ISO for the JSON, held as a Timestamp through '
                'Section 4, emitted as YYYY-MM-DD at export (Section 4.0.1, Section 7).',
    'datetime': 'Parsed day-first for the XML and ISO for the JSON, held as a Timestamp through '
                'Section 4, emitted as YYYY-MM-DD HH:MM:SS at export (Section 4.0.1, Section 7).',
    'number':   'Cast to numeric (Section 4.0.1).',
}
DIRECT_COPY = ('Direct copy after deduplication. No case change; identifier padding is '
               'preserved by holding the column as string through export.')

# Money is not a data_type. The dictionary types money and plain numbers alike as
# `number` and distinguishes them by comparison_rule, which is what Section 4.0 also
# reads — so the two cannot drift apart. Percent is the one case the dictionary cannot
# express at all, and it is named here for that reason.
MONEY_RULE     = 'numeric tolerance 0.01'   # the dictionary's own marker for a money field
PERCENT_FIELDS = {'coupon_discount'}        # XML writes '10%'; the contract only says 'number'

def category_of(field, data_type, comparison_rule):
    if data_type == 'number':
        if comparison_rule == MONEY_RULE:
            return 'money'
        if field in PERCENT_FIELDS:
            return 'percent'
    return data_type

# The five fields the specification defines by formula. They are rebuilt from the canonical
# rows and reconciled against the source value, never copied.
RECOMPUTED = {
    ('order_items', 'line_revenue'):
        'Recomputed as round(quantity x unit_price, 2) from the normalised columns; the source '
        'value is not copied. Reconciled against the source at the published tolerance 0.01 '
        '(Section 4.2, VAL-ARITH-01).',
    ('orders', 'order_price'):
        'Recomputed as round(sum of line_revenue, 2) over the canonical order_items of each '
        'order; the source value is not copied. Reconciled at tolerance 0.01 (Section 4.1, '
        'VAL-ARITH-02).',
    ('orders', 'tax_amount'):
        'Recomputed as round(order_price / 11, 2) — the price already includes GST, so the tax '
        'is divided out rather than added on, and it is reported separately rather than added '
        'to order_total. Reconciled at tolerance 0.01 (Section 4.1, VAL-ARITH-04).',
    ('orders', 'order_total'):
        'Recomputed as round(order_price x (1 - coupon_discount/100) + delivery_charges, 2), in '
        'that order: the discount is percentage points and applies before delivery, and GST is '
        'not added again. Reconciled at tolerance 0.01 (Section 4.1, VAL-ARITH-03).',
    ('orders', 'coupon_code'):
        'Direct copy. Missing is an empty string in the JSON and an empty element in the XML; '
        "both become the literal three-character 'NaN' sentinel, filled before any string cast "
        '(Section 4.1).',
    ('deliveries', 'delivery_note_clean'):
        'Direct copy from the source column of the same name, deliberately not cleaned. The '
        'field holds two structured values across all canonical deliveries and carries no '
        'markup, markers, URLs, entities or non-Latin characters; passing it through the '
        'narrative cleaner would alter every row by letter case alone and corrupt a categorical '
        '(Section 4.4, VAL-TEXT-01b).',
}

# The ten fields with no source column of that name. Each is produced by one published
# function; the wording states which value the function reads, because extraction runs on the
# raw text and the measures run on the cleaned text.
TEXT_DERIVED = {
    ('orders', 'customer_note_clean'):
        'clean_narrative_text(customer_note_raw). Decodes HTML entities, normalises to NFC, '
        'removes tags, the published bracketed markers, URLs, the PROMO wrapper with its code, '
        'the Reference and SKU wrappers, the two hashtag/handle markers and Unicode symbol '
        "characters, then lower-cases and collapses whitespace. Missing becomes 'NaN' "
        '(Sections 3.1, 4.1).',
    ('orders', 'promo_code'):
        'extract_promo_code(customer_note_raw), read from the raw note before cleaning removes '
        'the marker. Matches a standalone B1-B5 SAVE code with exactly two digits, bounded so a '
        "neighbouring letter, digit, hyphen or underscore rejects it; upper-cased, else 'NaN' "
        '(Sections 3.1, 4.1). Cross-checked against the structured coupon_code column '
        '(VAL-TEXT-13).',
    ('products', 'product_description_clean'):
        'clean_narrative_text(product_description_raw), the same published cleaner as above. '
        'Products exist only in the XML, so there is no JSON path (Sections 3.1, 4.5).',
    ('product_reviews', 'review_body_clean'):
        'clean_narrative_text(review_body_raw), the same published cleaner. Non-Latin scripts '
        'are preserved at this step; only the published noise is removed (Sections 3.1, 4.6).',
    ('product_reviews', 'review_body_latin_analysis'):
        'build_latin_analysis(review_body_clean) — computed from the cleaned body, not the raw '
        'review. Replaces every letter outside the Latin script with a space and collapses '
        "whitespace; returns 'NaN' when no Latin letter remains. Digits and punctuation are "
        'left alone, because the published rule removes non-Latin letters rather than keeping '
        'only Latin characters (Sections 3.1, 4.6).',
    ('product_reviews', 'review_length_chars'):
        'Number of Python characters in review_body_clean. Where the cleaned body is the literal '
        "'NaN' sentinel the count is 0, not 3, because the sentinel is an absent review rather "
        'than a three-character one (Section 4.6, VAL-ARITH-07).',
    ('product_reviews', 'review_word_count'):
        'Number of whitespace-separated tokens in review_body_clean, with the same sentinel rule '
        'as review_length_chars: 0 rather than 1 (Section 4.6, VAL-ARITH-07).',
    ('product_reviews', 'contains_non_latin_script'):
        'contains_non_latin_script(review_body_clean). True when any letter of the cleaned body '
        'is outside the Latin script; digits and punctuation are ignored, since only letters '
        'identify a script. Agrees with the structured language_code on every review '
        '(Sections 3.1, 4.6).',
    ('product_reviews', 'extracted_order_reference'):
        'extract_order_reference(review_body_raw), read from the raw review before cleaning '
        'removes the wrapper. Matches a standalone HORD/CORD followed by exactly six digits, '
        'bounded against a neighbouring letter, digit, hyphen or underscore, and rejected unless '
        "the match is ASCII; upper-cased, else 'NaN' (Sections 3.1, 4.6, VAL-TEXT-14).",
    ('product_reviews', 'extracted_product_sku'):
        'extract_product_sku(review_body_raw), read from the raw review for the same reason. '
        'Matches a standalone SKU- prefix followed by ASCII letters or digits, bounded the same '
        "way and rejected unless the match is ASCII; upper-cased, else 'NaN' (Sections 3.1, "
        '4.6, VAL-TEXT-15).',
}

rows = []
for _, f in dd.iterrows():
    key = (f.output_table, f.field_name)
    if key in TEXT_DERIVED:
        rows.append(TEXT_DERIVED[key])
    elif key in RECOMPUTED:
        rows.append(RECOMPUTED[key])
    else:
        rows.append(CATEGORY_TEXT.get(
            category_of(f.field_name, f.data_type, f.comparison_rule), DIRECT_COPY))

MAPPING_PATHS['transformation_or_derivation'] = rows

# The ten text derivations must be exactly the ten rows the path search found sourceless.
# Two independent routes to the same set; a disagreement means one of them is wrong.
by_text  = {k for k in TEXT_DERIVED}
by_paths = set(zip(MAPPING_PATHS.loc[MAPPING_PATHS.source_format == 'derived', 'output_table'],
                   MAPPING_PATHS.loc[MAPPING_PATHS.source_format == 'derived', 'target_field']))
assert by_text == by_paths, by_text ^ by_paths

print(f'{len(MAPPING_PATHS)} rows written')
print(f'  {len(by_text)} text derivations, agreeing with the path search')
print(f'  {len(RECOMPUTED)} individually worded rows')
print('  the rest by dictionary data_type:')
print(MAPPING_PATHS.loc[~MAPPING_PATHS.set_index(['output_table', 'target_field']).index
                        .isin(by_text | set(RECOMPUTED)), 'transformation_or_derivation']
      .str.slice(0, 40).value_counts().to_string())


# ### 2.4 The overlap and conflict column
#
# This column asks one question for every field: *both files supply this value for the same
# business key — what then?* The answer has three shapes on this data, and which one a row takes
# follows from where its table comes from, not from a preference.
#
# **Four tables arrive from both files.** For those the rule is the one Section 5 applies:
# concatenate, normalise, then keep one row per business key. Deduplication happens *after*
# normalisation, so `10` and `10%`, or `true` and `Y`, are compared as the same value rather than
# reported as a disagreement. Where the two sources give different non-missing values for the same
# key and field, the difference is recorded in the validation register rather than resolved by a
# silent source-precedence rule.
#
# **Two tables arrive from one file.** Customers exist only in the JSON and products only in the
# XML, so no cross-source comparison is possible for their fields. Saying so is the honest entry;
# within-source duplicates are still removed the same way.
#
# **Ten fields are computed.** They are derived after deduplication, from the canonical row, so
# they inherit the rule of the raw field they are computed from and are never compared across
# sources in their own right.
#
# Writing this column as a lookup on the table rather than as 111 sentences is deliberate: the
# rule genuinely is a property of the table, and 111 individually worded sentences would invite a
# reader to look for a distinction that does not exist.


# In[33]:

# --- Section 2.4: the overlap and conflict column ---

# Which files each output table is built from. Read from the parsed sets rather than declared,
# so a table that stopped arriving from one source would change this column.
SOURCES_OF = {t: ('both' if t in json_tables and t in xml_tables
                  else 'JSON' if t in json_tables else 'XML')
              for t in dd.output_table.unique()}
print('source of each table:', SOURCES_OF)

BOTH_RULE = (
    'Both files supply this table. Rows are concatenated, normalised, then reduced to one row '
    'per {key} with drop_duplicates(keep="first") — deduplication after normalisation, so a '
    'difference of source spelling is not read as a difference of value. A key whose two '
    'sources give different non-missing values for this field is recorded as a conflict in the '
    'validation register instead of being resolved by source precedence (Section 5, '
    'VAL-FLOW-09 to VAL-FLOW-12).')

SINGLE_RULE = (
    'This table is supplied by the {src} file only, so no cross-source overlap exists for this '
    'field and no precedence rule is needed. Within-source duplicates are removed by '
    'drop_duplicates({key}, keep="first") after normalisation (Section 5, VAL-FLOW-07).')

DERIVED_RULE = (
    'Computed after deduplication from the canonical row, so it is never compared across '
    'sources in its own right: it inherits the overlap rule of {feeder}, the raw field it is '
    'computed from (Section 5).')

KEY_OF = {'orders': 'order_id', 'order_items': 'order_item_id', 'customers': 'customer_id',
          'deliveries': 'delivery_id', 'products': 'product_id', 'product_reviews': 'review_id'}

rules = []
for _, r in MAPPING_PATHS.iterrows():
    table, key = r.output_table, KEY_OF[r.output_table]
    if r.source_format == 'derived':
        rules.append(DERIVED_RULE.format(feeder=DERIVED_SOURCE[r.target_field]))
    elif SOURCES_OF[table] == 'both':
        rules.append(BOTH_RULE.format(key=key))
    else:
        rules.append(SINGLE_RULE.format(src=SOURCES_OF[table], key=key))

MAPPING_PATHS['overlap_or_conflict_rule'] = rules
print()
print(MAPPING_PATHS.groupby([MAPPING_PATHS.output_table,
                             MAPPING_PATHS.overlap_or_conflict_rule.str.slice(0, 28)])
      .size().to_string())


# ### 2.5 Evidence, and the finished file
#
# `notebook_evidence` cites this notebook, by the section where the value is produced — one
# section per output table, plus Section 3.1 for the ten fields whose value comes out of a
# published function. Section numbers are used rather than cell headings because the numbering
# comes from the supplied template and is fixed for the life of the file.
#
# The checks below are the reason the mapping can be trusted: they re-read the written file and
# assert that it has one row per dictionary field in the dictionary's own order, that no
# placeholder survives in any column, that every row names a source or is derived from one, and
# that the ten computed rows are exactly the ten the path search found. If any of that stops
# being true, this cell fails rather than a marker noticing.


# In[34]:

# --- Section 2.5: evidence column, export, and the checks on the file ---
SECTION_OF = {'orders': '4.1', 'order_items': '4.2', 'customers': '4.3',
              'deliveries': '4.4', 'products': '4.5', 'product_reviews': '4.6'}

MAPPING_PATHS['notebook_evidence'] = [
    f'Section {SECTION_OF[r.output_table]} (functions Section 3.1)'
    if r.source_format == 'derived' else f'Section {SECTION_OF[r.output_table]}'
    for _, r in MAPPING_PATHS.iterrows()]

TEMPLATE_COLUMNS = ['mapping_id', 'output_table', 'target_field', 'source_format',
                    'json_source_path', 'xml_source_path', 'transformation_or_derivation',
                    'overlap_or_conflict_rule', 'notebook_evidence']

mapping_file = OUTPUT_DIR / f'{GROUP_ID}_source_to_target_mapping.csv'
MAPPING_PATHS[TEMPLATE_COLUMNS].to_csv(mapping_file, index=False,
                                       lineterminator=LINE_ENDING)

# Read the written file back and check it, rather than checking the frame in memory.
check = pd.read_csv(mapping_file, keep_default_na=False)

assert len(check) == len(dd), (len(check), len(dd))
assert list(check.columns) == TEMPLATE_COLUMNS
assert check.mapping_id.is_unique
assert (check.mapping_id.str.extract(r'-(\d+)$')[0].astype(int).values
        == dd.position.values).all(), 'row order no longer matches the dictionary'
assert list(zip(check.output_table, check.target_field)) == list(zip(dd.output_table, dd.field_name))

for col in ['source_format', 'transformation_or_derivation',
            'overlap_or_conflict_rule', 'notebook_evidence']:
    assert (check[col].str.strip() != '').all(), f'{col} has a blank cell'
    assert not check[col].str.contains('TODO', case=False).any(), f'{col} still has a placeholder'

pathless = check[(check.json_source_path == '') & (check.xml_source_path == '')]
assert pathless.empty, pathless[['mapping_id', 'target_field']]

print(f'{len(check)} rows, no blanks and no placeholders in any column')
print(check.groupby('source_format').size().to_string())
print('\nwritten to', mapping_file)
check.head(3)


# ## 3. Text and regex functions
#
# Implement and test the six required functions in
# `GroupNNN_text_functions.py`. Show public cases plus your own matched,
# unmatched, missing, multilingual and near-match cases here.


# ### 3.1 Cleaning and extraction implementation


# The six functions live in `Group001_text_functions.py` beside this notebook, because the
# specification requires them as an importable module with a fixed interface and no file or
# network access of its own. They are imported here rather than redefined, so the module the
# marker imports is the module this notebook used.
#
# Two ordering facts the rest of the notebook depends on. **Extraction runs on the raw value**,
# before cleaning removes the wrapper it looks for; the three measure and analysis fields run on
# the **cleaned** value. And every function returns the literal three-character string `NaN` for a
# missing result rather than `None` or a float NaN, so a missing value survives the round trip
# through CSV.


# In[35]:

# --- Section 3.1: import the published interface ---
TEXT_FN_CANDIDATES = [
    Path(f'{GROUP_ID}_text_functions.py'),          # beside this notebook, as submitted
    Path('..') / f'{GROUP_ID}_text_functions.py',
]
_hit = next((p for p in TEXT_FN_CANDIDATES if p.exists()), None)
assert _hit is not None, (
    f'{GROUP_ID}_text_functions.py not found. The module is part of the submission and '
    f'this notebook does not reimplement it. Tried: {TEXT_FN_CANDIDATES}')

sys.path.insert(0, str(_hit.resolve().parent))
from Group001_text_functions import (
    clean_narrative_text, extract_order_reference, extract_product_sku,
    extract_promo_code, build_latin_analysis, contains_non_latin_script,
)

TEXT_FUNCTIONS = [clean_narrative_text, extract_order_reference, extract_product_sku,
                  extract_promo_code, build_latin_analysis, contains_non_latin_script]
print('imported from', _hit)          # relative, so no personal path is stored in the output
for fn in TEXT_FUNCTIONS:
    print(f'   {fn.__name__:28s} {fn.__doc__.strip().splitlines()[0]}')


# ### 3.2 Public and student-designed tests


# Two files are run: the teaching team's public cases, and the group's own cases written in the
# same schema. The own cases were written to probe the five behaviours the public file does not
# cover in depth — a marker present, a marker absent, a missing input, a multilingual input, and
# a **near match** that must be rejected.
#
# The near-match group is the one worth reading. A reference is only a reference when it stands
# alone: `ORDER-HORD001451` embeds one but is not one, and a code written with non-ASCII digits
# looks right and is not. These cases change no value in this data set — every extraction below
# is identical with or without them — which is exactly why they have to be tested deliberately
# rather than discovered from the output.


# In[36]:

# --- Section 3.2: public and student-designed cases ---
import csv

def run_cases(path):
    """Run one test file in the published schema and report pass/fail per case."""
    failures = []
    with open(path, newline='', encoding='utf-8') as fh:
        cases = list(csv.DictReader(fh))
    for case in cases:
        fn = {f.__name__: f for f in TEXT_FUNCTIONS}[case['function']]
        actual = str(fn(case['input_value']))
        if actual != case['expected_output']:
            failures.append((case['case_id'], case['function'],
                             case['expected_output'], actual))
    print(f"{path.name:44s} {len(cases) - len(failures):>3} / {len(cases):<3} pass")
    for cid, fn, want, got in failures:
        print(f'   FAIL {cid} {fn}: expected {want!r}, got {got!r}')
    return len(cases), len(failures)

CASE_FILES = [Path('A1_public_text_test_cases.csv'),
              Path('templates/A1_public_text_test_cases.csv'),
              Path(f'{GROUP_ID}_own_text_test_cases.csv')]

total = failed = 0
for path in CASE_FILES:
    if path.exists():
        n, f = run_cases(path)
        total, failed = total + n, failed + f
assert total > 0, 'no test-case file found'
assert failed == 0, f'{failed} text-function cases failed'
print(f'\n{total} cases, {failed} failures')


# In[37]:

# --- Section 3.2: what the six functions do to one worked example ---
sample = ('[SYSTEM] Great <b>value</b>! Reference: HORD001451 / SKU: SKU-VES0042 '
          'PROMO: B1SAVE-66 &amp; fast delivery https://example.com #verified-buyer')

cleaned = clean_narrative_text(sample)
print('raw                       ', sample)
print('clean_narrative_text      ', cleaned)
print('extract_order_reference   ', extract_order_reference(sample))
print('extract_product_sku       ', extract_product_sku(sample))
print('extract_promo_code        ', extract_promo_code(sample))
print('build_latin_analysis      ', build_latin_analysis(cleaned))
print('contains_non_latin_script ', contains_non_latin_script(cleaned))

# The same, on a multilingual review: the body is preserved, the analysis field is not.
mixed = 'Excellent produit 这个产品很好 Reference: CORD004312'
mixed_clean = clean_narrative_text(mixed)
print('\nraw                       ', mixed)
print('clean_narrative_text      ', mixed_clean)
print('build_latin_analysis      ', build_latin_analysis(mixed_clean))
print('contains_non_latin_script ', contains_non_latin_script(mixed_clean))
print('extract_order_reference   ', extract_order_reference(mixed))

# A near match, rejected on purpose.
print('\nORDER-HORD001451 ->', extract_order_reference('ORDER-HORD001451'))


# ## 4. Build the six standardised relational tables
#
# Show the transformation and row-flow evidence for each table. Keep helper
# columns inside the workflow; export only fields in the public data dictionary.


#
# Building per source and unioning last fails *silently*. WP1 Section 1.3d shows why: JSON's reviews
# reference 1,813 `order_item_id` values JSON does not contain, and XML's reference 1,724 that XML
# does not. Neither export is referentially self-consistent, so every intermediate foreign-key
# check on a per-source table would fail and look like a transformation bug.
#
# No fan-out, no roll-up — source grain equals target grain for all six tables (WP1 Section 1.4). The only
# cross-table calculation is `order_price`, summing `line_revenue` from `order_items`.
#
# ### Three source cases
#
# | case | tables |
# |---|---|
# | both sources → concat, normalise, deduplicate | `orders`, `order_items`, `deliveries`, `product_reviews` |
# | JSON only | `customers` |
# | XML only | `products` |
# | not an output table — dropped | `warehouses` |
#
# **Cell order versus section numbering.** The headings follow the template's numbering verbatim
# (D4), but the cells are ordered by dependency: `4.1 orders` derives `order_price` from
# `4.2 order_items`, so 4.2 executes first. Restart and Run All is reproducible in this order; it
# would not be in numeric order.
#
# Build order was also chosen for cost: `order_items`, `deliveries` and `customers` carry no WP4
# dependency and were built first to prove the pipeline; `orders` and `product_reviews` came last
# because they carry nine of the ten derived text fields between them.


# ### 4.0 Target contract
#
# B1 is assessed on filenames, grains, fields **and field order**; B3 on types, nullability and the
# `NaN` sentinel. All of it is published in `public_data_dictionary.csv`, so the contract is *read*
# rather than transcribed — transcription is where silent field-order and dtype errors come from.
#
# The dictionary carries more than expected: `grain` per table, and a **`comparison_rule` per
# field**.
#
# >


# In[38]:

# --- Section 4.0 Read the published contract ---

# The dictionary was read once in Section 0.1; this cell only displays it.

print('shape  ', dd.shape)
print('columns', dd.columns.tolist())
print()
print(dd['output_table'].value_counts().to_string())
dd.head(12)


# In[39]:

# --- Section 4.0 Contract lookups ---
# Built once here so there is one reading of the dictionary, not six.

OUTPUT_TABLES = ['orders', 'order_items', 'customers', 'deliveries', 'products', 'product_reviews']

def contract(table):
    """The published contract for one output table, straight from the dictionary."""
    rows = dd.loc[dd['output_table'] == table].sort_values('position')
    return {
        'grain':      rows['grain'].iloc[0],
        'fields':     rows['field_name'].tolist(),                    # position order -> B1
        'pk':         rows.loc[rows['position'] == 1, 'field_name'].iloc[0],
        'dtype':      dict(zip(rows['field_name'], rows['data_type'])),
        'nullable':   dict(zip(rows['field_name'], rows['nullable'])),
        'comparison': dict(zip(rows['field_name'], rows['comparison_rule'])),
    }

CONTRACT = {t: contract(t) for t in OUTPUT_TABLES}

for t in OUTPUT_TABLES:
    c = CONTRACT[t]
    print(f"{t:16s} {len(c['fields']):>2} fields · pk = {c['pk']:<14s} · {c['grain']}")


# In[40]:

# --- Section 4.0 The target contract, table by table ---
# Read from the dictionary rather than transcribed: transcription is where silent
# field-order and dtype errors come from.

def show_contract(table):
    c = CONTRACT[table]
    print(f"\n{table}  —  {c['grain']}  ({len(c['fields'])} fields, pk = {c['pk']})")
    rows = dd.loc[dd['output_table'] == table].sort_values('position')
    print(rows[['position', 'field_name', 'data_type', 'nullable', 'comparison_rule']]
          .to_string(index=False))

for t in OUTPUT_TABLES:
    show_contract(t)


# **One thing the whole group needs to settle.** Every one of `product_reviews`' 21 fields is
# `nullable = False`, including four produced by text functions that return the literal `'NaN'`
# when there is nothing to extract: `review_body_clean`, `review_body_latin_analysis`,
# `extracted_order_reference`, `extracted_product_sku`.
#
# Two readings:
#
# - **A** — `nullable` means "the cell may be empty". `'NaN'` is three characters, so it is a
#   value, and any string field may carry it.
# - **B** — `nullable = True` marks the fields where the sentinel is permitted. Then
#   `nullable = False` is a claim that the field always resolves on this data.
#
# Evidence favours **B**: in `orders` the only two nullable fields are `coupon_code` and
# `promo_code` — exactly the two that can legitimately be absent. If `nullable` only meant
# non-empty there would be no reason to single those out.
#
# **B is testable.** Once WP4 ships, assert that no `nullable = False` field contains `'NaN'`.
# If one does, that is a genuine validation failure — which the rubric credits when it is
# identified and treated, and penalises only if a value is fabricated to hide it.
#
# >


# The plan derived from the dictionary is right for about 95% of fields. Two things it cannot
# know, corrected below from the report rather than guessed:
#
# - **derived fields have no source column** to normalise — `review_length_chars`,
#   `review_word_count` and `contains_non_latin_script` are produced by WP4, not read from a file;
# - **the dictionary has no `percent` type.** `coupon_discount` is `number` with an exact
#   comparison rule, but the XML writes `'10%'`. Source spelling is not a contract fact.
#
# >
# > Your `percent` category is necessary and cannot be derived — the dictionary describes the
# > target type, not how each file spells it. Worth saying so in that row's mapping text.
# >
# > `date` and `datetime` are separate `data_type` values and your map merges them. Parsing is the
# > same, but output formatting is not: five fields are `date` (`signup_date`, `dispatch_date`,
# > `promised_date`, `delivered_date`, `launch_date`, across three tables) and two are `datetime`
# > (`order_timestamp`, `review_timestamp`). Treating all seven as timestamps appends `00:00:00`
# > to the five, which B3 assesses. Section 4 follows the dictionary's two categories.
# >
# > Otherwise the plan I derived from the dictionary matches your hand-written map exactly — two
# > independent routes to the same answer.


# In[41]:

# --- Section 4.0 Derive the normalisation plan from the dictionary ---
# Money is not a data_type: the dictionary distinguishes it by comparison_rule, and date
# from datetime by data_type. Deriving the plan means it cannot drift from the contract.

MONEY_RULE = 'numeric tolerance 0.01'

def normalisation_plan(table):
    rows = dd.loc[dd['output_table'] == table]
    plan = {'money': [], 'number': [], 'date': [], 'datetime': [], 'boolean': []}
    for _, f in rows.iterrows():
        if f.data_type == 'number':
            plan['money' if f.comparison_rule == MONEY_RULE else 'number'].append(f.field_name)
        elif f.data_type in plan:
            plan[f.data_type].append(f.field_name)
    return {k: v for k, v in plan.items() if v}      # drop empty categories

PLAN = {t: normalisation_plan(t) for t in OUTPUT_TABLES}

for t in OUTPUT_TABLES:
    print(f'\n{t}')
    for kind, fields in PLAN[t].items():
        print(f'   {kind:9s} {fields}')


# In[42]:

# --- Section 4.0 Correct the derived plan ---
# Two things the dictionary cannot express, written from the output above rather than
# guessed: which fields have no source column, and which source spells a number with '%'.

SOURCE_COLUMNS = {}
for tabs in (json_tables, xml_tables):
    for name, df in tabs.items():
        SOURCE_COLUMNS.setdefault(name, set()).update(df.columns)

PERCENT_FIELDS = {'coupon_discount'}   # XML writes '10%'; the contract only says 'number'

for table, plan in PLAN.items():
    for kind in list(plan):
        plan[kind] = [f for f in plan[kind] if f in SOURCE_COLUMNS.get(table, set())]
    plan['percent'] = [f for f in plan.pop('number', []) if f in PERCENT_FIELDS] or []
    plan['number']  = [f for f in normalisation_plan(table).get('number', [])
                       if f in SOURCE_COLUMNS.get(table, set()) and f not in PERCENT_FIELDS]
    PLAN[table] = {k: v for k, v in plan.items() if v}

for t in OUTPUT_TABLES:
    print(f'\n{t}')
    for kind, fields in PLAN[t].items():
        print(f'   {kind:9s} {fields}')


# ### 4.0.1 Normalisers
#
# The parsers return source-native values by design, so every typed field needs converting before
# it can be compared, calculated with, or written out. XML is the heavy side: every value arrives
# as text. JSON is natively typed and needs only date parsing.
#
# Values stay typed through Section 4 — Timestamps, floats, bools — and are formatted to the published
# string forms only at export, in Section 7.
#
# XML strings compare lexicographically and give wrong answers *silently*:
# `'AUD 155.15' > 'AUD 1,827.30'` evaluates `True`, because `'5'` sorts after `','`. No sort,
# comparison or aggregation happens before this step.
#
# Booleans export as `True` / `False`, not `Y` / `N` or `1` / `0`. Stated as a
# convention rather than left as an observed fact: the dictionary says only
# `boolean`, and B3 assesses dtype conformance. The JSON writes `True` and the
# XML writes `Y` for the same fact, so this is also why comparison must happen
# after normalisation, not before.


# In[43]:

# --- Section 4.0.1 Normalisers ---
# Values stay typed through Section 4 (Timestamps, floats, bools) and are formatted to the
# published string forms only at export, in Section 7.

def norm_money(value):
    """'AUD 2,765.47' or 2765.47 -> 2765.47. The thousands comma appears on only some
    values, so it is stripped rather than matched."""
    return round(float(str(value).replace('AUD', '').replace(',', '').strip()), 2)

def norm_percent(value):
    """'10%' or 10 -> 10.0. Percentage points, so arithmetic divides by 100."""
    return float(str(value).replace('%', '').strip())

def norm_bool(value):
    """'Y' / 'N' / True / False -> bool. Anything unrecognised becomes False silently,
    so Section 6 should assert that no boolean source column is ever blank."""
    return str(value).strip().lower() in {'y', 'yes', 'true'}

def norm_temporal(series, dayfirst):
    """Vectorised: pd.to_datetime already accepts a Series. Calling it per element pays
    the parser start-up cost on every row — same result, ~100x slower."""
    return pd.to_datetime(series.astype(str).str.strip(), dayfirst=dayfirst, errors='coerce')

def normalise_frame(df, table, dayfirst):
    """Apply the derived plan to one source's frame."""
    plan = PLAN.get(table, {})
    out = df.copy()
    for kind, fields in plan.items():
        for f in fields:
            if kind == 'money':            out[f] = out[f].map(norm_money)
            elif kind == 'percent':        out[f] = out[f].map(norm_percent)
            elif kind == 'boolean':        out[f] = out[f].map(norm_bool)
            elif kind in ('date', 'datetime'):
                out[f] = norm_temporal(out[f], dayfirst)
            elif kind == 'number':         out[f] = pd.to_numeric(out[f], errors='coerce')
    return out


# In[44]:

# --- Section 4.0.1 Sanity check: normalise one table from both sources ---
# order_items is the smallest table with no derived fields, so it is the cheapest place
# to confirm the plan works before applying it to all six.

j = normalise_frame(json_tables['order_items'], 'order_items', dayfirst=False)
x = normalise_frame(xml_tables['order_items'],  'order_items', dayfirst=True)

print('dtypes after normalisation')
print(pd.DataFrame({'JSON': j.dtypes, 'XML': x.dtypes}).to_string())

print('\nsame row, both sources')
sid = sorted(set(j.order_item_id) & set(x.order_item_id))[0]
print(pd.DataFrame({
    'JSON': j.loc[j.order_item_id == sid].iloc[0],
    'XML':  x.loc[x.order_item_id == sid].iloc[0],
}).to_string())


# ### 4.0.2 Combine and deduplicate
#
# Deduplication handles **both** duplicate problems in one step: within-source repeats and
# cross-source overlap. That is legitimate only because of two WP1 findings — within-source
# duplicates are exactly two field-identical copies (A3), and shared keys agree on every field
# once normalised (A5). The surviving row therefore depends on neither which copy nor which
# source wins.
#
# Expected row counts are **derived**, never written in. The specification forbids hard-coded
# canonical counts and rubric E1's Fail descriptor names them.
#
# >
# > **Still waiting on you:** after this step the 500 shared orders are one row tagged
# > `source_system = "JSON"`, so "appeared in both files" is gone before Section 5 sees the tables.
# > Overlap key sets handed over pre-dedup, or a `"both"` marker?


# `source_system` records provenance so Section 5 can report source coverage and
# VAL-FLOW-12 can assert the overlap. It is a **helper column**: it never reaches
# the exported CSVs, because `conform_to_contract` selects the dictionary's
# fields rather than dropping by name, and the dictionary does not contain it.
# VAL-SCHEMA-08 asserts its absence downstream.
#
# **Order matters.** The marker is written *before* deduplication. `keep='first'`
# retains the JSON copy of a shared key, whose `source_system` is `JSON`, so
# marking afterwards would lose the very fact the column exists to record.
#
# Marking first also keeps both copies of a duplicated key field-identical —
# within-source pairs are both `JSON`, cross-source pairs are both `both` — so
# the field-identity evidence behind still holds with the column present.


# In[45]:

# --- Section 4.0.2 Pipeline helpers ---

BOTH_SOURCES = ['orders', 'order_items', 'deliveries', 'product_reviews']
JSON_ONLY    = ['customers']
XML_ONLY     = ['products']
NOT_AN_OUTPUT_TABLE = ['warehouses']

def combine_sources(table):
    """Normalise each source, then concatenate. Normalising first is required
    because `dayfirst` differs between the two files."""
    parts = []
    if table in json_tables:
        parts.append(normalise_frame(json_tables[table], table, dayfirst=False)
                     .assign(source_system='JSON'))
    if table in xml_tables and table not in NOT_AN_OUTPUT_TABLE:
        parts.append(normalise_frame(xml_tables[table], table, dayfirst=True)
                     .assign(source_system='XML'))
    return pd.concat(parts, ignore_index=True)

def mark_overlap(df, table):
    """Rewrite source_system to 'both' for keys carried by both sources.
    Must run before deduplication: keep='first' retains the JSON copy, so
    marking afterwards would lose the overlap fact."""
    key = CONTRACT[table]['pk']
    shared = df.groupby(key)['source_system'].transform('nunique') > 1
    out = df.copy()
    out.loc[shared, 'source_system'] = 'both'
    return out

def expected_canonical_rows(table):
    """Derived, never written in: the union of business keys across the sources."""
    key = CONTRACT[table]['pk']
    keys = set()
    for tabs in (json_tables, xml_tables):
        if table in tabs and table not in NOT_AN_OUTPUT_TABLE:
            keys |= set(tabs[table][key].astype(str))
    return len(keys)

def deduplicate(df, table):
    """One row per business key. Safe because within-source duplicates are
    field-identical (A3) and shared keys agree once normalised (A5)."""
    key = CONTRACT[table]['pk']
    out = df.drop_duplicates(subset=key, keep='first').reset_index(drop=True)

    assert len(out) == expected_canonical_rows(table), table
    assert out[key].is_unique
    assert out[key].notna().all() and (out[key].astype(str) != '').all()
    return out


# In[46]:

# --- Section 4.0.2 Pipeline helpers, continued ---

def conform_to_contract(df, table):
    """Select the published fields in `position` order. Helper columns never survive
    this step — selection is what drops `source_system`."""
    fields = CONTRACT[table]['fields']
    missing = [f for f in fields if f not in df.columns]
    assert not missing, (table, 'missing fields', missing)

    out = df[fields].copy()
    assert list(out.columns) == fields          # B1 field order
    return out

def row_flow(table, combined, final):
    """The before/after evidence the template's Section 4 and rubric E1 both ask for."""
    per_source = {s: len(t[table]) for s, t in (('JSON', json_tables), ('XML', xml_tables))
                  if table in t}
    parts = ' + '.join(f'{s} {n:,}' for s, n in per_source.items())
    print(f'{table}')
    print(f'   sources   {parts} = {sum(per_source.values()):,} concatenated')
    print(f'   canonical {len(final):,} rows x {final.shape[1]} columns'
          f'   ({sum(per_source.values()) - len(final):,} removed)')


# ### 4.0.3 Money rounding and tolerance
#
# Two things that look like detail and are not.
#
# **`pandas .round(2)` and Python's `round()` disagree.** pandas rounds the scaled float
# half-to-even; Python rounds the decimal value of the float. They part company on `.xx5`
# boundaries — raw totals like `365.96500000000003`, `11687.645`, `2715.6749999999997`. Measured
# on the JSON side: Python's `round()` reproduces the source exactly, 2,750 / 2,750; pandas
# `.round(2)` reproduces 2,705 / 2,750, with the other 45 out by one cent.
#
# The source was generated with Python's rounding, so Section 4 uses `money_round()` everywhere a
# monetary value is rounded. Element-wise is acceptable at this scale — thousands of rows, not
# the hundreds of thousands where the datetime parser needed vectorising.
#
# **Tolerance means `<=`, not `<`.** The dictionary publishes `numeric tolerance 0.01` for
# monetary fields, so a difference of exactly one cent is *inside* tolerance. Writing the check as
# `gap > 0.01` reports 23 false failures, because float arithmetic makes a difference of exactly
# 0.01 evaluate as greater than 0.01. `np.isclose(a, b, rtol=0, atol=0.01)` is the correct form.
#
# >


# In[47]:

# --- Section 4.0.3 Money rounding ---
# pandas .round(2) rounds the scaled float half-to-even; Python's round() rounds the
# decimal value of the float. They disagree on .xx5 boundaries, and the source was
# generated with Python's. Element-wise is fine at this scale (thousands of rows).

def money_round(series):
    return series.map(lambda v: round(v, 2))

TOLERANCE = 0.01
def within_tolerance(a, b, atol=TOLERANCE):
    """Tolerance means |a - b| <= atol. Float noise makes a strict > unreliable at the
    boundary, so np.isclose is used rather than a hand-written comparison."""
    import numpy as np
    return np.isclose(a, b, rtol=0, atol=atol, equal_nan=True)


# ### 4.0.4 The order the tables are built in
#
# Section numbers follow the template — 4.1 is `orders`, 4.2 is `order_items` — but the cells run
# in dependency order, and `order_items` is built first. The reason is in the specification's own
# definition of the arithmetic: `order_price` is the sum of that order's line revenues, so it can
# only be rebuilt once the canonical `order_items` rows exist. Copying the source value instead
# would remove the one check that makes the whole monetary chain meaningful.
#
# The other four tables are independent of each other and follow in numeric order.


# ### 4.2 `order_items`
#
# Six fields, no naming exceptions, no WP4 dependency — built first because it is the cheapest
# place to prove the pipeline before the harder tables use it.
#
# `line_revenue` is the only derived field: `round(quantity × unit_price, 2)`.
#
# The duplicate rows here are a *consequence* of the order duplication — 68 duplicated orders
# carry their whole cart a second time — so the counts removed from `order_items`, `orders` and
# `deliveries` move together. That relationship is a free consistency check.


# In[48]:

# --- Section 4.2 order_items ---

TABLE = 'order_items'

combined = mark_overlap(combine_sources(TABLE), TABLE)
deduped  = deduplicate(combined, TABLE)

print(f'{TABLE}')
print(f'   JSON {len(json_tables[TABLE]):,} + XML {len(xml_tables[TABLE]):,}'
      f' = {len(combined):,} concatenated')
print(f'   deduped {len(deduped):,}  ({len(combined) - len(deduped):,} removed)')

deduped.head()


# `line_revenue` is the only derived field in this table. The source carries a value for it, but
# the pipeline **recomputes** it from `quantity` and `unit_price` rather than copying — the
# specification prescribes the formula, and recomputing is what makes the arithmetic checkable.
#
# Recomputing also gives a free reconciliation: the recomputed column should match the source
# column within the published tolerance for every row. A mismatch would be a real finding.


# In[49]:

# --- Section 4.2 line_revenue: recompute and reconcile ---

recomputed = (deduped['quantity'] * deduped['unit_price']).round(2)
gap = (recomputed - deduped['line_revenue']).abs()

print(f'rows                     {len(deduped):,}')
print(f'outside tolerance 0.01   {int((gap > 0.01).sum()):,}')
print(f'largest difference       {gap.max():.4f}')

deduped['line_revenue'] = recomputed


# In[50]:

# --- Section 4.2 order_items: conform and report ---

order_items_marked = deduped
order_items_final  = conform_to_contract(order_items_marked, TABLE)
row_flow(TABLE, combined, order_items_final)

order_items_final.head()


# ### 4.1 `orders`
#
# The heaviest table. Three things happen here that happen nowhere else.
#
# **The arithmetic chain, in this order.** Verified against all 2,818 rows of both sources.
#
# ```
# line_revenue = round(quantity × unit_price, 2)          # Section 4.2, per item
# order_price  = round(Σ line_revenue, 2)                 # summed from order_items
# tax_amount   = round(order_price / 11, 2)               # BEFORE the discount
# order_total  = round(order_price × (1 − coupon_discount/100) + delivery_charges, 2)
# ```
#
# **A real finding, and what it was.** The first run of this section reported 40 rows where the
# recomputed `order_total` differed from the source. `order_price` and `tax_amount` matched
# exactly, which narrowed it to the last step. Two causes, both in the checking rather than the
# data: `.round(2)` disagreeing with the source's rounding on `.xx5` boundaries, and a strict `>`
# comparison rejecting differences of exactly one cent that the published tolerance permits. Both
# are fixed in Section 4.0.3. No row of source data was wrong.
#
# Worth recording rather than quietly correcting: a check that fires is only useful if what it
# found is written down.


#
# Three ways to get this wrong:
#
# - **`coupon_discount` is a percentage, not a dollar amount.** Reading it as dollars reproduces
#   only 640 of 2,818 order totals — and those 640 are exactly the rows where the discount is 0,
#   so the error hides in plain sight.
# - **`tax_amount` is computed before the discount and never added to `order_total`.**
# - **Use Python's built-in `round()`.** It reproduces the source exactly, 2,818/2,818. `Decimal`
#   with `ROUND_HALF_UP` matches 2,758 exactly and the other 60 differ by 0.01 — inside tolerance,
#   so both are defensible, but one needs no explanation.
#
# `order_price` is the only calculation that crosses tables. It does not change either table's
# grain: `order_items` stays one row per item, `orders` stays one row per order.


# In[51]:

# --- Section 4.1 orders: combine, deduplicate, rebuild the arithmetic ---

TABLE = 'orders'

combined = mark_overlap(combine_sources(TABLE), TABLE)
deduped  = deduplicate(combined, TABLE)

# order_price is the sum of the canonical line revenues, so it is rebuilt from Section 4.2's output
# rather than copied. Every order must have at least one item for this to be complete.
line_totals = order_items_final.groupby('order_id')['line_revenue'].sum().round(2)
assert deduped['order_id'].isin(line_totals.index).all(), 'orders with no items'

rebuilt = pd.DataFrame({'order_price': deduped['order_id'].map(line_totals)})
rebuilt['tax_amount']  = money_round(rebuilt['order_price'] / 11)
rebuilt['order_total'] = money_round(rebuilt['order_price'] * (1 - deduped['coupon_discount'] / 100)
                                     + deduped['delivery_charges'])

print(f'{TABLE}: recomputed vs source, tolerance {TOLERANCE}')
for f in ['order_price', 'tax_amount', 'order_total']:
    ok = within_tolerance(rebuilt[f], deduped[f])
    gap = (rebuilt[f] - deduped[f]).abs()
    print(f'   {f:14s} outside tolerance {int((~ok).sum()):>5,}   max diff {gap.max():.4f}')

for f in rebuilt.columns:
    deduped[f] = rebuilt[f]


# In[52]:

# --- Section 4.1 orders: derived text fields, sentinels, conform ---

# Two target fields come from one raw column via WP4. Provisional while the banner shows.
deduped['customer_note_clean'] = deduped['customer_note_raw'].map(clean_narrative_text)
deduped['promo_code']          = deduped['customer_note_raw'].map(extract_promo_code)

# The two nullable string fields in this table. The sentinel is the three characters 'NaN',
# so it is filled explicitly — .astype(str) would give lowercase 'nan' on pandas 2.x.
# coupon_code is a real source column - blanks become the literal sentinel.
cc = deduped['coupon_code']
deduped['coupon_code'] = cc.where(cc.notna() & (cc != ''), 'NaN')

orders_marked = deduped
orders_final  = conform_to_contract(orders_marked, TABLE)
row_flow(TABLE, combined, orders_final)

print(f"\n   coupon_code == 'NaN'  {int((orders_final['coupon_code'] == 'NaN').sum()):,} rows")
print(f"   promo_code  == 'NaN'  {int((orders_final['promo_code']  == 'NaN').sum()):,} rows")

orders_final.head()


# ### 4.3 `customers`
#
# JSON only — no cross-source reconciliation. The deduplication step stays in the pipeline
# anyway: its absence would be a gap in method, and its presence removing zero rows is evidence.


# In[53]:

# --- Section 4.3 customers ---

TABLE = 'customers'

combined = mark_overlap(combine_sources(TABLE), TABLE)
deduped  = deduplicate(combined, TABLE)
customers_marked = deduped
customers_final  = conform_to_contract(customers_marked, TABLE)

row_flow(TABLE, combined, customers_final)

# home_postcode is pure digits, so pandas would infer an integer on read-back.
# The six identifiers carry alpha prefixes and raise instead.
print(f"\n   home_postcode dtype  {customers_final['home_postcode'].dtype}")

customers_final.head()


# ### 4.4 `deliveries`
#
# Second, because it exercises three things `order_items` did not: `date` fields, `boolean`
# fields, and the grain filter.
#
# **Grain: one row per completed order.** Strictly 1:1 with `orders` — after deduplication both
# tables have the same row count and `order_id` is unique in each.
#
# **The `completed` filter is a no-op on this package.** `order_status` and `delivery_status` are
# 100% `Completed` / `Delivered` across both files, so the filter removes zero rows. It is still
# written, because the grain rule is part of the method and a reviewer needs to see it applied.
#
# >
#
# `delay_days` is `max(0, delivered_date − promised_date)`, not the raw difference —
# early arrivals record `0`, never a negative. Verified 5,000 of 5,000. A check written as the raw difference
# reports 2,985 false mismatches.
# `delivered_date` extends past 31 December 2018 — 76 deliveries, latest
# 2019-01-12 — for orders placed late in the period. A temporal range check
# therefore constrains `order_timestamp` only; written on `delivered_date` it
# would report 76 false failures.


# In[54]:

# --- Section 4.4 deliveries ---

TABLE = 'deliveries'

combined = mark_overlap(combine_sources(TABLE), TABLE)
deduped  = deduplicate(combined, TABLE)

deliveries_marked = deduped
deliveries_final  = conform_to_contract(deliveries_marked, TABLE)

row_flow(TABLE, combined, deliveries_final)

# 1:1 with orders — same count, and order_id unique in both.
print(f"\n   order_id unique      {deliveries_final['order_id'].is_unique}")
print(f"   delay_reason 'none'  {int((deliveries_final['delay_reason'] == 'none').sum()):,} rows")

# Not cleaned, and the evidence is that cleaning would damage it: the column
# holds two structured values, and clean_narrative_text alters all 5,000 rows
# by letter case alone.
notes = deliveries_final['delivery_note_clean']
print(f'delivery_note_clean: {notes.nunique()} distinct values')
print(notes.value_counts().to_string())

deliveries_final.head()


# ### 4.5 `products`
#
# XML only, and the most format-heavy table: every value arrives as text, so all eight typed
# fields need converting — money with a conditional thousands comma, `DD/MM/YYYY` dates, `Y`/`N`
# booleans.
#
# This is the table WP1's hand-written `NORMALISERS` originally missed, because it appears in only
# one source and so never showed up in the cross-source comparison the map was written for.
#
# `product_description_clean` comes from `product_description_raw` via WP4. All 1,000 descriptions
# carry a `[CATALOGUE]` marker and HTML tags, so this field stays provisional until G2.


# In[55]:

# --- Section 4.5 products ---

TABLE = 'products'

combined = mark_overlap(combine_sources(TABLE), TABLE)
deduped  = deduplicate(combined, TABLE)

# Every typed field arrived as a string. Confirm the conversion actually happened.
print('dtypes after normalisation')
for kind, fields in PLAN[TABLE].items():
    for f in fields:
        print(f'   {kind:9s} {f:24s} {deduped[f].dtype}')

deduped.head()


# In[56]:

# --- Section 4.5 products: derived field and conform ---

# product_description_clean comes from WP4. Provisional while the placeholder banner shows.
deduped['product_description_clean'] = deduped['product_description_raw'].map(clean_narrative_text)

products_marked = deduped
products_final  = conform_to_contract(products_marked, TABLE)
row_flow(TABLE, combined, products_final)

products_final.head()


# ### 4.6 `product_reviews`
#
# Built last: seven of its 21 fields are derived and every one depends on WP4.
#
# **The derivation order matters.** Three of the seven come from the raw text, four come from the
# *cleaned* text — the specification is explicit that the Latin analysis and the counts are built
# from `review_body_clean`, not from the raw value.
#
# | target field | derived from |
# |---|---|
# | `review_body_clean` | `review_body_raw` |
# | `extracted_order_reference`, `extracted_product_sku` | `review_body_raw` |
# | `review_body_latin_analysis` | `review_body_clean` |
# | `review_length_chars`, `review_word_count` | `review_body_clean` |
# | `contains_non_latin_script` | `review_body_clean` |
#
# Four foreign keys — `order_id`, `order_item_id`, `product_id`, `customer_id` — more than any
# other table. `order_item_id` is unique across the canonical reviews, so the relationship to
# `order_items` is 1:1 and no order item is reviewed twice. Joining the two cannot multiply rows.
#
# `review_title` is a direct copy. WP1 checked all 7,892 and none contain markup, markers, URLs,
# entities or uppercase — that count is the evidence for not cleaning it.
#
# >
#
# **Sentinel handling in the two review measures.** When `review_body_clean` is the
# literal `NaN`, `str.len()` returns 3 and `str.split()` returns 1 — the three
# letters counted as an ordinary review, which the specification forbids.
#
# No row in this package is affected: nothing cleans to the sentinel. The guard is
# here for a private test case or a re-run on different data, where a silent 3 and
# 1 would be indistinguishable from a real short review.
#
# The value is derived, not chosen: the dictionary types both fields as `number`
# with `nullable = False`, so the sentinel cannot propagate into them, and the
# length of absent text is 0.
#
# Both fields carry this rule in the mapping, and it is worth one clause in each row
# saying the measures are taken on the cleaned body and that the sentinel maps to 0.


# In[57]:

# --- Section 4.6 product_reviews ---

TABLE = 'product_reviews'

combined = mark_overlap(combine_sources(TABLE), TABLE)
deduped  = deduplicate(combined, TABLE)

# From the raw text.
deduped['review_body_clean']         = deduped['review_body_raw'].map(clean_narrative_text)
deduped['extracted_order_reference'] = deduped['review_body_raw'].map(extract_order_reference)
deduped['extracted_product_sku']     = deduped['review_body_raw'].map(extract_product_sku)

# From the cleaned text, not the raw value.
clean = deduped['review_body_clean']
deduped['review_body_latin_analysis'] = clean.map(build_latin_analysis)
deduped['contains_non_latin_script']  = clean.map(contains_non_latin_script)

# The sentinel is not an ordinary review: str.len() would return 3 and
# str.split() 1. Both fields are typed number / nullable False, so 0.
is_sentinel = clean.eq('NaN')
deduped['review_length_chars']       = clean.str.len().mask(is_sentinel, 0)
deduped['review_word_count']         = clean.str.split().str.len().mask(is_sentinel, 0)

product_reviews_marked = deduped
product_reviews_final  = conform_to_contract(product_reviews_marked, TABLE)
row_flow(TABLE, combined, product_reviews_final)

product_reviews_final.head()


# #### 4.7 No column is silently empty
#
# A column that is entirely the sentinel means a source column was lost or a derivation never
# ran. Nothing crashes and no row count changes, so this is the only check that would find it.


# In[58]:

# With the published functions in use, no column may be entirely the sentinel.
expected = set()

dead = {(name, c)
        for name in OUTPUT_TABLES
        for df in [globals()[f'{name}_final']]
        for c in df.columns if (df[c].astype(str) == 'NaN').all()}

assert dead == expected, f'unexpected all-sentinel columns: {dead ^ expected}'
print(f'{len(dead)} all-sentinel columns across the six tables')


# ## 5. Reconcile overlap and verify relationships
#
# Demonstrate how records are compared by stable business key, how canonical
# rows are retained and how silent source-precedence choices are avoided.


# Three questions, in the order they have to be answered.
#
# **Are the two copies of a duplicated key the same record?** Within each file some business keys
# appear twice. Every such pair is compared field by field before anything is discarded, so
# "deduplicate" is a claim this section supports rather than assumes.
#
# **Do the two files agree where they overlap?** A key carried by both files is compared *after*
# normalisation, never before: the XML writes `AUD 155.15`, `Y` and day-first dates where the JSON
# writes native types, and comparing first would report format as disagreement. Any key and field
# where the two sources give different non-missing values is collected and reported, not silently
# resolved.
#
# **Which copy is kept, and does it matter?** `drop_duplicates(keep="first")` on a frame with the
# JSON rows first keeps the JSON copy. That is a choice and it is written down here rather than
# left implicit — and the conflict count below is what says whether the choice can change any
# value.
#
# The comparison needs the frame *before* deduplication, which no exported file carries, so it is
# rebuilt here from the normalised sources.


# In[59]:

# --- Section 5: rebuild the pre-deduplication frames and compare the sources ---

def find_conflicts(combined, key):
    """Keys where the two sources give different non-missing values for the same field.

    `combined` is the concatenation of the two normalised sources, before deduplication,
    carrying a `source_system` column.
    """
    shared = combined[combined.duplicated(key, keep=False)]
    found = []
    for field in shared.columns.drop([key, 'source_system']):
        distinct = shared.groupby(key)[field].nunique(dropna=True)
        for k in distinct[distinct > 1].index:
            found.append({'key': k, 'field': field})
    return pd.DataFrame(found, columns=['key', 'field'])

def count_overlap(combined, key):
    """How many business keys came from both files.

    Distinct keys, not marked rows: within-source duplicates would make a row count
    read 513 orders where 500 keys are shared.
    """
    return combined.loc[combined.source_system == 'both', key].nunique()

PRE_DEDUP = {t: mark_overlap(combine_sources(t), t) for t in BOTH_SOURCES}
PRE_DEDUP.update({t: mark_overlap(combine_sources(t), t) for t in JSON_ONLY + XML_ONLY})

CONFLICTS, OVERLAP, WITHIN = {}, {}, {}
for t in OUTPUT_TABLES:
    key = CONTRACT[t]['pk']
    frame = PRE_DEDUP[t]
    CONFLICTS[t] = find_conflicts(frame, key)
    OVERLAP[t]   = count_overlap(frame, key) if t in BOTH_SOURCES else 0
    # Within-source duplicates: the same key twice inside ONE file. Counted on the
    # parsed sources, not on the combined frame — after mark_overlap a shared key reads
    # as 'both' and a filter on source_system would count cross-source pairs as well.
    WITHIN[t] = {src: int(len(tabs[t]) - tabs[t][key].nunique())
                 for src, tabs in (('JSON', json_tables), ('XML', xml_tables)) if t in tabs}

print(f"{'table':16s} {'rows in':>8} {'canonical':>10} {'within-source dups':>20} "
      f"{'shared keys':>12} {'conflicts':>10}")
for t in OUTPUT_TABLES:
    dups = ' + '.join(f'{s} {n}' for s, n in WITHIN[t].items())
    print(f'{t:16s} {len(PRE_DEDUP[t]):>8,} {len(globals()[t + "_final"]):>10,} '
          f'{dups:>20} {OVERLAP[t]:>12,} {len(CONFLICTS[t]):>10,}')

print('\nPrecedence: rows are concatenated JSON first and drop_duplicates keeps the first '
      'copy,\nso the JSON copy is retained wherever a key appears in both files. The conflict '
      'count\nabove is what decides whether that choice can change any exported value.')


# #### 5.1 The detector, shown working
#
# Zero conflicts and a detector that never fires produce the same output, so the difference has to
# be demonstrated rather than asserted. The cell below plants a disagreement in a four-row frame
# of the same shape, finds it, repairs it and finds nothing — and does the same for the
# deduplication rule, by comparing the two copies of every genuinely duplicated key in the real
# files.


# In[60]:

# --- Section 5.1: negative control for the conflict detector ---
fixture = pd.DataFrame({
    'order_id':      ['A1', 'A1', 'B2', 'B2'],
    'order_total':   ['100.00', '100.00', '250.00', '999.00'],   # B2 disagrees
    'currency':      ['AUD', 'AUD', 'AUD', 'AUD'],
    'source_system': ['JSON', 'XML', 'JSON', 'XML'],
})
planted  = find_conflicts(fixture, 'order_id')
repaired = fixture.copy()
repaired.loc[3, 'order_total'] = '250.00'
clean    = find_conflicts(repaired, 'order_id')

print('planted conflict found :', planted.to_dict('records'))
print('same frame, repaired   :', len(clean), 'conflicts')
assert len(planted) == 1 and len(clean) == 0

# The deduplication rule rests on the two copies of a duplicated key being field-identical
# INSIDE one file. Checked on the parsed sources, one file at a time, not assumed.
print()
WITHIN_DIFFS = 0
for t in OUTPUT_TABLES:
    key = CONTRACT[t]['pk']
    for src, tabs in (('JSON', json_tables), ('XML', xml_tables)):
        if t not in tabs:
            continue
        frame = normalise_frame(tabs[t], t, dayfirst=(src == 'XML')).assign(source_system=src)
        repeated = frame[frame[key].duplicated(keep=False)]
        if repeated.empty:
            continue
        differing = find_conflicts(repeated, key)
        WITHIN_DIFFS += len(differing)
        print(f'{t:16s} {src:5s} {repeated[key].nunique():>4} keys appear twice, '
              f'{len(differing)} field differences between the two copies')
print()
print(f'{WITHIN_DIFFS} field differences in total, so keeping either copy gives the '
      f'same canonical row.')


# ## 6. Validation register
#
# Keep each check executable and give it a stable `VAL-...` ID. Immediately after
# each code check, record the observed result, `PASS`/`FAIL`, evidence and
# resolution/interpretation. A genuine, explained failure is preferable to a
# fabricated pass.
#
# Required areas include schema/types, primary and foreign keys, row flow and
# source coverage, overlap, arithmetic, temporal logic, text/reference behaviour
# and multilingual handling.


# **Three rules that apply to every check below.**
#
# 1. **Compare after normalising, never before.** The XML writes money as `AUD 155.15`, booleans as
#    `Y`, and dates as day-first; the JSON uses native types. Comparing before normalising reports
#    format differences as conflicts that do not exist.
# 2. **Work out the expected number in the same cell that checks it.** Nothing is typed in by hand.
#    Writing `assert len(orders) == 5000` loses the mark; working out the same 5,000 from the two
#    files and then checking it keeps it.
# 3. **Say which source wins, do not leave it unsaid.** Deduplication puts the JSON rows first and
#    keeps the first copy, so JSON wins. The values agree either way, so the choice changes nothing
#    — but it is still a choice, and C2 marks whether we wrote it down.
#
# **Primary keys**: `orders.order_id` · `order_items.order_item_id` ·
# `customers.customer_id` · `deliveries.delivery_id` · `products.product_id` ·
# `product_reviews.review_id`.


# ### 6.0 What the checks read
#
# The register checks the **serialised** form of each table, not the frames in memory, because
# that is what the marker receives: dates as the published strings, booleans as `True`/`False`,
# and the missing-value sentinel as the three characters `NaN`. Each table is written to an
# in-memory buffer with exactly the formatting Section 7 uses and read back with
# `keep_default_na=False`, so a formatting fault is caught here rather than after export.
#
# Expected numbers are worked out from the raw files in the same cell that checks them. An
# assertion against a number typed in by hand proves only that the number was typed correctly.


# In[61]:

# --- Section 6.0: the register's inputs and helpers ---

def format_for_export(df, table):
    """Timestamps to the published string forms. `date` and `datetime` differ."""
    out = df.copy()
    plan = PLAN.get(table, {})
    for f in plan.get('date', []):
        out[f] = out[f].dt.strftime('%Y-%m-%d')
    for f in plan.get('datetime', []):
        out[f] = out[f].dt.strftime('%Y-%m-%d %H:%M:%S')
    return out

def as_written(table):
    """The table exactly as Section 7 will write it, read back as text."""
    buf = StringIO()
    format_for_export(globals()[f'{table}_final'], table).to_csv(
        buf, index=False, lineterminator=LINE_ENDING)
    buf.seek(0)
    return pd.read_csv(buf, keep_default_na=False, dtype=str)

TABLES = OUTPUT_TABLES                      # the register refers to the six by name
T = {t: as_written(t) for t in OUTPUT_TABLES}
PK = {t: CONTRACT[t]['pk'] for t in OUTPUT_TABLES}

# The raw documents, for working out expected numbers independently of Section 4.
jdata, xroot = raw_json, root

same_number = within_tolerance             # one tolerance rule for the whole notebook

RESULTS = []

def record(val_id, passed, evidence, note=''):
    """One check: its ID, its status, what was seen, and what it means.

    `passed` may be True, False, or None for a check that cannot run in this notebook.
    A gap that is named is worth more than a pass that was manufactured.
    """
    status = 'NOT RUN' if passed is None else ('PASS' if passed else 'FAIL')
    RESULTS.append({'id': val_id, 'status': status, 'evidence': evidence, 'note': note})
    print(f'{val_id:18s} {status:7s} {evidence}')

for t in OUTPUT_TABLES:
    print(f'{t:16s} {len(T[t]):>7,} rows x {T[t].shape[1]:>2} cols, read back as text')


# ### 6.1 Schema and type checks (`VAL-SCHEMA-...`)
#
# Does each table have the right columns, in the right order, with the right type? The data
# dictionary says what each table should look like. If this is wrong, nothing after it means
# anything, so it runs first.
#
# | ID | What it checks | Table | Passes when | If it fails |
# |---|---|---|---|---|
# | VAL-SCHEMA-01 | Columns match the dictionary: same names, same order, same types | orders | exact match | Wrong columns break B1's field-order mark and every later join |
# | VAL-SCHEMA-02 | Same check | order_items | exact match | as above |
# | VAL-SCHEMA-03 | Same check | customers | exact match | as above |
# | VAL-SCHEMA-04 | Same check | deliveries | exact match | as above |
# | VAL-SCHEMA-05 | Same check | products | exact match | as above |
# | VAL-SCHEMA-06 | Same check | product_reviews | exact match | as above |
# | VAL-SCHEMA-07 | IDs and `home_postcode` are still text, with leading zeros kept | all six | all text | `home_postcode` is all digits, so pandas turns it into a number without warning and the zero is lost |
# | VAL-SCHEMA-08 | No helper column reached the file — no `source_system`, no `_raw` | all six | none found | An internal column shipped in the submitted file |
# | VAL-SCHEMA-09 | Dates are written the published way: `YYYY-MM-DD` for dates, `YYYY-MM-DD HH:MM:SS` for timestamps | all dated tables | exact match | A date field with a time on the end breaks the dictionary |
# | VAL-SCHEMA-10 | Columns marked `nullable = False` have no empty cells | all six | no empty cells | A required field is blank |
# | VAL-SCHEMA-11 | The six files have the required names, including `_standardised` | output folder | all six present | B1's top band starts with "present with the required filenames" |
#
# **A note on `nullable = False`.** All 21 `product_reviews` columns are marked `nullable = False`,
# but the spec also says missing text must be written as `NaN`. Both cannot be true at once, so
# VAL-SCHEMA-10 reads `nullable = False` as *no empty cell*, not *no `NaN`*. Every table passes it
# today. Worth a `DEC-` row either way, because the check is written differently under each
# reading.


# In[62]:

# --- Section 6.1 checks ---
# The dictionary says what each table should look like. We compare against it,
# never against a list typed in by hand.

for name, df in T.items():
    want = dd[dd.output_table == name].sort_values("position")["field_name"].tolist()
    got  = list(df.columns)
    record(f"VAL-SCHEMA-{name}", got == want,
           f"{len(got)} columns, order matches the dictionary" if got == want
           else f"got {got[:3]}..., wanted {want[:3]}...")

# VAL-SCHEMA-07 — IDs and postcode must stay text with leading zeros.
# home_postcode is the risky one: it is all digits, so pandas converts it silently.
pc = T["customers"]["home_postcode"]
record("VAL-SCHEMA-07", pc.str.fullmatch(r"\d{4}").all(),
       f"home_postcode is 4-character text on every row ({pc.min()}..{pc.max()})")

# VAL-SCHEMA-08 — no helper column should reach the exported file.
leaked = [f"{n}.{c}" for n, df in T.items() for c in df.columns
          if c == "source_system" or c.endswith("_raw")]
record("VAL-SCHEMA-08", not leaked, f"helper columns found: {leaked or 'none'}")

# VAL-SCHEMA-09 — dates written the published way.
DATE   = r"\d{4}-\d{2}-\d{2}"
STAMP  = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
date_fields  = [("customers","signup_date"), ("deliveries","dispatch_date"),
                ("deliveries","promised_date"), ("deliveries","delivered_date"),
                ("products","launch_date")]
stamp_fields = [("orders","order_timestamp"), ("product_reviews","review_timestamp")]
bad = [f"{n}.{c}" for n, c in date_fields  if not T[n][c].str.fullmatch(DATE).all()]
bad += [f"{n}.{c}" for n, c in stamp_fields if not T[n][c].str.fullmatch(STAMP).all()]
record("VAL-SCHEMA-09", not bad, f"wrongly formatted date fields: {bad or 'none'}")

# VAL-SCHEMA-10 — nullable=False means no empty cell (see the note above).
empties = {f"{n}.{c}": int((T[n][c] == "").sum())
           for n in T
           for c in dd[(dd.output_table == n) & (dd.nullable == False)].field_name
           if (T[n][c] == "").any()}
record("VAL-SCHEMA-10", not empties, f"empty cells in nullable=False fields: {empties or 'none'}")

# VAL-SCHEMA-11 — the six files carry the required names.
# The names Section 7 will write, checked against the names the dictionary requires.
wanted = {f"{GROUP_ID}_{n}_standardised.csv" for n in dd.output_table.unique()}
planned = {f"{GROUP_ID}_{n}_standardised.csv" for n in T}
record("VAL-SCHEMA-11", wanted == planned,
       f"{len(wanted & planned)} of {len(wanted)} required filenames will be written; "
       f"missing {sorted(wanted - planned) or 'none'}, unexpected {sorted(planned - wanted) or 'none'}")


# **Observed result / status / interpretation.** All six field sets match the dictionary in
# name, order and count. `home_postcode` survives as four-character text, so the one column that
# pandas would convert without warning did not. No helper column reached any file, which is the
# evidence that `conform_to_contract` still strips the overlap marker WP2 adds before export. No
# `nullable = False` field holds an empty cell anywhere — that is what makes the reading proposed
# above checkable rather than rhetorical, since every absent value is the literal sentinel instead.
#
# **What would have made this section fail.** A renamed or reordered column, a postcode read as a
# number, `source_system` surviving into a CSV, or a date written with a time appended. The
# planted a blank `order_id` in a copy of the data and VAL-SCHEMA-10 caught it, so the section is
# sensitive rather than merely quiet.


# ### 6.2 Primary- and foreign-key checks (`VAL-PK-...`, `VAL-FK-...`)
#
# A **primary key** is the column that names each row. It has to be unique and never empty.
# A **foreign key** is a column pointing at another table's primary key — it has to point at a row
# that exists.
#
# | ID | What it checks | Table | Passes when | If it fails |
# |---|---|---|---|---|
# | VAL-PK-01 | `order_id` is unique and never empty | orders | unique, no blanks | Two rows share a name, so every foreign key pointing here is unreliable |
# | VAL-PK-02 | `order_item_id` is unique and never empty | order_items | unique, no blanks | as above |
# | VAL-PK-03 | `customer_id` is unique and never empty | customers | unique, no blanks | as above |
# | VAL-PK-04 | `delivery_id` is unique and never empty | deliveries | unique, no blanks | as above |
# | VAL-PK-05 | `product_id` is unique and never empty | products | unique, no blanks | as above |
# | VAL-PK-06 | `review_id` is unique and never empty | product_reviews | unique, no blanks | as above |
#
# The eight foreign keys the spec asks for. These are checked on the **exported files**, not on the
# sources — Section 1.3d already showed the sources are sound, but that is a different claim from the one
# B1 and C2 mark.
#
# | ID | Points from | Points to | Passes when | If it fails |
# |---|---|---|---|---|
# | VAL-FK-01 | `orders.customer_id` | `customers.customer_id` | nothing unmatched | An order belongs to a customer who does not exist |
# | VAL-FK-02 | `order_items.order_id` | `orders.order_id` | nothing unmatched | An item belongs to no order, so revenue totals are wrong |
# | VAL-FK-03 | `order_items.product_id` | `products.product_id` | nothing unmatched | An item points at a product not in the catalogue |
# | VAL-FK-04 | `deliveries.order_id` | `orders.order_id` | nothing unmatched | A delivery exists for no order |
# | VAL-FK-05 | `product_reviews.order_id` | `orders.order_id` | nothing unmatched | A review belongs to no order |
# | VAL-FK-06 | `product_reviews.order_item_id` | `order_items.order_item_id` | nothing unmatched | A review belongs to no item |
# | VAL-FK-07 | `product_reviews.product_id` | `products.product_id` | nothing unmatched | A review points at a missing product |
# | VAL-FK-08 | `product_reviews.customer_id` | `customers.customer_id` | nothing unmatched | A review belongs to an unknown customer |
#
# | ID | What it checks | Tables | Passes when | If it fails |
# |---|---|---|---|---|
# | VAL-FK-09 | `deliveries` has one row per order — same row count, `order_id` unique in both | deliveries, orders | 1:1 | The dictionary says one row per completed order delivery; if it is not 1:1, any join here multiplies rows |


# In[63]:

# --- Section 6.2 checks ---
PK = {"orders": "order_id", "order_items": "order_item_id", "customers": "customer_id",
      "deliveries": "delivery_id", "products": "product_id", "product_reviews": "review_id"}

for name, key in PK.items():
    col = T[name][key]
    ok = col.is_unique and (col != "").all()
    record(f"VAL-PK-{name}", ok,
           f"{col.nunique():,} different values in {len(col):,} rows, {int((col=='').sum())} blank")

# The eight foreign keys the spec lists, checked on the exported files.
FK = [("VAL-FK-01", "orders", "customer_id", "customers", "customer_id"),
      ("VAL-FK-02", "order_items", "order_id", "orders", "order_id"),
      ("VAL-FK-03", "order_items", "product_id", "products", "product_id"),
      ("VAL-FK-04", "deliveries", "order_id", "orders", "order_id"),
      ("VAL-FK-05", "product_reviews", "order_id", "orders", "order_id"),
      ("VAL-FK-06", "product_reviews", "order_item_id", "order_items", "order_item_id"),
      ("VAL-FK-07", "product_reviews", "product_id", "products", "product_id"),
      ("VAL-FK-08", "product_reviews", "customer_id", "customers", "customer_id")]

for vid, child_t, child_c, parent_t, parent_c in FK:
    child, parent = set(T[child_t][child_c]), set(T[parent_t][parent_c])
    missing = child - parent
    record(vid, not missing,
           f"{child_t}.{child_c} -> {parent_t}.{parent_c}: "
           f"{len(missing)} unmatched of {len(child):,} different values")

# VAL-FK-09 — deliveries must be one row per order, or any join here multiplies rows.
d = T["deliveries"]
record("VAL-FK-09", len(d) == d.order_id.nunique() == len(T["orders"]),
       f"deliveries {len(d):,} rows, {d.order_id.nunique():,} different order_id, "
       f"orders {len(T['orders']):,} rows")


# **Observed result / status / interpretation.** All six primary keys are unique and complete,
# and all eight required foreign keys resolve with nothing unmatched **on the exported files**.
# That last part matters: Section 1.3d showed the source union is referentially sound, which is a
# different claim from the one B1 and C2 assess. `deliveries` is confirmed one row per order, so
# no delivery-side join can multiply rows.
#
# **What would have made this section fail.** A duplicate or blank key, an orphan line item, a
# review pointing at an order that is not there, or `deliveries` holding more than one row per
# order.


# ### 6.3 Source coverage and reconciliation checks (`VAL-FLOW-...`)
#
# Did the right number of rows come through, and can each row be traced back to a source? This is
# the reconciliation part of WP3.
#
# | ID | What it checks | Table | Passes when | If it fails |
# |---|---|---|---|---|
# | VAL-FLOW-01 | Row count equals the number of different `order_id` in the two files put together, worked out in the same cell | orders | exact match | Deduplication dropped rows or kept too many |
# | VAL-FLOW-02 | Same, on `order_item_id` | order_items | exact match | as above |
# | VAL-FLOW-03 | Same, on `customer_id` (JSON is the only source) | customers | exact match | as above |
# | VAL-FLOW-04 | Same, on `delivery_id` | deliveries | exact match | as above |
# | VAL-FLOW-05 | Same, on `product_id` (XML is the only source) | products | exact match | as above |
# | VAL-FLOW-06 | Same, on `review_id` | product_reviews | exact match | as above |
# | VAL-FLOW-07 | The rows removed by deduplication match the count worked out from each raw file | all affected | exact match | Deduplication removed too much or too little |
# | VAL-FLOW-08 | Every exported row can be traced back to at least one source row | all six | none untraced | A row exists that no source produced |
# | VAL-FLOW-09 | For orders in **both** files, every shared column agrees **after normalising**. Any disagreement is written down with its key and column, not dropped | orders, order_items, deliveries, product_reviews | no conflicts | A real conflict exists, and Section 4 needs a rule about which source wins instead of a free choice |
# | VAL-FLOW-10 | Repeated keys inside one file are two identical copies, so keeping the first cannot change a value | affected tables | identical copies | Keeping the first is no longer safe to justify |
# | VAL-FLOW-11 | The conflict detector is tested on a small made-up table with a conflict planted in it, then run on the real data | test fixture, then real | fires on the fixture, quiet on the real data | "We found no conflicts" and "our detector never works" look identical without this |
# | VAL-FLOW-12 | The `both` marker survives deduplication: `source_system` is `JSON`, `XML` or `both` on `<table>_marked`, and the `both` set matches the overlap worked out again from the two key sets | shared tables, before export | marker matches | We lose track of which rows came from both files, right where Section 5 needs it. Note the marker must **not** reach the CSVs — VAL-SCHEMA-08 checks that |
# | VAL-FLOW-13 | No column is entirely `NaN` | all six | none | A column that is all sentinel means a real source column was lost upstream. Nothing crashes and no row count changes, so only this check finds it |
# | VAL-FLOW-14 | Items per order stay inside the limit worked out from the source, not a number typed in | order_items | within the limit | A limit written as 1–10 could never fire, because the 10 came from duplicates |
# | VAL-FLOW-15 | Joining `order_items` to `orders` gives the item row count, and no order total is worked out on the joined table | orders, order_items | join size matches | An order total worked out after the join is multiplied by the number of items. WP2 avoids this by grouping first; F1 asks for the check by name, and avoiding is not the same as showing |


# In[64]:

# --- Section 6.3 checks ---
# Every expected number below is worked out from the raw files in this cell.
# Nothing is typed in.

j_ord  = {o["header"]["orderID"] for o in jdata["orders"]}
x_ord  = {o.find("Header").find("Order_ID").text.strip() for o in xroot.iter("Order")}
j_item = {i["orderItemID"] for o in jdata["orders"] for i in o["shoppingCart"]}
x_item = {i.find("Order_Item_ID").text.strip() for i in xroot.iter("Item")}
j_cust = {c["customerID"] for c in jdata["customerProfiles"]}
j_del  = {o["delivery"]["deliveryID"] for o in jdata["orders"]}
x_del  = {e.find("Delivery_ID").text.strip() for e in xroot.iter("Delivery")}
x_prod = {p.find("Product_ID").text.strip() for p in xroot.iter("Product")}
j_rev  = {r["reviewID"] for r in jdata["productReviews"]}
x_rev  = {r.find("Review_ID").text.strip() for r in xroot.iter("Review")}

EXPECTED = {"orders": j_ord | x_ord, "order_items": j_item | x_item,
            "customers": j_cust, "deliveries": j_del | x_del,
            "products": x_prod, "product_reviews": j_rev | x_rev}

for i, (name, keys) in enumerate(EXPECTED.items(), start=1):
    record(f"VAL-FLOW-{i:02d}", len(T[name]) == len(keys),
           f"{name} has {len(T[name]):,} rows; the two files together hold {len(keys):,} different keys")

# VAL-FLOW-07 — how many rows deduplication removed, worked out per source.
raw_json_orders = [o["header"]["orderID"] for o in jdata["orders"]]
raw_xml_orders  = [o.find("Header").find("Order_ID").text.strip() for o in xroot.iter("Order")]
removed_json = len(raw_json_orders) - len(set(raw_json_orders))
removed_xml  = len(raw_xml_orders)  - len(set(raw_xml_orders))
record("VAL-FLOW-07", removed_json == removed_xml,
       f"deduplication removes {removed_json} rows from the JSON and {removed_xml} from the XML")

# VAL-FLOW-08 — every exported row traces back to a source row.
untraced = {n: len(set(T[n][PK[n]]) - keys) for n, keys in EXPECTED.items()}
record("VAL-FLOW-08", not any(untraced.values()),
       f"rows with no source: {untraced}")

# VAL-FLOW-13 — a column that is entirely NaN means a real source column was lost.
# Nothing crashes and no row count changes, so only this check finds it.
all_nan = [f"{n}.{c}" for n, df in T.items() for c in df.columns if (df[c] == "NaN").all()]
record("VAL-FLOW-13", not all_nan, f"columns that are entirely NaN: {all_nan or 'none'}")

# VAL-FLOW-14 — the limit comes from the source, not from a number we chose.
biggest_cart = max(len(o["shoppingCart"]) for o in jdata["orders"])
per_order = T["order_items"].groupby("order_id").size()
record("VAL-FLOW-14", per_order.max() == biggest_cart,
       f"items per order run {per_order.min()} to {per_order.max()}; "
       f"the biggest cart in the source holds {biggest_cart}")

# VAL-FLOW-15 — show the join multiplication instead of only avoiding it.
joined = T["order_items"].merge(T["orders"][["order_id"]], on="order_id")
record("VAL-FLOW-15", len(joined) == len(T["order_items"]),
       f"the join gives {len(joined):,} rows, the same as order_items; that is "
       f"{len(joined)/len(T['orders']):.2f} times the {len(T['orders']):,} orders, which is what "
       f"an order total worked out after the join would be multiplied by")

# VAL-FLOW-09 to -12 — the cross-source checks. In a personal notebook these could not
# run: they need the frame from before deduplication, which no exported file carries.
# Section 5 rebuilds it, so they are recorded here rather than deferred.

total_conflicts = sum(len(c) for c in CONFLICTS.values())
compared_keys   = sum(int(PRE_DEDUP[t].duplicated(CONTRACT[t]['pk'], keep=False).sum())
                      for t in OUTPUT_TABLES)
record("VAL-FLOW-09", total_conflicts == 0,
       f"{compared_keys:,} rows carry a key that appears more than once; "
       f"{total_conflicts} field disagreements after normalising, across all six tables")

# VAL-FLOW-10 — the two copies of a within-source duplicate must be field-identical,
# which is what makes drop_duplicates(keep='first') safe rather than lossy.
record("VAL-FLOW-10", WITHIN_DIFFS == 0,
       f"within-source repeated keys {({t: WITHIN[t] for t in OUTPUT_TABLES})}; "
       f"{WITHIN_DIFFS} field differences between the two copies of any of them")

# VAL-FLOW-11 — the negative control from Section 5.1. A detector that never fires and
# data with nothing to find produce the same output, so the detector is shown working.
record("VAL-FLOW-11", len(planted) == 1 and len(clean) == 0,
       f"planted conflict detected: {planted.to_dict('records')}; "
       f"same frame with the conflict repaired: {len(clean)} conflicts")

# VAL-FLOW-12 — how many keys came from both files, against the raw key sets.
expected_shared = {"orders": len(j_ord & x_ord), "order_items": len(j_item & x_item),
                   "deliveries": len(j_del & x_del), "product_reviews": len(j_rev & x_rev)}
observed_shared = {t: OVERLAP[t] for t in expected_shared}
record("VAL-FLOW-12", observed_shared == expected_shared,
       f"keys carried by both files {observed_shared}; the raw key sets intersect at "
       f"{expected_shared}")


# **Observed result / status / interpretation.** Every row count equals the union of business
# keys derived from the raw files in the same cell, and no exported row lacks a source. Items per
# order run within a bound taken from the source rather than from a number we chose, so the check
# cannot inherit the 1–10 duplication artefact.
#
# Two checks here earn their place beyond the counting. **VAL-FLOW-13** has a real result rather
# than a formal one: before WP4 landed, three columns were entirely sentinel, and WP2 reported a
# fault of exactly the kind this catches — Section 4.1 called the extractor and then overwrote the column
# with a leftover placeholder. That raises nothing and changes no row count; an all-sentinel column
# is the only symptom. **VAL-FLOW-15** measures the join fan-out rather than only avoiding it: the
# join returns the item row count, 3.14× the order count, which is the factor by which an
# order-level total computed after the join would be inflated.
#
# VAL-FLOW-09, -10 and -12 are **not run here**, and are not counted as passes. They compare the
# two sources row by row and need the combined frame from before deduplication, which exists only
# in the master. The detector is written and unit-tested above so assembly wires it up rather than
# invents it.
#
# **What would have made this section fail.** A row count that disagrees with the union, an
# exported row with no source, a fourth all-sentinel column, or a join that returns more rows than
# `order_items` holds.


# ### 6.4 Arithmetic checks (`VAL-ARITH-...`)
#
# Work the money out again and see if it matches. All of these use `money_round()` and
# `same_number()` from Section 0.2.
#
# | ID | What it checks | Table | Passes when | If it fails |
# |---|---|---|---|---|
# | VAL-ARITH-01 | `line_revenue` = quantity × unit price | order_items | within 0.01 | Line money is wrong, and every total built on it is wrong too |
# | VAL-ARITH-02 | `order_price` = the sum of that order's line revenues | orders, order_items | within 0.01 | The order total does not match the lines it is made of |
# | VAL-ARITH-03 | `order_total` = order price − discount + delivery. Tax is reported on its own and never added | orders | within 0.01 | Reading the discount as dollars instead of a percentage only reproduces the rows where the discount is zero |
# | VAL-ARITH-04 | `tax_amount` = order price ÷ 11, worked out before the discount | orders | within 0.01 | The price already includes GST, so dividing by 11 pulls the tax back out. Multiplying by 0.1 would charge it twice |
# | VAL-ARITH-05 | `coupon_discount` only holds values seen in this package | orders | all known | A percentage has been read as an amount, or an unexpected value crept in |
# | VAL-ARITH-06 | `delay_days` = delivered date − promised date, but never below zero | deliveries | exact match | Early deliveries record 0, not a negative number. The plain difference does not reproduce the column |
# | VAL-ARITH-07 | `review_length_chars` and `review_word_count` are counted from `review_body_clean` | product_reviews | exact match | The counts were taken from the messy raw text instead of the cleaned text |


# In[65]:

# --- Section 6.4 checks ---
oi = T["order_items"]
qty   = pd.to_numeric(oi.quantity)
price = pd.to_numeric(oi.unit_price)
line  = pd.to_numeric(oi.line_revenue)

# VAL-ARITH-01 — line revenue is quantity times unit price.
diff = ~same_number(line, money_round(qty * price))
record("VAL-ARITH-01", not diff.any(),
       f"{int(diff.sum())} of {len(oi):,} rows are more than 0.01 out")

o = T["orders"]
order_price = pd.to_numeric(o.order_price)
discount    = pd.to_numeric(o.coupon_discount)
delivery    = pd.to_numeric(o.delivery_charges)
total       = pd.to_numeric(o.order_total)
tax         = pd.to_numeric(o.tax_amount)

# VAL-ARITH-02 — order price is the sum of that order's line revenues.
per_order = money_round(pd.DataFrame({"oid": oi.order_id, "line": money_round(qty * price)})
                        .groupby("oid").line.sum())
lookup = o.set_index("order_id").order_price.astype(float)
diff = ~same_number(lookup, per_order.reindex(lookup.index))
record("VAL-ARITH-02", not diff.any(),
       f"{int(diff.sum())} of {len(o):,} orders are more than 0.01 out")

# VAL-ARITH-03 — the discount is a percentage, and tax is never added on top.
diff = ~same_number(total, money_round(order_price * (1 - discount / 100) + delivery))
record("VAL-ARITH-03", not diff.any(),
       f"{int(diff.sum())} of {len(o):,} orders are more than 0.01 out")

# VAL-ARITH-04 — the price already includes GST, so dividing by 11 pulls the tax back out.
diff = ~same_number(tax, money_round(order_price / 11))
record("VAL-ARITH-04", not diff.any(),
       f"{int(diff.sum())} of {len(o):,} orders are more than 0.01 out")

# VAL-ARITH-05 — the allowed set comes from the raw files, not from a list we chose.
# The earlier version passed unconditionally, which meant it could never fail.
raw_discounts = {float(src["header"]["couponDiscount"]) for src in jdata["orders"]}
for header in xroot.iter("Header"):
    node = header.find("Coupon_Discount")
    if node is not None and node.text:
        raw_discounts.add(float(node.text.replace("%", "").strip()))

seen = set(discount.unique())
record("VAL-ARITH-05", seen <= raw_discounts,
       f"export holds {sorted(int(v) for v in seen)}; the raw files hold "
       f"{sorted(int(v) for v in raw_discounts)}; unexpected values: "
       f"{sorted(seen - raw_discounts) or 'none'}")

# VAL-ARITH-08 — sensible numeric ranges. The specification asks for these
# alongside the allowed-value checks, and the register had none.
rv = T["product_reviews"]
rating = pd.to_numeric(rv.rating)
votes = pd.to_numeric(rv.helpful_votes)
money_columns = {
    "orders.order_price": order_price, "orders.order_total": total,
    "orders.delivery_charges": delivery, "orders.tax_amount": tax,
    "order_items.unit_price": price, "order_items.line_revenue": line,
}
out_of_range = {
    "rating outside 1-5": int(((rating < 1) | (rating > 5)).sum()),
    "quantity below 1": int((qty < 1).sum()),
    "helpful_votes negative": int((votes < 0).sum()),
    "negative money": sum(int((v < 0).sum()) for v in money_columns.values()),
}
record("VAL-ARITH-08", not any(out_of_range.values()),
       f"rating {rating.min()}-{rating.max()}, quantity from {qty.min()}, "
       f"helpful_votes from {votes.min()}, no negative money; violations {out_of_range}")

# Negative control for VAL-ARITH-04. The tax check only means something if the
# wrong formula fails. Adding GST on top instead of dividing it out should match
# almost nothing.
wrong_tax = money_round(order_price * 1.1 + delivery)
n_wrong = int(same_number(total, wrong_tax).sum())
print(f"{'(control)':18s} INFO  adding GST on top instead of dividing it out reproduces "
      f"{n_wrong:,} of {len(o):,} order totals — the correct formula reproduces "
      f"{int(same_number(total, money_round(order_price * (1 - discount / 100) + delivery)).sum()):,}")

# VAL-ARITH-06 — an early delivery records 0, not a negative number.
dl = T["deliveries"].copy()
for col in ["promised_date", "delivered_date"]:
    dl[col] = pd.to_datetime(dl[col])
gap = (dl.delivered_date - dl.promised_date).dt.days.clip(lower=0)
match = pd.to_numeric(dl.delay_days) == gap
record("VAL-ARITH-06", match.all(),
       f"{int(match.sum()):,} of {len(dl):,} rows match max(0, delivered - promised)")

# VAL-ARITH-07 — the counts come from the cleaned review, not the raw one.
body = rv.review_body_clean
chars_ok = (pd.to_numeric(rv.review_length_chars) == body.str.len()).all()
words_ok = (pd.to_numeric(rv.review_word_count) == body.str.split().str.len()).all()
record("VAL-ARITH-07", chars_ok and words_ok,
       f"character counts match: {chars_ok}; word counts match: {words_ok}")


# **Observed result / status / interpretation.** Every monetary chain reconciles with no row
# outside the published 0.01 tolerance, and `delay_days` matches `max(0, delivered − promised)` on
# every row — the plain difference does not reproduce the column, because an early arrival records
# zero rather than a negative.
#
# These pass because they take two conventions from WP2 Section 4.0.3 rather than the obvious
# implementations. Rounding uses Python's `round()`, not pandas `.round(2)`; comparison uses
# `np.isclose(rtol=0, atol=0.01)`, not a hand-written `>`. Written the obvious way, the same data
# reports 40 failures on `order_total`, none of which is a defect.
#
# **The negative control is what makes VAL-ARITH-04 mean anything.** Adding GST on top instead of
# dividing it out reproduces essentially none of the 5,000 totals, while the correct formula
# reproduces all of them. Without that contrast, a passing tax check would be indistinguishable
# from a check that cannot fail.
#
# **What would have made this section fail.** A discount read as dollars — which would still
# reproduce the zero-discount rows and so hide in plain sight — GST added rather than divided out,
# a coupon value absent from the sources, a rating outside 1–5, or negative money.


# ### 6.5 Temporal checks (`VAL-TIME-...`)
#
# Do the dates make sense in the order things actually happen?
#
# | ID | What it checks | Table | Passes when | If it fails |
# |---|---|---|---|---|
# | VAL-TIME-01 | Order time ≤ dispatch date ≤ delivered date | orders, deliveries | no breaks | An impossible order of events, which usually means a date was read with the day and month swapped |
# | VAL-TIME-02 | A review is not written before its order exists | product_reviews, orders | no breaks | The review points at an order that had not happened yet |
# | VAL-TIME-03 | Every date reads cleanly under its own file's format — day-first for XML, ISO for JSON — with no dates turning into empty values | all dated tables | no empty dates | A wrong `dayfirst` setting turns dates into blanks quietly, and every date comparison after that is wrong |
# | VAL-TIME-04 | Every `order_timestamp` falls inside 2018 | orders | all inside | A row from outside the period got in, or a date was read wrongly |
#
# **One check we deliberately do not write.** We do **not** check that delivery happened before the
# promised date. Some deliveries are late, and those rows have a `delay_days` and a `delay_reason`
# filled in (`warehouse_congestion`, `carrier_capacity`, `weather`). Late delivery is how the
# business went, not a data problem, so checking it would mark normal orders as failures. The
# late rate belongs in the EDA instead.
#
# For the same reason VAL-TIME-04 only looks at `order_timestamp`. Delivery dates run into January
# 2019 for orders placed at the very end of the year, which is fine.


# In[66]:

# --- Section 6.5 checks ---
dl = T["deliveries"].copy()
for col in ["dispatch_date", "promised_date", "delivered_date"]:
    dl[col] = pd.to_datetime(dl[col])

order_time = pd.Series(pd.to_datetime(T["orders"].order_timestamp).values,
                       index=T["orders"].order_id.values)
dl["ordered"] = dl.order_id.map(order_time)

# VAL-TIME-01 — order, then dispatch, then delivery. This one is always true.
late_dispatch = int((dl.ordered.dt.normalize() > dl.dispatch_date).sum())
late_delivery = int((dl.dispatch_date > dl.delivered_date).sum())
record("VAL-TIME-01", late_dispatch + late_delivery == 0,
       f"dispatched before ordered: {late_dispatch}; delivered before dispatched: {late_delivery}")

# VAL-TIME-02 — a review cannot exist before its order.
rv = T["product_reviews"]
written = pd.to_datetime(rv.review_timestamp)
ordered = rv.order_id.map(order_time)
early = int((written < ordered).sum())
record("VAL-TIME-02", early == 0, f"{early} reviews are dated before their order")

# VAL-TIME-03 — a wrong dayfirst setting turns dates into blanks quietly.
blanks = sum(int(dl[c].isna().sum()) for c in ["dispatch_date", "promised_date", "delivered_date"])
blanks += int(written.isna().sum())
record("VAL-TIME-03", blanks == 0, f"{blanks} dates turned into blanks while being read")

# VAL-TIME-04 — only order_timestamp is held to 2018. Deliveries for orders placed
# at the end of December legitimately land in January 2019.
years = sorted(pd.to_datetime(T["orders"].order_timestamp).dt.year.unique())
record("VAL-TIME-04", years == [2018], f"order_timestamp years present: {years}")

# For context, not a check: how many deliveries were late.
print(f"{'(context)':18s} INFO  {int((dl.delivered_date > dl.promised_date).sum()):,} "
      f"deliveries arrived after the promised date — a business outcome, not a data problem")


# **Observed result / status / interpretation.** The chain `order ≤ dispatch ≤ delivered` holds
# with no exceptions, no review predates its order, and no date turned into a blank while being
# read — which is the evidence that both `dayfirst` conventions were applied to the right file.
#
# **One check deliberately absent.** We do not assert that delivery beat the promised date. 528
# deliveries were late, and those rows carry a populated `delay_days` and `delay_reason`
# (`warehouse_congestion`, `carrier_capacity`, `weather`). That is a business outcome, not a data
# defect; asserting it would report normal operations as failures, and the rate belongs in the EDA
# instead. For the same reason VAL-TIME-04 constrains `order_timestamp` alone — delivery dates run
# into January 2019 for orders placed at the very end of the period, which is correct.
#
# **What would have made this section fail.** A delivery before its dispatch, a review before its
# order, a silent `NaT` from the wrong `dayfirst`, or an order stamped outside 2018.


# ### 6.6 Text and multilingual checks (`VAL-TEXT-...`)
#
# Was the text cleaned properly, and does the multilingual handling work? These check WP4's output.
#
# | ID | What it checks | Table | Passes when | If it fails |
# |---|---|---|---|---|
# | VAL-TEXT-01 | The three narrative `_clean` fields have no HTML tags, markers, URLs or emoji left, and are all lower case | orders, products, product_reviews | none left | Cleaning failed and the mess reached the file |
# | VAL-TEXT-01b | `delivery_note_clean` keeps the source's own capitals — it is a fixed category, not free text | deliveries | source spelling kept | Task 2 says not to lower-case a fixed category unless a rule says so, and no rule names this field. The `_clean` in the name is the source system's naming, not an instruction |
# | VAL-TEXT-02 | Bracketed wording that is not on the published marker list survives cleaning | orders, product_reviews | kept | A rule that removes every bracket also removes real customer wording (test case TXT-18) |
# | VAL-TEXT-03 | `extracted_order_reference` is `[HC]ORD` plus exactly six digits, or the text `NaN` | product_reviews | all match | The pattern matches too much, and a wrong reference goes out looking valid |
# | VAL-TEXT-04 | `extracted_product_sku` is `SKU-` plus letters or digits, or `NaN`. A broken SKU is rejected, not cut down to a valid start | product_reviews | all match | A broken SKU is exported as a good one (test case TXT-12) |
# | VAL-TEXT-05 | `promo_code` is `B[1-5]SAVE-` plus two digits, or `NaN` | orders | all match | An invalid code goes out looking valid |
# | VAL-TEXT-06 | The codes were pulled out of the **raw** text, not the cleaned text | orders, product_reviews | codes present | Cleaning deletes the reference, SKU and promo strings, so pulling them out afterwards returns `NaN` on every row |
# | VAL-TEXT-07 | `review_body_latin_analysis` keeps Latin letters including accents, turns non-Latin **letters** into spaces, leaves everything that is not a letter alone, and is `NaN` when no Latin letter is left. The check reports what survived **by character type**, so the rule is visible rather than assumed | product_reviews | no non-Latin letters; the sentinel fires whenever no Latin letter remains | Accents were dropped as if foreign, or the sentinel was not applied |
# | VAL-TEXT-08 | `contains_non_latin_script` is `True` exactly when the cleaned review has a non-Latin letter | product_reviews | flag matches text | The flag and the text disagree. Note Polish, German and French use Latin letters with accents and must stay `False` — this is where a simple ASCII test goes wrong |
# | VAL-TEXT-09 | `delay_reason` keeps `'none'` as a real value and no cleaning step turns it into `NaN` | deliveries | kept | A real value on thousands of rows is destroyed |
# | VAL-TEXT-10 | Three fields hold one value only — `order_status`, `delivery_status`, `verified_purchase` — so Section 4's "completed" filter removes no rows, and this is written down as expected | orders, deliveries, product_reviews | noted | A filter that removes nothing is read as broken, or a real filter is quietly missing. None of the three can carry an EDA figure either |
# | VAL-TEXT-12 | `coupon_code` is `B[1-5]SAVE-` plus two digits on every filled row | orders | all match | The shape VAL-TEXT-13 relies on is not what we think it is |
# | VAL-TEXT-13 | Where a row has both `coupon_code` and `promo_code`, they agree — and no row has one without the other | orders | agree, none one-sided | See the note below |
# | VAL-TEXT-14 | `extracted_order_reference` equals that row's own `order_id` | product_reviews | agree | The pattern matched a different order's reference inside the review |
# | VAL-TEXT-15 | `extracted_product_sku` equals `products.product_sku` for that row's `product_id` | product_reviews, products | agree | Same idea as VAL-TEXT-14, checked through the foreign key |
#
# **Why VAL-TEXT-13, -14 and -15 matter more than the rest.** Every other text check tests a
# pattern against its own output — if the pattern is wrong, the check is wrong in the same way and
# still passes. These three compare a value pulled out of free text against a value that got into
# the table by a completely different route: a structured source column, the review's own
# `order_id`, and the product catalogue. They are the only checks here that can tell a
# right-looking wrong answer from a right one.
#
# **What "Latin-script" means here, settled against the implementation.**
# `Group001_text_functions.py` keeps a character when it is **not a letter**, or when its Unicode
# name contains `LATIN`. So non-Latin *letters* become spaces, while digits, spaces and punctuation
# stay — including CJK punctuation such as `。` and `，`, and the combining vowel marks used in
# Devanagari and Arabic. That is the second of the two readings the spec allows: *remove non-Latin
# letters*, not *keep only Latin letters*.
#
# I checked the case this raises. If punctuation survives, could a review that is entirely
# non-Latin end up as punctuation instead of the sentinel? No — the sentinel is decided by
# "is there a Latin letter left", not by "is the text empty":
#
# ```
# build_latin_analysis("包装很好")    ->  "NaN"
# build_latin_analysis("包装很好。")  ->  "NaN"      punctuation left, still NaN
# build_latin_analysis("。，、")      ->  "NaN"
# ```
#
# All 18 published test cases pass, TXT-07 and TXT-09 among them. VAL-TEXT-07 therefore asserts
# zero non-Latin *letters* and reports the other character types as evidence of the rule, rather
# than treating them as a fault.


# In[67]:

# --- Section 6.6 checks ---
import re
import unicodedata

NOISE = re.compile(r"<[^>]+>|https?://|\[(?:SYSTEM|CATALOGUE|VERIFIED_PURCHASE|SOURCE:|RATING:)"
                   r"|@store_support|&[a-z]+;|[\U0001F300-\U0001FAFF]")

# VAL-TEXT-01 — the three narrative fields must be clean and lower case.
narrative = [("orders", "customer_note_clean"),
             ("products", "product_description_clean"),
             ("product_reviews", "review_body_clean")]
noise_left = {f"{n}.{c}": int(T[n][c].str.contains(NOISE).sum()) for n, c in narrative}
case_left  = {f"{n}.{c}": int((T[n][c] != T[n][c].str.lower()).sum()) for n, c in narrative}
record("VAL-TEXT-01", not any(noise_left.values()) and not any(case_left.values()),
       f"noise left {noise_left}; rows not lower case {case_left}")

# VAL-TEXT-01b — delivery_note_clean is a fixed category, so it keeps its own capitals.
note = T["deliveries"].delivery_note_clean
record("VAL-TEXT-01b", int(note.str.contains(NOISE).sum()) == 0,
       f"{note.nunique()} different values, {int(note.str.contains(NOISE).sum())} with noise; "
       f"values: {sorted(note.unique())}")

# VAL-TEXT-03 / -04 / -05 / -12 — shape checks. NaN is a valid answer for all of them.
rv = T["product_reviews"]
SHAPES = [("VAL-TEXT-03", rv.extracted_order_reference, r"[HC]ORD\d{6}|NaN", "extracted_order_reference"),
          ("VAL-TEXT-04", rv.extracted_product_sku,     r"SKU-[A-Za-z0-9]+|NaN", "extracted_product_sku"),
          ("VAL-TEXT-05", T["orders"].promo_code,       r"B[1-5]SAVE-\d{2}|NaN", "promo_code"),
          ("VAL-TEXT-12", T["orders"].coupon_code,      r"B[1-5]SAVE-\d{2}|NaN", "coupon_code")]
for vid, col, pattern, label in SHAPES:
    bad = int((~col.str.fullmatch(pattern)).sum())
    record(vid, bad == 0,
           f"{label}: {bad} wrong shape; {int((col != 'NaN').sum()):,} of {len(col):,} filled in")

# VAL-TEXT-06 — the codes must be pulled from the raw text, before cleaning removes them.
still_there = int(rv.review_body_clean.str.contains(r"[HC]ORD\d{6}|SKU-[A-Za-z0-9]+").sum())
found = int((rv.extracted_order_reference != "NaN").sum())
record("VAL-TEXT-06", still_there == 0 and found > 0,
       f"references left in the cleaned text: {still_there}; references found: {found:,} "
       f"— so extraction ran before cleaning")

def has_non_latin_letter(text):
    """True if any letter is outside the Latin alphabet. Accents stay Latin."""
    for ch in text:
        if ch.isalpha():
            try:
                if not unicodedata.name(ch).startswith("LATIN"):
                    return True
            except ValueError:
                return True
    return False

# VAL-TEXT-07 — the rule is "remove non-Latin letters", not "keep only Latin letters".
# Digits, spaces and punctuation are left alone by design, so the check asserts that
# no non-Latin LETTER survived, and reports the other character types as evidence.
latin = rv.review_body_latin_analysis
leaked = int(latin[latin != "NaN"].map(has_non_latin_letter).sum())

kinds = {"accented Latin letters": 0, "non-Latin letters": 0,
         "punctuation and marks (kept by design)": 0}
for ch in {c for s in latin for c in s if ord(c) > 127}:
    if not ch.isalpha():
        kinds["punctuation and marks (kept by design)"] += 1
    elif has_non_latin_letter(ch):
        kinds["non-Latin letters"] += 1
    else:
        kinds["accented Latin letters"] += 1   # é, ü, ą — these are meant to stay

# The sentinel is decided by "is a Latin letter left", not by "is the text empty",
# so a review with only non-Latin text still returns NaN even when punctuation survives.
no_latin_left = ~rv.review_body_clean.map(
    lambda s: any(ch.isalpha() and not has_non_latin_letter(ch) for ch in s))
sentinel_ok = (latin[no_latin_left] == "NaN").all() if no_latin_left.any() else True

record("VAL-TEXT-07", leaked == 0 and sentinel_ok,
       f"{leaked} rows keep a non-Latin letter; sentinel correct on the "
       f"{int(no_latin_left.sum())} rows with no Latin letter; character types present: {kinds}")

# VAL-TEXT-08 — the flag must match the text. Polish, German and French use Latin
# letters with accents and must stay False; this is where an ASCII test goes wrong.
actual = rv.review_body_clean.map(has_non_latin_letter)
flag = rv.contains_non_latin_script.map({"True": True, "False": False})
wrong = int((flag != actual).sum())
accented = rv[rv.language_code.isin(["pl", "de", "fr", "it", "es", "nl", "pt"])]
false_alarms = int(accented.contains_non_latin_script.map({"True": True, "False": False}).sum())
record("VAL-TEXT-08", wrong == 0 and false_alarms == 0,
       f"{wrong} rows disagree; flag is True on {int(flag.sum())}, text says {int(actual.sum())}; "
       f"{false_alarms} of {len(accented):,} accented-Latin reviews wrongly flagged")

# VAL-TEXT-09 — 'none' is a real category, not a missing value.
reason = T["deliveries"].delay_reason
record("VAL-TEXT-09", (reason == "none").any(),
       f"delay_reason is 'none' on {int((reason=='none').sum()):,} rows and was not turned into NaN")

# VAL-TEXT-10 — three fields hold one value only, so the completed filter removes nothing.
single = {"orders.order_status": sorted(T["orders"].order_status.unique()),
          "deliveries.delivery_status": sorted(T["deliveries"].delivery_status.unique()),
          "product_reviews.verified_purchase": sorted(rv.verified_purchase.unique())}
record("VAL-TEXT-10", all(len(v) == 1 for v in single.values()),
       f"{single} — the completed filter removes no rows, which is expected here")

# VAL-TEXT-13 / -14 / -15 — the three cross-checks. Each compares a value pulled out
# of free text against a value that reached the table by a different route.
cc, pc = T["orders"].coupon_code, T["orders"].promo_code
both = (cc != "NaN") & (pc != "NaN")
one_sided = int(len(cc) - both.sum() - ((cc == "NaN") & (pc == "NaN")).sum())
disagree = int((cc[both] != pc[both]).sum())
record("VAL-TEXT-13", disagree == 0 and one_sided == 0,
       f"{int(both.sum()):,} rows have both and {disagree} disagree; {one_sided} rows have one but not the other")

mismatch = int((rv.extracted_order_reference != rv.order_id).sum())
record("VAL-TEXT-14", mismatch == 0,
       f"{mismatch} of {len(rv):,} reviews have a reference that is not their own order_id")

sku_of = T["products"].set_index("product_id").product_sku
mismatch = int((rv.extracted_product_sku != rv.product_id.map(sku_of)).sum())
record("VAL-TEXT-15", mismatch == 0,
       f"{mismatch} of {len(rv):,} reviews have a SKU that does not match their product")


# **Observed result / status / interpretation.** The three narrative fields are free of markup,
# markers, URLs and emoji and are fully lower-cased. `delivery_note_clean` is asserted separately
# as a structured category and now carries the source's own casing, which is the evidence that the revert reached the files rather than living only in the register.
#
# `contains_non_latin_script` is `True` on exactly the rows whose cleaned text carries a non-Latin
# letter, and every review in a Latin-script language with diacritics correctly stays `False` —
# that is the discrimination a naive ASCII test fails. `build_latin_analysis` keeps punctuation and
# combining marks by design: the published rule removes non-Latin *letters*, and the sentinel is
# decided by whether a Latin letter remains, not by whether the text is empty, so a wholly
# non-Latin review still returns `NaN` even when punctuation survives.
#
# **VAL-TEXT-13, -14 and -15 are the strongest checks in the register.** Every other text check
# compares an extraction to the pattern that produced it, so a wrong pattern fails the same way
# twice and still passes. These three compare a value pulled from free text against a value that
# reached the table by an entirely different route — a structured source column, the review's own
# `order_id`, and the product catalogue reached through the foreign key. They are the only checks
# here that can distinguish a right-looking wrong answer from a right one, and all three come out
# with no disagreements and no one-sided rows.
#
# **What would have made this section fail.** Markup surviving cleaning, an extraction run on the
# cleaned text instead of the raw text, diacritics stripped as if foreign, `delay_reason == 'none'`
# mapped to the sentinel, or an extracted reference that does not match its own row.


# ### 6.7 Literal `NaN` reminder
#
# Where the spec says a missing piece of text should be written as `NaN`, it means the three
# letters `N`, `a`, `N` — not an empty cell, not Python's `None`, not a float NaN.
#
# Two traps:
#
# - Reading the file back with the normal settings turns that text into an empty value, and then
#   the check cannot see it. Always read with `keep_default_na=False`.
# - Turning an empty value into text does **not** produce `NaN` — pandas 2 gives lowercase `nan`.
#   The text has to be filled in before anything is turned into a string, never produced by the
#   conversion.
#
# Fields that can hold the sentinel: `orders.coupon_code`, `orders.promo_code`,
# `orders.customer_note_clean`, `deliveries.delivery_note_clean`,
# `products.product_description_clean`, `product_reviews.review_body_clean`,
# `product_reviews.review_body_latin_analysis`, `product_reviews.extracted_order_reference`,
# `product_reviews.extracted_product_sku`.
#
# | ID | What it checks | Table | Passes when | If it fails |
# |---|---|---|---|---|
# | VAL-TEXT-11 | In every field above, a missing value is the three letters `NaN`, checked on the exported file read with `keep_default_na=False` | orders, deliveries, products, product_reviews | all match | The required sentinel is not in the submitted files |


# In[68]:

# --- Section 6.7 checks ---
# The tables were read with keep_default_na=False in Section 0.1, so the text NaN is
# still visible as three characters rather than an empty value.

SENTINEL_FIELDS = [("orders", "coupon_code"), ("orders", "promo_code"),
                   ("orders", "customer_note_clean"),
                   ("deliveries", "delivery_note_clean"),
                   ("products", "product_description_clean"),
                   ("product_reviews", "review_body_clean"),
                   ("product_reviews", "review_body_latin_analysis"),
                   ("product_reviews", "extracted_order_reference"),
                   ("product_reviews", "extracted_product_sku")]

counts, mixed = {}, []
for name, col in SENTINEL_FIELDS:
    series = T[name][col]
    counts[f"{name}.{col}"] = int((series == "NaN").sum())
    if (series == "").any():
        mixed.append(f"{name}.{col}")   # an empty cell where the sentinel was expected

record("VAL-TEXT-11", not mixed,
       f"NaN counts {counts}; fields mixing an empty cell with the sentinel: {mixed or 'none'}")


# **Observed result / status / interpretation.** Read back with `keep_default_na=False`, the
# sentinel appears as three characters wherever expected and no field mixes an empty cell with it.
# Reading the files the ordinary way turns that text into a null and the check becomes blind, which
# is why the read options in Section 0.1 are part of the check rather than a convenience.
#
# **What would have made this section fail.** An empty cell where the sentinel belongs, or the
# lowercase `nan` that pandas produces when a null is cast to text instead of the sentinel being
# filled in first.


# ### How each result gets written down
#
# One line per check, right after the code that runs it:
#
# ```
# VAL-PK-01     PASS   5,000 different order_id, 0 blank, matches the number worked out from the sources
# VAL-FLOW-09   PASS   3,259 shared keys, 59 columns, 0 conflicts after normalising
# VAL-FLOW-11   PASS   planted conflict found in the test table; 0 in the real data
# VAL-ARITH-03  FAIL   40 rows outside 0.01  —  what it means and what we propose doing
# ```
#
# A failure gets its evidence and a suggested fix. The rubric gives marks for a real failed check
# that finds the problem and says what to do about it, and no marks for making a number up so the
# check passes. An all-green register is not the goal.


# In[69]:

register = pd.DataFrame(RESULTS, columns=["id", "status", "evidence", "note"])

if register.empty:
    print("No checks have run yet.")
else:
    print(register.status.value_counts().to_dict())
    # Saved so the report can cite VAL- IDs from a file rather than from a screenshot.
    out_path = OUTPUT_DIR / f"{GROUP_ID}_validation_register.csv"
    register.to_csv(out_path, index=False)
    print(f"written -> {out_path}")

register


# ## 7. Export the six CSV files
#
# Export exactly the required filenames, columns and order. Display a compact
# final schema/row-count summary without hard-coding certified counts.


# The export is guarded. A run in which the published text functions were not available would
# still produce six files of the right shape, with three columns entirely sentinel and every
# narrative field uncleaned — and the files themselves would carry no sign of it. The guard is
# here so that state cannot reach `outputs/` silently.
#
# After writing, each file is read back and checked against the contract, and against the frame
# the register validated in Section 6, so the exported bytes are the bytes that were checked.


# In[70]:

# --- Section 7: export the six CSV files ---

# A run built on anything other than the published functions must not write to outputs/.
assert all(fn.__module__ == 'Group001_text_functions' for fn in TEXT_FUNCTIONS), (
    'the six text functions are not the published module; refusing to write outputs/')

TABLES_FINAL = {t: globals()[f'{t}_final'] for t in OUTPUT_TABLES}

for name, df in TABLES_FINAL.items():
    path = OUTPUT_DIR / f'{GROUP_ID}_{name}_standardised.csv'
    format_for_export(df, name).to_csv(path, index=False,
                                       lineterminator=LINE_ENDING)

    # Read back and verify the contract survived the round trip.
    back = pd.read_csv(path, keep_default_na=False, dtype=str)
    fields, pk = CONTRACT[name]['fields'], CONTRACT[name]['pk']
    assert list(back.columns) == fields, name
    assert len(back) == len(df), name
    assert back[pk].is_unique and (back[pk] != '').all(), name
    # The bytes on disk are the bytes Section 6 validated.
    assert back.equals(T[name]), f'{name}: exported file differs from the validated frame'
    # And the same bytes on every operating system: no carriage returns.
    assert b'\r' not in path.read_bytes(), (
        f'{name}: file has CRLF line endings, so its bytes depend on the machine that ran this')

    print(f'{name:16s} {len(back):>7,} rows x {back.shape[1]:>2} cols  ->  {path.name}')


# #### 7.1 Field coverage of the exported files
#
# The rubric scores field-value accuracy as an equal-weight mean across the six tables, so the
# number worth printing is per table and then averaged, not summed over all 111 fields. A field
# counts as unfilled only when it is the sentinel or blank on **every** row — a field that is
# absent for some rows and present for others is a real value, not a gap.
#
# `coupon_code` and `promo_code` are the only fields carrying the sentinel at all, on the same
# rows: those orders used no promotion.


# In[71]:

# --- Section 7.1: coverage of the exported files, read from the files themselves ---
rows = []
for t in OUTPUT_TABLES:
    df = pd.read_csv(OUTPUT_DIR / f'{GROUP_ID}_{t}_standardised.csv',
                     keep_default_na=False, dtype=str)
    pk, fields = CONTRACT[t]['pk'], CONTRACT[t]['fields']
    unfilled = [f for f in fields if (df[f] == 'NaN').all() or (df[f] == '').all()]
    rows.append({'table': t, 'rows': len(df), 'fields': len(fields),
                 'pk_unique': df[pk].is_unique,
                 'pk_complete': (df[pk].str.strip() != '').all(),
                 'grain_holds': len(df) == df[pk].nunique(),
                 'unfilled': len(unfilled),
                 'coverage': (len(fields) - len(unfilled)) / len(fields)})

coverage = pd.DataFrame(rows)
print(coverage.to_string(index=False))
print(f"\nequal-weight mean field coverage: {coverage['coverage'].mean():.2%}")

sentinel = {f'{t}.{f}': int((pd.read_csv(OUTPUT_DIR / f'{GROUP_ID}_{t}_standardised.csv',
                                         keep_default_na=False, dtype=str)[f] == 'NaN').sum())
            for t in OUTPUT_TABLES for f in CONTRACT[t]['fields']}
print('fields carrying the sentinel at all:',
      {k: v for k, v in sentinel.items() if v} or 'none')


# ## 8. Final reproducibility record
#
# Record the final run date, dependency versions and the result of Restart and Run
# All. Confirm that the six outputs and validation evidence were recreated from
# the allocated raw files.


# In[72]:

# --- Section 8: reproducibility record ---
import datetime, platform

register = pd.DataFrame(RESULTS, columns=['id', 'status', 'evidence', 'note'])

print('run finished     ', datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))
print('python           ', platform.python_version())
print('pandas           ', pd.__version__)
print('input            ', INPUT_DIR.resolve().name, '(allocated package, unmodified)')
print('output           ', OUTPUT_DIR.resolve().name)
print()
print('validation register', register.status.value_counts().to_dict())
print()

written = sorted(p.name for p in OUTPUT_DIR.glob('*.csv'))
crlf = [n for n in written if b'\r' in (OUTPUT_DIR / n).read_bytes()]
assert not crlf, crlf
for name in written:
    print(f'   {name:52s} {(OUTPUT_DIR / name).stat().st_size:>10,} bytes')

required = {f'{GROUP_ID}_{t}_standardised.csv' for t in OUTPUT_TABLES}
assert required <= set(written), sorted(required - set(written))
print(f'\n{len(required)} required tables, the mapping and the validation register were '
      f'recreated from the allocated raw files by this run.')
print('No cell in this notebook reads a network resource, a private account or a file '
      'outside the submission.')

