"""Canonical-reference schema via the D1 runner (H1925 B absorbed by H2354).

After H2354 there is no second ledger. These tests pin:

* 0004/0005 add the canonical columns + legacy_ref_map through the shared runner;
* a DB that still has ``canonical_ref_migrations`` history is adopted without
  re-running those steps or diverging checksums;
* edited-after-apply still fails;
* backup/restore for the backfill script still works.
"""
import sqlite3

import aiosqlite
import pytest

from app.canonical_state_migrations import (
    apply_migrations,
    backup_state_db,
    restore_state_db,
)
from app.migrations.runner import (
    MigrationChecksumError,
    apply_migrations as apply_async,
    apply_migrations_at_path,
    discover_migrations,
    state_migrations_dir,
)
from canonical_fixtures import make_state


def _columns(path, table):
    conn = sqlite3.connect(path)
    try:
        return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


def _tables(path):
    conn = sqlite3.connect(path)
    try:
        return {
            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()


def _schema_versions(path):
    conn = sqlite3.connect(path)
    try:
        return [
            r[0]
            for r in conn.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            ).fetchall()
        ]
    finally:
        conn.close()


def test_migration_adds_canonical_columns_and_mapping_table(tmp_path):
    path = make_state(tmp_path / "state.db")
    applied = apply_migrations(path)

    assert "0004" in applied
    assert "0005" in applied
    assert {"source_slug", "canonical_id", "corpus_version", "ref_status"} <= _columns(
        path, "corrections"
    )
    assert "legacy_ref_map" in _tables(path)
    assert "0004" in _schema_versions(path)
    assert "0005" in _schema_versions(path)


def test_rerun_is_idempotent(tmp_path):
    path = make_state(tmp_path / "state.db")
    apply_migrations(path)
    assert apply_migrations(path) == []  # nothing left to do
    assert {"0004", "0005"} <= set(_schema_versions(path))


def test_editing_an_applied_migration_fails_loudly(tmp_path):
    """Copy the real set into tmp, apply, then tamper the copy only."""
    import shutil

    src = state_migrations_dir()
    mig_dir = tmp_path / "state"
    shutil.copytree(src, mig_dir)
    path = str(tmp_path / "state.db")
    apply_migrations_at_path(path, mig_dir)

    target = mig_dir / "0004_canonical_reference_columns.sql"
    target.write_bytes(target.read_bytes() + b"\n-- sneaky edit\n")
    with pytest.raises(MigrationChecksumError) as exc:
        apply_migrations_at_path(path, mig_dir)
    assert "edited after" in str(exc.value).lower()


def test_backup_and_restore_round_trip(tmp_path):
    path = make_state(
        tmp_path / "state.db",
        corrections=[{"id": 1, "source_id": 1, "line_num": 1}],
    )
    apply_migrations(path)
    backup = backup_state_db(path)

    conn = sqlite3.connect(path)
    conn.execute("DELETE FROM corrections")
    conn.commit()
    conn.close()
    assert _count(path) == 0

    restore_state_db(backup, path)
    assert _count(path) == 1


def _count(path):
    conn = sqlite3.connect(path)
    try:
        return conn.execute("SELECT COUNT(*) FROM corrections").fetchone()[0]
    finally:
        conn.close()


