"""Compatibility shims for the pre-H2354 canonical-reference migration path.

H1925 shipped this module with its own ledger table
``canonical_ref_migrations``. H2354 refiled those SQL steps as
``migrations/state/0004_*.sql`` and ``0005_*.sql`` under the D1 runner
(``app.migrations.runner``). Startup applies one ordered path only.

What remains here is what scripts still need:

- :func:`apply_migrations` / :func:`ensure_canonical_state` — thin wrappers
  over the D1 runner (path-based / async), so
  ``scripts/backfill_canonical_refs.py`` and any defensive call sites keep
  working without a second ledger;
- :func:`backup_state_db` / :func:`restore_state_db` — the physical backup
  half of the backfill safety contract.

The old integer-id ``Migration`` objects, rollback path, and
``canonical_ref_migrations`` writer are gone. A production DB that still
carries rows in that table is adopted once by the D1 runner's bridge (see
``compute_legacy_adoptions``); new applies never write to it.
"""
from __future__ import annotations

import datetime
import shutil
import sqlite3
from pathlib import Path

from app.migrations.runner import (
    MigrationChecksumError,
    apply_migrations_at_path,
)

# Re-export so existing ``from app.canonical_state_migrations import
# MigrationChecksumError`` keep resolving after the absorb.
__all__ = [
    "MigrationChecksumError",
    "apply_migrations",
    "backup_state_db",
    "ensure_canonical_state",
    "restore_state_db",
]


def apply_migrations(db_path: str | Path) -> list[str]:
    """Apply the full D1 state migration set (including 0004/0005).

    Returns the version strings newly applied (e.g. ``['0004', '0005']``),
    not the old integer ids. Callers that only care about "schema is ready"
    need not inspect the list.
    """
    return apply_migrations_at_path(db_path)


def backup_state_db(db_path: str | Path, suffix: str | None = None) -> Path:
    """Copy ``state.db`` beside itself before a destructive step.

    The recorded backup half of B3's "no destructive state migration without
    backup and tested recovery": :func:`restore_state_db` is the tested
    recovery, exercised by ``tests/test_canonical_state_migrations.py``.
    """
    src = Path(db_path)
    stamp = suffix or datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    dst = src.with_name(f"{src.name}.backup-{stamp}")
    # sqlite3's own backup API copies a consistent snapshot even with WAL
    # pages outstanding — a plain file copy can miss them.
    with sqlite3.connect(str(src)) as source, sqlite3.connect(str(dst)) as target:
        source.backup(target)
    return dst


def restore_state_db(backup_path: str | Path, db_path: str | Path) -> None:
    """Restore a backup produced by :func:`backup_state_db`, in place."""
    shutil.copyfile(str(backup_path), str(db_path))


async def ensure_canonical_state(db_path: str | Path) -> list[str]:
    """Async-friendly entry point for the request/lifespan path.

    Prefer :func:`app.migrations.runner.apply_migrations` on the open
    connection (``init_state_db`` already does). This path remains for any
    defensive call that only has a filesystem path.
    """
    import asyncio

    return await asyncio.to_thread(apply_migrations, db_path)
