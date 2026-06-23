"""Build ``works_index.json`` — a size-and-chronology index of the parallel
Sanskrit–Russian corpus, the data layer behind the ``/works`` page.

This is a *follow-on* to ``corpus_builder/chronology/build_chronology.py``: it
does not re-date anything. It reads the crosswalk that builder already produced
(``chronology/texts_chronology.json``), keeps only the ``parallel-ru`` corpus
(the works on samskrtam.ru/parallel-corpus), and enriches each work with:

* **size 1–10** — a logarithmic measure of *text volume*. Volume is the number
  of Sanskrit characters in a work (sum over its ``lang == "sa"`` segments in
  ``corpus_builder/jsonl/<member>.jsonl``); works with effectively no Sanskrit
  (a few Russian-only modern studies) fall back to their total character count
  so they still get a size. The log scale spans the smallest single *part* to
  the largest whole *work* (the Mahābhārata), so a part and a work are directly
  comparable: 1 = a short hymn/Upaniṣad, 10 = Mahābhārata-scale.
* **two views of the same data** — a work carries its summed size *and* a
  ``parts`` list, each part with its own date (inherited from the work),
  period, and independently-computed size. The page renders the merged works
  and the separate parts side by side.
* **links** — ``live_url`` points at the live reading page for the text
  (``/sources/{slug}``); ``timeline_url`` jumps to that work on ``/chronology``.

Run (from ``web/``)::

    python corpus_builder/works_index/build_works_index.py

Emits ``works_index.json`` (read once + cached by ``app/routers/works.py``) and
``works_index_report.md`` (a human-readable audit) next to this script. Reading
the ~530 MB of jsonl takes ~1 min; this is a one-time build, committed to git.
"""
import json
import math
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# works_index/ -> corpus_builder/ -> web/
_HERE = os.path.dirname(os.path.abspath(__file__))
_BUILDER_DIR = os.path.dirname(_HERE)
_CHRONO = os.path.join(_BUILDER_DIR, "chronology", "texts_chronology.json")
_JSONL_DIR = os.path.join(_BUILDER_DIR, "jsonl")
_OUT_JSON = os.path.join(_HERE, "works_index.json")
_OUT_REPORT = os.path.join(_HERE, "works_index_report.md")

# Fast-path marker: only Sanskrit segment lines are JSON-parsed for the volume
# measure. The jsonl writer emits `"lang": "sa"` with a space after the colon
# (verified against the committed files); match defensively either way.
_SA_MARKERS = ('"lang": "sa"', '"lang":"sa"')

# Slug derivation must match app/services/slug.py exactly so `live_url` lands on
# the real /sources/{slug} route. Duplicated (not imported) to keep this builder
# runnable without the FastAPI app package on sys.path.
_EXT = re.compile(r"\.(?:html?|txt|xml)$", re.IGNORECASE)
_NORM = re.compile(r"[^a-z0-9_]+")
_CYR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def derive_slug(filename: str) -> str:
    if not filename:
        return ""
    base = _EXT.sub("", filename)
    base = "".join(_CYR.get(c.lower(), c) for c in base).lower()
    return _NORM.sub("-", base).strip("-")


def measure_member(member: str) -> tuple[int, int, int, int]:
    """Return ``(sa_chars, sa_segs, total_chars, total_segs)`` for one jsonl
    member. Sanskrit volume is the primary signal; the totals are a fallback
    for Russian-only sources. Missing file → all zeros (logged by caller)."""
    path = os.path.join(_JSONL_DIR, f"{member}.jsonl")
    if not os.path.exists(path):
        return (0, 0, 0, 0)
    sa_chars = sa_segs = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not any(m in line for m in _SA_MARKERS):
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("lang") != "sa" or rec.get("deleted"):
                continue
            sa_chars += len(rec.get("text") or "")
            sa_segs += 1
    if sa_chars:
        return (sa_chars, sa_segs, sa_chars, sa_segs)
    # Russian-only work: second pass over every non-deleted record so the work
    # still gets an honest volume rather than a zero.
    total_chars = total_segs = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("deleted"):
                continue
            total_chars += len(rec.get("text") or "")
            total_segs += 1
    return (0, 0, total_chars, total_segs)


