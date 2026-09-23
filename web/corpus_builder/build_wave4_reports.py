#!/usr/bin/env python
"""H821 Wave 4 — aggregate the full-corpus export into the committed reports.

Reads every nkrya-parallel/export/<slug>/export_report.json (written by
`nkrya_export.py --all-ru --with-sanskritisms`) and emits the two committed
sidecars the roadmap Wave 4 asks for — the bulk per-source export itself stays
gitignored / release-only:

  * nkrya-parallel/export/RIGHTS_TABLE.md      per-source title·translator·year·publisher·rights
    (H5281: title/translator/year/publisher/rights come from the MERGED meta —
    nkrya_export.load_meta: Index/lib Data meta <- corpus_builder sidecar <-
    showcase bibliography — not from the export_report, which only ever saw
    the 54 sidecars and left 127/131 rows translator-less)
  * nkrya-parallel/export/FULL_CORPUS_VALIDATION.md   per-source classify() stats

Usage: python build_wave4_reports.py --export-dir ../../nkrya-parallel/export
"""
import argparse
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nkrya_export as nx  # noqa: E402

SHIP_ALL_NOTE = ("ship-all RU (MG 08-08-2026 H2440) — document translator; "
                 "no per-translator ship gate")


def rights_cell(rights):
    base = (rights or "").strip() or "in-copyright / grey residual"
    base = re.sub(r"\s*—\s*corpus rights stay grey per project ruling; no redistribution"
                  r"(?:, export bulk gitignored)?", "", base)
    base = re.sub(r"\s*—\s*no redistribution.*$", "", base)
    return f"{base} · {SHIP_ALL_NOTE}"


def cell(v):
    return str(v).replace("|", "/").strip() if v not in (None, "") else "—"


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
    ap.add_argument("--created", default="13-07-2026")
    ap.add_argument("--date", default="23-09-2026", help="Last updated (DD-MM-YYYY)")
    ap.add_argument("--frozen-set", metavar="VALIDATION_MD",
                    help="restrict to the sources listed in a committed FULL_CORPUS_VALIDATION.md "
                         "(the Wave-4 freeze), write RIGHTS_TABLE.md only, and fail if any pair "
                         "count drifted from that report (H5281)")
    ap.add_argument("--out-dir", help="where to write the .md reports (default: --export-dir)")
    a = ap.parse_args()
    reports = load_reports(a.export_dir)
    if not reports:
        sys.exit(f"no export_report.json under {a.export_dir}")
    frozen = None
    if a.frozen_set:
        rows = re.findall(r"^\| `([^`]+)` \| \*\*(\d+)\*\*", open(a.frozen_set, encoding="utf-8").read(), re.M)
        frozen = {s: int(n) for s, n in rows}
        reports = [r for r in reports if r.get("slug") in frozen]
        drift = [(r["slug"], frozen[r["slug"]], r["pairs"]) for r in reports if r["pairs"] != frozen[r["slug"]]]
        missing = sorted(set(frozen) - {r["slug"] for r in reports})
        if drift or missing:
            sys.exit(f"frozen-set mismatch: drift={drift} missing={missing}")

    def g(r, *keys, default=0):
        for k in keys:
            if k in r and r[k] is not None:
                return r[k]
        return default

    # ---- RIGHTS_TABLE.md ----
    showcase = set(nx.SHOWCASE_SOURCES)
    rt = [f"# НКРЯ full-corpus export — per-source rights table (Wave 4)\n",
          f"_Created: {a.created} · Last updated: {a.date}_\n",
          "**Policy (MG 08-08-2026, H2440):** **ship all** Russian text; **never reask** a "
          "per-translator ship gate. This table **documents translators** (and residual "
          "attribution gaps).\n",
          f"One row per exported seg=ru source ({len(reports)} sources). Title, translator, "
          "year, publisher and rights come from the merged per-source meta "
          "([`nkrya_export.load_meta`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py): "
          "desktop `Index/lib/x86_64-win64/Data/<slug>.html.meta.json` ← curated "
          "`web/corpus_builder/<slug>.meta.json` ← the H5281 showcase bibliography "
          "[`nkrya_showcase_bib.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_showcase_bib.json)). "
          "Raw meta credits are shown verbatim (some in the genitive, as printed); the 24 "
          "showcase rows (🪟) carry the curated nominative form. `Year` = the printing the "
          "text was taken from. Bulk export artifacts are gitignored / release-only.\n",
          "| # | Source (slug) | Title | Translator / author | Year | Publisher | Rights | Needs review |",
          "|---:|---|---|---|---:|---|---|:---:|"]
    review_n = documented = 0
    for i, r in enumerate(reports, 1):
        slug = r.get("slug", "?")
        m = nx.load_meta(slug)
        b = m.get("nkrya") or {}
        title = b.get("headers_all") or m.get("title_ru") or slug
        tr = b.get("translator") or (m.get("credit") or "").strip()
        documented += bool(tr)
        nr = bool(m.get("needs_review", True))
        review_n += nr
        mark = "🪟 " if slug in showcase else ""
        rt.append("| {i} | {mk}`{s}` | {t} | {tr} | {y} | {pb} | {ri} | {nr} |".format(
            i=i, mk=mark, s=slug, t=cell(title), tr=cell(tr), y=cell(m.get("year")),
            pb=cell(b.get("publisher") or m.get("publisher")), ri=cell(rights_cell(m.get("rights"))),
            nr=("🗳 spot-check sheet" if slug in showcase else "⚠️ yes") if nr else "no"))
    gap = len(reports) - documented
    rt.append(f"\n**Translator coverage: {documented} of {len(reports)} sources carry a "
              f"translator/author credit; {gap} show `—` (the meta files' own gap — no "
              "credit on the title page parsed by the desktop meta pass).**\n")
    rt.append("> **Metadata-loss finding (H821) — resolved by H5281.** H821 read only the "
              "`web/corpus_builder/<slug>.meta.json` sidecars (then 4 of 131) and concluded ~143 "
              "H231 fills were lost. They were not: the desktop client's "
              "`Index/lib/x86_64-win64/Data/*.meta.json` (231 files, `credit` on 204) had them all "
              "along; the table builder read the wrong place.\n")
    rt.append("_Dr. Mārcis Gasūns_")

    # ---- FULL_CORPUS_VALIDATION.md ----
    tot = {k: 0 for k in ("pairs", "mono_ru", "mono_sa", "commentary", "empty_side")}
    vr = [f"# НКРЯ full-corpus triple-export — validation report (Wave 4)\n",
          f"_Created: {a.created} · Last updated: {a.date}_\n",
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

    out = a.out_dir or a.export_dir
    with open(os.path.join(out, "RIGHTS_TABLE.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(rt) + "\n")
    if frozen is None:
        with open(os.path.join(out, "FULL_CORPUS_VALIDATION.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(vr) + "\n")
    else:
        print(f"frozen set: {len(reports)} sources, pair counts match {a.frozen_set}")
    print(f"reports: {len(reports)} sources, {tot['pairs']:,} pairs, {review_n} needs_review")
    print("wrote RIGHTS_TABLE.md" + ("" if frozen is not None else " + FULL_CORPUS_VALIDATION.md"))


if __name__ == "__main__":
    main()
