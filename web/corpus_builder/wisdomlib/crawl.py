#!/usr/bin/env python3
"""wisdomlib catalog crawler (Phase 1).

Stage A: enumerate every non-Marathi entry from topic-section listing pages.
Stage B: fetch each entry's landing page concurrently to enrich it with
         language / translation status / chapter list.
Stage C: download the actual chapter pages (/d/docN.html) of selected books.

Async + configurable worker pool (httpx). Polite, retrying, resumable.
robots.txt respected: only section pages and /book|essay|... + /d/docN.html
content is fetched; the Disallow'd /books?l=, print-chapter.php, search,
journals and ?i=/?l= params are never requested.

Usage:
    python crawl.py stageA                 # build entries_index.jsonl
    python crawl.py stageB [--workers N]    # enrich -> books_full.jsonl (resumable)
    python crawl.py report                  # summarise books_full.jsonl -> CATALOG.md
    python crawl.py stageC [filters]        # download chapter pages -> content/<slug>/
    python crawl.py all   [--workers N]     # stageA + stageB + report (NOT stageC)

Politeness / rate limiting (any stage):
    --workers N    concurrent requests (default 16; use 2-4 if Cloudflare pushes back)
    --delay S      sleep S s (jittered) after each request, held inside the worker
                   slot -> effective rate ~= workers/S req/s. e.g. --workers 2 --delay 1
The client uses a browser-like UA + headers and HTTP/2, and honours Retry-After on
429/503. None of this defeats an interactive JS/Turnstile challenge (httpx runs no
JS); it only eases heuristic gating. If challenges persist, slow down and wait.

Selection filters (apply to stageB's universe and stageC; combine with AND):
    --section S    only entries in section S        (repeatable / comma-list)
    --ctype T      only this content type           (book|essay|article|...)
    --lang L       only this source_lang            (books_full only; sanskrit|pali|...)
    --slug S       only these explicit slugs        (repeatable / comma-list)
    --english      only entries with an English translation   (books_full only)
    --pali / --no-pali   keep / drop Pali entries              (books_full only)
    --min-words N  only entries of >= N words
    --limit N      cap the selection at N entries
    --shard k/n    fetch only shard k of n machines (disjoint, stable by slug) so
                   several home/residential connections each take a non-overlapping
                   slice — spreading the per-IP Cloudflare volume budget. e.g. run
                   --shard 1/3, 2/3, 3/3 on three machines; merge the content/ dirs.
    --impersonate PROFILE   use a curl_cffi browser TLS fingerprint (e.g. chrome)
                   instead of httpx; can raise the per-IP budget (needs curl_cffi)
    --out DIR      stageC output dir (default: content)
    --dry-run      stageC: list what would be fetched, fetch nothing

Outputs (in this dir):
    entries_index.jsonl   master list from Stage A
    books_full.jsonl      enriched records from Stage B (one per line, resumable)
    CATALOG.md            human-readable summary built by `report`
    content/<slug>/*.html raw chapter pages from Stage C (gitignored)
"""
import re, sys, json, html as ihtml, asyncio, argparse, time, random, hashlib
from collections import Counter
from pathlib import Path

import httpx

try:                       # HTTP/2 needs the optional h2 package; fall back if absent
    import h2  # noqa: F401
    HTTP2 = True
except ImportError:
    HTTP2 = False

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
BASE = "https://www.wisdomlib.org"
# Browser-like UA + headers reduce Cloudflare bot-heuristic friction (a non-browser
# UA / bare header set is an easy bot tell). This does NOT defeat a JS/Turnstile
# challenge — httpx runs no JavaScript — it only helps with heuristic gating.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
              "image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
}
DELAY = 0.0   # seconds between requests per worker (set from --delay); jittered +0-30%
IMPERSONATE = None  # set from --impersonate: a curl_cffi browser profile, e.g. "chrome"
DOCS_MANIFEST = "_docs_manifest.json"
LAST_RUN = "_last_run.json"


