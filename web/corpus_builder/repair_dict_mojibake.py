#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bounded mojibake repair for the five RU dictionary JSONL files (H7790, Q3).

Known defect class (SAMUDRA_DICT_UI_GRILL_DECISIONS_2026-11-07.md §1):
Cyrillic↔Latin homoglyph flips inside the structured headword/translit
columns of the digitized dictionaries (ргаdA, араnI, bаkа, акампитa…).

This pass is deliberately BOUNDED:

* Token-level, script-mixed tokens only (same discriminator as
  scan_cyrillic_homoglyphs.py): a letter-run mixing Latin and Cyrillic
  letters can never be a legitimate Russian word nor a legitimate
  IAST/SLP1 form, so it is always a defect.
* Direction is decided by the EXPECTED script of the column:
  - Latin-expected columns (IAST/SLP1): Cyrillic homoglyphs → Latin.
  - Cyrillic-expected columns (Cyrillic translit / smirnova headword):
    Latin homoglyphs → Cyrillic.
* A token is repaired ONLY when every wrong-script char has a lookalike
  mapping and the result is uniform-script. Anything unmappable (Cyrillic
  г/б inside a Latin column, Latin i inside a Cyrillic word, Devanagari
  columns carrying foreign script) is FLAGGED in the census, never
  rewritten — those need a human.
* Repaired tokens are additionally substituted as exact substrings across
  the whole record text/html, which also fixes the garbled headword
  quoted inside the gloss (e.g. «+apa (араnī); отводить» → «(apanī)»).
* text and html carry the same content and are repaired identically.

Usage:
    python repair_dict_mojibake.py [--write] [--report PATH]

Default is a dry-run census; --write applies the repair in place.
Exit status: 0 when no repairable defect remains, 1 when defects remain
(either unrepaired in dry-run, or flagged-for-human after --write).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

HERE = Path(__file__).resolve().parent
JSONL_DIR = HERE / "jsonl"

# The five RU dictionaries of the dict-UI lane (H7790).
DICT_FILES = [
    "frish.jsonl",
    "kochergina.jsonl",
    "kossovich.jsonl",
    "knauer.jsonl",
    "slovar-smirnova.jsonl",
]

# Cyrillic → Latin lookalikes (from scan_cyrillic_homoglyphs.py, proven set).
CYR_TO_LAT = {
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x",
    "і": "i", "ѕ": "s", "ј": "j", "һ": "h",
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H",
    "О": "O", "Р": "P", "С": "C", "Т": "T", "Х": "X", "І": "I",
    "Ј": "J", "Ѕ": "S", "Ү": "Y",
}
# Latin → Cyrillic lookalikes (inverse set, RUSSIAN letters only — deliberately
# narrower than the inverse of CYR_TO_LAT: Ukrainian і/ѕ/ј/һ must never be
# written into Russian text).
LAT_TO_CYR = {
    "a": "а", "c": "с", "e": "е", "o": "о", "p": "р", "x": "х", "y": "у",
    "A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "K": "К",
    "M": "М", "O": "О", "P": "Р", "T": "Т", "X": "Х",
}

_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def _is_letter(ch, script):
    if not ch.isalpha():
        return False
    try:
        return unicodedata.name(ch).startswith(script)
    except ValueError:
        return False


def has_latin(s): return any(_is_letter(c, "LATIN") for c in s)
def has_cyrillic(s): return any(_is_letter(c, "CYRILLIC") for c in s)
def has_devanagari(s): return any(0x0900 <= ord(c) <= 0x097F for c in s)


def repair_token(tok: str, expect: str):
    """Repair one letter-run token toward `expect` script ('lat'|'cyr').

    Returns (fixed_token_or_None, n_changed, unmapped_chars).
    None means "not safely repairable" — the caller keeps the original.
    """
    mapping = CYR_TO_LAT if expect == "lat" else LAT_TO_CYR
    out, changed, unmapped = [], 0, []
    for ch in tok:
        wrong_script = (_is_letter(ch, "CYRILLIC") if expect == "lat"
                        else _is_letter(ch, "LATIN"))
        if wrong_script:
            repl = mapping.get(ch)
            if repl is None:
                unmapped.append(ch)
                out.append(ch)
                continue
            out.append(repl)
            changed += 1
        else:
            out.append(ch)
    if unmapped or changed == 0:
        return None, 0, unmapped
    fixed = "".join(out)
    if expect == "lat" and has_cyrillic(fixed):
        return None, 0, unmapped
    if expect == "cyr" and has_latin(fixed):
        return None, 0, unmapped
    return fixed, changed, unmapped


