import re
from typing import Iterator, Dict, Optional

VEDIC_MAP = {
    'á': 'a', 'à': 'a', 'é': 'e', 'è': 'e',
    'í': 'i', 'ì': 'i', 'ó': 'o', 'ò': 'o',
    'ú': 'u', 'ù': 'u', 'r̥': 'ṛ',
    '̀': '', '́': '',   # combining accents
}

def remove_html_tags(s: str) -> str:
    # Port of RemoveHTMLTags from textu.pas
    s = re.sub(r'<br>', ' ', s, flags=re.IGNORECASE)
    for vedic, plain in VEDIC_MAP.items():
        s = s.replace(vedic, plain)
    s = re.sub(r'<small>.*?</small>', '', s, flags=re.IGNORECASE)
    s = re.sub(r'<[^>]*>', '', s)
    s = re.sub(r'  +', ' ', s).strip()
    return s

def parse_corpus_file(path: str) -> Iterator[Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        return

    # Line 0: source title — strip <!-- prefix and --> or --!> suffix
    title_line = lines[0].strip()
    title = re.sub(r'^<!--\s*', '', re.sub(r'\s*--[>!]+$', '', title_line))
    
    # Yield title info first (as a special record or handle separately in ingest.py)
    # For simplicity, we'll return a dict with a "type" or just let ingest.py handle the first line.
    
    current_chapter = ""
    
    for i, line in enumerate(lines[1:], start=1):
        line = line.strip()
        if not line:
            continue
            
        if re.match(r'^\s*</?(?:html|head|body)[^>]*>\s*$', line, flags=re.IGNORECASE):
            continue
            
        # extract link_id: find id="..." attribute value
        link_id_match = re.search(r'id=["\']([^"\']+)["\']', line)
        link_id = link_id_match.group(1) if link_id_match else ""
        
        # extract chapter: if line contains <H1>...</H1>, update running chapter var
        chapter_match = re.search(r'<H1>(.*?)</H1>', line, flags=re.IGNORECASE)
        if chapter_match:
            current_chapter = remove_html_tags(chapter_match.group(1))
            
        # strip text from <span class="endchapter"> to end of line
        line_clean = re.sub(r'<span class="endchapter">.*', '', line, flags=re.IGNORECASE)
        
        plain_text = remove_html_tags(line_clean)
        
        yield {
            "line_num": i,
            "line_html": line,
            "line_text": plain_text,
            "link_id": link_id,
            "chapter": current_chapter
        }

def get_source_title(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        line = f.readline().strip()
        # Strip <!-- prefix and any variant of --> or --!> suffix
        return re.sub(r'^<!--\s*', '', re.sub(r'\s*--[>!]+$', '', line))
