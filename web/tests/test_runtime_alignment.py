"""D4 acceptance — the production Python version is covered by CI (H1927).

VERIFICATION D4: "The exact production Python version is covered by CI and
boots the application image."

This file is the *static* half — it reads the two files that can disagree and
fails when they do. The boot half is `web/scripts/deployment_contract_smoke.py`,
run against the built image in CI.

Why it exists: before H1927 the Dockerfile pinned `python:3.14-slim` while the
CI test matrix ran 3.10/3.11/3.12. Every release therefore shipped on an
interpreter no test had ever executed, and nothing anywhere would have said so.
A comment in the workflow would not have held; a test does.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = REPO_ROOT / "Dockerfile"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

# `FROM python:3.14-slim-bookworm@sha256:...` → 3.14
_FROM_RE = re.compile(
    r"^FROM\s+python:(\d+\.\d+)[-\w.]*(?:@sha256:[0-9a-f]+)?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def dockerfile_python_version(path: Path | None = None) -> str:
    text = (path or DOCKERFILE).read_text(encoding="utf-8")
    match = _FROM_RE.search(text)
    assert match, (
        "Could not parse a `FROM python:X.Y...` line out of the Dockerfile. If the "
        "base image changed shape, update this test — do not delete it."
    )
    return match.group(1)


def ci_test_matrix_versions(path: Path | None = None) -> list[str]:
    """Read the test job's python-version list.

    Regex rather than PyYAML on purpose: the CI test job installs only
    `requirements.txt` plus pytest, and a guard test that needs a dependency
    the guarded job does not have would simply be deleted the first time it
    broke someone's build.
    """
    text = (path or CI_WORKFLOW).read_text(encoding="utf-8")
    match = re.search(r"^\s*python-version:\s*\[([^\]]+)\]", text, re.MULTILINE)
    assert match, "Could not find a `python-version: [...]` matrix in ci.yml"
    return re.findall(r"\d+\.\d+", match.group(1))


@pytest.mark.skipif(not DOCKERFILE.exists(), reason="no Dockerfile in this checkout")
def test_production_python_version_is_in_the_ci_matrix():
    prod = dockerfile_python_version()
    matrix = ci_test_matrix_versions()
    assert prod in matrix, (
        f"Dockerfile runs Python {prod} in production but the CI test matrix is "
        f"{matrix}. Production would ship on an interpreter no test has executed. "
        f"Either add {prod} to the matrix in .github/workflows/ci.yml or pin the "
        f"image to a tested version."
    )


@pytest.mark.skipif(not DOCKERFILE.exists(), reason="no Dockerfile in this checkout")
def test_base_image_is_digest_pinned():
    """A floating tag would let the runtime drift under a green CI run."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    from_lines = [ln for ln in text.splitlines() if ln.upper().startswith("FROM ")]
    assert from_lines, "no FROM line in Dockerfile"
    for line in from_lines:
        assert "@sha256:" in line, (
            f"Base image is not digest-pinned: {line.strip()}. A moving tag can "
            f"change the interpreter without any commit to this repo."
        )


def test_guard_catches_the_historical_divergence(tmp_path):
    """The guard must go RED on the exact state that shipped before H1927.

    A guard nobody has watched fail is indistinguishable from a guard that
    cannot fail. This replays origin/main @ be9a303 — Dockerfile on 3.14, CI
    matrix on 3.10–3.12 — and asserts the parsers disagree.
    """
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text(
        "FROM python:3.14-slim-bookworm@sha256:"
        "86f975aca15cf04a40b399eebede9aea7c82eae084d1f1a0a6ef6bcaae871a30\n",
        encoding="utf-8",
    )
    workflow = tmp_path / "ci.yml"
    workflow.write_text(
        "jobs:\n  test:\n    strategy:\n      matrix:\n"
        '        python-version: ["3.10", "3.11", "3.12"]\n',
        encoding="utf-8",
    )

    prod = dockerfile_python_version(dockerfile)
    matrix = ci_test_matrix_versions(workflow)
    assert prod == "3.14"
    assert matrix == ["3.10", "3.11", "3.12"]
    assert prod not in matrix, "guard is vacuous — it would not have caught H1927's bug"


def test_runtime_matches_the_documented_support_floor():
    """The matrix must stay contiguous — no silent gaps between floor and prod.

    A gap (say 3.10, 3.12, 3.14 with 3.11 and 3.13 absent) usually means a
    version was dropped to make a red build green, which is exactly the kind of
    quiet narrowing this lane exists to prevent.
    """
    matrix = ci_test_matrix_versions()
    as_tuples = sorted(tuple(int(p) for p in v.split(".")) for v in matrix)
    for earlier, later in zip(as_tuples, as_tuples[1:]):
        assert later[0] == earlier[0] and later[1] == earlier[1] + 1, (
            f"CI python matrix has a gap between {earlier} and {later}: {matrix}"
        )