def classify_token(tok: str):
    """Census classifier: 'devanagari', 'cyr_in_lat', 'lat_in_cyr',
    'unmappable', or None when the token is clean."""
    if has_devanagari(tok) and (has_latin(tok) or has_cyrillic(tok)):
        return "flagged_devanagari"
    if not (has_latin(tok) and has_cyrillic(tok)):
        return None
    # Scholarly jer notation (knauer etymology comparanda: "ognь", "jamь") —
    # Latin transliteration carrying only the Cyrillic soft/back jers is a
    # legitimate convention, not a defect.
    cyr_letters = [c for c in tok if _is_letter(c, "CYRILLIC")]
    if cyr_letters and all(c in "ьЪъ" for c in cyr_letters):
        return None
    if all(c in CYR_TO_LAT for c in tok if _is_letter(c, "CYRILLIC")):
        return "mixed_cyr_in_lat"
    if all(c in LAT_TO_CYR for c in tok if _is_letter(c, "LATIN")):
        return "mixed_lat_in_cyr"
    return "flagged_unmappable"


class Repairer:
    """Counts (census mode) or repairs (write mode) one dict JSONL."""

    def __init__(self):
        self.counts = {
            "mixed_cyr_in_lat": 0, "mixed_lat_in_cyr": 0,
            "repaired_to_lat": 0, "repaired_to_cyr": 0,
            "chars_changed": 0, "flagged_unmappable": 0,
            "flagged_devanagari": 0, "records_changed": 0,
        }
        self.samples: list = []
        self.flagged: list = []  # (record_id, field, token) needing a human

    def _note(self, rec_id, field, kind, tok, fixed=None):
        self.counts[kind] = self.counts.get(kind, 0) + 1
        if len(self.samples) < 60:
            if fixed is not None:
                self.samples.append({"id": rec_id, "field": field,
                                     "before": tok, "after": fixed})
            else:
                self.samples.append({"id": rec_id, "field": field, "token": tok})
        if kind in ("flagged_unmappable", "flagged_devanagari"):
            self.flagged.append((rec_id, field, tok))

    def _fix_value(self, value, expect, rec_id, field, pairs_out):
        """Repair every script-mixed letter-run in `value` toward `expect`."""
        if not value or not isinstance(value, str):
            return value
        for m in _WORD.finditer(value):
            tok = m.group()
            kind = classify_token(tok)
            if kind == "flagged_devanagari" or kind == "flagged_unmappable":
                self._note(rec_id, field, kind, tok)
                continue
            if kind is None:
                continue
            fixed, n, _unmapped = repair_token(tok, expect)
            if fixed is None:
                self._note(rec_id, field, "flagged_unmappable", tok)
                continue
            self._note(rec_id, field,
                       "repaired_to_lat" if expect == "lat" else "repaired_to_cyr",
                       tok, fixed)
            self.counts["chars_changed"] += n
            pairs_out.append((tok, fixed))
        return value

    @staticmethod
    def _apply_pairs(value, pairs):
        if not value or not isinstance(value, str) or not pairs:
            return value
        result = value
        for old, new in dict.fromkeys(pairs):
            if old in result:
                result = result.replace(old, new)
        return result

    def _fix_tabbed(self, rec, lat_cols, cyr_cols, deva_col=0):
        """frish/knauer/smirnova tab-separated text+html.

        Structured columns are repaired toward their expected script; gloss
        columns (RU text + IAST headword refs — a Russian word never carries
        Latin letters, so any script-mixed token there is a garbled IAST ref)
        are repaired toward Latin; the repaired tokens are then substituted
        everywhere else in the same field. Devanagari and page columns are
        never rewritten (deva contamination is flagged for a human).
        """
        rid = rec.get("id", "")
        for field in ("text", "html"):
            val = rec.get(field) or ""
            if "\t" not in val:
                continue
            cols = val.split("\t")
            pairs: list = []
            for i, col in enumerate(cols):
                if not col or i == deva_col:
                    continue
                if i in cyr_cols:
                    self._fix_value(col, "cyr", rid, f"{field}[{i}]", pairs)
                else:
                    self._fix_value(col, "lat", rid, f"{field}[{i}]", pairs)
            if pairs:
                cols = [self._apply_pairs(c, pairs) for c in cols]
                rec[field] = "\t".join(cols)

    def _fix_whole_fields(self, rec, fields, expect):
        """kochergina/kossovich: repair mixed tokens across whole fields.

        Safe: RU glosses are pure Cyrillic, IAST/SLP1 pure Latin — any
        script-mixed token in these fields is a defect.
        """
        rid = rec.get("id", "")
        for field in fields:
            val = rec.get(field)
            if not isinstance(val, str) or not val:
                continue
            pairs: list = []
            self._fix_value(val, expect, rid, field, pairs)
            if pairs:
                rec[field] = self._apply_pairs(val, pairs)

    def _fix_forms(self, rec):
        forms = rec.get("forms") or {}
        rid = rec.get("id", "")
        changed = False
        for key, expect in (("iast", "lat"), ("cyrillic", "cyr"), ("slp1", "lat")):
            val = forms.get(key)
            if not isinstance(val, str) or not val:
                continue
            pairs: list = []
            self._fix_value(val, expect, rid, f"forms.{key}", pairs)
            if pairs:
                forms[key] = self._apply_pairs(val, pairs)
                changed = True
        if changed:
            rec["forms"] = forms

    def census(self, rec):
        """Count defect instances without repairing (before/after census)."""
        def walk(val, field):
            if isinstance(val, str):
                for m in _WORD.finditer(val):
                    kind = classify_token(m.group())
                    if kind:
                        self._note(rec.get("id", ""), field, kind, m.group())
            elif isinstance(val, dict):
                for k, v in val.items():
                    walk(v, f"{field}.{k}")
        for field in ("text", "html", "slp1"):
            walk(rec.get(field), field)
        walk(rec.get("forms"), "forms")

    def process(self, rec):
        """Repair one record in place. Returns True when changed."""
        before = json.dumps(rec, sort_keys=True, ensure_ascii=False)
        work = rec.get("work")
        if work in ("frish", "knauer"):
            # cols: 0 deva | 1 iast | 2 slp1 | 3 cyrillic | 4 gloss [| 5 page]
            self._fix_tabbed(rec, lat_cols={1, 2}, cyr_cols={3})
        elif work == "slovar-smirnova":
            # cols: 0 head(cyr caps) | 1 iast | 2 iast | 3 badge | 4 gloss
            self._fix_tabbed(rec, lat_cols={1, 2}, cyr_cols={0})
        elif work in ("kochergina", "kossovich"):
            # html «°head /iast/ gloss», text «gloss deva iast» — mixed tokens
            # anywhere in text/html/slp1 are defects toward Latin (the RU
            # gloss words are pure Cyrillic and never match the mixed rule).
            self._fix_whole_fields(rec, ("text", "html", "slp1"), "lat")
        if work in ("kochergina", "kossovich", "knauer", "slovar-smirnova"):
            self._fix_forms(rec)
        after = json.dumps(rec, sort_keys=True, ensure_ascii=False)
        if after != before:
            self.counts["records_changed"] += 1
            return True
        return False


