#!/usr/bin/env python3
"""Join the kosha `cyrillic-proper-noun-slp1` table into the SamudraManthanam
name glossaries (H4715, xwalk-a10).

The five Russian proper-noun glossaries under Index/lib/x86_64-win64/Data/ are
the seed sources of the sanctioned Cyrillic->SLP1 lookup table (built by
SanskritLexicography H3985). This builder keys each glossary entry that the
table covers with its validated SLP1 key, emitting:

  reports/name_glossary_slp1_joined.tsv        joined keying rows
  reports/name_glossary_slp1_join_report.json  census + 15-name sample verify

Rights guard: the glossaries are in-copyright academic editions ("no
redistribution" per their .meta.json), so the joined output carries ONLY
identifiers, keys and validation metadata -- never the Russian gloss text.

Usage:
  python3 scripts/build_name_glossary_slp1_join.py            # build
  python3 scripts/build_name_glossary_slp1_join.py --check    # byte-parity gate

Table location: env CYR_SLP1_TSV overrides, else the sibling-repo default.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from datetime import date, datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, "Index", "lib", "x86_64-win64", "Data")
DEFAULT_TABLE = os.path.join(
    os.path.dirname(REPO),
    "SanskritLexicography", "RussianTranslation", "data",
    "cyrillic_proper_noun_slp1.tsv",
)
OUT_TSV = os.path.join(REPO, "reports", "name_glossary_slp1_joined.tsv")
OUT_JSON = os.path.join(REPO, "reports", "name_glossary_slp1_join_report.json")

# slug -> glossary filename (the five Cyrillic proper-noun name glossaries)
GLOSSARIES = [
    ("ramayana3", "Рамаяна 3. Словарь.txt"),
    ("grintser-kadambari", "Словарь Гринцера из Бада Кадамбари.txt"),
    ("grintser-ramayana12", "Словарь Гринцера из Рамаяны 1-2.txt"),
    ("potapova", "Словарь Потаповой.txt"),
    ("smirnov", "Словарь Смирнова.txt"),
]

TSV_FIELDS = [
    "glossary_slug", "cyrillic", "slp1", "iast_witness",
    "validation", "onomasticon", "witness_count", "iast_inline",
]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_iast_span(text: str) -> str:
    """Leading IAST witness from the first parenthesised span, cut at the
    em-dash that separates it from a Russian gloss/etymology. Never returns
    free running text -- identifiers only."""
    m = re.search(r"\(([^)]*)\)", text)
    if not m:
        return ""
    span = m.group(1)
    # Rights guard: editions sometimes parenthesise a Russian gloss/synonym
    # (Потапова) or append editorial notes («или Tāṭakā», «этимология не ясна»).
    # Any Cyrillic in the span means it is NOT a pure IAST witness — suppress
    # it entirely; the authoritative witness lives in the kosha table.
    if any("\u0400" <= c <= "\u04FF" for c in span):
        return ""
    for cut in (" — ", "—", " – ", "–"):
        if cut in span:
            span = span.split(cut, 1)[0]
            break
    return span.strip().strip("«»\"'").strip()


def fold(s: str) -> str:
    """Diacritic/case-folded comparison key for IAST strings."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def parse_glossary(path: str):
    """Yield (headword, iast_inline, lineno) per glossary entry.

    Two house formats: TAB-separated headword, or space-separated with the
    inline IAST in the first parenthesised span. Comments/blank lines skipped.
    """
    for lineno, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("<!--"):
            continue
        iast_inline = ""
        if "\t" in line:
            head, rest = line.split("\t", 1)
            iast_inline = extract_iast_span(rest)
        else:
            m = re.match(r"^(.*?) \(([^)]*)\)", line)
            if m:
                head, rest = m.group(1), m.group(2)
                iast_inline = extract_iast_span("(" + rest + ")")
            elif " " in line:
                head, rest = line.split(" ", 1)
            else:
                head, rest = line, ""
        head = head.strip()
        if not head:
            continue
        yield head, iast_inline, lineno


