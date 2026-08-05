"""Ordered, checksum-tracked SQL migration runner for the mutable state DB.

Why not Alembic/yoyo: the application's whole persistence layer is stdlib
``sqlite3`` + ``aiosqlite``, and the Lane D guardrail is explicit that no new
framework or repository-wide layering scheme may be introduced. Both of those
tools bring a migration DSL, a CLI, and (for Alembic) SQLAlchemy. What Lane D
actually asks for is narrow: *ordered files, recorded checksums, and a refusal
to run when an applied migration was edited afterwards.* That is this module.

Contract
--------
* Migration files live in ``<dir>/NNNN_<slug>.sql``, applied in numeric order.
* Each applied migration is recorded in ``schema_migrations`` with the SHA-256
  of its **newline-normalised** bytes. Normalisation matters: this repo is
  developed on Windows and cloned on Linux CI, so a CRLF checkout would
  otherwise change every checksum and fail every deployment.
* Re-running is a no-op. Editing a file that was already applied is an error,
  not a silent divergence — that is the whole point of recording checksums.
* A recorded migration whose file has vanished is also an error: the DB is
  ahead of the code, which usually means a rollback deployed old code onto a
  migrated database.

Idempotent-error directive
--------------------------
SQLite cannot express a conditional ``ALTER TABLE``, but this project has
long-lived state DBs that may already carry columns a migration adds. Rather
than hand-wave that with a blanket try/except around the whole file, a single
statement may be preceded by::

    -- @idempotent-error: duplicate column name
    ALTER TABLE users ADD COLUMN telegram_username TEXT;

Only that statement, and only an error whose text contains that substring, is
swallowed. The directive is per-statement and auditable in review; a blanket
exemption is not.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_FILENAME_RE = re.compile(r"^(\d{4})_([A-Za-z0-9._-]+)\.sql$")
_DIRECTIVE_RE = re.compile(r"^\s*--\s*@idempotent-error:\s*(.+?)\s*$", re.IGNORECASE)

CREATE_SCHEMA_MIGRATIONS = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    checksum   TEXT NOT NULL,
    applied_at TEXT NOT NULL
)
"""


class MigrationError(Exception):
    """Base class for every refusal raised by the runner."""


class MigrationChecksumError(MigrationError):
    """An already-applied migration file was edited after it was applied."""


class MigrationMissingError(MigrationError):
    """The DB records a migration that no longer exists on disk."""


@dataclass(frozen=True)
class Migration:
    version: str
    name: str
    path: Path
    sql: str
    checksum: str


def state_migrations_dir() -> Path:
    """Directory holding the ``state.db`` migration files."""
    return Path(__file__).resolve().parent / "state"


def _normalise(raw: bytes) -> str:
    """Decode UTF-8 and collapse CRLF/CR to LF.

    Checksums must be identical for a Windows working copy and a Linux CI
    checkout of the same commit, whatever ``core.autocrlf`` did to the file.
    """
    return raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def discover_migrations(directory: Path | str | None = None) -> list[Migration]:
    """Return every migration in ``directory``, ordered by numeric version.

    Raises MigrationError on a duplicate version number — two files claiming
    ``0003`` would apply in an order that depends on the filesystem.
    """
    directory = Path(directory) if directory is not None else state_migrations_dir()
    if not directory.is_dir():
        return []

    found: dict[str, Migration] = {}
    for path in sorted(directory.iterdir()):
        if path.suffix != ".sql" or not path.is_file():
            continue
        match = _FILENAME_RE.match(path.name)
        if not match:
            raise MigrationError(
                f"Migration filename does not match NNNN_slug.sql: {path.name}"
            )
        version, name = match.group(1), match.group(2)
        if version in found:
            raise MigrationError(
                f"Duplicate migration version {version}: "
                f"{found[version].path.name} and {path.name}"
            )
        sql = _normalise(path.read_bytes())
        found[version] = Migration(
            version=version, name=name, path=path, sql=sql, checksum=_checksum(sql)
        )

    return [found[v] for v in sorted(found)]


def _has_sql(statement: str) -> bool:
    """True if anything remains once blank lines and ``--`` comments are removed.

    Migration files open with a comment header, which the splitter naturally
    carries into the first chunk. Handing SQLite a comment-only string is not
    worth finding out about at deploy time.
    """
    for line in statement.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("--"):
            return True
    return False


