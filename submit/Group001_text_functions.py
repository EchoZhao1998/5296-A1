"""Group001 - the six published text functions for FIT5196 A1.

No file I/O, no network access and no row-specific lookup: every function takes
one value and returns one value, so the module can be tested on its own.
"""

import re
import html
import unicodedata
import regex

NAN = "NaN"

# Match complete Unicode emoji sequences instead of maintaining incomplete
# handwritten ranges.
_EMOJI_SEQUENCE = regex.compile(
    r"(?:"
    r"\p{Regional_Indicator}{2}"
    r"|[#*0-9]\ufe0f?\u20e3"
    r"|(?:\p{Extended_Pictographic}|\p{Emoji_Presentation})"
    r"\ufe0f?\p{Emoji_Modifier}?"
    r"(?:\u200d(?:\p{Extended_Pictographic}|\p{Emoji_Presentation})"
    r"\ufe0f?\p{Emoji_Modifier}?)*"
    r"(?:[\U000E0020-\U000E007E]+\U000E007F)?"
    r")"
)

# Match plausible HTML/XML-like tags without consuming comparison text.
_TAG_PATTERN = re.compile(
    r"<!--.*?-->|<\?.*?\?>|<![A-Za-z][^<>]*>|</?[A-Za-z][^<>]*>",
    flags=re.DOTALL,
)


def _missing(value):
    """Return True for None, non-string, blank, or literal 'NaN'.
    """
    return (
        value is None
        or not isinstance(value, str)
        or value.strip() in {"", NAN}
    )


def clean_narrative_text(value):
    """Clean narrative text by removing published wrappers and noise.
    Args:
        value (object): Raw narrative value. 
    Returns:
        str: Clean lower-case text, or literal "NaN" when missing.
    """
    if _missing(value):
        return NAN

    # decode html
    text = html.unescape(value)
    text = unicodedata.normalize("NFC", text)

    # remove <tag> markup, keeping the human-readable content it wraps
    text = _TAG_PATTERN.sub(" ", text)

    # remove the published bracketed and social markers:
    # [SYSTEM] [CATALOGUE] [VERIFIED_PURCHASE] [SOURCE: ...] [RATING: n/5]
    text = re.sub(r"\[(?:SYSTEM|CATALOGUE|VERIFIED_PURCHASE|SOURCE:[^]]+|RATING:\s*[1-5]/5)\]",
                 " ", text, flags=re.IGNORECASE)
    
    text = re.sub(r"(?:#verified-buyer|@store_support)\b", 
                 " ", text, flags=re.IGNORECASE)
    
    # remove urls
    text = re.sub(r"https?://\S+",
                 " ", text, flags=re.IGNORECASE)
    
    # remove complete emoji sequences while keeping ordinary symbols such as $+=
    text = _EMOJI_SEQUENCE.sub(" ", text)

    # remove the complete review reference wrapper
    text = re.sub(r"\bReference:\s*[HC]ORD[0-9]{6}\s*(?:[/|;]\s*)?SKU:\s*SKU-[A-Z0-9]+\b",
                 " ", text, flags=re.IGNORECASE)
    
    # remove PROMO: and its code
    text = re.sub(r"\bPROMO:\s*B[1-5]SAVE-[0-9]{2}\b", 
                 " ", text, flags=re.IGNORECASE)

    text = " ".join(text.lower().split())
    return text or NAN


def _extract_reference(value, pattern):
    """Extract one bounded ASCII reference and return it in upper case.
    Args:
        value (object): Raw narrative value.
        pattern (str): Regex for the reference format.
    Returns:
        str: Upper-case reference, or literal "NaN" when invalid or absent.
    """
    if _missing(value):
        return NAN

    # No letter, digit, underscore or hyphen may touch either end.
    match = re.search(
        r"(?<![\w-])" + pattern + r"(?![\w-])",
        value,
        flags=re.IGNORECASE,
    )
    if match is None:
        return NAN

    # Published reference formats are ASCII; reject Unicode look-alikes.
    token = match.group(0)
    if not token.isascii():
        return NAN

    return token.upper()


def extract_order_reference(value):
    """Extract a valid HORD/CORD order reference from raw text.
    Args:
        value (object): Raw narrative value.
    Returns:
        str: Upper-case order reference, or literal "NaN" when absent.
    """
    return _extract_reference(value, r"[HC]ORD\d{6}")


def extract_product_sku(value):
    """Extract a valid product SKU from raw text.
    Args:
        value (object): Raw narrative value.
    Returns:
        str: Upper-case product SKU, or literal "NaN" when absent.
    """
    return _extract_reference(value, r"SKU-[A-Z0-9]+")


def extract_promo_code(value):
    """Extract a valid promotion code from raw text.
    Args:
        value (object): Raw narrative value
    Returns:
        str: Upper-case promotion code, or literal "NaN" when absent.
    """
    return _extract_reference(value, r"B[1-5]SAVE-\d{2}")

def build_latin_analysis(value):
    """Build a Latin-script analysis value from cleaned narrative text.
    Args:
        value (object): Cleaned narrative value.
    Returns:
        str: Text without non-Latin letters, or literal "NaN" if none remain.
    """
    if _missing(value):
        return NAN

    text = unicodedata.normalize("NFC", value)

    # Keep Latin letters (including diacritics) and replace other-script letters with spaces.
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
    Args:
        value (object): Cleaned narrative value.
    Returns:
        bool: True if a non-Latin letter exists; otherwise False.
    """
    if _missing(value):
        return False

    # Ignore numbers and punctuation; only letters can identify a script.
    text = unicodedata.normalize("NFC", value)
    for char in text:
        if char.isalpha() and "LATIN" not in unicodedata.name(char, ""):
            return True

    return False
