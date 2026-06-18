#!/usr/bin/env python3
"""wisdomlib catalog crawler (Phase 1).

Stage A: enumerate every non-Marathi entry from topic-section listing pages.
Stage B: fetch each entry's landing page concurrently to enrich it with
         language / translation status / chapter list.

Async + configurable worker pool (httpx). Polite, retrying, resumable.
robots.txt respected: only section pages and /book|essay|... + /d/docN.html
content is fetched; the Disallow'd /books?l=, print-chapter.php, search,
journals and ?i=/?l= params are never requested.

Usage:
    python crawl.py stageA                 # build entries_index.jsonl
    python crawl.py stageB [--workers N]    # enrich -> books_full.jsonl (resumable)
    python crawl.py report                  # summarise books_full.jsonl -> CATALOG.md
    python crawl.py all   [--workers N]     # stageA + stageB + report

Outputs (in this dir):
    entries_index.jsonl   master list from Stage A
    books_full.jsonl      enriched records from Stage B (one per line, resumable)
    CATALOG.md            human-readable summary built by `report`
"""
import re, sys, json, html as ihtml, asyncio, argparse, time
from collections import Counter
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
BASE = "https://www.wisdomlib.org"
UA = "Mozilla/5.0 (compatible; samskrtam-corpus-index/1.0; +https://samskrtam.ru)"

SKIP_SECTIONS = {"marathi", "books", "gallery", "shop", "glossary"}
SECTIONS = [
    "arthashastra","arts","ayurveda","buddhism","chandas","dhanurveda","dharmashastra",
    "ganapatya","gandhashastra","ganitashastra","hindu-philosophy","hinduism","history",
    "itihasa","jainism","jyotisha","katha","kavya","kosha","linguistics","mahayana",
    "mimamsa","natyashastra","nitishastra","nyaya","pali","pancaratra","purana",
    "rasashastra","samkhya","sanskrit","science","shaivism","shaktism","shiksha",
    "shilpashastra","theravada","tibetan-buddhism","vaisheshika","vaishnavism","various",
    "vastushastra","vedanta","vedic-hinduism","vyakarana","yoga",
]

# journal is Disallow'd by robots -> excluded from capture
ROW = re.compile(
    r'<a href="(/[a-z0-9-]+/(book|essay|compilation|scripture|article)/[a-z0-9-]+)"'
    r'\s+title="([^"]*)"\s+class="title-l">(.*?)</a>', re.S)
AUTHOR = re.compile(r'<span class="author">\s*(?:by\s*)?([^<]*?)\s*</span>', re.S)
WORDS = re.compile(r'<span class="words">\s*([\d,]+)\s*words', re.S)
H3 = re.compile(r'<h3>([^<]+)</h3>')
DESC = re.compile(r'name="description" content="([^"]*)"')
DOC = re.compile(r'href="(/[a-z0-9-]+/[a-z0-9-]+/[a-z0-9-]+/d/doc\d+\.html)"')
TITLE = re.compile(r'<title>([^<]*)</title>')

# meta-description language/kind markers
EDITION = re.compile(
    r'\bThe\s+(Sanskrit|Pali|Pāli|Prakrit|Tibetan|Tamil|Telugu|Hindi|Bengali|'
    r'English|German|French)\s+(edition|translation|version|text)\b', re.I)
ENG_STAR = re.compile(r'\*english translation\*', re.I)

PALI_KW = re.compile(
    r'\b(Pāli|Pali|Tipitaka|Tipiṭaka|Nikāya|Nikaya|Sutta|Suttanta|'
    r'Abhidhamma|Theravada|Theravāda|Jataka|Jātaka|Visuddhimagga|'
    r'Patimokkha|Pātimokkha|Vinaya|Dhammapada|Paritta|Atthakatha|Atthakathā|'
    r'Mahavamsa|Mahāvaṃsa|Petavatthu|Vimanavatthu|Milinda)\b')


def parse_section(page):
    out = []
    parts = H3.split(page)
    segments = [("(unclassified)", parts[0])]
    for i in range(1, len(parts), 2):
        segments.append((parts[i].strip(), parts[i + 1] if i + 1 < len(parts) else ""))
    for group, chunk in segments:
        for m in ROW.finditer(chunk):
            url = m.group(1); ctype = m.group(2)
            slug = url.rsplit("/", 1)[-1]
            title = ihtml.unescape(m.group(3)).strip()
            am = AUTHOR.search(m.group(4))
            author = ihtml.unescape(am.group(1)).strip() if am else ""
            wm = WORDS.search(chunk, m.end(), m.end() + 600)
            words = int(wm.group(1).replace(",", "")) if wm else None
            out.append((slug, BASE + url, title, author, words, group, ctype))
    return out


