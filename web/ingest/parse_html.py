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

# Matches the trailing "CHAPTER. VERSE" or "CHAPTER. VERSE_FIRST-VERSE_LAST"
# segment of a `<div class="range" title="...">` attribute. Examples:
#   "Махабхарата VI. 1. 1"      -> ("1", "1")
#   "Махабхарата VI. 1. 3-6"    -> ("1", "3-6")
#   "Гитаговинда, 1. 11-12"     -> ("1", "11-12")
_RANGE_TITLE_VERSE = re.compile(r'(\d+)\.\s*(\d+(?:-\d+)?)\s*$')

_CITATION_BLOCK_ID = re.compile(
    r'class=["\']citation_block["\'][^>]*\sid=["\']([^"\']+)["\']'
)
_RANGE_DIV_TITLE = re.compile(
    r'class=["\']range["\'][^>]*\stitle=["\']([^"\']+)["\']'
)
_ANY_ID = re.compile(r'id=["\']([^"\']+)["\']')


def _extract_link_id(line: str) -> str:
    """Extract a URL-friendly verse identifier from a corpus HTML line.

    Three priorities, in order:

    1. `id="..."` on a `class="citation_block"` div — the clean form authored
       in most newer corpus files (e.g. `id="1.1"`).
    2. `<div class="range" title="...">` — fallback for older files
       (Mahābhārata Bhīṣma-parvan, Gītagovinda) whose `citation_block` divs
       lack an `id` attribute but whose surrounding `range` div carries a
       human-readable "Work-name BOOK. CHAPTER. VERSE" string. We extract
       the trailing CHAPTER.VERSE (or CHAPTER.VERSE_RANGE for merged
       stanzas) to produce a URL anchor like "1.1" or "1.3-6".
    3. Any `id="..."` anywhere on the line — covers chapter-title divs
       (`id="chapter_1"`) and other non-verse anchors.

    Why this matters: the original regex `re.search(r'id=...')` matched the
    *first* `id=` on the line, which for Bhīṣma-parvan / Gītagovinda lines is
    the `range` div's bibliographic-page identifier ("Махабхарата 2009 (VI): 9").
    That string is unique-per-edition but not URL-routable and prevents deep
    linking to ~23k Mahābhārata verses and the whole Gītagovinda.
    """
    m = _CITATION_BLOCK_ID.search(line)
    if m:
        return m.group(1)

    range_match = _RANGE_DIV_TITLE.search(line)
    if range_match:
        cv = _RANGE_TITLE_VERSE.search(range_match.group(1))
        if cv:
            return f"{cv.group(1)}.{cv.group(2)}"
        # Range div present but title isn't a CHAPTER.VERSE form — its `id=`
        # is a bibliographic page reference, not a verse anchor. Bail rather
        # than fall through and pick up the useless page id.
        return ""

    m = _ANY_ID.search(line)
    return m.group(1) if m else ""


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
            
        link_id = _extract_link_id(line)
        
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
