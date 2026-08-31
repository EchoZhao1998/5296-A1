"""
S1.3g  Source paths for the mapping, read from the files instead of typed by hand.

Produces the three mechanical columns of the source-to-target mapping
(source_format, json_source_path, xml_source_path) for all 111 target fields.
The two judgement columns -- transformation_or_derivation and
overlap_or_conflict_rule -- are still written by hand; this only removes the
typing that a machine does more reliably than we do.
"""
import json
import xml.etree.ElementTree as ET
import pandas as pd

# --- 1. Every leaf path in each source ----------------------------------
def json_leaves(node, path=""):
    """Dotted path of every scalar. Lists collapse to '[]': the path
    describes the shape of a record, not the position of one row."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from json_leaves(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for item in node[:50]:      # 50 samples catch keys that are optional
            yield from json_leaves(item, path + "[]")
    else:
        yield path

def xml_leaves(elem, path=""):
    """Path of every childless element."""
    path = f"{path}/{elem.tag}" if path else elem.tag
    if len(elem) == 0:
        yield path
    else:
        for child in elem:
            yield from xml_leaves(child, path)

json_paths = set(json_leaves(json.load(open(INPUT_DIR / "Group001_commerce.json"))))
xml_paths  = set(xml_leaves(ET.parse(INPUT_DIR / "Group001_operations.xml").getroot()))

# --- 2. Index the paths by their final segment --------------------------
# orderID (JSON), Order_ID (XML) and order_id (dictionary) are the same name
# in three casings, so compare them with the casing removed.
def norm(name):
    return name.lower().replace("_", "")

def index_by_leaf(paths, sep):
    out = {}
    for p in paths:
        out.setdefault(norm(p.split(sep)[-1]), []).append(p)
    return out

json_index = index_by_leaf(json_paths, ".")
xml_index  = index_by_leaf(xml_paths, "/")

# --- 3. The grain anchor ------------------------------------------------
# A name alone is ambiguous: order_id appears in four JSON blocks. The anchor
# says which block carries one row per output row, so the right one is picked.
# Read off the structure survey in S1.1/S1.2 and the grain evidence in S1.4.
ANCHOR = {   # output_table: (json prefix, xml prefix); None = absent here
    "orders":          ("orders[].header.",         "Orders/Order/Header/"),
    "order_items":     ("orders[].shoppingCart[].", "Orders/Order/Shopping_Cart/Item/"),
    "deliveries":      ("orders[].delivery.",       "Orders/Order/Delivery/"),
    "customers":       ("customerProfiles[].",      None),
    "products":        (None,                       "ProductCatalogue/Product/"),
    "product_reviews": ("productReviews[].",        "ProductReviews/Review/"),
}

def pick(candidates, prefix):
    """Keep the single candidate that sits under this table's anchor."""
    if prefix is None:
        return ""
    hits = [p for p in candidates if prefix in p]
    return hits[0] if len(hits) == 1 else ""

# --- 4. Match the dictionary against both indexes -----------------------
dictionary = pd.read_csv(INPUT_DIR.parent / "public_data_dictionary.csv")

rows = []
for _, field in dictionary.iterrows():
    json_prefix, xml_prefix = ANCHOR[field.output_table]
    name = norm(field.field_name)
    jp = pick(json_index.get(name, []), json_prefix)
    xp = pick(xml_index.get(name, []), xml_prefix)
    fmt = "both" if jp and xp else "JSON" if jp else "XML" if xp else "derived"
    rows.append({
        "mapping_id":       f"MAP-{field.output_table}-{field.position:02d}",
        "output_table":     field.output_table,
        "target_field":     field.field_name,
        "source_format":    fmt,
        "json_source_path": jp,
        "xml_source_path":  xp.replace("OperationsExport/", ""),
    })

paths = pd.DataFrame(rows)

# --- 5. Checks ----------------------------------------------------------
# 'derived' here means "no field of this name at this grain in either file",
# which is what a derived field looks like from the outside. It must land on
# exactly the ten text fields, or the anchors above are wrong.
assert len(paths) == 111, len(paths)
assert (paths.source_format == "derived").sum() == 10
print(paths.pivot_table(index="output_table", columns="source_format",
                        values="target_field", aggfunc="count", fill_value=0))
paths.to_csv("Group001_mapping_paths_auto.csv", index=False)
