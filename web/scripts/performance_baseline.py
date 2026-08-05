"""Record a reproducible performance baseline against a live deployment (H1927 D7).

VERIFICATION: "Wave 1 first records a reproducible production-corpus baseline."

`tests/test_performance_budgets.py` runs on a 4-line seeded corpus inside the
test process, which makes it a regression tripwire and nothing more. This
measures the real thing — a running deployment serving the real corpus — so the
budgets in VERIFICATION have an actual number to be compared against.

It reports percentiles and states which budget each one is measured against; it
does not silently pass or fail. Per the document, a host that cannot meet a
ceiling records the exception and preserves its measured baseline rather than
deleting the budget.

Usage
-----
    python web/scripts/performance_baseline.py --base-url http://127.0.0.1:8000
    python web/scripts/performance_baseline.py --base-url ... --markdown docs/PERFORMANCE_BASELINES.md
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deployment_contract_smoke import request  # noqa: E402  (shared HTTP helper)

# Budgets from docs/VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md.
BUDGETS_MS = {
    "plain_search_p95": 500.0,
    "reader_lookup_p95": 500.0,
    "health_p95": 1000.0,
}
REGEX_DEADLINE_S = 2.0

DEFAULT_QUERIES = ["dharma", "arjuna", "yoga", "karma", "atman"]


@dataclass
class Measurement:
    name: str
    samples_ms: list[float] = field(default_factory=list)
    budget_ms: float | None = None
    note: str = ""

    @property
    def p50(self) -> float:
        return statistics.median(self.samples_ms) if self.samples_ms else 0.0

    @property
    def p95(self) -> float:
        if not self.samples_ms:
            return 0.0
        ordered = sorted(self.samples_ms)
        idx = max(0, min(len(ordered) - 1, int(round(0.95 * len(ordered))) - 1))
        return ordered[idx]

    @property
    def within_budget(self) -> bool | None:
        if self.budget_ms is None:
            return None
        return self.p95 <= self.budget_ms


def measure(name, fn, n, budget=None, note="") -> Measurement:
    result = Measurement(name=name, budget_ms=budget, note=note)
    fn()  # warm-up, excluded
    for _ in range(n):
        started = time.perf_counter()
        fn()
        result.samples_ms.append((time.perf_counter() - started) * 1000)
    return result


def run(base: str, samples: int, queries: list[str]) -> tuple[list[Measurement], dict]:
    base = base.rstrip("/")

    health = request(f"{base}/api/health")
    meta = health.json().get("corpus_db", {}) if health.status == 200 else {}
    context = {
        "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "source_count": meta.get("source_count"),
        "corpus_version": meta.get("metadata", {}).get("corpus_version"),
        "samples_per_measurement": samples,
    }

    measurements = [
        measure(
            "health_p95",
            lambda: request(f"{base}/api/health"),
            samples,
            BUDGETS_MS["health_p95"],
            "readiness probe; the 10 s readiness budget covers full startup",
        )
    ]

    for query in queries:
        measurements.append(
            measure(
                f"plain_search_p95[{query}]",
                lambda q=query: request(
                    f"{base}/api/search",
                    method="POST",
                    payload={"mode": "plain", "query": q, "limit": 50},
                ),
                samples,
                BUDGETS_MS["plain_search_p95"],
            )
        )

    listing = request(f"{base}/api/sources")
    slug = None
    if listing.status == 200:
        try:
            rows = listing.json()
            rows = rows if isinstance(rows, list) else rows.get("sources", [])
            slug = next((r.get("slug") for r in rows if r.get("slug")), None)
        except Exception:  # noqa: BLE001
            slug = None
    if slug:
        measurements.append(
            measure(
                "reader_lookup_p95",
                lambda: request(f"{base}/sources/{slug}"),
                samples,
                BUDGETS_MS["reader_lookup_p95"],
                f"renders the whole source page for /{slug}; cost scales with the "
                f"work's line count, so the first source in sort_order is not the "
                f"median case",
            )
        )

    # Regex deadline — a correctness bound, measured once. `(a|a)*$` rather than
    # the textbook `(a+)+$`, which this app's regex engine optimises away.
    started = time.perf_counter()
    request(
        f"{base}/api/search",
        method="POST",
        payload={"mode": "regex", "query": "(a|a)*$", "limit": 50},
        timeout=REGEX_DEADLINE_S + 30,
    )
    regex_elapsed = (time.perf_counter() - started) * 1000
    measurements.append(
        Measurement(
            "catastrophic_regex",
            [regex_elapsed],
            REGEX_DEADLINE_S * 1000,
            "hard wall-clock deadline (correctness bound, not a latency target). "
            "search_service.MAX_TIME is 5.0 s, so the implementation's whole-scan "
            "budget was never aligned to this 2 s spec — owned by Lane C2 / H1926",
        )
    )

    return measurements, context


def render_markdown(measurements: list[Measurement], context: dict) -> str:
    today = datetime.now(timezone.utc).strftime("%d-%m-%Y")
    rows = []
    for m in measurements:
        verdict = (
            "—"
            if m.within_budget is None
            else ("✅ within" if m.within_budget else "⚠️ over — exception recorded")
        )
        budget = f"{m.budget_ms:.0f} ms" if m.budget_ms else "—"
        rows.append(
            f"| `{m.name}` | {m.p50:.1f} ms | {m.p95:.1f} ms | {budget} | {verdict} |"
        )
    table = "\n".join(rows)

    over = [m for m in measurements if m.within_budget is False]
    if over:
        exception_rows = "\n".join(
            f"| `{m.name}` | {m.p95:.0f} ms | {m.budget_ms:.0f} ms | "
            f"{m.p95 / m.budget_ms:.1f}× | {m.note or '—'} |"
            for m in over
        )
        exceptions = f"""
