"""Tests for `language_filter` and the `?lang=ru|sa` filter on /sources/{id}.

Three layers:
1. Pure helper tests (filter regex, parallel detection, lang normalisation).
2. HTTP integration on a seeded parallel source: filter strips the right
   blocks, hreflang alternates are emitted, canonical URL reflects the variant.
3. HTTP integration on a NON-parallel source: no hreflang, no filter effect,
   `?lang=` silently no-ops.
"""
import re

import aiosqlite
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.services.language_filter import (
    ALLOWED_LANGS,
    filter_html_to_language,
    is_parallel_source,
    normalize_lang,
)
from app.settings import settings

client = TestClient(app)


# ── normalize_lang ──────────────────────────────────────────────────────────

def test_normalize_lang_accepts_canonical_codes():
    assert normalize_lang("ru") == "ru"
    assert normalize_lang("sa") == "sa"


def test_normalize_lang_is_case_insensitive():
    assert normalize_lang("RU") == "ru"
    assert normalize_lang("Sa") == "sa"


def test_normalize_lang_strips_whitespace():
    assert normalize_lang("  ru  ") == "ru"


def test_normalize_lang_rejects_unknown_codes():
    # Silently → None so a stray param doesn't 4xx the request.
    assert normalize_lang("en") is None
    assert normalize_lang("fr") is None
    assert normalize_lang("") is None
    assert normalize_lang(None) is None


def test_allowed_langs_is_frozenset():
    # Defensive: callers must NOT be able to mutate the public allow-list.
    assert isinstance(ALLOWED_LANGS, frozenset)
    assert ALLOWED_LANGS == frozenset({"ru", "sa"})


# ── filter_html_to_language ─────────────────────────────────────────────────

_PARALLEL_HTML = (
    '<div class="citation_block" id="1.1">'
    '<div class="chapter_block iast">dharmakṣetre kurukṣetre</div>'
    '<div class="chapter_block translation">На поле дхармы, на поле Куру</div>'
    '</div>'
)


def test_filter_sa_keeps_iast_drops_translation():
    out = filter_html_to_language(_PARALLEL_HTML, "sa")
    assert "dharmakṣetre" in out
    assert "На поле дхармы" not in out


def test_filter_ru_keeps_translation_drops_iast():
    out = filter_html_to_language(_PARALLEL_HTML, "ru")
    assert "На поле дхармы" in out
    assert "dharmakṣetre" not in out


def test_filter_none_returns_unchanged():
    assert filter_html_to_language(_PARALLEL_HTML, None) == _PARALLEL_HTML


def test_filter_unknown_lang_returns_unchanged():
    # Defensive — `reader.py` normalises before calling, but the filter
    # itself shouldn't silently strip on unrecognised codes either.
    assert filter_html_to_language(_PARALLEL_HTML, "en") == _PARALLEL_HTML


def test_filter_on_non_parallel_html_passes_through():
    plain = '<div class="citation_block" id="1.1">Plain Russian text only.</div>'
    assert filter_html_to_language(plain, "ru") == plain
    assert filter_html_to_language(plain, "sa") == plain


def test_filter_handles_empty_html():
    assert filter_html_to_language("", "ru") == ""
    assert filter_html_to_language(None, "ru") is None  # type: ignore[arg-type]


# ── is_parallel_source ──────────────────────────────────────────────────────

def test_is_parallel_when_any_line_has_iast_marker():
    htmls = [
        '<div class="citation_block">no markers</div>',
        '<div class="chapter_block iast">foo</div>',
        '<div>plain</div>',
    ]
    assert is_parallel_source(htmls) is True


def test_is_not_parallel_when_no_iast_anywhere():
    htmls = [
        '<div class="citation_block">no markers</div>',
        '<div>plain</div>',
        '<div class="chapter_block translation">Russian only</div>',
    ]
    assert is_parallel_source(htmls) is False


def test_is_parallel_short_circuits_on_first_hit():
    # Generator with side effect — confirms we stop iterating once a marker
    # is found. The third element is a regex bomb that would error if reached.
    def gen():
        yield '<div class="chapter_block iast">found</div>'
        yield "should not be evaluated 1"
        raise AssertionError("iterator advanced past the first hit")

    assert is_parallel_source(gen()) is True


def test_is_not_parallel_for_empty_sample():
    assert is_parallel_source([]) is False
    assert is_parallel_source(["", None]) is False  # type: ignore[list-item]


# ── HTTP integration: parallel source ───────────────────────────────────────

@pytest_asyncio.fixture
async def parallel_source():
    """Seed a source whose lines have both IAST and Russian chapter_block
    divs — the kind that should get hreflang and respond to ?lang=."""
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute(
        "INSERT INTO sources (id, filename, title, sort_order) "
        "VALUES (700, 'parallel-src.html', 'Parallel test source', 700)"
    )
    # 3 lines, all with parallel structure.
    for i, link_id in enumerate(["1.1", "1.2", "1.3"], start=1):
        await db.execute(
            "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) "
            "VALUES (?, ?, 700, ?, ?, 'Глава I')",
            (
                f"sanskrit-{i} russian-{i}",
                f'<div class="citation_block" id="{link_id}">'
                f'<div class="chapter_block iast">sanskrit-{i}</div>'
                f'<div class="chapter_block translation">russian-{i}</div>'
                f'</div>',
                i,
                link_id,
            ),
        )
    await db.commit()
    await db.close()
    yield 700
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute("DELETE FROM corpus_lines WHERE source_id = 700")
    await db.execute("DELETE FROM sources WHERE id = 700")
    await db.commit()
    await db.close()


