# Future OxAlpha status-gate design — SamudraManthanam (DESIGN ONLY, NOT ENABLED)

_Created: 27-08-2026 · Last updated: 27-08-2026_

**Handoff:** H3552 (OxAlpha). Ruling 12 of the plan: **design but do not enable** the gate. This document describes a future required status check; **no workflow file, branch-protection rule, or repository setting has been created or changed** for it. Enabling anything below is a separate human decision.

## Purpose

A repeatable, independent gate that reviews every executable-code change before merge, so the defect classes found by the H3552 retrospective (F1–F14 in [the evidence report](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/reviews/OXALPHA_RETROSPECTIVE_CODE_REVIEW_26-08-2026.md)) are caught at PR time instead of in a 30-day retrospective.

## 1. Executable-code matching

A PR needs the OxAlpha gate only when its diff touches executable surface:

- `web/app/**`, `web/corpus_builder/**`, `scripts/**`, `Corpus_builder/**`, `deploy/**` (nginx/systemd units count as executable ops surface);
- top-level `*.sh`, `*.ps1`, `*.py`.

Generated, vendor, docs-only, data-only (`.jsonl`, `.csv`, `.tsv`, corpus bulk) diffs skip the gate — same exclusion rule the retrospective used. Implementation shape: a paths-filter on the (not created) workflow, plus a label escape hatch `skip-oxalpha-review` restricted to humans.

## 2. Independent required status check

- A GitHub Actions workflow (name: `oxalpha-review`) runs on `pull_request` for matched paths, executing an OxAlpha headless review pass with a locked prompt contract: two independent verdicts (Standards, Spec), no finding without severity + file/line + failure mode + repro-or-`no repro constructed`, no re-ranking axes between slices.
- The check posts the verdict summary as a PR comment and reports **success only on "no P0/P1 finding"**; any P0/P1 finding → check failure with the finding table in the comment.
- Branch protection (only when enabled): the check becomes a **required status check** for the paths above; humans can override via a ruled admin bypass, recorded in the PR.

## 3. Added human approval for money/security/production paths

Model review is not release accountability. On top of the gate, PRs whose diff touches any of:

- money/spend control (`ai_policy.py`, `ai_service.py` quota paths, `rate_limit.py`, pricing/settings of AI),
- security edge (nginx configs, HSTS/security headers, auth/session/identity, admin env),
- production state (systemd units, deploy scripts, `OPS.md`-referenced prod commands, irreversible migrations),

require one **human** review approval (CODEOWNERS-style route to the owner) before merge, even when the OxAlpha gate is green. The gate never self-approves these paths.

## 4. Failure policy

- Gate infrastructure failure (workflow error, executor unreachable) = **check failure**, not a skip — fail closed, mirroring `fail_open=False` for billable buckets.
- Flaky/timeout → re-run once automatically; second failure stays red.
- A stop-condition hit (secrets/PII, production state, irreversible migration, unclear money, bulk generated edits) is reported as an explicit blocked finding naming the condition — never a silent pass (H3552 F2 discipline).

## 5. Rollout (when a human decides to enable)

1. Shadow phase: workflow runs, comments, check **not** required — two weeks of calibration, false-positive census.
2. Required phase: add the check to branch protection for matched paths only.
3. Approval phase: wire the money/security/production CODEOWNERS route.

Each phase is a separate PR with its own review; nothing in this handoff pre-stages those diffs.

## 6. Observability

- Workflow run retention default; verdict summaries stay on the PR (no parallel shadow store).
- Monthly one-line metric appended to a chosen hub by a human: gate runs, P0/P1 catches, overrides — derived from `gh` queries, not a new datastore.

## 7. Rollback

Disabling = remove the required-check entry (branch protection) or the workflow file; both are single-commit reverts with no data migration. The gate holds no state, so rollback is instantaneous and lossless.

## Non-activation proof

- `git log -- .github/workflows` shows no gate workflow added by H3552.
- Branch protection untouched during H3552 (no protection-rule mutation in the plan's non-goals).

_Dr. Mārcis Gasūns_
