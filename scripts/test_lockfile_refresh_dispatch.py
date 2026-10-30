"""H7466 contract tests for the lockfile-refresh dispatch logic.

Exercises the REAL dispatch script (scripts/lockfile_refresh_dispatch.sh)
across the acceptance matrix with controlled git/gh boundaries (PATH-shimmed
fakes), plus two named mutation controls that must catch the historical
defects:

  - direct-main push on a default-branch dispatch (pre-#430, run 40977997827)
  - swallowed ``gh pr create`` refusal (pre-H7466, run 40978950775 / PR #431)

and workflow-fidelity checks pinning .github/workflows/lockfile-refresh.yml to
delegate every push/PR decision to the tested script (nothing inline).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HELPER = ROOT / "scripts" / "lockfile_refresh_dispatch.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "lockfile-refresh.yml"

# Verbatim dispatch logic shipped at 19d634a..dddad66 (pre-H7466), with only
# the template expression `${{ github.ref_name }}` replaced by "$REF_NAME" so
# the harness can drive it. This is the swallowed-error mutation target.
HISTORICAL_SNIPPET = r"""
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add nkrya-parallel/package-lock.json
if git diff --cached --quiet; then
  echo "lockfile already up to date"
  exit 0
fi
git commit -m "chore(nkrya-parallel): regenerate package-lock (overrides applied)"
if [ "$REF_NAME" = "main" ]; then
  BRANCH="bot/lockfile-refresh"
  git push -f origin "HEAD:$BRANCH"
  gh pr create --head "$BRANCH" --base main \
    --title "chore(nkrya-parallel): regenerate package-lock (overrides applied)" \
    --body "Automated lockfile regeneration after override changes. Auto-merges when required checks pass." 2>/dev/null || true
  gh pr merge "$BRANCH" --squash --auto || gh pr merge "$BRANCH" --squash
else
  git push origin "HEAD:$REF_NAME"
fi
"""

FAKE_GIT = r"""#!/usr/bin/env bash
printf 'git %s\n' "$*" >> "$FAKE_CALLS_LOG"
case "$1" in
  rev-parse)
    if [ "${2:-}" = "HEAD" ]; then echo "${FAKE_GIT_HEAD:-271fee9}"; exit 0; fi
    ;;
  diff)
    case "$*" in
      *--quiet*)
        if [ "${FAKE_GIT_STAGED_CHANGES:-1}" = "1" ]; then exit 1; else exit 0; fi
        ;;
    esac
    ;;
  push)
    if [ "${FAKE_GIT_PUSH_FAIL:-0}" = "1" ]; then
      echo "fake git: push rejected" >&2
      exit 1
    fi
    ;;
esac
exit 0
"""

FAKE_GH = r"""#!/usr/bin/env bash
printf 'gh %s\n' "$*" >> "$FAKE_CALLS_LOG"
if [ "${1:-}" != "pr" ]; then exit 0; fi
sub="${2:-}"; shift 2 || true
case "$sub" in
  view)
    if [ "${FAKE_GH_PR_EXISTS:-0}" = "1" ]; then exit 0; fi
    echo "no pull requests found for branch" >&2
    exit 1
    ;;
  create)
    if [ "${FAKE_GH_CREATE_REFUSED:-0}" = "1" ]; then
      echo "gh: refusing to create PR: workflow does not have permission (Actions-PR policy)" >&2
      exit 1
    fi
    echo "https://github.com/gasyoun/SamudraManthanam/pull/999"
    exit 0
    ;;
  merge)
    exit "${FAKE_GH_MERGE_EXIT:-0}"
    ;;
