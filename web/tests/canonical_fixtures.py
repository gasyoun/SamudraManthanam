"""Shared fixture builders for the Lane B canonical-reference tests (H1925).

Builds throwaway corpus and state SQLite files with the same schema shape the
app uses, so the identity tests exercise real SQL rather than a mock that can
agree with a broken implementation.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

CORPUS_SCHEMA = """
CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    slug TEXT
);
CREATE VIRTUAL TABLE corpus_lines USING fts5(
    line_text, line_html UNINDEXED, source_id UNINDEXED, line_num UNINDEXED,
    link_id UNINDEXED, chapter UNINDEXED, canonical_id UNINDEXED,
    tokenize="unicode61"
);
CREATE TABLE corpus_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

STATE_SCHEMA = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE corrections (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL,
    line_num INTEGER NOT NULL,
    old_text TEXT NOT NULL,
    new_text TEXT NOT NULL,
    user_id INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);
"""


def make_corpus(
    path: str | Path,
    *,
    corpus_version: str,
    sources: list[tuple[int, str, str]],
    lines: list[tuple[int, int, str | None, str]],
) -> str:
    """Create a corpus DB.

    ``sources``: ``(source_id, slug, title)``
    ``lines``:   ``(source_id, line_num, canonical_id, line_text)``
    """
    path = str(path)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(CORPUS_SCHEMA)
        for sid, slug, title in sources:
            conn.execute(
                "INSERT INTO sources (id, filename, title, sort_order, slug) "
                "VALUES (?, ?, ?, ?, ?)",
                (sid, f"{slug}.html", title, sid, slug),
            )
        for sid, line_num, canonical_id, text in lines:
            conn.execute(
                "INSERT INTO corpus_lines "
                "(line_text, line_html, source_id, line_num, link_id, chapter, canonical_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (text, f"<p>{text}</p>", sid, line_num, canonical_id or "", "", canonical_id),
            )
        conn.execute(
            "INSERT INTO corpus_meta (key, value) VALUES ('corpus_version', ?)",
            (corpus_version,),
        )
        conn.commit()
    finally:
        conn.close()
    return path


def make_state(path: str | Path, corrections: list[dict] | None = None) -> str:
    """Create a pre-migration state DB, optionally seeded with corrections."""
    path = str(path)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(STATE_SCHEMA)
        for c in corrections or []:
            conn.execute(
                "INSERT INTO corrections (id, source_id, line_num, old_text, new_text, "
                "created_at) VALUES (?, ?, ?, ?, ?, '2026-08-05T00:00:00')",
                (c["id"], c["source_id"], c["line_num"], c.get("old", "old"), c.get("new", "new")),
            )
        conn.commit()
    finally:
        conn.close()
    return path
