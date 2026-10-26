# Eval harness note (H6846)

_Created: 26-10-2026_

`evals/` now carries the repo's first eval scaffold, a deterministic canary
over the committed alignment gold:

- suite manifest: [`evals/manifest.json`](../evals/manifest.json)
- runner: [`evals/run_eval.py`](../evals/run_eval.py) (`--canary` proves the
  grader goes red on a wrong-side id)
- gold: [`web/tests/fixtures/alignment_gold.jsonl`](../web/tests/fixtures/alignment_gold.jsonl)
  — existing committed fixture, not new annotation.

Scope is deliberately narrow: the suite guards canonical-id/locus integrity,
not translation quality. A capability suite over the same corpus needs a
separately pre-registered reference solution and negative class (H6714).

CI: [`.github/workflows/eval-canary.yml`](../.github/workflows/eval-canary.yml)
runs the canary on PRs and pushes that touch `evals/`.

_Dr. Mārcis Gasūns_
