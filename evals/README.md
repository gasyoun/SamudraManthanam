# SamudraManthanam eval harness

_Created: 26-10-2026 · H6846 (eval-harness scaffold rollout)_

Minimal, deterministic eval scaffold over alignment gold this repo already
commits. It creates no new gold and adds no annotation.

## Suite `alignment-locus-gold`

Grades `web/tests/fixtures/alignment_gold.jsonl` — the A-clean,
commentary-bearing fixture the parallel-view tests use — against the corpus
id contract:

- unique `group` per row;
- `cardinality` is `n:m` and the present sides match it (`0:1` monolingual
  rows carry `sa_id: null`, not a fabricated Sanskrit id);
- at least one text fragment and the alignment tag are non-empty;
- every `comm_ids` entry starts with `group + ".comm"`.

This is the MT/corpus-facing canary: a wrong-side or wrong-group id is exactly
the failure that would silently mis-pair translation fragments.

## Run

```sh
python evals/run_eval.py            # gold replay
python evals/run_eval.py --canary   # gold passes AND a mutated id fails
```

`--canary` re-points the first Russian id at the Sanskrit side (`#sa`) and
requires the grader to reject it. Exit code 0 means the gold replay passed (and,
with `--canary`, the mutation was caught).

The same command runs on PRs and pushes touching `evals/` via
`.github/workflows/eval-canary.yml`.

_Dr. Mārcis Gasūns_
