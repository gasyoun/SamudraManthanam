"""robots.txt and the sitemap index + three child sitemaps.

Extracted from `app.main` by H1927 / Lane D2. Route paths, XML shape, priority
values and the hreflang alternate rules are unchanged — `app.main` still
re-exports the private helpers that the sitemap tests import directly.
"""

from fastapi import APIRouter
from fastapi.responses import Response

from app.db import get_db
from app.settings import settings

router = APIRouter(tags=["seo"])


@router.get("/robots.txt")
async def robots():
    sitemap_url = (settings.PUBLIC_BASE_URL.rstrip("/") + "/sitemap.xml") if settings.PUBLIC_BASE_URL else "/sitemap.xml"
    content = f"User-agent: *\nDisallow: /api/\nAllow: /\nSitemap: {sitemap_url}\n"
    return Response(content=content, media_type="text/plain")


async def _get_corpus_lastmod(db) -> str:
    """Return the corpus-build date in `YYYY-MM-DD` form for `<lastmod>`,
    or an empty string when `corpus_meta.generated_at` is missing/unparseable.

    `generated_at` is written by `ingest.ingest` as a full ISO timestamp
    (`2026-05-17T12:34:56.789012`); the sitemap only needs the date prefix.
    Date-only is W3C-DTF compliant and sufficient for crawl-freshness
    signalling — Google honours daily granularity for `<lastmod>`.
    """
    try:
        async with db.execute(
            "SELECT value FROM corpus_meta WHERE key = 'generated_at'"
        ) as cursor:
            row = await cursor.fetchone()
        if not row or not row[0]:
            return ""
        # The DB stores ISO 8601; sitemaps spec accepts YYYY-MM-DD. Take
        # the first 10 chars — robust to either '2026-05-17' or full
        # `2026-05-17T12:34:56.789012`.
        candidate = str(row[0])[:10]
        # Sanity-check the shape so a malformed value doesn't make every
        # `<lastmod>` invalid; Google will reject the whole sitemap on
        # malformed dates.
        if len(candidate) == 10 and candidate[4] == "-" and candidate[7] == "-":
            return candidate
        return ""
    except Exception:
        return ""


def _xml_response(content: str):
    """Wrap an XML string in a Response with the correct media type."""
    return Response(content=content, media_type="application/xml")


def _render_urlset(url_entries: list[str], *, include_xhtml: bool = False) -> str:
    """Wrap a list of `<url>…</url>` strings in a sitemap urlset envelope.

    `include_xhtml=True` declares the xhtml namespace on the urlset element,
    which is required when any `<url>` entry inside contains `<xhtml:link>`
    hreflang alternates (Google's preferred sitemap-level multilingual signal).
    """
    xhtml_attr = ' xmlns:xhtml="http://www.w3.org/1999/xhtml"' if include_xhtml else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"{xhtml_attr}>\n'
        + "\n".join(url_entries)
        + "\n</urlset>\n"
    )


