"""Language filter for parallel-content corpus pages.

Many corpus sources (Smirnov BhG, Erman Bhīṣma-parvan, Sürkin Gītagovinda,
etc.) pack BOTH Sanskrit IAST and Russian translation into a single
`citation_block` row, using two sibling divs:

    <div class="chapter_block iast">...IAST...</div>
    <div class="chapter_block translation">...Russian...</div>

This module:

* identifies sources where this parallel structure is actually present
  (`is_parallel_source`);
* and strips one side or the other from `line_html` to render a single-
  language view (`filter_html_to_language`).

Used by `reader.py` to support `?lang=ru` and `?lang=sa` query variants
with reciprocal hreflang alternates. Non-parallel sources (Erman BhG prose,
Ṛgveda, Kāmasūtra, Upaniṣads from Sürkin, dictionaries) get no hreflang and
no language filter — they serve identically regardless of `?lang=`.
"""
import re
from typing import Iterable

# Module-level compiled regexes — pattern equivalent to the one in
# compare_service._IAST_BLOCK by design; kept independent here so callers
# don't reach across service boundaries for shared parsing primitives.
_IAST_BLOCK = re.compile(
    r'<div class="chapter_block iast">.*?</div>', re.DOTALL | re.IGNORECASE
)
_TRANSLATION_BLOCK = re.compile(
    r'<div class="chapter_block translation">.*?</div>', re.DOTALL | re.IGNORECASE
)

# Allowed language codes for `?lang=`. ISO 639-1 'ru' (Russian) and ISO 639-3
# 'sa' (Sanskrit). Anything else is silently treated as "no filter".
ALLOWED_LANGS: frozenset[str] = frozenset({"ru", "sa"})


def normalize_lang(raw: str | None) -> str | None:
    """Lower-case the input and accept only `ru` or `sa`. Unknown/empty
    values return None — keeps invalid query params from leaking into
    canonical URLs and hreflang alternates."""
    if not raw:
        return None
    candidate = raw.strip().lower()
    return candidate if candidate in ALLOWED_LANGS else None


def filter_html_to_language(line_html: str, lang: str | None) -> str:
    """Strip the OTHER language's `chapter_block` from a corpus line.

    `lang="sa"` → drop the translation div (keep IAST visible).
    `lang="ru"` → drop the IAST div (keep Russian visible).
    `lang=None` or anything else → return `line_html` unchanged.

    The regex is anchored on the `chapter_block iast|translation` class name
    so non-parallel sources (no such divs) pass through unchanged — the
    filter is safe to apply blanket-wise without checking source kind first.
    """
    if not line_html:
        return line_html
    if lang == "sa":
        return _TRANSLATION_BLOCK.sub("", line_html)
    if lang == "ru":
        return _IAST_BLOCK.sub("", line_html)
    return line_html


def is_parallel_source(line_htmls: Iterable[str]) -> bool:
    """True if any line carries the `chapter_block iast` marker.

    Caller passes a SAMPLE — typically the first 5–10 lines with non-empty
    `link_id`. A single hit is enough to classify the source as parallel,
    so the iteration short-circuits; passing the full lines list is fine
    but wasteful for big sources.
    """
    return any(_IAST_BLOCK.search(html or "") for html in line_htmls)
