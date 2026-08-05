"""D1 acceptance — ordered, checksum-tracked state migrations (H1927).

Covers VERIFICATION D1: "Applied state migrations are ordered, checksum-recorded,
and reject later edits", plus the adoption path for a state.db that predates the
runner (which is what every existing deployment is).
"""

import aiosqlite
import pytest

from app.migrations.runner import (
    MigrationChecksumError,
    MigrationError,
    MigrationMissingError,
    apply_migrations,
    discover_migrations,
    split_statements,
    state_migrations_dir,
)


@pytest.fixture
def migrations_dir(tmp_path):
    d = tmp_path / "state"
    d.mkdir()
    return d


def _write(d, name, sql):
    (d / name).write_text(sql, encoding="utf-8")


# ---------------------------------------------------------------------------
# Discovery and ordering
# ---------------------------------------------------------------------------

def test_migrations_are_discovered_in_numeric_order(migrations_dir):
    # Written out of order, and 0010 would sort before 0002 lexically if the
    # zero-padding were ever dropped.
    _write(migrations_dir, "0010_ten.sql", "SELECT 1;")
    _write(migrations_dir, "0002_two.sql", "SELECT 1;")
    _write(migrations_dir, "0001_one.sql", "SELECT 1;")

    versions = [m.version for m in discover_migrations(migrations_dir)]
    assert versions == ["0001", "0002", "0010"]


def test_duplicate_version_is_refused(migrations_dir):
    _write(migrations_dir, "0001_one.sql", "SELECT 1;")
    _write(migrations_dir, "0001_also_one.sql", "SELECT 2;")

    with pytest.raises(MigrationError, match="Duplicate migration version"):
        discover_migrations(migrations_dir)


def test_malformed_filename_is_refused(migrations_dir):
    _write(migrations_dir, "add_a_column.sql", "SELECT 1;")

    with pytest.raises(MigrationError, match="does not match"):
        discover_migrations(migrations_dir)


def test_checksum_ignores_line_ending_style(migrations_dir, tmp_path):
    """A CRLF checkout must not change the checksum.

    This repo is authored on Windows and cloned on Linux CI. If line endings
    fed the hash, every migration would look edited on the other platform and
    every deployment would refuse to start.
    """
    lf = tmp_path / "lf"
    crlf = tmp_path / "crlf"
    lf.mkdir()
    crlf.mkdir()
    (lf / "0001_x.sql").write_bytes(b"CREATE TABLE t (a INT);\nSELECT 1;\n")
    (crlf / "0001_x.sql").write_bytes(b"CREATE TABLE t (a INT);\r\nSELECT 1;\r\n")

    assert (
        discover_migrations(lf)[0].checksum == discover_migrations(crlf)[0].checksum
    )


# ---------------------------------------------------------------------------
# Statement splitting
# ---------------------------------------------------------------------------

def test_semicolon_inside_string_literal_does_not_split():
    stmts = split_statements("INSERT INTO t VALUES ('a;b');\nSELECT 1;")
    assert len(stmts) == 2
    assert "'a;b'" in stmts[0][0]


def test_semicolon_inside_comment_does_not_split():
    stmts = split_statements("-- a comment with ; in it\nSELECT 1;")
    assert len(stmts) == 1


def test_idempotent_directive_binds_to_next_statement_only():
    stmts = split_statements(
        "-- @idempotent-error: duplicate column name\n"
        "ALTER TABLE users ADD COLUMN a TEXT;\n"
        "ALTER TABLE users ADD COLUMN b TEXT;\n"
    )
    assert len(stmts) == 2
    assert stmts[0][1] == "duplicate column name"
    assert stmts[1][1] is None, "directive must not leak onto the following statement"


