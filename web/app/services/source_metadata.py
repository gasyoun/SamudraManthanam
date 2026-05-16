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

# Matches a 4-digit year inside parentheses. Anchored loosely so years can
# appear anywhere in the work-part (usually trailing, but occasionally inline).
_YEAR_IN_PARENS = re.compile(r"\((\d{4})\)")


def parse_source_title(title: str) -> dict:
    """Decompose a corpus source title into name / translator / year fields.

    Returns a dict with keys `name`, `translator`, `year`. Missing fields are
    empty strings. The `name` is always the original `title` — we don't strip
    the year or translator from it because the full string is what users
    expect to see as the page heading.
    """
    if not title:
        return {"name": "", "translator": "", "year": ""}

    work_part, _, translator_part = title.partition(";")

    year_match = _YEAR_IN_PARENS.search(work_part)
    year = year_match.group(1) if year_match else ""

    translator = translator_part.strip()

    return {
        "name": title.strip(),
        "translator": translator,
        "year": year,
    }


def build_source_jsonld(*, source: dict, canonical_url: str, site_name: str) -> dict:
    """Build a schema.org Book entity for a `/sources/{id}` page.

    The Book is the right primary type even for translated material — Google's
    own examples use Book for translated literary works, with `translator` and
    `inLanguage` as siblings.

    We also nest a `WebSite` parent so the SearchAction (declared elsewhere)
    is discoverable from any source page Google indexes.
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
