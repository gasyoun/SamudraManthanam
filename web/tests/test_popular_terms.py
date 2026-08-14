"""Tests for `/q/{slug}` popular-query landing pages.

Three layers:
1. Registry integrity (no DB, no HTTP) — slug shape, related-link bidirectionality,
   field presence.
2. HTTP routing — known slug renders, unknown 404s, case-insensitive lookup
   emits the canonical lowercase URL.
3. Template + JSON-LD — definition, related links, DefinedTerm graph.
"""
import json
import re

import aiosqlite
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.popular_terms import POPULAR_TERMS, REFERENCE_WORK_FILENAMES, get_term
from app.routers.popular_terms import _fetch_primary_source_ids
from app.settings import settings

client = TestClient(app)


# ── Registry integrity ───────────────────────────────────────────────────────

def test_every_slug_matches_ascii_lowercase_pattern():
    pattern = re.compile(r"^[a-z0-9-]+$")
    for slug in POPULAR_TERMS:
        assert pattern.match(slug), f"slug {slug!r} is not ASCII-lowercase"


def test_every_entry_has_required_fields():
    for slug, entry in POPULAR_TERMS.items():
        for field in ("term", "iast", "devanagari"):
            assert entry.get(field), f"{slug}: missing required field {field}"


def test_related_slugs_all_resolve_to_real_entries():
    # Catch typos in the `related` cross-link lists.
    for slug, entry in POPULAR_TERMS.items():
        for rel in entry.get("related", []):
            assert rel in POPULAR_TERMS, (
                f"{slug} → related {rel!r} is not a known term"
            )


def test_no_slug_self_references_in_related():
    for slug, entry in POPULAR_TERMS.items():
        assert slug not in entry.get("related", []), (
            f"{slug} lists itself in related"
        )


def test_get_term_case_insensitive():
    # Same entry regardless of input case.
    a = get_term("dharma")
    b = get_term("Dharma")
    c = get_term("DHARMA")
    assert a is not None
    assert a is b is c


def test_get_term_unknown_returns_none():
    assert get_term("not-a-real-term") is None


# ── HTTP routing ─────────────────────────────────────────────────────────────

def test_known_term_renders_200():
    r = client.get("/q/dharma")
    assert r.status_code == 200
    assert "дхарма" in r.text


def test_unknown_term_returns_404():
    r = client.get("/q/not-a-real-term")
    assert r.status_code == 404


def test_uppercase_slug_resolves_but_canonical_is_lowercase():
    r = client.get("/q/DHARMA")
    assert r.status_code == 200
    # Canonical link should point at the lowercased form, not uppercase.
    m = re.search(r'<link rel="canonical" href="([^"]+)"', r.text)
    assert m is not None
    assert "/q/dharma" in m.group(1)
    assert "/q/DHARMA" not in m.group(1)


def test_non_ascii_slug_returns_404():
    # Cyrillic in the URL — we don't accept those, the canonical slug is Latin.
    r = client.get("/q/" + "дхарма")
    # URL has Cyrillic which gets percent-encoded by the client; the route
    # handler should still reject (slug must match _SLUG_PATTERN).
    assert r.status_code == 404


def test_oversized_slug_rejected():
    r = client.get("/q/" + "a" * 200)
    # Either 400 (length-cap) or 404 (no such slug). Both acceptable — both
    # represent rejection.
    assert r.status_code in (400, 404)


def test_punctuation_in_slug_rejected():
    # Defensive: an injected slug like "dharma;DROP" must not match.
    r = client.get("/q/dharma;drop")
    assert r.status_code == 404


# ── Template content ─────────────────────────────────────────────────────────

def test_page_renders_definition_when_present():
    r = client.get("/q/dharma")
    body = r.text
    # The dharma entry has a curated definition.
    assert POPULAR_TERMS["dharma"]["definition"] in body


def test_page_renders_iast_and_devanagari_forms():
    r = client.get("/q/karma")
    body = r.text
    assert "karma" in body          # IAST
    assert "कर्म" in body            # Devanagari


def test_page_renders_related_term_links():
    # dharma → karma, moksha, varna, ashrama
    r = client.get("/q/dharma")
    body = r.text
    for rel in POPULAR_TERMS["dharma"]["related"]:
        assert f'href="/q/{rel}"' in body, f"related link {rel} missing"


def test_page_emits_full_search_link():
    r = client.get("/q/dharma")
    # Pretty IRI — Cyrillic stays readable, no ?q=%D0…
    assert "/s/дхарм" in r.text
    assert "/search?q=" not in r.text


# ── JSON-LD ──────────────────────────────────────────────────────────────────

def test_page_emits_valid_defined_term_jsonld():
    r = client.get("/q/dharma")
    body = r.text
    m = re.search(r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
                  body, re.DOTALL)
    assert m is not None
    data = json.loads(m.group(1))
    assert data["@type"] == "WebPage"
    assert data["mainEntity"]["@type"] == "DefinedTerm"
    assert data["mainEntity"]["name"] == "дхарма"
    # alternateName carries IAST + Devanagari.
    alt = data["mainEntity"]["alternateName"]
    assert "dharma" in alt
    assert "धर्म" in alt


def test_page_emits_canonical_link():
    r = client.get("/q/karma")
    assert 'rel="canonical"' in r.text


# ── Sitemap integration ──────────────────────────────────────────────────────

def test_sitemap_core_includes_all_popular_term_urls():
    # Popular-term URLs live in /sitemap-core.xml after the v1.15.6 split.
    r = client.get("/sitemap-core.xml")
    body = r.text
    for slug in POPULAR_TERMS:
        # Asserting `loc` end-tag to avoid partial matches.
        assert f"/q/{slug}</loc>" in body, f"{slug} missing from sitemap"


# ── Reference-work exclusion (prevent dictionaries from dominating SERPs) ────

def test_reference_works_set_is_non_empty():
    # Safety check: if a future refactor empties this set, landing pages
    # would silently regress to dictionary-dominated results.
    assert len(REFERENCE_WORK_FILENAMES) >= 14


@pytest.mark.asyncio
async def test_fetch_primary_source_ids_excludes_reference_works():
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        # Seed: one primary text + one reference work (both unique IDs).
        await db.execute(
            "INSERT INTO sources (id, filename, title, sort_order) "
            "VALUES (600, 'primary.html', 'Primary', 600)"
        )
        # Use a real dictionary filename from the exclude list.
        await db.execute(
            "INSERT INTO sources (id, filename, title, sort_order) "
            "VALUES (601, 'Словарь Смирнова.txt', 'Dict', 601)"
        )
        await db.commit()

        ids = await _fetch_primary_source_ids(db)
        assert 600 in ids
        assert 601 not in ids
    finally:
        await db.execute("DELETE FROM sources WHERE id IN (600, 601)")
        await db.commit()
        await db.close()
