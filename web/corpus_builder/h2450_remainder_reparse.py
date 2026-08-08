#!/usr/bin/env python3
"""H2450 residual reparse — all H2415 remainder works with footnote-mode auto.

Uses local ``_h2415_preview`` extracts when the gitignored archive is absent.
For each work: prep (same cuts as h2415_remainder_ingest) → parse(auto) →
ru_only align → HTML emit (unless --dry-run) → summary row.

Expected modes:
  kama-samuha          → prose (already shipped H2450)
  MBH book 18          → bracket-free ([N] free text + inline [N])
  yoni-puja-texts      → bracket-free
  kadambara            → residue (N(pada). grammar; not this front-end)
  bhagavati            → residue (bullet ПРИМЕЧАНИЯ, not numbered)
  MBH books 16–17      → no note block attached (shared notes on book 18)
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
_PREP = _HERE / "_h2415_prep"
_PREVIEW = Path(r"C:\Users\user\Documents\GitHub\SamudraManthanam\_h2415_preview")
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))

import ignatiev_book_to_canonical as ib  # noqa: E402
import h2415_remainder_ingest as h2415  # noqa: E402


def prep_from_preview() -> list[tuple[str, Path, dict]]:
    """Build prep texts from H2415 preview dumps (no archive required)."""
    _PREP.mkdir(parents=True, exist_ok=True)
    out: list[tuple[str, Path, dict]] = []

    # --- kama ---
    kama = (_PREVIEW / "kama-samuha.txt").read_text(encoding="utf-8")
    lines = kama.replace("\x0c", "\n").split("\n")
    idxs = [i for i, ln in enumerate(lines) if ln.strip() == "КАМА-САМУХА"]
    start = idxs[1] if len(idxs) > 1 else (idxs[0] if idxs else 0)
    p = _PREP / "kama-samuha.prep.txt"
    p.write_text("Глава первая\n" + "\n".join(lines[start:]), encoding="utf-8")
    out.append((
        "kama-samuha", p,
        h2415._meta_base(
            "kama-samuha",
            "Кама-самуха; А. Игнатьев",
            "Kāma-samūha (Ignatiev)",
            "Кама-самуха",
            "H2450 reparse (auto); prose commentary apparatus.",
        ),
    ))

    # --- kadambara ---
    kad = (_PREVIEW / "kadambara.txt").read_text(encoding="utf-8")
    # strip HYPERLINK debris like prep_kadambara
    kad = re.sub(
        r"HYPERLINK\s+\"[^\"]*\"(?:\s*\\\\o\s+\"[^\"]*\")?", "", kad,
    )
    kl = kad.split("\n")
    titles = [
        i for i, ln in enumerate(kl)
        if ln.strip().upper().replace("Ё", "Е") == "КАДАМБАРА-СВИКАРАНА-КАРИКА"
    ]
    first_v1 = next(
        (i for i, ln in enumerate(kl) if re.search(r"\(\s*1\s*\)\s*$", ln)),
        None,
    )
    if first_v1 is not None and titles:
        before = [i for i in titles if i < first_v1]
        kstart = before[-1] if before else titles[-1]
    elif titles:
        kstart = titles[-1]
    else:
        kstart = 0
    p = _PREP / "kadambara-svikarana-karika.prep.txt"
    p.write_text("Глава первая\n" + "\n".join(kl[kstart:]), encoding="utf-8")
    out.append((
        "kadambara-svikarana-karika", p,
        h2415._meta_base(
            "kadambara-svikarana-karika",
            "Кадамбара-свикарана-карика; А. Игнатьев",
            "Kādambara-svīkaraṇa-kārikā (Ignatiev)",
            "Кадамбара-свикарана-карика",
            "H2450 reparse (auto); N(pada). residue expected.",
        ),
    ))

    # --- MBH three books from mbh.txt ---
    mbh = (_PREVIEW / "mbh.txt").read_text(encoding="utf-8")
    ml = mbh.replace("\x0c", "\n").split("\n")
    book_re = re.compile(
        r"^\s*КНИГА\s+(ШЕСТНАДЦАТАЯ|СЕМНАДЦАТАЯ|ВОСЕМНАДЦАТАЯ)\.?\s*$",
        re.IGNORECASE,
    )
    starts: list[tuple[int, str]] = []
    for i, ln in enumerate(ml):
        m = book_re.match(ln)
        if m:
            starts.append((i, m.group(1).lower().replace("ё", "е")))
    name_map = {
        "шестнадцатая": (
            "mahabharata-mausalaparva-ignatiev",
            "Махабхарата XVI Маусала-парва; А. Игнатьев",
            "Mahābhārata XVI Mausala-parva (Ignatiev)",
            "Махабхарата XVI. Маусала-парва",
        ),
        "семнадцатая": (
            "mahabharata-mahaprasthanikaparva-ignatiev",
            "Махабхарата XVII Махапрастханика-парва; А. Игнатьев",
            "Mahābhārata XVII Mahāprasthānika-parva (Ignatiev)",
            "Махабхарата XVII. Махапрастханика-парва",
        ),
        "восемнадцатая": (
            "mahabharata-svargarohanikaparva-ignatiev",
            "Махабхарата XVIII Сварга-арохана-парва; А. Игнатьев",
            "Mahābhārata XVIII Svargārohaṇa-parva (Ignatiev)",
            "Махабхарата XVIII. Сварга-арохана-парва",
        ),
    }
    # Shared free-form [N] endnotes sit after book 18; books 16–17 also
    # carry inline [N] refs (1..~211). Attach the same note block to every
    # book so first-use linking can fire (H2415 left notes only on book 18).
    notes_i = next(
        (
            i for i, ln in enumerate(ml)
            if re.match(
                r"^\s*(?:\[\d+\]\s*)?(Комментари[йи]|Примечани[яе])\s*$",
                ln,
                re.IGNORECASE,
            )
        ),
        None,
    )
    notes_tail = ml[notes_i:] if notes_i is not None else []
    for bi, (bstart, key) in enumerate(starts):
        end = starts[bi + 1][0] if bi + 1 < len(starts) else len(ml)
        if bi < len(starts) - 1:
            chunk = list(ml[bstart:end])
            if notes_tail:
                chunk.extend([""] + notes_tail)
        else:
            chunk = list(ml[bstart:])  # already includes notes through EOF
        slug, title_ru, title_en, title_display = name_map[key]
        p = _PREP / f"{slug}.prep.txt"
        p.write_text("\n".join(chunk), encoding="utf-8")
        out.append((
            slug, p,
            h2415._meta_base(
                slug, title_ru, title_en, title_display,
                "H2450 reparse (auto); shared free [N] notes attached to "
                "each of books 16–18 for inline linking.",
            ),
        ))

    # --- yoni ---
    yoni = (_PREVIEW / "yoni-puja.txt").read_text(encoding="utf-8")
    p = _PREP / "yoni-puja-texts.prep.txt"
    p.write_text("Глава первая\n" + yoni, encoding="utf-8")
    out.append((
        "yoni-puja-texts", p,
        h2415._meta_base(
            "yoni-puja-texts",
            "Тексты по йони-пудже; А. Игнатьев",
            "Yoni-pūjā texts (Ignatiev)",
            "Тексты по йони-пудже",
            "H2450 reparse (auto); free [N] notes expected.",
        ),
    ))

    # --- bhagavati ---
    bha = (_PREVIEW / "bhagavati-manasa.txt").read_text(encoding="utf-8")
    bi = bha.find("ГИМН МЫСЛЕННОГО")
    if bi < 0:
        bi = bha.find("ГИМН")
    p = _PREP / "bhagavati-manasa-puja-stotra.prep.txt"
    p.write_text(
        "Глава первая\n" + (bha[bi:] if bi >= 0 else bha),
        encoding="utf-8",
    )
    out.append((
        "bhagavati-manasa-puja-stotra", p,
        h2415._meta_base(
            "bhagavati-manasa-puja-stotra",
            "Шри-Бхагавати-манаса-пуджа-стотра; А. Игнатьев",
            "Śrī-Bhagavatī-mānasa-pūjā-stotra (Ignatiev)",
            "Бхагавати-манаса-пуджа-стотра",
            "H2450 reparse (auto); bullet ПРИМЕЧАНИЯ residue expected.",
        ),
    ))
    return out


def run_one(
    slug: str,
    src: Path,
    meta: dict,
    *,
    dry_run: bool,
    footnote_mode: str,
) -> dict:
    text = src.read_text(encoding="utf-8")
    records, report = ib.parse_book(
        text, slug, footnote_mode=footnote_mode,
    )
    raw_path = _JSONL / f"{slug}.raw.jsonl"
    rep_path = _JSONL / f"{slug}.report.json"
    aligned_path = _JSONL / f"{slug}.jsonl"
    align_rep_path = _JSONL / f"{slug}.alignment.json"
    meta_path = _HERE / f"{slug}.meta.json"

    h2415._write_jsonl(raw_path, records)
    rep_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    # preserve existing rights/provenance if present; bump reparse note
    if meta_path.is_file():
        old = json.loads(meta_path.read_text(encoding="utf-8"))
        old["provenance"] = (
            (old.get("provenance") or "")
            + f" H2450 remainder reparse footnote_mode={report.get('footnote_mode')} "
            f"comments={report.get('comment_count')}."
        ).strip()
        meta = old
    h2415._write_meta(meta_path, meta)

    subprocess.run(
        [
            sys.executable, str(_HERE / "align_sanskrit.py"),
            "--ru", str(raw_path),
            "--out", str(aligned_path),
            "--report", str(align_rep_path),
        ],
        check=True,
        cwd=str(_REPO),
    )

    row = {
        "slug": slug,
        "footnote_mode": report.get("footnote_mode"),
        "footnote_mode_requested": report.get("footnote_mode_requested"),
        "chapters": report.get("chapters"),
        "verse_count": report.get("verse_count"),
        "comment_count": report.get("comment_count"),
        "total_endnotes": report.get("total_endnotes"),
        "prose_notes_linked": report.get("prose_notes_linked"),
        "prose_notes_unlinked": report.get("prose_notes_unlinked"),
        "bracket_free_notes_linked": report.get("bracket_free_notes_linked"),
        "bracket_free_notes_unlinked": report.get("bracket_free_notes_unlinked"),
        "unlinked_prose_notes": report.get("unlinked_prose_notes") or [],
        "unlinked_bracket_free_notes": report.get(
            "unlinked_bracket_free_notes"
        ) or [],
    }

    if dry_run:
        row["html_emitted"] = False
        return row

    subprocess.run(
        [
            sys.executable, str(_HERE / "build_corpus_html.py"),
            "--jsonl", str(aligned_path),
            "--report", str(rep_path),
            "--meta", str(meta_path),
            "--data-dir", str(_DATA),
            "--data-txt", str(_DATA_TXT),
            "--split", "none",
            "--slug", slug,
        ],
        check=True,
        cwd=str(_REPO),
    )
    row["html_emitted"] = True
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--footnote-mode", default="auto",
        choices=("auto", "bracket", "prose", "bracket-free"),
    )
    ap.add_argument(
        "--only",
        nargs="*",
        help="optional slug filter",
    )
    args = ap.parse_args()

    if not _PREVIEW.is_dir():
        print(f"missing preview dir: {_PREVIEW}", file=sys.stderr)
        return 2

    works = prep_from_preview()
    if args.only:
        want = set(args.only)
        works = [w for w in works if w[0] in want]

    summary = {
        "wave": "H2450-remainder-reparse",
        "footnote_mode_requested": args.footnote_mode,
        "works": [],
    }
    for slug, path, meta in works:
        print(f"--- {slug} ---")
        row = run_one(
            slug, path, meta,
            dry_run=args.dry_run,
            footnote_mode=args.footnote_mode,
        )
        summary["works"].append(row)
        print(
            f"  mode={row['footnote_mode']} verses={row['verse_count']} "
            f"comments={row['comment_count']} "
            f"endnotes={row['total_endnotes']}"
        )

    out = _JSONL / "h2450_remainder_reparse_summary.json"
    out.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"summary -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
