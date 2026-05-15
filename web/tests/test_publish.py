"""Hermetic tests for the Track A publish pipeline."""
import json
import os
import shutil
import sqlite3
import sys
import pytest

# Ensure web/ is importable so that `ingest` resolves as the package web/ingest/
_web_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _web_dir not in sys.path:
    sys.path.insert(0, _web_dir)

from ingest.validate import validate_corpus
from ingest.publish import atomic_swap, do_backup, integrity_check, smoke_check


# ── Corpus tree fixtures ──────────────────────────────────────────────────────

def _make_corpus(tmp_path, filenames: list[str], *, manifest: list[str] | None = None) -> str:
    """Build a minimal corpus directory under tmp_path."""
    corpus = tmp_path / "corpus"
    (corpus / "Programdata").mkdir(parents=True)
    (corpus / "Data").mkdir(parents=True)

    if manifest is None:
        manifest = filenames

    manifest_path = corpus / "Programdata" / "data.txt"
    manifest_path.write_text("\n".join(manifest) + "\n", encoding="utf-8")

    for fname in filenames:
        (corpus / "Data" / fname).write_text(
            f"<!-- Title of {fname} -->\n<p>some content</p>\n",
            encoding="utf-8",
        )
    return str(corpus)


# ── validate_corpus ───────────────────────────────────────────────────────────

def test_validate_ok(tmp_path):
    corpus = _make_corpus(tmp_path, ["a.html", "b.html"])
    report = validate_corpus(corpus)
    assert report.ok
    assert report.stats["manifest_entries"] == 2
    assert report.stats["missing_files"] == 0


def test_validate_no_manifest(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    report = validate_corpus(str(corpus))
    assert not report.ok
    assert any("Manifest not found" in e for e in report.errors)


def test_validate_missing_file(tmp_path):
    corpus = _make_corpus(tmp_path, ["present.html"], manifest=["present.html", "absent.html"])
    report = validate_corpus(corpus)
    assert not report.ok
    assert any("absent.html" in e for e in report.errors)


def test_validate_duplicate(tmp_path):
    corpus = _make_corpus(tmp_path, ["dup.html"], manifest=["dup.html", "dup.html"])
    report = validate_corpus(corpus)
    assert not report.ok
    assert any("Duplicate" in e for e in report.errors)


def test_validate_no_title_comment(tmp_path):
    corpus = tmp_path / "corpus"
    (corpus / "Programdata").mkdir(parents=True)
    (corpus / "Data").mkdir()
    (corpus / "Programdata" / "data.txt").write_text("notitle.html\n", encoding="utf-8")
    (corpus / "Data" / "notitle.html").write_text("<p>no comment here</p>\n", encoding="utf-8")
    report = validate_corpus(str(corpus))
    # Missing title is a warning, not an error
    assert report.ok
    assert report.stats["no_title_comment"] == 1


# ── integrity_check ───────────────────────────────────────────────────────────

def test_integrity_check_ok(tmp_path):
    db_path = str(tmp_path / "good.db")
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE t (x INTEGER)")
    con.close()
    assert integrity_check(db_path) is True


def test_integrity_check_nonexistent(tmp_path):
    # sqlite3 will create an empty DB for a missing path — that still passes
    db_path = str(tmp_path / "empty.db")
    # An empty file (not a valid SQLite DB) should fail
    (tmp_path / "empty.db").write_bytes(b"not a db")
    assert integrity_check(db_path) is False


# ── smoke_check ───────────────────────────────────────────────────────────────

def _build_minimal_db(db_path: str, src_count: int = 3, line_count: int = 30) -> None:
    con = sqlite3.connect(db_path)
    con.execute(
        "CREATE TABLE sources (id INTEGER PRIMARY KEY, filename TEXT, title TEXT, sort_order INTEGER, sha256 TEXT, size INTEGER)"
    )
    con.execute(
        "CREATE TABLE corpus_lines (id INTEGER PRIMARY KEY, source_id INTEGER, line_num INTEGER, line_text TEXT, line_html TEXT, link_id TEXT, chapter TEXT)"
    )
    for i in range(src_count):
        con.execute(
            "INSERT INTO sources (filename, title, sort_order, sha256, size) VALUES (?,?,?,?,?)",
            (f"src{i}.html", f"Source {i}", i, "abc", 100),
        )
    for j in range(line_count):
        con.execute(
            "INSERT INTO corpus_lines (source_id, line_num, line_text, line_html) VALUES (?,?,?,?)",
            (1, j, f"line {j}", f"<p>line {j}</p>"),
        )
    con.commit()
    con.close()


def test_smoke_check_counts(tmp_path):
    db_path = str(tmp_path / "corpus.db")
    _build_minimal_db(db_path, src_count=5, line_count=50)
    src, lines = smoke_check(db_path)
    assert src == 5
    assert lines == 50


# ── do_backup ─────────────────────────────────────────────────────────────────

def test_do_backup_creates_file(tmp_path):
    db_path = str(tmp_path / "corpus.db")
    _build_minimal_db(db_path)
    backup_dir = str(tmp_path / "backups")
    result = do_backup(db_path, backup_dir)
    assert result is not None
    assert os.path.exists(result)
    assert result.startswith(backup_dir)


def test_do_backup_no_existing_db(tmp_path):
    result = do_backup(str(tmp_path / "missing.db"), str(tmp_path / "backups"))
    assert result is None


# ── atomic_swap ───────────────────────────────────────────────────────────────

def test_atomic_swap_replaces_target(tmp_path):
    next_db = str(tmp_path / "corpus.next.db")
    live_db = str(tmp_path / "corpus.db")
    _build_minimal_db(next_db, src_count=7)
    _build_minimal_db(live_db, src_count=3)

    atomic_swap(next_db, live_db)

    assert not os.path.exists(next_db)
    assert os.path.exists(live_db)
    src, _ = smoke_check(live_db)
    assert src == 7


def test_atomic_swap_fresh_install(tmp_path):
    next_db = str(tmp_path / "corpus.next.db")
    live_db = str(tmp_path / "corpus.db")
    _build_minimal_db(next_db, src_count=2)

    atomic_swap(next_db, live_db)

    assert os.path.exists(live_db)
    src, _ = smoke_check(live_db)
    assert src == 2
