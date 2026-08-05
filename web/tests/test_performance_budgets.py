"""D7 — recorded performance baselines and enforced budgets (H1927).

VERIFICATION "Performance budgets" sets initial ceilings on the reference host:

* plain representative search — p95 no more than 500 ms
* reader/source lookup — p95 no more than 500 ms
* regex — hard wall-clock deadline 2 s, teardown complete within 500 ms
* application readiness with existing local DBs — no more than 10 s

Two honest limitations, stated rather than papered over:

1. **A CI runner is not the reference host.** A shared runner's p95 is not a
   production number, so a budget assertion here would be measuring the wrong
   machine. What is enforced here is a *generous* upper bound whose only job is
   to catch an order-of-magnitude regression — a search that went from
   milliseconds to seconds. The real reference-host baseline is captured by
   `scripts/performance_baseline.py` against a live deployment and recorded in
   `docs/PERFORMANCE_BASELINES.md`.
2. **The seeded test corpus is tiny.** Latency here is dominated by framework
   overhead, not by corpus size, so these numbers must never be quoted as
   production performance. They are a regression tripwire.

The document is explicit that a budget must not be silently deleted when a host
cannot meet it. So nothing here is skipped on slowness: the assertion is loose
enough to be meaningful and the measurement is always printed.
"""

import statistics
import time

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# Deliberately far above the reference-host budget — see the module docstring.
# This catches "milliseconds became seconds", not "480 ms became 520 ms".
CI_SEARCH_CEILING_MS = 2000.0
CI_READER_CEILING_MS = 2000.0

# The regex deadline is a CORRECTNESS bound, not a performance one: an
# unbounded catastrophic pattern occupies a worker indefinitely. So this one IS
# enforced at the documented value plus the teardown allowance.
REGEX_DEADLINE_S = 2.0
REGEX_TEARDOWN_ALLOWANCE_S = 0.5

SAMPLES = 20


def _p95(values: list[float]) -> float:
    """95th percentile, nearest-rank — no interpolation on a 20-sample run."""
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round(0.95 * len(ordered))) - 1))
    return ordered[index]


def _report(label: str, samples_ms: list[float], budget_ms: float) -> None:
    print(
        f"\n[perf] {label}: "
        f"p50={statistics.median(samples_ms):.1f}ms "
        f"p95={_p95(samples_ms):.1f}ms "
        f"max={max(samples_ms):.1f}ms "
        f"(reference-host budget {budget_ms:.0f}ms, n={len(samples_ms)})"
    )


@pytest.mark.asyncio
async def test_plain_search_p95_has_not_regressed_by_an_order_of_magnitude():
    transport = ASGITransport(app=app)
    samples: list[float] = []
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # One warm-up: the first request pays template and connection setup.
        await ac.post("/api/search", json={"query": "arjuna", "mode": "plain"})
        for _ in range(SAMPLES):
            started = time.perf_counter()
            resp = await ac.post(
                "/api/search", json={"query": "arjuna", "mode": "plain"}
            )
            samples.append((time.perf_counter() - started) * 1000)
            assert resp.status_code == 200

    _report("plain search", samples, 500.0)
    assert _p95(samples) < CI_SEARCH_CEILING_MS, (
        f"plain-search p95 {_p95(samples):.0f}ms exceeds the regression tripwire "
        f"{CI_SEARCH_CEILING_MS:.0f}ms. The reference-host budget is 500ms; this "
        f"ceiling is deliberately looser because CI is not the reference host, so "
        f"crossing it means something is badly wrong, not merely slow."
    )


@pytest.mark.asyncio
async def test_reader_lookup_p95_has_not_regressed_by_an_order_of_magnitude():
    transport = ASGITransport(app=app)
    samples: list[float] = []
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.get("/sources/source1")
        for _ in range(SAMPLES):
            started = time.perf_counter()
            resp = await ac.get("/sources/source1")
            samples.append((time.perf_counter() - started) * 1000)
            assert resp.status_code in (200, 404)

    _report("reader lookup", samples, 500.0)
    assert _p95(samples) < CI_READER_CEILING_MS


