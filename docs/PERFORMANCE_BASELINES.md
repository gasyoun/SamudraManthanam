# Performance baselines

_Created: 05-08-2026 · Last updated: 05-08-2026_

Recorded by [`web/scripts/performance_baseline.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/performance_baseline.py)
against a live deployment. Do not hand-edit — re-run the script.

Budgets come from [VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md)
§ Performance budgets. Where a measurement is over budget, the exception is
recorded here and the measured value becomes the baseline to preserve or
improve — the budget is never silently deleted.

## Measurement context

| Field | Value |
|---|---|
| Measured at (UTC) | 2026-08-05T06:25:40+00:00 |
| Python | 3.14.4 |
| Platform | Windows 10 (AMD64) |
| Sources in corpus | 183 |
| Corpus version | v2026.07.15 |
| Samples per measurement | 25 |

## Results

| Measurement | p50 | p95 | Budget | Verdict |
|---|---|---|---|---|
| `health_p95` | 9.7 ms | 32.5 ms | 1000 ms | ✅ within |
| `plain_search_p95[dharma]` | 96.0 ms | 118.7 ms | 500 ms | ✅ within |
| `plain_search_p95[arjuna]` | 45.4 ms | 52.0 ms | 500 ms | ✅ within |
| `plain_search_p95[yoga]` | 54.9 ms | 68.6 ms | 500 ms | ✅ within |
| `plain_search_p95[karma]` | 77.6 ms | 91.0 ms | 500 ms | ✅ within |
| `plain_search_p95[atman]` | 58.3 ms | 67.8 ms | 500 ms | ✅ within |
| `reader_lookup_p95` | 968.3 ms | 1078.6 ms | 500 ms | ⚠️ over — exception recorded |
| `catastrophic_regex` | 3357.5 ms | 3357.5 ms | 2000 ms | ⚠️ over — exception recorded |

## Recorded exceptions

These measurements are over their documented budget. Per VERIFICATION, the
budget is **not** deleted: the measured value below becomes the baseline that
must be preserved or improved, and the exception is recorded here.

| Measurement | Measured p95 | Budget | Over by | Note |
|---|---|---|---|---|
| `reader_lookup_p95` | 1079 ms | 500 ms | 2.2× | renders the whole source page for /slovar-smirnova; cost scales with the work's line count, so the first source in sort_order is not the median case |
| `catastrophic_regex` | 3358 ms | 2000 ms | 1.7× | hard wall-clock deadline (correctness bound, not a latency target). search_service.MAX_TIME is 5.0 s, so the implementation's whole-scan budget was never aligned to this 2 s spec — owned by Lane C2 / H1926 |

## Reading these numbers

The p95 figures are single-host, single-client measurements with no concurrent
load — they establish a floor, not a capacity model. A regression against this
baseline is meaningful; an absolute claim about production throughput is not.

`catastrophic_regex` is a single measurement by design: it is a correctness
bound (an unbounded pattern must not occupy a worker), so what matters is that
it terminates within the deadline, not its distribution.

_Dr. Mārcis Gasūns_
