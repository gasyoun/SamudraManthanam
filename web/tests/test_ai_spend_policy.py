"""H2866: the paid-AI spend policy must reject BEFORE any HTTP is issued.

Every rejection test in this file asserts `mock_post.call_count == 0`. That
assertion is the whole point: a control that rejects *after* the provider
has been called is not a spend control, it is a log line. H2772 already
proved auth and quota; this file proves the preventive half — kill switch,
output bound, model pricing and per-call cost ceiling — and that an allowed
call carries the exact `max_tokens` the ceiling was computed against.

All provider traffic is mocked. Nothing here funds, reads, rotates or
reveals a key, and nothing here mutates quota state.
"""
import json
import os

import aiosqlite
import httpx
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

import app.routers.ai as ai_router
from app.main import app
from app.services.ai_cache import cache_put, hash_request
from app.services.ai_policy import (
    CHARS_PER_TOKEN,
    HARD_MAX_COST_PER_CALL,
    HARD_MAX_OUTPUT_TOKENS,
    estimate_prompt_tokens,
    evaluate_call,
    load_price_table,
    policy_config_report,
)
from app.services.ai_service import _openai_chat
from app.services.session_service import SESSION_HEADER
from app.settings import settings
from app.state_db import init_state_db

client = TestClient(app)

PRICES = {
    "currency": "USD",
    "models": {"gpt-4-mock": {"input_per_1m": 0.15, "output_per_1m": 0.60}},
}


def _mock_ok():
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


@pytest_asyncio.fixture
async def state_db_for_routes(tmp_path):
    """A real state.db so the H2772 auth+quota gate can run for route tests."""
    db_path = str(tmp_path / "state_h2866_routes.db")
    old_path = settings.STATE_DB_PATH
    settings.STATE_DB_PATH = db_path
    async with aiosqlite.connect(db_path) as db:
        await init_state_db(db)
    yield db_path
    settings.STATE_DB_PATH = old_path
    if os.path.exists(db_path):
        os.remove(db_path)


def _auth_headers(email: str) -> dict:
    """Verified session for a route test (same exchange as H2772's suite —
    `verification_token` is only echoed back outside production)."""
    old_env = settings.APP_ENV
    settings.APP_ENV = "development"
    try:
        assert client.post(
            "/api/identity/lead",
            json={"email": email, "consent_data": True, "consent_marketing": False},
        ).status_code == 200
        requested = client.post("/api/identity/verify/request", json={"email": email})
        assert requested.status_code == 202
        confirmed = client.post(
            "/api/identity/verify/confirm", json={"token": requested.json()["verification_token"]}
        )
        assert confirmed.status_code == 200
        return {SESSION_HEADER: confirmed.json()["session_token"]}
    finally:
        settings.APP_ENV = old_env


@pytest.fixture
def policy_env():
    """A fully valid, allowing configuration that each test then breaks in
    exactly one way — so a failure names the single field responsible."""
    saved = {
        n: getattr(settings, n)
        for n in (
            "AI_ENABLED",
            "AI_MODEL",
            "AI_MODEL_PRICES",
            "AI_MAX_OUTPUT_TOKENS",
            "AI_MAX_COST_PER_CALL",
            "AI_COST_CURRENCY",
            "AI_BASE_URL",
            "AI_API_KEY",
            "AI_CACHE_ENABLED",
        )
    }
    settings.AI_ENABLED = True
    settings.AI_MODEL = "gpt-4-mock"
    settings.AI_MODEL_PRICES = json.dumps(PRICES)
    settings.AI_MAX_OUTPUT_TOKENS = 1024
    settings.AI_MAX_COST_PER_CALL = 0.05
    settings.AI_COST_CURRENCY = "USD"
    settings.AI_BASE_URL = "https://api.openai.com/v1"
    settings.AI_API_KEY = "sk-test"
    settings.AI_CACHE_ENABLED = False  # isolate policy from cache by default
    try:
        yield settings
    finally:
        for name, value in saved.items():
            setattr(settings, name, value)


