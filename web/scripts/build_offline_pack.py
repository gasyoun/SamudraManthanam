#!/usr/bin/env python3
"""Build offline search packs from corpus.db.

Two packs:
  base.db  -- all corpus sources except MW and Apte dictionaries (target ≤120 MB)
  dict.db  -- MW + Apte dictionaries only (target ≤75 MB)

Usage (run from web/):
  python scripts/build_offline_pack.py              # build both packs
  python scripts/build_offline_pack.py --pack base
  python scripts/build_offline_pack.py --pack dict
  python scripts/build_offline_pack.py --validate-only   # CI gate, no output
  python scripts/build_offline_pack.py --db /path/corpus.db --out /path/out/
"""
import sys
import os
import gzip
import shutil
import sqlite3
import hashlib
import argparse
import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

PACK_VERSION = "1"
# Limits are on the WIRE size — the gzipped .db.gz that the client actually
# downloads (served with Content-Encoding: gzip). The raw .db is larger and
# lands in the user's OPFS, but the download is what we gate. See D1 in
# docs/DECISIONS_NEEDED.md.
SIZE_LIMIT_MB = {"base": 130, "dict": 90}
GZIP_LEVEL = 6  # 6 ≈ best ratio/CPU tradeoff; packs compress to ~40% regardless

# Identify MW and Apte by filename substring (case-insensitive).
DICT_FILENAME_MARKERS = ("DIC_MW", "DIC_APTE")

PACK_SCHEMA = """\
CREATE TABLE pack_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE pack_sources (
    source_id   INTEGER PRIMARY KEY,
    source_slug TEXT NOT NULL,
    title       TEXT NOT NULL,
    role        TEXT NOT NULL
);

CREATE TABLE corpus_lines (
    id           INTEGER PRIMARY KEY,
    source_id    INTEGER NOT NULL REFERENCES pack_sources(source_id),
    link_id      TEXT NOT NULL,
    canonical_id TEXT,
    chapter      TEXT,
    line_num     INTEGER,
    line_text    TEXT NOT NULL
);

CREATE INDEX corpus_lines_source ON corpus_lines (source_id);
CREATE INDEX corpus_lines_link   ON corpus_lines (link_id);
"""

FTS_CREATE = """\
CREATE VIRTUAL TABLE corpus_fts USING fts5(
    line_text,
    content='corpus_lines',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 0'
);
"""


def _is_dict_source(filename: str) -> bool:
    upper = filename.upper()
    return any(m in upper for m in DICT_FILENAME_MARKERS)


def _infer_role(filename: str, slug: str, sample_cids: list[str]) -> str:
    if _is_dict_source(filename):
        return "dictionary"
    has_comm = any("#comm" in c for c in sample_cids)
    has_sa = any(c.endswith("#sa") for c in sample_cids)
    if has_comm:
        return "commentary"
    if has_sa:
        return "translation"
    return "anthology"


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _gzip_file(src: str, dst: str) -> None:
    """Stream-compress src → dst (gzip). Used to produce the .db.gz that the
    endpoint serves with Content-Encoding: gzip so the browser decodes it
    transparently and the client-side SHA-256 still matches the raw .db.

    mtime=0 makes the output deterministic (the gzip header otherwise embeds the
    build timestamp, which would change the .gz bytes — and any future .gz hash —
    on every rebuild of identical content)."""
    with open(src, "rb") as f_in, gzip.GzipFile(dst, "wb", compresslevel=GZIP_LEVEL, mtime=0) as f_out:
        shutil.copyfileobj(f_in, f_out, length=1 << 20)


def get_dict_source_ids(src_db: sqlite3.Connection) -> list[int]:
    rows = src_db.execute("SELECT id, filename FROM sources").fetchall()
    return [r[0] for r in rows if _is_dict_source(r[1] or "")]


