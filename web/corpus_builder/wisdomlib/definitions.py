#!/usr/bin/env python3
"""wisdomlib per-word definition fetcher — tradition tags + English glosses.

Companion to crawl.py (the book/chapter crawler). This fetches the per-word
`/definition/<word>` pages, which the book crawler never touches, and extracts:
  - the TRADITION sections the word appears under (Buddhism / Jainism / Ayurveda /
    Vyakarana / Vedic / Vedanta / Hinduism / Sanskrit-dictionary), and
  - the count of English glosses.

Used downstream by RussianTranslation `enrich_renou_wisdomlib.py` as a tertiary,
lower-confidence Renou **V** (Buddhist/Jaina) hint, and as a Sanskrit→English
gloss reference.

Reuses crawl.py's polite fetch (browser headers, HTTP/2, Retry-After, the
`is_block_page` soft-200 block detector). robots.txt permits `/definition/`.

  python definitions.py fetch buddha skandha dharma     # fetch a few words
  python definitions.py batch words.txt [--delay 5]     # one word per line
  python definitions.py parse cached.html               # validate the parser on a saved page
  python definitions.py selftest                        # parser unit check (no network)

Rights: like the book content, cached HTML in definitions/ is gitignored and
provisional — do not redistribute. word_traditions.jsonl is metadata only.

NOTE (2026-06-24): wisdomlib content is Cloudflare-gated per-IP (see README
"Cloudflare reality"); run gently from a residential connection. The HTML parser
below is written to wisdomlib's documented <h2> tradition-heading structure and
should be VALIDATED with `parse` on the first real page before a bulk run.
"""
import asyncio, json, re, sys, html as ihtml, argparse, time
from pathlib import Path

import httpx
import crawl  # reuse: fetch(), HEADERS, is_block_page, BASE, HTTP2

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
CACHE = HERE / "definitions"          # gitignored raw-HTML cache
OUT = HERE / "word_traditions.jsonl"  # word -> {traditions, glosses, headings}

# tradition tag -> heading-text matcher. Order matters only for readability; a page
# may match several (a word can be both a Buddhist and a Hindu term).
TRADITIONS = [
    ("buddhism",  re.compile(r"buddh|mah[āa]y[āa]na|therav[āa]da|tibetan\s+budd", re.I)),
    ("jainism",   re.compile(r"jain", re.I)),
    ("ayurveda",  re.compile(r"[āa]yurveda|rasa[śs][āa]stra", re.I)),
    ("vyakarana", re.compile(r"vy[āa]kara[ṇn]a|\bgrammar\b", re.I)),
    ("vedic",     re.compile(r"\bvedic\b|vedic-hinduism", re.I)),
    ("vedanta",   re.compile(r"ved[āa]nta", re.I)),
    ("hinduism",  re.compile(r"hinduism|pur[āa][ṇn]a|itih[āa]sa|dharma[śs][āa]stra|k[āa]vya|yoga|[śs]aivism|vai[śs][ṇn]avism", re.I)),
    ("sanskrit_dict", re.compile(r"languages of india|sanskrit dictionary|sanskrit-english|\bkosha\b", re.I)),
]
H2 = re.compile(r"<h2\b[^>]*>(.*?)</h2>", re.S)
# each gloss carries a `class="suffix source"` attribution span — counting these is
# a faithful "how many English glosses" proxy (validated on a real page, 2026-06-24).
GLOSS = re.compile(r'class="suffix source"')


def _text(fragment):
    return ihtml.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def parse_definition(html):
    """-> {'traditions': [...], 'headings': [...], 'glosses': N}. Keyed on the page's
    <h2> tradition headings; defensive to markup variation."""
    headings = [_text(h) for h in H2.findall(html or "")]
    trads = []
    for h in headings:
        for tag, rx in TRADITIONS:
            if rx.search(h) and tag not in trads:
                trads.append(tag)
    return {"traditions": trads, "headings": headings,
            "glosses": len(GLOSS.findall(html or ""))}


async def _fetch_one(client, word):
    url = f"{crawl.BASE}/definition/{word}"
    html = await crawl.fetch(client, url)
    if html is None:
        return {"word": word, "error": "fetch_failed"}
    if crawl.is_block_page(html):
        return {"word": word, "error": "blocked"}
    (CACHE / f"{word}.html").write_text(html, encoding="utf-8", newline="")
    rec = {"word": word}
    rec.update(parse_definition(html))
    return rec


async def run_fetch(words, delay):
    CACHE.mkdir(parents=True, exist_ok=True)
    crawl.DELAY = delay
    done = set()
    if OUT.exists():
        for line in OUT.open(encoding="utf-8"):
            try:
                done.add(json.loads(line)["word"])
            except Exception:
                pass
    todo = [w for w in words if w not in done]
    print(f"fetch: {len(todo)} words ({len(done)} cached), delay={delay}s", file=sys.stderr)
    out = OUT.open("a", encoding="utf-8")
    blocked = 0
    # http2=False: wisdomlib drops HTTP/2 from non-residential egress (timeouts);
    # HTTP/1.1 gets through. workers=1 deliberately — wisdomlib is per-IP rate-limited; be gentle.
    async with httpx.AsyncClient(headers=crawl.HEADERS, http2=False) as client:
        for w in todo:
            rec = await _fetch_one(client, w)
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            if rec.get("error") == "blocked":
                blocked += 1
                if blocked >= 3:
                    print("  3 consecutive blocks — stopping (Cloudflare). Resume later "
                          "from a residential connection.", file=sys.stderr)
                    break
            else:
                blocked = 0
    out.close()


SAMPLE = (
    '<h1>Akshobhya</h1>'
    '<h2>Buddhism (Mahayana concepts)</h2><div class="suffix source">a Dhyani-Buddha</div>'
    '<h2>In Jainism</h2><div class="suffix source">a deity</div>'
    '<h2>Languages of India and abroad: Sanskrit dictionary</h2><div class="suffix source">immovable</div>'
)


def selftest():
    r = parse_definition(SAMPLE)
    assert r["traditions"] == ["buddhism", "jainism", "sanskrit_dict"], r
    assert r["glosses"] == 3, r
    print("selftest OK:", r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "batch", "parse", "selftest"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--delay", type=float, default=5.0)
    a = ap.parse_args()
    if a.cmd == "selftest":
        selftest()
    elif a.cmd == "parse":
        html = Path(a.args[0]).read_text(encoding="utf-8")
        print(json.dumps(parse_definition(html), ensure_ascii=False, indent=1))
    elif a.cmd == "fetch":
        asyncio.run(run_fetch(a.args, a.delay))
    elif a.cmd == "batch":
        words = [w.strip() for w in Path(a.args[0]).read_text(encoding="utf-8").splitlines() if w.strip()]
        asyncio.run(run_fetch(words, a.delay))


if __name__ == "__main__":
    main()
