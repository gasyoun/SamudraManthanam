"""H2772: auth + hard monthly quota on `/api/ai/*` before the OpenRouter key
is ever funded (issue #307).

Both AI routes used to be reachable with no authentication and no cap — a
dead `AI_API_KEY` answered 503, which looked like a control but was really
just the absence of a bill. This file locks down the two behaviours that
close that gap:

1. Route level — unauthenticated → 401/403, over-quota → 429.
2. Fail-direction level — a storage error on the AI bucket denies the call
   (fails closed); the pre-existing corrections bucket is unchanged and
   still fails open (H1926 C7 — a broken table must never block an
   anonymous reader reporting a typo).
"""
import os

import aiosqlite
import httpx
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

import app.routers.ai as ai_router
from app.main import app
from app.services.rate_limit import check_and_consume
from app.services.session_service import SESSION_HEADER
from app.settings import settings
from app.state_db import init_state_db

client = TestClient(app)


@pytest_asyncio.fixture(autouse=True)
async def state_db(tmp_path):
    db_path = str(tmp_path / "state_ai_auth_quota.db")
    old_path = settings.STATE_DB_PATH
    settings.STATE_DB_PATH = db_path
    async with aiosqlite.connect(db_path) as db:
        await init_state_db(db)
    yield db_path
    settings.STATE_DB_PATH = old_path
    if os.path.exists(db_path):
        os.remove(db_path)


def _auth_headers(email="ai-quota-tester@example.com") -> dict:
    """`verification_token` is only echoed back when APP_ENV != "production"
    (identity.py) — force dev mode for the exchange regardless of what an
    earlier test in the same process left `settings.APP_ENV` as."""
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


def _mock_provider_ok():
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    return httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": "ok"}}],
            "model": "gpt-4-mock",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        },
        request=req,
    )


# ── Route level: auth ───────────────────────────────────────────────────────


def test_explain_rejects_unauthenticated_caller():
    r = client.post(
        "/api/ai/explain", json={"query": "arjuna", "context_lines": ["line 1"]}
    )
    assert r.status_code == 401


def test_explain_rejects_bogus_session_token():
    r = client.post(
        "/api/ai/explain",
        json={"query": "arjuna", "context_lines": ["line 1"]},
        headers={SESSION_HEADER: "not-a-real-token"},
    )
    assert r.status_code == 401


def test_compare_translations_rejects_unauthenticated_caller():
    payload = {
        "work_title": "Бхагавадгита",
        "chapter": 1,
        "verse": 1,
        "translations": [
            {"label": "A", "text": "one"},
            {"label": "B", "text": "two"},
        ],
    }
    r = client.post("/api/ai/compare-translations", json=payload)
    assert r.status_code == 401


# ── Route level: hard monthly quota ─────────────────────────────────────────


def test_explain_returns_429_with_retry_after_when_quota_exhausted(
    monkeypatch, ai_policy_allowed
):
    monkeypatch.setattr(ai_router, "AI_MONTHLY_CALL_LIMIT", 1)
    settings.AI_BASE_URL = "https://api.openai.com/v1"
    settings.AI_API_KEY = "sk-test"
    headers = _auth_headers()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_provider_ok()
        first = client.post(
            "/api/ai/explain",
            json={"query": "arjuna", "context_lines": ["line 1"]},
            headers=headers,
        )
        second = client.post(
            "/api/ai/explain",
            json={"query": "arjuna", "context_lines": ["line 1"]},
            headers=headers,
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert "Retry-After" in second.headers
    # The provider must only have been billed once — the point of the quota.
    assert mock_post.call_count == 1


def test_quota_is_scoped_per_session_not_global(monkeypatch, ai_policy_allowed):
    """A second, distinct session must not inherit the first session's
    exhausted bucket — the quota is `key=f"user:{session.user_id}"`."""
    monkeypatch.setattr(ai_router, "AI_MONTHLY_CALL_LIMIT", 1)
    settings.AI_BASE_URL = "https://api.openai.com/v1"
    settings.AI_API_KEY = "sk-test"
    headers_a = _auth_headers("ai-quota-a@example.com")
    headers_b = _auth_headers("ai-quota-b@example.com")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_provider_ok()
        a = client.post(
            "/api/ai/explain",
            json={"query": "x", "context_lines": ["l"]},
            headers=headers_a,
        )
        b = client.post(
            "/api/ai/explain",
            json={"query": "x", "context_lines": ["l"]},
            headers=headers_b,
        )

    assert a.status_code == 200
    assert b.status_code == 200


# ── Fail-direction: AI bucket closed, corrections bucket unchanged (open) ──


@pytest.mark.asyncio
async def test_ai_bucket_fails_closed_on_storage_error(state_db):
    async with aiosqlite.connect(state_db) as db:
        await db.execute("DROP TABLE rate_limits")
        await db.commit()
        decision = await check_and_consume(
            db,
            bucket="ai.call",
            key="user:1",
            limit=1000,
            window_seconds=3600,
            fail_open=False,
        )
    assert decision.allowed is False


@pytest.mark.asyncio
async def test_corrections_bucket_still_fails_open_on_storage_error(state_db):
    """Unchanged pre-H2772 behaviour (H1926 C7) — a broken rate_limits table
    must not block anonymous correction intake. Same helper, default
    fail_open=True, proving the shared default was never flipped."""
    async with aiosqlite.connect(state_db) as db:
        await db.execute("DROP TABLE rate_limits")
        await db.commit()
        decision = await check_and_consume(
            db,
            bucket="corrections.propose",
            key="ip:deadbeef",
            limit=10,
            window_seconds=3600,
        )
    assert decision.allowed is True
