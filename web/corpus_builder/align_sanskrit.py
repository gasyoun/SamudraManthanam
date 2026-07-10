#!/usr/bin/env python3
"""Attach GRETIL-style Sanskrit onto Ignatjev Russian on SKANDHA.CHAPTER.VERSE.

H534 Phase 2. Source-agnostic verse aligner: it joins a Sanskrit canonical
JSONL (keyed by ``skandha,chapter.verse`` — e.g. produced from GRETIL's
``DbhP_1,6.6`` markers or any edition converted to that key) onto the Russian
JSONL from ``ignatjev_pdf_to_canonical.py``, under the shared ``group`` key,
and emits an aligned JSONL plus an alignment report.

Per ALIGNMENT_SPEC, the alignable unit is the verse group. This joiner is a
**markup/key join, not a statistical aligner**: it pairs ``#sa`` and ``#ru``
only when their ``SKANDHA.CHAPTER.VERSE`` passage ids match. Where the Russian
verse boundaries or numbering diverge from the Sanskrit edition (the known
DBhP risk — the Devigita `dg_1.1 = dbhp_7,31.1` offset), the verse stays
**Russian-only** (cardinality ``0:1``, the sanctioned fallback) and the
mismatch is itemised in the report for human review — never silently dropped
or fabricated.

Reality note (H534): as of ingestion the **full DBhP Sanskrit does not exist
on GRETIL** — only the Devigita fragment (skandha 7, adhy. 31–40,
``dbhp_dgu.htm``). With no Sanskrit input for a skandha, every verse is emitted
Russian-only and the report records 100% ``ru_only`` — which is correct, not a
failure. See the handoff's "GRETIL edition vs Ignatjev's source" open question.

Usage:
    python web/corpus_builder/align_sanskrit.py \
        --ru web/corpus_builder/jsonl/devibhagavata-purana_s1.raw.jsonl \
        [--sa web/corpus_builder/jsonl/dbhp_sanskrit.jsonl] \
        --out web/corpus_builder/jsonl/devibhagavata-purana_s1.aligned.jsonl \
        --report web/corpus_builder/jsonl/devibhagavata-purana_s1.alignment.json
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def load_jsonl(path: Path) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _passage_key(rec: dict) -> str:
    """Normalise a passage id to a comparable SKANDHA.CHAPTER.VERSE key.

    Zero-padding is stripped so a Sanskrit ``1.6.6`` matches a Russian
    ``1.006.006``. Ranges collapse to their first verse for the join.
    """
    p = rec.get("passage", "")
    parts = re.split(r"[.,]", p)
    norm = []
    for tok in parts[:3]:
        first = re.split(r"[-–]", tok)[0]
        norm.append(str(int(first)) if first.isdigit() else first)
    return ".".join(norm)


def align(ru_recs: list[dict], sa_recs: list[dict]):
    """Return (aligned_records, report).

    aligned_records preserves the RU records verbatim and inserts any matched
    SA record into the same group (its ``group`` rewritten to the RU group so
    the emitter renders them together).
    """
    sa_by_key: dict[str, dict] = {}
    for r in sa_recs:
        if r.get("seg") in (None, "sa"):
            sa_by_key.setdefault(_passage_key(r), r)

    ru_groups: dict[str, list[dict]] = defaultdict(list)
    for r in ru_recs:
        ru_groups[r["group"]].append(r)

    report = {
        "ru_verses": sum(1 for r in ru_recs if r.get("seg") == "ru"),
        "sa_verses": len(sa_by_key),
        "matched": 0, "ru_only": 0, "sa_orphan": 0,
        "by_chapter": defaultdict(lambda: {"matched": 0, "ru_only": 0}),
        "sa_orphans": [],
    }

    aligned: list[dict] = []
    matched_keys: set[str] = set()
    for r in ru_recs:
        aligned.append(r)
        if r.get("seg") != "ru":
            continue
        key = _passage_key(r)
        ch = f"{r.get('skandha','?')}.{r.get('chapter','?')}"
        sa = sa_by_key.get(key)
        if sa:
            matched_keys.add(key)
            sa_rec = dict(sa)
            sa_rec["group"] = r["group"]
            sa_rec["passage"] = r["passage"]
            sa_rec["seg"] = "sa"
            sa_rec["seq"] = r.get("seq", 0) - 0.5  # sort before the ru pane
            aligned.append(sa_rec)
            report["matched"] += 1
            report["by_chapter"][ch]["matched"] += 1
        else:
            report["ru_only"] += 1
            report["by_chapter"][ch]["ru_only"] += 1

    for key, sa in sa_by_key.items():
        if key not in matched_keys:
            report["sa_orphan"] += 1
            if len(report["sa_orphans"]) < 50:
                report["sa_orphans"].append(key)

    aligned.sort(key=lambda r: (r.get("seq", 0)))
    report["by_chapter"] = dict(report["by_chapter"])
    return aligned, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ru", required=True)
    ap.add_argument("--sa", help="optional Sanskrit JSONL keyed skandha,ch.verse")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    ru = load_jsonl(Path(args.ru))
    sa = load_jsonl(Path(args.sa)) if args.sa else []
    aligned, report = align(ru, sa)

    with open(args.out, "w", encoding="utf-8") as f:
        for rec in aligned:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    pct = (100 * report["matched"] / report["ru_verses"]
           if report["ru_verses"] else 0)
    print(f"aligned: {report['matched']} matched, {report['ru_only']} ru-only, "
          f"{report['sa_orphan']} sa-orphan  ({pct:.1f}% Sanskrit coverage)")
    if not sa:
        print("  (no Sanskrit input — all verses Russian-only, the sanctioned "
              "fallback; see align_sanskrit.py docstring)")


if __name__ == "__main__":
    main()
