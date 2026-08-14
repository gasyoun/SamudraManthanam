#!/usr/bin/env python3
"""H2738 — register Smirnov-series MBH articles + indexes as corpus layers.

Reads pre-extracted UTF-8 text (or extracts via pandoc from the Word dumps
parked in the gitignored archive). Emits JSONL + desktop HTML/txt, appends
``Programdata/data.txt``. Comments stay on the parva files.

Usage (from repo root):

    python web/corpus_builder/h2738_mbh_word_ingest.py \\
        --source-dir archive_anatoly_mbh_word
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent.parent
sys.path.insert(0, str(_HERE))

import mbh_word_layers as ml  # noqa: E402
from h2449_backmatter_ingest import (  # noqa: E402
    emit_dictionary_txt,
    roundtrip_dictionary,
    roundtrip_prose_html,
)
from build_corpus_html import append_data_txt  # noqa: E402

_JSONL = _HERE / "jsonl"
_DATA = _REPO / "Index" / "lib" / "x86_64-win64" / "Data"
_DATA_TXT = _REPO / "Index" / "lib" / "x86_64-win64" / "Programdata" / "data.txt"
_DEFAULT_SRC = _REPO / "archive_anatoly_mbh_word"

_RIGHTS = (
    "Printed Nauka / AN SSSR Mahābhārata volumes (Barannikov, Kalyanov, "
    "Erman, Vassilkov, Neveleva, Serebryany). Same edition family as the "
    "already-public parva HTML on samudra. Rights uncertainty is not a stop "
    "(Uprava STANDING_POLICY_RIGHTS_UNCERTAINTY_IS_NOT_A_STOP_2026). "
    "Source: Anatoliy Artemenko Drive «Для Пахтания»."
)

_INDEX_SLUGS = {
    "imen": (
        "mahabharata-ukazatel-imen",
        "Махабхарата — именной указатель (тома АН СССР / Наука)",
    ),
    "geo": (
        "mahabharata-ukazatel-geo",
        "Махабхарата — географический и этнический указатель",
    ),
    "predmet": (
        "mahabharata-ukazatel-predmet",
        "Махабхарата — предметно-терминологический указатель",
    ),
    "flora": (
        "mahabharata-ukazatel-flora",
        "Махабхарата — указатель флоры и фауны",
    ),
}

ARTICLES_SLUG = "mahabharata-stati"


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


def _read_text(source_dir: Path, *names: str) -> str:
    for name in names:
        p = source_dir / name
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"none of {names} in {source_dir} — extract the Word dump first"
    )


def articles_meta() -> dict:
    return {
        "schema_version": 1,
        "slug": ARTICLES_SLUG,
        "parent_work": "mahabharata",
        "layer": "article",
        "layer_title": "Статьи и предисловия томов",
        "title_ru": "Махабхарата — статьи и предисловия томов (АН СССР / Наука)",
        "title_display": "Махабхарата: статьи томов",
        "title_en": "Mahabharata volume articles (Smirnov series)",
        "credit": "Баранников, Кальянов, Эрман, Васильков, Невелева, Серебряный",
        "credit_role": "Предисловия, послесловия и статьи томов",
        "imprint": "АН СССР / Наука, 1950–2017",
        "publisher": "Наука",
        "year": None,
        "scripts": ["cyrillic"],
        "structure": "prose",
        "needs_review": False,
        "provenance": (
            "H2738. Anatoliy Drive «Для Пахтания» / "
            "Все статьи Махабхараты (для чтения).docx (2024-10-04). "
            "Parsed by mbh_word_layers.split_articles."
        ),
        "rights": _RIGHTS,
    }


def index_meta(kind: str) -> dict:
    slug, title = _INDEX_SLUGS[kind]
    return {
        "schema_version": 1,
        "slug": slug,
        "parent_work": "mahabharata",
        "layer": "index",
        "layer_title": title,
        "title_ru": title,
        "title_display": title,
        "title_en": f"Mahabharata {kind} index (Smirnov series)",
        "credit": "указатели томов АН СССР / Наука",
        "credit_role": "Указатель",
        "imprint": "АН СССР / Наука",
        "publisher": "Наука",
        "year": None,
        "scripts": ["cyrillic"],
        "structure": "dictionary",
        "needs_review": False,
        "provenance": (
            "H2738. Anatoliy Drive «Для Пахтания» / "
            "Махабхарата -все указатели.doc (2022-10-26). "
            f"Kind={kind}; volume tag [N] prefixes each entry."
        ),
        "rights": _RIGHTS,
    }


def emit_articles(text: str, *, skip_rt: bool) -> dict:
    arts = ml.split_articles(text)
    recs = ml.article_records(arts, ARTICLES_SLUG)
    meta = articles_meta()
    _write_jsonl(_JSONL / f"{ARTICLES_SLUG}.jsonl", recs)
    _write_meta(_HERE / f"{ARTICLES_SLUG}.meta.json", meta)
    titles = ml.article_titles(arts)
    # emit_prose_html uses titles={} — pass via render ourselves for headings
    from build_corpus_html import render_document, write_document

    lines = render_document(recs, meta, titles=titles, skandha=None)
    fn = f"{ARTICLES_SLUG}.html"
    write_document(lines, _DATA, fn, meta, None)
    added = append_data_txt(_DATA_TXT, [fn])
    out = {
        "slug": ARTICLES_SLUG,
        "kind": "articles",
        "articles": len(arts),
        "records": len(recs),
        "filename": fn,
        "data_txt_added": added,
        "volumes": sorted({a.volume for a in arts}),
        "titles": [f"{a.volume}. {a.title}" for a in arts],
    }
    if not skip_rt:
        out["roundtrip"] = roundtrip_prose_html(ARTICLES_SLUG)
    return out


def emit_indexes(text: str, *, skip_rt: bool) -> list[dict]:
    sections = ml.split_indexes(text)
    by_kind: dict[str, list[str]] = {k: [] for k in _INDEX_SLUGS}
    section_counts: dict[str, int] = {k: 0 for k in _INDEX_SLUGS}
    for sec in sections:
        by_kind[sec.kind].extend(ml.prefixed_entries(sec))
        section_counts[sec.kind] += 1
    summaries: list[dict] = []
    for kind, entries in by_kind.items():
        slug, _title = _INDEX_SLUGS[kind]
        recs = ml.index_records(entries, slug)
        meta = index_meta(kind)
        _write_jsonl(_JSONL / f"{slug}.jsonl", recs)
        _write_meta(_HERE / f"{slug}.meta.json", meta)
        fn = emit_dictionary_txt(recs, meta, _DATA, slug)
        added = append_data_txt(_DATA_TXT, [fn])
        s = {
            "slug": slug,
            "kind": kind,
            "sections": section_counts[kind],
            "records": len(recs),
            "filename": fn,
            "data_txt_added": added,
        }
        if not skip_rt:
            s["roundtrip"] = roundtrip_dictionary(slug)
        summaries.append(s)
    return summaries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-dir", type=Path, default=_DEFAULT_SRC)
    ap.add_argument("--skip-rt", action="store_true")
    ap.add_argument("--articles-only", action="store_true")
    ap.add_argument("--indexes-only", action="store_true")
    args = ap.parse_args()
    src = args.source_dir
    summary: dict = {"source_dir": str(src)}

    if not args.indexes_only:
        art_text = _read_text(
            src,
            "vse_stati_dlya_chteniya.txt",
            "Все статьи Махабхараты (для чтения).txt",
        )
        art = emit_articles(art_text, skip_rt=args.skip_rt)
        summary["articles"] = art
        rt = art.get("roundtrip", {})
        print(
            f"articles n={art['articles']} recs={art['records']} "
            f"RT={rt.get('rate_pct', 'skip')}%"
        )
        for t in art["titles"]:
            print(f"  - {t}")

    if not args.articles_only:
        idx_text = _read_text(
            src,
            "vse_ukazateli.txt",
            "Махабхарата -все указатели.txt",
        )
        idxs = emit_indexes(idx_text, skip_rt=args.skip_rt)
        summary["indexes"] = idxs
        for s in idxs:
            rt = s.get("roundtrip", {})
            print(
                f"{s['slug']}: sections={s['sections']} recs={s['records']} "
                f"RT={rt.get('rate_pct', 'skip')}%"
            )

    out = _JSONL / "wave_h2738_mbh_word_summary.json"
    out.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"summary {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
