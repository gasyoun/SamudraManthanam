"""Ordered, checksum-tracked state migrations for canonical corpus references.

Lane B / B3. Adds to ``state.db``:

- canonical-reference columns on ``corrections``
  (``source_slug``, ``canonical_id``, ``corpus_version``, ``ref_status``);
- ``legacy_ref_map`` — the mapping from a legacy ordinal tuple
  ``(corpus_version, source_id, line_num)`` to a canonical ``(source_slug,
  canonical_id)``, built by backfilling from a **pinned** corpus;
- ``canonical_ref_migrations`` — the applied-migration ledger, storing each
  migration's checksum so an edited-after-apply migration fails loudly instead
  of drifting.

Properties this module guarantees, in the order the verification table (B5, B3)
asks for them:

- **idempotent** — re-running applies nothing and changes nothing;
- **transactional** — each migration commits as a unit or not at all;
- **reversible** — every migration ships a ``down`` and :func:`rollback_to`
  executes them in reverse, with :func:`backup_state_db` as the recorded
  physical fallback for the SQLite versions that cannot drop a column.

Deliberately sync (``sqlite3``), not ``aiosqlite``: this is one engine used by
both the async app (via ``asyncio.to_thread``) and the plain scripts, rather
than two engines that can drift apart. Lane D (H1927) owns the *general*
migration runner for state schema; this module is scoped to the canonical
reference columns and is written to be absorbed by that runner without changing
its ledger semantics.
"""
from __future__ import annotations

import datetime
import hashlib
import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

LEDGER_TABLE = "canonical_ref_migrations"


class MigrationChecksumError(RuntimeError):
    """An already-applied migration's SQL was edited after the fact."""


