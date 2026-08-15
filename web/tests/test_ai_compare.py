"""Tests for the translation-comparison AI endpoint.

Three layers:
1. `build_compare_prompt` pure helper — prompt shape, HTML stripping,
   role markers, IAST handling.
2. `POST /api/ai/compare-translations` route — validation rules,
   bounds, mocked happy-path, error mapping.
3. Comparison-view template integration — the AI button + hidden
   panel + JSON payload script are present when there are 2+ hits.
"""
import json
import os
import re
from unittest.mock import AsyncMock, patch

import aiosqlite
import httpx
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai_service import build_compare_prompt
from app.services.session_service import SESSION_HEADER
from app.settings import settings
from app.state_db import init_state_db

client = TestClient(app)


@pytest_asyncio.fixture(autouse=True)
async def state_db(tmp_path):
    """/api/ai/compare-translations now resolves a session against state.db
    (H2772) — every route test needs one, even the pre-existing validation
    ones that never touched state.db before."""
    db_path = str(tmp_path / "state_ai_compare.db")
    old_path = settings.STATE_DB_PATH
    settings.STATE_DB_PATH = db_path
    async with aiosqlite.connect(db_path) as db:
        await init_state_db(db)
    yield db_path
    settings.STATE_DB_PATH = old_path
    if os.path.exists(db_path):
        os.remove(db_path)


def _auth_headers(email="ai-compare-tester@example.com") -> dict:
    """Run the real two-step verification loop and return session headers.

    `verification_token` is only echoed back when APP_ENV != "production"
    (identity.py) — force dev mode for the exchange regardless of what an
    earlier test in the same process left `settings.APP_ENV` as.
    """
    old_env = settings.APP_ENV
    settings.APP_ENV = "development"
    try:
        r = client.post(
            "/api/identity/lead",
            json={"email": email, "consent_data": True, "consent_marketing": False},
        )
        assert r.status_code == 200
        requested = client.post("/api/identity/verify/request", json={"email": email})
        assert requested.status_code == 202
        token = requested.json()["verification_token"]
        confirmed = client.post("/api/identity/verify/confirm", json={"token": token})
        assert confirmed.status_code == 200
        return {SESSION_HEADER: confirmed.json()["session_token"]}
    finally:
        settings.APP_ENV = old_env


# ── build_compare_prompt ────────────────────────────────────────────────────

def _sample_translations(n=3):
    return [
        {"label": "Смирнов 1977", "role": "translation",
         "text": "Перевод первый."},
        {"label": "Семенцов 1999", "role": "translation",
         "text": "Перевод второй."},
        {"label": "Рамануджа", "role": "commentary",
         "text": "<p>Комментарий с <b>HTML</b>.</p>"},
    ][:n]


def test_prompt_includes_work_title_and_verse_coord():
    p = build_compare_prompt(
        work_title="Бхагавадгита",
        work_title_iast="Bhagavadgītā",
        chapter=2,
        verse=47,
        iast="karmaṇy evādhikāras te",
        translations=_sample_translations(2),
    )
    assert "Бхагавадгита" in p
    assert "Bhagavadgītā" in p
    assert "2.47" in p


def test_prompt_strips_html_tags_from_translation_text():
    # The commentary entry contains <p> and <b> — must not appear in the
    # prompt sent to the model.
    p = build_compare_prompt(
        work_title="W", work_title_iast="W", chapter=1, verse=1, iast="",
        translations=_sample_translations(3),
    )
    assert "<p>" not in p and "</p>" not in p
    assert "<b>" not in p and "</b>" not in p
    # The plain text survives.
    assert "Комментарий" in p and "HTML" in p


def test_prompt_includes_role_marker_only_for_non_translation_roles():
    p = build_compare_prompt(
        work_title="W", work_title_iast="W", chapter=1, verse=1, iast="",
        translations=_sample_translations(3),
    )
    # Translations don't get a role bracket; commentary does.
    assert "[commentary]" in p
    assert "[translation]" not in p


def test_prompt_includes_iast_line_when_provided():
    p = build_compare_prompt(
        work_title="W", work_title_iast="W", chapter=1, verse=1,
        iast="dharmakṣetre kurukṣetre",
        translations=_sample_translations(2),
    )
    assert "dharmakṣetre" in p


def test_prompt_omits_iast_line_when_blank():
    p = build_compare_prompt(
        work_title="W", work_title_iast="W", chapter=1, verse=1, iast="   ",
        translations=_sample_translations(2),
    )
    assert "Санскрит (IAST)" not in p


def test_prompt_numbers_each_translation_in_order():
    p = build_compare_prompt(
        work_title="W", work_title_iast="W", chapter=1, verse=1, iast="",
        translations=_sample_translations(3),
    )
    assert "1. Смирнов 1977" in p
    assert "2. Семенцов 1999" in p
    assert "3. Рамануджа" in p


# ── POST /api/ai/compare-translations validation ────────────────────────────

def _valid_payload(translations_count=3):
    return {
        "work_title": "Бхагавадгита",
        "work_title_iast": "Bhagavadgītā",
        "chapter": 2,
        "verse": 47,
        "iast": "karmaṇy evādhikāras te",
        "translations": _sample_translations(translations_count),
    }


def test_route_requires_auth():
    """Unauthenticated callers never reach validation or the provider (H2772)."""
    r = client.post("/api/ai/compare-translations", json=_valid_payload())
    assert r.status_code == 401


