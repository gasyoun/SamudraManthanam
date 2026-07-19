"""Run the manual full-corpus pytest gate with visible progress and timeouts."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime


sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def main() -> int:
    db_value = os.environ.get("DB_PATH")
    if not db_value:
        print("ERROR: DB_PATH must point to an existing full corpus database.", file=sys.stderr)
        return 2

    db_path = Path(db_value).expanduser().resolve()
    if not db_path.is_file():
        print(f"ERROR: DB_PATH does not exist or is not a file: {db_path}", file=sys.stderr)
        return 2

    if importlib.util.find_spec("pytest_timeout") is None:
        print(
            "ERROR: pytest-timeout is required. Install pytest, pytest-asyncio, "
            "and pytest-timeout before running this launcher.",
            file=sys.stderr,
        )
        return 2

    web_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["DB_PATH"] = str(db_path)
    env["USE_REAL_CORPUS"] = "1"
    env["PYTHONPATH"] = "."
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-m",
        "corpus",
        "-vv",
        "--durations=20",
        "--maxfail=1",
        "--timeout=180",
    ]

    started = datetime.now().astimezone()
    print(f"Start time: {started.isoformat(timespec='seconds')}", flush=True)
    print(f"Working directory: {web_root}", flush=True)
    print(f"DB_PATH: {db_path}", flush=True)
    print(f"Command: {subprocess.list2cmdline(command)}", flush=True)

    completed = subprocess.run(command, cwd=web_root, env=env, check=False)
    finished = datetime.now().astimezone()
    status = "PASS" if completed.returncode == 0 else "FAIL"
    print(
        f"Completion status: {status} (exit code {completed.returncode}) at "
        f"{finished.isoformat(timespec='seconds')}",
        flush=True,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
