# 2026-11-10 — Python 3.10 floor enforced for web requirements (H7934)

_Created: 10-11-2026 · Last updated: 10-11-2026_

Re-capped `web/requirements.txt` (`sse-starlette==3.5.0`, `python-multipart==0.0.32`) —
PR #447 had re-bumped both to >=3.11-only versions and was squash-merged while the
`Pytest (Python 3.10)` job was still red. Three guards so it cannot recur: Dependabot
`ignore:` entries (`sse-starlette >=3.6`, `python-multipart >=0.0.33`, H7160 pattern),
`dependabot-auto-merge.yml` now polls CI on the head SHA and refuses to merge unless it
completes `success` (the direct `gh pr merge --squash` fallback was the red-merge window),
and a new paths-filtered `dependency-floor-install.yml` does a cache-free install of the
web requirements on Python 3.10 for any PR touching the file (~40 s, its own named check).
Controls: sse-starlette==3.6.0 and python-multipart==0.0.33 both fail `pip download
--python-version 3.10` (exit 1), the capped set resolves 52 distributions (exit 0).
[PR #450](https://github.com/gasyoun/SamudraManthanam/pull/450) · [issue #449](https://github.com/gasyoun/SamudraManthanam/issues/449) · Uprava H7934.

_Dr. Mārcis Gasūns_
