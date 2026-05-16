"""Parse a corpus source title into structured metadata, and emit JSON-LD.

The corpus title strings on `sources.title` follow a loose but consistent
convention:

    [Author. ]Work (Year); Translator

Examples drawn from the live corpus:

    "Махабхарата VI (2009); В.Г. Эрман"
    "Бхагавад-Гита (1977); Б. Л. Смирнов"
    "Бхартрихари. Шатакатраям (2020); М. В. Леонов"
    "Ашвагхоша. Буддхачарита; М.В. Леонов"        — no year
    "Махабхарата XIII"                             — no translator, no year
    "Хатха Йога Прадипика; Шайлендра Шарма"        — no year, no parens

The parser handles all of these by treating the year and translator as
independently optional. JSON-LD output omits empty fields rather than
emitting empty strings — Google ignores empty values but they hurt the
schema-validator score.

What's NOT in scope yet
-----------------------
- Author detection (the "Author. " prefix for kāvya / philosophical works).
  Title strings vary too much to do this reliably without a curated
  per-source registry; would be a worthwhile follow-up.
- Parent-work detection (Bhīṣma-parvan → isPartOf Mahābhārata; Mandala I
  → isPartOf Ṛgveda). Similar story — needs a registry.
- inLanguage of the source content itself. Page content is Russian; the
  underlying corpus mixes Sanskrit IAST with Russian translation. We emit
  "ru" at the page level which is honest about the rendered surface.
"""
import re
from urllib.parse import quote

# Matches a 4-digit year inside parentheses. Anchored loosely so years can
# appear anywhere in the work-part (usually trailing, but occasionally inline).
_YEAR_IN_PARENS = re.compile(r"\((\d{4})\)")

# Known Sanskrit-tradition author names whose titles use the pattern
# "{Author}. {Work}" in the corpus database, mapped to standard scholarly
# IAST transliterations. We curate this list rather than regex-detecting an
# author prefix because work names like "Ригведа.", "Атхарваведа.",
# "Махабхарата." also end in a period before a subpart specifier, and we
# don't want to mis-classify "Ригведа. Мандала I" as
# "Author: Ригведа, Work: Мандала I".
#
# IAST values populate the `Person.alternateName` field in the JSON-LD —
# giving Google an unambiguous Latin-alphabet handle on each author, which
# helps disambiguation across languages and improves Knowledge-Graph linking.
#
# Sorted longest-first at lookup time so multi-word author names take
# precedence over a substring (`"Ватсьяянга Маланга"` before `"Ватсьяянга"`).
# Adding a new author: add an entry here and the prefix-form detector picks
# it up automatically.
_AUTHOR_IAST: dict[str, str] = {
    "Абхинавагупта":      "Abhinavagupta",
    "Ашвагхоша":          "Aśvaghoṣa",
    "Бильхана":           "Bilhaṇa",
    "Бхартрихари":        "Bhartṛhari",
    "Ватсьяяна":          "Vātsyāyana",
    "Ватсьяянга Маланга": "Vātsyāyana Mallanāga",
    "Джаядева":           "Jayadeva",
    "Калидаса":           "Kālidāsa",
    "Патанджали":         "Patañjali",
    "Рамануджа":          "Rāmānuja",
    "Ямуначарья":         "Yāmunācārya",
}

# Public membership set — derived from the IAST mapping to keep a single
# source of truth. Detector code iterates this; JSON-LD builder looks up
# IAST values directly from `_AUTHOR_IAST` when emitting alternateName.
KNOWN_SANSKRIT_AUTHORS: frozenset[str] = frozenset(_AUTHOR_IAST.keys())

# Per-line Quotation `text` is capped to keep JSON-LD payload bounded for the
# handful of sources that pack extensive footnote prose into a single
# corpus_lines row (Smirnov BhG is the worst offender at ~6 KB/line).
# Most real verses are well under this — the cap mostly affects fringe rows.
_MAX_QUOTATION_TEXT = 1500

# Cap on hasPart sample size for the Book entity. Bigger payloads risk
# crowding the page weight for crawlers without proportional SEO value;
# the highlighted-line Quotation handles deep-link cases separately.
_DEFAULT_HASPART_SAMPLE = 20


