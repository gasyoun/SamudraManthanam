"""A41 data-descriptor statistics — reproducible re-derivation.

Recomputes every headline number in papers/A41_parallel_corpus_descriptor.md
from the committed artifacts (conversion_report.json + the live JSONL layer +
per-source meta.json), and builds the §5 Bhagavadgita per-edition table with
diachronic register metrics (aggregates only — no corpus text is emitted, per
the RU-translation rights gate).

Outputs (all under papers/data/ and papers/figures/):
  A41_corpus_stats.json      — full recomputation record (dated, self-describing)
  A41_gita_editions.tsv      — §5 per-edition translator/year/rights/metrics table
  A41_gita_register.svg      — register metrics vs. publication year (figure 1)

Run:  python papers/scripts/a41_stats.py   (from the repo root)
"""

import json
import math
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
JSONL_DIR = ROOT / "web" / "corpus_builder" / "jsonl"
REPORT = ROOT / "web" / "corpus_builder" / "conversion_report.json"
META_DIR = ROOT / "Index" / "lib" / "x86_64-win64" / "Data"
CORPUS_DB = ROOT / "web" / "corpus.db"
OUT_DATA = ROOT / "papers" / "data"
OUT_FIG = ROOT / "papers" / "figures"

# The 11 translation sources + 3 commentaries named in §5.
GITA_TRANSLATIONS = [
    "bhagavadgita-1788", "bhagavadgita-1909", "bhagavadgita-1914",
    "bhagavadgita-smirnov", "bhagavadgita-sementsov", "bhagavadgita-erman",
    "bhagavadgita-burba", "bhagavadgita-prabhupada", "bhagavadgita-radha",
    "bhagavadgita-sharma", "bhagavadgity",
]
GITA_COMMENTARIES = [
    "ramanuja_gitabhashya", "gitartha-samgraha_yamunacharya",
    "gitarthasamgraha-abhinavagupta",
]

# Transparent, fixed stem list for the Sanskrit-term retention metric:
# transliterated Sanskrit loans a Russian translator may either retain or
# translate away. Matched case-insensitively as substrings of RU verse text.
SANSKRIT_LOAN_STEMS = [
    "йог", "карм", "дхарм", "брахм", "атман", "гун", "майя", "майи",
    "мантр", "пракрит", "пуруш", "кшатри", "санньяс", "яджн", "бхакт",
    "мокш", "сансар", "риши",
]

TOKEN_RE = re.compile(r"[а-яё]+", re.IGNORECASE)


def load_jsonl(slug):
    recs = []
    with open(JSONL_DIR / f"{slug}.jsonl", encoding="utf-8") as f:
        for line in f:
            recs.append(json.loads(line))
    return recs


def verse_group_cardinality(slugs):
    """Per-group cardinality over verse sources: 1:1 / 0:1 / 1:0.

    A group is (work, passage); sides are the sa/ru segments with non-empty
    text (commentary segments are outside cardinality by design).
    """
    both = ru_only = sa_only = 0
    mono_ru_by_work = Counter()
    for slug in slugs:
        groups = defaultdict(lambda: {"sa": False, "ru": False})
        for r in load_jsonl(slug):
            seg = r.get("seg")
            if seg in ("sa", "ru") and (r.get("text") or "").strip():
                groups[r["passage"]][seg] = True
        for g in groups.values():
            if g["sa"] and g["ru"]:
                both += 1
            elif g["ru"]:
                ru_only += 1
                mono_ru_by_work[slug] += 1
            elif g["sa"]:
                sa_only += 1
    return both, ru_only, sa_only, mono_ru_by_work


def register_metrics(slug):
    """Aggregate register metrics over one edition's RU verse segments."""
    recs = load_jsonl(slug)
    passages = set()
    pair_passages = set()
    sides = defaultdict(lambda: {"sa": False, "ru": False})
    tokens = []
    loan_hits = 0
    ru_segs = 0
    for r in recs:
        seg = r.get("seg")
        if seg in ("sa", "ru") and (r.get("text") or "").strip():
            passages.add(r["passage"])
            sides[r["passage"]][seg] = True
        if seg == "ru" and (r.get("text") or "").strip():
            ru_segs += 1
            text = r["text"].lower()
            tokens.extend(TOKEN_RE.findall(text))
            if any(stem in text for stem in SANSKRIT_LOAN_STEMS):
                loan_hits += 1
    for p, s in sides.items():
        if s["sa"] and s["ru"]:
            pair_passages.add(p)
    n_tok = len(tokens)
    n_typ = len(set(tokens))
    return {
        "records": len(recs),
        "passages": len(passages),
        "clean_pairs": len(pair_passages),
        "ru_segments": ru_segs,
        "ru_tokens": n_tok,
        "ru_types": n_typ,
        "ttr": round(n_typ / n_tok, 4) if n_tok else None,
        "guiraud_r": round(n_typ / math.sqrt(n_tok), 2) if n_tok else None,
        "mean_ru_tokens_per_segment": round(n_tok / ru_segs, 2) if ru_segs else None,
        "loan_retention_rate": round(loan_hits / ru_segs, 4) if ru_segs else None,
    }


