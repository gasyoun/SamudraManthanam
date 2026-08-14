"""Pretty search IRIs — `/s/Хастинапур` instead of `/search/…` or `?q=%D0%A5…`.

Query-string permalinks percent-encode Cyrillic (ugly, bad for sharing).
Path IRIs stay readable in the address bar. `/s/` is the short share
form; `/search/Хастинапур` 301s onto it. Short source aliases keep
long slugs like `mahabharata-ukazatel-geo` out of the URL.

On the wire the browser may still send UTF-8 percent-encoding; HTML
canonicals and `pushState` emit the Unicode form.

`/q/{ascii-slug}` popular-term landings are a different surface and stay
ASCII-only (see `popular_terms.py`).
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import urlencode

# Short public tokens → corpus slugs. Add a row when a layer is worth sharing.
SOURCE_ALIASES: dict[str, str] = {
    "geo": "mahabharata-ukazatel-geo",
    "imen": "mahabharata-ukazatel-imen",
    "predmet": "mahabharata-ukazatel-predmet",
    "flora": "mahabharata-ukazatel-flora",
    "stati": "mahabharata-stati",
}
SLUG_TO_ALIAS: dict[str, str] = {slug: alias for alias, slug in SOURCE_ALIASES.items()}

_MAX_QUERY = 1000
PRETTY_PREFIX = "/s"


def expand_source_token(token: str) -> str:
    return SOURCE_ALIASES.get(token, token)


def shorten_source(slug: str) -> str:
    return SLUG_TO_ALIAS.get(slug, slug)


def path_segment(text: str) -> str:
    """Strip and drop characters that would break a single path segment."""
    cleaned = text.strip().replace("/", " ").replace("?", " ").replace("#", " ")
    return " ".join(cleaned.split())


def pretty_search_path(
    query: str,
    source_slugs: Optional[list[str]] = None,
) -> str:
    q = path_segment(query)
    if not q:
        return "/search"
    if len(q) > _MAX_QUERY:
        q = q[:_MAX_QUERY]
    if source_slugs and len(source_slugs) == 1:
        return f"{PRETTY_PREFIX}/{shorten_source(source_slugs[0])}/{q}"
    return f"{PRETTY_PREFIX}/{q}"


def pretty_search_url(
    *,
    base: str,
    query: str,
    mode: str = "plain",
    case_sensitive: bool = False,
    whole_word: bool = False,
    source_slugs: Optional[list[str]] = None,
) -> str:
    """Canonical share URL. Pretty path when the extra flags are defaults."""
    root = (base or "").rstrip("/")
    extra: list[tuple[str, str]] = []
    if mode and mode != "plain":
        extra.append(("mode", mode))
    if case_sensitive:
        extra.append(("cs", "1"))
    if whole_word:
        extra.append(("ww", "1"))
    many = bool(source_slugs and len(source_slugs) > 1)
    if extra or many:
        parts: list[tuple[str, str]] = [("q", path_segment(query).lower() or query.strip())]
        parts.extend(extra)
        if source_slugs:
            parts.append(("src", ",".join(sorted(source_slugs))))
        return f"{root}/search?{urlencode(parts)}"
    return f"{root}{pretty_search_path(query, source_slugs)}"


def can_use_pretty_path(
    *,
    query: str,
    mode: str = "plain",
    case_sensitive: bool = False,
    whole_word: bool = False,
    source_slugs: Optional[list[str]] = None,
) -> bool:
    if not path_segment(query):
        return False
    if mode != "plain" or case_sensitive or whole_word:
        return False
    if source_slugs and len(source_slugs) > 1:
        return False
    return True
