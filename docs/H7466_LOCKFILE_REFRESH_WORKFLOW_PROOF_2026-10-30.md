# H7466 — Lockfile-refresh workflow: permission & rerun-safety proof

_Created: 30-10-2026 · Executor: GLM 5.3 (opencode/zai-coding-plan/glm-5.3) ·
Base: `dddad66` (origin/main)_

## What this is

Proof receipt for the lockfile-refresh dispatch workflow
(`.github/workflows/lockfile-refresh.yml`). The dispatch logic was extracted
into `scripts/lockfile_refresh_dispatch.sh` and exercised across the full
acceptance matrix with controlled git/gh boundaries (PATH-shimmed fakes); the
workflow is pinned to delegate every push/PR decision to that tested script.
Two reproduced defects were repaired; everything else is unchanged.

## Reproduced defects (evidence)

1. **Swallowed `gh pr create` refusal** — live run
   [40978950775](https://github.com/gasyoun/SamudraManthanam/actions/runs/40978950775)
   (30-10-2026, dispatched on `main`, *after* the #430/#431 fixes): the
   commit landed on `bot/lockfile-refresh` (271fee9), then
   `gh pr create … 2>/dev/null || true` discarded the token-policy refusal,
   and the run died red on `gh pr merge` with "no pull requests found for
   branch" — nonzero but not actionable, refusal cause invisible. Same class
   as PR #431 (token could not open the PR).
2. **Silent non-reuse on repeat dispatch** — repeat main dispatches hit
   `gh pr create` blind (error swallowed) instead of detecting and reusing
   the existing PR for the bot branch.

## Live read-only evidence (separate from offline simulation)

Recorded 30-10-2026 via `gh api` (read-only, no policy or permission change):

- **Branch protection `main`:** required status check `paper-priv-guard`
  (strict=false), `enforce_admins: false`, `allow_force_pushes: false`,
  `required_pull_request_reviews`: absent, `restrictions`: absent.
- **Actions policy:** `actions/permissions` →
  `{"enabled": true, "allowed_actions": "all", "sha_pinning_required": false}`.
- **Dispatch history (workflow `lockfile-refresh.yml`):** runs
  40977997827, 40978315487, 40978950775 — all `completed/failure` on `main`.
  40977997827 is the GH006 protected-main push (pre-#430); 40978950775 is
  the swallowed-refusal failure above (post-#430/#431).
- No live dispatch, force-push, merge, deploy or paid runner was run as a
  test; matrix rows below are the offline simulation on the real script.

## Acceptance matrix (offline, real script + shimmed git/gh)

Command per row: `python -m pytest scripts/test_lockfile_refresh_dispatch.py -v`
(boundaries = PATH-shimmed `git`/`gh` recording fakes; script under test =
`scripts/lockfile_refresh_dispatch.sh`).

| Row | Test | Expected | Observed | Exit |
|---|---|---|---|---|
| main dispatch | `test_main_dispatch_never_writes_main_ships_via_bot_pr` | never writes `main`; one force-push to `bot/lockfile-refresh`; PR created `--base main` | as expected | PASS |
| feature dispatch | `test_feature_dispatch_stays_on_feature_branch` | pushes only `HEAD:<ref>`; no gh calls | as expected | PASS |
| unchanged lock | `test_unchanged_lockfile_is_noop` | exit 0, no push, no PR | as expected | PASS |
| repeat dispatch | `test_repeat_dispatch_reuses_single_pr` | reuses existing PR; zero `gh pr create` | as expected | PASS |
| denied PR creation | `test_pr_refusal_preserves_artifact_and_fails_actionably` | commit already on bot branch; nonzero + `::error::` naming artifact + manual fallback URL; refusal text visible | as expected | PASS |
| guard | `test_missing_ref_name_fails_fast` | nonzero before any push/PR | as expected | PASS |

## Named negative controls (historical mutations must fail)

| Mutation | Control test | Result |
|---|---|---|
| direct-main push on main dispatch (pre-#430, run 40977997827) | `test_mutation_direct_main_push_is_caught` — detector `pushed_to_default` flags it (⇒ `test_main_dispatch_never_writes_main_ships_via_bot_pr` FAILS against this mutation) | CAUGHT |
| swallowed `gh pr create` refusal (verbatim 19d634a..dddad66 logic) | `test_mutation_swallowed_pr_create_error_is_caught` — contract `actionable_failure` does NOT hold for it (⇒ `test_pr_refusal_…` FAILS against this mutation); refusal text invisible (`2>/dev/null`) | CAUGHT |

## Workflow fidelity (the tested path IS the shipped path)

`test_workflow_delegates_dispatch_to_tested_script`,
`test_workflow_has_no_inline_push_or_pr_logic`,
`test_workflow_permissions_and_trigger_unchanged`,
`test_workflow_keeps_regeneration_step`: the workflow calls the script with
`REF_NAME=${{ github.ref_name }}` / `GH_TOKEN=${{ github.token }}`; **no**
inline `git push` / `gh pr` anywhere; `permissions: contents:write,
pull-requests:write` and `workflow_dispatch` unchanged; regeneration step
(`npm install --package-lock-only`) unchanged.

## Repair shipped

`scripts/lockfile_refresh_dispatch.sh`: on a default-branch dispatch — after
force-pushing the bot branch, `gh pr view` detects an existing PR (reuse),
else `gh pr create`; if creation is refused, the run exits 1 with
`::error::` that names the preserved commit (`origin/bot/lockfile-refresh` at
`<sha>`), the manual PR URL, and the token remedy. Feature dispatch and
unchanged-lock paths behave exactly as before.

## Checks

- `python -m pytest scripts/test_lockfile_refresh_dispatch.py -v` → 12 passed.
- `python -m pytest -m "not corpus" -q --ignore=web/tests` → 20 passed,
  1 skipped (web/tests skipped locally only — needs `requirements.txt` deps
  that CI installs; untouched by this change).
- `bash -n scripts/lockfile_refresh_dispatch.sh` → OK.

## Verifier

Independent non-zai review recorded on the PR (model + final commit noted
there). Missing review ⇒ INCONCLUSIVE.
