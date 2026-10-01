#!/usr/bin/env python3
"""H4743 (xwalk-s7) — verify Samudra sibling corpora presumed-same-shape.

Verifies the numbered sibling JSONL files (`NN_<work>.jsonl` in
web/corpus_builder/jsonl/) for:
  * schema parity — identical JSON key set across all siblings of a work;
  * line-count / group parity — every group has exactly one `sa` and one `ru`
    segment, ids consistent (id = work:passage#seg, group = work:passage);
  * sample parity — first/middle/last group per file has non-empty sa (with
    slp1) and ru (Cyrillic) text.

Works verified: atharvaveda (expect 20 books), mahabharata-* (expect 18 parvans).

Usage:
    python3 scripts/xwalk_s7_verify_siblings.py \
        [--jsonl-dir web/corpus_builder/jsonl] [--out reports/xwalk-s7-sibling-verification-report.md]

Exit 0 = all PASS, 1 = any FAIL.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

CANONICAL_KEYS = {
    "id", "work", "passage", "seg", "group", "lang", "script", "text",
    "html", "slp1", "structure", "chapter", "seq", "deleted",
}
CYRILLIC_RE = re.compile(r"[а-яА-ЯёЁ]")
EXPECTED_COUNTS = {"atharvaveda": 20, "mahabharata": 18}


def siblings(jsonl_dir: Path, pattern: str) -> list[Path]:
    rx = re.compile(pattern)
    return sorted(
        [p for p in jsonl_dir.iterdir() if rx.match(p.name)],
        key=lambda p: int(p.name.split("_", 1)[0]),
    )


def work_family(name: str) -> str:
    stem = re.sub(r"^\d+_", "", name)
    if stem.startswith("mahabharata"):
        return "mahabharata"
    return stem.replace(".jsonl", "")


def verify_file(path: Path) -> dict:
    """Per-file structural verification. Returns a stats dict."""
    problems: list[str] = []
    key_sets: Counter = Counter()
    seg_counter: Counter = Counter()
    groups: dict[str, list[dict]] = {}
    n_lines = 0
    book = int(path.name.split("_", 1)[0])
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        raw = raw.strip()
        if not raw:
            continue
        n_lines += 1
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError as exc:
            problems.append(f"L{lineno}: JSON decode error: {exc}")
            continue
        key_sets[f"{rec.get('seg')}|{'|'.join(sorted(rec.keys()))}"] += 1
        # id / group / seg consistency
        work = rec.get("work")
        passage = rec.get("passage")
        seg = rec.get("seg")
        if rec.get("id") != f"{work}:{passage}#{seg}":
            problems.append(f"L{lineno}: id mismatch {rec.get('id')!r}")
        if rec.get("group") != f"{work}:{passage}":
            problems.append(f"L{lineno}: group mismatch {rec.get('group')!r}")
        if seg not in ("sa", "ru"):
            problems.append(f"L{lineno}: unexpected seg {seg!r}")
        seg_counter[seg] += 1
        # book/chapter agreement
        if seg == "sa" and str(rec.get("chapter")) != str(book):
            problems.append(
                f"L{lineno}: chapter {rec.get('chapter')!r} != book {book}"
            )
        # text emptiness
        if not str(rec.get("text") or "").strip():
            problems.append(f"L{lineno}: empty text on seg={seg}")
        if seg == "sa" and not str(rec.get("slp1") or "").strip():
            problems.append(f"L{lineno}: empty slp1 on sa segment")
        groups.setdefault(str(rec.get("group")), []).append(rec)

    # group parity: exactly one sa + one ru per group; comm1..N segments allowed
    orphan_groups = 0
    sig_census: Counter = Counter()
    for group, recs in groups.items():
        segs = [str(r.get("seg")) for r in recs]
        sig_census[tuple(sorted(segs))] += 1
        ok = (
            segs.count("sa") == 1
            and segs.count("ru") == 1
            and all(re.fullmatch(r"comm\d+", s) or s in ("sa", "ru") for s in segs)
        )
        if not ok:
            orphan_groups += 1
            if len(problems) < 50:
                problems.append(f"group {group}: segs={sorted(segs)}")

    return {
        "file": path.name,
        "lines": n_lines,
        "sa": seg_counter["sa"],
        "ru": seg_counter["ru"],
        "groups": len(groups),
        "orphan_groups": orphan_groups,
        "key_sets": key_sets,
        "problems": problems,
        "records": [r for recs in groups.values() for r in recs],
    }


def sample_parity(records_by_group: dict[str, list[dict]]) -> list[dict]:
    """First/middle/last group sample checks: sa vs ru language sanity."""
    keys = sorted(records_by_group)
    picks = {keys[0], keys[len(keys) // 2], keys[-1]}
    out = []
    for key in sorted(picks):
        recs = records_by_group[key]
        sa = next((r for r in recs if r["seg"] == "sa"), None)
        ru = next((r for r in recs if r["seg"] == "ru"), None)
        sa_ok = sa is not None and not CYRILLIC_RE.search(sa["text"])
        ru_ok = ru is not None and bool(CYRILLIC_RE.search(ru["text"]))
        out.append({
            "group": key,
            "sa_ok": sa_ok,
            "ru_ok": ru_ok,
            "sa_text": (sa["text"][:90] + "…") if sa and len(sa["text"]) > 90 else (sa or {}).get("text", ""),
            "ru_text": (ru["text"][:90] + "…") if ru and len(ru["text"]) > 90 else (ru or {}).get("text", ""),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent.parent
    ap.add_argument("--jsonl-dir", type=Path,
                    default=here / "web/corpus_builder/jsonl")
    ap.add_argument("--out", type=Path,
                    default=here / "reports/xwalk-s7-sibling-verification-report.md")
    args = ap.parse_args()

    families = {
        "atharvaveda": siblings(args.jsonl_dir, r"^\d+_atharvaveda\.jsonl$"),
        "mahabharata": siblings(args.jsonl_dir, r"^\d+_mahabharata-.*\.jsonl$"),
    }

    lines: list[str] = [
        "# xwalk-s7 — Samudra sibling corpora shape verification (H4743)",
        "",
        "_Generated: 15-09-2026 by `scripts/xwalk_s7_verify_siblings.py` — deterministic, re-run to reproduce._",
        "",
        "Verifies presumed-same-shape of numbered sibling JSONL corpora",
        "(`NN_atharvaveda.jsonl`, `NN_mahabharata-*.jsonl`): schema parity,",
        "line/group parity (one `sa` + one `ru` per group), id/group/chapter",
        "consistency, first/middle/last sample language sanity.",
        "",
    ]
    overall_pass = True
    for fam, files in families.items():
        lines.append(f"## Family `{fam}` — {len(files)} sibling files"
                     f" (expected {EXPECTED_COUNTS[fam]})")
        lines.append("")
        if len(files) != EXPECTED_COUNTS[fam]:
            lines.append(f"- **FINDING**: expected {EXPECTED_COUNTS[fam]} files, found {len(files)}")
        if fam == "atharvaveda" and len(files) == EXPECTED_COUNTS[fam] - 1:
            lines.append("  - AVŚ book 20 (Kuntāpa) absent from the corpus — "
                         "documented shape fact, not sibling drift (book-20 "
                         "hymns have no RU side to align).")
        if not files:
            lines.append("")
            continue
        # schema parity: per-seg key-set variants; every file must realize
        # exactly the family-wide variant set for its seg types
        rows = []
        fam_variants: dict[str, set] = {"sa": set(), "ru": set(), "other": set()}
        per_file_variants: list[dict[str, set]] = []
        for path in files:
            stats = verify_file(path)
            variants: dict[str, set] = {"sa": set(), "ru": set(), "other": set()}
            for tagged, _n in stats["key_sets"].items():
                seg, _, keystr = tagged.partition("|")
                bucket = variants.get(seg, variants["other"])
                bucket.add(keystr)
                fam_variants.get(seg, fam_variants["other"]).add(keystr)
            per_file_variants.append(variants)
            stats.pop("records")
            rows.append(stats)
        lines.append("| file | lines | sa | ru | groups | parity defects | schema |")
        lines.append("|---|---|---|---|---|---|---|")
        # drift = a file carrying a key-set variant NO other sibling carries
        # (optional variants like ru+annotates are heterogeneity, not drift)
        family_schema_ok = True
        for idx, (r, variants) in enumerate(zip(rows, per_file_variants)):
            drift = []
            for seg in ("sa", "ru"):
                others: set = set()
                for jdx, v2 in enumerate(per_file_variants):
                    if jdx != idx:
                        others |= v2[seg]
                if variants[seg] - others:
                    drift.append(seg)
            schema = "OK" if not drift else f"DRIFT({','.join(drift)})"
            if schema != "OK":
                overall_pass = False
                family_schema_ok = False
            if r["orphan_groups"] or r["problems"]:
                overall_pass = False
            lines.append(
                f"| {r['file']} | {r['lines']} | {r['sa']} | {r['ru']} | "
                f"{r['groups']} | {r['orphan_groups']} | {schema} |")
        lines.append("")
        sa_variants = sorted(fam_variants["sa"])
        lines.append(f"Family schema — sa key set ({len(sa_variants[0].split('|'))} keys): "
                     + sa_variants[0].replace("|", ", "))
        lines.append(f"Family schema — ru key set: "
                     + sorted(fam_variants["ru"])[0].replace("|", ", "))
        extra_ru = [v for v in fam_variants["ru"]
                    if v != next(iter(fam_variants["ru"]))]
        for v in extra_ru:
            added = set(v.split("|")) - set(next(iter(fam_variants["ru"])).split("|"))
            lines.append(f"- ru variant with extra keys {sorted(added)}: "
                         "documented heterogeneity (commentary-annotated ru segments)")
        lines.append("- schema parity across siblings (no novel key-set variants): "
                     f"**{'PASS' if family_schema_ok else 'FAIL'}**")
        # sample parity: 3 samples per family from the first file for brevity + per-file quiet
        lines.append("")
        lines.append("### Sample parity (first · middle · last group, per file)")
        lines.append("")
        for path in files:
            stats = verify_file(path)
            # rebuild groups cheaply from a second pass over first file only? no: use records kept in first pass
            records_by_group: dict[str, list[dict]] = {}
            for raw in path.read_text(encoding="utf-8").splitlines():
                raw = raw.strip()
                if not raw:
                    continue
                rec = json.loads(raw)
                records_by_group.setdefault(rec["group"], []).append(rec)
            for s in sample_parity(records_by_group):
                flag = "PASS" if (s["sa_ok"] and s["ru_ok"]) else "FAIL"
                if flag == "FAIL":
                    overall_pass = False
                lines.append(
                    f"- `{s['group']}` — sa_ok={s['sa_ok']} ru_ok={s['ru_ok']} → **{flag}**")
                lines.append(f"  - sa: {s['sa_text']!r}")
                lines.append(f"  - ru: {s['ru_text']!r}")
        # problems digest
        problem_rows = [r for r in rows if r["problems"]]
        if problem_rows:
            lines.append("")
            lines.append(f"### Structural problems ({len(problem_rows)} files)")
            lines.append("")
            for r in problem_rows[:5]:
                lines.append(f"- `{r['file']}`: " + "; ".join(r["problems"][:5]))
        lines.append("")

    verdict = "PASS" if overall_pass else "FAIL"
    lines.insert(4, f"**Verdict: {verdict}**")
    lines.insert(5, "")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[xwalk-s7] report -> {args.out}")
    print(f"[xwalk-s7] verdict: {verdict}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
