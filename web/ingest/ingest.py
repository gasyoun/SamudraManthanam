import asyncio
import json
import os
import argparse
import hashlib
import sys
from pathlib import Path

# Add necessary directories to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
web_dir = os.path.dirname(script_dir)
sys.path.append(web_dir)
sys.path.append(script_dir)

from app.db import get_db, create_schema
from app.services.slug import make_unique_slug
from parse_html import get_source_title

_JSONL_DIR = Path(web_dir) / "corpus_builder" / "jsonl"

def get_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def _load_jsonl_rows(jsonl_path: Path, source_id: int):
    with open(jsonl_path, encoding="utf-8") as jf:
        for raw in jf:
            raw = raw.strip()
            if not raw:
                continue
            rec = json.loads(raw)
            if rec.get("deleted"):
                continue
            canonical_id = rec.get("id")
            if not canonical_id:
                raise ValueError(f"{jsonl_path}: record missing id/canonical_id")
            yield (
                rec.get("text", ""),
                rec.get("html", ""),
                source_id,
                rec.get("seq", 0),
                rec.get("passage", ""),
                rec.get("chapter"),
                canonical_id,
            )


async def _validate_jsonl_ingest(db):
    async with db.execute(
        "SELECT COUNT(*) FROM corpus_lines "
        "WHERE canonical_id IS NULL OR canonical_id = ''"
    ) as cursor:
        missing = (await cursor.fetchone())[0]
    if missing:
        raise ValueError(f"JSONL ingest validation failed: {missing} rows lack canonical_id")

    async with db.execute(
        "SELECT source_id, canonical_id, COUNT(*) AS n "
        "FROM corpus_lines "
        "GROUP BY source_id, canonical_id "
        "HAVING canonical_id IS NOT NULL AND canonical_id != '' AND n > 1 "
        "LIMIT 10"
    ) as cursor:
        dupes = await cursor.fetchall()
    if dupes:
        sample = ", ".join(
            f"source_id={row[0]} canonical_id={row[1]!r} count={row[2]}"
            for row in dupes
        )
        raise ValueError(f"JSONL ingest validation failed: duplicate canonical_id rows: {sample}")

    async with db.execute(
        "SELECT s.filename "
        "FROM sources s "
        "LEFT JOIN corpus_lines cl ON cl.source_id = s.id "
        "GROUP BY s.id "
        "HAVING COUNT(cl.rowid) = 0 "
        "LIMIT 10"
    ) as cursor:
        empty_sources = await cursor.fetchall()
    if empty_sources:
        sample = ", ".join(row[0] for row in empty_sources)
        raise ValueError(f"JSONL ingest validation failed: sources inserted zero rows: {sample}")