def test_route_requires_at_least_two_translations():
    # The whole point is comparison — one translation is meaningless.
    bad = _valid_payload(translations_count=1)
    r = client.post("/api/ai/compare-translations", json=bad, headers=_auth_headers())
    assert r.status_code == 422


def test_route_rejects_oversized_translation_text():
    payload = _valid_payload()
    payload["translations"][0]["text"] = "x" * 5000
    r = client.post("/api/ai/compare-translations", json=payload, headers=_auth_headers())
    assert r.status_code == 422


def test_route_rejects_too_many_translations():
    payload = _valid_payload()
    payload["translations"] = [
        {"label": f"L{i}", "role": "translation", "text": "t"}
        for i in range(25)
    ]
    r = client.post("/api/ai/compare-translations", json=payload, headers=_auth_headers())
    assert r.status_code == 422


def test_route_rejects_invalid_chapter_or_verse():
    payload = _valid_payload()
    payload["chapter"] = 0
    r = client.post("/api/ai/compare-translations", json=payload, headers=_auth_headers())
    assert r.status_code == 422


def test_route_rejects_oversized_label():
    payload = _valid_payload()
    payload["translations"][0]["label"] = "x" * 300
    r = client.post("/api/ai/compare-translations", json=payload, headers=_auth_headers())
    assert r.status_code == 422


def test_route_returns_503_when_ai_service_returns_error():
    # No AI_BASE_URL configured in test → ai_service returns error → route 503.
    old = settings.AI_BASE_URL
    settings.AI_BASE_URL = ""
    try:
        r = client.post(
            "/api/ai/compare-translations", json=_valid_payload(), headers=_auth_headers()
        )
        assert r.status_code == 503
    finally:
        settings.AI_BASE_URL = old


def test_route_happy_path_with_mocked_provider():
    settings.AI_BASE_URL = "https://api.openai.com/v1"
    settings.AI_API_KEY = "sk-test"

    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    mock_response = httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": "Сравнительный разбор..."}}],
            "model": "gpt-4-mock",
            "usage": {"prompt_tokens": 500, "completion_tokens": 200},
        },
        request=req,
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        r = client.post(
            "/api/ai/compare-translations", json=_valid_payload(), headers=_auth_headers()
        )

    assert r.status_code == 200
    body = r.json()
    assert body["synthesis"] == "Сравнительный разбор..."
    assert body["model"] == "gpt-4-mock"
    # And the provider was called once.
    assert mock_post.call_count == 1


# ── Comparison view template integration ────────────────────────────────────

@pytest_asyncio.fixture
async def two_hit_compare_db():
    """Seed enough sources/lines for the BhG compare view to produce ≥2 hits
    at 1.1, so the AI button + payload render."""
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    fixtures = [
        (1101, "bhagavadgita-smirnov.html",  "Бхагавад-Гита (1977); Б. Л. Смирнов",  "bhagavadgita-smirnov"),
        (1102, "bhagavadgita-erman.html",    "Бхагавад-Гита (2009); В. Г. Эрман",     "bhagavadgita-erman"),
    ]
    for sid, fname, title, slug in fixtures:
        await db.execute(
            "INSERT INTO sources (id, filename, title, sort_order, slug) "
            "VALUES (?, ?, ?, ?, ?)", (sid, fname, title, sid, slug),
        )
    await db.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) "
        "VALUES ('Smirnov v1.1 text', '<div class=\"citation_block\" id=\"1.1\">Smirnov</div>', 1101, 1, '1.1', 'Глава I')"
    )
    await db.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) "
        "VALUES ('Erman v1.1 text', '<div class=\"citation_block\" id=\"1.1\">Erman</div>', 1102, 1, '1.1', 'Глава I')"
    )
    await db.commit()
    await db.close()
    yield
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute("DELETE FROM corpus_lines WHERE source_id IN (1101, 1102)")
    await db.execute("DELETE FROM sources WHERE id IN (1101, 1102)")
    await db.commit()
    await db.close()


def test_compare_view_emits_ai_button_when_multiple_hits(two_hit_compare_db):
    r = client.get("/compare/bhagavadgita/1.1")
    assert r.status_code == 200
    assert 'id="aiCompareBtn"' in r.text
    assert "Сравнить переводы" in r.text


def test_compare_view_emits_ai_payload_script(two_hit_compare_db):
    r = client.get("/compare/bhagavadgita/1.1")
    body = r.text
    # The JSON payload script that the JS handler reads.
    m = re.search(
        r'<script id="aiComparePayload" type="application/json">\s*(.*?)\s*</script>',
        body, re.DOTALL,
    )
    assert m is not None
    payload = json.loads(m.group(1))
    # Shape matches what /api/ai/compare-translations expects.
    assert payload["work_title"] == "Бхагавадгита"
    assert payload["chapter"] == 1
    assert payload["verse"] == 1
    assert len(payload["translations"]) >= 2
    for t in payload["translations"]:
        assert "label" in t and "role" in t and "text" in t


def test_compare_view_emits_hidden_synthesis_section(two_hit_compare_db):
    # The result panel is in markup but hidden until the user clicks the
    # button — avoids visual clutter on page load.
    r = client.get("/compare/bhagavadgita/1.1")
    body = r.text
    m = re.search(r'<section id="aiSyntheses"[^>]*style="([^"]*)"', body)
    assert m is not None
    assert "display:none" in m.group(1)