def validate_corpus_db(db_path: str) -> int:
    """Validate that corpus.db is present and usable. Returns 0 on success, 1 on failure."""
    if not os.path.exists(db_path):
        print(f"ERROR: corpus.db not found at {db_path}", file=sys.stderr)
        return 1
    try:
        src = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        src.row_factory = sqlite3.Row
        row = src.execute("SELECT value FROM corpus_meta WHERE key = 'corpus_version'").fetchone()
        if not row:
            print("ERROR: corpus_meta missing corpus_version key", file=sys.stderr)
            return 1
        version = row[0]

        count = src.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        if count == 0:
            print("ERROR: sources table is empty", file=sys.stderr)
            return 1

        line_count = src.execute("SELECT COUNT(*) FROM corpus_lines").fetchone()[0]
        if line_count == 0:
            print("ERROR: corpus_lines is empty", file=sys.stderr)
            return 1

        dict_ids = get_dict_source_ids(src)
        src.close()

        print(f"OK: corpus_version={version}  sources={count}  lines={line_count}  dict_sources={len(dict_ids)}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def build_pack(
    db_path: str,
    out_path: str,
    pack_type: str,  # 'base' or 'dict'
) -> dict:
    """Build one offline pack. Returns stats dict."""
    src = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

    # Corpus version and, when the DB was built from a manifest, the bundle
    # identity this pack inherits — a pack is a derivative view, so it must name
    # the same input manifest the web DB does (criterion A6).
    row = src.execute("SELECT value FROM corpus_meta WHERE key = 'corpus_version'").fetchone()
    corpus_version = row[0] if row else "unknown"
    corpus_meta = dict(src.execute("SELECT key, value FROM corpus_meta").fetchall())
    input_manifest_hash = corpus_meta.get("input_manifest_hash", "")
    bundle_version = corpus_meta.get("bundle_version", "")

    # Decide which sources go in this pack
    all_rows = src.execute("SELECT id, slug, title, filename FROM sources ORDER BY sort_order").fetchall()
    dict_ids = {r[0] for r in all_rows if _is_dict_source(r[3] or "")}
    if pack_type == "dict":
        target_rows = [r for r in all_rows if r[0] in dict_ids]
    else:
        target_rows = [r for r in all_rows if r[0] not in dict_ids]

    if not target_rows:
        src.close()
        raise ValueError(f"No sources found for pack_type={pack_type!r}")

    # Build into TEMP files and atomically swap into place at the very end (see
    # the commit block below). This keeps the build crash-safe: an interrupted
    # rebuild never destroys the previously-working pack, never leaves a
    # half-written .db, and never produces a .gz whose decoded bytes disagree
    # with the .sha256 sidecar (which would otherwise either fail-closed forever
    # or — worse — silently install stale-corpus content that still passes SHA).
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    tmp_db = out_path + ".tmp"
    tmp_gz = out_path + ".gz.tmp"
    tmp_sha = out_path + ".sha256.tmp"
    for stale in (tmp_db, tmp_gz, tmp_sha):
        if os.path.exists(stale):
            os.remove(stale)

    dst = sqlite3.connect(tmp_db)
    dst.execute("PRAGMA journal_mode=WAL")
    dst.execute("PRAGMA synchronous=NORMAL")
    dst.execute("PRAGMA page_size=4096")
    dst.execute("PRAGMA cache_size=-32768")  # 32 MB cache during build

    for stmt in PACK_SCHEMA.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            dst.execute(stmt)
    dst.commit()

    # Insert sources with inferred roles
    source_count = 0
    for sid, slug, title, filename in target_rows:
        slug = slug or filename or str(sid)
        sample = src.execute(
            "SELECT canonical_id FROM corpus_lines WHERE source_id = ? LIMIT 100",
            (sid,),
        ).fetchall()
        sample_cids = [r[0] or "" for r in sample]
        role = _infer_role(filename or "", slug, sample_cids)
        dst.execute(
            "INSERT INTO pack_sources (source_id, source_slug, title, role) VALUES (?, ?, ?, ?)",
            (sid, slug, title or "", role),
        )
        source_count += 1

    dst.commit()

    # Copy corpus_lines (text only, no HTML) in a single pass. Filter on the
    # small DICTIONARY id set (IN for the dict pack, NOT IN for base) rather than
    # binding every target source id — this keeps the bind-variable count at the
    # number of dictionaries (2 today), well under SQLITE_MAX_VARIABLE_NUMBER, no
    # matter how many sources the corpus grows to. Selecting target_ids (146 for
    # base) directly would trip the ~999-variable limit as the corpus expands.
    dict_id_list = sorted(dict_ids)
    dph = ",".join("?" * len(dict_id_list))
    if pack_type == "dict":
        where = f"source_id IN ({dph})" if dict_id_list else "0"
    else:
        where = f"source_id NOT IN ({dph})" if dict_id_list else "1"
    row_count = 0
    BATCH = 2000

    cur = src.execute(
        f"SELECT source_id, link_id, canonical_id, chapter, line_num, line_text "
        f"FROM corpus_lines WHERE {where} ORDER BY source_id, line_num",
        dict_id_list,
    )

    while True:
        batch = cur.fetchmany(BATCH)
        if not batch:
            break
        dst.executemany(
            "INSERT INTO corpus_lines "
            "(source_id, link_id, canonical_id, chapter, line_num, line_text) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            batch,
        )
        row_count += len(batch)
        dst.commit()
        print(f"  {row_count:,} rows...", end="\r", flush=True)

    print(f"  {row_count:,} rows copied" + " " * 20)

    # Build FTS5 index
    print("  Building FTS5 index...", flush=True)
    dst.execute(FTS_CREATE)
    dst.execute("INSERT INTO corpus_fts(corpus_fts) VALUES('rebuild')")
    dst.commit()

    # Write pack_meta. Note: NO self-referential sha256 key — a file cannot
    # contain its own hash (writing the hash in would change the hash). The
    # SHA-256 lives ONLY in the sidecar, computed below on the final file, and
    # that sidecar is what the client verifies against. (The previous design
    # wrote sha256 into pack_meta via a post-hash reopen, which mutated the file
    # after the sidecar was computed → every client install failed SHA check.)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    dst.executemany(
        "INSERT OR REPLACE INTO pack_meta (key, value) VALUES (?, ?)",
        [
            ("corpus_version", corpus_version),
            ("pack_version", PACK_VERSION),
            ("pack_type", pack_type),
            ("built_at", now),
            ("source_count", str(source_count)),
            ("row_count", str(row_count)),
        ]
        + ([("input_manifest_hash", input_manifest_hash)] if input_manifest_hash else [])
        + ([("bundle_version", bundle_version)] if bundle_version else []),
    )
    dst.commit()
    # Fold the WAL back into the main db file and drop the -wal/-shm sidecars so
    # the on-disk file is a single, stable artifact whose bytes match the hash.
    dst.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    dst.execute("PRAGMA journal_mode=DELETE")
    dst.commit()
    dst.close()
    src.close()

    # Compute SHA-256 on the completed temp .db (over the RAW bytes — what the
    # client reconstructs after the browser decodes Content-Encoding: gzip, so
    # the hash is independent of compression). Then build the gzip wire artifact
    # and the sidecar, also as temp files.
    sha = _sha256_file(tmp_db)
    print("  Compressing (gzip)...", flush=True)
    _gzip_file(tmp_db, tmp_gz)
    with open(tmp_sha, "w", encoding="utf-8") as f:
        f.write(sha)

    # ── Atomic commit ────────────────────────────────────────────────────────
    # Order matters for crash-safety. Remove the real sidecar FIRST: while it is
    # absent /api/corpus-version reports no hash and the client fails CLOSED, so
    # no install can latch onto a half-swapped pack. Then swap the .db and .gz,
    # and place the sidecar LAST — the sidecar is the commit marker, so a NEW
    # sidecar can never coexist with an OLD .gz. A crash anywhere before the
    # final replace leaves the pack fail-closed (re-run to finish), never a
    # silent stale install nor a permanent gz/sidecar mismatch.
    sha_path = out_path + ".sha256"
    gz_path = out_path + ".gz"
    if os.path.exists(sha_path):
        os.remove(sha_path)
    os.replace(tmp_db, out_path)
    os.replace(tmp_gz, gz_path)
    os.replace(tmp_sha, sha_path)

    raw_size_mb = os.path.getsize(out_path) / (1024 * 1024)
    wire_size_mb = os.path.getsize(gz_path) / (1024 * 1024)
    limit_mb = SIZE_LIMIT_MB.get(pack_type, 200)

    return {
        "pack_type": pack_type,
        "source_count": source_count,
        "row_count": row_count,
        "sha256": sha,
        "input_manifest_hash": input_manifest_hash,
        "bundle_version": bundle_version,
        "raw_size_mb": raw_size_mb,    # on-disk / OPFS footprint on the client
        "wire_size_mb": wire_size_mb,  # actual download (gated)
        "size_ok": wire_size_mb <= limit_mb,
        "size_limit_mb": limit_mb,
    }


