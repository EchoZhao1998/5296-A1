#!/usr/bin/env python
# coding: utf-8

# # FIT5196 Assessment 1 - Solution Notebook
# 
# **Group:** Group001
# 
# This notebook parses the allocated JSON and XML files, creates the six required
# tables, tests the published text interface, reconciles overlap, validates the
# results, and exports the assessed CSV files.
# 

# ## 0. Configuration and reproducibility
# 
# All paths are relative or configurable. The workflow runs offline from a fresh
# kernel and writes generated files to `OUTPUT_DIR`.
# 

# In[1]:


# --- Section 0: configuration ---
from pathlib import Path

GROUP_ID = 'Group001'

# A Python export may be launched from any working directory. Anchor its outputs
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

JSON_PATH = INPUT_DIR / f'{GROUP_ID}_commerce.json'
XML_PATH  = INPUT_DIR / f'{GROUP_ID}_operations.xml'
DICT_PATH = INPUT_DIR.parent / 'public_data_dictionary.csv'

for label, path in [('input', INPUT_DIR), ('output', OUTPUT_DIR)]:
    print(f'{label:7s} {path}')


# ## 1. Parse and profile the two sources
# 
# JSON and XML are read with structured parsers. The following evidence covers
# source structure, grain, formats, keys, missing values and overlap.
# 

# In[2]:


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


# In[3]:


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


# In[4]:


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


# In[5]:


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


# In[6]:


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


# In[7]:


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

# In[8]:


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


# In[9]:


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


# In[10]:


naive_xml, _ = parse_xml(XML_PATH)
check_names(naive_xml, DICT_PATH)


# In[11]:


# Written from the pass-1 report above, not before it. Keys are original tags.
XML_NAME_EXCEPTIONS = {
    "Customer_Note":       "customer_note_raw",
    "Review_Text":         "review_body_raw",
    "Product_Description": "product_description_raw",
}


# In[12]:


xml_tables, xml_meta = parse_xml(XML_PATH, XML_NAME_EXCEPTIONS)
check_names(xml_tables, DICT_PATH)
del naive_xml

print("\nExport metadata:", xml_meta)
for name, df in xml_tables.items():
    print(f"{name:16s} {df.shape[0]:,} rows x {df.shape[1]:>2} cols")


# In[13]:


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


# In[14]:


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
# Comparable values are normalised before overlap is assessed. Required keys come
# from the public dictionary and are checked against the observed data.
# 

# In[15]:


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


# In[16]:


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


# In[17]:


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


# In[18]:


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


# In[19]:


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


# In[20]:


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


# In[21]:


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


# In[22]:


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


# In[23]:


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


# In[24]:


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


# #### Assumptions
# 
# - Customer records occur only in JSON and product records only in XML.
# - Shared records are reconciled by business key after field normalisation.
# - Different non-missing values for a shared key are reported as conflicts.
# - Dates use the source-specific formats demonstrated above.
# - Monetary and derived fields follow the published formulas and tolerance.
# 

# ### 1.4 Source grain and requirement coverage
# 

# In[25]:


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


# ## 2. Source-to-target mapping
# 
# The supplied mapping structure is completed from observed source paths and the
# public dictionary. The final checks require every target row, preserve dictionary
# order and reject blank or placeholder entries.
# 

# In[26]:


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


# In[27]:


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


# In[28]:


# "derived" is not declared anywhere above: it is simply what is left when no field of
# that name exists at that table's grain in either file. If an anchor were wrong, this
# list would move — which is what makes it a check rather than a restatement.
assert len(MAPPING_PATHS) == len(DICTIONARY), (len(MAPPING_PATHS), len(DICTIONARY))

derived = MAPPING_PATHS[MAPPING_PATHS.source_format == "derived"]
print(f"{len(derived)} fields with no source path:")
print(derived[["output_table", "target_field"]].to_string(index=False))

# The number in each mapping_id is the dictionary's own position, so the mapping, the
# dictionary and the column order of the output CSVs remain one ordering, not three.
positions = MAPPING_PATHS.mapping_id.str.extract(r"-(\d+)$")[0].astype(int)
assert (positions.values == DICTIONARY.position.values).all()
print("\nrow numbers match the dictionary's field positions")


# In[29]:


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


# In[30]:


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


# In[31]:


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


# In[32]:


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
# The six required functions are imported from `Group001_text_functions.py` and
# tested against both public and group-designed cases, including missing,
# multilingual and malformed near-match inputs.
# 

# In[33]:


