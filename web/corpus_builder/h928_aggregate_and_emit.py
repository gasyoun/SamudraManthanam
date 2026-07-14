#!/usr/bin/env python3
"""H928 aggregation: turn the per-taranga Workflow fan-out results (one JSON
object per taranga task, as returned by the alignment Workflow) into
per-book canonical JSONL for books 1-10.

Input is a JSON array of {book, taranga, ru_global_start, sa_count, ru_count,
groups: [{ru_idx, taranga, sloka_start, sloka_end, confidence}, ...]} --
exactly the Workflow's return value. ru_idx in each group is LOCAL to its
taranga's Russian slice; this script converts it to the GLOBAL per-book idx
(matching parse_russian's own numbering) via ru_global_start before handing
the combined per-book mapping to validate_mapping/emit_jsonl (H910, unchanged).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

from somadeva_gretil_to_canonical import parse_sanskrit, parse_russian, validate_mapping, emit_jsonl

BOOKS = {i: f"{i:02d}" for i in range(1, 11)}


def load_results(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def to_global_mapping(results):
    by_book = defaultdict(list)
    for r in results:
        for g in r.get("groups", []):
            global_idx = r["ru_global_start"] + (g["ru_idx"] - 1)
            by_book[r["book"]].append({
                "ru_idx": global_idx,
                "taranga": g["taranga"],
                "sloka_start": g["sloka_start"],
                "sloka_end": g["sloka_end"],
                "confidence": g.get("confidence", 1.0),
            })
    return by_book


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True, help="workflow return-value JSON")
    ap.add_argument("--src", required=True, help="somadeva clone root")
    ap.add_argument("--outdir", required=True, help="jsonl output dir")
    args = ap.parse_args()

    results = load_results(Path(args.results))
    by_book = to_global_mapping(results)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    src = Path(args.src)
    all_confs = []
    for book, num in BOOKS.items():
        mapping = by_book.get(book, [])
        if not mapping:
            print(f"book {book}: NO MAPPING -- missing from results")
            continue
        sa_path = src / "chapters_san" / f"kathasaritsagara_san_cleant_chap_{num}.txt"
        ru_path = src / "chapters_rus" / f"kathasaritsagara_rus_cleant_chap_{num}.txt"
        sa = list(parse_sanskrit(sa_path))
        ru = list(parse_russian(ru_path))
        problems = validate_mapping(sa, mapping)
        out_path = outdir / f"kathasaritsagara-{book:02d}.jsonl"
        recs = emit_jsonl(sa, ru, mapping, slug="kathasaritsagara")
        out_path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n",
            encoding="utf-8")
        confs = [m.get("confidence", 1.0) for m in mapping]
        all_confs.extend(confs)
        low = [m["ru_idx"] for m in mapping if (m.get("confidence") or 1.0) < 0.6]
        print(f"book {book}: {len(recs)} records, {len(mapping)} groups, "
              f"mean conf {sum(confs)/len(confs):.2f}, {len(low)} < 0.6 -> {out_path}")
        if problems:
            print(f"  VALIDATION PROBLEMS ({len(problems)}):")
            for p in problems[:20]:
                print("   -", p)

    if all_confs:
        print(f"\noverall mean confidence: {sum(all_confs)/len(all_confs):.2f} "
              f"over {len(all_confs)} groups")


if __name__ == "__main__":
    main()