def write_pack_report(out_path: str, stats: dict) -> str:
    """Register a built pack against the input manifest it inherited."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from corpus_builder.build_report import (
        build_report,
        manifest_reference_from_meta,
        output_entry,
        write_report,
    )

    reference = manifest_reference_from_meta({
        "input_manifest_hash": stats["input_manifest_hash"],
        "bundle_version": stats.get("bundle_version"),
        "source_count": stats["source_count"],
        "record_count": stats["row_count"],
    })
    outputs = [output_entry(out_path, record_count=stats["row_count"])]
    gz_path = out_path + ".gz"
    if os.path.exists(gz_path):
        outputs.append(output_entry(gz_path))
    report = build_report(
        artifact_name=f"{stats['pack_type']}.db",
        artifact_kind="offline-pack",
        manifest_ref=reference,
        outputs=outputs,
        counts={"sources": stats["source_count"], "rows": stats["row_count"]},
        generator="build_offline_pack/1",
    )
    return str(write_report(report, out_path + ".build-report.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Samudra Manthanam offline search packs")
    parser.add_argument("--db", default="corpus.db", help="Path to corpus.db (default: corpus.db)")
    parser.add_argument("--out", default="offline-packs", help="Output directory (default: offline-packs)")
    parser.add_argument("--pack", choices=["base", "dict", "both"], default="both",
                        help="Which pack(s) to build (default: both)")
    parser.add_argument("--validate-only", action="store_true",
                        help="Validate corpus.db only — no output files (CI gate)")
    args = parser.parse_args()

    if args.validate_only:
        return validate_corpus_db(args.db)

    if not os.path.exists(args.db):
        print(f"ERROR: {args.db} not found. Run from web/ or pass --db.", file=sys.stderr)
        return 1

    packs_to_build = ["base", "dict"] if args.pack == "both" else [args.pack]
    exit_code = 0

    for pack_type in packs_to_build:
        out_path = os.path.join(args.out, f"{pack_type}.db")
        print(f"\nBuilding {pack_type} pack → {out_path}")
        try:
            stats = build_pack(args.db, out_path, pack_type)
            gate = "OK" if stats["size_ok"] else "EXCEEDS LIMIT"
            print(
                f"  Done: {stats['source_count']} sources, {stats['row_count']:,} rows, "
                f"raw {stats['raw_size_mb']:.1f} MB → wire {stats['wire_size_mb']:.1f} MB gzip "
                f"({stats['size_limit_mb']} MB wire limit) [{gate}]"
            )
            print(f"  SHA-256 (raw .db): {stats['sha256']}")
            if stats.get("input_manifest_hash"):
                report_path = write_pack_report(out_path, stats)
                print(f"  Input manifest:    {stats['input_manifest_hash']}")
                print(f"  Build report:      {report_path}")
            else:
                print("  Input manifest:    none (corpus.db was built without a manifest)")
            if not stats["size_ok"]:
                print(
                    f"FAIL: {pack_type}.db.gz ({stats['wire_size_mb']:.1f} MB) exceeds "
                    f"{stats['size_limit_mb']} MB wire limit", file=sys.stderr
                )
                exit_code = 1
        except Exception as exc:
            print(f"ERROR building {pack_type} pack: {exc}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
