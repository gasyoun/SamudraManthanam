"""Fixed-window rate limiting backed by state.db (H1926, C7).

Anonymous correction intake must stay open — a reader who spots a typo should
never need an account to report it — which is exactly why it needs a cap: an
open write endpoint with no cap is a free way to fill the state database.

Deliberately dependency-free and stored in SQLite rather than in a process
dict. The application runs multiple workers, and a per-process counter silently
multiplies the real limit by the worker count — a limit that is not actually
the limit is worse than none, because it reads as protection.

Fixed windows (not a sliding log) keep the write path to one UPSERT and one
SELECT. The known trade-off is that a caller can spend a full quota at the end
of one window and again at the start of the next; for an abuse cap measured in
proposals per hour that burst is acceptable, and it is documented here rather
than discovered later.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass

import aiosqlite

logger = logging.getLogger(__name__)

#: Anonymous correction proposals per window, per client.
ANONYMOUS_CORRECTION_LIMIT = 10

#: Verified-session correction proposals per window (a real account is a
#: stronger signal, so the cap is looser — but it is still a cap).
VERIFIED_CORRECTION_LIMIT = 60

#: Window length, seconds.
CORRECTION_WINDOW_SECONDS = 3600

#: Hard monthly quota for `/api/ai/*` calls, per verified session (H2640
#: §2.4, H2772). This is the only thing standing between a funded
#: `AI_API_KEY` and an unbounded provider bill — the per-call bounds in
#: `app/routers/ai.py` limit the cost of one call, not the number of calls.
AI_MONTHLY_CALL_LIMIT = 1000

#: Fixed window covering "a month" for the AI quota. A 30-day fixed window
#: is deliberately simpler than a calendar-month boundary — see the module
#: docstring's trade-off note, which applies unchanged here.
AI_MONTHLY_WINDOW_SECONDS = 30 * 24 * 3600


@dataclass
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int


def client_fingerprint(client_host: str | None) -> str:
    """A stable, non-reversible per-client bucket key.

    The raw address is never stored: the corrections table already keeps this
    hash for audit, and a rate-limit ledger is not a reason to start retaining
    IP addresses.
    """
    return hashlib.sha256((client_host or "unknown").encode()).hexdigest()[:16]


async def check_and_consume(
    db: aiosqlite.Connection,
    bucket: str,
    key: str,
    limit: int,
    window_seconds: int,
    now: float | None = None,
    fail_open: bool = True,
) -> RateLimitDecision:
    """Consume one unit from ``(bucket, key)``; report whether it was allowed.

    By default fails **open** on a storage error: a broken rate-limit table
    must not take down correction intake, and the failure is logged loudly
    rather than silently degrading to "everything is allowed" with no trace.

    Pass ``fail_open=False`` for a billable bucket (H2772) — there, a storage
    error must deny the call rather than let it through uncounted, because an
    uncounted call still reaches the paid provider.
    """
    now = time.time() if now is None else now
    window_start = int(now // window_seconds) * window_seconds
    reset_at = window_start + window_seconds

    try:
        await db.execute(
            """INSERT INTO rate_limits (bucket, key, window_start, count)
               VALUES (?, ?, ?, 1)
               ON CONFLICT(bucket, key, window_start)
               DO UPDATE SET count = count + 1""",
            (bucket, key, window_start),
        )
        async with db.execute(
            "SELECT count FROM rate_limits WHERE bucket = ? AND key = ? AND window_start = ?",
            (bucket, key, window_start),
        ) as cursor:
            row = await cursor.fetchone()
        count = int(row[0]) if row else 1

        # Opportunistic cleanup of windows nobody can consume from again.
        await db.execute(
            "DELETE FROM rate_limits WHERE window_start < ?",
            (window_start - window_seconds,),
        )
        await db.commit()
    except Exception:
        logger.exception(
            "rate limit check failed for bucket=%s — failing %s",
            bucket,
            "open" if fail_open else "closed",
        )
        if fail_open:
            return RateLimitDecision(True, limit, limit, 0)
        return RateLimitDecision(False, limit, 0, window_seconds)

    allowed = count <= limit
    return RateLimitDecision(
        allowed=allowed,
        limit=limit,
        remaining=max(0, limit - count),
        retry_after_seconds=max(1, int(reset_at - now)),
    )