def sanscript_check(iast_witness: str, slp1: str):
    """Re-derive the H3985 invariant: slp1 == translit(iast_witness, IAST->SLP1)."""
    try:
        from indic_transliteration import sanscript
    except ImportError:
        return "sanscript-unavailable"
    try:
        return "OK" if sanscript.transliterate(
            iast_witness, sanscript.IAST, sanscript.SLP1) == slp1 else "MISMATCH"
    except Exception as exc:  # noqa: BLE001 - record, never crash the report
        return f"error:{type(exc).__name__}"


def build(table_path: str):
    rows = list(csv.DictReader(open(table_path, encoding="utf-8"), delimiter="\t"))
    by_form: dict[str, list[dict]] = {}
    for r in rows:
        by_form.setdefault(r["cyrillic"], []).append(r)

    joined: list[dict] = []
    per_gloss = {}
    for slug, fn in GLOSSARIES:
        path = os.path.join(DATA_DIR, fn)
        entries = parsed = 0
        for head, iast_inline, _lineno in parse_glossary(path):
            entries += 1
            hits = by_form.get(head)
            if not hits:
                continue
            parsed += 1
            for r in hits:
                joined.append({
                    "glossary_slug": slug,
                    "cyrillic": head,
                    "slp1": r["slp1"],
                    "iast_witness": r["iast_witness"],
                    "validation": r["validation"],
                    "onomasticon": r["onomasticon"],
                    "witness_count": r["witness_count"],
                    "iast_inline": iast_inline,
                })
        per_gloss[slug] = {"file": fn, "entries": entries,
                           "joined_forms": parsed,
                           "joined_rows": sum(1 for j in joined
                                              if j["glossary_slug"] == slug)}

    return rows, by_form, joined, per_gloss


def witness_agreement(inline: str, witness: str) -> str:
    """Classify the glossary paren span against the table's IAST witness.
    Editions do not guarantee the first paren span is IAST (Russian synonyms
    occur), so a Cyrillic span is NOT_IAST_SPAN, not a failure; a Latin span
    that disagrees IS a failure signal."""
    if not inline:
        return "NO_SPAN"
    if any("\u0400" <= c <= "\u04FF" for c in inline):
        return "NOT_IAST_SPAN"
    return "MATCH" if fold(inline) == fold(witness) else "MISMATCH"


def headword_present(slug: str, form: str) -> bool:
    """Re-read the source glossary and confirm the form starts a line."""
    fn = dict(GLOSSARIES)[slug]
    for raw in open(os.path.join(DATA_DIR, fn), encoding="utf-8"):
        line = raw.rstrip("\n")
        if (line == form or line.startswith(form + "\t")
                or line.startswith(form + " ")):
            return True
    return False