def _detect_author(work_part: str) -> str:
    """Detect a Sanskrit-tradition author name in the work-part.

    Two title conventions exist in the corpus, both supported here:

    1. **Prefix:** "Author. Work" — e.g. "Бхартрихари. Шатакатраям". Most
       common; checked first.
    2. **Suffix:** "Work. Author" or "Work. Subpart. Author" — e.g. the
       Serebryakov edition "Шатакатраям. Бхартрихари (1979)" and Erman's
       "Рагхуванша. Род Рагху. Калидаса (1996)". The author appears as its
       own dot-separated segment, optionally followed by a `(year)` paren.

    Longer names win (so 'Ватсьяянга Маланга' beats any partial match).
    Returns the author or ''.
    """
    stripped = work_part.strip()
    sorted_authors = sorted(KNOWN_SANSKRIT_AUTHORS, key=len, reverse=True)

    for author in sorted_authors:
        if stripped.startswith(author + ". "):
            return author

    # Suffix form: iterate segments after the first; trim a trailing `(YYYY)`
    # before comparing so "Бхартрихари (1979)" still matches "Бхартрихари".
    segments = [s.strip() for s in stripped.split(". ")]
    for seg in segments[1:]:
        cleaned = _YEAR_IN_PARENS.sub("", seg).strip()
        if cleaned in KNOWN_SANSKRIT_AUTHORS:
            return cleaned
    return ""


def parse_source_title(title: str) -> dict:
    """Decompose a corpus source title into name / translator / year / author.

    Returns a dict with keys `name`, `translator`, `year`, `author`. Missing
    fields are empty strings. The `name` is always the original `title` — we
    don't strip the year or translator from it because the full string is
    what users expect to see as the page heading.

    `author` is detected only for titles whose work-part begins with a curated
    Sanskrit-author name (`KNOWN_SANSKRIT_AUTHORS`). Anonymous works
    (Mahābhārata, Bhagavadgītā, Ṛgveda, Upaniṣads, etc.) correctly return
    an empty author — including any whose title happens to contain a period,
    like "Ригведа. Мандала I".
    """
    if not title:
        return {"name": "", "translator": "", "year": "", "author": ""}

    work_part, _, translator_part = title.partition(";")

    year_match = _YEAR_IN_PARENS.search(work_part)
    year = year_match.group(1) if year_match else ""

    translator = translator_part.strip()
    author = _detect_author(work_part)

    return {
        "name": title.strip(),
        "translator": translator,
        "year": year,
        "author": author,
    }