def read_meta(slug):
    p = META_DIR / f"{slug}.html.meta.json"
    if not p.exists():
        return {}
    m = json.loads(p.read_text(encoding="utf-8"))
    # The slug sometimes encodes the ORIGINAL edition year (bhagavadgita-1788)
    # while meta `year` is the digitised imprint (the 1914 reprint of Petrov's
    # 1788 translation). Keep both; the diachronic axis uses original-first.
    slug_year = None
    ym = re.search(r"(1[6-9]\d\d|20\d\d)$", slug)
    if ym:
        slug_year = int(ym.group(1))
    return {
        "title_en": m.get("title_en"),
        "credit": m.get("credit"),
        "imprint": m.get("imprint"),
        "year": m.get("year"),
        "orig_year": slug_year or m.get("year"),
        "rights": m.get("rights"),
    }


def main():
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    OUT_FIG.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    report = json.loads(REPORT.read_text(encoding="utf-8"))
    rep_slugs = [s["slug"] for s in report["sources"]]
    rep_by_slug = {s["slug"]: s for s in report["sources"]}

    # 1. Canonical report aggregates.
    by_structure = defaultdict(lambda: {"sources": 0, "records": 0})
    seg_totals = Counter()
    needs_review = 0
    for s in report["sources"]:
        by_structure[s["structure"]]["sources"] += 1
        by_structure[s["structure"]]["records"] += s["records"]
        needs_review += s.get("needs_review", 0)
        for k, v in s.get("seg_counts", {}).items():
            key = "comm" if k.startswith("comm") else k
            seg_totals[key] += v

    # 2. Live JSONL census: report sources vs. extras.
    disk_slugs = sorted(p.stem for p in JSONL_DIR.glob("*.jsonl"))
    extras = [s for s in disk_slugs if s not in rep_by_slug]
    extra_counts = {}
    for s in extras:
        extra_counts[s] = sum(1 for _ in open(JSONL_DIR / f"{s}.jsonl", encoding="utf-8"))
    live_records = 0
    unique_ids = set()
    for slug in rep_slugs:
        for r in load_jsonl(slug):
            live_records += 1
            unique_ids.add(r["id"])

    # 3. Verse-group cardinality (the headline recount).
    verse_slugs = [s["slug"] for s in report["sources"] if s["structure"] == "verse"]
    both, ru_only, sa_only, mono_by_work = verse_group_cardinality(verse_slugs)
    total_groups = both + ru_only + sa_only

    # 4. corpus.db view-layer numbers (reconciliation footnote ONLY).
    #
    # web/corpus.db is gitignored (742 MB runtime search view, built from the reading
    # HTML) and is NOT part of the corpus of record — §3.1 says so explicitly. It is
    # therefore absent (or a 0-byte stub) in any fresh clone or linked worktree, which
    # used to abort this whole script on `no such table: sources` and so falsified the
    # paper's "every statistic recomputes in one pass" claim from a clean checkout.
    # Degrade to None and report it: a missing footnote must not take the headline
    # numbers down with it. (H2403, 10-08-2026.)
    db_sources = db_lines = db_version = None
    db_status = "absent (gitignored runtime view; footnote skipped)"
    try:
        db = sqlite3.connect(f"file:{CORPUS_DB}?mode=ro", uri=True)
        try:
            db_sources = db.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
            db_lines = db.execute("SELECT COUNT(*) FROM corpus_lines").fetchone()[0]
            db_version = dict(
                db.execute("SELECT key, value FROM corpus_meta")
            ).get("corpus_version")
            db_status = "read"
        finally:
            db.close()
    except sqlite3.Error as exc:
        print(f"  ! corpus.db view layer unavailable ({exc}) — footnote fields null",
              file=sys.stderr)

    # 5. Gita per-edition table.
    editions = []
    for slug in GITA_TRANSLATIONS:
        row = {"slug": slug, "role": "translation", **read_meta(slug), **register_metrics(slug)}
        editions.append(row)
    for slug in GITA_COMMENTARIES:
        row = {"slug": slug, "role": "commentary", **read_meta(slug), **register_metrics(slug)}
        editions.append(row)

    stats = {
        "derived": today,
        "script": "papers/scripts/a41_stats.py",
        "report": {
            "total_sources": report["total_sources"],
            "total_records": report["total_records"],
            "by_structure": dict(by_structure),
            "seg_totals": dict(seg_totals),
            "needs_review_sum": needs_review,
        },
        "live_jsonl": {
            "files_on_disk": len(disk_slugs),
            "report_sources": len(rep_slugs),
            "post_report_extras": extra_counts,
            "extras_records_sum": sum(extra_counts.values()),
            "records_148_sources": live_records,
            "unique_ids_148_sources": len(unique_ids),
        },
        "verse_group_cardinality": {
            "clean_1_1": both,
            "ru_only_0_1": ru_only,
            "sa_only_1_0": sa_only,
            "total_groups": total_groups,
            "clean_share_pct": round(100 * both / total_groups, 2),
            "top_monolingual_sources": mono_by_work.most_common(5),
        },
        "corpus_db_view_layer": {
            "note": "web/corpus.db is the runtime search view built from the "
                    "reading HTML, NOT the canonical JSONL layer; its counts "
                    "include nav headings and post-report sources.",
            "status": db_status,
            "version": db_version,
            "sources": db_sources,
            "lines": db_lines,
        },
        "sanskrit_loan_stems": SANSKRIT_LOAN_STEMS,
        "gita_editions": editions,
    }
    out_json = OUT_DATA / "A41_corpus_stats.json"
    out_json.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_json.relative_to(ROOT)}")

    # TSV for the paper table.
    cols = ["slug", "role", "orig_year", "year", "credit", "rights", "passages",
            "clean_pairs", "ru_segments", "mean_ru_tokens_per_segment", "ttr",
            "guiraud_r", "loan_retention_rate"]
    out_tsv = OUT_DATA / "A41_gita_editions.tsv"
    with open(out_tsv, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(cols) + "\n")
        for e in editions:
            f.write("\t".join("" if e.get(c) is None else str(e.get(c)) for c in cols) + "\n")
    print(f"wrote {out_tsv.relative_to(ROOT)}")

    # Figure: register metrics vs. year, single datable editions only.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    datable = [e for e in editions
               if e["role"] == "translation" and e["slug"] != "bhagavadgity"
               and e.get("orig_year") and e.get("ttr")]
    datable.sort(key=lambda e: e["orig_year"])
    years = [e["orig_year"] for e in datable]
    labels = [e["slug"].replace("bhagavadgita-", "") for e in datable]
    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.plot(years, [e["loan_retention_rate"] * 100 for e in datable],
             "o-", color="#1a6091", label="Sanskrit-loan retention (% of RU segments)")
    ax1.set_xlabel("Original edition year (slug-encoded where present, else imprint)")
    ax1.set_ylabel("Loan retention, % of RU segments", color="#1a6091")
    ax1.tick_params(axis="y", labelcolor="#1a6091")
    ax2 = ax1.twinx()
    ax2.plot(years, [e["guiraud_r"] for e in datable],
             "s--", color="#b0413e", label="Guiraud R (lexical richness)")
    ax2.set_ylabel("Guiraud R = types/√tokens", color="#b0413e")
    ax2.tick_params(axis="y", labelcolor="#b0413e")
    for x, e, lab in zip(years, datable, labels):
        ax1.annotate(lab, (x, e["loan_retention_rate"] * 100),
                     textcoords="offset points", xytext=(0, 8), fontsize=7, rotation=30)
    ax1.set_title(f"Bhagavadgītā in Russian, {years[0]}–{years[-1]}: register metrics per edition\n"
                  f"(n = {len(datable)} single-edition sources, x = original edition year; "
                  f"derived {today} by papers/scripts/a41_stats.py)")
    fig.tight_layout()
    out_svg = OUT_FIG / "A41_gita_register.svg"
    fig.savefig(out_svg)
    print(f"wrote {out_svg.relative_to(ROOT)}")

    # Console summary for the paper edit.
    print("\n--- headline recount ---")
    print(f"148-source live records: {live_records:,} (unique ids {len(unique_ids):,})")
    print(f"verse groups: {total_groups:,} = 1:1 {both:,} + 0:1 {ru_only:,} + 1:0 {sa_only:,}"
          f" (clean {100 * both / total_groups:.2f}%)")
    print(f"extras on disk: {len(extras)} files, {sum(extra_counts.values()):,} records: {extras}")
    if db_lines is None:
        print(f"corpus.db view: {db_status}")
    else:
        print(f"corpus.db view: {db_sources} sources, {db_lines:,} lines ({db_version})")
    print("\n--- gita editions ---")
    for e in editions:
        print(f"{e['slug']:<38} {str(e.get('year')):<6} pairs={e['clean_pairs']:<5}"
              f" ru_seg={e['ru_segments']:<6} ttr={e.get('ttr')} R={e.get('guiraud_r')}"
              f" loans={e.get('loan_retention_rate')}")


if __name__ == "__main__":
    main()