# ---------------------------------------------------------------------------
# Apply / re-apply / tamper
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_apply_then_rerun_is_a_noop(tmp_path, migrations_dir):
    _write(migrations_dir, "0001_one.sql", "CREATE TABLE a (x INT);")
    _write(migrations_dir, "0002_two.sql", "CREATE TABLE b (y INT);")
    db_path = str(tmp_path / "state.db")

    db = await aiosqlite.connect(db_path)
    try:
        assert await apply_migrations(db, migrations_dir) == ["0001", "0002"]
        # Second run applies nothing and does not blow up on the existing tables.
        assert await apply_migrations(db, migrations_dir) == []
        async with db.execute("SELECT COUNT(*) FROM schema_migrations") as cur:
            assert (await cur.fetchone())[0] == 2
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_editing_an_applied_migration_is_refused(tmp_path, migrations_dir):
    _write(migrations_dir, "0001_one.sql", "CREATE TABLE a (x INT);")
    db_path = str(tmp_path / "state.db")

    db = await aiosqlite.connect(db_path)
    try:
        await apply_migrations(db, migrations_dir)
        _write(migrations_dir, "0001_one.sql", "CREATE TABLE a (x INT, z INT);")
        with pytest.raises(MigrationChecksumError, match="edited after"):
            await apply_migrations(db, migrations_dir)
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_tampered_migration_is_refused_before_anything_is_applied(
    tmp_path, migrations_dir
):
    """Verification happens up front — a tampered 0001 must not let 0002 land."""
    _write(migrations_dir, "0001_one.sql", "CREATE TABLE a (x INT);")
    db_path = str(tmp_path / "state.db")

    db = await aiosqlite.connect(db_path)
    try:
        await apply_migrations(db, migrations_dir)
        _write(migrations_dir, "0001_one.sql", "CREATE TABLE a (x INT, z INT);")
        _write(migrations_dir, "0002_two.sql", "CREATE TABLE b (y INT);")
        with pytest.raises(MigrationChecksumError):
            await apply_migrations(db, migrations_dir)

        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='b'"
        ) as cur:
            assert await cur.fetchone() is None, "0002 applied despite the refusal"
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_missing_applied_migration_is_refused(tmp_path, migrations_dir):
    _write(migrations_dir, "0001_one.sql", "CREATE TABLE a (x INT);")
    db_path = str(tmp_path / "state.db")

    db = await aiosqlite.connect(db_path)
    try:
        await apply_migrations(db, migrations_dir)
        (migrations_dir / "0001_one.sql").unlink()
        with pytest.raises(MigrationMissingError, match="ahead of this code"):
            await apply_migrations(db, migrations_dir)
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_failing_statement_raises_rather_than_recording_success(
    tmp_path, migrations_dir
):
    _write(migrations_dir, "0001_bad.sql", "CREATE TABLE a (x INT);\nNOT SQL AT ALL;")
    db_path = str(tmp_path / "state.db")

    db = await aiosqlite.connect(db_path)
    try:
        with pytest.raises(MigrationError):
            await apply_migrations(db, migrations_dir)
        async with db.execute("SELECT COUNT(*) FROM schema_migrations") as cur:
            assert (await cur.fetchone())[0] == 0
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_idempotent_error_directive_is_narrow(tmp_path, migrations_dir):
    """The tolerated error applies to its own statement, not to the file."""
    _write(migrations_dir, "0001_base.sql", "CREATE TABLE users (id INT);")
    _write(
        migrations_dir,
        "0002_alter.sql",
        "-- @idempotent-error: duplicate column name\n"
        "ALTER TABLE users ADD COLUMN email TEXT;\n"
        "ALTER TABLE nonexistent_table ADD COLUMN whatever TEXT;\n",
    )
    db_path = str(tmp_path / "state.db")

    db = await aiosqlite.connect(db_path)
    try:
        with pytest.raises(MigrationError, match="nonexistent_table|no such table"):
            await apply_migrations(db, migrations_dir)
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# The real migration set
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_real_migrations_build_the_expected_schema(tmp_path):
    from app.migrations.runner import apply_migrations as apply

    db_path = str(tmp_path / "state.db")
    db = await aiosqlite.connect(db_path)
    try:
        applied = await apply(db, state_migrations_dir())
        assert applied, "no migrations shipped"

        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ) as cur:
            tables = {row[0] for row in await cur.fetchall()}
        assert {
            "migrations",
            "morph_cache",
            "users",
            "consent",
            "corrections",
            "ai_cache",
            "schema_migrations",
        } <= tables

        async with db.execute("PRAGMA table_info(users)") as cur:
            cols = {row[1] for row in await cur.fetchall()}
        assert {
            "telegram_username",
            "utm_source",
            "utm_medium",
            "utm_campaign",
        } <= cols
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_preexisting_state_db_is_adopted_without_loss(tmp_path):
    """The adoption path every live deployment will actually take.

    A state.db created by the OLD inline init_state_db — tables present, no
    schema_migrations table, users already carrying the marketing columns —
    must be adopted by the runner with its rows intact.
    """
    db_path = str(tmp_path / "legacy_state.db")
    db = await aiosqlite.connect(db_path)
    try:
        # Simulate the pre-H1927 schema, including the ALTERed columns.
        await db.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, "
            "name TEXT, created_at TEXT NOT NULL)"
        )
        for col in ("telegram_username", "utm_source", "utm_medium", "utm_campaign"):
            await db.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        await db.execute(
            "INSERT INTO users (id, email, name, created_at) "
            "VALUES (1, 'a@example.com', 'A', '2026-01-01')"
        )
        await db.commit()

        applied = await apply_migrations(db, state_migrations_dir())
        assert applied == ["0001", "0002"]

        async with db.execute("SELECT email FROM users WHERE id = 1") as cur:
            assert (await cur.fetchone())[0] == "a@example.com"

        # And a second startup is quiet.
        assert await apply_migrations(db, state_migrations_dir()) == []
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_init_state_db_delegates_to_the_runner(tmp_path, monkeypatch):
    """init_state_db must go through the runner, not re-inline the schema."""
    from app import state_db as state_db_module

    db_path = str(tmp_path / "state.db")
    db = await aiosqlite.connect(db_path)
    try:
        await state_db_module.init_state_db(db)
        async with db.execute("SELECT version FROM schema_migrations ORDER BY version") as cur:
            versions = [row[0] for row in await cur.fetchall()]
        assert versions == ["0001", "0002"]

        async with db.execute("PRAGMA journal_mode") as cur:
            assert (await cur.fetchone())[0].lower() == "wal"
    finally:
        await db.close()
