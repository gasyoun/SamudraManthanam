"""Build the tiny fixture corpus.db + state.db a boot test needs (H1927 D3/D4).

The deployment contract smoke suite has to run against something. Pointing it
at the real 500 MB corpus would make the container boot check a data-availability
test, which is not what it is for — D3 asks for the image to be booted "against
fixture databases". This builds those: a handful of Sanskrit and Russian lines,
the corpus_meta rows the version-exposure check reads, and a state.db migrated
through the real runner so the migration path is exercised at boot too.

Usage
-----
    python web/scripts/build_fixture_db.py --corpus-db /tmp/corpus.db --state-db /tmp/state.db
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Make `app` importable when this is run as a plain script from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import aiosqlite  # noqa: E402

from app.db import create_schema  # noqa: E402
from app.migrations.corpus_policy import (  # noqa: E402
    CORPUS_SCHEMA_VERSION,
    CORPUS_SCHEMA_VERSION_KEY,
)
from app.migrations.runner import apply_migrations  # noqa: E402

FIXTURE_SOURCES = [
    (1, "bhagavadgita-fixture.html", "Бхагавад-гита (fixture)", 1, "bhagavadgita-fixture"),
    (2, "mahabharata-fixture.html", "Махабхарата (fixture)", 2, "mahabharata-fixture"),
]

FIXTURE_LINES = [
    # (line_text, line_html, source_id, line_num, link_id, chapter)
    (
        "dharmakṣetre kurukṣetre samavetā yuyutsavaḥ",
        '<p class="chapter_block iast">dharmakṣetre kurukṣetre samavetā yuyutsavaḥ</p>',
        1, 1, "1.1", "Глава 1",
    ),
    (
        "На поле дхармы, на поле Куру сошлись жаждущие битвы",
        "<p>На поле дхармы, на поле Куру сошлись жаждущие битвы</p>",
        1, 2, "1.1r", "Глава 1",
    ),
    (
        "yadā yadā hi dharmasya glānir bhavati bhārata",
        '<p class="chapter_block iast">yadā yadā hi dharmasya glānir bhavati bhārata</p>',
        1, 3, "4.7", "Глава 4",
    ),
    (
        "Всякий раз, когда дхарма приходит в упадок, о Бхарата",
        "<p>Всякий раз, когда дхарма приходит в упадок, о Бхарата</p>",
        1, 4, "4.7r", "Глава 4",
    ),
    (
        "nārāyaṇaṃ namaskṛtya naraṃ caiva narottamam",
        "<p>nārāyaṇaṃ namaskṛtya naraṃ caiva narottamam</p>",
        2, 1, "1.1", "Адипарва",
    ),
    (
        "Поклонившись Нараяне и Наре, лучшему из людей",
        "<p>Поклонившись Нараяне и Наре, лучшему из людей</p>",
        2, 2, "1.1r", "Адипарва",
    ),
]


async def build_corpus_db(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)
    db = await aiosqlite.connect(path)
    try:
        await create_schema(db)
        for row in FIXTURE_SOURCES:
            await db.execute(
                "INSERT INTO sources (id, filename, title, sort_order, slug) "
                "VALUES (?, ?, ?, ?, ?)",
                row,
            )
        for line in FIXTURE_LINES:
            await db.execute(
                "INSERT INTO corpus_lines "
                "(line_text, line_html, source_id, line_num, link_id, chapter) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                line,
            )
        now = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        for key, value in (
            ("corpus_version", "fixture-0"),
            ("generated_at", now),
            (CORPUS_SCHEMA_VERSION_KEY, str(CORPUS_SCHEMA_VERSION)),
        ):
            await db.execute(
                "INSERT OR REPLACE INTO corpus_meta (key, value) VALUES (?, ?)",
                (key, value),
            )
        await db.commit()
    finally:
        await db.close()
    print(
        f"OK    corpus fixture: {path} "
        f"({len(FIXTURE_SOURCES)} sources, {len(FIXTURE_LINES)} lines, "
        f"schema v{CORPUS_SCHEMA_VERSION})"
    )


async def build_state_db(path: str) -> None:
    """Build state.db through the real migration runner.

    Deliberately not a hand-written CREATE TABLE dump: booting against a
    fixture built by a different code path than production would hide exactly
    the migration failures this check exists to catch.
    """
    if os.path.exists(path):
        os.remove(path)
    db = await aiosqlite.connect(path)
    try:
        applied = await apply_migrations(db)
        await db.execute("PRAGMA journal_mode=WAL")
        await db.commit()
    finally:
        await db.close()
    print(f"OK    state fixture:  {path} (migrations applied: {', '.join(applied) or 'none'})")


async def main_async(args) -> int:
    await build_corpus_db(args.corpus_db)
    await build_state_db(args.state_db)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpus-db", default="fixture-corpus.db")
    parser.add_argument("--state-db", default="fixture-state.db")
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
