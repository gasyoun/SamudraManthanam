#!/usr/bin/env python3
"""H927 fan-out prep: slice book 12's remaining taranga (not yet aligned in
the interrupted prior pass) and book 14 (QA re-run, all tarangas) into
per-taranga SA/RU text files + a resolved task list.

Adapted from H928's h927_prep_taranga_slices.py (same book1-10 rekey prep
pattern); reuses parse_sanskrit/parse_russian from somadeva_gretil_to_canonical.py
(H910) unchanged. Taranga 0 is never a fan-out task (single-sloka mangala,
hardcoded 1:1 downstream) -- only tarangas actually needing an LLM alignment
call are emitted here.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from somadeva_gretil_to_canonical import parse_sanskrit, parse_russian

# (sa_book, ru_book, [tarangas to slice])
BOOKS = [
    (12, 12, [6] + list(range(8, 37))),  # already done: t0(hardcoded),1-5,7
    (14, 15, [1, 2, 3, 4]),              # QA re-run, replaces the positional map
]


def group_by_taranga(recs):
    out: dict[int, list] = {}
    for r in recs:
        out.setdefault(r["taranga"], []).append(r)
    return out


def build_tasks(src: Path, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    tasks = []
    for sa_book, ru_book, wanted in BOOKS:
        sa_path = src / "chapters_san" / f"kathasaritsagara_san_cleant_chap_{sa_book:02d}.txt"
        ru_path = src / "chapters_rus" / f"kathasaritsagara_rus_cleant_chap_{ru_book:02d}.txt"
        sa = list(parse_sanskrit(sa_path))
        ru = list(parse_russian(ru_path))
        sa_by_t, ru_by_t = group_by_taranga(sa), group_by_taranga(ru)
        ru_idx = 0  # running 1-based global index into ru (idx field), for offset math
        for t in sorted(set(sa_by_t) | set(ru_by_t)):
            sa_slice = sa_by_t.get(t, [])
            ru_slice = ru_by_t.get(t, [])
            ru_global_start = ru_idx + 1
            ru_idx += len(ru_slice)
            if t not in wanted:
                continue
            if not sa_slice:
                continue
            sa_file = outdir / f"book{sa_book:02d}_t{t:02d}.sa.txt"
            ru_file = outdir / f"book{sa_book:02d}_t{t:02d}.ru.txt"
            sa_file.write_text(
                "\n".join(f"[{r['taranga']}.{r['sloka']}] {r['iast']}" for r in sa_slice),
                encoding="utf-8")
            ru_file.write_text(
                "\n".join(f"[{j + 1}] {r['text']}" for j, r in enumerate(ru_slice)),
                encoding="utf-8")
            tasks.append({
                "sa_book": sa_book, "ru_book": ru_book, "taranga": t,
                "sa_path": str(sa_file), "ru_path": str(ru_file),
                "sa_count": len(sa_slice), "ru_count": len(ru_slice),
                "ru_global_start": ru_global_start,
            })
        book_sa_total = sum(len(v) for t, v in sa_by_t.items() if t in wanted)
        task_sa_total = sum(t["sa_count"] for t in tasks if t["sa_book"] == sa_book)
        assert book_sa_total == task_sa_total, (
            f"book {sa_book}: {task_sa_total} sliced vs {book_sa_total} parsed")
    return tasks


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--tasks-out", required=True)
    args = ap.parse_args()
    tasks = build_tasks(Path(args.src), Path(args.outdir))
    Path(args.tasks_out).write_text(
        json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    total_sa = sum(t["sa_count"] for t in tasks)
    total_ru = sum(t["ru_count"] for t in tasks)
    print(f"{len(tasks)} taranga tasks, {total_sa} slokas, {total_ru} RU sentences -> {args.tasks_out}")
