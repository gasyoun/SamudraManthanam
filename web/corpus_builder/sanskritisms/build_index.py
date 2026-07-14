"""CLI: run the санскритизм stemmer over one or all verse-structure sources.

Usage:
    python -m web.corpus_builder.sanskritisms.build_index --source 03_mahabharata-aranyakaparva
    python -m web.corpus_builder.sanskritisms.build_index --all

Output lands under `nkrya-parallel/export/sanskritisms/` (gitignored bulk
convention matches `nkrya_export.py`/`nkrya_annotate.py`; small per-source
lexicon files are what actually gets committed — see README.md).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
JSONL_DIR = REPO_ROOT / "web" / "corpus_builder" / "jsonl"
DATA_META_DIR = REPO_ROOT / "Index" / "lib" / "x86_64-win64" / "Data"
DEFAULT_OUT_DIR = REPO_ROOT / "nkrya-parallel" / "export" / "sanskritisms"

sys.path.insert(0, str(REPO_ROOT))

from web.corpus_builder.sanskritisms import disambiguate, stemmer  # noqa: E402
from web.corpus_builder.sanskritisms.lexicons import (  # noqa: E402
    RussianDictionary,
    build_sorensen_pool,
    load_foreign_words,
)


def discover_verse_sources() -> tuple[list[str], list[str]]:
    """Returns (slugs_with_jsonl, slugs_missing_jsonl) for every
    `structure: verse` source in the live meta.json layer (SPEC.md §5)."""
    verse_slugs: list[str] = []
    for pattern in ("*.html.meta.json", "*.htm.meta.json", "*.txt.meta.json"):
        for meta_path in DATA_META_DIR.glob(pattern):
            with meta_path.open(encoding="utf-8") as fh:
                meta = json.load(fh)
            if meta.get("structure") == "verse":
                slug = meta.get("slug")
                if slug:
                    verse_slugs.append(slug)

    jsonl_slugs = {p.stem for p in JSONL_DIR.glob("*.jsonl")}
    have = sorted(set(s for s in verse_slugs if s in jsonl_slugs))
    missing = sorted(set(s for s in verse_slugs if s not in jsonl_slugs))
    return have, missing


def iter_ru_texts(jsonl_path: Path):
    with jsonl_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("lang") == "ru":
                yield rec["text"]


def run_source(slug: str, pool, dictionary: RussianDictionary, foreign_words: frozenset[str]) -> dict:
    jsonl_path = JSONL_DIR / f"{slug}.jsonl"
    all_detections: list[stemmer.Detection] = []
    n_records = 0
    for text in iter_ru_texts(jsonl_path):
        n_records += 1
        all_detections.extend(stemmer.detect(text, pool, dictionary, foreign_words))

    resolved = disambiguate.resolve(all_detections)
    entries = disambiguate.aggregate(resolved)
    entries.sort(key=lambda e: (-e.count, e.lemma))

    n_review = sum(1 for e in entries if e.needs_review)
    n_rescued = sum(e.capitalization_rescued_count for e in entries)

    return {
        "slug": slug,
        "n_ru_records": n_records,
        "n_detections_raw": len(all_detections),
        "n_lemma_entries": len(entries),
        "n_needs_review": n_review,
        "n_capitalization_rescued": n_rescued,
        "entries": entries,
    }


def write_outputs(result: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = result["slug"]

    lexicon_path = out_dir / f"{slug}.sanskritisms.jsonl"
    with lexicon_path.open("w", encoding="utf-8") as fh:
        for e in result["entries"]:
            row = {
                "source": slug,
                "lemma": e.lemma,
                "surface_forms": sorted(e.surface_forms),
                "count": e.count,
                "needs_review": e.needs_review,
                "lemma_candidates": e.lemma_candidates,
            }
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    report_path = out_dir / f"{slug}.sanskritisms_report.json"
    report = {k: v for k, v in result.items() if k != "entries"}
    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="single source slug (matches a web/corpus_builder/jsonl/<slug>.jsonl)")
    parser.add_argument("--all", action="store_true", help="run every discovered verse source with canonical JSONL")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    pool = build_sorensen_pool()
    dictionary = RussianDictionary()
    foreign_words = load_foreign_words()

    if args.all:
        have, missing = discover_verse_sources()
        print(f"{len(have)} verse sources with canonical JSONL; {len(missing)} skipped (no JSONL yet): {missing}")
        for slug in have:
            result = run_source(slug, pool, dictionary, foreign_words)
            write_outputs(result, args.out_dir)
            print(
                f"  {slug}: {result['n_lemma_entries']} lemmas "
                f"({result['n_needs_review']} needs_review, {result['n_capitalization_rescued']} rescued)"
            )
    elif args.source:
        result = run_source(args.source, pool, dictionary, foreign_words)
        write_outputs(result, args.out_dir)
        print(json.dumps({k: v for k, v in result.items() if k != "entries"}, ensure_ascii=False, indent=2))
    else:
        parser.error("pass --source SLUG or --all")


if __name__ == "__main__":
    main()
