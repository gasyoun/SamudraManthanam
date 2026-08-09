#!/usr/bin/env python3
"""H2433 — headless Corpus Builder jobs before web DB ingest / reindex.

Runs ``cb_headless --build … [--out …] [--check]`` for each line in a jobs
file, then the caller continues with ``build-web-db.ps1`` / ``reindex.sh``.

Default behaviour (safe for prod cron that only rsyncs prebuilt HTML):

* No jobs file, empty jobs, or ``SKIP_HEADLESS_CB=1`` → exit **0** (no-op).
* Jobs present and binary found → run each; non-zero cb exit fails the pipeline.
* Jobs present and binary missing → exit **1** (unless ``--allow-missing-binary``).

Jobs file (JSONL, one object per line; ``#`` comments and blank lines OK)::

    {"build": "path/to/work-dir-or-config.ini", "out": "Data/book.html"}
    {"build": "path/to/config.ini", "out": "Data/book.html", "check": true}

Lookup order for jobs path:

1. ``--jobs`` / ``CB_HEADLESS_JOBS``
2. ``<repo>/Corpus_builder/pipeline/headless_jobs.jsonl``
3. ``<corpus-path>/Programdata/headless_jobs.jsonl`` (deploy-side)

Binary lookup: ``--binary`` / ``CB_HEADLESS``, then common ``lib/<cpu-os>/``
paths under ``Corpus_builder/PSRCBuilder/``, then ``PATH``.

Exit codes:
  0  success or intentional skip
  1  job failure / missing binary when jobs are configured
  2  usage / unreadable jobs file
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


@dataclass(frozen=True)
class HeadlessJob:
    build: str
    out: str | None = None
    check: bool = False

    def argv(self, binary: Path, repo_root: Path) -> list[str]:
        build_path = _resolve_path(self.build, repo_root)
        cmd = [str(binary), "--build", str(build_path)]
        if self.out:
            cmd.extend(["--out", str(_resolve_path(self.out, repo_root))])
        if self.check:
            cmd.append("--check")
        return cmd


def _resolve_path(raw: str, repo_root: Path) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    return (repo_root / p).resolve()


def parse_jobs_text(text: str) -> list[HeadlessJob]:
    """Parse JSONL jobs; ignore blank lines and ``#`` comments."""
    jobs: list[HeadlessJob] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"jobs line {lineno}: invalid JSON: {exc}") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"jobs line {lineno}: expected object, got {type(obj).__name__}")
        build = obj.get("build")
        if not build or not isinstance(build, str):
            raise ValueError(f"jobs line {lineno}: missing string field 'build'")
        out = obj.get("out")
        if out is not None and not isinstance(out, str):
            raise ValueError(f"jobs line {lineno}: 'out' must be a string when set")
        check = bool(obj.get("check", False))
        jobs.append(HeadlessJob(build=build, out=out, check=check))
    return jobs


def load_jobs(path: Path) -> list[HeadlessJob]:
    text = path.read_text(encoding="utf-8")
    return parse_jobs_text(text)


def default_cpu_os() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if machine in ("amd64", "x86_64"):
        cpu = "x86_64"
    elif machine in ("aarch64", "arm64"):
        cpu = "aarch64"
    else:
        cpu = machine or "unknown"
    if system.startswith("win"):
        os_name = "win64" if cpu == "x86_64" else "win32"
    elif system == "linux":
        os_name = "linux"
    elif system == "darwin":
        os_name = "darwin"
    else:
        os_name = system
    return f"{cpu}-{os_name}"


def candidate_binaries(repo_root: Path, explicit: str | None = None) -> list[Path]:
    out: list[Path] = []
    if explicit:
        out.append(Path(explicit))
    env = os.environ.get("CB_HEADLESS", "").strip()
    if env:
        out.append(Path(env))
    ps = repo_root / "Corpus_builder" / "PSRCBuilder"
    cpu_os = default_cpu_os()
    names = ("cb_headless.exe", "cb_headless")
    for name in names:
        out.append(ps / "lib" / cpu_os / name)
        out.append(ps / name)
        # Common alternate FPC targets
        if cpu_os.startswith("x86_64"):
            out.append(ps / "lib" / "x86_64-linux" / name)
            out.append(ps / "lib" / "x86_64-win64" / name)
    which = shutil.which("cb_headless") or shutil.which("cb_headless.exe")
    if which:
        out.append(Path(which))
    # de-dupe preserving order
    seen: set[str] = set()
    unique: list[Path] = []
    for p in out:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)
    return unique


