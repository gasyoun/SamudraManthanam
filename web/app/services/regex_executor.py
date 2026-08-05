"""Bounded executor for user-supplied regular expressions (H1926, Lane C2).

The public ``/api/search?mode=regex`` boundary accepts arbitrary user patterns,
so it is the one place in this application where a single request can occupy a
worker indefinitely. Catastrophic backtracking (``(a+)+$`` against a long run of
``a``) is not a slow query — it is unbounded CPU inside the event loop, and the
whole-scan wall-clock budget that used to guard it only ran *between* rows, so
it could never interrupt a match already in progress (H1830).

This module is the single place that owns those bounds:

* **Engine.** The third-party ``regex`` package is required, because it is the
  only Python-``re``-compatible engine with a genuine per-match ``timeout=``
  that aborts backtracking *mid-call*. It is a documented superset of ``re``
  syntax, so the scholarly patterns in
  ``tests/fixtures/regex_compat_scholarly.json`` keep their semantics.
* **No unbounded fallback.** When the package is missing the executor refuses
  the mode with a stable error instead of silently degrading to unbounded
  ``re.search`` in the event loop. A refusal is visible and fixable; a
  degradation is neither — that is the silent-failure shape the org's
  false-passing-gate rule exists to prevent.
* **Static caps** on pattern length and pattern count, applied before any
  matching, so a request cannot buy more CPU simply by sending more patterns.
* **A hard request deadline** (:data:`HARD_DEADLINE_SECONDS`) checked between
  rows, on top of the per-match timeout. Per-match bounds one match; the
  deadline bounds the scan.

Every abandoned row is counted and surfaced, never swallowed: a timeout that
silently under-reports matches is indistinguishable from an honest "no hits".
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, List

logger = logging.getLogger(__name__)

try:  # pragma: no cover - the import branch itself is environment-dependent
    import regex as _engine  # type: ignore

    HAS_TIMEOUT_ENGINE = True
except ImportError:  # pragma: no cover - only on a deployment missing the dep
    _engine = None  # type: ignore[assignment]
    HAS_TIMEOUT_ENGINE = False
    logger.warning(
        "regex mode DISABLED: the `regex` package is not installed, so no "
        "per-match timeout is available (H1830/H1926). Install it from "
        "web/requirements.txt to re-enable /api/search?mode=regex."
    )

# ── Contract constants (mirrored in web/SEARCH_CONTRACT.md §3) ────────────────

#: Per-match wall-clock budget, seconds. Bounds one pattern against one line.
PER_MATCH_TIMEOUT = 0.05

#: Hard wall-clock deadline for a whole regex scan, seconds (VERIFICATION
#: budget: 2 s deadline, teardown complete within 500 ms).
HARD_DEADLINE_SECONDS = 2.0

#: Allowance for finishing the in-flight match and closing the cursor after the
#: deadline trips. Deadline + this is the worst-case worker occupancy.
TEARDOWN_ALLOWANCE_SECONDS = 0.5

#: Rows scanned before the scan gives up regardless of elapsed time.
MAX_SCANNED_ROWS = 1_000_000

#: Longest single pattern accepted, characters.
MAX_PATTERN_LENGTH = 512

#: Most patterns accepted in one request (one per input line).
MAX_PATTERNS = 10

#: Stable, internals-free payload for a refused or failed pattern (C3).
ERROR_INVALID_PATTERN = "invalid_regex"
ERROR_PATTERN_TOO_LONG = "regex_too_long"
ERROR_TOO_MANY_PATTERNS = "too_many_regex_patterns"
ERROR_ENGINE_UNAVAILABLE = "regex_unavailable"


class RegexContractError(Exception):
    """A user pattern violates the published contract.

    Carries a stable machine-readable ``code`` and a short human message. It
    deliberately never carries engine text, offsets, or paths — a regex
    compiler error can quote the pattern back and describe internal state, and
    the timeout/error payload is required to reveal no internal details.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_payload(self) -> dict:
        return {"error": self.code, "detail": self.message}