def _render_sitemapindex(sitemap_entries: list[str]) -> str:
    """Wrap a list of `<sitemap>…</sitemap>` strings in a sitemapindex envelope."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(sitemap_entries)
        + "\n</sitemapindex>\n"
    )


def _sitemap_base() -> str:
    """XML-escaped `PUBLIC_BASE_URL` (operator-controlled; & must become &amp;)."""
    from xml.sax.saxutils import escape as xml_escape
    raw_base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
    return xml_escape(raw_base)


async def _fetch_source_ids(db) -> list[int]:
    """Legacy: returns numeric IDs. Retained for tests; new code should use
    `_fetch_source_slugs` so the sitemap emits stable URLs."""
    async with db.execute("SELECT id FROM sources ORDER BY sort_order") as cursor:
        return [row[0] for row in await cursor.fetchall()]


async def _fetch_source_slugs(db) -> list[str]:
    """Return slugs of every source in `sort_order`. Skips rows where the
    slug is NULL or empty (shouldn't happen post-migration, but defensive)."""
    async with db.execute(
        "SELECT slug FROM sources WHERE slug IS NOT NULL AND slug != '' "
        "ORDER BY sort_order"
    ) as cursor:
        return [row[0] for row in await cursor.fetchall()]


async def _fetch_parallel_source_slugs(db) -> set[str]:
    """Return slugs of sources whose corpus_lines carry the `chapter_block
    iast` marker — i.e. parallel-content sources that earn hreflang
    alternates in the sitemap.
    """
    try:
        sql = """
            SELECT s.slug FROM sources s
            WHERE s.slug IS NOT NULL AND s.slug != ''
              AND EXISTS (
                SELECT 1 FROM corpus_lines cl
                WHERE cl.source_id = s.id
                  AND cl.line_html LIKE '%chapter_block iast%'
                LIMIT 1
              )
        """
        async with db.execute(sql) as cursor:
            return {row[0] for row in await cursor.fetchall()}
    except Exception:
        return set()


async def _fetch_parallel_source_ids(db) -> set[int]:
    """Return the set of source IDs whose corpus_lines contain at least one
    `chapter_block iast` marker — i.e. sources that have parallel Sanskrit +
    Russian content and therefore deserve hreflang alternates in the sitemap.

    Single SQL pass with EXISTS + LIMIT 1 short-circuit, so per-source work
    stops at the first qualifying line. On the live ~120k-line corpus this
    runs in well under a second; not worth pre-computing a column for now.
    Fails soft to an empty set so the sitemap still serves on errors.
    """
    try:
        sql = """
            SELECT s.id FROM sources s
            WHERE EXISTS (
                SELECT 1 FROM corpus_lines cl
                WHERE cl.source_id = s.id
                  AND cl.line_html LIKE '%chapter_block iast%'
                LIMIT 1
            )
        """
        async with db.execute(sql) as cursor:
            return {row[0] for row in await cursor.fetchall()}
    except Exception:
        return set()


# ──────────────────────────────────────────────────────────────────────────────
# Sitemap index + three child sitemaps.
#
# Why split: the previous flat sitemap reached 1,420 URLs and ~145 KB. Splitting
# into core (~34) / sources (~148) / compare-leaves (~1,238) gives crawlers
# clearer prioritisation signals and keeps the high-value hub pages off the same
# document as the long-tail verse URLs. The robots.txt `Sitemap: /sitemap.xml`
# directive still points at the index — Google transparently follows children.
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/sitemap.xml")
async def sitemap_index():
    """Sitemap index pointing to the three child sitemaps."""
    base = _sitemap_base()
    lastmod = ""
    try:
        db = await get_db(settings.DB_PATH)
        try:
            lastmod = await _get_corpus_lastmod(db)
        finally:
            await db.close()
    except Exception:
        lastmod = ""

    lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    entries = [
        f"  <sitemap><loc>{base}/sitemap-core.xml</loc>{lm}</sitemap>",
        f"  <sitemap><loc>{base}/sitemap-sources.xml</loc>{lm}</sitemap>",
        f"  <sitemap><loc>{base}/sitemap-compare.xml</loc>{lm}</sitemap>",
    ]
    return _xml_response(_render_sitemapindex(entries))


@router.get("/sitemap-core.xml")
async def sitemap_core():
    """High-value hub pages: root + 3 work hubs + 30 popular-query landings."""
    from app.compare_config import WORKS
    from app.popular_terms import POPULAR_TERMS

    base = _sitemap_base()
    lastmod = ""
    try:
        db = await get_db(settings.DB_PATH)
        try:
            lastmod = await _get_corpus_lastmod(db)
        finally:
            await db.close()
    except Exception:
        lastmod = ""

    lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    urls = [f"  <url><loc>{base}/</loc>{lm}<priority>1.0</priority></url>"]
    urls.append(f"  <url><loc>{base}/chronology</loc>{lm}<priority>0.8</priority></url>")
    for work_slug in WORKS:
        urls.append(f"  <url><loc>{base}/compare/{work_slug}</loc>{lm}<priority>0.9</priority></url>")
    for slug in POPULAR_TERMS:
        urls.append(f"  <url><loc>{base}/q/{slug}</loc>{lm}<priority>0.9</priority></url>")
    return _xml_response(_render_urlset(urls))


@router.get("/sitemap-sources.xml")
async def sitemap_sources():
    """One entry per `/sources/{slug}` for non-parallel sources, three entries
    (bare + `?lang=ru` + `?lang=sa`) for parallel sources. Each parallel
    entry carries the full `<xhtml:link>` hreflang alternate set, which is
    Google's preferred sitemap-level signal for multilingual content.
    Slug URLs (not numeric IDs) so the sitemap survives re-ingest renumbering.
    """
    from urllib.parse import quote

    base = _sitemap_base()
    slugs: list[str] = []
    parallel_slugs: set[str] = set()
    lastmod = ""
    try:
        db = await get_db(settings.DB_PATH)
        try:
            slugs = await _fetch_source_slugs(db)
            parallel_slugs = await _fetch_parallel_source_slugs(db)
            lastmod = await _get_corpus_lastmod(db)
        finally:
            await db.close()
    except Exception:
        slugs = []

    lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    urls: list[str] = []
    for slug in slugs:
        # Cyrillic-derived slugs are already ASCII via transliteration, but
        # underscores etc. are URL-safe so `quote` is mostly a no-op here.
        encoded = quote(slug, safe="-_")
        source_url = f"{base}/sources/{encoded}"
        if slug in parallel_slugs:
            # Per Google: each language variant gets its own <url> entry,
            # and each entry repeats the full alternate set (including a
            # self-reference). The bare URL is the x-default.
            alternates = (
                f'<xhtml:link rel="alternate" hreflang="x-default" href="{source_url}"/>'
                f'<xhtml:link rel="alternate" hreflang="ru" href="{source_url}?lang=ru"/>'
                f'<xhtml:link rel="alternate" hreflang="sa" href="{source_url}?lang=sa"/>'
            )
            for variant_url in (source_url, f"{source_url}?lang=ru", f"{source_url}?lang=sa"):
                urls.append(
                    f"  <url><loc>{variant_url}</loc>{lm}<priority>0.8</priority>{alternates}</url>"
                )
        else:
            urls.append(
                f"  <url><loc>{source_url}</loc>{lm}<priority>0.8</priority></url>"
            )

    return _xml_response(_render_urlset(urls, include_xhtml=bool(parallel_slugs)))


@router.get("/sitemap-compare.xml")
async def sitemap_compare():
    """Leaf comparison URLs (~1,238 on the live corpus). Each verse where a
    `/compare/{work}/{ch}.{v}` page would surface at least one hit."""
    from app.compare_config import WORKS
    from app.services.compare_service import enumerate_verses

    base = _sitemap_base()
    work_verses: dict[str, list[tuple[int, int]]] = {}
    lastmod = ""
    try:
        db = await get_db(settings.DB_PATH)
        try:
            for work_slug in WORKS:
                try:
                    work_verses[work_slug] = await enumerate_verses(db, work_slug)
                except Exception:
                    work_verses[work_slug] = []
            lastmod = await _get_corpus_lastmod(db)
        finally:
            await db.close()
    except Exception:
        pass

    lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    urls = [
        f"  <url><loc>{base}/compare/{work_slug}/{ch}.{v}</loc>{lm}<priority>0.7</priority></url>"
        for work_slug, verses in work_verses.items()
        for ch, v in verses
    ]
    return _xml_response(_render_urlset(urls))