async def fetch(client, url, tries=4):
    for k in range(tries):
        try:
            r = await client.get(url, timeout=30.0, follow_redirects=True)
            if r.status_code == 200:
                return r.text
            if r.status_code in (404, 410):
                return None
        except Exception as e:
            last = e
        await asyncio.sleep(1.0 * (k + 1))
    print(f"  FAIL {url}", file=sys.stderr)
    return None


async def stage_a(workers):
    sem = asyncio.Semaphore(workers)
    books = {}
    async with httpx.AsyncClient(headers={"User-Agent": UA}, http2=False) as client:
        async def one(sec):
            async with sem:
                page = await fetch(client, f"{BASE}/{sec}")
            if not page:
                print(f"{sec:18s} FAILED"); return
            rows = parse_section(page)
            print(f"{sec:18s} {len(rows):4d} rows")
            for slug, url, title, author, words, group, ctype in rows:
                r = books.get(slug)
                if r is None:
                    books[slug] = dict(slug=slug, url=url, title=title, author=author,
                                       words=words, group=group, ctype=ctype, sections=[sec])
                else:
                    if sec not in r["sections"]:
                        r["sections"].append(sec)
                    if r["group"] == "(unclassified)" and group != "(unclassified)":
                        r["group"] = group
        await asyncio.gather(*(one(s) for s in SECTIONS if s not in SKIP_SECTIONS))

    out = sorted(books.values(), key=lambda x: x["slug"])
    p = HERE / "entries_index.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nStage A: {len(out)} unique non-Marathi entries -> {p.name}")
    return out


def classify(rec, html):
    desc = ""
    m = DESC.search(html)
    if m:
        desc = ihtml.unescape(m.group(1)).strip()
    has_english = bool(ENG_STAR.search(desc)) or "english translation" in desc.lower()
    src_lang = None; kind = None
    em = EDITION.search(desc)
    if em:
        lang = em.group(1).lower().replace("pāli", "pali")
        kind = em.group(2).lower()
        if kind in ("edition", "text", "version"):
            src_lang = lang  # "The Sanskrit edition of" -> source is Sanskrit
        if lang == "english" and kind == "translation":
            has_english = True
    secs = set(rec.get("sections", []))
    is_pali = bool(
        ("theravada" in secs or "pali" in secs)
        or PALI_KW.search(desc) or PALI_KW.search(rec.get("title", ""))
    )
    if src_lang is None:
        if is_pali:
            src_lang = "pali"
        elif secs & {"jainism"}:
            src_lang = "prakrit?"
        elif secs & {"tibetan-buddhism"}:
            src_lang = "tibetan?"
        else:
            src_lang = "sanskrit?"  # default for the Sanskritic sections
    docs = sorted(set(DOC.findall(html)))
    return dict(
        desc=desc, has_english=has_english, source_lang=src_lang,
        edition_kind=kind, is_pali=is_pali, chapter_count=len(docs),
        first_doc=(BASE + docs[0]) if docs else None,
    )


async def stage_b(workers):
    src = HERE / "entries_index.jsonl"
    if not src.exists():
        print("Run stageA first."); return
    entries = [json.loads(l) for l in src.open(encoding="utf-8")]
    out_p = HERE / "books_full.jsonl"
    done = set()
    if out_p.exists():
        for l in out_p.open(encoding="utf-8"):
            try: done.add(json.loads(l)["slug"])
            except Exception: pass
    todo = [e for e in entries if e["slug"] not in done]
    print(f"Stage B: {len(todo)} to fetch ({len(done)} already done), workers={workers}")

    sem = asyncio.Semaphore(workers)
    lock = asyncio.Lock()
    n = [0]
    out = out_p.open("a", encoding="utf-8")
    async with httpx.AsyncClient(headers={"User-Agent": UA}) as client:
        async def one(e):
            async with sem:
                html = await fetch(client, e["url"])
            rec = dict(e)
            if html:
                rec.update(classify(e, html))
            else:
                rec["fetch_failed"] = True
            line = json.dumps(rec, ensure_ascii=False)
            async with lock:
                out.write(line + "\n"); out.flush()
                n[0] += 1
                if n[0] % 25 == 0:
                    print(f"  {n[0]}/{len(todo)}")
        await asyncio.gather(*(one(e) for e in todo))
    out.close()
    print(f"Stage B done: wrote {n[0]} records -> {out_p.name}")


