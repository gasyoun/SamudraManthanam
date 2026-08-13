#!/usr/bin/env python3
"""Operator check: Samudra .env is not world-readable and the parent cannot
replace it.

Prints a PASS/FAIL table. Never prints secret values.

    python3 scripts/check_env_hardening.py
    python3 scripts/check_env_hardening.py --root /opt/samudra
"""
from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def mode_of(path: Path) -> int:
    return path.stat().st_mode & 0o777


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="/opt/samudra", type=Path)
    args = parser.parse_args()
    root: Path = args.root
    env = root / ".env"
    rows: list[tuple[str, bool, str]] = []

    if not env.is_file():
        print(f"FAIL: {env} missing", file=sys.stderr)
        return 2

    env_mode = mode_of(env)
    rows.append(
        (
            "live .env mode 600",
            env_mode == 0o600,
            f"{env} {env_mode:03o}",
        )
    )
    st = env.stat()
    rows.append(
        (
            "live .env not world-readable",
            not bool(env_mode & stat.S_IROTH),
            f"world_r={bool(env_mode & stat.S_IROTH)}",
        )
    )
    parent_mode = mode_of(root)
    rows.append(
        (
            "parent not group-writable (cannot unlink .env)",
            not bool(parent_mode & stat.S_IWGRP),
            f"{root} {parent_mode:03o} sticky={bool(root.stat().st_mode & stat.S_ISVTX)}",
        )
    )

    world_baks = []
    siblings = []
    for p in sorted(root.glob(".env*")):
        if p.name == ".env":
            continue
        siblings.append(p.name)
        m = mode_of(p)
        if m & stat.S_IROTH:
            world_baks.append(f"{p.name}:{m:03o}")
    rows.append(
        (
            "no world-readable .env* siblings",
            not world_baks,
            ",".join(world_baks) if world_baks else (f"siblings={siblings}" if siblings else "none"),
        )
    )

    if os.name != "nt":
        rows.append(
            (
                "this process cannot read .env unless root/owner",
                os.access(env, os.R_OK) == (os.geteuid() == 0 or os.geteuid() == st.st_uid),
                f"euid={os.geteuid()} readable={os.access(env, os.R_OK)}",
            )
        )

    width = max(len(name) for name, _, _ in rows)
    failed = 0
    for name, ok, detail in rows:
        mark = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"{mark:4}  {name:<{width}}  {detail}")
    print(f"VERDICT={'PASS' if failed == 0 else 'FAIL'}  failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
