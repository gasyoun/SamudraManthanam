#!/usr/bin/env python3
"""H927 final emit: build the complete book12 JSONL (existing 7-taranga
partial + new 30 tarangas, taranga-ordered, seq renumbered globally so
ingest.py's line_num context queries stay monotonic across the whole book)
and the complete book14 JSONL (hardcoded t0 + new t1-4, single emit_jsonl
call so seq is already globally consistent -- replaces the old positional
map entirely per H927's QA re-run goal)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from somadeva_gretil_to_canonical import parse_sanskrit, parse_russian, emit_jsonl, validate_mapping

SRC = Path("../../../somadeva")
MERGED = Path("somadeva_alignments/_h927_merged")
JSONL_DIR = Path("jsonl")

# ---- book 12 ----
sa12 = list(parse_sanskrit(SRC / "chapters_san" / "kathasaritsagara_san_cleant_chap_12.txt"))
ru12 = list(parse_russian(SRC / "chapters_rus" / "kathasaritsagara_rus_cleant_chap_12.txt"))
new12_mapping = json.loads((MERGED / "book12_new_tarangas.json").read_text(encoding="utf-8"))

problems = validate_mapping(sa12, new12_mapping)
if problems:
    print("book12 new-tarangas validate_mapping PROBLEMS:")
    for p in problems:
        print(" -", p)
    sys.exit(1)

new12_records = emit_jsonl(sa12, ru12, new12_mapping, slug="kathasaritsagara")
new12_by_chapter: dict[str, list] = {}
for r in new12_records:
    new12_by_chapter.setdefault(r["chapter"], []).append(r)

old12_records = [json.loads(l) for l in (JSONL_DIR / "kathasaritsagara-12.jsonl").open(encoding="utf-8")]
old12_by_chapter: dict[str, list] = {}
for r in old12_records:
    old12_by_chapter.setdefault(r["chapter"], []).append(r)

DONE_TARANGAS = {0, 1, 2, 3, 4, 5, 7}
final12 = []
for t in range(0, 37):
    key = str(t)
    if t in DONE_TARANGAS:
        final12.extend(old12_by_chapter.get(key, []))
    else:
        final12.extend(new12_by_chapter.get(key, []))

for i, r in enumerate(final12, start=1):
    r["seq"] = i

out12 = JSONL_DIR / "kathasaritsagara-12.jsonl"
out12.write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in final12) + "\n", encoding="utf-8")
tarangas12 = sorted(set(int(r["chapter"]) for r in final12))
print(f"book12: wrote {len(final12)} records, tarangas {tarangas12} -> {out12}")
assert tarangas12 == list(range(0, 37)), f"book12 missing tarangas: {set(range(0,37)) - set(tarangas12)}"

# ---- book 14 (full QA re-run: t0 hardcoded + new t1-4) ----
sa14 = list(parse_sanskrit(SRC / "chapters_san" / "kathasaritsagara_san_cleant_chap_14.txt"))
ru14 = list(parse_russian(SRC / "chapters_rus" / "kathasaritsagara_rus_cleant_chap_15.txt"))
new14_mapping = json.loads((MERGED / "book14_new_tarangas.json").read_text(encoding="utf-8"))
t0_hardcoded = [{"ru_idx": 1, "taranga": 0, "sloka_start": 1, "sloka_end": 1, "confidence": 0.95}]
full14_mapping = t0_hardcoded + new14_mapping

problems14 = validate_mapping(sa14, full14_mapping)
if problems14:
    print("book14 full-mapping validate_mapping PROBLEMS:")
    for p in problems14:
        print(" -", p)
    sys.exit(1)

final14 = emit_jsonl(sa14, ru14, full14_mapping, slug="kathasaritsagara")
confs14 = [m.get("confidence", 1.0) for m in full14_mapping]
out14 = JSONL_DIR / "kathasaritsagara-14.jsonl"
out14.write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in final14) + "\n", encoding="utf-8")
tarangas14 = sorted(set(int(r["chapter"]) for r in final14))
print(f"book14: wrote {len(final14)} records, tarangas {tarangas14} -> {out14}")
print(f"book14 confidence: min {min(confs14):.2f}, mean {sum(confs14)/len(confs14):.2f}; "
      f"{sum(1 for c in confs14 if c < 0.6)} groups < 0.6")
