#!/usr/bin/env python3
"""H558 batch builder: run the RU→canonical, Sanskrit→canonical, and alignment
stages for a range of Devībhāgavata-purāṇa skandhas, emitting one aligned JSONL
+ one alignment report per skandha. HTML emission is a separate step
(build_corpus_html.py). Skandha 1 was done by H534; default here is 2–12.

The six Ignatjev volumes hold skandhas two-per-volume: Vol N = skandhas 2N-1, 2N.

Usage:
    python build_dbhp_skandhas.py \
        --pdf-dir "<...>/AdnrejIgnatjev/devibhagavata-purana" \
        [--skandhas 2-12] [--output-dir jsonl]
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


def vol_of(skandha: int) -> int:
    return (skandha + 1) // 2


def run(cmd: list[str]) -> None:
    print("  $", " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True, cwd=_HERE, encoding="utf-8")


def parse_range(spec: str) -> list[int]:
    if "-" in spec:
        a, b = spec.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in spec.split(",")]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-dir", required=True,
                    help="dir holding 'Девибхагавата-пурана. Том N.pdf'")
    ap.add_argument("--skandhas", default="2-12")
    ap.add_argument("--output-dir", default="jsonl")
    args = ap.parse_args()

    pdf_dir = Path(args.pdf_dir)
    out = Path(args.output_dir)
    summary: list[dict] = []

    for sk in parse_range(args.skandhas):
        vol = vol_of(sk)
        pdf = pdf_dir / f"Девибхагавата-пурана. Том {vol}.pdf"
        itx = _HERE / "sanskrit_src" / f"devIbhAgavatam{sk:02d}.itx"
        print(f"\n=== skandha {sk} (Vol {vol}) ===")
        # 1. Russian side (parse the whole volume, keep only this skandha)
        run([sys.executable, "ignatjev_pdf_to_canonical.py", "--pdf", str(pdf),
             "--skandha-only", str(sk), "--output-dir", args.output_dir])
        ru = out / f"{WORK}_s{sk}.raw.jsonl"
        # 2. Sanskrit side
        run([sys.executable, "sanskritdocuments_dbhp_to_canonical.py",
             "--itx", str(itx), "--skandha", str(sk), "--output-dir", args.output_dir])
        sa = out / f"{WORK}_s{sk}.sanskrit.jsonl"
        # 3. Align on the shared SKANDHA.CHAPTER.VERSE key
        aligned = out / f"{WORK}-{sk}.jsonl"
        report = out / f"{WORK}-{sk}.alignment.json"
        run([sys.executable, "align_sanskrit.py", "--ru", str(ru), "--sa", str(sa),
             "--out", str(aligned), "--report", str(report)])
        rep = json.loads(report.read_text(encoding="utf-8"))
        rep["skandha"] = sk
        summary.append(rep)

    print("\n===== ALIGNMENT SUMMARY =====")
    for r in summary:
        keys = [k for k in ("matched", "ru_only", "sa_orphan", "ru_total",
                            "sa_total", "match_rate", "pct_aligned") if k in r]
        line = "  ".join(f"{k}={r[k]}" for k in keys)
        print(f"  skandha {r['skandha']:>2}: {line}")


if __name__ == "__main__":
    main()
