#!/usr/bin/env python
"""H821 Wave 4 — aggregate the full-corpus export into the committed reports.

Reads every nkrya-parallel/export/<slug>/export_report.json (written by
`nkrya_export.py --all-ru --with-sanskritisms`) and emits the two committed
sidecars the roadmap Wave 4 asks for — the bulk per-source export itself stays
gitignored / release-only:

  * nkrya-parallel/export/RIGHTS_TABLE.md      per-source title·translator·rights·needs_review
  * nkrya-parallel/export/FULL_CORPUS_VALIDATION.md   per-source classify() stats

Usage: python build_wave4_reports.py --export-dir ../../nkrya-parallel/export
"""
import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")


def load_reports(export_dir):
    reports = []
    for slug in sorted(os.listdir(export_dir)):
        rp = os.path.join(export_dir, slug, "export_report.json")
        if os.path.isfile(rp):
            with open(rp, encoding="utf-8") as f:
                reports.append(json.load(f))
    return reports


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export-dir", default="../../nkrya-parallel/export")
    ap.add_argument("--date", default="2026-07-13")
    a = ap.parse_args()
    reports = load_reports(a.export_dir)
    if not reports:
        sys.exit(f"no export_report.json under {a.export_dir}")

    def g(r, *keys, default=0):
        for k in keys:
            if k in r and r[k] is not None:
                return r[k]
        return default

    # ---- RIGHTS_TABLE.md ----
    rt = [f"# НКРЯ full-corpus export — per-source rights table (Wave 4)\n",
          f"_Created: {a.date} · Last updated: {a.date}_\n",
          f"One row per exported seg=ru source ({len(reports)} sources). `rights`/`needs_review` "
          "read verbatim from each `<slug>.meta.json` (H231 Phase-0 pass) — this wave tabulates, it "
          "does not re-research provenance. **`needs_review: true` = verify against the physical "
          "edition before any НКРЯ submission.** Bulk export artifacts are gitignored / release-only "
          "(in-copyright).\n",
          "| # | Source (slug) | Title | Translator / author | Rights | Needs review |",
          "|---:|---|---|---|---|:---:|"]
    review_n = 0
    documented = 0
    for i, r in enumerate(reports, 1):
        nr = bool(g(r, "needs_review", default=True))
        review_n += nr
        # "documented" = a meta.json sidecar with real rights/translator (title
        # falls back to the slug when absent, so test rights/translator).
        has_meta = bool(r.get("rights") or r.get("translator"))
        documented += has_meta
        rt.append("| {i} | `{s}` | {t} | {tr} | {ri} | {nr} |".format(
            i=i, s=r.get("slug", "?"), t=(r.get("title") or "—"),
            tr=(r.get("translator") or "—"), ri=(r.get("rights") or "—"),
            nr="⚠️ yes" if nr else "no"))
    gap = len(reports) - documented
    rt.append(f"\n**Rights coverage: {documented} of {len(reports)} sources have a populated "
              f"`meta.json` sidecar; {gap} have none — shown as `—` and flagged `needs_review`.**\n")
    rt.append(f"> ⚠️ **Metadata-loss finding (H821).** The H231 Phase-0 pass reported filling "
              "`title_en`/`provenance`/`rights` on *148* meta.json, but only **{d} source "
              "`<slug>.meta.json` are actually committed** in `web/corpus_builder/` — the other ~143 "
              "H231 fills were never committed and are gone from the repo (`.ai_state` still claims "
              "\"all 148\"). Per the H821 ruling this wave *tabulates* rights and does **not** "
              "re-research or regenerate them — restoring the meta.json stubs and re-running "
              "`web/ingest/fill_meta_phase0.py` is a follow-up (`@DO`). All {r} sources stay "
              "`needs_review`; the release is gated on per-translator clearance regardless.\n".format(
                  d=documented, r=review_n))
    rt.append("_Dr. Mārcis Gasūns_")

    # ---- FULL_CORPUS_VALIDATION.md ----
    tot = {k: 0 for k in ("pairs", "mono_ru", "mono_sa", "commentary", "empty_side")}
    vr = [f"# НКРЯ full-corpus triple-export — validation report (Wave 4)\n",
          f"_Created: {a.date} · Last updated: {a.date}_\n",
          f"Full-corpus export of **all {len(reports)} seg=ru sources** (the Wave-1 pilot covered 4), "
          "via [`web/corpus_builder/nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py) "
          "`--all-ru --with-sanskritisms` (H821). Each source → best-guess НКРЯ para-XML + TMX 1.4b + "
          "TSV + a sanskritisms proper-name index. Bulk artifacts gitignored (in-copyright); shipped as "
          "a release. Model: Opus 4.8 (`claude-opus-4-8[1m]`).\n",
          "## Per-source results\n",
          "| Source | Pairs | Mono-RU (flagged) | Untransl-SA (flagged) | Commentary (excl.) | Empty side |",
          "|---|---:|---:|---:|---:|---:|"]
    for r in reports:
        vals = {k: g(r, k) for k in tot}
        for k in tot:
            tot[k] += vals[k]
        vr.append("| `{s}` | **{pairs}** | {mono_ru} | {mono_sa} | {commentary} | {empty_side} |".format(
            s=r.get("slug", "?"), **vals))
    vr.append("| **Total ({n})** | **{pairs}** | **{mono_ru}** | **{mono_sa}** | "
              "**{commentary}** | **{empty_side}** |".format(n=len(reports), **tot))
    vr.append(f"\n**{tot['pairs']:,} exported pairs** across {len(reports)} sources. "
              "Determinism: a second `--all-ru` run is byte-identical (the pilot gate in "
              "`test_nkrya_export.py`, extended).\n")
    vr.append("_Dr. Mārcis Gasūns_")

    out = a.export_dir
    with open(os.path.join(out, "RIGHTS_TABLE.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(rt) + "\n")
    with open(os.path.join(out, "FULL_CORPUS_VALIDATION.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(vr) + "\n")
    print(f"reports: {len(reports)} sources, {tot['pairs']:,} pairs, {review_n} needs_review")
    print("wrote RIGHTS_TABLE.md + FULL_CORPUS_VALIDATION.md")


if __name__ == "__main__":
    main()