# ── Unit level: evaluate_call issues no HTTP and denies by default ──────────


def test_defaults_are_deny_by_default():
    """Untouched settings — no enable, no prices — must not allow a call.

    This is the property that makes the whole feature safe on the day the
    key is funded: nobody has to remember to turn anything OFF.
    """
    saved = (settings.AI_ENABLED, settings.AI_MODEL_PRICES)
    try:
        settings.AI_ENABLED = False
        settings.AI_MODEL_PRICES = ""
        decision = evaluate_call("sys", "user", model="gpt-4-mock")
    finally:
        settings.AI_ENABLED, settings.AI_MODEL_PRICES = saved
    assert decision.allowed is False
    assert decision.code == "ai_disabled"


def test_kill_switch_denies_even_with_perfect_pricing(policy_env):
    policy_env.AI_ENABLED = False
    decision = evaluate_call("sys", "user")
    assert decision.allowed is False
    assert decision.code == "ai_disabled"


@pytest.mark.parametrize("bad", [0, -1, HARD_MAX_OUTPUT_TOKENS + 1, "many"])
def test_invalid_output_bound_fails_closed(policy_env, bad):
    policy_env.AI_MAX_OUTPUT_TOKENS = bad
    decision = evaluate_call("sys", "user")
    assert decision.allowed is False
    assert decision.code == "invalid_output_bound"


@pytest.mark.parametrize("bad", [0, -0.5, HARD_MAX_COST_PER_CALL + 0.01, "free"])
def test_invalid_cost_ceiling_fails_closed(policy_env, bad):
    policy_env.AI_MAX_COST_PER_CALL = bad
    decision = evaluate_call("sys", "user")
    assert decision.allowed is False
    assert decision.code == "invalid_cost_ceiling"


def test_empty_model_fails_closed(policy_env):
    policy_env.AI_MODEL = "   "
    decision = evaluate_call("sys", "user")
    assert decision.allowed is False
    assert decision.code == "unknown_model"


def test_missing_price_config_fails_closed(policy_env):
    policy_env.AI_MODEL_PRICES = ""
    decision = evaluate_call("sys", "user")
    assert decision.allowed is False
    assert decision.code == "pricing_not_configured"


@pytest.mark.parametrize(
    "raw",
    [
        "{not json",
        "[]",
        json.dumps({"models": {"gpt-4-mock": {"input_per_1m": 1, "output_per_1m": 1}}}),
        json.dumps({"currency": "USD"}),
        json.dumps({"currency": "USD", "models": "nope"}),
    ],
)
def test_malformed_price_config_fails_closed(policy_env, raw):
    policy_env.AI_MODEL_PRICES = raw
    decision = evaluate_call("sys", "user")
    assert decision.allowed is False
    assert decision.code in {"pricing_invalid", "pricing_not_configured"}


def test_currency_mismatch_fails_closed(policy_env):
    policy_env.AI_COST_CURRENCY = "EUR"
    decision = evaluate_call("sys", "user")
    assert decision.allowed is False
    assert decision.code == "currency_mismatch"


def test_unpriced_model_fails_closed(policy_env):
    policy_env.AI_MODEL = "some-brand-new-model"
    decision = evaluate_call("sys", "user")
    assert decision.allowed is False
    assert decision.code == "unknown_model_price"


@pytest.mark.parametrize(
    "entry",
    [
        {"input_per_1m": "cheap", "output_per_1m": 1},
        {"input_per_1m": -1, "output_per_1m": 1},
        {"input_per_1m": 1},
        "0.15",
    ],
)
def test_unusable_price_entry_fails_closed(policy_env, entry):
    policy_env.AI_MODEL_PRICES = json.dumps(
        {"currency": "USD", "models": {"gpt-4-mock": entry}}
    )
    decision = evaluate_call("sys", "user")
    assert decision.allowed is False
    assert decision.code == "unknown_model_price"