@pytest_asyncio.fixture
async def non_parallel_source():
    """Seed a source with Russian-only content — hreflang should NOT emit."""
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute(
        "INSERT INTO sources (id, filename, title, sort_order) "
        "VALUES (701, 'rus-only-src.html', 'Russian-only test source', 701)"
    )
    await db.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) "
        "VALUES ('plain russian', '<div class=\"citation_block\" id=\"1.1\">plain russian</div>',"
        " 701, 1, '1.1', '')"
    )
    await db.commit()
    await db.close()
    yield 701
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute("DELETE FROM corpus_lines WHERE source_id = 701")
    await db.execute("DELETE FROM sources WHERE id = 701")
    await db.commit()
    await db.close()


def test_parallel_source_emits_three_hreflang_alternates(parallel_source):
    r = client.get(f"/sources/{parallel_source}")
    body = r.text
    alts = re.findall(
        r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', body,
    )
    hreflangs = {hl for hl, _ in alts}
    assert hreflangs == {"x-default", "ru", "sa"}


def test_parallel_source_hreflang_urls_are_reciprocal(parallel_source):
    # x-default = no lang param; ru = ?lang=ru; sa = ?lang=sa.
    r = client.get(f"/sources/{parallel_source}")
    alts = dict(re.findall(
        r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', r.text,
    ))
    assert alts["x-default"].endswith(f"/sources/{parallel_source}")
    assert alts["ru"].endswith(f"/sources/{parallel_source}?lang=ru")
    assert alts["sa"].endswith(f"/sources/{parallel_source}?lang=sa")


def test_parallel_source_lang_sa_strips_russian_content(parallel_source):
    r = client.get(f"/sources/{parallel_source}?lang=sa")
    body = r.text
    # Sanskrit content survives.
    assert "sanskrit-1" in body
    # Russian translation blocks stripped from the displayed HTML.
    # (We check that no chapter_block translation div remains.)
    assert 'class="chapter_block translation"' not in body


def test_parallel_source_lang_ru_strips_iast_content(parallel_source):
    r = client.get(f"/sources/{parallel_source}?lang=ru")
    body = r.text
    assert "russian-1" in body
    assert 'class="chapter_block iast"' not in body


def test_parallel_source_canonical_reflects_variant(parallel_source):
    r = client.get(f"/sources/{parallel_source}?lang=sa")
    m = re.search(r'<link rel="canonical" href="([^"]+)"', r.text)
    assert m is not None
    assert m.group(1).endswith(f"/sources/{parallel_source}?lang=sa")


def test_parallel_source_unknown_lang_silently_drops_filter(parallel_source):
    # ?lang=fr is unknown — must not 4xx, must not strip content, must not
    # leak into canonical URL.
    r = client.get(f"/sources/{parallel_source}?lang=fr")
    assert r.status_code == 200
    body = r.text
    assert "sanskrit-1" in body  # IAST survives
    assert "russian-1" in body   # Russian survives
    # Canonical does NOT reference fr.
    m = re.search(r'<link rel="canonical" href="([^"]+)"', body)
    assert "fr" not in m.group(1)


def test_parallel_source_jsonld_inlanguage_reflects_filter(parallel_source):
    import json
    r = client.get(f"/sources/{parallel_source}?lang=sa")
    m = re.search(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        r.text, re.DOTALL,
    )
    book = json.loads(m.group(1))
    assert book["inLanguage"] == "sa"


# ── HTTP integration: non-parallel source ───────────────────────────────────

def test_non_parallel_source_omits_hreflang(non_parallel_source):
    r = client.get(f"/sources/{non_parallel_source}")
    assert "hreflang=" not in r.text


def test_non_parallel_source_ignores_lang_param(non_parallel_source):
    # ?lang=sa on a Russian-only source: page serves identically (no filter
    # effect possible) and no hreflang is emitted.
    r = client.get(f"/sources/{non_parallel_source}?lang=sa")
    assert r.status_code == 200
    assert "plain russian" in r.text
    assert "hreflang=" not in r.text


def test_non_parallel_source_canonical_still_includes_lang_when_set(non_parallel_source):
    # Even though hreflang is suppressed, the canonical URL still reflects
    # the request URL when lang is provided — so multiple `?lang=` URLs
    # don't all canonicalise to the same one (which would be a bigger SEO
    # signal than the hreflang omission). Actually, we DO want them to
    # canonicalise together: there's no content difference, so emit the
    # bare canonical. Verify this.
    r = client.get(f"/sources/{non_parallel_source}?lang=sa")
    m = re.search(r'<link rel="canonical" href="([^"]+)"', r.text)
    # Documented behaviour: canonical reflects the requested variant URL
    # regardless of parallel-ness. The hreflang suppression is the signal
    # that says "these variants are equivalent." Mirrors how Wikipedia
    # handles language toggles on un-translated articles.
    assert "lang=sa" in m.group(1)
