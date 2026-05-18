"""Tests for the AI response cache (`web/app/services/ai_cache.py`).

Three layers:
1. `hash_request` determinism and field sensitivity.
2. `cache_get` / `cache_put` round-trip against state.db, including TTL
   expiry, REPLACE semantics, and disabled-by-flag fail-soft.
3. End-to-end through `_openai_chat`: first call hits provider, second
   call returns cached result with `cached: True` and zero extra
   provider calls.
"""
import asyncio
import time
from unittest.mock import AsyncMock, patch

import aiosqlite
import httpx
import pytest
import pytest_asyncio

from app.services.ai_cache import (
    cache_get,
    cache_put,
    cache_stats,
    hash_request,
)
from app.services.ai_service import _openai_chat
from app.settings import settings
from app.state_db import init_state_db


# ── Fixture: clean ai_cache table on a real state.db ─────────────────────────

@pytest_asyncio.fixture
async def fresh_ai_cache(tmp_path):
    """Point STATE_DB_PATH at a tmp file, init schema, clear ai_cache.
    Restores the original setting afterwards."""
    old_path = settings.STATE_DB_PATH
    old_enabled = settings.AI_CACHE_ENABLED
    old_ttl = settings.AI_CACHE_TTL_DAYS
    settings.STATE_DB_PATH = str(tmp_path / "state.db")
    settings.AI_CACHE_ENABLED = True
    settings.AI_CACHE_TTL_DAYS = 30

    db = await aiosqlite.connect(settings.STATE_DB_PATH)
    try:
        await init_state_db(db)
    finally:
        await db.close()

    yield

    settings.STATE_DB_PATH = old_path
    settings.AI_CACHE_ENABLED = old_enabled
    settings.AI_CACHE_TTL_DAYS = old_ttl


# ── hash_request ────────────────────────────────────────────────────────────

def test_hash_is_deterministic_for_same_input():
    h1 = hash_request("sys", "user", "gpt-4")
    h2 = hash_request("sys", "user", "gpt-4")
    assert h1 == h2


def test_hash_changes_when_system_prompt_changes():
    h1 = hash_request("sys v1", "user", "gpt-4")
    h2 = hash_request("sys v2", "user", "gpt-4")
    assert h1 != h2


def test_hash_changes_when_user_prompt_changes():
    h1 = hash_request("sys", "user A", "gpt-4")
    h2 = hash_request("sys", "user B", "gpt-4")
    assert h1 != h2


def test_hash_changes_when_model_changes():
    # Different models produce different outputs — must cache separately.
    h1 = hash_request("sys", "user", "gpt-3.5-turbo")
    h2 = hash_request("sys", "user", "gpt-4")
    assert h1 != h2


def test_hash_handles_unicode():
    h = hash_request("Системный промпт", "Пользователь", "gpt-4")
    assert len(h) == 64  # SHA-256 hex


def test_hash_handles_empty_inputs():
    h = hash_request("", "", "")
    assert len(h) == 64
    assert h == hash_request("", "", "")


# ── cache_get / cache_put round-trip ────────────────────────────────────────

@pytest.mark.asyncio
async def test_cache_miss_returns_none(fresh_ai_cache):
    out = await cache_get("nonexistent")
    assert out is None


@pytest.mark.asyncio
async def test_cache_put_then_get_returns_payload(fresh_ai_cache):
    key = hash_request("s", "u", "m")
    payload = {"content": "hello", "model": "m", "usage": {"x": 1}}
    ok = await cache_put(request_hash=key, task="explain", response=payload, model="m", latency_ms=42)
    assert ok is True
    got = await cache_get(key)
    assert got == payload


@pytest.mark.asyncio
async def test_cache_replace_semantics(fresh_ai_cache):
    # Second put with same hash overwrites, doesn't 500.
    key = hash_request("s", "u", "m")
    await cache_put(request_hash=key, task="explain",
                    response={"content": "first"}, model="m")
    await cache_put(request_hash=key, task="explain",
                    response={"content": "second"}, model="m")
    got = await cache_get(key)
    assert got["content"] == "second"


@pytest.mark.asyncio
async def test_cache_ttl_expires_stale_rows(fresh_ai_cache):
    key = hash_request("s", "u", "m")
    await cache_put(request_hash=key, task="explain", response={"content": "x"}, model="m")
    # Force the row's created_at well past the TTL window.
    db = await aiosqlite.connect(settings.STATE_DB_PATH)
    try:
        ancient = int(time.time()) - (settings.AI_CACHE_TTL_DAYS + 1) * 86400
        await db.execute("UPDATE ai_cache SET created_at = ? WHERE request_hash = ?", (ancient, key))
        await db.commit()
    finally:
        await db.close()

    out = await cache_get(key)
    assert out is None  # stale → miss


