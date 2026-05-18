from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
import re
from typing import List, Dict, Any, Optional

from app.services.compare_service import compare_url_for_hit
from app.services.slug import derive_slug

# KWIC defaults — 40 chars of context on each side of the matched term.
# Wider windows make the excerpt useful for scanning; narrower ones cram
# more results on screen. 40 strikes a balance for Russian + IAST.
_KWIC_WINDOW = 40


def _query_terms(query: str) -> list[str]:
    """Split a user-entered query into individual tokens, preserving order.
    Multi-line queries are flattened; whitespace within a line is split."""
    terms: list[str] = []
    for line in query.split("\n"):
        for token in line.split():
            t = token.strip()
            if t:
                terms.append(t)
    return terms


def kwic_excerpt(line_text: str, query: str, window: int = _KWIC_WINDOW) -> dict[str, str]:
    """Return a `{before, match, after}` keyword-in-context excerpt.

    Finds the first occurrence of any query term in `line_text` (case-
    insensitive), then trims `window` characters of context on each side.
    Prepends/appends `…` when truncation occurred so users see the elision.

    Falls back to a leading-window excerpt with no `match` highlight when
    nothing matches — happens for hits that came from FTS prefix expansion
    where the source line contains the full word but our naive substring
    search doesn't find it, or for regex matches without literal substrings.
    """
    if not line_text:
        return {"before": "", "match": "", "after": ""}
    if not query:
        return {"before": "", "match": "", "after": line_text[: window * 2]}

    lc = line_text.lower()
    for term in _query_terms(query):
        idx = lc.find(term.lower())
        if idx < 0:
            continue
        start = max(0, idx - window)
        end = min(len(line_text), idx + len(term) + window)
        return {
            "before": ("…" if start > 0 else "") + line_text[start:idx],
            "match": line_text[idx : idx + len(term)],
            "after": line_text[idx + len(term) : end] + ("…" if end < len(line_text) else ""),
        }

    fallback = line_text[: window * 2]
    return {
        "before": "",
        "match": "",
        "after": fallback + ("…" if len(line_text) > window * 2 else ""),
    }


def build_source_chart_data(results: list[dict]) -> list[dict]:
    """Aggregate results into a per-source hit-count list for the bar chart.

    Output is sorted by count descending. Each entry carries the source's
    title (for label), count (for bar width), and chart_anchor (matching
    the `id="chapter_N"` markup the existing fragment template emits).
    Returns empty list when only one source is hit — the chart adds no
    information then.
    """
    if not results:
        return []

    # Preserve first-seen order so multiple sources with the same count don't
    # reshuffle on every render.
    grouped: dict[int, dict] = {}
    order: list[int] = []
    for r in results:
        sid = r["source_id"]
        if sid not in grouped:
            grouped[sid] = {"title": r["source_title"], "count": 0}
            order.append(sid)
        grouped[sid]["count"] += 1

    if len(order) < 2:
        return []

    rows = []
    for chart_idx, sid in enumerate(sorted(order, key=lambda s: -grouped[s]["count"]), 1):
        rows.append({
            "title": grouped[sid]["title"],
            "count": grouped[sid]["count"],
            "chart_anchor": f"chapter_{order.index(sid) + 1}",
        })
    return rows

# Setup Jinja2 environment with autoescape
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates")
env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml'])
)

def get_count_suffix(count: int) -> str:
    if count == 100: return f"{count}-та"
    if count % 100 == 90: return f"{count}-та"
    if count % 100 == 40: return f"{count}-ка"
    
    if (count <= 10) or (count > 20):
        m = count % 10
        if m == 1: suffix = "-м"
        elif 2 <= m <= 4: suffix = "-х"
        elif m in [7, 8]: suffix = "-ми"
        else: suffix = "-ти"
    else:
        suffix = "-ти"
    return f"{count}{suffix}"