# --- Section 3.1: import the published interface ---
TEXT_FN_CANDIDATES = [
    BASE_DIR / f'{GROUP_ID}_text_functions.py',
    BASE_DIR.parent / f'{GROUP_ID}_text_functions.py',
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


# In[34]:


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

CASE_FILES = [
    BASE_DIR / 'A1_public_text_test_cases.csv',
    BASE_DIR / 'templates' / 'A1_public_text_test_cases.csv',
    BASE_DIR / f'{GROUP_ID}_own_text_test_cases.csv',
]

total = failed = 0
for path in CASE_FILES:
    if path.exists():
        n, f = run_cases(path)
        total, failed = total + n, failed + f
assert total > 0, 'no test-case file found'
assert failed == 0, f'{failed} text-function cases failed'
print(f'\n{total} cases, {failed} failures')


# ## 4. Build the six standardised relational tables
# 
# Shared helpers normalise source values, compare duplicate records, retain one
# canonical row per key, and conform each result to the dictionary. Helper columns
# are removed before export.
# 

# In[35]:


# --- Section 4.0 Read the published contract ---

# The dictionary was read once in Section 0.1; this cell only displays it.

print('shape  ', dd.shape)
print('columns', dd.columns.tolist())
print()
print(dd['output_table'].value_counts().to_string())
dd.head(12)


# In[36]:


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


# In[37]:


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


# In[38]:


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


# In[39]:


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


# In[40]:


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


# In[41]:


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


# In[42]:


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


# In[43]:


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


# ### 4.0 Shared transformation rules
# 
# Money uses decimal-style half-up rounding. Order items are built before orders
# because canonical `order_price` is calculated from rounded line revenue.
# 

# In[44]:


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


# ### 4.2 `order_items`
# 

# In[45]:


# --- Section 4.2 order_items ---

TABLE = 'order_items'

combined = mark_overlap(combine_sources(TABLE), TABLE)
deduped  = deduplicate(combined, TABLE)

print(f'{TABLE}')
print(f'   JSON {len(json_tables[TABLE]):,} + XML {len(xml_tables[TABLE]):,}'
      f' = {len(combined):,} concatenated')
print(f'   deduped {len(deduped):,}  ({len(combined) - len(deduped):,} removed)')

deduped.head()


# In[46]:


# --- Section 4.2 line_revenue: recompute and reconcile ---

recomputed = (deduped['quantity'] * deduped['unit_price']).round(2)
gap = (recomputed - deduped['line_revenue']).abs()

print(f'rows                     {len(deduped):,}')
print(f'outside tolerance 0.01   {int((gap > 0.01).sum()):,}')
print(f'largest difference       {gap.max():.4f}')

deduped['line_revenue'] = recomputed


# In[47]:


# --- Section 4.2 order_items: conform and report ---

order_items_marked = deduped
order_items_final  = conform_to_contract(order_items_marked, TABLE)
row_flow(TABLE, combined, order_items_final)

order_items_final.head()


# ### 4.1 `orders`
# 

# In[48]:


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


# In[49]:


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

# In[50]:


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

# In[51]:


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

# In[52]:


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


# In[53]:


# --- Section 4.5 products: derived field and conform ---

# product_description_clean comes from WP4. Provisional while the placeholder banner shows.
deduped['product_description_clean'] = deduped['product_description_raw'].map(clean_narrative_text)

products_marked = deduped
products_final  = conform_to_contract(products_marked, TABLE)
row_flow(TABLE, combined, products_final)

products_final.head()


# ### 4.6 `product_reviews`
# 

# In[54]:


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


# In[55]:


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
# The pre-deduplication frames show within-source repetition, cross-source overlap
# and any non-missing field conflicts after normalisation.
# 

# In[56]:


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


# ## 6. Validation register
# 
# Every executable check records a stable ID, PASS/FAIL status, observed result and
# interpretation. Expected quantities are derived from the source or dictionary,
# not hard-coded canonical answers.
# 

# In[57]:


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


# ### 6.1 Schema, type and missing-value checks
# 

# In[58]:


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
date_fields = list(dd.loc[dd.data_type.eq('date'),
                          ['output_table', 'field_name']].itertuples(index=False, name=None))
stamp_fields = list(dd.loc[dd.data_type.eq('datetime'),
                           ['output_table', 'field_name']].itertuples(index=False, name=None))
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


# ### 6.2 Primary- and foreign-key checks
# 

# In[59]:


# --- Section 6.2 checks ---
PK = {table: CONTRACT[table]['pk'] for table in OUTPUT_TABLES}

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


# ### 6.3 Source coverage and reconciliation checks
# 

# In[60]:


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

# VAL-FLOW-12 — how many keys came from both files, against the raw key sets.
expected_shared = {"orders": len(j_ord & x_ord), "order_items": len(j_item & x_item),
                   "deliveries": len(j_del & x_del), "product_reviews": len(j_rev & x_rev)}
observed_shared = {t: OVERLAP[t] for t in expected_shared}
record("VAL-FLOW-12", observed_shared == expected_shared,
       f"keys carried by both files {observed_shared}; the raw key sets intersect at "
       f"{expected_shared}")


# ### 6.4 Arithmetic and numeric-range checks
# 

# In[61]:


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


# ### 6.5 Temporal checks
# 

# In[62]:


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

# VAL-TIME-04 — exported order years must equal the years derived from both raw sources.
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

# For context, not a check: how many deliveries were late.
print(f"{'(context)':18s} INFO  {int((dl.delivered_date > dl.promised_date).sum()):,} "
      f"deliveries arrived after the promised date — a business outcome, not a data problem")


# ### 6.6 Text and multilingual checks
# 

# In[63]:


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
record('VAL-TEXT-08', wrong == 0,
       f"{wrong} rows disagree; flag is True on {int(flag.sum())}, "
       f"cleaned text contains non-Latin letters on {int(actual.sum())}")

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


# ### 6.7 Literal `NaN` checks
# 

# In[64]:


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


# In[65]:


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
# Each table is written in dictionary field order and read back to confirm its
# schema, grain, primary key, values and platform-independent line endings.
# 

# In[66]:


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


# ## 8. Final reproducibility record
# 
# The final cell reports versions, validation totals and generated artifacts.
# 

# In[67]:


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