def test_over_ceiling_fails_closed(policy_env):
    policy_env.AI_MAX_COST_PER_CALL = 0.0000001
    decision = evaluate_call("sys", "user")
    assert decision.allowed is False
    assert decision.code == "cost_ceiling_exceeded"
    assert decision.details["estimated_cost"] > policy_env.AI_MAX_COST_PER_CALL


def test_expensive_model_over_ceiling_fails_closed(policy_env):
    """A realistic shape of the failure: same prompt, 1000x pricier model."""
    policy_env.AI_MODEL_PRICES = json.dumps(
        {
            "currency": "USD",
            "models": {"gpt-4-mock": {"input_per_1m": 150.0, "output_per_1m": 600.0}},
        }
    )
    decision = evaluate_call("sys", "user" * 1000)
    assert decision.allowed is False
    assert decision.code == "cost_ceiling_exceeded"


def test_allowed_call_reports_bound_and_cost(policy_env):
    decision = evaluate_call("sys", "user")
    assert decision.allowed is True
    assert decision.max_tokens == 1024
    assert decision.currency == "USD"
    # 1024 output tokens at 0.60/1M ≈ 0.000614 — well under the 0.05 ceiling.
    assert 0 < decision.estimated_cost < 0.05


def test_input_token_estimate_is_conservative():
    """Estimation must over-count, never under-count: an under-count means an
    under-priced call slipping past the ceiling."""
    assert estimate_prompt_tokens("a" * 100) == int(100 / CHARS_PER_TOKEN)
    assert CHARS_PER_TOKEN <= 2.0, "raising this weakens every cost estimate"
    assert estimate_prompt_tokens("abc", "de") == estimate_prompt_tokens("abcde")


def test_price_table_parses_documented_shape(policy_env):
    table, err = load_price_table()
    assert err == ""
    assert table["currency"] == "USD"
    assert "gpt-4-mock" in table["models"]


# ── Service level: every rejection costs zero provider calls ────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "break_it,expected_code",
    [
        (lambda s: setattr(s, "AI_ENABLED", False), "ai_disabled"),
        (lambda s: setattr(s, "AI_MAX_OUTPUT_TOKENS", 0), "invalid_output_bound"),
        (lambda s: setattr(s, "AI_MAX_COST_PER_CALL", 0), "invalid_cost_ceiling"),
        (lambda s: setattr(s, "AI_MODEL_PRICES", ""), "pricing_not_configured"),
        (lambda s: setattr(s, "AI_MODEL", "unpriced-model"), "unknown_model_price"),
        (lambda s: setattr(s, "AI_COST_CURRENCY", "EUR"), "currency_mismatch"),
        (
            lambda s: setattr(s, "AI_MAX_COST_PER_CALL", 0.0000001),
            "cost_ceiling_exceeded",
        ),
    ],
)
async def test_openai_chat_rejects_without_touching_provider(
    policy_env, break_it, expected_code
):
    break_it(policy_env)
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_ok()
        result = await _openai_chat("system", "user", task="explain")

    assert mock_post.call_count == 0, "a rejected call must never reach the provider"
    assert result.get("policy_code") == expected_code
    assert "error" in result


@pytest.mark.asyncio
async def test_allowed_call_sends_bounded_max_tokens(policy_env):
    policy_env.AI_MAX_OUTPUT_TOKENS = 256
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_ok()
        result = await _openai_chat("system", "user", task="explain")

    assert result["content"] == "ok"
    assert mock_post.call_count == 1
    sent = mock_post.call_args.kwargs["json"]
    assert sent["max_tokens"] == 256, "the provider payload must carry the bound"
    assert sent["model"] == "gpt-4-mock"