def new_client():
    """Construct the async HTTP client used by every stage.

    Default: httpx with HTTP/2 + browser-like headers (follow_redirects at the
    client level so the per-request call is identical across backends).

    With --impersonate (and curl_cffi installed): a curl_cffi AsyncSession that
    replays a real browser's TLS/JA3 + HTTP/2 fingerprint. That fingerprint is
    distinct from the request headers we already send, and Cloudflare's per-IP
    bot score weighs it — a genuine-Chrome handshake can lift the per-IP request
    budget before a 403. It does NOT defeat an interactive JS/Turnstile challenge.
    Falls back to httpx (with a warning) if curl_cffi is absent."""
    if IMPERSONATE:
        try:
            from curl_cffi.requests import AsyncSession
            return AsyncSession(headers=HEADERS, impersonate=IMPERSONATE)
        except ImportError:
            print(f"  --impersonate {IMPERSONATE!r} requested but curl_cffi is not "
                  "installed; falling back to httpx (pip install curl_cffi)",
                  file=sys.stderr)
    return httpx.AsyncClient(headers=HEADERS, http2=HTTP2, follow_redirects=True)

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

# Soft-200 detector: Cloudflare / interstitial / "verify you are human" pages are
# served WITH status 200 but are not content. Catch them so a block is never cached
# as a chapter (and never silently skipped by the per-page resume check).
BLOCK_SIG = re.compile(
    r'cf-browser-verification|challenge-platform|/cdn-cgi/challenge|'
    r'Just a moment\.\.\.|Attention Required|Checking your browser|'
    r'Enable JavaScript and cookies to continue', re.I)


def is_block_page(html):
    """True if an HTTP-200 body looks like a bot-block/challenge rather than content."""
    return not html or len(html) < 200 or bool(BLOCK_SIG.search(html[:4000]))


def _doc_name(url):
    return url.rsplit("/", 1)[-1]


def _load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _docs_from_landing(html):
    return sorted(set(DOC.findall(html)))


def _urls_from_expected(r, expected):
    first_doc = r.get("first_doc") or ""
    if not first_doc or "/" not in first_doc:
        return []
    base = first_doc.rsplit("/", 1)[0]
    return [f"{base}/{name}" for name in expected]


def _validate_cached_docs(bdir, expected_names):
    expected = set(expected_names)
    valid = set()
    invalid_removed = 0
    if not bdir.exists():
        return valid, invalid_removed
    for f in bdir.glob("doc*.html"):
        # Only DELETE a file if it is itself corrupt (a cached block/empty page).
        # A good file merely absent from `expected` is left in place: `expected`
        # can be short/stale (a truncated-but-not-blocked landing page yields a
        # partial doc list), and pruning by name there would destroy valid
        # chapters and force a re-download against a rate-limited host.
        try:
            corrupt = is_block_page(f.read_text(encoding="utf-8"))
        except Exception:
            corrupt = True
        if corrupt:
            try:
                f.unlink()
                invalid_removed += 1
            except FileNotFoundError:
                pass
        elif f.name in expected:
            valid.add(f.name)
    return valid, invalid_removed

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
            r = await client.get(url, timeout=30.0)   # redirects handled per-client
            if r.status_code == 200:
                if DELAY:                              # throttle held inside caller's
                    await asyncio.sleep(DELAY * (1 + 0.3 * random.random()))  # semaphore
                return r.text
            if r.status_code in (404, 410):
                return None
            if r.status_code in (429, 503):            # rate-limited -> honour Retry-After
                ra = r.headers.get("retry-after", "")
                wait = float(ra) if ra.isdigit() else 5.0 * (k + 1)
                await asyncio.sleep(wait)
                continue
        except Exception:
            pass
        await asyncio.sleep(1.0 * (k + 1))
    print(f"  FAIL {url}", file=sys.stderr)
    return None


async def stage_a(workers):
    sem = asyncio.Semaphore(workers)
    books = {}
    async with new_client() as client:
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


async def stage_b(workers, a):
    src = HERE / "entries_index.jsonl"
    if not src.exists():
        print("Run stageA first."); return
    entries = [json.loads(l) for l in src.open(encoding="utf-8")]
    entries = select(entries, a)                       # honour shared CLI filters
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
    async with new_client() as client:
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


def _csv(vals):
    """Flatten an argparse append-list, splitting comma-lists -> set of tokens."""
    out = []
    for v in vals or []:
        out += [x.strip() for x in v.split(",") if x.strip()]
    return set(out)