async def ingest(corpus_path: str, db_path: str, jsonl_dir: str | None = None):
    jsonl_root = Path(jsonl_dir) if jsonl_dir else _JSONL_DIR
    
    data_txt_path = os.path.join(corpus_path, "Programdata", "data.txt")
    if not os.path.exists(data_txt_path):
        print(f"Error: {data_txt_path} not found.")
        return

    with open(data_txt_path, "r", encoding="utf-8") as f:
        filenames = [line.strip() for line in f if line.strip()]

    print(f"Found {len(filenames)} sources in data.txt")

    # Slug uniqueness tracking — built once before the per-source loop, then
    # extended as each new slug is minted. This lets `make_unique_slug`
    # disambiguate across the entire ingest batch in one pass.
    seen_slugs: set[str] = set()
    sources_to_ingest = []
    missing_jsonl = []

    for idx, filename in enumerate(filenames):
        file_path = os.path.join(corpus_path, "Data", filename)
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} not found. Skipping.")
            continue

        title = get_source_title(file_path)
        sha256 = get_sha256(file_path)
        size = os.path.getsize(file_path)
        slug = make_unique_slug(filename, seen_slugs)
        seen_slugs.add(slug)
        jsonl_path = jsonl_root / f"{slug}.jsonl"
        if not jsonl_path.exists():
            missing_jsonl.append(f"{filename} (slug {slug!r}): {jsonl_path}")
        sources_to_ingest.append({
            "idx": idx,
            "filename": filename,
            "file_path": file_path,
            "title": title,
            "sha256": sha256,
            "size": size,
            "slug": slug,
            "jsonl_path": jsonl_path,
        })

    if missing_jsonl:
        sample = "\n  ".join(missing_jsonl)
        raise FileNotFoundError(
            "Missing canonical JSONL for active sources:\n  " + sample
        )

    db = await get_db(db_path)
    await create_schema(db)

    # Reconciliation: Remove sources that are no longer in data.txt
    async with db.execute("SELECT filename FROM sources") as cursor:
        db_filenames = [row[0] for row in await cursor.fetchall()]

    to_remove = set(db_filenames) - set(filenames)
    if to_remove:
        print(f"Removing {len(to_remove)} sources no longer in manifest...")
        for fname in to_remove:
            async with db.execute("SELECT id FROM sources WHERE filename = ?", (fname,)) as c:
                row = await c.fetchone()
                if row:
                    sid = row[0]
                    await db.execute("DELETE FROM corpus_lines WHERE source_id = ?", (sid,))
                    await db.execute("DELETE FROM sources WHERE id = ?", (sid,))
        await db.commit()

    for entry in sources_to_ingest:
        idx = entry["idx"]
        filename = entry["filename"]
        file_path = entry["file_path"]
        title = entry["title"]
        sha256 = entry["sha256"]
        size = entry["size"]
        slug = entry["slug"]
        jsonl_path = entry["jsonl_path"]

        # Clean up existing data for this filename to ensure idempotency
        async with db.execute("SELECT id FROM sources WHERE filename = ?", (filename,)) as c:
            row = await c.fetchone()
            if row:
                old_source_id = row[0]
                await db.execute("DELETE FROM corpus_lines WHERE source_id = ?", (old_source_id,))
                await db.execute("DELETE FROM sources WHERE id = ?", (old_source_id,))

        # Insert fresh source record
        cursor = await db.execute(
            "INSERT INTO sources (filename, title, sort_order, sha256, size, slug) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (filename, title, idx, sha256, size, slug)
        )
        source_id = cursor.lastrowid
        
        print(f"[{idx+1}/{len(filenames)}] Ingesting {filename}: {title}")

        # Load bibliographic metadata from sibling .meta.json if present.
        meta_json_path = file_path + ".meta.json"
        if os.path.exists(meta_json_path):
            with open(meta_json_path, "r", encoding="utf-8") as fh:
                meta = json.load(fh)
            await db.execute(
                "UPDATE sources SET title_en=?, subtitle=?, credit=?, credit_role=?, "
                "imprint=?, publisher=?, year=? WHERE id=?",
                (
                    meta.get("title_en") or None,
                    meta.get("subtitle") or None,
                    meta.get("credit") or None,
                    meta.get("credit_role") or None,
                    meta.get("imprint") or None,
                    meta.get("publisher") or None,
                    meta.get("year"),
                    source_id,
                ),
            )

        # Bulk insert lines from canonical JSONL. HTML parsing remains available
        # for the converter, but normal ingest is strict JSONL-only.
        _INSERT = (
            "INSERT INTO corpus_lines "
            "(line_text, line_html, source_id, line_num, link_id, chapter, canonical_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)"
        )
        lines_data = []

        inserted_for_source = 0
        for row in _load_jsonl_rows(jsonl_path, source_id):
            lines_data.append(row)
            inserted_for_source += 1
            if len(lines_data) >= 1000:
                await db.executemany(_INSERT, lines_data)
                lines_data = []

        if lines_data:
            await db.executemany(_INSERT, lines_data)
        if inserted_for_source == 0:
            raise ValueError(
                f"JSONL ingest validation failed: {filename} ({slug}) inserted zero rows"
            )

        await db.commit()

    await _validate_jsonl_ingest(db)
    
    # Insert metadata. source_count comes from the actual rows in `sources`,
    # not len(filenames) — they diverge if any files were skipped due to a
    # missing file warning above.
    import datetime
    async with db.execute("SELECT COUNT(*) FROM sources") as cursor:
        row = await cursor.fetchone()
        actual_source_count = row[0]

    version = f"v{datetime.datetime.now().strftime('%Y.%m.%d')}"
    meta = [
        ("corpus_version", version),
        ("generated_at", datetime.datetime.now().isoformat()),
        ("source_count", str(actual_source_count)),
    ]
    await db.execute("DELETE FROM corpus_meta")
    await db.executemany("INSERT INTO corpus_meta (key, value) VALUES (?, ?)", meta)
    await db.commit()

    print(f"Ingestion complete. Corpus Version: {version}")
    await db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest corpus HTML files into SQLite")
    parser.add_argument("--corpus-path", required=True, help="Path to the corpus directory (containing Data/ and Programdata/)")
    parser.add_argument("--db-path", default="corpus.db", help="Path to the output SQLite database")
    parser.add_argument("--jsonl-dir", default=str(_JSONL_DIR), help="Path to canonical JSONL directory")
    
    args = parser.parse_args()
    
    asyncio.run(ingest(args.corpus_path, args.db_path, args.jsonl_dir))
