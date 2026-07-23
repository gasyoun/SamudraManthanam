#!/usr/bin/env python3
"""Scratch driver for H1438 Wave B -- runs the 3-stage pipeline for one work.
Not committed; deleted at the end of the pass (mirrors the ad-hoc scratch
`ingest.py` FTS5 smoke test the Wave-A-tail pass used and discarded)."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
DATA_DIR = HERE / "../../Index/lib/x86_64-win64/Data"
DATA_TXT = HERE / "../../Index/lib/x86_64-win64/Programdata/data.txt"


def run(cmd):
    print("+", " ".join(str(c) for c in cmd))
    r = subprocess.run(cmd, cwd=HERE)
    if r.returncode != 0:
        sys.exit(r.returncode)


def main():
    slug = sys.argv[1]
    inputs = sys.argv[2:]
    run([sys.executable, "ignatiev_book_to_canonical.py",
         "--input", *inputs, "--work-slug", slug, "--output-dir", "jsonl"])
    run([sys.executable, "align_sanskrit.py",
         "--ru", f"jsonl/{slug}.raw.jsonl",
         "--out", f"jsonl/{slug}.jsonl",
         "--report", f"jsonl/{slug}.alignment.json"])
    run([sys.executable, "build_corpus_html.py",
         "--jsonl", f"jsonl/{slug}.jsonl",
         "--report", f"jsonl/{slug}.report.json",
         "--meta", f"{slug}.meta.json",
         "--data-dir", str(DATA_DIR),
         "--data-txt", str(DATA_TXT),
         "--split", "none",
         "--slug", slug])
    with open(HERE / f"jsonl/{slug}.report.json", encoding="utf-8") as f:
        report = json.load(f)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