def resolve_binary(repo_root: Path, explicit: str | None = None) -> Path | None:
    for p in candidate_binaries(repo_root, explicit):
        if p.is_file():
            return p.resolve()
    return None


def resolve_jobs_path(
    repo_root: Path,
    *,
    explicit: str | None = None,
    corpus_path: str | None = None,
) -> Path | None:
    if explicit:
        return Path(explicit)
    env = os.environ.get("CB_HEADLESS_JOBS", "").strip()
    if env:
        return Path(env)
    repo_jobs = repo_root / "Corpus_builder" / "pipeline" / "headless_jobs.jsonl"
    if repo_jobs.is_file():
        return repo_jobs
    if corpus_path:
        deploy_jobs = Path(corpus_path) / "Programdata" / "headless_jobs.jsonl"
        if deploy_jobs.is_file():
            return deploy_jobs
    return None


def run_jobs(
    jobs: Sequence[HeadlessJob],
    *,
    binary: Path,
    repo_root: Path,
    dry_run: bool = False,
    runner=None,
) -> int:
    """Run jobs; return 0 on success, 1 if any job fails."""
    run = runner or subprocess.run
    for i, job in enumerate(jobs, start=1):
        cmd = job.argv(binary, repo_root)
        print(f"[headless-cb] job {i}/{len(jobs)}: {' '.join(cmd)}")
        if dry_run:
            continue
        # Ensure parent of --out exists when we control the path
        if job.out:
            out_path = _resolve_path(job.out, repo_root)
            out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            proc = run(cmd, check=False)
        except OSError as exc:
            print(f"[headless-cb] failed to spawn: {exc}", file=sys.stderr)
            return 1
        code = getattr(proc, "returncode", proc)
        if code != 0:
            print(
                f"[headless-cb] job {i} failed with exit {code}",
                file=sys.stderr,
            )
            return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Run headless cb builds before web DB ingest/reindex (H2433)."
    )
    ap.add_argument(
        "--repo-root",
        default=None,
        help="Repo root (default: parent of scripts/)",
    )
    ap.add_argument("--jobs", default=None, help="JSONL jobs file (overrides lookup)")
    ap.add_argument("--binary", default=None, help="cb_headless path (overrides lookup)")
    ap.add_argument(
        "--corpus-path",
        default=None,
        help="Corpus root for Programdata/headless_jobs.jsonl lookup",
    )
    ap.add_argument(
        "--require",
        action="store_true",
        help="Fail if jobs are configured but binary is missing (default behaviour)",
    )
    ap.add_argument(
        "--allow-missing-binary",
        action="store_true",
        help="If jobs exist but binary is missing, warn and exit 0",
    )
    ap.add_argument(
        "--skip",
        action="store_true",
        help="Force no-op (also set by SKIP_HEADLESS_CB=1)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands only; do not spawn cb_headless",
    )
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.skip or os.environ.get("SKIP_HEADLESS_CB", "").strip() in ("1", "true", "yes"):
        print("[headless-cb] skipped (SKIP_HEADLESS_CB / --skip)")
        return 0

    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        repo_root = Path(__file__).resolve().parent.parent

    corpus_path = args.corpus_path or os.environ.get("CORPUS_PATH") or None
    jobs_path = resolve_jobs_path(
        repo_root, explicit=args.jobs, corpus_path=corpus_path
    )
    if jobs_path is None:
        print("[headless-cb] no jobs file — skip (HTML assumed prebuilt)")
        return 0
    if not jobs_path.is_file():
        print(f"[headless-cb] jobs path not found: {jobs_path}", file=sys.stderr)
        return 2

    try:
        jobs = load_jobs(jobs_path)
    except ValueError as exc:
        print(f"[headless-cb] {exc}", file=sys.stderr)
        return 2

    if not jobs:
        print(f"[headless-cb] empty jobs file ({jobs_path}) — skip")
        return 0

    print(f"[headless-cb] {len(jobs)} job(s) from {jobs_path}")
    binary = resolve_binary(repo_root, args.binary)
    if binary is None:
        msg = (
            "[headless-cb] cb_headless binary not found. "
            "Build with: lazbuild Corpus_builder/PSRCBuilder/cb_headless.lpi "
            "or set CB_HEADLESS=/path/to/cb_headless"
        )
        if args.allow_missing_binary:
            print(msg + " — continuing (--allow-missing-binary)", file=sys.stderr)
            return 0
        print(msg, file=sys.stderr)
        return 1

    print(f"[headless-cb] binary: {binary}")
    return run_jobs(
        jobs,
        binary=binary,
        repo_root=repo_root,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
