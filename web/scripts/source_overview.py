#!/usr/bin/env python3
"""Compact per-source search overview (no tall bar chart).

Calls POST /api/search, aggregates hits by source, and prints a short
ranked text report — top N sources + residue — suitable for chat, shell,
or a report file. Mirrors the compact «По источникам» panel in the UI
(H2422).

Examples
--------
  python web/scripts/source_overview.py огонь
  python web/scripts/source_overview.py --top 20 --out report.txt огонь
  python web/scripts/source_overview.py --base http://127.0.0.1:8000 dharma
  python web/scripts/source_overview.py --mode plain --whole-word огонь

Environment
-----------
  SAMUDRA_BASE_URL  default API base (overridden by --base)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from collections import OrderedDict
from typing import Any

# Allow `python web/scripts/source_overview.py` from repo root / worktree.
_WEB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WEB_ROOT not in sys.path:
    sys.path.insert(0, _WEB_ROOT)

from app.services.html_service import (  # noqa: E402
    SOURCE_OVERVIEW_TOP_N,
    build_source_chart_data,
    format_elapsed_ru,
    format_source_overview_text,
)

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_BASE = os.environ.get(
    "SAMUDRA_BASE_URL",
    "https://samudra.193.232.229.92.sslip.io",
)


def _post_search(
    base: str,
    *,
    query: str,
    mode: str,
    case_sensitive: bool,
    whole_word: bool,
    limit: int,
    timeout: float,
) -> dict[str, Any]:
    url = base.rstrip("/") + "/api/search"
    payload = {
        "query": query,
        "mode": mode,
        "case_sensitive": case_sensitive,
        "whole_word": whole_word,
        "source_ids": None,
        "limit": limit,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code} from {url}: {raw[:500]}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"Network error contacting {url}: {e}") from e


def _rows_from_results(results: list[dict]) -> list[dict]:
    """Prefer the shared aggregator; fall back if results lack source_title."""
    try:
        rows = build_source_chart_data(results)
        if rows:
            return rows
    except (KeyError, TypeError):
        pass
    # Single-source or odd payloads — still produce one line.
    grouped: "OrderedDict[Any, dict]" = OrderedDict()
    for r in results:
        sid = r.get("source_id")
        title = r.get("source_title") or f"source_id={sid}"
        if sid not in grouped:
            grouped[sid] = {"title": title, "count": 0, "chart_anchor": ""}
        grouped[sid]["count"] += 1
    return sorted(grouped.values(), key=lambda x: -int(x["count"]))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Текстовый обзор результатов поиска по источникам (без длинного графика).",
    )
    p.add_argument("query", help="Поисковый запрос (кириллица / IAST / …)")
    p.add_argument(
        "--base",
        default=DEFAULT_BASE,
        help=f"Base URL API (default: {DEFAULT_BASE})",
    )
    p.add_argument(
        "--top",
        type=int,
        default=SOURCE_OVERVIEW_TOP_N,
        help=f"Сколько источников показать полностью (default: {SOURCE_OVERVIEW_TOP_N})",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=5000,
        help="Лимит hit-ов API (default: 5000, как в UI)",
    )
    p.add_argument(
        "--mode",
        default="plain",
        choices=("plain", "regex", "morphological"),
        help="Режим поиска (default: plain)",
    )
    p.add_argument("--case-sensitive", action="store_true")
    p.add_argument("--whole-word", action="store_true")
    p.add_argument(
        "--out",
        metavar="PATH",
        help="Записать отчёт в файл (UTF-8); иначе stdout",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Машинный JSON вместо текста",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="HTTP timeout seconds (default: 120)",
    )
    args = p.parse_args(argv)

    data = _post_search(
        args.base,
        query=args.query,
        mode=args.mode,
        case_sensitive=args.case_sensitive,
        whole_word=args.whole_word,
        limit=args.limit,
        timeout=args.timeout,
    )
    results = data.get("results") or []
    rows = _rows_from_results(results)
    total = int(data.get("total") or len(results))
    elapsed_ms = data.get("elapsed_ms")

    if args.as_json:
        # When build_source_chart_data suppressed a single-source hit list, rebuild.
        json_rows = rows
        if not json_rows and results:
            json_rows = _rows_from_results(results) or [
                {
                    "title": results[0].get("source_title") or "(один источник)",
                    "count": total,
                }
            ]
        report = {
            "query": args.query,
            "total": total,
            "sources_hit": int(data.get("sources_hit") or max(len(json_rows), 1 if total else 0)),
            "elapsed_ms": elapsed_ms,
            "top_n": args.top,
            "sources": [
                {
                    "rank": i,
                    "title": r["title"],
                    "count": int(r["count"]),
                    "pct": round(100.0 * int(r["count"]) / total, 2) if total else 0.0,
                }
                for i, r in enumerate(json_rows, 1)
            ],
        }
        text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    else:
        if total == 0:
            text = f"Запрос: «{args.query}» · 0 записей\n"
        elif not rows:
            # Single source — build_source_chart_data returns [] by design.
            title = (results[0].get("source_title") if results else "") or "(один источник)"
            el = format_elapsed_ru(elapsed_ms)
            bits = [f"Запрос: «{args.query}»", f"{total} записей", "1 источник"]
            if el:
                bits.append(el)
            text = " · ".join(bits) + f"\n1. {title} — {total} (100.0%)\n"
        else:
            text = format_source_overview_text(
                rows,
                total=total,
                top_n=args.top,
                query=args.query,
                elapsed_ms=elapsed_ms,
            )
            if not text.endswith("\n"):
                text += "\n"

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
