"""Generate per-source metadata skeletons (Phase 0, ROADMAP_2026_H2_DH_MOBILE.md).

For every corpus HTML file, write a sibling `<name>.meta.json` capturing the
bibliographic facts that can be extracted mechanically from the file header:

- title (first-line HTML comment, same source as the desktop app's captions)
- header fields: subtitle, editor/translator credit, imprint line
- year/publisher parsed from the imprint where the pattern is recognizable
- scripts actually present in the body (devanagari / iast / cyrillic / latin)
- slug (same derivation as the web app's stable URLs)

Fields that need a human eye (English title, translator normalization,
provenance, rights) are emitted empty with `needs_review: true` so a later
editing pass — human or model — can fill them without re-running extraction.

Existing meta.json files are NOT overwritten unless --force is given: hand
edits win over extraction.

Usage:
    python web/ingest/extract_source_meta.py --corpus-path Index/lib/x86_64-win64/Data
    python web/ingest/extract_source_meta.py --corpus-path ... --force
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.slug import derive_slug  # noqa: E402

SCHEMA_VERSION = 1

# First line of each corpus file: <!-- Title text --> (often with the legacy
# `--!>` typo for the closing marker).
_TITLE_COMMENT = re.compile(r"^<!--\s*(.*?)\s*--!?>")
_HEADER_DIV = re.compile(
    r'<div class="header (header_[a-z0-9_]+)">(.*?)</div>', re.DOTALL
)
_TAG = re.compile(r"<[^>]+>")
# Imprint like: М.: "Наука" ♦ 1989  /  СПб., 1993
_YEAR = re.compile(r"\b(1[89]\d\d|20[0-2]\d)\b")
_PUBLISHER = re.compile(r"[«\"]([^»\"]{2,40})[»\"]")

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_IAST = re.compile(r"[āīūṛṝḷḹṅñṭḍṇśṣṃḥĀĪŪṚṜḶḸṄÑṬḌṆŚṢṂḤ]")
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")


def detect_scripts(text: str) -> list[str]:
    found = []
    if _DEVANAGARI.search(text):
        found.append("devanagari")
    if _IAST.search(text):
        found.append("iast")
    if _CYRILLIC.search(text):
        found.append("cyrillic")
    return found


def extract_one(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    first_line = raw.split("\n", 1)[0]
    m = _TITLE_COMMENT.match(first_line)
    title = m.group(1) if m else ""

    headers: dict[str, str] = {}
    # Headers live in the first few KB; cap the scan so 30 MB epics stay fast.
    for cls, body in _HEADER_DIV.findall(raw[:20000]):
        text = _TAG.sub("", body).strip()
        if text and cls not in headers:
            headers[cls] = text

    imprint = headers.get("header_year", "")
    year_m = _YEAR.search(imprint) or _YEAR.search(title)
    pub_m = _PUBLISHER.search(imprint)

    # Body sample for script detection — skip the Russian annotation header,
    # sample from several offsets so a long Russian preface doesn't mask
    # Sanskrit further down.
    n = len(raw)
    sample = raw[:50000] + raw[n // 2:n // 2 + 50000] + raw[-50000:]

    return {
        "schema_version": SCHEMA_VERSION,
        "filename": path.name,
        "slug": derive_slug(path.name),
        "title_ru": title,
        "title_en": "",
        "subtitle": headers.get("header_2", ""),
        "credit": headers.get("header_5", ""),
        "credit_role": headers.get("header_4", ""),
        "imprint": imprint,
        "publisher": pub_m.group(1) if pub_m else "",
        "year": int(year_m.group(1)) if year_m else None,
        "scripts": detect_scripts(sample),
        "provenance": "",
        "rights": "",
        "needs_review": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-path", required=True)
    parser.add_argument("--force", action="store_true",
                        help="overwrite existing .meta.json files")
    args = parser.parse_args()

    corpus = Path(args.corpus_path)
    html_files = (sorted(corpus.glob("*.html")) + sorted(corpus.glob("*.htm"))
                  + sorted(corpus.glob("*.txt")))
    html_files = [p for p in html_files if not p.name.endswith(".no_tags")]
    if not html_files:
        print(f"No corpus files found under {corpus}", file=sys.stderr)
        return 1

    written = skipped = 0
    review_flags: list[str] = []
    for path in html_files:
        meta_path = path.with_suffix(path.suffix + ".meta.json")
        if meta_path.exists() and not args.force:
            skipped += 1
            continue
        meta = extract_one(path)
        # BOM pitfall: plain utf-8, never utf-8-sig.
        with open(meta_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        written += 1
        problems = []
        if not meta["title_ru"]:
            problems.append("no title")
        if not meta["year"]:
            problems.append("no year")
        if not meta["scripts"]:
            problems.append("no scripts detected")
        if problems:
            review_flags.append(f"  {path.name}: {', '.join(problems)}")

    print(f"meta.json written: {written}, skipped (existing): {skipped}")
    if review_flags:
        print(f"needs attention ({len(review_flags)}):")
        print("\n".join(review_flags))
    return 0


if __name__ == "__main__":
    sys.exit(main())
