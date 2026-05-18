"""Tests for `<xhtml:link>` hreflang alternates in /sitemap-sources.xml.

Behaviour:
- Parallel sources (lines contain `chapter_block iast`) get 3 <url> entries
  (bare + ?lang=ru + ?lang=sa), each carrying the full reciprocal alternate set.
- Non-parallel sources keep their single <url> entry with no <xhtml:link>.
- The xhtml namespace is declared on the urlset element only when at least
  one parallel source exists (no namespace bloat on dictionary-only corpora).
- Well-formed XML guaranteed regardless of fixture state.
"""
import re
import xml.etree.ElementTree as ET

import aiosqlite
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app, _fetch_parallel_source_slugs
from app.settings import settings

client = TestClient(app)

_SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
_XHTML_NS = "http://www.w3.org/1999/xhtml"


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def parallel_source_in_corpus():
    """Insert a parallel source (lines carry `chapter_block iast`). Yields
    its slug — tests assert on slug-based sitemap URLs."""
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute(
        "INSERT INTO sources (id, filename, title, sort_order, slug) "
        "VALUES (800, 'p-src.html', 'Parallel test source', 800, 'p-src')"
    )
    await db.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) "
        "VALUES ('t', '<div class=\"chapter_block iast\">x</div><div class=\"chapter_block translation\">y</div>',"
        " 800, 1, '1.1', '')"
    )
    await db.commit()
    await db.close()
    yield "p-src"
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute("DELETE FROM corpus_lines WHERE source_id = 800")
    await db.execute("DELETE FROM sources WHERE id = 800")
    await db.commit()
    await db.close()


@pytest_asyncio.fixture
async def non_parallel_source_in_corpus():
    """Insert a Russian-only source (no iast marker). Yields slug."""
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute(
        "INSERT INTO sources (id, filename, title, sort_order, slug) "
        "VALUES (801, 'np-src.html', 'Russian-only test source', 801, 'np-src')"
    )
    await db.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) "
        "VALUES ('rus', '<div>plain russian text</div>', 801, 1, '1.1', '')"
    )
    await db.commit()
    await db.close()
    yield "np-src"
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute("DELETE FROM corpus_lines WHERE source_id = 801")
    await db.execute("DELETE FROM sources WHERE id = 801")
    await db.commit()
    await db.close()


# ── _fetch_parallel_source_ids (SQL helper) ─────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_parallel_source_slugs_finds_parallel(parallel_source_in_corpus):
    db = await aiosqlite.connect(settings.DB_PATH)
    try:
        slugs = await _fetch_parallel_source_slugs(db)
    finally:
        await db.close()
    assert parallel_source_in_corpus in slugs


@pytest.mark.asyncio
async def test_fetch_parallel_source_slugs_excludes_non_parallel(non_parallel_source_in_corpus):
    db = await aiosqlite.connect(settings.DB_PATH)
    try:
        slugs = await _fetch_parallel_source_slugs(db)
    finally:
        await db.close()
    assert non_parallel_source_in_corpus not in slugs


# ── HTTP integration: sitemap-sources with xhtml:link ───────────────────────

def test_sitemap_sources_declares_xhtml_namespace_when_parallel_exists(parallel_source_in_corpus):
    r = client.get("/sitemap-sources.xml")
    assert r.status_code == 200
    assert 'xmlns:xhtml="http://www.w3.org/1999/xhtml"' in r.text


def test_sitemap_sources_omits_xhtml_namespace_when_no_parallel_sources():
    # No fixture seeds parallel content (test_db has only sources 1 and 2,
    # both with plain HTML). Namespace should be absent to avoid bloat.
    r = client.get("/sitemap-sources.xml")
    assert 'xmlns:xhtml' not in r.text


def test_sitemap_sources_emits_three_url_entries_per_parallel_source(parallel_source_in_corpus):
    r = client.get("/sitemap-sources.xml")
    body = r.text
    slug = parallel_source_in_corpus
    # Three distinct <loc> values: bare, ?lang=ru, ?lang=sa.
    for loc in (
        f"<loc>/sources/{slug}</loc>",
        f"<loc>/sources/{slug}?lang=ru</loc>",
        f"<loc>/sources/{slug}?lang=sa</loc>",
    ):
        assert loc in body, f"missing <url> for {loc}"


def test_sitemap_sources_non_parallel_source_emits_single_entry(non_parallel_source_in_corpus):
    r = client.get("/sitemap-sources.xml")
    body = r.text
    slug = non_parallel_source_in_corpus
    # Bare URL appears; ?lang= variants do NOT.
    assert f"<loc>/sources/{slug}</loc>" in body
    assert f"/sources/{slug}?lang=ru" not in body
    assert f"/sources/{slug}?lang=sa" not in body


def test_sitemap_sources_parallel_entries_carry_full_alternate_set(parallel_source_in_corpus):
    r = client.get("/sitemap-sources.xml")
    body = r.text
    slug = parallel_source_in_corpus

    # Find each <url> for this source and verify it has all three alternates.
    pattern = re.compile(rf'<url><loc>/sources/{slug}(?:\?lang=(?:ru|sa))?</loc>.*?</url>', re.DOTALL)
    matches = pattern.findall(body)
    assert len(matches) == 3, f"expected 3 <url> entries for slug={slug}, got {len(matches)}"

    expected_alts = (
        f'<xhtml:link rel="alternate" hreflang="x-default" href="/sources/{slug}"/>',
        f'<xhtml:link rel="alternate" hreflang="ru" href="/sources/{slug}?lang=ru"/>',
        f'<xhtml:link rel="alternate" hreflang="sa" href="/sources/{slug}?lang=sa"/>',
    )
    for url_block in matches:
        for alt in expected_alts:
            assert alt in url_block, (
                f"<url> block for slug={slug} missing alternate {alt!r}\nBlock was: {url_block[:300]}"
            )


def test_sitemap_sources_remains_well_formed_xml(parallel_source_in_corpus, non_parallel_source_in_corpus):
    r = client.get("/sitemap-sources.xml")
    # Both parallel and non-parallel sources present in the fixture. The XML
    # must parse cleanly — namespace declaration, multiple url entries,
    # xhtml:link children all need to be valid.
    root = ET.fromstring(r.text)
    # Root is <urlset>.
    assert root.tag == f"{{{_SITEMAP_NS}}}urlset"
    # At least one xhtml:link element appears.
    xhtml_links = root.findall(f".//{{{_XHTML_NS}}}link")
    assert len(xhtml_links) > 0


def test_sitemap_sources_alternates_are_self_referential(parallel_source_in_corpus):
    # Each language variant's <url> entry must list itself among the alternates
    # — Google rejects unilateral hreflang declarations.
    r = client.get("/sitemap-sources.xml")
    body = r.text
    slug = parallel_source_in_corpus

    # For the ?lang=ru variant, the ru alternate must point at it.
    ru_block = re.search(
        rf'<url><loc>/sources/{slug}\?lang=ru</loc>.*?</url>', body, re.DOTALL,
    )
    assert ru_block is not None
    assert f'hreflang="ru" href="/sources/{slug}?lang=ru"' in ru_block.group(0)

    # For the ?lang=sa variant, the sa alternate must point at it.
    sa_block = re.search(
        rf'<url><loc>/sources/{slug}\?lang=sa</loc>.*?</url>', body, re.DOTALL,
    )
    assert sa_block is not None
    assert f'hreflang="sa" href="/sources/{slug}?lang=sa"' in sa_block.group(0)
