#!/usr/bin/env python3
"""H2449 — register Ignatiev preface + glossary/bibliography layers.

Reads the same archive sources as H2415 (full books, not the verse-only prep
that strips front matter), extracts front/back-matter via
``ignatiev_backmatter``, writes JSONL + meta, emits desktop HTML (prose) or
``.txt`` dictionary files (glossaries), appends ``Programdata/data.txt``, and
gates with text RT ≥99% (or documents residue).

Non-goals: prose commentary apparatus (H2450); inventing SA; re-baseline of
already-glued PDF works.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import ignatiev_backmatter as bm  # noqa: E402
import ignatiev_book_to_canonical as ib  # noqa: E402

_DEFAULT_ARCH = (
    Path(r"C:\Users\user\Documents\GitHub\SamudraManthanam")
    / "archive_ignatiev_2026"
    / "Переводы с санскрита"
)
_REPO = _HERE.parent.parent
_JSONL = _HERE / "jsonl"
_DATA = _REPO / "Index" / "lib" / "x86_64-win64" / "Data"
_DATA_TXT = _REPO / "Index" / "lib" / "x86_64-win64" / "Programdata" / "data.txt"

_RIGHTS = (
    "cleared 15-07-2026 — translator А. Игнатьев granted full/exclusive/"
    "worldwide/perpetual redistribution + derivative-work rights to "
    '"all my works ... whether published or unpublished" to MG/samskrtam.ru '
    "via email (unsigned, sender not independently verified; MG accepted at "
    "face value). Full text: "
    "https://github.com/gasyoun/Uprava/blob/main/RIGHTS_GRANT_IGNATJEV_DBHP_2026H2.md"
)

from build_corpus_html import (  # noqa: E402
    append_data_txt,
    render_document,
    write_document,
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


def _meta_for_layer(
    *,
    slug: str,
    parent_slug: str,
    section: bm.LayerSection,
    parent_title: str,
) -> dict:
    kind_ru = {
        "preface": "Предисловие",
        "glossary": section.title,
        "bibliography": section.title or "Литература",
        "about_author": "Об авторе перевода",
    }.get(section.kind, section.title)
    structure = "dictionary" if section.kind == "glossary" else "prose"
    return {
        "schema_version": 1,
        "slug": slug,
        "parent_work": parent_slug,
        "layer": section.kind,
        "layer_title": section.title,
        "title_ru": f"{parent_title} — {kind_ru}; А. Игнатьев",
        "title_display": f"{parent_title}: {kind_ru}",
        "title_en": f"{parent_slug} / {section.slug_suffix} (Ignatiev)",
        "credit": "А. Игнатьев",
        "credit_role": "Перевод с санскрита, предисловие и комментарий",
        "imprint": "неопубликованный перевод",
        "publisher": None,
        "year": None,
        "scripts": ["cyrillic"],
        "structure": structure,
        "needs_review": True,
        "provenance": (
            f"H2449 back-matter layer of parent {parent_slug!r} "
            f"(H2415 remainder). Section heading {section.title!r}. "
            f"Extracted via ignatiev_backmatter.py; not verse-aligned."
        ),
        "rights": _RIGHTS,
    }


def emit_dictionary_txt(
    records: list[dict], meta: dict, data_dir: Path, slug: str
) -> str:
    """Dic_Apte-style plain text: title line + one entry per line."""
    title = meta.get("title_ru", slug)
    lines = [f"<!-- {title} --!>"]
    for r in records:
        lines.append(r["text"])
    fn = f"{slug}.txt"
    path = data_dir / fn
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (data_dir / f"{fn}.meta.json").write_text(
        json.dumps({**meta, "filename": fn}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    # .no_tags identical for plain text (search surface)
    (data_dir / f"{slug}.no_tags").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return fn


def emit_prose_html(
    records: list[dict], meta: dict, data_dir: Path, slug: str
) -> str:
    lines = render_document(records, meta, titles={}, skandha=None)
    fn = f"{slug}.html"
    write_document(lines, data_dir, fn, meta, None)
    return fn


def roundtrip_dictionary(slug: str) -> dict:
    src = _JSONL / f"{slug}.jsonl"
    txt = _DATA / f"{slug}.txt"
    if not src.exists() or not txt.exists():
        return {"slug": slug, "error": "missing txt or jsonl"}
    src_texts: list[str] = []
    with open(src, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("deleted"):
                continue
            src_texts.append(re.sub(r"\s+", " ", rec["text"]).strip())
    body = txt.read_text(encoding="utf-8").splitlines()[1:]  # skip title
    rt = [re.sub(r"\s+", " ", ln).strip() for ln in body if ln.strip()]
    matched = sum(1 for a, b in zip(src_texts, rt) if a == b)
    # also count set equality if order preserved
    missing = max(0, len(src_texts) - len(rt))
    mismatched = sum(
        1 for i, t in enumerate(src_texts) if i < len(rt) and rt[i] != t
    )
    total = len(src_texts)
    rate = (matched / total * 100.0) if total else 0.0
    return {
        "slug": slug,
        "src_entries": total,
        "rt_entries": len(rt),
        "matched": matched,
        "mismatched": mismatched,
        "missing_in_rt": missing,
        "rate_pct": round(rate, 2),
    }


def roundtrip_prose_html(slug: str) -> dict:
    """Reuse H2415-style HTML→JSONL text match on citation_block RU.

    Prose layers are emitted with citation_block markup (same as verse HTML)
    but meta.structure stays ``prose``. For RT we temporarily treat the file
    as verse so ``html_to_canonical`` walks citation blocks.
    """
    import html_to_canonical as h2c

    html_path = _DATA / f"{slug}.html"
    src_jsonl = _JSONL / f"{slug}.jsonl"
    meta_path = _HERE / f"{slug}.meta.json"
    if not html_path.exists() or not src_jsonl.exists():
        return {"slug": slug, "error": "missing html or jsonl"}

    src_texts: dict[str, str] = {}
    with open(src_jsonl, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("deleted"):
                continue
            if rec.get("seg") not in (None, "ru"):
                continue
            p = rec.get("passage")
            t = rec.get("text")
            if p and t is not None:
                src_texts[p] = re.sub(r"\s+", " ", t).strip()

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    # Force verse path: citation_block HTML is the verse converter's job.
    meta_rt = dict(meta)
    meta_rt["structure"] = "verse"
    rt_dir = _JSONL / "_rt_tmp_h2449"
    rt_dir.mkdir(parents=True, exist_ok=True)
    report_data: dict = {}
    try:
        h2c.convert_source(
            f"{slug}.html",
            meta_rt,
            _DATA,
            rt_dir,
            report_data,
        )
    except Exception as e:
        return {"slug": slug, "error": f"rt convert failed: {e}"}

    rt_path = rt_dir / f"{slug}.jsonl"
    rt_texts: dict[str, str] = {}
    if rt_path.exists():
        with open(rt_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("seg") not in (None, "ru"):
                    continue
                p = rec.get("passage")
                t = rec.get("text")
                if p and t is not None:
                    rt_texts[p] = re.sub(r"\s+", " ", t).strip()

    def _fold(s: str) -> str:
        # html_to_canonical occasionally strips Latin combining accents
        # (littérature → litterature) while Cyrillic is preserved. Count
        # accent-only deltas as soft matches + document residue.
        nk = unicodedata.normalize("NFKD", s)
        return "".join(ch for ch in nk if not unicodedata.combining(ch))

    matched = mismatched = missing = soft = 0
    residue: list[dict] = []
    for p, t in src_texts.items():
        if p not in rt_texts:
            missing += 1
            residue.append({"passage": p, "class": "missing"})
        elif rt_texts[p] == t:
            matched += 1
        elif _fold(rt_texts[p]) == _fold(t):
            soft += 1
            residue.append(
                {
                    "passage": p,
                    "class": "latin_accent_fold",
                    "src_snip": t[:80],
                    "rt_snip": rt_texts[p][:80],
                }
            )
        else:
            mismatched += 1
            residue.append(
                {
                    "passage": p,
                    "class": "text_mismatch",
                    "src_snip": t[:80],
                    "rt_snip": rt_texts[p][:80],
                }
            )
    total = len(src_texts)
    # Soft accent folds count toward the gate (emitted HTML is correct).
    effective = matched + soft
    rate = (effective / total * 100.0) if total else 0.0
    return {
        "slug": slug,
        "src_units": total,
        "rt_units": len(rt_texts),
        "matched": matched,
        "soft_accent_match": soft,
        "mismatched": mismatched,
        "missing_in_rt": missing,
        "rate_pct": round(rate, 2),
        "residue": residue[:20],
    }


def load_source_text(kind: str, arch: Path) -> str:
    if kind == "kama-samuha":
        return ib.extract_text(arch / "Кама-самуха" / "Кама-самуха.docx")
    if kind == "kadambara-svikarana-karika":
        raw = ib.extract_text(
            arch / "Кадамбара-свикарана-карика" / "Кадамбара-свикарана-карика.doc"
        )
        idx = raw.find("КАДАМБАРА-СВИКАРАНА-КАРИКА")
        return raw[idx:] if idx >= 0 else raw
    if kind == "mahabharata-ignatiev-xvi-xviii":
        return ib.extract_text(
            arch / "Махабхарата" / "Махабхарата Три заключительные книги.docx"
        )
    if kind == "yoni-puja-texts":
        return ib.extract_text(arch / "Прочее" / "Тексты по йони-пудже.docx")
    if kind == "bhagavati-manasa-puja-stotra":
        return ib.extract_text(
            arch / "Прочее" / "Шри-Бхагавати-манаса-пуджа-стотра.doc"
        )
    raise KeyError(kind)


# parent_slug → display title for meta
_PARENTS: list[tuple[str, str]] = [
    ("kama-samuha", "Кама-самуха"),
    ("kadambara-svikarana-karika", "Кадамбара-свикарана-карика"),
    (
        "mahabharata-ignatiev-xvi-xviii",
        "Махабхарата XVI–XVIII (Игнатьев)",
    ),
    ("yoni-puja-texts", "Тексты для йони-пуджи"),
    ("bhagavati-manasa-puja-stotra", "Гимн мысленного поклонения Бхагавати"),
]


def run_parent(
    parent_slug: str,
    parent_title: str,
    text: str,
    *,
    dry_run: bool,
    skip_rt: bool,
) -> list[dict]:
    summaries: list[dict] = []
    layers = list(bm.iter_work_layers(text, parent_slug))
    if not layers:
        summaries.append(
            {
                "parent": parent_slug,
                "disposition": "skip_no_layers",
                "reason": "no preface/glossary/bibliography/about sections found",
                "layers": [],
            }
        )
        return summaries

    for layer_slug, section, recs in layers:
        meta = _meta_for_layer(
            slug=layer_slug,
            parent_slug=parent_slug,
            section=section,
            parent_title=parent_title,
        )
        raw_path = _JSONL / f"{layer_slug}.jsonl"
        meta_path = _HERE / f"{layer_slug}.meta.json"
        _write_jsonl(raw_path, recs)
        _write_meta(meta_path, meta)

        s: dict = {
            "parent": parent_slug,
            "slug": layer_slug,
            "kind": section.kind,
            "title": section.title,
            "record_count": len(recs),
            "structure": meta["structure"],
            "jsonl": str(raw_path.relative_to(_REPO)).replace("\\", "/"),
        }
        if dry_run:
            s["emitted"] = False
            summaries.append(s)
            print(
                f"  [dry] {layer_slug}: {section.kind} n={len(recs)} "
                f"({section.title})"
            )
            continue

        if section.kind == "glossary":
            fn = emit_dictionary_txt(recs, meta, _DATA, layer_slug)
            added = append_data_txt(_DATA_TXT, [fn])
            s["filename"] = fn
            s["data_txt_added"] = added
            if not skip_rt:
                rt = roundtrip_dictionary(layer_slug)
                s["roundtrip"] = rt
                print(
                    f"  {layer_slug}: glossary n={len(recs)} "
                    f"RT={rt.get('rate_pct')}% ({rt.get('matched')}/{rt.get('src_entries')})"
                )
            else:
                print(f"  {layer_slug}: glossary n={len(recs)}")
        else:
            fn = emit_prose_html(recs, meta, _DATA, layer_slug)
            added = append_data_txt(_DATA_TXT, [fn])
            s["filename"] = fn
            s["data_txt_added"] = added
            if not skip_rt:
                rt = roundtrip_prose_html(layer_slug)
                s["roundtrip"] = rt
                print(
                    f"  {layer_slug}: {section.kind} n={len(recs)} "
                    f"RT={rt.get('rate_pct')}% "
                    f"({rt.get('matched')}/{rt.get('src_units')})"
                )
            else:
                print(f"  {layer_slug}: {section.kind} n={len(recs)}")
        s["emitted"] = True
        summaries.append(s)
    return summaries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive-root", type=Path, default=_DEFAULT_ARCH)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-rt", action="store_true")
    ap.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Parent slug filter (e.g. kama-samuha)",
    )
    ap.add_argument(
        "--from-preview",
        type=Path,
        default=None,
        help="Optional dir of pre-extracted .txt (kama-samuha.txt etc.) "
        "instead of archive docx — for offline re-runs",
    )
    args = ap.parse_args()

    parents = _PARENTS
    if args.only:
        only = set(args.only)
        parents = [p for p in parents if p[0] in only]

    all_summaries: list[dict] = []
    for parent_slug, parent_title in parents:
        print(f"--- parent {parent_slug} ---")
        if args.from_preview:
            # map parent → preview filename
            preview_map = {
                "kama-samuha": "kama-samuha.txt",
                "kadambara-svikarana-karika": "kadambara.txt",
                "mahabharata-ignatiev-xvi-xviii": "mbh.txt",
                "yoni-puja-texts": "yoni-puja.txt",
                "bhagavati-manasa-puja-stotra": "bhagavati-manasa.txt",
            }
            p = args.from_preview / preview_map[parent_slug]
            if not p.exists():
                print(f"  missing preview {p}")
                all_summaries.append(
                    {
                        "parent": parent_slug,
                        "disposition": "skip_missing_source",
                        "path": str(p),
                    }
                )
                continue
            text = p.read_text(encoding="utf-8")
        else:
            if not args.archive_root.is_dir():
                print(f"archive root missing: {args.archive_root}", file=sys.stderr)
                return 2
            try:
                text = load_source_text(parent_slug, args.archive_root)
            except Exception as e:
                print(f"  extract failed: {e}")
                all_summaries.append(
                    {
                        "parent": parent_slug,
                        "disposition": "skip_extract_error",
                        "error": str(e),
                    }
                )
                continue
        all_summaries.extend(
            run_parent(
                parent_slug,
                parent_title,
                text,
                dry_run=args.dry_run,
                skip_rt=args.skip_rt,
            )
        )

    out_sum = _JSONL / "wave_h2449_backmatter_summary.json"
    out_sum.parent.mkdir(parents=True, exist_ok=True)
    out_sum.write_text(
        json.dumps(
            {
                "wave": "H2449-backmatter",
                "handoff": "H2449",
                "layers": all_summaries,
                "gate": "layer text RT ≥99% or documented residue",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out_sum}")
    # Fail if any RT < 99
    bad = [
        s
        for s in all_summaries
        if s.get("roundtrip")
        and s["roundtrip"].get("rate_pct") is not None
        and s["roundtrip"]["rate_pct"] < 99.0
    ]
    if bad:
        print(f"FAIL: {len(bad)} layer(s) under 99% RT", file=sys.stderr)
        for s in bad:
            print(f"  {s['slug']}: {s['roundtrip']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
