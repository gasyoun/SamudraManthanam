import asyncio
import os
import argparse
import hashlib
import sys

# Add necessary directories to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
web_dir = os.path.dirname(script_dir)
sys.path.append(web_dir)
sys.path.append(script_dir)

from app.db import get_db, create_schema
from app.services.slug import make_unique_slug
from parse_html import parse_corpus_file, get_source_title

def get_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

async def ingest(corpus_path: str, db_path: str):
    db = await get_db(db_path)
    await create_schema(db)
    
    data_txt_path = os.path.join(corpus_path, "Programdata", "data.txt")
    if not os.path.exists(data_txt_path):
        print(f"Error: {data_txt_path} not found.")
        return

    with open(data_txt_path, "r", encoding="utf-8") as f:
        filenames = [line.strip() for line in f if line.strip()]

    print(f"Found {len(filenames)} sources in data.txt")

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

    # Slug uniqueness tracking — built once before the per-source loop, then
    # extended as each new slug is minted. This lets `make_unique_slug`
    # disambiguate across the entire ingest batch in one pass.
    seen_slugs: set[str] = set()

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

        # Bulk insert lines
        lines_data = []
        for line_info in parse_corpus_file(file_path):
            lines_data.append((
                line_info["line_text"],
                line_info["line_html"],
                source_id,
                line_info["line_num"],
                line_info["link_id"],
                line_info["chapter"]
            ))
            
            if len(lines_data) >= 1000:
                await db.executemany(
                    "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) VALUES (?, ?, ?, ?, ?, ?)",
                    lines_data
                )
                lines_data = []
        
        if lines_data:
            await db.executemany(
                "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) VALUES (?, ?, ?, ?, ?, ?)",
                lines_data
            )

        await db.commit()
    
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
    
    args = parser.parse_args()
    
    asyncio.run(ingest(args.corpus_path, args.db_path))
