"""State-migration properties for canonical references (H1925, B3/B5).

Criterion B5: *migration can be rerun safely and rolled back/recovered from its
recorded backup.* Nothing here is a smoke test — each function asserts one
property the plan requires by name: idempotent, ordered, checksum-guarded,
reversible, recoverable.
"""
import sqlite3

import pytest

from app.canonical_state_migrations import (
    MIGRATIONS,
    Migration,
    MigrationChecksumError,
    applied_migrations,
    apply_migrations,
    backup_state_db,
    restore_state_db,
    rollback_to,
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


def test_migration_adds_canonical_columns_and_mapping_table(tmp_path):
    path = make_state(tmp_path / "state.db")
    applied = apply_migrations(path)

    assert applied == [1, 2]
    assert {"source_slug", "canonical_id", "corpus_version", "ref_status"} <= _columns(
        path, "corrections"
    )
    assert "legacy_ref_map" in _tables(path)


def test_rerun_is_idempotent(tmp_path):
    path = make_state(tmp_path / "state.db")
    apply_migrations(path)
    assert apply_migrations(path) == []  # nothing left to do
    assert set(applied_migrations(path)) == {1, 2}


def test_editing_an_applied_migration_fails_loudly(tmp_path):
    path = make_state(tmp_path / "state.db")
    apply_migrations(path)

    tampered = (
        Migration(
            id=MIGRATIONS[0].id,
            name=MIGRATIONS[0].name,
            up=MIGRATIONS[0].up + ("ALTER TABLE corrections ADD COLUMN sneaky TEXT",),
            down=MIGRATIONS[0].down,
        ),
    )
    with pytest.raises(MigrationChecksumError) as exc:
        apply_migrations(path, tampered)
    assert "edited after it was applied" in str(exc.value)
    # And the tampered statement did NOT run.
    assert "sneaky" not in _columns(path, "corrections")


def test_rollback_reverses_in_order(tmp_path):
    path = make_state(tmp_path / "state.db")
    apply_migrations(path)

    assert rollback_to(path, 0) == [2, 1]
    assert applied_migrations(path) == {}
    assert "legacy_ref_map" not in _tables(path)
    # SQLite >= 3.35 drops the columns outright; older builds keep them (the
    # down step is tolerant). Either way the mapping table is gone and the
    # ledger is empty, so a re-apply is clean.
    assert apply_migrations(path) == [1, 2]


def test_partial_rollback_keeps_earlier_migrations(tmp_path):
    path = make_state(tmp_path / "state.db")
    apply_migrations(path)
    assert rollback_to(path, 1) == [2]
    assert set(applied_migrations(path)) == {1}
    assert "legacy_ref_map" in _tables(path)


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


def test_failed_migration_leaves_no_ledger_row(tmp_path):
    path = make_state(tmp_path / "state.db")
    broken = (
        Migration(
            id=1,
            name="broken",
            up=("CREATE TABLE ok_marker (x INTEGER)", "THIS IS NOT SQL"),
            down=("DROP TABLE IF EXISTS ok_marker",),
        ),
    )
    with pytest.raises(sqlite3.OperationalError):
        apply_migrations(path, broken)
    assert applied_migrations(path) == {}
    # Transactional, not just unrecorded: the statement that DID succeed before
    # the failure is rolled back too, so a retry starts from a clean schema.
    assert "ok_marker" not in _tables(path)
