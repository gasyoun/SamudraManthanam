"""Structural tag census of every corpus source file.

Phase-1 prerequisite (Session S2 — HTML→JSONL converter spec). Produces a
per-file inventory of the markup constructs the converter must handle, so the
converter spec is grounded in measured reality rather than the handful of files
seen so far.

For each source listed in corpus.db (in sort order) it records, by scanning the
raw file on disk:

  - basic shape: line count, byte size, extension, title-comment present
  - structural-tag counts: citation_block, range div, chapter_content, <H1>,
    endchapter span, <br>, footnote/note spans, <small>, comment_* anchors,
    chapter_N / chapter_NC anchors, bare id= occurrences
  - id landscape: how many lines carry an id=, distinct id count, format
    histogram (N, N.N, N.N-N, N.N.N, chapter_N, chapter_NC, other)
  - Vedic accent characters present (drives the accent-stripping rule)
  - a proposed structure class (verse | dictionary | prose) heuristic, for the
    meta.json `structure` field — flagged LOW-confidence where ambiguous

Outputs:
  docs/TAG_CENSUS.json  — full machine-readable record per file
  docs/TAG_CENSUS.md    — human summary table + aggregate rollups

Run:  cd web ; python ingest/tag_census.py
"""
import json
import os
import re
import sqlite3
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(HERE)
ROOT = os.path.dirname(WEB)
DATA_DIR = os.path.join(ROOT, "Index", "lib", "x86_64-win64", "Data")
DB_PATH = os.path.join(WEB, "corpus.db")
OUT_JSON = os.path.join(ROOT, "docs", "TAG_CENSUS.json")
OUT_MD = os.path.join(ROOT, "docs", "TAG_CENSUS.md")

# Structural markers (substring/regex counts over the raw file text).
_CITATION_BLOCK = re.compile(r'class=["\']citation_block["\']')
_RANGE_DIV = re.compile(r'class=["\']range["\']')
_CHAPTER_CONTENT = re.compile(r'class=["\']chapter_content["\']')
_H1 = re.compile(r"<H1>", re.IGNORECASE)
_ENDCHAPTER = re.compile(r'class=["\']endchapter["\']')
_BR = re.compile(r"<br\s*/?>", re.IGNORECASE)
_SMALL = re.compile(r"<small>", re.IGNORECASE)
_NOTE = re.compile(r'class=["\'][^"\']*(?:note|footnote|fn)[^"\']*["\']', re.IGNORECASE)
_COMMENT_ANCHOR = re.compile(r'id=["\']comment_[^"\']*["\']')
_CHAPTER_C_ANCHOR = re.compile(r'id=["\']chapter_\d+C["\']')
_CHAPTER_ANCHOR = re.compile(r'id=["\']chapter_\d+["\']')
_ID_ANY = re.compile(r'\sid=["\']([^"\']+)["\']')

# Vedic accent characters (the VEDIC_MAP keys in parse_html.py) + combining.
_VEDIC = "áàéèíìóòúùr̥̀́"

# id format classifier
_FMT = [
    ("N.N.N", re.compile(r"^\d+\.\d+\.\d+$")),
    ("N.N-N", re.compile(r"^\d+\.\d+-\d+$")),
    ("N.N", re.compile(r"^\d+\.\d+$")),
    ("chapter_NC", re.compile(r"^chapter_\d+C$")),
    ("chapter_N", re.compile(r"^chapter_\d+$")),
    ("comment_*", re.compile(r"^comment_")),
    ("N", re.compile(r"^\d+$")),
]


def classify_id(v: str) -> str:
    for name, rx in _FMT:
        if rx.match(v):
            return name
    return "other"


def guess_structure(slug: str, fmt: Counter, id_lines: int, n_lines: int) -> tuple[str, str]:
    """Heuristic A/B/C class. Returns (class, confidence)."""
    dict_markers = ("slovar", "dic_", "kewa", "kochergina", "kossovich", "knauer",
                    "warnemyr", "fasmer", "dsg", "toporov", "ramayana-3-slovar")
    if any(k in slug for k in dict_markers):
        return "dictionary", "high"
    verse_ids = fmt.get("N.N", 0) + fmt.get("N.N-N", 0) + fmt.get("N.N.N", 0) + fmt.get("N", 0)
    if n_lines and verse_ids / max(n_lines, 1) > 0.25:
        return "verse", "high"
    if verse_ids > 0 and id_lines > 0:
        return "verse", "low"
    return "prose", "low"