@pytest.mark.asyncio
async def test_disabled_service_does_not_serve_from_cache(policy_env, tmp_path):
    """Kill switch beats the cache. A cached answer is provider-free, but
    serving it from a service the operator has switched OFF would make the
    switch a half-truth — and would keep a withdrawn feature alive."""
    saved_state = settings.STATE_DB_PATH
    settings.STATE_DB_PATH = str(tmp_path / "state.db")
    settings.AI_CACHE_ENABLED = True
    try:
        import aiosqlite

        from app.state_db import init_state_db

        async with aiosqlite.connect(settings.STATE_DB_PATH) as db:
            await init_state_db(db)
        key = hash_request("system", "user", "gpt-4-mock")
        await cache_put(
            request_hash=key, task="explain", response={"content": "cached"}, model="gpt-4-mock"
        )

        policy_env.AI_ENABLED = False
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_ok()
            result = await _openai_chat("system", "user", task="explain")

        assert mock_post.call_count == 0
        assert result.get("policy_code") == "ai_disabled"
        assert "content" not in result
    finally:
        settings.STATE_DB_PATH = saved_state


@pytest.mark.asyncio
async def test_cache_hit_under_allowing_policy_is_provider_free(policy_env, tmp_path):
    saved_state = settings.STATE_DB_PATH
    settings.STATE_DB_PATH = str(tmp_path / "state_hit.db")
    settings.AI_CACHE_ENABLED = True
    try:
        import aiosqlite

        from app.state_db import init_state_db

        async with aiosqlite.connect(settings.STATE_DB_PATH) as db:
            await init_state_db(db)
        key = hash_request("system", "user", "gpt-4-mock")
        await cache_put(
            request_hash=key, task="explain", response={"content": "cached"}, model="gpt-4-mock"
        )

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _mock_ok()
            result = await _openai_chat("system", "user", task="explain")

        assert mock_post.call_count == 0
        assert result["content"] == "cached"
        assert result["cached"] is True
    finally:
        settings.STATE_DB_PATH = saved_state


@pytest.mark.asyncio
async def test_provider_failure_is_an_error_not_a_crash(policy_env):
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(500, json={"error": "boom"}, request=req)
        result = await _openai_chat("system", "user", task="explain")

    assert "error" in result
    assert "policy_code" not in result, "a provider 500 is not a policy rejection"


# ── Route level: rejections surface as clean 503s, quota still first ────────


def test_route_returns_503_when_policy_disabled(policy_env, state_db_for_routes):
    policy_env.AI_ENABLED = False
    headers = _auth_headers("h2866-disabled@example.com")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_ok()
        response = client.post(
            "/api/ai/explain",
            json={"query": "arjuna", "context_lines": ["line 1"]},
            headers=headers,
        )

    assert response.status_code == 503
    assert mock_post.call_count == 0


def test_quota_exhaustion_costs_zero_provider_calls(
    policy_env, state_db_for_routes, monkeypatch
):
    """Quota is checked at the route, before the service — so an exhausted
    user cannot spend even one call, not even the first."""
    monkeypatch.setattr(ai_router, "AI_MONTHLY_CALL_LIMIT", 0)
    headers = _auth_headers("h2866-quota@example.com")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _mock_ok()
        response = client.post(
            "/api/ai/explain",
            json={"query": "arjuna", "context_lines": ["line 1"]},
            headers=headers,
        )

    assert response.status_code == 429
    assert mock_post.call_count == 0


# ── Startup configuration report ───────────────────────────────────────────


def test_config_report_flags_enabled_but_unpriced(policy_env):
    policy_env.AI_MODEL_PRICES = ""
    report = policy_config_report()
    assert report["enabled"] is True
    assert report["problems"] == ["pricing_not_configured"]


def test_config_report_is_quiet_when_disabled(policy_env):
    policy_env.AI_ENABLED = False
    report = policy_config_report()
    assert report["enabled"] is False
    assert report["problems"] == [], "disabled is the safe default, not a problem"


def test_config_report_never_leaks_the_key(policy_env):
    report = policy_config_report()
    assert "sk-test" not in json.dumps(report)
    assert "AI_API_KEY" not in json.dumps(report)