def _parse_shard(spec):
    """Parse a "k/n" shard spec into (k, n). Splits the selection across machines
    by a stable hash of slug so N home connections each fetch a disjoint subset
    (no coordination, no overlap — the per-IP Cloudflare budget is what we spread).
    Returns None when unset."""
    if not spec:
        return None
    m = re.match(r"^\s*(\d+)\s*/\s*(\d+)\s*$", spec)
    if not m:
        raise ValueError(f"--shard must be k/n (got {spec!r})")
    k, n = int(m.group(1)), int(m.group(2))
    if n < 1 or not (1 <= k <= n):
        raise ValueError(f"--shard k/n must satisfy 1<=k<=n (got {spec!r})")
    return k, n


def _shard_of(slug, n):
    """Stable 0-based shard index for a slug. Uses md5 (not Python's salted
    hash()) so the partition is identical across machines and runs."""
    return int(hashlib.md5((slug or "").encode("utf-8")).hexdigest(), 16) % n


def select(records, a):
    """Apply the shared CLI filters (AND-combined) to a list of records.
    Missing fields fail the corresponding filter, so lang/english/pali only
    select meaningfully on books_full.jsonl records (Stage C), not Stage B's
    leaner entries_index records."""
    secs, ctypes, langs, slugs = _csv(a.section), _csv(a.ctype), _csv(a.lang), _csv(a.slug)
    out = []
    for r in records:
        if slugs and r.get("slug") not in slugs: continue
        if secs and not (set(r.get("sections", [])) & secs): continue
        if ctypes and r.get("ctype") not in ctypes: continue
        if langs and r.get("source_lang") not in langs: continue
        if a.english and not r.get("has_english"): continue
        if a.pali is True and not r.get("is_pali"): continue
        if a.pali is False and r.get("is_pali"): continue
        if a.min_words and (r.get("words") or 0) < a.min_words: continue
        out.append(r)
    shard = _parse_shard(getattr(a, "shard", None))
    if shard:
        k, n = shard
        out = [r for r in out if _shard_of(r.get("slug"), n) == k - 1]
    if a.limit:
        out = out[:a.limit]
    return out


