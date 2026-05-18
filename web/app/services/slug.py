"""Stable URL slug derivation for corpus sources.

Replaces the numeric `source_id` in `/sources/{id}` URLs with a derived,
human-readable slug that survives re-ingests (source IDs renumber on
every ingest, slugs don't).

Slug rules
----------
1. Strip the file extension (`.html`, `.htm`, `.txt`, `.xml`).
2. Transliterate Cyrillic to Latin (BGN/PCGN-style table — pragmatic, not
   strict ISO 9; aims for readability over reversibility).
3. Lowercase.
4. Replace any run of non-[a-z0-9_] characters with a single `-`.
5. Strip leading and trailing `-`.

Examples (verified on the live corpus):

    bhagavadgita-smirnov.html        → bhagavadgita-smirnov
    06_mahabharata-bhishmaparva.html → 06_mahabharata-bhishmaparva
    01_rigveda.html                  → 01_rigveda
    Словарь Смирнова.txt             → slovar-smirnova
    Кнауэр.txt                       → knauer
    Эрман-Темкин.txt                 → erman-temkin
    Рамаяна 3. Словарь.txt           → ramayana-3-slovar

Uniqueness
----------
Two filenames could in theory derive the same slug (e.g. distinct Cyrillic
strings that flatten to the same Latin). `make_unique_slug` resolves
collisions by appending `-2`, `-3`, … so callers can guarantee a UNIQUE
index on `sources.slug` will not conflict on insert.
"""
import re

# Cyrillic-to-Latin transliteration table. Lowercase only — callers
# lowercase before lookup. Uppercase variants share the lowercase mapping
# (we lowercase after transliteration, not before, to keep the table simple).
_CYR_TO_LAT: dict[str, str] = {
    "а": "a",  "б": "b",  "в": "v",  "г": "g",  "д": "d",
    "е": "e",  "ё": "yo", "ж": "zh", "з": "z",  "и": "i",
    "й": "y",  "к": "k",  "л": "l",  "м": "m",  "н": "n",
    "о": "o",  "п": "p",  "р": "r",  "с": "s",  "т": "t",
    "у": "u",  "ф": "f",  "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "",
    "э": "e",  "ю": "yu", "я": "ya",
}

# Known corpus extensions stripped during slug derivation.
_EXTENSION_PATTERN = re.compile(r"\.(?:html?|txt|xml)$", re.IGNORECASE)
# Anything that isn't ASCII alnum or underscore becomes a hyphen; underscores
# are preserved because the corpus uses them as natural separators
# (e.g. `01_rigveda`, `yoga-sutry_sharma`).
_SLUG_NORMALIZE = re.compile(r"[^a-z0-9_]+")


def transliterate_cyrillic(text: str) -> str:
    """Apply the Cyrillic→Latin table character by character. ASCII passes
    through unchanged. Non-Cyrillic non-ASCII characters (Devanagari, IAST
    diacritics) also pass through — slug normalisation will dash them later."""
    out = []
    for ch in text:
        out.append(_CYR_TO_LAT.get(ch.lower(), ch))
    return "".join(out)


def derive_slug(filename: str) -> str:
    """Return the URL slug for a corpus filename. See module docstring for
    the algorithm. Returns empty string for empty input."""
    if not filename:
        return ""
    base = _EXTENSION_PATTERN.sub("", filename)
    base = transliterate_cyrillic(base)
    base = base.lower()
    base = _SLUG_NORMALIZE.sub("-", base)
    return base.strip("-")


def make_unique_slug(filename: str, existing: set[str]) -> str:
    """Derive a slug and disambiguate against `existing` by appending
    `-2`, `-3`, … until unique. Does NOT mutate `existing`; caller is
    responsible for adding the returned slug back to the set if more
    insertions follow.

    Edge case: if `derive_slug` returns empty (e.g. filename was just a
    bare extension), we fall back to a `source-` prefix; callers should
    pair this with the source's id or another disambiguator for a sane
    end-user URL.
    """
    base = derive_slug(filename) or "source"
    if base not in existing:
        return base
    n = 2
    while f"{base}-{n}" in existing:
        n += 1
    return f"{base}-{n}"