def part_label(member: str, group: str, work_title: str) -> str:
    """Human label for a part: the work's IAST title plus the part's
    distinguishing suffix (parva/maṇḍala/translator), derived from the member
    slug. Multi-part works disambiguate by suffix; single-part works are just
    the work title."""
    s = re.sub(r"^\d+[_-]?", "", member)              # drop leading "06_"
    lead = re.match(r"^(\d+)", member)
    if group:
        s = re.sub(rf"^{re.escape(group)}[_-]?", "", s, flags=re.IGNORECASE)
    suffix = s.replace("_", " ").replace("-", " ").strip()
    if not suffix and lead:                            # e.g. maṇḍala number
        suffix = lead.group(1)
    if not suffix:
        return work_title
    return f"{work_title} — {suffix[:1].upper() + suffix[1:]}"


# Literary kinds set the scale: the Mahābhārata (largest primary work) anchors
# 10 and the tiniest Upaniṣad anchors 1, so the chronology reads naturally.
# Reference works (dictionaries) genuinely carry more Sanskrit than the epics —
# they clamp at 10 rather than pushing the literature down the scale.
_LITERARY = {"primary", "commentary", "historical-source"}


def log_scale(volume: int, vmin: int, vmax: int):
    """Map a Sanskrit-character volume onto an integer 1–10 by log10. Returns
    None for a work with no Sanskrit (Russian-only studies — not a Sanskrit
    text to size). Clamps protect the degenerate single-value domain and let
    reference works that exceed the literary max sit at 10."""
    if volume <= 0:
        return None
    if vmax <= vmin:
        return 1
    lo, hi = math.log10(max(vmin, 1)), math.log10(vmax)
    if hi <= lo:
        return 1
    frac = (math.log10(volume) - lo) / (hi - lo)
    return max(1, min(10, round(1 + 9 * frac)))


