# H2866 — paid-AI spend policy: status and evidence

_Created: 17-08-2026 · Last updated: 17-08-2026_

Executor: **Opus 5 (`claude-opus-5`)**. Handoff:
[H2866 (Opus 5) — Paid-AI kill switch, output and per-call cost ceilings with bypass-proof tests](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2866-Opus_SamudraManthanam_paid-ai-spend-safety_16.08.26.md).
Plan family:
[PLAN](https://github.com/gasyoun/Uprava/blob/main/docs/PLAN_UPRAVA_MAX20_HARD_HANDOFFS_16.08.26.md) ·
[architecture](https://github.com/gasyoun/Uprava/blob/main/docs/ARCHITECTURE_UPRAVA_MAX20_HARD_HANDOFFS.md) ·
[implementation](https://github.com/gasyoun/Uprava/blob/main/docs/IMPLEMENTATION_UPRAVA_MAX20_HARD_HANDOFFS.md) ·
[verification](https://github.com/gasyoun/Uprava/blob/main/docs/VERIFICATION_UPRAVA_MAX20_HARD_HANDOFFS.md).

## 1. Prior-art census — what already existed, and the gap actually built

The architecture doc's verdict for this repo was **PARTIAL**, and the census
confirmed it before a line was written:

| Surface | State before H2866 | Owner |
|---|---|---|
| Paid routes | exactly two — `POST /api/ai/explain`, `POST /api/ai/compare-translations` | [`web/app/routers/ai.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/routers/ai.py) |
| Provider dispatch | exactly one call site, `_openai_chat` — every task already converged there | [`web/app/services/ai_service.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/services/ai_service.py) |
| Session auth | shipped (401 without a session) | H2772 `_require_quota` |
| Monthly quota | shipped, 1 000 calls / 30 days per user, fails **closed** | H2772 + [`rate_limit.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/services/rate_limit.py) |
| Prompt-size bounds | shipped (context lines, per-line and per-field lengths) | H2772 route models |
| Response cache | shipped, fail-soft, keyed on both prompts + model | [`ai_cache.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/services/ai_cache.py) |
| **Kill switch** | **absent** — `AI_ENABLED` existed only as an aspiration in TARGET_ARCHITECTURE §5 | — |
| **Output bound** | **absent** — no `max_tokens` in the payload at all | — |
| **Model pricing** | **absent** | — |
| **Per-call cost ceiling** | **absent** | — |
| **Bypass census** | **absent** — nothing failed when a new paid route skipped the gate | — |

Only the last five rows were built. Auth, quota, input bounds and the cache
were left untouched, and the existing tests that cover them still pass
unmodified except for opting in to the new policy (see §3).

## 2. What was built

[`web/app/services/ai_policy.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/services/ai_policy.py)
— one shared, deny-by-default verdict computed from configuration plus the
prompt text, issuing **no HTTP of its own**. Called from `_openai_chat`
*before* the base-URL check and *before* the cache lookup, so a disabled or
misconfigured service is uniformly inert.

Rejection order and stable reason codes:

| # | Condition | Code |
|---|---|---|
| 1 | `AI_ENABLED` false | `ai_disabled` |
| 2 | `AI_MAX_OUTPUT_TOKENS` outside 1..4096 | `invalid_output_bound` |
| 3 | `AI_MAX_COST_PER_CALL` outside (0, 1.0] | `invalid_cost_ceiling` |
| 4 | model name empty | `unknown_model` |
| 5 | `AI_MODEL_PRICES` unset / malformed | `pricing_not_configured` · `pricing_invalid` |
| 6 | price currency ≠ `AI_COST_CURRENCY` | `currency_mismatch` |
| 7 | model absent or unusable in the price map | `unknown_model_price` |
| 8 | worst-case cost > ceiling | `cost_ceiling_exceeded` |
| 9 | otherwise | allow, carrying the bounded `max_tokens` |

Three design decisions worth keeping deliberate:

- **No built-in price table.** A stale hard-coded price under-states cost and
  silently widens the ceiling. Prices are configuration; an unpriced model
  fails closed. The consequence is intended: enabling paid AI is a *two-step*
  operator action, and either step alone leaves the service refusing.
- **The kill switch beats the cache.** A cache hit is provider-free, so serving
  one while `AI_ENABLED=false` would cost nothing — but it would make the
  switch a half-truth and keep a withdrawn feature alive. Policy runs first.
- **Input tokens are estimated at 2 characters/token, not 4.** The live prompts
  are Russian; Cyrillic costs roughly 2–3 characters per token. Under-counting
  tokens under-counts cost and lets an over-budget call through, so the
  estimate errs high on purpose. Output is not estimated at all — the policy
  charges the full configured `max_tokens`, which is exactly the bound sent.

Settings (all in [`web/app/settings.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/settings.py)):
`AI_ENABLED` (**false**), `AI_MAX_OUTPUT_TOKENS` (1024), `AI_MAX_COST_PER_CALL`
(0.05), `AI_COST_CURRENCY` (`USD`), `AI_MODEL_PRICES` (**empty**).

Startup logs the posture once, so "is the AI on?" is answerable from
`journalctl` rather than by reading the env by hand.

## 3. Proof — every rejection costs zero provider calls

Commands (from `web/`, PowerShell):

```powershell
$env:PYTHONPATH="."; python -m pytest tests/test_ai_spend_policy.py tests/test_ai_policy_census.py -q
$env:PYTHONPATH="."; python -m pytest -m "not corpus" -q
```

| Run | Result |
|---|---|
| New H2866 files (`test_ai_spend_policy.py` + `test_ai_policy_census.py`) | **51 passed** |
| All AI-related files (adds the four H2772/cache/compare suites) | **94 passed** |
| Full hermetic suite, `-m "not corpus"` | **1020 passed, 9 skipped, 67 deselected, 1 failed** |

The single failure is
`tests/test_api.py::test_multi_query_header_does_not_duplicate_ordinal`
(a multi-query result-header ordinal string). It **pre-exists on `origin/main`**
— verified by running that test alone in the untouched main checkout at
`4ed9515`, where it fails identically — and has nothing to do with AI. It is
out of this handoff's fence; residual handoff
[H2954 (Sonnet 5) — Multi-query search header ordinal regression (pre-existing test_api failure)](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2954-Sonnet_SamudraManthanam_multi-query-header-ordinal-regression_17.08.26.md)
carries it.

Every rejection path asserts `mock_post.call_count == 0`. The cases covered:
disabled; invalid output bound (0, −1, 4097, non-numeric); invalid ceiling (0,
negative, above hard cap, non-numeric); empty model; unset pricing; five shapes
of malformed pricing; currency mismatch; unpriced model; four shapes of unusable
price entry; over-ceiling by a tiny ceiling and by a 1000× pricier model;
allowed-with-bounded-`max_tokens` (asserted on the actual payload); kill switch
beating a seeded cache entry; cache hit under an allowing policy; provider 500;
route-level 503 when disabled; route-level 429 when quota is exhausted; and
that the config report never leaks the key.

**Bypass census** —
[`web/tests/test_ai_policy_census.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ai_policy_census.py)
derives the paid surface from the source tree and the live FastAPI route table
instead of a hand-maintained list, and fails when:

1. any module outside `routers/ai.py` imports `services/ai_service`;
2. any module outside `services/ai_service.py` reads `AI_BASE_URL` / `AI_API_KEY`
   or names `chat/completions` **in code** (AST-based, so the H2772 rationale
   living in neighbouring docstrings is not a false positive);
3. `evaluate_call` stops preceding the HTTP dispatch inside `_openai_chat`
   (line-order on the AST, so a reordering regression fails);
4. a second dispatch appears anywhere else in `ai_service`;
5. the set of `/api/ai/*` routes mounted on the live app changes;
6. any `@router.*` handler in `routers/ai.py` lacks a `Depends(_require_quota)`
   parameter.

`ai_policy.py` is deliberately **not** exempt from (2): it must decide without
ever holding the credentials.

Checks (5) and (6) deliberately avoid FastAPI internals, and the reason is
worth recording because the first two attempts both failed silently in the one
direction that matters.

The first version filtered `app.routes` with `isinstance(r, APIRoute)` and
walked `route.dependant`. On the CI image's `fastapi==0.141.1` (local dev runs
0.136.1) that returned an **empty** route set while every route served
normally — the census went vacuous exactly where it was supposed to be
loudest. Reproduced in a throwaway 0.141.1 venv: `include_router` no longer
appends child routes at all, it appends one opaque
`fastapi.routing._IncludedRouter` with no `path`, no `routes` and no `router`
attribute, keeping its children behind `original_router` /
`effective_candidates`. So the obvious second fix — a recursive `.routes` walk
— returns empty too, and starting the app through `TestClient` does not
flatten it either.

The version that ships reads `app.openapi()["paths"]`, a documented public
surface that reports the same set on both versions, and check (6) parses
`routers/ai.py` for a `Depends(_require_quota)` parameter on every `@router.*`
handler. The regression being guarded against is a handler added without the
gate — visible in the source regardless of what the routing layer does
internally. `test_paid_routes_exist_so_the_census_is_not_vacuous` is what
caught both failures; keep it.

## 4. Deploy, smoke, rollback

_Filled in after the merge — see the deploy section below._

## 5. Production verdict

`AI_ENABLED` stays **false** in production. See §6 for the exact reason.

## 6. What a human decides, and what happens if nobody does

Nothing in this handoff waits on a human. The service is complete and safe in
its shipped configuration; enabling paid AI is an optional business decision,
not a missing engineering step.

If someone does want it on, the act is: edit `/opt/samudra/.env` on
`root@193.232.229.92`, add an `AI_MODEL_PRICES` line pricing whichever model
`AI_MODEL` names (numbers copied from the provider's current price list —
nothing in the app can verify them), change `AI_ENABLED=false` to
`AI_ENABLED=true`, and `systemctl restart samudra`. The literal commands and
the one-line rollback are in
[OPS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md)
§ Paid-AI kill switch.

If nobody ever does it, the two AI routes keep answering 503 for authenticated
callers, no provider request is ever dispatched, and the key can be funded or
left dead with identical financial consequence — zero. That is the point of the
default.

_Dr. Mārcis Gasūns_