def sample_verify(joined: list[dict], target: int = 15):
    """Deterministic 15-name sample: alphabetical joined forms distributed over
    the glossaries that have joins (smirnov is unkeyed by design and gets none);
    verify headword provenance + witness agreement + SLP1 re-derivation."""
    live = [slug for slug, _fn in GLOSSARIES
            if any(j["glossary_slug"] == slug for j in joined)]
    base, extra = divmod(target, len(live))
    quota = {slug: base + (1 if i < extra else 0) for i, slug in enumerate(live)}
    results = []
    for slug, _fn in GLOSSARIES:
        forms = sorted({j["cyrillic"] for j in joined if j["glossary_slug"] == slug})
        for form in forms[:quota.get(slug, 0)]:
            row = next(j for j in joined
                       if j["glossary_slug"] == slug and j["cyrillic"] == form)
            checks = {
                "headword_in_glossary": headword_present(slug, form),
                "slp1_rederived_from_witness": sanscript_check(
                    row["iast_witness"], row["slp1"]),
                "witness_vs_inline": witness_agreement(
                    row["iast_inline"], row["iast_witness"]),
            }
            verdict = "PASS" if (
                checks["headword_in_glossary"]
                and checks["slp1_rederived_from_witness"] == "OK"
                and checks["witness_vs_inline"] != "MISMATCH"
            ) else "FAIL"
            results.append({
                "name": form, "glossary": slug, "slp1": row["slp1"],
                "iast_witness": row["iast_witness"],
                "iast_inline": row["iast_inline"],
                "checks": checks, "verdict": verdict,
            })
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="recompute and byte-compare committed outputs")
    ap.add_argument("--table", default=os.environ.get("CYR_SLP1_TSV", DEFAULT_TABLE))
    args = ap.parse_args()

    if not os.path.exists(args.table):
        print(f"FAIL: cyrillic-proper-noun-slp1 table not found at {args.table} "
              f"(set CYR_SLP1_TSV)", file=sys.stderr)
        return 2

    rows, by_form, joined, per_gloss = build(args.table)
    sample = sample_verify(joined)

    tsv_body = "".join(
        "\t".join(str(j[f]) for f in TSV_FIELDS) + "\n" for j in joined)

    covered = len({j["cyrillic"] for j in joined})
    report = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "handoff": "H4715 (xwalk-a10 cyr-propernoun-glossaries)",
        "dataset": {
            "id": "cyrillic-proper-noun-slp1",
            "path": os.path.relpath(args.table, REPO),
            "sha256": sha256_file(args.table),
            "rows": len(rows),
            "distinct_cyrillic_forms": len(by_form),
        },
        "rights_note": ("joined rows carry identifiers/keys/metadata only; "
                        "gloss text NOT redistributed (in-copyright editions)"),
        "totals": {
            "glossary_entries": sum(g["entries"] for g in per_gloss.values()),
            "joined_forms": sum(g["joined_forms"] for g in per_gloss.values()),
            "joined_rows": len(joined),
            "table_rows_with_glossary_home": sum(
                len(v) for k, v in by_form.items() if k in {j["cyrillic"] for j in joined}),
            "distinct_covered_forms": covered,
        },
        "validation_tiers_joined": dict(Counter(j["validation"] for j in joined)),
        "per_glossary": per_gloss,
        "sample_verify": {
            "method": ("3 alphabetical joined names per glossary; headword "
                       "provenance by construction, slp1 re-derived from IAST "
                       "witness, inline-IAST witness agreement"),
            "n": len(sample),
            "pass": sum(1 for s in sample if s["verdict"] == "PASS"),
            "fail": sum(1 for s in sample if s["verdict"] == "FAIL"),
            "results": sample,
        },
        "builder": "scripts/build_name_glossary_slp1_join.py",
    }

    if args.check:
        ok = True
        tsv_body = "\t".join(TSV_FIELDS) + "\n" + tsv_body
        for path, body in ((OUT_TSV, tsv_body), (OUT_JSON,
                           json.dumps(report, ensure_ascii=False, indent=1) + "\n")):
            if not os.path.exists(path):
                print(f"CHECK FAIL: missing {path}")
                ok = False
                continue
            committed = open(path, encoding="utf-8").read()
            # --check tolerates the timestamp field only
            def strip_ts(t):
                return re.sub(r'"generated": "[^"]*"', '"generated": "-"', t)
            if strip_ts(committed) != strip_ts(body):
                print(f"CHECK FAIL: drift in {path} — rerun builder and commit")
                ok = False
        print("CHECK PASS" if ok else "CHECK FAIL")
        return 0 if ok else 1

    os.makedirs(os.path.dirname(OUT_TSV), exist_ok=True)
    with open(OUT_TSV, "w", encoding="utf-8") as f:
        f.write("\t".join(TSV_FIELDS) + "\n" + tsv_body)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=1) + "\n")

    sv = report["sample_verify"]
    print(f"joined_rows={report['totals']['joined_rows']} "
          f"forms={report['totals']['joined_forms']}/{report['totals']['glossary_entries']} "
          f"covered_forms={covered}/{len(by_form)} "
          f"sample={sv['pass']}/{sv['n']} PASS")
    return 0 if sv["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