def process_file(path: Path, write: bool):
    before = Repairer()
    applied = Repairer()
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    out_lines = list(lines)
    for lineno, line in enumerate(lines, 1):
        s = line.strip()
        if not s:
            continue
        try:
            rec = json.loads(s)
        except json.JSONDecodeError:
            continue
        before.census(rec)
        if not write:
            continue
        if applied.process(rec):
            out_lines[lineno - 1] = json.dumps(rec, ensure_ascii=False) + "\n"
    if write and applied.counts["records_changed"]:
        path.write_text("".join(out_lines), encoding="utf-8", newline="\n")
    return before, applied


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true",
                    help="apply the repair in place (default: dry-run census)")
    ap.add_argument("--report", default=None,
                    help="write a JSON census report to this path")
    args = ap.parse_args()

    report = {
        "handoff": "H7790",
        "generated": datetime.now(timezone.utc).isoformat(),
        "mode": "write" if args.write else "census",
        "files": {},
    }
    defects_remaining = 0
    for name in DICT_FILES:
        path = JSONL_DIR / name
        if not path.exists():
            continue
        before, applied = process_file(path, args.write)
        post = Repairer()
        if args.write:
            for line in path.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if not s:
                    continue
                try:
                    rec = json.loads(s)
                except json.JSONDecodeError:
                    continue
                post.census(rec)
        else:
            post = before
        remaining = sum(post.counts[k] for k in (
            "mixed_cyr_in_lat", "mixed_lat_in_cyr",
            "flagged_unmappable", "flagged_devanagari"))
        defects_remaining += remaining
        report["files"][name] = {
            "before": dict(before.counts),
            "after": dict(post.counts),
            "repaired": dict(applied.counts) if args.write else None,
            "flagged_for_human": [
                {"id": r, "field": f, "token": t}
                for r, f, t in (applied.flagged if args.write else before.flagged)
            ][:120],
            "samples": (applied.samples if args.write else before.samples),
        }
        print(f"== {name}")
        print(f"   before: mixed_cyr_in_lat={before.counts['mixed_cyr_in_lat']} "
              f"mixed_lat_in_cyr={before.counts['mixed_lat_in_cyr']} "
              f"unmappable={before.counts['flagged_unmappable']} "
              f"devanagari_flag={before.counts['flagged_devanagari']}")
        if args.write:
            print(f"   repaired: to_lat={applied.counts['repaired_to_lat']} "
                  f"to_cyr={applied.counts['repaired_to_cyr']} "
                  f"chars={applied.counts['chars_changed']} "
                  f"records={applied.counts['records_changed']}")
        print(f"   after:  mixed_cyr_in_lat={post.counts['mixed_cyr_in_lat']} "
              f"mixed_lat_in_cyr={post.counts['mixed_lat_in_cyr']} "
              f"unmappable={post.counts['flagged_unmappable']} "
              f"devanagari_flag={post.counts['flagged_devanagari']}")

    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nreport: {args.report}")
    print(f"\nremaining defects (flagged, need human): {defects_remaining}")
    return 1 if defects_remaining else 0


if __name__ == "__main__":
    sys.exit(main())