@pytest.mark.asyncio
async def test_cache_disabled_returns_none_and_does_not_write(fresh_ai_cache):
    settings.AI_CACHE_ENABLED = False
    key = hash_request("s", "u", "m")

    assert await cache_get(key) is None
    ok = await cache_put(request_hash=key, task="explain",
                         response={"content": "x"}, model="m")
    assert ok is False

    # Re-enable and confirm nothing was actually written.
    settings.AI_CACHE_ENABLED = True
    assert await cache_get(key) is None


@pytest.mark.asyncio
async def test_cache_fails_soft_when_state_db_path_unset(monkeypatch):
    # When STATE_DB_PATH is "", get_state_db returns None — cache is a no-op.
    monkeypatch.setattr(settings, "STATE_DB_PATH", "")
    monkeypatch.setattr(settings, "AI_CACHE_ENABLED", True)
    out = await cache_get("any-key")
    assert out is None
    ok = await cache_put(request_hash="any-key", task="t", response={}, model=None)
    assert ok is False


@pytest.mark.asyncio
async def test_cache_stats_counts_by_task(fresh_ai_cache):
    await cache_put(request_hash="a", task="explain", response={"c": "1"}, model="m")
    await cache_put(request_hash="b", task="explain", response={"c": "2"}, model="m")
    await cache_put(request_hash="c", task="compare_translations",
                    response={"c": "3"}, model="m")
    stats = await cache_stats()
    assert stats["total"] == 3
    assert stats.get("task_explain") == 2
    assert stats.get("task_compare_translations") == 1


# ── End-to-end through _openai_chat: hit/miss with mocked provider ──────────

@pytest.mark.asyncio
async def test_openai_chat_writes_to_cache_on_first_call(fresh_ai_cache):
    settings.AI_BASE_URL = "https://api.openai.com/v1"
    settings.AI_API_KEY = "sk-test"
    settings.AI_MODEL = "gpt-4-mock"

    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    mock_response = httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": "AI says hi"}}],
            "model": "gpt-4-mock",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        },
        request=req,
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await _openai_chat("system", "user", task="explain")

    assert result["content"] == "AI says hi"
    assert not result.get("cached")
    # Verify the row landed in the cache.
    key = hash_request("system", "user", "gpt-4-mock")
    cached = await cache_get(key)
    assert cached is not None
    assert cached["content"] == "AI says hi"


@pytest.mark.asyncio
async def test_openai_chat_returns_cached_on_second_call_without_provider_hit(fresh_ai_cache):
    settings.AI_BASE_URL = "https://api.openai.com/v1"
    settings.AI_API_KEY = "sk-test"
    settings.AI_MODEL = "gpt-4-mock"

    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    mock_response = httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": "first call only"}}],
            "model": "gpt-4-mock",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        },
        request=req,
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        # First call — hits provider, writes cache.
        r1 = await _openai_chat("system", "user", task="explain")
        # Second call with identical input — should NOT hit provider.
        r2 = await _openai_chat("system", "user", task="explain")

    assert mock_post.call_count == 1, "second call must use cached response, not re-call provider"
    assert r1["content"] == "first call only"
    assert r2["content"] == "first call only"
    assert r2["cached"] is True
    assert not r1.get("cached")


@pytest.mark.asyncio
async def test_openai_chat_different_prompts_cache_separately(fresh_ai_cache):
    settings.AI_BASE_URL = "https://api.openai.com/v1"
    settings.AI_API_KEY = "sk-test"
    settings.AI_MODEL = "gpt-4-mock"

    def make_response(content):
        req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": content}}], "model": "gpt-4-mock"},
            request=req,
        )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [make_response("A"), make_response("B")]
        r1 = await _openai_chat("sys", "prompt A", task="explain")
        r2 = await _openai_chat("sys", "prompt B", task="explain")

    assert mock_post.call_count == 2, "different prompts must NOT share cache"
    assert r1["content"] == "A"
    assert r2["content"] == "B"


@pytest.mark.asyncio
async def test_openai_chat_error_response_is_not_cached(fresh_ai_cache):
    # Provider 500 → error result → don't poison the cache with the error.
    settings.AI_BASE_URL = "https://api.openai.com/v1"
    settings.AI_API_KEY = "sk-test"
    settings.AI_MODEL = "gpt-4-mock"

    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    err_response = httpx.Response(500, json={"error": "boom"}, request=req)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = err_response
        result = await _openai_chat("system", "user", task="explain")

    assert "error" in result
    # Cache must NOT contain anything for this request.
    key = hash_request("system", "user", "gpt-4-mock")
    assert await cache_get(key) is None
