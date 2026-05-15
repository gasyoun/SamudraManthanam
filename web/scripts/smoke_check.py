"""Standalone post-publish smoke-test.

Verifies that the live corpus DB exists, is readable, and contains at least
--min-sources sources. Exits 0 on success, 1 on any failure.

Usage
-----
  python web/scripts/smoke_check.py --db-path /app/corpus.db --min-sources 5
"""
import argparse
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def smoke_check(db_path: str, min_sources: int = 1) -> bool:
    if not os.path.exists(db_path):
        print(f"FAIL  DB not found: {db_path}", file=sys.stderr)
        return False

    try:
        con = sqlite3.connect(db_path)
        src_count = con.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        line_count = con.execute("SELECT COUNT(*) FROM corpus_lines").fetchone()[0]
        version_row = con.execute(
            "SELECT value FROM corpus_meta WHERE key = 'corpus_version'"
        ).fetchone()
        con.close()
    except Exception as exc:
        print(f"FAIL  Could not query DB: {exc}", file=sys.stderr)
        return False

    version_str = version_row[0] if version_row else "unknown"
    print(f"OK    sources={src_count}  lines={line_count}  version={version_str}")

    if src_count < min_sources:
        print(
            f"FAIL  Expected >= {min_sources} sources, got {src_count}",
            file=sys.stderr,
        )
        return False

    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify corpus DB health after publish."
    )
    parser.add_argument(
        "--db-path", default="corpus.db", help="Path to corpus.db (default: corpus.db)"
    )
    parser.add_argument(
        "--min-sources",
        type=int,
        default=1,
        help="Minimum accepted source count (default: 1)",
    )
    args = parser.parse_args()
    ok = smoke_check(args.db_path, min_sources=args.min_sources)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
