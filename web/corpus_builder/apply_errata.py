#!/usr/bin/env python3
"""Apply one work's errata.yml to its canonical JSONL and rebuild HTML.

Does not launch cb.exe. After the JSONL patch, the catalog recipe is
html-from-jsonl (build_corpus_html.py) — re-ingesting from PDF/Word would
wipe the patch. See docs/KATALOG_KOMBINACIJ_SBORKI_KORPUSA.md §5.

Usage:
    python web/corpus_builder/apply_errata.py --work bhagavati-manasa-puja-stotra
    python web/corpus_builder/apply_errata.py \\
        --errata web/tests/fixtures/errata/errata.yml \\
        --jsonl  web/tests/fixtures/errata/work.jsonl \\
        --out    /tmp/work.patched.jsonl \\
        --rebuild --meta web/tests/fixtures/errata/work.meta.json \\
        --data-dir /tmp/errata-html --slug errata-pilot
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import errata_yml as ey  # noqa: E402


def _resolve_paths(args: argparse.Namespace) -> dict[str, Path | str | None]:
    errata = Path(args.errata) if args.errata else None
    jsonl = Path(args.jsonl) if args.jsonl else None
    meta = Path(args.meta) if args.meta else None
    report = Path(args.report) if args.report else None
    slug = args.slug or args.work
    if args.work and (errata is None or jsonl is None):
        recipe = ey.recipe_for(args.work)
        slug = slug or recipe.get("slug") or args.work
        if errata is None:
            errata = ey.ERRATA_ROOT / args.work / "errata.yml"
        if jsonl is None:
            jsonl = ey._repo_path(recipe["jsonl"])
        if meta is None and recipe.get("meta"):
            meta = ey._repo_path(recipe["meta"])
        if report is None and recipe.get("report"):
            report = ey._repo_path(recipe["report"])
    if errata is None or jsonl is None:
        raise SystemExit("need --work (catalog recipe) or both --errata and --jsonl")
    return {
        "errata": errata,
        "jsonl": jsonl,
        "meta": meta,
        "report": report,
        "slug": slug,
    }


def rebuild_html(
    jsonl: Path,
    meta: Path,
    data_dir: Path,
    slug: str,
    report: Path | None,
) -> None:
    from build_corpus_html import main as html_main

    argv = [
        "build_corpus_html.py",
        "--jsonl",
        str(jsonl),
        "--meta",
        str(meta),
        "--data-dir",
        str(data_dir),
        "--slug",
        slug,
        "--combined",
    ]
    if report and report.exists():
        argv.extend(["--report", str(report)])
    old = sys.argv
    try:
        sys.argv = argv
        html_main()
    finally:
        sys.argv = old


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", help="catalog slug (looks up errata/recipes.json)")
    ap.add_argument("--errata", help="path to errata.yml")
    ap.add_argument("--jsonl", help="canonical JSONL to patch")
    ap.add_argument("--out", help="write patched JSONL here (default: in-place)")
    ap.add_argument("--rebuild", action="store_true", help="run html-from-jsonl")
    ap.add_argument("--meta", help="work meta.json (rebuild)")
    ap.add_argument("--report", help="parser report.json (rebuild, optional)")
    ap.add_argument("--data-dir", help="HTML output directory (rebuild)")
    ap.add_argument("--slug", help="HTML filename slug")
    args = ap.parse_args()

    paths = _resolve_paths(args)
    errata_path = Path(paths["errata"])
    jsonl_path = Path(paths["jsonl"])
    if not errata_path.is_file():
        raise SystemExit(f"missing errata.yml: {errata_path}")
    if not jsonl_path.is_file():
        raise SystemExit(f"missing JSONL: {jsonl_path}")

    loaded = ey.load_errata_yml(errata_path)
    rows = ey.load_jsonl(jsonl_path)
    patched, report = ey.apply_entries(rows, loaded["entries"])
    dest = Path(args.out) if args.out else jsonl_path
    ey.write_jsonl(dest, patched)

    applied = sum(1 for r in report if r["status"] == "applied")
    already = sum(1 for r in report if r["status"] == "already_applied")
    print(
        json.dumps(
            {
                "work": loaded.get("work") or args.work,
                "errata": str(errata_path).replace("\\", "/"),
                "jsonl_in": str(jsonl_path).replace("\\", "/"),
                "jsonl_out": str(dest).replace("\\", "/"),
                "entries": len(loaded["entries"]),
                "applied": applied,
                "already_applied": already,
                "report": report,
            },
            ensure_ascii=False,
        )
    )

    if args.rebuild:
        meta = Path(paths["meta"]) if paths["meta"] else None
        if meta is None or not meta.is_file():
            raise SystemExit("--rebuild needs --meta (or a catalog recipe with meta)")
        data_dir = Path(args.data_dir) if args.data_dir else dest.parent / "html"
        slug = str(paths["slug"] or "work")
        rebuild_html(
            dest,
            meta,
            data_dir,
            slug,
            Path(paths["report"]) if paths["report"] else None,
        )
        print(f"rebuilt HTML under {data_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