@dataclass
class ScanStats:
    """Counters for one scan. Non-zero abandonment makes results incomplete."""

    scanned_rows: int = 0
    deadline_exceeded: bool = False
    budget_exceeded: bool = False
    match_timeouts: int = 0
    match_errors: int = 0

    def as_metadata(self) -> dict:
        return {
            "scanned_rows": self.scanned_rows,
            # `timeout` is the pre-H1926 field name; kept for response-shape
            # compatibility with existing clients and tests.
            "timeout": self.deadline_exceeded,
            "budget_exceeded": self.budget_exceeded,
            "match_timeouts": self.match_timeouts,
            "match_errors": self.match_errors,
            "regex_timeout_engine": HAS_TIMEOUT_ENGINE,
            "hard_deadline_s": HARD_DEADLINE_SECONDS,
            "truncated": (
                self.deadline_exceeded
                or self.budget_exceeded
                or bool(self.match_timeouts)
            ),
        }


@dataclass
class BoundedRegexExecutor:
    """Compiled user patterns plus the bounds that make them safe to run.

    Construct with :meth:`compile_patterns`; it raises
    :class:`RegexContractError` for anything the contract refuses, so a caller
    can map the failure to a 400/503 before touching the database.
    """

    patterns: List[Any] = field(default_factory=list)
    per_match_timeout: float = PER_MATCH_TIMEOUT

    @classmethod
    def compile_patterns(
        cls, raw_patterns: List[str], case_sensitive: bool
    ) -> "BoundedRegexExecutor":
        if not HAS_TIMEOUT_ENGINE:
            raise RegexContractError(
                ERROR_ENGINE_UNAVAILABLE,
                "Regex search is temporarily unavailable.",
            )

        cleaned = [p.strip() for p in raw_patterns if p.strip()]
        if len(cleaned) > MAX_PATTERNS:
            raise RegexContractError(
                ERROR_TOO_MANY_PATTERNS,
                f"At most {MAX_PATTERNS} regex patterns per search.",
            )

        flags = 0 if case_sensitive else _engine.IGNORECASE
        compiled: List[Any] = []
        for pattern in cleaned:
            if len(pattern) > MAX_PATTERN_LENGTH:
                raise RegexContractError(
                    ERROR_PATTERN_TOO_LONG,
                    f"Regex patterns are limited to {MAX_PATTERN_LENGTH} characters.",
                )
            try:
                compiled.append(_engine.compile(pattern, flags))
            except Exception as exc:  # engine-specific error classes
                # Never echo the engine's message: it quotes the pattern and
                # describes internal parser state (C3).
                logger.info("regex compile rejected: %s", type(exc).__name__)
                raise RegexContractError(
                    ERROR_INVALID_PATTERN, "Invalid regular expression."
                ) from exc

        return cls(patterns=compiled)

    def __bool__(self) -> bool:
        return bool(self.patterns)

    def matches(self, text: str, stats: ScanStats) -> bool:
        """True when any compiled pattern matches ``text`` within its budget.

        A per-match timeout is counted into ``stats`` and treated as a
        non-match so the scan continues; the caller surfaces the count so the
        user can tell "no hits" from "we gave up on N rows".
        """
        if not text:
            return False
        for compiled in self.patterns:
            try:
                if compiled.search(text, timeout=self.per_match_timeout) is not None:
                    return True
            except TimeoutError:
                stats.match_timeouts += 1
            except Exception as exc:
                logger.debug("regex match error: %s", type(exc).__name__)
                stats.match_errors += 1
        return False


def validate_patterns(raw_patterns: List[str], case_sensitive: bool = False) -> None:
    """Compile-and-discard, for routes that validate before dispatching.

    Raises :class:`RegexContractError` exactly as :meth:`compile_patterns` does.
    """
    BoundedRegexExecutor.compile_patterns(raw_patterns, case_sensitive)