async def stage_c(workers, a):
    """Download the chapter pages of the selected books into content/<slug>/.
    Resumable at page granularity: cached pages are validated against the
    expected doc manifest before a book is treated as complete."""
    src = HERE / "books_full.jsonl"
    if not src.exists():
        print("Run stageB first."); return
    recs = [json.loads(l) for l in src.open(encoding="utf-8") if l.strip()]
    recs = [r for r in recs if not r.get("fetch_failed")]
    chosen = select(recs, a)
    out_dir = HERE / a.out
    print(f"Stage C: {len(chosen)} of {len(recs)} books selected -> {out_dir.name}/, workers={workers}")
    if not chosen:
        return

    sem = asyncio.Semaphore(workers)
    lock = asyncio.Lock()
    docs_manifest_path = out_dir / DOCS_MANIFEST
    docs_manifest = _load_json(docs_manifest_path, {})
    stats = {
        "pages_written": 0,
        "blocked_landings": 0,
        "blocked_pages": 0,
        "invalid_cached_files_removed": 0,
        "pending_pages": 0,
        "selected_books": len(chosen),
    }

    async def docs_for(client, r):
        slug = r["slug"]
        bdir = out_dir / slug
        expected = docs_manifest.get(slug)
        if expected and r.get("chapter_count") and len(expected) < r["chapter_count"]:
            expected = None
        urls = _urls_from_expected(r, expected) if expected else []
        if not urls:
            async with sem:
                html = await fetch(client, r["url"])   # landing page -> full doc list
            if is_block_page(html):                    # blocked/empty -> leave for retry
                return {"slug": slug, "blocked": True, "docs": [], "invalid": 0}
            docs = _docs_from_landing(html)
            expected = [_doc_name(d) for d in docs]
            docs_manifest[slug] = expected
            urls = [BASE + d for d in docs]

        valid, invalid = _validate_cached_docs(bdir, expected)
        pending = [(slug, url) for url in urls if _doc_name(url) not in valid]
        return {"slug": slug, "blocked": False, "docs": pending, "invalid": invalid}

    async with new_client() as client:
        results = await asyncio.gather(*(docs_for(client, r) for r in chosen))
        out_dir.mkdir(parents=True, exist_ok=True)
        _save_json(docs_manifest_path, docs_manifest)
        pending = []
        for result in results:
            if result["blocked"]:
                stats["blocked_landings"] += 1
            stats["invalid_cached_files_removed"] += result["invalid"]
        for slug, url in (t for result in results for t in result["docs"]):
            f = out_dir / slug / url.rsplit("/", 1)[-1]
            pending.append((slug, url, f))
        stats["pending_pages"] = len(pending)
        print(f"  {len(pending)} chapter pages to fetch")
        if a.dry_run:
            for _, url, _f in pending[:50]:
                print("   ", url)
            print(f"  (dry-run; {len(pending)} total, nothing written)")
            _save_json(out_dir / LAST_RUN, stats)
            return

        # manifest so watch.py knows the denominator + can relaunch this selection
        (out_dir / "_manifest.json").write_text(json.dumps({
            "ts": time.time(), "argv": sys.argv[1:],
            "books": [[r["slug"], r.get("chapter_count") or 0] for r in chosen],
            "total_chapters": sum(r.get("chapter_count") or 0 for r in chosen),
        }), encoding="utf-8")

        async def grab(slug, url, f):
            async with sem:
                html = await fetch(client, url)
            if is_block_page(html):                    # don't cache a block/empty page
                async with lock:
                    stats["blocked_pages"] += 1
                return
            f.parent.mkdir(parents=True, exist_ok=True)
            # newline="" so raw HTML bytes are preserved verbatim (no CRLF translation)
            f.write_text(html, encoding="utf-8", newline="")
            async with lock:
                stats["pages_written"] += 1
                if stats["pages_written"] % 100 == 0:
                    print(f"  {stats['pages_written']}/{len(pending)}")
        await asyncio.gather(*(grab(s, u, f) for s, u, f in pending))
        stats["pending_pages"] = max(0, len(pending) - stats["pages_written"])
        _save_json(out_dir / LAST_RUN, stats)
        print(
            "Stage C done: "
            f"{stats['pages_written']} pages written, "
            f"{stats['blocked_landings']} blocked landings, "
            f"{stats['blocked_pages']} blocked/failed chapter pages, "
            f"{stats['invalid_cached_files_removed']} invalid cached files removed, "
            f"{stats['pending_pages']} pending pages -> {out_dir}/"
        )


def main():
    global DELAY
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["stageA", "stageB", "stageC", "report", "all"])
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--delay", type=float, default=0.0,
                    help="seconds between requests per worker (jittered); throttles rate")
    # shared selection filters (used by stageB and stageC)
    ap.add_argument("--section", action="append", help="section(s); repeatable or comma-list")
    ap.add_argument("--ctype", action="append", help="content type(s)")
    ap.add_argument("--lang", action="append", help="source_lang(s) (books_full only)")
    ap.add_argument("--slug", action="append", help="explicit slug(s)")
    ap.add_argument("--english", action="store_true", help="only entries with English translation")
    ap.add_argument("--pali", dest="pali", action="store_true", default=None, help="keep only Pali")
    ap.add_argument("--no-pali", dest="pali", action="store_false", help="drop Pali")
    ap.add_argument("--min-words", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--shard", help="k/n: fetch only shard k of n machines (stable by slug)")
    ap.add_argument("--impersonate", metavar="PROFILE",
                    help="curl_cffi browser TLS profile (e.g. chrome) — needs `pip install curl_cffi`")
    ap.add_argument("--out", default="content", help="stageC output dir")
    ap.add_argument("--dry-run", action="store_true", help="stageC: list, don't fetch")
    a = ap.parse_args()
    _parse_shard(a.shard)                  # validate early, fail fast on a bad spec
    global IMPERSONATE
    IMPERSONATE = a.impersonate or None
    DELAY = a.delay
    t0 = time.time()
    if a.stage in ("stageA", "all"):
        asyncio.run(stage_a(a.workers))
    if a.stage in ("stageB", "all"):
        asyncio.run(stage_b(a.workers, a))
    if a.stage in ("report", "all"):
        make_report()
    if a.stage == "stageC":
        asyncio.run(stage_c(a.workers, a))
    print(f"elapsed {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