@pytest.mark.asyncio
async def test_catastrophic_regex_respects_the_hard_deadline():
    """This budget IS enforced at its documented value.

    Unlike the latency ceilings, the regex deadline is a correctness property:
    without it a single crafted pattern occupies an application worker for an
    unbounded time. A slow host does not make an unbounded search acceptable.
    """
    evil_pattern = "(a|a)*$"
    transport = ASGITransport(app=app)
    allowance = REGEX_DEADLINE_S + REGEX_TEARDOWN_ALLOWANCE_S

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        started = time.perf_counter()
        resp = await ac.post(
            "/api/search",
            json={"query": evil_pattern, "mode": "regex"},
            timeout=allowance + 10.0,
        )
        elapsed = time.perf_counter() - started

    print(f"\n[perf] catastrophic regex: {elapsed:.3f}s -> HTTP {resp.status_code}")
    assert elapsed <= allowance, (
        f"catastrophic regex occupied the worker for {elapsed:.2f}s, over the "
        f"{REGEX_DEADLINE_S:.0f}s deadline + {REGEX_TEARDOWN_ALLOWANCE_S:.1f}s teardown"
    )


def test_regex_executor_aborts_backtracking_at_engine_level():
    """The deadline, tested where it actually lives — not via the tiny corpus.

    The endpoint test above runs against a 4-line seeded corpus, where a
    catastrophic pattern finishes in milliseconds simply because there is
    nothing to backtrack over. That makes it a route smoke test, not proof the
    bound works. This drives the executor directly with a string engineered to
    blow up `(a+)+$`, so the assertion is about the engine's per-match timeout
    (H1830) and holds whatever the corpus contains.
    """
    # H1926 moved these out of search_service into the executor module that now
    # owns every regex bound.
    from app.services.regex_executor import (
        HAS_TIMEOUT_ENGINE as _HAS_REGEX_TIMEOUT,
        PER_MATCH_TIMEOUT as _REGEX_MATCH_TIMEOUT,
        BoundedRegexExecutor,
        ScanStats,
    )

    if not _HAS_REGEX_TIMEOUT:
        pytest.fail(
            "the timeout-capable `regex` engine is missing, so /api/search?mode=regex "
            "runs unbounded stdlib re — install requirements.txt (H1830)"
        )

    # NOT `(a+)+$`. Measured 05-08-2026: the `regex` engine optimises that
    # textbook ReDoS pattern away — it returns in ~1 ms on 40 chars and never
    # reaches the timeout, so a test built on it asserts nothing. `(a|a)*$` is
    # an alternation the optimiser cannot collapse and does blow up.
    executor = BoundedRegexExecutor.compile_patterns(["(a|a)*$"], True)
    pathological = "a" * 40 + "!"  # matches the prefix, never the anchor
    stats = ScanStats()

    started = time.perf_counter()
    matched = executor.matches(pathological, stats)
    elapsed = time.perf_counter() - started

    print(
        f"\n[perf] regex executor: aborted in {elapsed:.3f}s "
        f"(per-match timeout {_REGEX_MATCH_TIMEOUT}s, timeouts recorded={stats.match_timeouts})"
    )
    assert matched is False
    assert elapsed < _REGEX_MATCH_TIMEOUT + 1.0, (
        f"per-match timeout did not fire: {elapsed:.2f}s on a pattern that should "
        f"abort at {_REGEX_MATCH_TIMEOUT}s"
    )
    assert stats.match_timeouts == 1, (
        "the abandoned row was not counted — a swallowed timeout silently "
        "under-reports matches (H2219)"
    )


@pytest.mark.asyncio
async def test_regex_timeout_response_reveals_nothing_internal():
    """VERIFICATION C3's payload rule, checked from the performance side."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/search", json={"query": "(a|a)*$", "mode": "regex"}, timeout=15.0
        )
    body = resp.text
    for marker in ("Traceback (most recent call last)", "site-packages", '.py", line '):
        assert marker not in body, f"error payload leaks internals: {marker!r}"


@pytest.mark.asyncio
async def test_health_probe_is_fast_enough_for_a_readiness_gate():
    """Readiness is budgeted at 10 s end-to-end; the probe itself must be cheap.

    A health endpoint that takes seconds turns every orchestrator restart into
    a rolling outage, so it gets its own much tighter bound.
    """
    transport = ASGITransport(app=app)
    samples: list[float] = []
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.get("/api/health")
        for _ in range(10):
            started = time.perf_counter()
            resp = await ac.get("/api/health")
            samples.append((time.perf_counter() - started) * 1000)
            assert resp.status_code == 200

    _report("health probe", samples, 1000.0)
    assert _p95(samples) < 1000.0
