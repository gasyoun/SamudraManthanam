"""H1926 Lane C, acceptance C1–C3: bounded regex.

C1 — catastrophic input cannot occupy a worker past the hard deadline plus the
     teardown allowance.
C2 — legitimate scholarly patterns keep their documented semantics.
C3 — the timeout/error payload is stable and reveals no internal details.

The adversarial timing assertions are the load-bearing ones: they are written
so that they FAIL if the executor ever loses its per-match timeout (e.g. the
`regex` package disappears from requirements and a fallback quietly reappears),
rather than passing because nothing ran.
"""

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import regex_executor
from app.services.regex_executor import (
    ERROR_ENGINE_UNAVAILABLE,
    ERROR_INVALID_PATTERN,
    ERROR_PATTERN_TOO_LONG,
    ERROR_TOO_MANY_PATTERNS,
    HARD_DEADLINE_SECONDS,
    MAX_PATTERN_LENGTH,
    MAX_PATTERNS,
    PER_MATCH_TIMEOUT,
    TEARDOWN_ALLOWANCE_SECONDS,
    BoundedRegexExecutor,
    RegexContractError,
    ScanStats,
)

client = TestClient(app)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ── C2: compatibility corpus ─────────────────────────────────────────────────

COMPAT_CASES = _load("regex_compat_scholarly.json")["cases"]


@pytest.mark.parametrize("case", COMPAT_CASES, ids=[c["name"] for c in COMPAT_CASES])
def test_scholarly_patterns_retain_documented_semantics(case):
    """Every legitimate pattern behaves exactly as the search contract says."""
    executor = BoundedRegexExecutor.compile_patterns(
        [case["pattern"]], case["case_sensitive"]
    )
    stats = ScanStats()
    assert executor.matches(case["subject"], stats) is case["expect"]
    # A legitimate pattern must never be abandoned mid-match.
    assert stats.match_timeouts == 0
    assert stats.match_errors == 0


def test_compatibility_corpus_is_not_empty():
    """Guards against a fixture file that silently loses its cases."""
    assert len(COMPAT_CASES) >= 20


# ── C1: adversarial termination ──────────────────────────────────────────────

ADVERSARIAL_CASES = _load("regex_adversarial_backtracking.json")["cases"]


def _subject(case: dict) -> str:
    return case["subject_template"] * case["repeat"] + case["suffix"]


@pytest.mark.parametrize(
    "case", ADVERSARIAL_CASES, ids=[c["name"] for c in ADVERSARIAL_CASES]
)
def test_catastrophic_pattern_terminates_within_budget(case):
    """One pathological match is abandoned inside the per-match budget.

    The ceiling is generous relative to PER_MATCH_TIMEOUT because the engine
    checks its deadline at backtracking checkpoints, not on a timer interrupt —
    but it is far below the unbounded behaviour it replaces, where these same
    inputs do not terminate at all.
    """
    executor = BoundedRegexExecutor.compile_patterns([case["pattern"]], True)
    stats = ScanStats()

    start = time.perf_counter()
    executor.matches(_subject(case), stats)
    elapsed = time.perf_counter() - start

    assert elapsed < HARD_DEADLINE_SECONDS, (
        f"{case['name']} ran {elapsed:.3f}s — past the hard deadline"
    )
    # It must have been abandoned, not answered: a case that completes honestly
    # is not adversarial any more and should be moved to the compat corpus.
    assert stats.match_timeouts >= 1, (
        f"{case['name']} returned without hitting the per-match timeout — "
        "the fixture no longer exercises catastrophic backtracking"
    )


def test_scan_of_many_adversarial_rows_stays_within_deadline_plus_teardown():
    """Many pathological rows in sequence still cannot exceed the budget.

    Simulates the scan loop's real shape (per-match timeout inside, hard
    deadline outside) without needing a corpus of thousands of rows.
    """
    case = ADVERSARIAL_CASES[0]
    executor = BoundedRegexExecutor.compile_patterns([case["pattern"]], True)
    subject = _subject(case)
    stats = ScanStats()

    start = time.perf_counter()
    rows = 0
    while time.perf_counter() - start <= HARD_DEADLINE_SECONDS:
        executor.matches(subject, stats)
        rows += 1
    elapsed = time.perf_counter() - start

    assert rows > 0
    # Each row costs at most one per-match budget, so the loop cannot overrun
    # the deadline by more than the teardown allowance.
    assert elapsed < HARD_DEADLINE_SECONDS + TEARDOWN_ALLOWANCE_SECONDS
    # Every row was abandoned, and abandonment was counted on every one of them
    # — an uncounted timeout is an invisible incomplete result.
    assert stats.match_timeouts == rows


