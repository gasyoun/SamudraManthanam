"""Atomic corpus publish workflow.

Usage
-----
  python ingest/publish.py \\
      --corpus-path /path/to/corpus \\
      --db-path     /app/corpus.db  \\
      --next-db-path /app/corpus.next.db \\
      --backup-dir  /app/backups

Steps
-----
1. validate_corpus() — hard stop on any error.
2. ingest() into a temp DB (next-db-path).
3. integrity_check() on the temp DB.
4. smoke_check() — ensure source/line counts look sane.
5. do_backup() — copy current live DB aside.
6. atomic_swap() — replace live DB with the temp DB.
"""
import argparse
import asyncio
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Ensure the web/ directory is on the path so ingest imports resolve.
_script_dir = os.path.dirname(os.path.abspath(__file__))
_web_dir = os.path.dirname(_script_dir)
if _web_dir not in sys.path:
    sys.path.insert(0, _web_dir)

from ingest.ingest import ingest as _run_ingest  # noqa: E402
from ingest.validate import validate_corpus       # noqa: E402


# ── Individual steps ──────────────────────────────────────────────────────────

def integrity_check(db_path: str) -> bool:
    """Run SQLite PRAGMA integrity_check. Returns True iff the DB is healthy."""
    con = None
    try:
        con = sqlite3.connect(db_path)
        cur = con.execute("PRAGMA integrity_check")
        rows = cur.fetchall()
        return rows == [("ok",)]
    except Exception as exc:
        print(f"integrity_check failed: {exc}", file=sys.stderr)
        return False
    finally:
        if con is not None:
            con.close()


def smoke_check(db_path: str) -> tuple[int, int]:
    """Return (source_count, line_count) from the freshly built DB."""
    con = sqlite3.connect(db_path)
    try:
        src_count = con.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        line_count = con.execute("SELECT COUNT(*) FROM corpus_lines").fetchone()[0]
    finally:
        con.close()
    return src_count, line_count


def do_backup(db_path: str, backup_dir: str) -> str | None:
    """Copy the current live DB to backup_dir with a timestamp suffix.

    Returns the backup path, or None if the live DB doesn't exist yet.
    """
    if not os.path.exists(db_path):
        return None
    os.makedirs(backup_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    stem = Path(db_path).stem
    backup_path = os.path.join(backup_dir, f"{stem}_{ts}.db")
    shutil.copy2(db_path, backup_path)
    print(f"Backup written to {backup_path}")
    return backup_path


def atomic_swap(next_db: str, db_path: str) -> None:
    """Replace the live DB with the freshly built one atomically."""
    Path(next_db).replace(db_path)
    print(f"Swapped {next_db} → {db_path}")


# ── Orchestrator ──────────────────────────────────────────────────────────────

def publish(
    corpus_path: str,
    db_path: str,
    next_db_path: str,
    backup_dir: str = "backups",
    force: bool = False,
    min_sources: int = 1,
) -> bool:
    """Run the full publish pipeline. Returns True on success."""

    print("Step 1/6  Validating corpus…")
    report = validate_corpus(corpus_path)
    report.print_summary()
    if not report.ok:
        print("Publish aborted: validation errors must be resolved first.")
        return False

    print("Step 2/6  Ingesting corpus into temp DB…")
    if os.path.exists(next_db_path):
        os.remove(next_db_path)
    asyncio.run(_run_ingest(corpus_path, next_db_path))

    print("Step 3/6  Running integrity check…")
    if not integrity_check(next_db_path):
        print("Publish aborted: PRAGMA integrity_check failed.", file=sys.stderr)
        if os.path.exists(next_db_path):
            os.remove(next_db_path)
        return False

    print("Step 4/6  Smoke-checking row counts…")
    src_count, line_count = smoke_check(next_db_path)
    print(f"  sources={src_count}  lines={line_count}")
    if src_count < min_sources:
        msg = f"Publish aborted: expected ≥{min_sources} sources, got {src_count}."
        print(msg, file=sys.stderr)
        if not force:
            if os.path.exists(next_db_path):
                os.remove(next_db_path)
            return False
        print("  --force set, continuing despite low source count.")

    print("Step 5/6  Backing up current DB…")
    backup = do_backup(db_path, backup_dir)
    if backup is None:
        print("  No existing DB to back up (fresh install).")

    print("Step 6/6  Atomic swap…")
    atomic_swap(next_db_path, db_path)

    print("Publish complete.")
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate, ingest, and atomically publish the corpus DB."
    )
    parser.add_argument("--corpus-path", required=True,
                        help="Directory containing Data/ and Programdata/")
    parser.add_argument("--db-path", default="corpus.db",
                        help="Path to the live corpus DB (default: corpus.db)")
    parser.add_argument("--next-db-path", default="corpus.next.db",
                        help="Temp DB built before swap (default: corpus.next.db)")
    parser.add_argument("--backup-dir", default="backups",
                        help="Directory for backup copies (default: backups/)")
    parser.add_argument("--min-sources", type=int, default=1,
                        help="Minimum expected source count (default: 1)")
    parser.add_argument("--force", action="store_true",
                        help="Skip smoke-check abort (still logs the warning)")
    args = parser.parse_args()

    success = publish(
        corpus_path=args.corpus_path,
        db_path=args.db_path,
        next_db_path=args.next_db_path,
        backup_dir=args.backup_dir,
        force=args.force,
        min_sources=args.min_sources,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
