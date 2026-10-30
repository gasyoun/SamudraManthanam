#!/usr/bin/env bash
# Dispatch/ship half of .github/workflows/lockfile-refresh.yml (H7466).
#
# Runs after the lockfile has been regenerated (npm --package-lock-only).
# Stages, commits and ships the regenerated lock:
#   - unchanged staged lock          -> no-op, exit 0
#   - dispatch on the default branch -> NEVER pushes the default branch
#                                       (protected, GH006 / run 40977997827);
#                                       force-pushes the bot branch, reuses
#                                       the existing PR or creates one, and
#                                       fails actionably if creation is refused
#                                       (run 40978950775 / PR #431)
#   - dispatch on a feature branch   -> pushes that branch only
#
# Contract-tested by scripts/test_lockfile_refresh_dispatch.py with PATH-shimmed
# git/gh; the workflow file is pinned to delegate here (no inline git push/gh).
#
# Env:
#   REF_NAME    github.ref_name of the dispatch (required)
#   BASE        protected default branch        (default: main)
#   BOT_BRANCH  bot branch for default-branch dispatches (default: bot/lockfile-refresh)

set -euo pipefail

REF_NAME="${REF_NAME:?REF_NAME (github.ref_name) is required}"
BASE="${BASE:-main}"
BOT_BRANCH="${BOT_BRANCH:-bot/lockfile-refresh}"

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add nkrya-parallel/package-lock.json

if git diff --cached --quiet; then
  echo "lockfile already up to date"
  exit 0
fi

git commit -m "chore(nkrya-parallel): regenerate package-lock (overrides applied)"

if [ "$REF_NAME" = "$BASE" ]; then
  # Default branch is protected (GH006, run 40977997827): ship via bot PR.
  # -f is safe: the bot branch is single-purpose and bot-owned.
  git push -f origin "HEAD:$BOT_BRANCH"

  if gh pr view "$BOT_BRANCH" >/dev/null 2>&1; then
    echo "PR for $BOT_BRANCH already exists - reusing it for the refreshed commit"
  elif gh pr create --head "$BOT_BRANCH" --base "$BASE" \
      --title "chore(nkrya-parallel): regenerate package-lock (overrides applied)" \
      --body "Automated lockfile regeneration after override changes. Auto-merges when required checks pass."; then
    echo "PR created for $BOT_BRANCH"
  else
    # Creation refused is real (Actions-PR policy, run 40978950775 / PR #431).
    # The regenerated lock IS already preserved on the bot branch above -
    # surface that loudly instead of swallowing the refusal into a confusing
    # "no pull requests found" merge failure.
    echo "::error::gh pr create refused for $BOT_BRANCH (see gh output above). The regenerated lock IS preserved on origin/$BOT_BRANCH at $(git rev-parse HEAD) - open/merge the PR manually (https://github.com/gasyoun/SamudraManthanam/pull/new/$BOT_BRANCH) or grant the workflow token pull-requests:write."
    exit 1
  fi

  gh pr merge "$BOT_BRANCH" --squash --auto || gh pr merge "$BOT_BRANCH" --squash
else
  # Feature dispatch: the branch already carries the override changes and its
  # PR - push the regenerated lock onward to the same branch only.
  git push origin "HEAD:$REF_NAME"
fi