@dataclass(frozen=True)
class Migration:
    id: int
    name: str
    up: tuple[str, ...]
    down: tuple[str, ...]

    @property
    def checksum(self) -> str:
        payload = "\n".join(s.strip() for s in self.up)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        id=1,
        name="canonical_reference_columns",
        up=(
            "ALTER TABLE corrections ADD COLUMN source_slug TEXT",
            "ALTER TABLE corrections ADD COLUMN canonical_id TEXT",
            "ALTER TABLE corrections ADD COLUMN corpus_version TEXT",
            # How the stored reference was resolved when the row was written or
            # backfilled: one of canonical / legacy_mapped / legacy_direct /
            # unresolved. Keeps an un-backfillable row visible instead of
            # letting it look canonical.
            "ALTER TABLE corrections ADD COLUMN ref_status TEXT",
            """
            CREATE TABLE IF NOT EXISTS legacy_ref_map (
                corpus_version TEXT    NOT NULL,
                source_id      INTEGER NOT NULL,
                line_num       INTEGER NOT NULL,
                source_slug    TEXT    NOT NULL,
                canonical_id   TEXT    NOT NULL,
                fingerprint    TEXT,
                created_at     TEXT    NOT NULL,
                PRIMARY KEY (corpus_version, source_id, line_num)
            )
            """,
        ),
        down=(
            "DROP TABLE IF EXISTS legacy_ref_map",
            "ALTER TABLE corrections DROP COLUMN ref_status",
            "ALTER TABLE corrections DROP COLUMN corpus_version",
            "ALTER TABLE corrections DROP COLUMN canonical_id",
            "ALTER TABLE corrections DROP COLUMN source_slug",
        ),
    ),
    Migration(
        id=2,
        name="canonical_reference_indices",
        up=(
            "CREATE INDEX IF NOT EXISTS idx_corrections_canonical "
            "ON corrections(source_slug, canonical_id)",
            "CREATE INDEX IF NOT EXISTS idx_corrections_ref_status "
            "ON corrections(ref_status)",
            "CREATE INDEX IF NOT EXISTS idx_legacy_ref_map_canonical "
            "ON legacy_ref_map(source_slug, canonical_id)",
        ),
        down=(
            "DROP INDEX IF EXISTS idx_legacy_ref_map_canonical",
            "DROP INDEX IF EXISTS idx_corrections_ref_status",
            "DROP INDEX IF EXISTS idx_corrections_canonical",
        ),
    ),
)


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _ensure_ledger(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {LEDGER_TABLE} (
            id         INTEGER PRIMARY KEY,
            name       TEXT NOT NULL,
            checksum   TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )


def _applied(conn: sqlite3.Connection) -> dict[int, tuple[str, str]]:
    _ensure_ledger(conn)
    rows = conn.execute(f"SELECT id, name, checksum FROM {LEDGER_TABLE}").fetchall()
    return {int(r[0]): (r[1], r[2]) for r in rows}


def _execute_tolerant(conn: sqlite3.Connection, statement: str) -> None:
    """Run one DDL statement, tolerating the two benign SQLite races.

    ``ALTER TABLE … ADD COLUMN`` has no ``IF NOT EXISTS`` form, and ``DROP
    COLUMN`` is unsupported before SQLite 3.35. A pre-existing column (an older
    manual patch, or a second worker winning the race) and a missing column on
    the way down are both no-ops, not failures — anything else propagates.
    """
    try:
        conn.execute(statement)
    except sqlite3.OperationalError as exc:
        msg = str(exc).lower()
        benign = (
            "duplicate column name" in msg
            or "no such column" in msg
            or "near \"drop\"" in msg  # SQLite < 3.35 cannot DROP COLUMN
        )
        if not benign:
            raise


def apply_migrations(
    db_path: str | Path, migrations: Sequence[Migration] = MIGRATIONS
) -> list[int]:
    """Apply every not-yet-applied migration. Returns the ids actually applied.

    Raises :class:`MigrationChecksumError` when an applied migration's SQL no
    longer hashes to the recorded checksum — the edited-after-apply case the
    verification table (D1, and B5's rerun-safety criterion) requires to fail
    rather than silently diverge.
    """
    conn = sqlite3.connect(str(db_path))
    # Explicit transaction control. Python's sqlite3 opens a transaction only
    # for DML, so with the default isolation level every DDL statement
    # auto-commits — a migration that fails halfway would leave half a schema
    # behind and no ledger row explaining it. SQLite itself is transactional
    # over DDL; we just have to ask for the transaction.
    conn.isolation_level = None
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        applied = _applied(conn)
        for m in migrations:
            if m.id in applied:
                recorded_checksum = applied[m.id][1]
                if recorded_checksum != m.checksum:
                    raise MigrationChecksumError(
                        f"migration {m.id} ({m.name}) was edited after it was applied: "
                        f"recorded {recorded_checksum[:12]}…, now {m.checksum[:12]}…"
                    )
        done: list[int] = []
        for m in migrations:
            if m.id in applied:
                continue
            conn.execute("BEGIN")
            try:
                for stmt in m.up:
                    _execute_tolerant(conn, stmt)
                conn.execute(
                    f"INSERT INTO {LEDGER_TABLE} (id, name, checksum, applied_at) "
                    "VALUES (?, ?, ?, ?)",
                    (m.id, m.name, m.checksum, _now()),
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
            done.append(m.id)
        return done
    finally:
        conn.close()


def rollback_to(
    db_path: str | Path, target_id: int, migrations: Sequence[Migration] = MIGRATIONS
) -> list[int]:
    """Reverse every applied migration with ``id > target_id``, newest first."""
    conn = sqlite3.connect(str(db_path))
    conn.isolation_level = None
    try:
        applied = _applied(conn)
        undone: list[int] = []
        for m in sorted(migrations, key=lambda x: -x.id):
            if m.id <= target_id or m.id not in applied:
                continue
            conn.execute("BEGIN")
            try:
                for stmt in m.down:
                    _execute_tolerant(conn, stmt)
                conn.execute(f"DELETE FROM {LEDGER_TABLE} WHERE id = ?", (m.id,))
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
            undone.append(m.id)
        return undone
    finally:
        conn.close()


def applied_migrations(db_path: str | Path) -> dict[int, tuple[str, str]]:
    conn = sqlite3.connect(str(db_path))
    try:
        return _applied(conn)
    finally:
        conn.close()


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


async def ensure_canonical_state(db_path: str | Path) -> list[int]:
    """Async-friendly entry point for the request/lifespan path."""
    import asyncio

    return await asyncio.to_thread(apply_migrations, db_path)
