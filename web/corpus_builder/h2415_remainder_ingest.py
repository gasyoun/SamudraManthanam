#!/usr/bin/env python3
"""H2415 — Ignatiev archive remainder ingest (Kāma-samūha, Kādambara, MBH 16–18, Прочее).

Prepares sources that lack a ``Глава <ordinal>`` open (or restart chapter
numbers per book) so ``ignatiev_book_to_canonical.parse_book`` does not cut
the body at early ALL-CAPS back-matter / ToC lines, then runs the standard
pipeline: parse → ru_only align → HTML emit → data.txt append.

Non-goals: invent SA alignment; re-baseline already-glued PDF works.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import subprocess

import ignatiev_book_to_canonical as ib  # noqa: E402

# Default archive root (gitignored); override with --archive-root.
_DEFAULT_ARCH = (
    Path(r"C:\Users\user\Documents\GitHub\SamudraManthanam")
    / "archive_ignatiev_2026"
    / "Переводы с санскрита"
)
_REPO = _HERE.parent.parent  # SamudraManthanam worktree root
_JSONL = _HERE / "jsonl"
_DATA = _REPO / "Index" / "lib" / "x86_64-win64" / "Data"
_DATA_TXT = _REPO / "Index" / "lib" / "x86_64-win64" / "Programdata" / "data.txt"
_PREP = _HERE / "_h2415_prep"
_RIGHTS = (
    "cleared 15-07-2026 — translator А. Игнатьев granted full/exclusive/"
    "worldwide/perpetual redistribution + derivative-work rights to "
    '"all my works ... whether published or unpublished" to MG/samskrtam.ru '
    "via email (unsigned, sender not independently verified; MG accepted at "
    "face value). Full text: "
    "https://github.com/gasyoun/Uprava/blob/main/RIGHTS_GRANT_IGNATJEV_DBHP_2026H2.md"
)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _write_meta(path: Path, meta: dict) -> None:
    path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _meta_base(
    slug: str,
    title_ru: str,
    title_en: str,
    title_display: str,
    provenance: str,
) -> dict:
    return {
        "schema_version": 1,
        "slug": slug,
        "title_ru": title_ru,
        "title_display": title_display,
        "title_en": title_en,
        "credit": "А. Игнатьев",
        "credit_role": "Перевод с санскрита",
        "imprint": "неопубликованный перевод",
        "publisher": None,
        "year": None,
        "scripts": ["cyrillic"],
        "structure": "verse",
        "needs_review": True,
        "provenance": provenance,
        "rights": _RIGHTS,
    }


def prep_kama_samuha(arch: Path) -> Path:
    """Drop ToC/preface; inject synthetic ch.1 so back-matter scan works."""
    text = ib.extract_text(arch / "Кама-самуха" / "Кама-самуха.docx")
    lines = text.replace("\x0c", "\n").split("\n")
    idxs = [i for i, ln in enumerate(lines) if ln.strip() == "КАМА-САМУХА"]
    start = idxs[1] if len(idxs) > 1 else (idxs[0] if idxs else 0)
    prep = "Глава первая\n" + "\n".join(lines[start:])
    out = _PREP / "kama-samuha.prep.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(prep, encoding="utf-8")
    return out


def prep_kadambara(arch: Path) -> Path:
    """OLE .doc extract → strip binary head + start at translation body.

    The .doc carries a long preface whose ALL-CAPS ``ПРЕДИСЛОВИЕ`` would be
    read as back-matter if a synthetic chapter were planted at the file head.
    Start at the second title line (after preface) immediately before verse (1).
    """
    raw = ib.extract_text(
        arch / "Кадамбара-свикарана-карика" / "Кадамбара-свикарана-карика.doc"
    )
    idx = raw.find("КАДАМБАРА-СВИКАРАНА-КАРИКА")
    clean = raw[idx:] if idx >= 0 else raw
    # OLE/Word field noise
    clean = re.sub(
        r"HYPERLINK\s+\"[^\"]*\"(?:\s*\\\\o\s+\"[^\"]*\")?",
        "",
        clean,
    )
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    lines = clean.split("\n")
    title_idxs = [
        i
        for i, ln in enumerate(lines)
        if ln.strip().upper().replace("Ё", "Е") == "КАДАМБАРА-СВИКАРАНА-КАРИКА"
    ]
    # Prefer the title that immediately precedes the first trailing "(1)"
    first_v1 = next(
        (
            i
            for i, ln in enumerate(lines)
            if re.search(r"\(\s*1\s*\)\s*$", ln)
        ),
        None,
    )
    start = 0
    if first_v1 is not None and title_idxs:
        before = [i for i in title_idxs if i < first_v1]
        start = before[-1] if before else title_idxs[-1]
    elif len(title_idxs) > 1:
        start = title_idxs[-1]
    elif title_idxs:
        start = title_idxs[0]
    body = "\n".join(lines[start:])
    prep = "Глава первая\n" + body
    out = _PREP / "kadambara-svikarana-karika.prep.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(prep, encoding="utf-8")
    return out


def prep_mbh_books(arch: Path) -> list[tuple[str, Path, dict]]:
    """Split the three final books into separate works (ch numbers restart)."""
    text = ib.extract_text(
        arch / "Махабхарата" / "Махабхарата Три заключительные книги.docx"
    )
    lines = text.replace("\x0c", "\n").split("\n")
    book_re = re.compile(
        r"^\s*КНИГА\s+(ШЕСТНАДЦАТАЯ|СЕМНАДЦАТАЯ|ВОСЕМНАДЦАТАЯ)\.?\s*$",
        re.IGNORECASE,
    )
    starts: list[tuple[int, str]] = []
    for i, ln in enumerate(lines):
        m = book_re.match(ln)
        if m:
            starts.append((i, m.group(1).lower().replace("ё", "е")))

    # Shared endnotes for the whole volume often sit after book 18.
    # Find first КОММЕНТАРИЙ / ПРИМЕЧАНИЯ after last book start.
    notes_idx = None
    if starts:
        for i in range(starts[-1][0], len(lines)):
            if re.match(
                r"^\s*(Комментари[йи]|Примечани[яе])\s*$",
                lines[i],
                re.IGNORECASE,
            ):
                notes_idx = i
                break

    name_map = {
        "шестнадцатая": (
            "mahabharata-mausalaparva-ignatiev",
            "Махабхарата XVI Маусала-парва; А. Игнатьев",
            "Mahābhārata XVI Mausala-parva (Ignatiev)",
            "Махабхарата XVI. Маусала-парва",
            "PARTIAL: book 16 only (from «Три заключительные книги»)",
        ),
        "семнадцатая": (
            "mahabharata-mahaprasthanikaparva-ignatiev",
            "Махабхарата XVII Махапрастханика-парва; А. Игнатьев",
            "Mahābhārata XVII Mahāprasthānika-parva (Ignatiev)",
            "Махабхарата XVII. Махапрастханика-парва",
            "PARTIAL: book 17 only (from «Три заключительные книги»)",
        ),
        "восемнадцатая": (
            "mahabharata-svargarohanikaparva-ignatiev",
            "Махабхарата XVIII Сварга-арохана-парва; А. Игнатьев",
            "Mahābhārata XVIII Svargārohaṇa-parva (Ignatiev)",
            "Махабхарата XVIII. Сварга-арохана-парва",
            "PARTIAL: book 18 only (from «Три заключительные книги»)",
        ),
    }
    out: list[tuple[str, Path, dict]] = []
    for bi, (start, key) in enumerate(starts):
        end = starts[bi + 1][0] if bi + 1 < len(starts) else len(lines)
        # Attach shared endnotes only to the last book so earlier books
        # do not swallow later parvas; earlier books have no endnotes.
        if bi == len(starts) - 1 and notes_idx is not None and notes_idx < end:
            # notes already inside end
            pass
        elif bi < len(starts) - 1 and notes_idx is not None:
            # stop before next book (already end)
            pass
        chunk_lines = list(lines[start:end])
        # Last book: if notes sit after end (shouldn't), append them
        if bi == len(starts) - 1 and notes_idx is not None and notes_idx >= end:
            chunk_lines = list(lines[start:])
        prep = "\n".join(chunk_lines)
        slug, title_ru, title_en, title_display, extent = name_map[key]
        path = _PREP / f"{slug}.prep.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(prep, encoding="utf-8")
        meta = _meta_base(
            slug,
            title_ru,
            title_en,
            title_display,
            (
                f"А. Игнатьев (перев.). Махабхарата — {extent}. "
                f"Source: «Махабхарата Три заключительные книги.docx». "
                f"Distinct from Vasilkov/Neveleva 2005 editions already in "
                f"corpus (16–18_mahabharata-*.html). H2415. "
                f"Ingest via h2415_remainder_ingest.py → "
                f"ignatiev_book_to_canonical.py → align_sanskrit.py (ru_only) "
                f"→ build_corpus_html.py."
            ),
        )
        out.append((slug, path, meta))
    return out


def prep_yoni_puja(arch: Path) -> Path:
    text = ib.extract_text(arch / "Прочее" / "Тексты по йони-пудже.docx")
    prep = "Глава первая\n" + text
    out = _PREP / "yoni-puja-texts.prep.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(prep, encoding="utf-8")
    return out


def prep_bhagavati(arch: Path) -> Path:
    raw = ib.extract_text(
        arch / "Прочее" / "Шри-Бхагавати-манаса-пуджа-стотра.doc"
    )
    idx = raw.find("ГИМН МЫСЛЕННОГО")
    if idx < 0:
        idx = raw.find("ГИМН")
    clean = raw[idx:] if idx >= 0 else raw
    prep = "Глава первая\n" + clean
    out = _PREP / "bhagavati-manasa-puja-stotra.prep.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(prep, encoding="utf-8")
    return out


def run_one(
    slug: str,
    src: Path,
    meta: dict,
    *,
    dry_run: bool = False,
) -> dict:
    if src.suffix.lower() == ".txt":
        text = src.read_text(encoding="utf-8")
    else:
        text = ib.extract_text(src)
    records, report = ib.parse_book(text, slug)
    raw_path = _JSONL / f"{slug}.raw.jsonl"
    rep_path = _JSONL / f"{slug}.report.json"
    aligned_path = _JSONL / f"{slug}.jsonl"
    align_rep_path = _JSONL / f"{slug}.alignment.json"
    meta_path = _HERE / f"{slug}.meta.json"

    _write_jsonl(raw_path, records)
    rep_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_meta(meta_path, meta)

    # ru_only align via CLI (no --sa)
    subprocess.run(
        [
            sys.executable,
            str(_HERE / "align_sanskrit.py"),
            "--ru",
            str(raw_path),
            "--out",
            str(aligned_path),
            "--report",
            str(align_rep_path),
        ],
        check=True,
        cwd=str(_REPO),
    )

    summary = {
        "slug": slug,
        "src": str(src),
        "chapters": report.get("chapters"),
        "verse_count": report.get("verse_count"),
        "comment_count": report.get("comment_count"),
        "chapter_numbers": report.get("chapter_numbers"),
        "prose_paragraph_split_chapters": report.get(
            "prose_paragraph_split_chapters"
        ),
        "alignment": "ru_only",
        "raw_jsonl": str(raw_path.relative_to(_REPO)).replace("\\", "/"),
        "aligned_jsonl": str(aligned_path.relative_to(_REPO)).replace("\\", "/"),
    }

    if dry_run:
        summary["html_emitted"] = False
        return summary

    subprocess.run(
        [
            sys.executable,
            str(_HERE / "build_corpus_html.py"),
            "--jsonl",
            str(aligned_path),
            "--report",
            str(rep_path),
            "--meta",
            str(meta_path),
            "--data-dir",
            str(_DATA),
            "--data-txt",
            str(_DATA_TXT),
            "--split",
            "none",
            "--slug",
            slug,
        ],
        check=True,
        cwd=str(_REPO),
    )
    summary["html_emitted"] = True
    summary["html"] = f"{slug}.html"
    return summary


def roundtrip_check(slug: str) -> dict:
    """HTML → canonical RU text match rate (Wave D gate)."""
    import html_to_canonical as h2c

    html_path = _DATA / f"{slug}.html"
    src_jsonl = _JSONL / f"{slug}.jsonl"
    meta_path = _HERE / f"{slug}.meta.json"
    if not html_path.exists() or not src_jsonl.exists():
        return {"slug": slug, "error": "missing html or jsonl"}

    src_texts: dict[str, str] = {}
    with open(src_jsonl, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("deleted"):
                continue
            if rec.get("seg") not in (None, "ru"):
                continue
            passage = rec.get("passage")
            text = rec.get("text")
            if passage and text is not None:
                src_texts[passage] = re.sub(r"\s+", " ", text).strip()

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    rt_dir = _JSONL / "_rt_tmp"
    rt_dir.mkdir(parents=True, exist_ok=True)
    report_data: dict = {}
    try:
        h2c.convert_source(
            f"{slug}.html",
            meta,
            _DATA,
            rt_dir,
            report_data,
        )
    except Exception as e:
        return {"slug": slug, "error": f"rt convert failed: {e}"}

    rt_jsonl = rt_dir / f"{slug}.jsonl"
    rt_texts: dict[str, str] = {}
    if rt_jsonl.exists():
        with open(rt_jsonl, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("seg") not in (None, "ru"):
                    continue
                passage = rec.get("passage")
                text = rec.get("text")
                if passage and text is not None:
                    rt_texts[passage] = re.sub(r"\s+", " ", text).strip()

    matched = 0
    mismatched = 0
    missing = 0
    for p, t in src_texts.items():
        if p not in rt_texts:
            missing += 1
        elif rt_texts[p] == t:
            matched += 1
        else:
            mismatched += 1
    total = len(src_texts)
    rate = (matched / total * 100.0) if total else 0.0
    return {
        "slug": slug,
        "src_verses": total,
        "rt_verses": len(rt_texts),
        "matched": matched,
        "mismatched": mismatched,
        "missing_in_rt": missing,
        "rate_pct": round(rate, 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--archive-root",
        type=Path,
        default=_DEFAULT_ARCH,
        help="Path to archive_ignatiev_2026/Переводы с санскрита",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse+align only; do not emit HTML / touch data.txt",
    )
    ap.add_argument(
        "--skip-rt",
        action="store_true",
        help="Skip HTML round-trip gate",
    )
    ap.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Optional slug filter",
    )
    args = ap.parse_args()
    arch: Path = args.archive_root
    if not arch.is_dir():
        print(f"archive root missing: {arch}", file=sys.stderr)
        return 2

    jobs: list[tuple[str, Path, dict]] = []

    # 1 Kāma-samūha
    kama_src = prep_kama_samuha(arch)
    jobs.append(
        (
            "kama-samuha",
            kama_src,
            _meta_base(
                "kama-samuha",
                "Кама-самуха; А. Игнатьев",
                "Kāma-samūha (Ignatiev)",
                "Кама-самуха",
                (
                    "А. Игнатьев (перев.). Кама-самуха (архив переводчика). "
                    "H2415 remainder: full translation (no chapter heads — "
                    "synthetic Глава первая after preface strip). "
                    "Ingest via h2415_remainder_ingest.py → "
                    "ignatiev_book_to_canonical.py → align_sanskrit.py "
                    "(ru_only) → build_corpus_html.py."
                ),
            ),
        )
    )

    # 2 Kādambara
    kad_src = prep_kadambara(arch)
    jobs.append(
        (
            "kadambara-svikarana-karika",
            kad_src,
            _meta_base(
                "kadambara-svikarana-karika",
                "Кадамбара-свикарана-карика; А. Игнатьев",
                "Kādambara-svīkaraṇa-kārikā (Ignatiev)",
                "Кадамбара-свикарана-карика",
                (
                    "А. Игнатьев (перев.). Кадамбара-свикарана-карика "
                    "(архив переводчика, .doc OLE). H2415 remainder: full "
                    "short kāmaśāstra (≈132 ślokas); synthetic ch.1. "
                    "Ingest via h2415_remainder_ingest.py → "
                    "ignatiev_book_to_canonical.py → align_sanskrit.py "
                    "(ru_only) → build_corpus_html.py."
                ),
            ),
        )
    )

    # 3 MBH three books
    jobs.extend(prep_mbh_books(arch))

    # 4 Прочее
    jobs.append(
        (
            "yoni-puja-texts",
            prep_yoni_puja(arch),
            _meta_base(
                "yoni-puja-texts",
                "Тексты для йони-пуджи; А. Игнатьев",
                "Yoni-pūjā texts (Ignatiev miscellany)",
                "Тексты для йони-пуджи",
                (
                    "А. Игнатьев (перев.). Тексты по йони-пудже.docx "
                    "(Прочее). H2415 remainder: short liturgical miscellany "
                    "(dhyāna, nyāsa, stotra, kavaca); synthetic ch.1; "
                    "ru_only. Ingest via h2415_remainder_ingest.py."
                ),
            ),
        )
    )
    jobs.append(
        (
            "bhagavati-manasa-puja-stotra",
            prep_bhagavati(arch),
            _meta_base(
                "bhagavati-manasa-puja-stotra",
                "Шри-Бхагавати-манаса-пуджа-стотра; А. Игнатьев",
                "Śrī-Bhagavatī-mānasa-pūjā-stotra (Ignatiev; Śaṅkara)",
                "Гимн мысленного поклонения Бхагавати",
                (
                    "А. Игнатьев (перев.). Шри-Бхагавати-манаса-пуджа-стотра.doc "
                    "(Прочее; attrib. Śaṅkara). H2415 remainder: short stotra "
                    "with (N) verse markers; synthetic ch.1; ru_only. "
                    "Ingest via h2415_remainder_ingest.py."
                ),
            ),
        )
    )

    if args.only:
        only = set(args.only)
        jobs = [j for j in jobs if j[0] in only]

    summaries = []
    for slug, src, meta in jobs:
        print(f"--- ingest {slug} from {src.name} ---")
        s = run_one(slug, src, meta, dry_run=args.dry_run)
        if not args.dry_run and not args.skip_rt:
            rt = roundtrip_check(slug)
            s["roundtrip"] = rt
            print(
                f"  verses={s['verse_count']} ch={s['chapters']} "
                f"RT={rt.get('rate_pct')}% "
                f"({rt.get('matched')}/{rt.get('src_verses')})"
            )
        else:
            print(f"  verses={s['verse_count']} ch={s['chapters']}")
        summaries.append(s)

    out_sum = _JSONL / "wave_h2415_remainder_summary.json"
    out_sum.write_text(
        json.dumps(
            {
                "wave": "H2415-remainder",
                "handoff": "H2415",
                "works": summaries,
                "gate": "html→jsonl text match ≥99% or documented residue",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out_sum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
