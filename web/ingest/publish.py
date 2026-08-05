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
1. validate — with `--manifest`, open and hash the canonical JSONL that is about
   to be published; otherwise fall back to the legacy HTML-tree check.
2. ingest() into a temp DB (next-db-path).
3. integrity_check() on the temp DB.
4. smoke_check() — ensure source/line counts look sane.
5. do_backup() — copy current live DB aside.
6. atomic_swap() — replace live DB with the temp DB, and write a build report
   naming the input manifest hash.

Rollback
--------
A failed candidate never touches the live DB: every abort before step 6 removes
the temp DB and returns. After a swap, `restore_backup()` re-activates the
previous bundle from the copy step 5 wrote — the rehearsal behind criterion A7.
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
from ingest.validate import validate_bundle, validate_corpus  # noqa: E402


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


def restore_backup(backup_path: str, db_path: str) -> bool:
    """Re-activate a previously published DB from its backup copy.

    The other half of `do_backup`: a publication that shipped a bad bundle is
    reversed by putting the prior file back, with the same atomic replace the
    forward path uses. Returns False if the backup is missing or fails its
    integrity check, so a rollback cannot itself install a corrupt DB.
    """
    if not os.path.exists(backup_path):
        print(f"Rollback aborted: backup not found: {backup_path}", file=sys.stderr)
        return False
    if not integrity_check(backup_path):
        print(f"Rollback aborted: backup failed integrity check: {backup_path}", file=sys.stderr)
        return False
    staging = str(db_path) + ".rollback.tmp"
    shutil.copy2(backup_path, staging)
    Path(staging).replace(db_path)
    print(f"Rolled back {db_path} ← {backup_path}")
    return True


def corpus_identity(db_path: str) -> dict:
    """Read the bundle identity a published DB carries, if any."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT key, value FROM corpus_meta WHERE key IN "
            "('corpus_version', 'bundle_version', 'input_manifest_hash', 'source_count')"
        ).fetchall()
    except sqlite3.Error:
        return {}
    finally:
        con.close()
    return dict(rows)


# ── Orchestrator ──────────────────────────────────────────────────────────────

def publish(
    corpus_path: str,
    db_path: str,
    next_db_path: str,
    backup_dir: str = "backups",
    force: bool = False,
    min_sources: int = 1,
    manifest_path: str | None = None,
    repo_root: str | None = None,
    report_path: str | None = None,
) -> bool:
    """Run the full publish pipeline. Returns True on success."""

    if manifest_path:
        print("Step 1/6  Validating bundle against manifest…")
        report = validate_bundle(manifest_path, repo_root=repo_root)
    else:
        # Legacy path: this validates the desktop HTML tree, which is NOT what
        # gets published. Say so rather than letting a green report imply the
        # published bytes were checked.
        print("Step 1/6  Validating legacy corpus tree (no manifest given)…")
        print("  NOTE: without --manifest the canonical JSONL that will be "
              "published is not hashed. Prefer --manifest.")
        report = validate_corpus(corpus_path)
    report.print_summary()
    if not report.ok:
        print("Publish aborted: validation errors must be resolved first.")
        return False

    print("Step 2/6  Ingesting corpus into temp DB…")
    if os.path.exists(next_db_path):
        os.remove(next_db_path)
    try:
        asyncio.run(_run_ingest(
            corpus_path,
            next_db_path,
            manifest_path=manifest_path,
            repo_root=repo_root,
        ))
    except (ValueError, OSError) as exc:
        # A bad candidate is an abort, not a crash: the live DB has not been
        # touched at this point, so the previous bundle stays active and the
        # caller gets a clean False to act on.
        print(f"Publish aborted during ingest: {exc}", file=sys.stderr)
        if os.path.exists(next_db_path):
            os.remove(next_db_path)
        return False

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

    if manifest_path:
        written = write_publish_report(
            db_path=db_path,
            manifest_path=manifest_path,
            src_count=src_count,
            line_count=line_count,
            report_path=report_path,
        )
        print(f"  Build report: {written}")

    print("Publish complete.")
    return True


def write_publish_report(
    *,
    db_path: str,
    manifest_path: str,
    src_count: int,
    line_count: int,
    report_path: str | None = None,
) -> str:
    """Register the published web DB against its input manifest (criterion A6)."""
    from corpus_builder.build_report import build_report, output_entry, write_report
    from corpus_builder.corpus_manifest import load_manifest

    manifest = load_manifest(manifest_path)
    report = build_report(
        artifact_name=Path(db_path).name,
        artifact_kind="web-db",
        manifest=manifest,
        outputs=[output_entry(db_path, record_count=line_count)],
        counts={"sources": src_count, "rows": line_count},
        generator="ingest.publish/1",
    )
    target = report_path or (str(Path(db_path).with_suffix("")) + ".build-report.json")
    return str(write_report(report, target))


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate, ingest, and atomically publish the corpus DB."
    )
    parser.add_argument("--corpus-path", default="",
                        help="Directory containing Data/ and Programdata/ (legacy path; not needed with --manifest)")
    parser.add_argument("--manifest", default=None,
                        help="Corpus manifest to validate, ingest, and register against")
    parser.add_argument("--repo-root", default=str(Path(_web_dir).parent),
                        help="Root that the manifest's corpus_root is relative to")
    parser.add_argument("--report-path", default=None,
                        help="Where to write the build report (default: alongside the DB)")
    parser.add_argument("--rollback-from", default=None,
                        help="Restore the live DB from this backup and exit")
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

    if args.rollback_from:
        sys.exit(0 if restore_backup(args.rollback_from, args.db_path) else 1)

    if not args.manifest and not args.corpus_path:
        parser.error("one of --manifest or --corpus-path is required")

    success = publish(
        corpus_path=args.corpus_path,
        db_path=args.db_path,
        next_db_path=args.next_db_path,
        backup_dir=args.backup_dir,
        force=args.force,
        min_sources=args.min_sources,
        manifest_path=args.manifest,
        repo_root=args.repo_root,
        report_path=args.report_path,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
