from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
from typing import List, Dict, Any, Optional

# Setup Jinja2 environment with autoescape
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates")
env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml'])
)

def get_count_suffix(count: int) -> str:
    if count == 100: return f"{count}-та"
    if count == 90: return f"{count}-та"
    if count == 40: return f"{count}-ка"
    
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
    grouped = {}
    for r in results:
        sid = r["source_id"]
        if sid not in grouped:
            grouped[sid] = {"title": r["source_title"], "items": []}
        grouped[sid]["items"].append(r)

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

def render_standalone(query: str, fragment: str) -> str:
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
        selection_js=selection_js
    )
