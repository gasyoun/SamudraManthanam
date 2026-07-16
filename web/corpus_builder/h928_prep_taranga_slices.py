#!/usr/bin/env python3
"""H928 fan-out prep: slice books 1-10 into per-taranga SA/RU text files +
a resolved task list.

Taranga slices are derived directly from parse_sanskrit/parse_russian's
already-ordered output (grouped by each record's own 'taranga' field), NOT
from h928_plan.json's cumulative offsets -- those were found to drift (a
per-book sa_count cross-check showed both under- and over-counts vs the
whole-book totals, e.g. book 5 short by 223 slokas), so this derives ground
truth instead of trusting a precomputed plan. Taranga 0 (the mangala
invocation, whose Russian side is the translator's preface sentences before
the first wave header) is its own task like every other taranga -- kept
separate rather than folded into taranga 1, so no task ever mixes two
taranga's sloka numbering. Reuses parse_sanskrit/parse_russian from
somadeva_gretil_to_canonical.py (H910) unchanged.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from somadeva_gretil_to_canonical import parse_sanskrit, parse_russian

BOOKS = {
    1: "01", 2: "02", 3: "03", 4: "04", 5: "05",
    6: "06", 7: "07", 8: "08", 9: "09", 10: "10",
}


def group_by_taranga(recs):
    out: dict[int, list] = {}
    for r in recs:
        out.setdefault(r["taranga"], []).append(r)
    return out


def build_tasks(src: Path, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    tasks = []
    for book, num in BOOKS.items():
        sa_path = src / "chapters_san" / f"kathasaritsagara_san_cleant_chap_{num}.txt"
        ru_path = src / "chapters_rus" / f"kathasaritsagara_rus_cleant_chap_{num}.txt"
        sa = list(parse_sanskrit(sa_path))
        ru = list(parse_russian(ru_path))
        sa_by_t, ru_by_t = group_by_taranga(sa), group_by_taranga(ru)
        ru_idx = 0  # running 1-based global index into ru (idx field), for offset math
        for t in sorted(set(sa_by_t) | set(ru_by_t)):
            sa_slice = sa_by_t.get(t, [])
            ru_slice = ru_by_t.get(t, [])
            ru_global_start = ru_idx + 1
            ru_idx += len(ru_slice)
            if not sa_slice:
                continue
            sa_file = outdir / f"book{book:02d}_t{t:02d}.sa.txt"
            ru_file = outdir / f"book{book:02d}_t{t:02d}.ru.txt"
            # tag SA lines with the literal (taranga, sloka) from the parsed
            # record -- always this task's own taranga now, kept explicit so
            # the mapping schema/prompt stay uniform across every task.
            sa_file.write_text(
                "\n".join(f"[{r['taranga']}.{r['sloka']}] {r['iast']}" for r in sa_slice),
                encoding="utf-8")
            ru_file.write_text(
                "\n".join(f"[{j + 1}] {r['text']}" for j, r in enumerate(ru_slice)),
                encoding="utf-8")
            tasks.append({
                "book": book, "taranga": t,
                "sa_path": str(sa_file), "ru_path": str(ru_file),
                "sa_count": len(sa_slice), "ru_count": len(ru_slice),
                "ru_global_start": ru_global_start,
            })
        book_sa_total = sum(len(v) for v in sa_by_t.values())
        task_sa_total = sum(t["sa_count"] for t in tasks if t["book"] == book)
        assert book_sa_total == task_sa_total, (
            f"book {book}: {task_sa_total} sliced vs {book_sa_total} parsed")
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