def census_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    lines = raw.splitlines()
    n_lines = len(lines)

    ids = _ID_ANY.findall(raw)
    fmt = Counter(classify_id(v) for v in ids)
    distinct_ids = len(set(ids))

    vedic_present = sorted({ch for ch in _VEDIC if ch in raw})

    rec = {
        "n_lines": n_lines,
        "bytes": len(raw.encode("utf-8")),
        "ext": os.path.splitext(path)[1].lower(),
        "title_comment": bool(lines) and lines[0].lstrip().startswith("<!--"),
        "tags": {
            "citation_block": len(_CITATION_BLOCK.findall(raw)),
            "range_div": len(_RANGE_DIV.findall(raw)),
            "chapter_content": len(_CHAPTER_CONTENT.findall(raw)),
            "h1": len(_H1.findall(raw)),
            "endchapter": len(_ENDCHAPTER.findall(raw)),
            "br": len(_BR.findall(raw)),
            "small": len(_SMALL.findall(raw)),
            "note_like": len(_NOTE.findall(raw)),
            "comment_anchor": len(_COMMENT_ANCHOR.findall(raw)),
            "chapter_C_anchor": len(_CHAPTER_C_ANCHOR.findall(raw)),
            "chapter_anchor": len(_CHAPTER_ANCHOR.findall(raw)),
            "id_total": len(ids),
        },
        "id_distinct": distinct_ids,
        "id_formats": dict(fmt),
        "vedic_accents": vedic_present,
    }
    return rec, fmt


def main() -> None:
    db = sqlite3.connect(DB_PATH)
    sources = db.execute("SELECT filename, slug FROM sources ORDER BY sort_order").fetchall()

    records = []
    agg_tags = Counter()
    agg_fmt = Counter()
    class_counts = Counter()
    flags = []

    for filename, slug in sources:
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            flags.append((slug, "FILE MISSING ON DISK"))
            continue
        rec, fmt = census_file(path)
        cls, conf = guess_structure(slug, fmt, rec["tags"]["id_total"], rec["n_lines"])
        rec["filename"] = filename
        rec["slug"] = slug
        rec["structure_guess"] = cls
        rec["structure_confidence"] = conf
        records.append(rec)
        agg_tags.update(rec["tags"])
        agg_fmt.update(fmt)
        class_counts[cls] += 1

        # Converter-risk flags worth surfacing for S2.
        if rec["tags"]["range_div"] and not rec["tags"]["citation_block"]:
            flags.append((slug, "range div without citation_block (older markup path)"))
        if rec["tags"]["comment_anchor"] or rec["tags"]["chapter_C_anchor"]:
            flags.append((slug, "commentary anchors (comment_* / chapter_NC)"))
        if rec["tags"]["id_total"] == 0:
            flags.append((slug, "no id= anchors at all"))
        if conf == "low":
            flags.append((slug, f"LOW-confidence structure guess = {cls}"))

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"sources": records, "aggregate_tags": dict(agg_tags),
                   "aggregate_id_formats": dict(agg_fmt),
                   "class_counts": dict(class_counts)}, f, ensure_ascii=False, indent=2)

    # Markdown summary.
    lines = []
    lines.append("# Tag Census — corpus structural inventory\n")
    lines.append(f"_Generated by `web/ingest/tag_census.py` over {len(records)} sources._\n")
    lines.append("Prerequisite for Session S2 (HTML→JSONL converter spec). "
                 "See `docs/DESIGN_SESSIONS_PLAN.md`.\n")

    lines.append("## Aggregate structure classes (heuristic)\n")
    for cls in ("verse", "dictionary", "prose"):
        lines.append(f"- **{cls}**: {class_counts.get(cls, 0)}")
    lines.append("")

    lines.append("## Aggregate tag counts (whole corpus)\n")
    lines.append("| Tag / marker | Total occurrences | Sources using it |")
    lines.append("|---|---:|---:|")
    for tag in ("citation_block", "range_div", "chapter_content", "h1", "endchapter",
                "br", "small", "note_like", "comment_anchor", "chapter_C_anchor",
                "chapter_anchor", "id_total"):
        users = sum(1 for r in records if r["tags"].get(tag, 0) > 0)
        lines.append(f"| {tag} | {agg_tags.get(tag, 0):,} | {users} |")
    lines.append("")

    lines.append("## Aggregate id-format histogram\n")
    lines.append("| Format | Count |")
    lines.append("|---|---:|")
    for k, v in sorted(agg_fmt.items(), key=lambda x: -x[1]):
        lines.append(f"| `{k}` | {v:,} |")
    lines.append("")

    lines.append("## Converter-risk flags (sources needing explicit handling)\n")
    if flags:
        lines.append("| Source | Flag |")
        lines.append("|---|---|")
        for slug, msg in flags:
            lines.append(f"| `{slug}` | {msg} |")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("## Per-source detail\n")
    lines.append("| Source | ext | lines | id= | distinct id | cite | range | H1 | "
                 "note | vedic | class (conf) |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|---|")
    for r in records:
        t = r["tags"]
        vedic = "✓" if r["vedic_accents"] else ""
        lines.append(
            f"| `{r['slug']}` | {r['ext']} | {r['n_lines']:,} | {t['id_total']:,} | "
            f"{r['id_distinct']:,} | {t['citation_block']:,} | {t['range_div']:,} | "
            f"{t['h1']} | {t['note_like']} | {vedic} | "
            f"{r['structure_guess']} ({r['structure_confidence']}) |"
        )
    lines.append("")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print(f"Classes: {dict(class_counts)}")
    print(f"Flags: {len(flags)}")


if __name__ == "__main__":
    main()