## Recorded exceptions

These measurements are over their documented budget. Per VERIFICATION, the
budget is **not** deleted: the measured value below becomes the baseline that
must be preserved or improved, and the exception is recorded here.

| Measurement | Measured p95 | Budget | Over by | Note |
|---|---|---|---|---|
{exception_rows}
"""
    else:
        exceptions = "\n## Recorded exceptions\n\nNone — every measurement is within budget.\n"

    return f"""# Performance baselines

_Created: {today} · Last updated: {today}_

Recorded by [`web/scripts/performance_baseline.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/performance_baseline.py)
against a live deployment. Do not hand-edit — re-run the script.

Budgets come from [VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md)
§ Performance budgets. Where a measurement is over budget, the exception is
recorded here and the measured value becomes the baseline to preserve or
improve — the budget is never silently deleted.

## Measurement context

| Field | Value |
|---|---|
| Measured at (UTC) | {context.get("measured_at")} |
| Python | {context.get("python")} |
| Platform | {context.get("platform")} |
| Sources in corpus | {context.get("source_count")} |
| Corpus version | {context.get("corpus_version")} |
| Samples per measurement | {context.get("samples_per_measurement")} |

## Results

| Measurement | p50 | p95 | Budget | Verdict |
|---|---|---|---|---|
{table}
{exceptions}
## Reading these numbers

The p95 figures are single-host, single-client measurements with no concurrent
load — they establish a floor, not a capacity model. A regression against this
baseline is meaningful; an absolute claim about production throughput is not.

`catastrophic_regex` is a single measurement by design: it is a correctness
bound (an unbounded pattern must not occupy a worker), so what matters is that
it terminates within the deadline, not its distribution.

_Dr. Mārcis Gasūns_
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--samples", type=int, default=25)
    parser.add_argument("--queries", nargs="*", default=DEFAULT_QUERIES)
    parser.add_argument("--markdown")
    parser.add_argument("--json")
    args = parser.parse_args()

    measurements, context = run(args.base_url, args.samples, args.queries)

    width = max(len(m.name) for m in measurements)
    print(f"\nPerformance baseline — {args.base_url}")
    print(f"corpus: {context.get('source_count')} sources, version {context.get('corpus_version')}")
    print("-" * (width + 52))
    for m in measurements:
        verdict = "" if m.within_budget is None else (" OK" if m.within_budget else " OVER BUDGET")
        budget = f" / budget {m.budget_ms:.0f}ms" if m.budget_ms else ""
        print(f"{m.name:<{width}}  p50={m.p50:8.1f}ms  p95={m.p95:8.1f}ms{budget}{verdict}")
    print("-" * (width + 52))

    if args.markdown:
        Path(args.markdown).write_text(render_markdown(measurements, context), encoding="utf-8")
        print(f"markdown -> {args.markdown}")
    if args.json:
        Path(args.json).write_text(
            json.dumps(
                {
                    "context": context,
                    "measurements": [
                        {
                            "name": m.name,
                            "p50_ms": m.p50,
                            "p95_ms": m.p95,
                            "budget_ms": m.budget_ms,
                            "within_budget": m.within_budget,
                            "note": m.note,
                        }
                        for m in measurements
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"json     -> {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
