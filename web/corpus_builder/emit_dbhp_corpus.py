#!/usr/bin/env python3
"""H558 corpus emitter: turn the per-skandha aligned JSONL + parser reports into
the app HTML — one file per skandha (skandhas 2–12; skandha 1 shipped by H534)
plus one combined ``devibhagavata-purana.html`` for the whole 12-skandha work —
and register every new filename in data.txt.

Runs build_corpus_html twice: once with --split over skandhas 2–12 (so skandha
1's already-published file is not rewritten), once with --combined over all 12
(the combined file needs every skandha). Chapter titles are merged from each
skandha's parser report.

Usage:
    python emit_dbhp_corpus.py --data-root ../../Index/lib/x86_64-win64
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

WORK = "devibhagavata-purana"
_HERE = Path(__file__).resolve().parent
_JSONL = _HERE / "jsonl"


def merged_report(skandhas: list[int], out_path: Path) -> Path:
    """Concatenate the chapter_titles of each skandha's parser report."""
    titles: list[dict] = []
    for sk in skandhas:
        rep = _JSONL / f"{WORK}_s{sk}.report.json"
        data = json.loads(rep.read_text(encoding="utf-8"))
        titles.extend(data.get("chapter_titles", []))
    out_path.write_text(json.dumps({"chapter_titles": titles}, ensure_ascii=False),
                        encoding="utf-8")
    return out_path


def concat_jsonl(skandhas: list[int], out_path: Path) -> Path:
    with out_path.open("w", encoding="utf-8") as w:
        for sk in skandhas:
            src = _JSONL / f"{WORK}-{sk}.jsonl"
            w.write(src.read_text(encoding="utf-8"))
    return out_path


def run(cmd: list[str]) -> None:
    print("  $", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True, cwd=_HERE, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True,
                    help="app data root holding Data/ and Programdata/data.txt")
    ap.add_argument("--meta", default=str(_HERE / f"{WORK}.meta.json"))
    args = ap.parse_args()

    root = Path(args.data_root)
    data_dir = root / "Data"
    data_txt = root / "Programdata" / "data.txt"

    # per-skandha files for 2–12 (skandha 1 already published by H534)
    split_sk = list(range(2, 13))
    rep_split = merged_report(split_sk, _JSONL / "_merged_report_2_12.json")
    jl_split = concat_jsonl(split_sk, _JSONL / "_concat_2_12.jsonl")
    print("== per-skandha (2–12) ==")
    run([sys.executable, "build_corpus_html.py", "--jsonl", str(jl_split),
         "--report", str(rep_split), "--meta", args.meta,
         "--data-dir", str(data_dir), "--data-txt", str(data_txt),
         "--split", "skandha"])

    # combined file for the whole 12-skandha work
    all_sk = list(range(1, 13))
    rep_all = merged_report(all_sk, _JSONL / "_merged_report_1_12.json")
    jl_all = concat_jsonl(all_sk, _JSONL / "_concat_1_12.jsonl")
    print("== combined (1–12) ==")
    run([sys.executable, "build_corpus_html.py", "--jsonl", str(jl_all),
         "--report", str(rep_all), "--meta", args.meta,
         "--data-dir", str(data_dir), "--data-txt", str(data_txt),
         "--combined"])


if __name__ == "__main__":
    main()
