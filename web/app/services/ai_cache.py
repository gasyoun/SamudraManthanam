"""AI response cache backed by state.db.

Hash key shape
--------------
The cache key is the SHA-256 of a canonical JSON of
`{system_prompt, user_prompt, model}`. Including BOTH prompts means any
prompt-template tweak in `ai_service` automatically invalidates affected
entries — we don't need a manual cache-version bump on every prompt edit.
Including the model means different models cache separately.

Fail-soft contract
------------------
Every helper here swallows exceptions and returns either `None` (cache
miss) or `False` (write fail). The caller MUST treat the cache as
best-effort and always have a fallback path to the live provider call.
A broken state.db never blocks AI requests.

TTL
---
Entries past `AI_CACHE_TTL_DAYS` are ignored on read. There's no
background sweeper; stale rows just sit until a `VACUUM` or a manual
DELETE. At current scale (one row per unique scholarly query, ~kilobytes
each) this is fine for years.
"""
import hashlib
import json
import logging
import time
from typing import Any

from app.settings import settings
from app.state_db import get_state_db

logger = logging.getLogger(__name__)


def hash_request(system_prompt: str, user_prompt: str, model: str) -> str:
    """Deterministic SHA-256 of the full request triple.

    Canonicalised with `sort_keys=True, ensure_ascii=False` so the same
    semantic input always produces the same hash regardless of JSON
    encoder quirks.
    """
    payload = {"system": system_prompt or "", "user": user_prompt or "", "model": model or ""}
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def cache_get(request_hash: str) -> dict[str, Any] | None:
    """Return the cached response dict for `request_hash` if it exists and
    isn't past TTL. Returns None on any error — caller falls back to live call.
    """
    if not settings.AI_CACHE_ENABLED:
        return None
    db = None
    try:
        db = await get_state_db()
        if db is None:
            return None  # STATE_DB_PATH unset

        cutoff = int(time.time()) - settings.AI_CACHE_TTL_DAYS * 86400
        async with db.execute(
            "SELECT response, model, created_at FROM ai_cache "
            "WHERE request_hash = ? AND created_at >= ?",
            (request_hash, cutoff),
        ) as cursor:
            row = await cursor.fetchone()
        if not row:
            return None
        return json.loads(row[0])
    except Exception:
        logger.exception("ai_cache.get failed; falling back to live provider")
        return None
    finally:
        if db is not None:
            try:
                await db.close()
            except Exception:
                pass


async def cache_put(
    *,
    request_hash: str,
    task: str,
    response: dict[str, Any],
    model: str | None,
    latency_ms: int | None = None,
) -> bool:
    """Persist a provider response under `request_hash`. Returns True on
    success, False on any error. Idempotent via REPLACE — repeat requests
    refresh the row's timestamp, extending its effective TTL."""
    if not settings.AI_CACHE_ENABLED:
        return False
    db = None
    try:
        db = await get_state_db()
        if db is None:
            return False
        payload = json.dumps(response, ensure_ascii=False)
        await db.execute(
            "INSERT OR REPLACE INTO ai_cache "
            "(request_hash, task, response, model, created_at, latency_ms) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (request_hash, task, payload, model, int(time.time()), latency_ms),
        )
        await db.commit()
        return True
    except Exception:
        logger.exception("ai_cache.put failed; provider response not cached")
        return False
    finally:
        if db is not None:
            try:
                await db.close()
            except Exception:
                pass


async def cache_stats() -> dict[str, int]:
    """Return `{total, by_task}` for diagnostics. Safe to call from admin
    routes; never raises."""
    db = None
    try:
        db = await get_state_db()
        if db is None:
            return {"total": 0}
        async with db.execute("SELECT task, COUNT(*) FROM ai_cache GROUP BY task") as cur:
            rows = await cur.fetchall()
        by_task = {r[0]: r[1] for r in rows}
        return {"total": sum(by_task.values()), **{f"task_{k}": v for k, v in by_task.items()}}
    except Exception:
        logger.exception("ai_cache.stats failed")
        return {"total": 0}
    finally:
        if db is not None:
            try:
                await db.close()
            except Exception:
                pass