def split_statements(sql: str) -> list[tuple[str, str | None]]:
    """Split a migration into ``(statement, idempotent_error_substring)`` pairs.

    A hand-rolled splitter rather than ``executescript`` because the directive
    above is per-statement, which needs statement boundaries. It tracks
    single-quoted string literals and ``--`` line comments so a semicolon
    inside either does not end a statement.

    A directive line applies to the next statement that closes, and is consumed
    by it — so it can never leak onto the statement after that.
    """
    statements: list[tuple[str, str | None]] = []
    buffer: list[str] = []
    pending_directive: str | None = None

    for line in sql.splitlines():
        directive = _DIRECTIVE_RE.match(line)
        if directive:
            pending_directive = directive.group(1)
            continue

        buffer.append(line)
        joined = "\n".join(buffer)

        # Does this line close a statement? Scan for an unquoted ';'.
        in_string = False
        idx = 0
        cut_at: int | None = None
        while idx < len(line):
            ch = line[idx]
            if in_string:
                if ch == "'":
                    # '' is an escaped quote inside a literal.
                    if idx + 1 < len(line) and line[idx + 1] == "'":
                        idx += 1
                    else:
                        in_string = False
            elif ch == "'":
                in_string = True
            elif ch == "-" and line[idx : idx + 2] == "--":
                break
            elif ch == ";":
                cut_at = idx
                break
            idx += 1

        if cut_at is not None:
            head = joined[: len(joined) - (len(line) - cut_at)]
            statement = head.strip()
            if _has_sql(statement):
                statements.append((statement, pending_directive))
                pending_directive = None
            remainder = line[cut_at + 1 :]
            buffer = [remainder] if remainder.strip() else []

    tail = "\n".join(buffer).strip()
    if _has_sql(tail):
        statements.append((tail, pending_directive))
    return statements


async def _applied_rows(db) -> dict[str, tuple[str, str]]:
    async with db.execute(
        "SELECT version, name, checksum FROM schema_migrations"
    ) as cursor:
        return {row[0]: (row[1], row[2]) for row in await cursor.fetchall()}


async def apply_migrations(db, directory: Path | str | None = None) -> list[str]:
    """Apply every pending migration in order. Returns the versions applied.

    Verification is done *before* anything is applied, so a tampered file is
    refused without half-migrating the database.
    """
    migrations = discover_migrations(directory)
    await db.execute(CREATE_SCHEMA_MIGRATIONS)
    await db.commit()

    applied = await _applied_rows(db)
    on_disk = {m.version for m in migrations}

    for version in sorted(applied):
        if version not in on_disk:
            raise MigrationMissingError(
                f"Migration {version} ({applied[version][0]}) is recorded as applied "
                f"but no longer exists on disk. The database is ahead of this code — "
                f"deploy the matching revision rather than continuing."
            )

    for migration in migrations:
        record = applied.get(migration.version)
        if record and record[1] != migration.checksum:
            raise MigrationChecksumError(
                f"Migration {migration.version}_{migration.name}.sql was edited after "
                f"it was applied (recorded {record[1][:12]}…, file {migration.checksum[:12]}…). "
                f"Applied migrations are immutable — add a new migration instead."
            )

    newly_applied: list[str] = []
    for migration in migrations:
        if migration.version in applied:
            continue
        for statement, tolerated in split_statements(migration.sql):
            try:
                await db.execute(statement)
            except Exception as exc:  # noqa: BLE001 — re-raised unless tolerated
                if tolerated and tolerated.lower() in str(exc).lower():
                    continue
                first_sql_line = next(
                    (
                        ln.strip()
                        for ln in statement.splitlines()
                        if ln.strip() and not ln.strip().startswith("--")
                    ),
                    statement.strip(),
                )
                raise MigrationError(
                    f"Migration {migration.version}_{migration.name}.sql failed on "
                    f"statement: {first_sql_line[:120]} — {exc}"
                ) from exc
        await db.execute(
            "INSERT INTO schema_migrations (version, name, checksum, applied_at) "
            "VALUES (?, ?, ?, ?)",
            (
                migration.version,
                migration.name,
                migration.checksum,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        await db.commit()
        newly_applied.append(migration.version)

    return newly_applied