def sklonenie_v_n_poiskovyh_zaprosah(n: int) -> str:
    res = f" в {get_count_suffix(n)}"
    if n % 10 == 1 and n % 100 != 11:
        res += " поисковом запросе"
    else:
        res += " поисковых запросах"
    return res

def sklonenie_naideno_x_zapisey(x: int) -> str:
    if x % 10 == 1 and x % 100 != 11:
        return f"найдена {x} запись"
    elif (2 <= x % 10 <= 4) and (x % 100 < 10 or x % 100 > 20):
        return f"найдено {x} записи"
    else:
        return f"найдено {x} записей"

def sklonenie_naideno_v_y_istochnikah(y: int) -> str:
    if y % 10 == 1 and y % 100 != 11:
        return f" в {get_count_suffix(y)} источнике"
    else:
        return f" в {get_count_suffix(y)} источниках"

def render_fragment(query: str, results: List[Dict[str, Any]], limit_reached: bool = False, search_metadata: Optional[Dict[str, Any]] = None) -> str:
    # Group results preserving SQL order (sort_order, then line_num).
    # Do NOT re-sort by source_id — that breaks sources with sort_order != id.
    # Each item gets enriched with `compare_url` so the template can render a
    # cross-link to /compare/{work}/{ch}.{v} for hits in comparison-eligible
    # sources (None for the rest, which most sources are).
    grouped = {}
    for r in results:
        sid = r["source_id"]
        if sid not in grouped:
            grouped[sid] = {"title": r["source_title"], "items": []}
        r["compare_url"] = compare_url_for_hit(
            r.get("source_filename", "") or "",
            r.get("link_id", "") or "",
        )
        # Derive slug from filename so the template can emit slug-form source
        # URLs without an extra DB lookup. Filename comes from the SQL JOIN
        # in search_service; derive_slug is cheap (regex + transliteration table).
        r["source_slug"] = derive_slug(r.get("source_filename", "") or "")
        # Per-result KWIC excerpt for compact-view scanning.
        r["kwic"] = kwic_excerpt(r.get("line_text", "") or "", query)
        grouped[sid]["items"].append(r)

    # Per-source bar chart data (sorted by count desc). Empty when 0-1 sources.
    source_chart = build_source_chart_data(results)

    sorted_groups = list(grouped.values())  # dict preserves insertion order (Python 3.7+)
    
    # Create the header sentence
    total = len(results)
    sources_hit = len(grouped)
    
    # Handle multi-line query display
    query_display = query.replace('\n', ', ')
    query_count = len([q for q in query.split('\n') if q.strip()])
    
    template = env.get_template("result_fragment.html")
    return template.render(
        query=query,
        query_display=query_display,
        query_count=query_count,
        total=total,
        sources_hit=sources_hit,
        groups=sorted_groups,
        source_chart=source_chart,
        limit_reached=limit_reached,
        search_metadata=search_metadata,
        # Helper functions for the template
        get_count_suffix=get_count_suffix,
        sklonenie_v_n_poiskovyh_zaprosah=sklonenie_v_n_poiskovyh_zaprosah,
        sklonenie_naideno_x_zapisey=sklonenie_naideno_x_zapisey,
        sklonenie_naideno_v_y_istochnikah=sklonenie_naideno_v_y_istochnikah
    )

def render_full_page(query: str, fragment: str) -> str:
    template = env.get_template("full_page.html")
    return template.render(
        query=query,
        fragment=fragment
    )

def render_standalone(query: str, fragment: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    # Read assets to inline
    static_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static")
    
    try:
        with open(os.path.join(static_path, "style.css"), "r", encoding="utf-8") as f:
            css = f.read()
    except OSError:
        css = ""

    try:
        with open(os.path.join(static_path, "scripts", "selection.js"), "r", encoding="utf-8") as f:
            selection_js = f.read()
    except OSError:
        selection_js = ""
        
    template = env.get_template("standalone_page.html")
    return template.render(
        query=query,
        fragment=fragment,
        css=css,
        selection_js=selection_js,
        metadata=metadata
    )
