# Fix (29 Aug 2026):
# Added NFC normalisation after HTML entity decoding.
# Narrowed Unicode filtering from all S* categories to So only

import re
import html
import unicodedata

NAN = "NaN"
def _missing(value):
    """Return True for None, non-string, blank, or literal 'NaN'.

    对 None、非字符串、空白文本或字面量 'NaN' 返回 True。
    """
    return (
        value is None
        or not isinstance(value, str)
        or value.strip() in {"", NAN}
    )


def clean_narrative_text(value):
    """Clean narrative text by removing published wrappers and noise.
    清洗叙述文本，删除规定的包装标记和噪声。
    Args / 参数:
        value (object): Raw narrative value. 原始叙述文本值。
    Returns / 返回:
        str: Clean lower-case text, or literal "NaN" when missing.
             清洗后的小写文本；缺失时返回字面量 "NaN"。
    """
    if _missing(value):
        return NAN

    # decode html
    text = html.unescape(value)
    text = unicodedata.normalize("NFC", text)

    # remove part in <tag>
    text = re.sub(r"<[^>]*>",                                                                   " ", text) 
    # remove part in [SYSTEM] [CATALOGUE] [VERIFIED_PURCHASE] [SOURCE: mobile-app ©] [SOURCE: web-form ™] [RATING: 4/5]
    text = re.sub(r"\[(?:SYSTEM|CATALOGUE|VERIFIED_PURCHASE|SOURCE:[^]]+|RATING:\s*[1-5]/5)\]", " ", text, flags=re.IGNORECASE)
    # remove url
    text = re.sub(r"https?://\S+",                                                              " ", text, flags=re.IGNORECASE)
    # remove coupon 
    text = re.sub(r"\bPROMO:\s*B[1-5]SAVE-\d{2}\b",                                             " ", text, flags=re.IGNORECASE)
    # remove ref
    text = re.sub(r"\bReference:\s*[HC]ORD\d{6}\b\s*[/|;]?",                                    " ", text, flags=re.IGNORECASE)
    # remove SKU
    text = re.sub(r"\bSKU:\s*SKU-[A-Z0-9]+\b",                                                  " ", text, flags=re.IGNORECASE)
    # remove #verified-buyer @store_support
    text = re.sub(r"(?:#verified-buyer|@store_support)\b",                                      " ", text, flags=re.IGNORECASE)

    # remove Unicode emoji but will keep others like $+=
    text = "".join(char for char in text if unicodedata.category(char) != "So")

    text = " ".join(text.lower().split())
    return text or NAN


def extract_order_reference(value):
    """Extract a valid HORD/CORD order reference from raw text.
    从原始文本中提取有效的 HORD/CORD 订单编号。
    Args / 参数:
        value (object): Raw narrative value. 原始叙述文本值。
    Returns / 返回:
        str: Upper-case order reference, or literal "NaN" when absent.
             大写订单编号；不存在时返回字面量 "NaN"。
    """
    if _missing(value):
        return NAN

    # Match a standalone HORD/CORD followed by exactly six digits.
    match = re.search(
        r"(?<![A-Z0-9])[HC]ORD\d{6}(?![A-Z0-9])",
        value,
        flags=re.IGNORECASE,
    )
    return match.group(0).upper() if match else NAN


def extract_product_sku(value):
    """Extract a valid product SKU from raw text.
    从原始文本中提取有效的产品 SKU。
    Args / 参数:
        value (object): Raw narrative value. 原始叙述文本值。
    Returns / 返回:
        str: Upper-case product SKU, or literal "NaN" when absent.
             大写产品 SKU 不存在时返回字面量 "NaN"。
    """
    if _missing(value):
        return NAN

    # Match a standalone SKU- followed by letters or digits; reject extensions.
    # 匹配独立的 SKU-及其后的字母或数字，并拒绝额外扩展。
    match = re.search(
        r"(?<![A-Z0-9_-])SKU-[A-Z0-9]+(?![A-Z0-9_-])",
        value,
        flags=re.IGNORECASE,
    )
    return match.group(0).upper() if match else NAN


def extract_promo_code(value):
    """Extract a valid promotion code from raw text.

    从原始文本中提取有效的促销码。

    Args / 参数:
        value (object): Raw narrative value. 原始叙述文本值。

    Returns / 返回:
        str: Upper-case promotion code, or literal "NaN" when absent.
             大写促销码；不存在时返回字面量 "NaN"。
    """
    if _missing(value):
        return NAN

    # Match a standalone B1-B5 SAVE code followed by exactly two digits.
    # 匹配独立的 B1-B5 SAVE 促销码及其后的两位数字。
    match = re.search(
        r"(?<![A-Z0-9_-])B[1-5]SAVE-\d{2}(?![A-Z0-9_-])",
        value,
        flags=re.IGNORECASE,
    )
    return match.group(0).upper() if match else NAN

def build_latin_analysis(value):
    """Build a Latin-script analysis value from cleaned narrative text.
    从清洗后的叙述文本中生成拉丁文字分析值。
    Args / 参数:
        value (object): Cleaned narrative value. 清洗后的叙述文本值。
    Returns / 返回:
        str: Text without non-Latin letters, or literal "NaN" if none remain.
             删除非拉丁字母后的文本；没有拉丁字母时返回字面量 "NaN"。
    """
    if _missing(value):
        return NAN

    text = unicodedata.normalize("NFC", value)

    # Keep Latin letters (including diacritics) and replace other-script letters with spaces.
    # 保留拉丁字母（包括重音字母），并用空格替换其他文字系统的字母。
    kept_characters = []
    for char in text:
        if not char.isalpha() or "LATIN" in unicodedata.name(char, ""):
            kept_characters.append(char)
        else:
            kept_characters.append(" ")

    text = "".join(kept_characters)
    text = " ".join(text.split())

    has_latin_letter = False
    for char in text:
        if char.isalpha() and "LATIN" in unicodedata.name(char, ""):
            has_latin_letter = True
            break

    if has_latin_letter:
        return text
    return NAN

def contains_non_latin_script(value):
    """Check whether cleaned narrative text contains a non-Latin letter.
    检查清洗后的叙述文本是否包含非拉丁字母。
    Args / 参数:
        value (object): Cleaned narrative value. 清洗后的叙述文本值。
    Returns / 返回:
        bool: True if a non-Latin letter exists; otherwise False.
              存在非拉丁字母时返回 True 否则返回 False。
    """
    if _missing(value):
        return False

    # Ignore numbers and punctuation; only letters can identify a script.
    # 忽略数字和标点；只有字母用于判断文字系统。
    text = unicodedata.normalize("NFC", value)
    for char in text:
        if char.isalpha() and "LATIN" not in unicodedata.name(char, ""):
            return True

    return False


if __name__ == "__main__":
    import csv
    from pathlib import Path
    test_path = (
        Path(__file__).resolve().parents[1]
        / "Admin"
        / "templates"
        / "A1_public_text_test_cases.csv"
    )
    tested = 0
    with test_path.open(newline="", encoding="utf-8") as test_file:
        for case in csv.DictReader(test_file):
            function = globals()[case["function"]]
            actual = function(case["input_value"])
            expected = case["expected_output"]

            print(f'\n{case["case_id"]} - {case["function"]}')
            print(f'原字符串：{case["input_value"]!r}')
            print(f'处理后的字符串：{actual!r}')

            assert str(actual) == expected, (
                f'{case["case_id"]}: expected {expected!r}, got {actual!r}'
            )
            tested += 1

    print(f"\n{tested} public text tests passed.")
