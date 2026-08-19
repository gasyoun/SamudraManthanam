#!/usr/bin/env python3
"""Vote sheet for the H759 3-path (A/B/C) НКРЯ lemma-adjudication sample (H789).

Regenerates the 51-group review sheet from the committed sample artifact
(nkrya-parallel/export/annotation_adjudication_sample.json) — the previous
sheet lived only in the gitignored `review/` directory and was lost. The
sample is stratified by B<->C Jaccard tertile (band low/mid/high); nothing is
screened out (H1649) because judging lemma-set quality on a specific verse is
exactly the human call this sample was drawn to collect, not something an
agent can pre-decide.

Usage:  python scripts/build_nkrya_adjudication_sheet.py
Output: review/samudramanthanam-nkrya-3path-lemma_adjudication51_review.html
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from csl_pyutil import render_review_sheet  # noqa: E402
from csl_pyutil.evidence import EvidenceManifest  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SAMPLE = os.path.join(REPO, "nkrya-parallel", "export", "annotation_adjudication_sample.json")
OUTDIR = os.path.join(REPO, "review")
SHEET_ID = "samudramanthanam-nkrya-3path-lemma_adjudication51"
SHEET = os.path.join(OUTDIR, f"{SHEET_ID}_review.html")
GENERATED = "19-08-2026"
BLOB = "https://github.com/gasyoun/SamudraManthanam/blob/main/"

BAND_LABEL = {"low": "низкий Jaccard", "mid": "средний Jaccard", "high": "высокий Jaccard"}


def esc(s):
    import html
    return html.escape(str(s), quote=True)


def lemma_chips(lemmas):
    if not lemmas:
        return '<span class="muted">— пусто —</span>'
    return "".join(f'<span class="chip">{esc(w)}</span>' for w in lemmas)


def build_item(row):
    group = row["group"]
    band = row["band"]
    jaccard = row["jaccard"]
    b_set, c_set = set(row["b_lemmas_iast"]), set(row["c_lemmas_iast"])
    shared = b_set & c_set
    return {
        "id": group,
        "filt": band,
        "title": group,
        "badges": [BAND_LABEL.get(band, band), f"Jaccard {jaccard:.2f}",
                   f"B {len(b_set)} / C {len(c_set)} / общих {len(shared)}"],
        "question": (
            "<p>Строка НКРЯ-параллельного корпуса (Sanskrit-side), путь A = "
            f"{esc(row['text_iast'])}</p>"
            "<p>Path B — DCS lemma+morph crosswalk; path C — vidyut fresh "
            "auto-tagging. Оцените, чей набор лемм точнее описывает эту "
            "строку.</p>"),
        "panels": [
            ("path B — DCS lemma crosswalk (n=%d)" % len(b_set), lemma_chips(sorted(b_set))),
            ("path C — vidyut auto-tag (n=%d)" % len(c_set), lemma_chips(sorted(c_set))),
        ],
        "note_placeholder": "Если ни один путь не верен целиком — опишите верную лемматизацию здесь.",
    }


def main():
    rows = json.load(open(SAMPLE, encoding="utf-8"))
    items = [build_item(r) for r in rows]

    manifest = EvidenceManifest(SHEET_ID, [i["id"] for i in items], repo_root=REPO)
    manifest.declare_joined("nkrya-parallel/export/annotation_adjudication_sample.json",
                            ["band", "group", "jaccard", "text_iast",
                             "b_lemmas_iast", "c_lemmas_iast"])
    manifest.declare_omitted(
        "nkrya-parallel/export/annotation_3path_metrics.json",
        "corpus-wide aggregate metrics, not a per-row source for these 51 groups")
    manifest.declare_omitted(
        "nkrya-parallel/export/ANNOTATION_3PATH_COMPARISON.md",
        "prose report summarizing the same measurement, not a joinable table")
    manifest.declare_omitted(
        "the gitignored per-source annotated TSV/JSONL bulk (H754/H759)",
        "in-copyright running text; the committed sample IS the citable artifact")
    for i in items:
        manifest.add_card(i["id"], ["band", "jaccard", "text_iast",
                                    "b_lemmas_iast", "c_lemmas_iast"])

    cfg = {
        "sheet_id": SHEET_ID,
        "title": "НКРЯ 3-path Sanskrit lemma adjudication (H759 -> A41 §6.4)",
        "subtitle": (f"{len(items)} verse groups, stratified by B<->C Jaccard "
                     "tertile (seed 759). Approve = B right/better · Reject = "
                     "B wrong / C better · Defer = both bad."),
        "footer": ("Approve = path B (DCS crosswalk) is right or better on this "
                   "verse. Reject = path B is wrong / path C (vidyut) is "
                   "better. Defer = both lemma sets are bad. Verdict folds "
                   "into A41 §6.4 and the vidyut-shipping decision."),
        "approve_label": "✅ B right/better",
        "reject_label": "❌ B wrong / C better",
        "filters": [("low", "низкий Jaccard"), ("mid", "средний Jaccard"),
                    ("high", "высокий Jaccard")],
        "generated": GENERATED,
        "show_ids": True,
        "note_min_height_px": 72,
        "save_as": r"SamudraManthanam\review\%s_decisions.json" % SHEET_ID,
        "preflight": {"overlap_threshold": 0.5},
    }
    screening = {
        "deterministic": 0,
        "lookup": 0,
        "agent": 0,
        "human": len(items),
        "evidence_path": "nkrya-parallel/export/annotation_adjudication_sample.json",
        "rules": [],
    }

    os.makedirs(OUTDIR, exist_ok=True)
    html_out = render_review_sheet(items, cfg, screening=screening, manifest=manifest)
    with open(SHEET, "w", encoding="utf-8") as fh:
        fh.write(html_out)
    print(f"{len(items)} cards -> {os.path.relpath(SHEET, REPO)}")


if __name__ == "__main__":
    main()
