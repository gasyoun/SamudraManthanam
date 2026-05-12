from jinja2 import Environment, FileSystemLoader
import os
from typing import List, Dict, Any

# Setup Jinja2 environment
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates")
env = Environment(loader=FileSystemLoader(template_dir))

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

def render_fragment(query: str, results: List[Dict[str, Any]]) -> str:
    # Group results by source
    grouped = {}
    for r in results:
        sid = r["source_id"]
        if sid not in grouped:
            grouped[sid] = {
                "title": r["source_title"],
                "items": []
            }
        grouped[sid]["items"].append(r)
    
    # Sort groups by source_id (or title)
    sorted_groups = [grouped[sid] for sid in sorted(grouped.keys())]
    
    # Create the header sentence
    total = len(results)
    sources_hit = len(grouped)
    header = f"При пахтании... {sklonenie_v_n_poiskovyh_zaprosah(1)} для слова „{query}“ {sklonenie_naideno_x_zapisey(total)}{sklonenie_naideno_v_y_istochnikah(sources_hit)}"
    
    template = env.get_template("result_fragment.html")
    return template.render(
        query=query,
        header=header,
        groups=sorted_groups,
        total=total
    )

def render_full_page(query: str, fragment: str) -> str:
    template = env.get_template("full_page.html")
    return template.render(
        query=query,
        fragment=fragment
    )