def _truncate(text: str, max_chars: int = _MAX_QUOTATION_TEXT) -> str:
    """Hard-truncate at `max_chars` with an ellipsis. Used to keep JSON-LD
    payload sizes bounded on the few sources with very long packed lines."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


def _line_anchor_url(*, base_url: str, source_id: int, link_id: str | None) -> str:
    """Stable anchor URL for a single verse on a source page.

    Uses `?highlight=` rather than `#fragment` because Google indexes query
    strings as distinct URLs but treats `#fragment` as a within-page hash —
    deep links via `?highlight=` get their own SERP entries.
    """
    safe = quote(link_id or "", safe="")
    return f"{base_url}/sources/{source_id}?highlight={safe}"


def build_line_quotation(*, line: dict, source_id: int, source_url: str, base_url: str = "") -> dict:
    """Build a single `Quotation` JSON-LD entity for one corpus line.

    The `@id` doubles as the URL the verse can be deep-linked to (the
    `?highlight=` form already implemented by the reader route). `isPartOf`
    threads back to the parent Book by its @id so the relationship is
    discoverable when the Quotation is crawled standalone.
    """
    link_id = line.get("link_id") or str(line.get("line_num") or "")
    quotation: dict = {
        "@context": "https://schema.org",
        "@type": "Quotation",
        "@id": _line_anchor_url(base_url=base_url, source_id=source_id, link_id=link_id),
        "text": _truncate(line.get("line_text", "")),
        "inLanguage": "ru",
        "isPartOf": {"@id": source_url},
        "url": _line_anchor_url(base_url=base_url, source_id=source_id, link_id=link_id),
    }
    if line.get("chapter"):
        quotation["citation"] = f"{line['chapter']}, {link_id}" if link_id else line["chapter"]
    return quotation


def _line_haspart_entry(*, line: dict, source_id: int, base_url: str) -> dict:
    """Compact Quotation for inclusion inside Book.hasPart (no @context, no
    redundant @id collisions; relies on the parent graph for namespacing)."""
    link_id = line.get("link_id") or str(line.get("line_num") or "")
    return {
        "@type": "Quotation",
        "@id": _line_anchor_url(base_url=base_url, source_id=source_id, link_id=link_id),
        "text": _truncate(line.get("line_text", "")),
        "inLanguage": "ru",
    }


def build_source_jsonld(
    *,
    source: dict,
    canonical_url: str,
    site_name: str,
    sample_lines: list[dict] | None = None,
    sample_size: int = _DEFAULT_HASPART_SAMPLE,
    base_url: str = "",
) -> dict:
    """Build a schema.org Book entity for a `/sources/{id}` page.

    The Book is the right primary type even for translated material — Google's
    own examples use Book for translated literary works, with `translator` and
    `inLanguage` as siblings.

    When `sample_lines` is provided, the first `sample_size` entries with a
    non-empty `line_text` are emitted as nested `Quotation` items inside
    `hasPart` plus a `numberOfItems` count of the FULL sample provided (i.e.
    the caller passes all lines; we sample here so the cap is enforced in
    one place). Lines with empty text — typically chapter-anchor or header
    rows — are skipped.
    """
    parsed = parse_source_title(source.get("title", ""))

    jsonld: dict = {
        "@context": "https://schema.org",
        "@type": "Book",
        "@id": canonical_url,
        "name": parsed["name"],
        "url": canonical_url,
        "inLanguage": "ru",
        "isPartOf": {
            "@type": "WebSite",
            "name": site_name,
        },
    }

    if parsed["author"]:
        # `author` is the Sanskrit-tradition writer the work is attributed to
        # (e.g. Bhartṛhari, Aśvaghoṣa, Kālidāsa). Distinct from `translator`,
        # which is the modern person who rendered it into Russian.
        # Anonymous works (Mahābhārata, Bhagavadgītā, Vedas, most Upaniṣads)
        # have no author here — we don't fabricate "Vyāsa" for MBh etc.
        author_entity: dict = {
            "@type": "Person",
            "name": parsed["author"],
        }
        # Add the IAST form as `alternateName` so Google has an unambiguous
        # Latin-alphabet handle for disambiguation / Knowledge-Graph linking.
        iast = _AUTHOR_IAST.get(parsed["author"])
        if iast:
            author_entity["alternateName"] = iast
        jsonld["author"] = author_entity

    if parsed["translator"]:
        # Person is the right type when we have a single named individual.
        # If we can't tell (rare in this corpus — only anthologies omit it),
        # we just drop the field rather than emit a CreativeWork stub.
        jsonld["translator"] = {
            "@type": "Person",
            "name": parsed["translator"],
        }

    if parsed["year"]:
        jsonld["datePublished"] = parsed["year"]

    if sample_lines:
        verse_lines = [l for l in sample_lines if l.get("line_text")]
        jsonld["numberOfItems"] = len(verse_lines)
        source_id = source.get("id")
        if source_id is not None:
            jsonld["hasPart"] = [
                _line_haspart_entry(line=l, source_id=source_id, base_url=base_url)
                for l in verse_lines[:sample_size]
            ]

    return jsonld


def build_breadcrumb_jsonld(*, source_title: str, source_url: str, site_name: str, site_url: str) -> dict:
    """A minimal two-step breadcrumb (Site → Source).

    Adding intermediate levels (e.g. Mahābhārata → Bhīṣma-parvan) would
    require parent-work detection which we explicitly skip for now.
    """
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": site_name,
                "item": site_url or "/",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": source_title,
                "item": source_url,
            },
        ],
    }