def _pct(n, total):
    return f"{100 * n / total:.0f}%" if total else "0%"


def make_report():
    """Summarise books_full.jsonl into a human-readable CATALOG.md."""
    src = HERE / "books_full.jsonl"
    if not src.exists():
        print("Run stageB first."); return
    recs = [json.loads(l) for l in src.open(encoding="utf-8") if l.strip()]
    n = len(recs)
    failed = [r for r in recs if r.get("fetch_failed")]
    ok = [r for r in recs if not r.get("fetch_failed")]
    total_words = sum(r.get("words") or 0 for r in ok)
    total_ch = sum(r.get("chapter_count") or 0 for r in ok)
    eng = sum(1 for r in ok if r.get("has_english"))
    pali = sum(1 for r in ok if r.get("is_pali"))

    by_lang = Counter(r.get("source_lang") or "?" for r in ok)
    by_type = Counter(r.get("ctype") or "?" for r in ok)
    by_sec = Counter(s for r in ok for s in r.get("sections", []))
    by_group = Counter(r.get("group") or "(unclassified)" for r in ok)

    L = []
    L.append("# wisdomlib catalog\n")
    L.append(f"Generated by `crawl.py report` from `books_full.jsonl` "
             f"on {time.strftime('%Y-%m-%d')}.\n")
    L.append("## Totals\n")
    L.append(f"- **Entries:** {n} ({len(failed)} fetch-failed)")
    L.append(f"- **Total words:** {total_words:,}")
    L.append(f"- **Total chapters/docs:** {total_ch:,}")
    L.append(f"- **English translation available:** {eng} ({_pct(eng, len(ok))})")
    L.append(f"- **Pali entries:** {pali} ({_pct(pali, len(ok))})\n")

    def table(title, counter, col):
        L.append(f"## {title}\n")
        L.append(f"| {col} | Entries | Share |")
        L.append("|---|--:|--:|")
        for k, c in counter.most_common():
            L.append(f"| {k} | {c} | {_pct(c, len(ok))} |")
        L.append("")

    table("By source language", by_lang, "Source language")
    table("By content type", by_type, "Type")
    table("By section", by_sec, "Section")
    table("By group", by_group, "Group")

    if failed:
        L.append(f"## Fetch failures ({len(failed)})\n")
        L.append("To retry, delete these slugs' lines from `books_full.jsonl` "
                 "(they count as done otherwise), then re-run `python crawl.py stageB`.\n")
        L.append("| Title | Slug | Section | URL |")
        L.append("|---|---|---|---|")
        for r in sorted(failed, key=lambda x: x.get("slug") or ""):
            title = (r.get("title") or "").replace("|", "\\|")
            secs = ", ".join(r.get("sections", []))
            L.append(f"| {title} | `{r.get('slug','')}` | {secs} | <{r.get('url','')}> |")
        L.append("")

    L.append("## Largest entries (top 25 by word count)\n")
    L.append("| Title | Words | Type | Source | English | URL |")
    L.append("|---|--:|---|---|:--:|---|")
    for r in sorted(ok, key=lambda x: x.get("words") or 0, reverse=True)[:25]:
        title = (r.get("title") or "").replace("|", "\\|")
        eng_m = "✓" if r.get("has_english") else ""
        L.append(f"| {title} | {(r.get('words') or 0):,} | {r.get('ctype','')} | "
                 f"{r.get('source_lang','')} | {eng_m} | <{r.get('url','')}> |")
    L.append("")

    p = HERE / "CATALOG.md"
    p.write_text("\n".join(L), encoding="utf-8")
    print(f"report: {n} entries -> {p.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["stageA", "stageB", "report", "all"])
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    t0 = time.time()
    if a.stage in ("stageA", "all"):
        asyncio.run(stage_a(a.workers))
    if a.stage in ("stageB", "all"):
        asyncio.run(stage_b(a.workers))
    if a.stage in ("report", "all"):
        make_report()
    print(f"elapsed {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
