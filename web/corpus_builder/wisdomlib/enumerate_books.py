#!/usr/bin/env python3
"""Stage A: enumerate every wisdomlib book from the topic-section listing pages.

robots.txt note: the alphabetical browse filter (`/books?l=`) is Disallow'd, as are
print-chapter.php, search, journals and `?i=`/`?l=` params. The topic-section pages
(e.g. /hinduism, /buddhism, /purana) are allowed and list every book in structured
rows, so we enumerate from those. Category pages are NOT paginated (?p=2 == ?p=1).

Output: books_index.jsonl  (one deduplicated book per line, with the set of sections
it appears under and its wisdomlib translation-status group header).
"""
import re, sys, json, time, html as ihtml
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE = "https://www.wisdomlib.org"
UA = "Mozilla/5.0 (compatible; samskrtam-corpus-index/1.0; +https://samskrtam.ru)"

# Topic sections discovered from /books. `marathi` is EXCLUDED per request.
# Non-book hubs (books, gallery, shop, glossary) are harmless (yield 0 rows) but skipped.
SKIP = {"marathi", "books", "gallery", "shop", "glossary"}
SECTIONS = [
    "arthashastra","arts","ayurveda","buddhism","chandas","dhanurveda","dharmashastra",
    "ganapatya","gandhashastra","ganitashastra","hindu-philosophy","hinduism","history",
    "itihasa","jainism","jyotisha","katha","kavya","kosha","linguistics","mahayana",
    "mimamsa","natyashastra","nitishastra","nyaya","pali","pancaratra","purana",
    "rasashastra","samkhya","sanskrit","science","shaivism","shaktism","shiksha",
    "shilpashastra","theravada","tibetan-buddhism","vaisheshika","vaishnavism","various",
    "vastushastra","vedanta","vedic-hinduism","vyakarana","yoga",
]

# Content types: book, essay, compilation, scripture, article are allowed.
# `journal` is Disallow'd by robots.txt (/<section>/journal/) -> excluded.
ROW = re.compile(
    r'<a href="(/[a-z0-9-]+/(book|essay|compilation|scripture|article)/[a-z0-9-]+)"'
    r'\s+title="([^"]*)"\s+class="title-l">(.*?)</a>', re.S)
AUTHOR = re.compile(r'<span class="author">\s*(?:by\s*)?([^<]*?)\s*</span>', re.S)
WORDS = re.compile(r'<span class="words">\s*([\d,]+)\s*words', re.S)
H3 = re.compile(r'<h3>([^<]+)</h3>')


def fetch(url, tries=3):
    for k in range(tries):
        try:
            req = Request(url, headers={"User-Agent": UA})
            with urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if k == tries - 1:
                print(f"  FAIL {url}: {e}", file=sys.stderr)
                return ""
            time.sleep(1.5 * (k + 1))


def parse_section(section, page):
    """Yield (slug, url, title, author, words, group_header)."""
    # Mark group headers so each row inherits the most recent <h3> above it.
    out = []
    # Split keeping headers
    parts = H3.split(page)
    # parts = [pre, header1, chunk1, header2, chunk2, ...]
    cur = "(unclassified)"
    segments = [(cur, parts[0])]
    for i in range(1, len(parts), 2):
        cur = parts[i].strip()
        segments.append((cur, parts[i + 1] if i + 1 < len(parts) else ""))
    for group, chunk in segments:
        for m in ROW.finditer(chunk):
            url = m.group(1)
            ctype = m.group(2)
            slug = url.rsplit("/", 1)[-1]
            title = ihtml.unescape(m.group(3)).strip()
            inner = m.group(4)
            am = AUTHOR.search(inner)
            author = ihtml.unescape(am.group(1)).strip() if am else ""
            # words live in the sibling block right after the </a>; search a window
            wm = WORDS.search(chunk, m.end(), m.end() + 600)
            words = int(wm.group(1).replace(",", "")) if wm else None
            out.append((slug, BASE + url, title, author, words, group, ctype))
    return out


def main():
    books = {}  # slug -> record
    for sec in SECTIONS:
        if sec in SKIP:
            continue
        page = fetch(f"{BASE}/{sec}")
        rows = parse_section(sec, page)
        print(f"{sec:18s} {len(rows):4d} rows")
        for slug, url, title, author, words, group, ctype in rows:
            r = books.get(slug)
            if r is None:
                books[slug] = {
                    "slug": slug, "url": url, "title": title, "author": author,
                    "words": words, "group": group, "ctype": ctype, "sections": [sec],
                }
            else:
                if sec not in r["sections"]:
                    r["sections"].append(sec)
                # keep the most informative group label (prefer a real header)
                if r["group"] == "(unclassified)" and group != "(unclassified)":
                    r["group"] = group
        time.sleep(0.3)

    out = sorted(books.values(), key=lambda x: x["slug"])
    with open("books_index.jsonl", "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Summary
    from collections import Counter
    gc = Counter(r["group"] for r in out)
    tc = Counter(r["ctype"] for r in out)
    print(f"\nTOTAL unique non-Marathi entries: {len(out)}")
    print("By translation-status group:")
    for g, n in gc.most_common():
        print(f"  {n:5d}  {g}")
    print("By content type:")
    for t, n in tc.most_common():
        print(f"  {n:5d}  {t}")


if __name__ == "__main__":
    main()
