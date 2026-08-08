#!/usr/bin/env python3
"""H2450 pilot: re-ingest Kāma-samūha with prose commentary apparatus.

Uses the H2415 preview text (or regenerable prep) when the gitignored archive
is absent. Pipeline: prep → parse (prose) → align ru_only → HTML → RT summary.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent.parent
_JSONL = _HERE / "jsonl"
_DATA = _REPO / "Index" / "lib" / "x86_64-win64" / "Data"
_DATA_TXT = _REPO / "Index" / "lib" / "x86_64-win64" / "Programdata" / "data.txt"
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))

import ignatiev_book_to_canonical as ib  # noqa: E402


def prep_from_preview(preview: Path) -> str:
    text = preview.read_text(encoding="utf-8")
    lines = text.replace("\x0c", "\n").split("\n")
    idxs = [i for i, ln in enumerate(lines) if ln.strip() == "КАМА-САМУХА"]
    start = idxs[1] if len(idxs) > 1 else (idxs[0] if idxs else 0)
    return "Глава первая\n" + "\n".join(lines[start:])


def roundtrip_check(slug: str) -> dict:
    """HTML → canonical: verse RT + separate comment-text RT."""
    import html_to_canonical as h2c

    html_path = _DATA / f"{slug}.html"
    src_jsonl = _JSONL / f"{slug}.jsonl"
    meta_path = _HERE / f"{slug}.meta.json"
    if not html_path.exists() or not src_jsonl.exists():
        return {"slug": slug, "error": "missing html or jsonl"}

    src_verses: dict[str, str] = {}
    src_comms: dict[str, str] = {}
    with open(src_jsonl, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("deleted"):
                continue
            passage = rec.get("passage")
            text = rec.get("text")
            if not passage or text is None:
                continue
            norm = re.sub(r"\s+", " ", text).strip()
            seg = rec.get("seg")
            if seg in (None, "ru"):
                src_verses[passage] = norm
            elif str(seg).startswith("comm"):
                src_comms[passage] = norm

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    rt_dir = _JSONL / "_rt_tmp_h2450"
    rt_dir.mkdir(parents=True, exist_ok=True)
    report_data: dict = {}
    try:
        h2c.convert_source(
            f"{slug}.html", meta, _DATA, rt_dir, report_data,
        )
    except Exception as e:
        return {"slug": slug, "error": f"rt convert failed: {e}"}

    rt_jsonl = rt_dir / f"{slug}.jsonl"
    rt_verses: dict[str, str] = {}
    rt_comms: dict[str, str] = {}
    if rt_jsonl.exists():
        with open(rt_jsonl, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                passage = rec.get("passage")
                text = rec.get("text")
                if not passage or text is None:
                    continue
                norm = re.sub(r"\s+", " ", text).strip()
                seg = rec.get("seg")
                if seg in (None, "ru"):
                    rt_verses[passage] = norm
                elif str(seg).startswith("comm"):
                    rt_comms[passage] = norm

    def _rate(src: dict, rt: dict) -> dict:
        matched = sum(1 for p, t in src.items() if rt.get(p) == t)
        missing = sum(1 for p in src if p not in rt)
        mismatched = sum(
            1 for p, t in src.items() if p in rt and rt[p] != t
        )
        total = len(src)
        return {
            "total": total,
            "matched": matched,
            "mismatched": mismatched,
            "missing_in_rt": missing,
            "rate_pct": round(100.0 * matched / total, 2) if total else 0.0,
        }

    # Comment text RT: HTML re-parse prefixes "N. " from comment_number span
    # and may remint passage keys. Compare by stripping the leading number
    # and matching on annotates-derived keys when possible, else multiset.
    def _strip_fn(t: str) -> str:
        return re.sub(r"^\d+\.\s*", "", t).strip()

    def _comm_key(passage: str) -> str:
        # "1.5.comm1" → "1.5"; "c.0.p1.comm1" stays as-is
        m = re.match(r"^(\d+\.\d+)", passage)
        return m.group(1) if m else passage

    src_by_ann: dict[str, list[str]] = {}
    for p, t in src_comms.items():
        src_by_ann.setdefault(_comm_key(p), []).append(_strip_fn(t))
    rt_by_ann: dict[str, list[str]] = {}
    for p, t in rt_comms.items():
        # RT may use 1.5.comm1 after id fix, or c.0.pN before.
        key = _comm_key(p)
        rt_by_ann.setdefault(key, []).append(_strip_fn(t))

    c_matched = 0
    c_missing = 0
    c_mismatched = 0
    for ann, texts in src_by_ann.items():
        rt_list = list(rt_by_ann.get(ann) or [])
        for t in texts:
            if t in rt_list:
                rt_list.remove(t)
                c_matched += 1
            elif not rt_list and ann not in rt_by_ann:
                c_missing += 1
            else:
                c_mismatched += 1
    # Fallback content multiset if passage-key scheme still diverges
    if c_matched == 0 and src_comms and rt_comms:
        src_bag = sorted(_strip_fn(t) for t in src_comms.values())
        rt_bag = sorted(_strip_fn(t) for t in rt_comms.values())
        c_matched = sum(1 for a, b in zip(src_bag, rt_bag) if a == b)
        c_mismatched = abs(len(src_bag) - len(rt_bag)) + sum(
            1 for a, b in zip(src_bag, rt_bag) if a != b
        )
        c_missing = max(0, len(src_bag) - len(rt_bag))
        key_scheme = "content_multiset_fallback"
    else:
        key_scheme = "annotates_key"

    c_total = len(src_comms)
    comments_rt = {
        "total": c_total,
        "matched": c_matched,
        "mismatched": c_mismatched,
        "missing_in_rt": c_missing,
        "rate_pct": round(100.0 * c_matched / c_total, 2) if c_total else 0.0,
        "key_scheme": key_scheme,
    }

    return {
        "slug": slug,
        "verses": _rate(src_verses, rt_verses),
        "comments": comments_rt,
        "comments_passage_key_rt": _rate(src_comms, rt_comms),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--preview",
        type=Path,
        default=Path(
            r"C:\Users\user\Documents\GitHub\SamudraManthanam"
            r"\_h2415_preview\kama-samuha.txt"
        ),
    )
    ap.add_argument(
        "--prep-out",
        type=Path,
        default=_HERE / "_h2415_prep" / "kama-samuha.prep.txt",
    )
    ap.add_argument("--skip-html", action="store_true")
    args = ap.parse_args()

    if not args.preview.is_file():
        print(f"missing preview: {args.preview}", file=sys.stderr)
        return 2

    prep = prep_from_preview(args.preview)
    args.prep_out.parent.mkdir(parents=True, exist_ok=True)
    args.prep_out.write_text(prep, encoding="utf-8")

    records, report = ib.parse_book(
        prep, "kama-samuha", footnote_mode="prose",
    )

    raw_path = _JSONL / "kama-samuha.raw.jsonl"
    rep_path = _JSONL / "kama-samuha.report.json"
    aligned_path = _JSONL / "kama-samuha.jsonl"
    align_rep_path = _JSONL / "kama-samuha.alignment.json"
    _JSONL.mkdir(parents=True, exist_ok=True)

    with open(raw_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    rep_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Bump meta provenance for H2450 prose layer.
    meta_path = _HERE / "kama-samuha.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["provenance"] = (
        "А. Игнатьев (перев.). Кама-самуха (архив переводчика). "
        "H2415 remainder verses + H2450 prose commentary apparatus "
        "(--footnote-mode prose: N. notes, link note#=verse#). "
        "Ingest via h2450_prose_commentary_pilot.py → "
        "ignatiev_book_to_canonical.py → align_sanskrit.py (ru_only) → "
        "build_corpus_html.py."
    )
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            str(_HERE / "align_sanskrit.py"),
            "--ru", str(raw_path),
            "--out", str(aligned_path),
            "--report", str(align_rep_path),
        ],
        check=True,
        cwd=str(_REPO),
    )

    rt = None
    if not args.skip_html:
        subprocess.run(
            [
                sys.executable,
                str(_HERE / "build_corpus_html.py"),
                "--jsonl", str(aligned_path),
                "--report", str(rep_path),
                "--meta", str(meta_path),
                "--data-dir", str(_DATA),
                "--data-txt", str(_DATA_TXT),
                "--split", "none",
                "--slug", "kama-samuha",
            ],
            check=True,
            cwd=str(_REPO),
        )
        rt = roundtrip_check("kama-samuha")

    comms = [r for r in records if str(r.get("seg", "")).startswith("comm")]
    sample = []
    for r in comms[:3]:
        sample.append({
            "passage": r["passage"],
            "fn": r.get("fn"),
            "annotates": r.get("annotates"),
            "text_head": (r.get("text") or "")[:160],
        })
    for r in comms:
        if r.get("fn") == 109:
            sample.append({
                "passage": r["passage"],
                "fn": 109,
                "annotates": r.get("annotates"),
                "text_head": (r.get("text") or "")[:200],
                "role": "handoff_example",
            })
            break

    pilot = {
        "handoff": "H2450",
        "executor": "Grok 4.5 (grok-4.5)",
        "work": "kama-samuha",
        "footnote_mode": report.get("footnote_mode"),
        "link_rule": report.get("prose_link_rule"),
        "chapters": report.get("chapters"),
        "verse_count": report.get("verse_count"),
        "comment_count": report.get("comment_count"),
        "total_endnotes": report.get("total_endnotes"),
        "prose_notes_linked": report.get("prose_notes_linked"),
        "prose_notes_unlinked": report.get("prose_notes_unlinked"),
        "unlinked_prose_notes": report.get("unlinked_prose_notes") or [],
        "prose_note_stats": report.get("prose_note_stats") or {},
        "verse_gaps": report.get("verse_gaps") or [],
        "h2415_verse_baseline": 685,
        "verse_count_stable": report.get("verse_count") == 685,
        "sample_comments": sample,
        "roundtrip": rt,
        "generalization_plan": [
            "Other H2415 remainder works: re-parse with footnote-mode auto "
            "(upgrades when bracket empty + prose density >=3).",
            "Kādambara: different note grammar (N(pada). + OLE hyperlink noise) "
            "— separate residual, not this prose mode.",
            "MBH 16–18 shared endnote volume: census prose vs bracket before "
            "bulk re-emit.",
            "Do not re-baseline Wave A–D glued-digit/bracket works unless the "
            "same N. grammar appears free.",
        ],
    }
    pilot_path = _JSONL / "h2450_kama_samuha_prose_pilot.json"
    pilot_path.write_text(
        json.dumps(pilot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"kama-samuha: {report.get('verse_count')} verses, "
        f"{report.get('comment_count')} comments "
        f"(linked={report.get('prose_notes_linked')}, "
        f"unlinked={report.get('prose_notes_unlinked')}) "
        f"mode={report.get('footnote_mode')}"
    )
    if rt:
        print(
            f"RT verses={rt.get('verses', {}).get('rate_pct')}% "
            f"comments={rt.get('comments', {}).get('rate_pct')}%"
        )
    print(f"pilot -> {pilot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
