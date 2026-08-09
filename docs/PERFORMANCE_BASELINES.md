# Performance baselines

_Created: 09-08-2026 · Last updated: 09-08-2026_

Recorded by [`web/scripts/performance_baseline.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/performance_baseline.py)
against a live deployment. Do not hand-edit — re-run the script.

Budgets come from [VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md)
§ Performance budgets. Where a measurement is over budget, the exception is
recorded here and the measured value becomes the baseline to preserve or
improve — the budget is never silently deleted.

## Measurement context

| Field | Value |
|---|---|
| Measured at (UTC) | 2026-08-09T12:46:02+00:00 |
| Python | 3.14.4 |
| Platform | Windows 10 (AMD64) |
| Sources in corpus | 230 |
| Corpus version | 2026.08 |
| Samples per measurement | 25 |

## Results

| Measurement | p50 | p95 | Budget | Verdict |
|---|---|---|---|---|
| `health_p95` | 74.5 ms | 83.8 ms | 1000 ms | ✅ within |
| `plain_search_p95[dharma]` | 226.6 ms | 244.4 ms | 500 ms | ✅ within |
| `plain_search_p95[arjuna]` | 183.4 ms | 230.8 ms | 500 ms | ✅ within |
| `plain_search_p95[yoga]` | 193.6 ms | 221.1 ms | 500 ms | ✅ within |
| `plain_search_p95[karma]` | 215.8 ms | 262.2 ms | 500 ms | ✅ within |
| `plain_search_p95[atman]` | 192.4 ms | 699.6 ms | 500 ms | ⚠️ over — exception recorded |
| `reader_lookup_p95` | 602.0 ms | 634.8 ms | 500 ms | ⚠️ over — exception recorded |
| `catastrophic_regex` | 1670.7 ms | 1670.7 ms | 2000 ms | ✅ within |

## Recorded exceptions

These measurements are over their documented budget. Per VERIFICATION, the
budget is **not** deleted: the measured value below becomes the baseline that
must be preserved or improved, and the exception is recorded here.

| Measurement | Measured p95 | Budget | Over by | Note |
|---|---|---|---|---|
| `plain_search_p95[atman]` | 700 ms | 500 ms | 1.4× | — |
| `reader_lookup_p95` | 635 ms | 500 ms | 1.3× | renders the whole source page for /01_atharvaveda; cost scales with the work's line count, so the first source in sort_order is not the median case |

## Reading these numbers

The p95 figures are single-host, single-client measurements with no concurrent
load — they establish a floor, not a capacity model. A regression against this
baseline is meaningful; an absolute claim about production throughput is not.

`catastrophic_regex` is a single measurement by design: it is a correctness
bound (an unbounded pattern must not occupy a worker), so what matters is that
it terminates within the deadline, not its distribution.

_Dr. Mārcis Gasūns_
