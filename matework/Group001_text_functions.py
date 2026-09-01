"""Group001 - the six published text functions for FIT5196 A1.

No file I/O, no network access and no row-specific lookup: every function takes
one value and returns one value, so the module can be tested on its own.
"""

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

    # remove <tag> markup, keeping the human-readable content it wraps
    text = re.sub(r"<[^>]*>", " ", text)

    # remove the published bracketed markers:
    # [SYSTEM] [CATALOGUE] [VERIFIED_PURCHASE] [SOURCE: ...] [RATING: n/5]
    text = re.sub(r"\[(?:SYSTEM|CATALOGUE|VERIFIED_PURCHASE|SOURCE:[^]]+|RATING:\s*[1-5]/5)\]",
                  " ", text, flags=re.IGNORECASE)

    # remove urls
    text = re.sub(r"https?://\S+", " ", text, flags=re.IGNORECASE)

    # remove PROMO: and its code
    text = re.sub(r"\bPROMO:\s*B[1-5]SAVE-\d{2}\b", " ", text, flags=re.IGNORECASE)

    # remove the review reference wrapper, then the SKU wrapper
    text = re.sub(r"\bReference:\s*[HC]ORD\d{6}\b\s*[/|;]?", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bSKU:\s*SKU-[A-Z0-9]+\b", " ", text, flags=re.IGNORECASE)

    # remove the two social markers
    text = re.sub(r"(?:#verified-buyer|@store_support)\b", " ", text, flags=re.IGNORECASE)

    # remove Unicode emoji but will keep others like $+=
    text = "".join(char for char in text if unicodedata.category(char) != "So")

    text = " ".join(text.lower().split())
    return text or NAN


def _extract_reference(value, pattern):
    """Extract one bounded ASCII reference and return it in upper case.
    提取一个边界完整的 ASCII 编号，并以大写形式返回。
    Args / 参数:
        value (object): Raw narrative value. 原始叙述文本值。
        pattern (str): Regex for the reference format. 编号格式正则。
    Returns / 返回:
        str: Upper-case reference, or literal "NaN" when invalid or absent.
             大写编号；格式无效或不存在时返回字面量 "NaN"。
    """
    if _missing(value):
        return NAN

    # No letter, digit, underscore or hyphen may touch either end.
    # 编号两端不能紧邻字母、数字、下划线或连字符。
    match = re.search(
        r"(?<![\w-])" + pattern + r"(?![\w-])",
        value,
        flags=re.IGNORECASE,
    )
    if match is None:
        return NAN

    # Published reference formats are ASCII; reject Unicode look-alikes.
    # 规定的编号格式仅限 ASCII，拒绝其他文字系统中的相似字符。
    token = match.group(0)
    if not token.isascii():
        return NAN

    return token.upper()


def extract_order_reference(value):
    """Extract a valid HORD/CORD order reference from raw text.
    从原始文本中提取有效的 HORD/CORD 订单编号。
    Args / 参数:
        value (object): Raw narrative value. 原始叙述文本值。
    Returns / 返回:
        str: Upper-case order reference, or literal "NaN" when absent.
             大写订单编号；不存在时返回字面量 "NaN"。
    """
    return _extract_reference(value, r"[HC]ORD\d{6}")


def extract_product_sku(value):
    """Extract a valid product SKU from raw text.
    从原始文本中提取有效的产品 SKU。
    Args / 参数:
        value (object): Raw narrative value. 原始叙述文本值。
    Returns / 返回:
        str: Upper-case product SKU, or literal "NaN" when absent.
             大写产品 SKU 不存在时返回字面量 "NaN"。
    """
    return _extract_reference(value, r"SKU-[A-Z0-9]+")


def extract_promo_code(value):
    """Extract a valid promotion code from raw text.

    从原始文本中提取有效的促销码。

    Args / 参数:
        value (object): Raw narrative value. 原始叙述文本值。

    Returns / 返回:
        str: Upper-case promotion code, or literal "NaN" when absent.
             大写促销码；不存在时返回字面量 "NaN"。
    """
    return _extract_reference(value, r"B[1-5]SAVE-\d{2}")

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