def main() -> int:
    with open(_CHRONO, encoding="utf-8") as f:
        chrono = json.load(f)

    period_order = {p["period"]: i for i, p in enumerate(chrono["periods"])}
    bucket_date = {p["period"]: p.get("bucket_date") for p in chrono["periods"]}

    works_raw = [t for t in chrono["texts"] if t.get("corpus") == "parallel-ru"]

    # Pass 1: measure every member, accumulate per-work volume + per-part data.
    missing: list[str] = []
    works = []
    for w in works_raw:
        members = w.get("members") or [w["slug"]]
        group = w.get("group") or w["slug"]
        parts = []
        w_sa_chars = w_sa_segs = w_chars = w_segs = 0
        for m in members:
            sa_c, sa_s, tot_c, tot_s = measure_member(m)
            if not os.path.exists(os.path.join(_JSONL_DIR, f"{m}.jsonl")):
                missing.append(m)
            # Size is a Sanskrit-volume measure: parts are sized by their
            # Sanskrit characters only (Russian-only parts → unsized).
            parts.append({
                "member": m,
                "slug": derive_slug(m),
                "title": part_label(m, group, w["title"]),
                "sa_chars": sa_c,
                "sa_segs": sa_s,
                "volume": sa_c,
                "live_url": f"/sources/{derive_slug(m)}",
            })
            w_sa_chars += sa_c
            w_sa_segs += sa_s
            w_chars += tot_c
            w_segs += tot_s
        works.append({
            "raw": w,
            "parts": parts,
            "volume": w_sa_chars,
            "sa_chars": w_sa_chars,
            "sa_segs": w_sa_segs,
        })

    # Scale domain: smallest literary part → largest whole literary work
    # (Mahābhārata). Restricting the domain to literary kinds keeps the epics at
    # the top (10) instead of letting the Monier-Williams dictionary set the
    # ceiling; reference works larger than the epics simply clamp at 10.
    part_vols = [p["volume"] for w in works for p in w["parts"]
                 if p["volume"] > 0 and w["raw"].get("kind") in _LITERARY]
    work_vols = [w["volume"] for w in works
                 if w["volume"] > 0 and w["raw"].get("kind") in _LITERARY]
    vmin = min(part_vols) if part_vols else 1
    vmax = max(work_vols) if work_vols else 1

    # Pass 2: assign sizes + assemble the output rows.
    out_works = []
    for w in works:
        r = w["raw"]
        for p in w["parts"]:
            p["size"] = log_scale(p["volume"], vmin, vmax)
        out_works.append({
            "slug": r["slug"],
            "title": r["title"],
            "ru_title": r.get("ru_title"),
            "period": r.get("period"),
            "date_ce": r.get("date_ce"),
            "confidence": r.get("confidence"),
            "method": r.get("method"),
            "kind": r.get("kind"),
            "dcs_match": r.get("dcs_match"),
            "size": log_scale(w["volume"], vmin, vmax),
            "sa_chars": w["sa_chars"],
            "sa_segs": w["sa_segs"],
            "n_parts": len(w["parts"]),
            "live_url": w["parts"][0]["live_url"] if w["parts"] else None,
            "timeline_url": f"/chronology?focus={r['slug']}",
            "parts": [
                {k: p[k] for k in
                 ("slug", "title", "size", "sa_chars", "sa_segs", "live_url")}
                for p in w["parts"]
            ],
        })

    # Sort: by period (chronological bucket order), then by date, then size desc.
    # Undated works (dictionaries, modern studies) sort last via a sentinel.
    def sort_key(w):
        po = period_order.get(w["period"], 999)
        d = w["date_ce"] if w["date_ce"] is not None else 10_000
        return (po, d, -(w["size"] or 0), w["title"])

    out_works.sort(key=sort_key)

    out = {
        "about": (
            "Size-and-chronology index of the parallel Sanskrit–Russian corpus. "
            "Dates are inherited from chronology/texts_chronology.json (VisualDCS); "
            "size 1–10 is log10 of Sanskrit text volume, parts and works on one scale."
        ),
        "scale": {
            "metric": "sanskrit_chars",
            "transform": "log10",
            "domain_min": vmin,
            "domain_max": vmax,
            "domain_note": "smallest literary part to largest whole literary "
                           "work (Mahābhārata); reference works clamp at 10",
        },
        "periods": [
            {"period": p["period"], "bucket_date": bucket_date.get(p["period"])}
            for p in chrono["periods"]
        ],
        "n_works": len(out_works),
        "n_parts": sum(w["n_parts"] for w in out_works),
        "works": out_works,
    }
    with open(_OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # Audit report.
    dated = sum(1 for w in out_works if w["date_ce"] is not None)
    lines = [
        "# Works index — build report", "",
        f"- Works (parallel-ru): **{len(out_works)}** ({dated} dated, "
        f"{len(out_works) - dated} undated)",
        f"- Parts (members): **{out['n_parts']}**",
        f"- Size scale: log10 of Sanskrit chars, domain "
        f"[{vmin:,} … {vmax:,}] → 1…10",
        f"- Missing jsonl files: **{len(missing)}**"
        + (f" ({', '.join(missing)})" if missing else ""),
        "", "## Works by size", "",
        "| size | parts | Sanskrit segs | period | date | work |",
        "|----:|----:|----:|---|---:|---|",
    ]
    for w in sorted(out_works, key=lambda x: (-(x["size"] or 0), x["title"])):
        d = w["date_ce"]
        ds = "—" if d is None else (f"{-d} BCE" if d < 0 else f"{d} CE")
        lines.append(
            f"| {w['size'] if w['size'] is not None else '—'} | {w['n_parts']} "
            f"| {w['sa_segs']:,} | {w['period'] or '—'} | {ds} | {w['title']} |"
        )
    with open(_OUT_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"works_index.json: {len(out_works)} works, {out['n_parts']} parts")
    print(f"size domain (sa chars): {vmin:,} … {vmax:,}")
    if missing:
        print(f"WARNING: {len(missing)} missing jsonl: {missing}")
    print(f"wrote {_OUT_JSON}")
    print(f"wrote {_OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