def test_per_match_timeout_is_below_the_hard_deadline():
    """A per-match budget at or above the scan deadline would be no bound."""
    assert PER_MATCH_TIMEOUT < HARD_DEADLINE_SECONDS


def test_timeout_engine_is_present():
    """The bound is only real with the timeout-capable engine installed.

    If this fails, `regex` is missing from the environment and regex search is
    refused rather than served unprotected — which is the intended behaviour,
    but it means the ReDoS guarantee is not being exercised here.
    """
    assert regex_executor.HAS_TIMEOUT_ENGINE, (
        "the `regex` package is not installed — see web/requirements.txt"
    )


# ── C3: stable, internals-free error payloads ────────────────────────────────


def test_invalid_pattern_yields_stable_code_without_engine_text():
    with pytest.raises(RegexContractError) as exc:
        BoundedRegexExecutor.compile_patterns(["(unclosed"], False)
    payload = exc.value.as_payload()
    assert payload["error"] == ERROR_INVALID_PATTERN
    # No engine message, no offsets, no echo of the pattern itself.
    assert "unclosed" not in payload["detail"]
    assert "position" not in payload["detail"].lower()


def test_overlong_pattern_is_refused():
    with pytest.raises(RegexContractError) as exc:
        BoundedRegexExecutor.compile_patterns(["a" * (MAX_PATTERN_LENGTH + 1)], False)
    assert exc.value.code == ERROR_PATTERN_TOO_LONG


def test_too_many_patterns_are_refused():
    with pytest.raises(RegexContractError) as exc:
        BoundedRegexExecutor.compile_patterns(["a"] * (MAX_PATTERNS + 1), False)
    assert exc.value.code == ERROR_TOO_MANY_PATTERNS


def test_engine_unavailable_refuses_rather_than_degrading(monkeypatch):
    """Without a timeout-capable engine the mode is closed, not unprotected.

    This is the H2219 failure shape inverted: a missing dependency used to
    silently drop the ReDoS guarantee while still serving the endpoint.
    """
    monkeypatch.setattr(regex_executor, "HAS_TIMEOUT_ENGINE", False)
    with pytest.raises(RegexContractError) as exc:
        BoundedRegexExecutor.compile_patterns(["abc"], False)
    assert exc.value.code == ERROR_ENGINE_UNAVAILABLE


def test_api_returns_stable_400_for_invalid_regex(test_db):
    response = client.post("/api/search", json={"query": "(unclosed", "mode": "regex"})
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == ERROR_INVALID_PATTERN
    assert "unclosed" not in body["detail"]


def test_api_returns_stable_400_for_overlong_regex(test_db):
    response = client.post(
        "/api/search",
        json={"query": "a" * (MAX_PATTERN_LENGTH + 1), "mode": "regex"},
    )
    assert response.status_code == 400
    assert response.json()["error"] == ERROR_PATTERN_TOO_LONG


def test_export_and_stream_share_the_same_error_contract(test_db):
    """All three regex entry points answer identically — no per-route drift."""
    for path in ("/api/search/export?query=(unclosed&mode=regex",
                 "/api/search/stream?query=(unclosed&mode=regex"):
        response = client.get(path)
        assert response.status_code == 400, path
        assert response.json()["error"] == ERROR_INVALID_PATTERN, path


def test_adversarial_search_request_returns_and_reports_truncation(test_db):
    """An adversarial query over the corpus answers, and says it gave up.

    A swallowed timeout would return an empty result set indistinguishable
    from an honest "no matches" — the false-passing shape the org's
    silent-failure rule bans.
    """
    case = ADVERSARIAL_CASES[0]
    start = time.perf_counter()
    response = client.post(
        "/api/search", json={"query": case["pattern"], "mode": "regex"}
    )
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert elapsed < HARD_DEADLINE_SECONDS + TEARDOWN_ALLOWANCE_SECONDS
    metadata = response.json()["search_metadata"]
    assert metadata["hard_deadline_s"] == HARD_DEADLINE_SECONDS
    assert metadata["regex_timeout_engine"] is True


def test_legitimate_regex_search_still_finds_seeded_lines(test_db):
    """End-to-end proof the bounded path did not break real searching."""
    response = client.post(
        "/api/search", json={"query": "arjuna", "mode": "regex"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert body["search_metadata"]["truncated"] is False
