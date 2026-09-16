"""Nightly word-of-the-day picker (H4955).

Reads the committed Kochergina pool (`web/app/data/word_of_day_pool.jsonl`,
built by `word_of_day_export_pool.py`), picks one not-yet-shown entry at
random, looks up one corpus example sentence for it, and writes the day's
static record to `web/app/data/word_of_day_current.json`. The FastAPI widget
route only ever reads that static file — no per-request DB query.

No-repeat tracking lives in the app's state DB (`word_of_day_shown`, added by
migration `0006_word_of_day.sql`); once every pool entry has been shown the
table is truncated and a fresh cycle starts.

Intended to run once nightly via a systemd timer
(`deploy/samudra-word-of-day.timer`), mirroring the existing
`samudra-health-monitor` timer/service pair.

Usage:
    python scripts/word_of_day_generate.py [--date YYYY-MM-DD]
        [--pool PATH] [--state-db PATH] [--corpus-db PATH] [--out PATH]
"""
import argparse
import datetime
import json
import random
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "web"))

from app.migrations.runner import apply_migrations_at_path  # noqa: E402
from app.services.search_service import escape_fts  # noqa: E402
from app.settings import settings  # noqa: E402

DEFAULT_POOL = REPO_ROOT / "web" / "app" / "data" / "word_of_day_pool.jsonl"
DEFAULT_OUT = REPO_ROOT / "web" / "app" / "data" / "word_of_day_current.json"


def load_pool(pool_path: Path) -> list[dict]:
    entries = []
    with pool_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def read_shown(state_db_path: str) -> set[str]:
    conn = sqlite3.connect(state_db_path)
    try:
        rows = conn.execute("SELECT entry_id FROM word_of_day_shown").fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


def pick_entry(pool: list[dict], shown_ids: set[str], rng: random.Random) -> tuple[dict, bool]:
    """Return (picked_entry, cycle_reset). Pure — no I/O, easy to unit test."""
    eligible = [e for e in pool if e["entry_id"] not in shown_ids]
    cycle_reset = False
    if not eligible:
        eligible = pool
        cycle_reset = True
    return rng.choice(eligible), cycle_reset


def mark_shown(state_db_path: str, entry: dict, date_str: str, cycle_reset: bool) -> None:
    conn = sqlite3.connect(state_db_path)
    try:
        if cycle_reset:
            conn.execute("DELETE FROM word_of_day_shown")
        conn.execute(
            "INSERT OR REPLACE INTO word_of_day_shown (entry_id, headword, shown_date) "
            "VALUES (?, ?, ?)",
            (entry["entry_id"], entry["iast"], date_str),
        )
        conn.commit()
    finally:
        conn.close()


def find_example(corpus_db_path: str, entry: dict) -> dict | None:
    """Best-effort one-sentence corpus attestation for `entry`.

    Tries IAST first (the corpus's own text encoding, per
    web/tests/conftest.py's seed data), falls back to Devanagari. Returns
    None (never raises) when the corpus DB is unreachable, has no FTS table
    yet, or has no hit — the spec's documented graceful-fallback path.
    """
    try:
        conn = sqlite3.connect(corpus_db_path)
        conn.row_factory = sqlite3.Row
        try:
            for query in (entry["iast"], entry["devanagari"]):
                if not query:
                    continue
                fts_query = escape_fts(query, whole_word=False)
                row = conn.execute(
                    """
                    SELECT s.title as source_title, cl.line_text
                    FROM corpus_lines cl
                    JOIN sources s ON cl.source_id = s.id
                    WHERE corpus_lines MATCH ?
                    LIMIT 1
                    """,
                    (fts_query,),
                ).fetchone()
                if row:
                    return {"text": row["line_text"], "source": row["source_title"]}
        finally:
            conn.close()
    except sqlite3.Error as exc:
        print(f"word_of_day: corpus example lookup skipped ({exc})", file=sys.stderr)
    return None


def generate(
    date_str: str,
    pool_path: Path,
    state_db_path: str,
    corpus_db_path: str,
    out_path: Path,
    rng: random.Random | None = None,
) -> dict:
    rng = rng or random.Random()
    apply_migrations_at_path(state_db_path)

    pool = load_pool(pool_path)
    shown_ids = read_shown(state_db_path)
    entry, cycle_reset = pick_entry(pool, shown_ids, rng)

    example = find_example(corpus_db_path, entry)

    record = {
        "date": date_str,
        "entry_id": entry["entry_id"],
        "slp1": entry["slp1"],
        "iast": entry["iast"],
        "devanagari": entry["devanagari"],
        "gloss": entry["gloss"],
        "pos": entry["pos"],
        "source": entry["source"],
        "example": example,
        "cycle_reset": cycle_reset,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    mark_shown(state_db_path, entry, date_str, cycle_reset)
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    ap.add_argument("--state-db", default=settings.STATE_DB_PATH or str(REPO_ROOT / "state.db"))
    ap.add_argument("--corpus-db", default=settings.DB_PATH)
    ap.add_argument(
        "--out", type=Path,
        default=Path(settings.WORD_OF_DAY_RECORD_PATH) if settings.WORD_OF_DAY_RECORD_PATH else DEFAULT_OUT,
    )
    args = ap.parse_args()

    record = generate(args.date, args.pool, args.state_db, args.corpus_db, args.out)
    tag = " (cycle reset)" if record["cycle_reset"] else ""
    print(f"word_of_day {record['date']}: {record['iast']} ({record['entry_id']}){tag}")


if __name__ == "__main__":
    main()