esac
exit 0
"""


def _bash() -> str:
    bash = shutil.which("bash")
    if not bash:
        pytest.skip("bash not available for dispatch-script harness")
    return bash


def run_dispatch(
    ref_name,
    *,
    script: Path = HELPER,
    staged_changes=True,
    pr_exists=False,
    create_refused=False,
    push_fail=False,
    merge_exit=0,
    ref_name_set=True,
    timeout=30,
):
    """Run the real dispatch script with shimmed git/gh; return (proc, calls)."""
    tmp = Path(os.environ.get("TEMP", "/tmp")) / f"h7466-{os.getpid()}-{id(ref_name)}"
    bin_dir = tmp / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / "git").write_text(FAKE_GIT, encoding="utf-8", newline="\n")
    (bin_dir / "gh").write_text(FAKE_GH, encoding="utf-8", newline="\n")
    calls_log = tmp / "calls.log"
    if calls_log.exists():
        calls_log.unlink()

    if script == HELPER:
        target = script
    else:  # mutation fixture text -> materialize a runnable copy
        target = tmp / "mutated.sh"
        target.write_text(script if isinstance(script, str) else script.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

    env = dict(os.environ)
    env.update(
        {
            "PATH": str(bin_dir) + os.pathsep + env.get("PATH", ""),
            "FAKE_CALLS_LOG": calls_log.as_posix(),
            "FAKE_GIT_STAGED_CHANGES": "1" if staged_changes else "0",
            "FAKE_GH_PR_EXISTS": "1" if pr_exists else "0",
            "FAKE_GH_CREATE_REFUSED": "1" if create_refused else "0",
            "FAKE_GIT_PUSH_FAIL": "1" if push_fail else "0",
            "FAKE_GH_MERGE_EXIT": str(merge_exit),
        }
    )
    if ref_name_set:
        env["REF_NAME"] = ref_name
    else:
        env.pop("REF_NAME", None)

    proc = subprocess.run(
        [_bash(), target.as_posix()],
        env=env,
        cwd=tmp.as_posix(),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    calls = calls_log.read_text(encoding="utf-8").splitlines() if calls_log.exists() else []
    return proc, calls


# ---------------------------------------------------------------- contract detectors

def pushed_to_default(calls) -> bool:
    """A dispatch wrote the protected default branch (the GH006 mutation)."""
    return any(re.search(r"git push .*HEAD:main(\s|$)", c) for c in calls)


def actionable_failure(proc) -> bool:
    """Nonzero exit AND an actionable ::error:: naming the preserved artifact."""
    out = (proc.stdout or "") + (proc.stderr or "")
    return (
        proc.returncode != 0
        and "::error::" in out
        and "bot/lockfile-refresh" in out
    )


# ---------------------------------------------------------------- acceptance matrix

def test_unchanged_lockfile_is_noop():
    proc, calls = run_dispatch("main", staged_changes=False)
    assert proc.returncode == 0, proc.stderr
    assert "lockfile already up to date" in proc.stdout
    assert not [c for c in calls if c.startswith(("git push", "gh"))]
    assert not pushed_to_default(calls)


def test_main_dispatch_never_writes_main_ships_via_bot_pr():
    proc, calls = run_dispatch("main")
    assert proc.returncode == 0, proc.stderr
    pushes = [c for c in calls if c.startswith("git push")]
    assert pushes == ['git push -f origin HEAD:bot/lockfile-refresh']
    assert not pushed_to_default(calls)
    create = [c for c in calls if c.startswith("gh pr create")]
    assert len(create) == 1
    assert "--head bot/lockfile-refresh" in create[0]
    assert "--base main" in create[0]
    assert any(c.startswith("gh pr merge") for c in calls)


def test_feature_dispatch_stays_on_feature_branch():
    proc, calls = run_dispatch("fix/429-override-body-parser")
    assert proc.returncode == 0, proc.stderr
    pushes = [c for c in calls if c.startswith("git push")]
    assert pushes == ["git push origin HEAD:fix/429-override-body-parser"]
    assert not [c for c in calls if c.startswith("gh")]


def test_repeat_dispatch_reuses_single_pr():
    # PR already open for the bot branch: reuse it, never create a second one.
    proc, calls = run_dispatch("main", pr_exists=True)
    assert proc.returncode == 0, proc.stderr
    assert any(c.startswith("gh pr view") for c in calls)
    assert not [c for c in calls if c.startswith("gh pr create")]
    assert any(c.startswith("gh pr merge") for c in calls)
    assert any("HEAD:bot/lockfile-refresh" in c for c in calls if c.startswith("git push"))


def test_pr_refusal_preserves_artifact_and_fails_actionably():
    # Refused PR creation (Actions-PR policy): the regenerated commit must
    # already sit on the bot branch, and the run must exit nonzero with an
    # actionable message - not swallow the refusal into a merge failure.
    proc, calls = run_dispatch("main", create_refused=True, merge_exit=1)
    out = (proc.stdout or "") + (proc.stderr or "") 
    assert proc.returncode != 0, "refused PR creation must fail the run"
    assert actionable_failure(proc)
    # artifact preserved BEFORE the refusal was reported
    push_idx = next(i for i, c in enumerate(calls) if "HEAD:bot/lockfile-refresh" in c)
    create_idx = next(i for i, c in enumerate(calls) if c.startswith("gh pr create"))
    assert push_idx < create_idx
    # the actual refusal reason passes through instead of /dev/null
    assert "permission" in out or "refus" in out.lower()
    assert "pull/new/bot/lockfile-refresh" in out  # manual fallback URL


def test_missing_ref_name_fails_fast():
    proc, calls = run_dispatch(None, ref_name_set=False)
    assert proc.returncode != 0
    assert not [c for c in calls if c.startswith(("git push", "gh"))]


# ---------------------------------------------------------------- named mutation controls

def test_mutation_direct_main_push_is_caught():
    """Named control for the pre-#430 defect (run 40977997827): a dispatch
    step that pushes the default branch directly must be detectable - the
    detector flags it, i.e. test_main_dispatch_never_writes_main would FAIL
    against this mutation."""
    mutated = (
        'REF_NAME="${REF_NAME:?}"\nset -e\n'
        'git add nkrya-parallel/package-lock.json\n'
        'if git diff --cached --quiet; then exit 0; fi\n'
        'git commit -m "regenerate"\n'
        'git push origin "HEAD:main"\n'  # the GH006 mutation
    )
    proc, calls = run_dispatch("main", script=mutated)
    assert pushed_to_default(calls), "detector must catch a direct main push"


def test_mutation_swallowed_pr_create_error_is_caught():
    """Named control for the pre-H7466 defect (run 40978950775 / PR #431):
    the shipped dispatch logic suppressed gh pr create failures and ran into
    an unactionable merge failure. The actionable_failure contract must NOT
    hold for it, i.e. test_pr_refusal_... would FAIL against this mutation."""
    proc, calls = run_dispatch(
        "main", script=HISTORICAL_SNIPPET, create_refused=True, merge_exit=1
    )
    assert proc.returncode != 0  # it failed - confusingly, via gh pr merge
    assert not actionable_failure(proc), (
        "historical logic must not satisfy the actionable-failure contract"
    )
    # and the refusal itself was invisible (2>/dev/null || true)
    out = (proc.stdout or "") + (proc.stderr or "")
    assert "permission" not in out and "refus" not in out.lower()


# ---------------------------------------------------------------- workflow fidelity

def _yaml():
    pytest.importorskip("yaml")
    import yaml

    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_workflow_delegates_dispatch_to_tested_script():
    wf = _yaml()
    steps = wf["jobs"]["refresh"]["steps"]
    dispatch = [s for s in steps if "lockfile_refresh_dispatch.sh" in str(s.get("run", ""))]
    assert len(dispatch) == 1, "dispatch step must call the contract-tested script"
    env = dispatch[0]["env"]
    assert env["REF_NAME"] == "${{ github.ref_name }}"
    assert env["GH_TOKEN"] == "${{ github.token }}"


def test_workflow_has_no_inline_push_or_pr_logic():
    wf = _yaml()
    for step in wf["jobs"]["refresh"]["steps"]:
        run = str(step.get("run", ""))
        assert "git push" not in run, f"inline git push escapes the tested path: {run}"
        assert "gh pr" not in run, f"inline gh pr escapes the tested path: {run}"


def test_workflow_permissions_and_trigger_unchanged():
    wf = _yaml()
    assert wf["permissions"] == {"contents": "write", "pull-requests": "write"}
    trigger = wf.get("on") or wf.get(True)  # yaml parses bare `on:` as True
    assert "workflow_dispatch" in trigger


def test_workflow_keeps_regeneration_step():
    wf = _yaml()
    regen = [s for s in wf["jobs"]["refresh"]["steps"] if "npm install --package-lock-only" in str(s.get("run", ""))]
    assert len(regen) == 1
    assert regen[0]["working-directory"] == "nkrya-parallel"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