def _seed_pre_absorb_dual_ledger(path: str) -> None:
    """Shape a state.db as production looked mid-H1925+H1927 dual-ledger era.

    - schema_migrations has 0001–0003 (D1)
    - canonical columns + legacy_ref_map already present
    - canonical_ref_migrations records B migrations 1 and 2 with *old-style*
      checksums that will NOT match the D1 file hashes
    """
    conn = sqlite3.connect(path)
    try:
        # Minimal tables D1 0001 would create; enough for 0004's ALTER targets.
        conn.executescript(
            """
            CREATE TABLE corrections (
                id INTEGER PRIMARY KEY,
                source_id INTEGER NOT NULL,
                line_num INTEGER NOT NULL,
                old_text TEXT NOT NULL,
                new_text TEXT NOT NULL,
                user_id INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                source_slug TEXT,
                canonical_id TEXT,
                corpus_version TEXT,
                ref_status TEXT
            );
            CREATE TABLE legacy_ref_map (
                corpus_version TEXT NOT NULL,
                source_id INTEGER NOT NULL,
                line_num INTEGER NOT NULL,
                source_slug TEXT NOT NULL,
                canonical_id TEXT NOT NULL,
                fingerprint TEXT,
                created_at TEXT NOT NULL,
                PRIMARY KEY (corpus_version, source_id, line_num)
            );
            CREATE TABLE schema_migrations (
                version TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TEXT NOT NULL
            );
            CREATE TABLE canonical_ref_migrations (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TEXT NOT NULL
            );
            """
        )
        # Record 0001–0003 as applied with placeholder checksums that match
        # current files so verification passes for those versions.
        for m in discover_migrations(state_migrations_dir()):
            if m.version in ("0001", "0002", "0003"):
                conn.execute(
                    "INSERT INTO schema_migrations (version, name, checksum, applied_at) "
                    "VALUES (?, ?, ?, ?)",
                    (m.version, m.name, m.checksum, "2026-07-30T00:00:00+00:00"),
                )
        # Old B ledger with deliberately wrong (pre-D1-algorithm) checksums.
        conn.execute(
            "INSERT INTO canonical_ref_migrations (id, name, checksum, applied_at) "
            "VALUES (?, ?, ?, ?)",
            (1, "canonical_reference_columns", "a" * 64, "2026-07-30T00:00:00"),
        )
        conn.execute(
            "INSERT INTO canonical_ref_migrations (id, name, checksum, applied_at) "
            "VALUES (?, ?, ?, ?)",
            (2, "canonical_reference_indices", "b" * 64, "2026-07-30T00:00:00"),
        )
        conn.commit()
    finally:
        conn.close()


def test_dual_ledger_history_is_adopted_without_reapply(tmp_path):
    """The adopt path every dual-ledger production DB will take (H2354).

    B already applied under canonical_ref_migrations; D1 has 0001–0003.
    After one runner pass: 0004/0005 appear in schema_migrations with *current*
    file checksums, SQL is not re-run in a way that fails, and a second pass
    is quiet. Editing 0004 still fails checksum verification.
    """
    path = str(tmp_path / "dual.db")
    _seed_pre_absorb_dual_ledger(path)

    applied = apply_migrations_at_path(path)
    # Bridge records 0004/0005 without listing them as "newly applied" only if
    # we count inserts from the bridge as non-apply. Current contract: bridge
    # rows are not returned in newly_applied (they were already on disk via B).
    # Remaining migrations after 0003 that were NOT bridged would appear —
    # both 0004 and 0005 are bridged, so newly_applied is empty.
    assert applied == []
    versions = _schema_versions(path)
    assert "0004" in versions
    assert "0005" in versions

    # Current file checksums, not the deadbeef placeholders.
    conn = sqlite3.connect(path)
    try:
        for m in discover_migrations(state_migrations_dir()):
            if m.version in ("0004", "0005"):
                row = conn.execute(
                    "SELECT checksum FROM schema_migrations WHERE version = ?",
                    (m.version,),
                ).fetchone()
                assert row[0] == m.checksum
    finally:
        conn.close()

    assert apply_migrations_at_path(path) == []

    # Edited-after-apply still refuses (tamper a *copy*, not the repo tree).
    import shutil

    mig_dir = tmp_path / "state_copy"
    shutil.copytree(state_migrations_dir(), mig_dir)
    # Re-seed schema_migrations checksums against the copy's current bytes
    # (identical to repo until we edit).
    for m in discover_migrations(mig_dir):
        conn = sqlite3.connect(path)
        try:
            conn.execute(
                "UPDATE schema_migrations SET checksum = ? WHERE version = ?",
                (m.checksum, m.version),
            )
            conn.commit()
        finally:
            conn.close()
    (mig_dir / "0005_canonical_reference_indices.sql").write_bytes(
        (mig_dir / "0005_canonical_reference_indices.sql").read_bytes() + b"\n-- tamper\n"
    )
    with pytest.raises(MigrationChecksumError):
        apply_migrations_at_path(path, mig_dir)


@pytest.mark.asyncio
async def test_async_runner_adopts_dual_ledger(tmp_path):
    path = str(tmp_path / "dual_async.db")
    _seed_pre_absorb_dual_ledger(path)

    db = await aiosqlite.connect(path)
    try:
        newly = await apply_async(db, state_migrations_dir())
        assert newly == []
        async with db.execute(
            "SELECT version FROM schema_migrations WHERE version IN ('0004','0005') "
            "ORDER BY version"
        ) as cur:
            rows = [r[0] for r in await cur.fetchall()]
        assert rows == ["0004", "0005"]
    finally:
        await db.close()
