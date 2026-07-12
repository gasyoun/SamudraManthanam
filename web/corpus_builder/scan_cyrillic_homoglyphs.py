#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan canonical corpus JSONL for Cyrillic homoglyphs mis-encoded inside
Sanskrit-IAST ('sa') segments, and optionally fix them in place.

Background (12-07-2026): the southern-vulgate Sundarakāṇḍa source carried
Cyrillic letters (U+0400–U+04FF) where Latin IAST letters belong — e.g. a
Cyrillic 'с' (U+0441) typed instead of Latin 'c'. Surfaced by the
CommentaryStrategies helayo-alignment apparatus run.

CRITICAL — homoglyph contamination vs legitimate Russian. A 'sa' record's
text can legitimately contain whole Russian words (editorial notes like
"[на GRETIL не шлока]" = "not a shloka on GRETIL"). Those must NEVER be
touched. The real target is a *homoglyph*: a lone Cyrillic letter sitting
inside an otherwise-Latin word ("saṃcukoсa", "tad-vipākа-аnuguṇānām").

The discriminator is therefore token-level, not char-level: split each field
on whitespace and classify every token by script —
  * MIXED   (≥1 Latin letter AND ≥1 Cyrillic letter)  -> homoglyph, FIX it.
  * PURE-CYR (Cyrillic letters, no Latin)              -> Russian word, LEAVE.
  * clean   (no Cyrillic)                              -> ignore.
Only mappable Cyrillic letters inside MIXED tokens are ever substituted; a
pure-Cyrillic run is reported once as an informational Russian note and left
verbatim. IAST precomposed diacritics (ā ī ś ṣ ṇ ṭ ḥ ṃ …) are Latin-block,
so they count as Latin context.

Usage:
    python scan_cyrillic_homoglyphs.py [--fix] [--show-russian] [PATH ...]

Without paths, scans every *.jsonl under this file's jsonl/ directory.
Report mode (default) is read-only and lists every homoglyph verse with the
exact char, codepoint, mapped Latin letter, and byte offset within the field.
--fix rewrites the JSONL in place, substituting each homoglyph with its Latin
IAST equivalent inside MIXED tokens of each 'sa' record only.

Exit status: 0 if no homoglyph remains in 'sa' segments after the run,
1 if homoglyphs remain (report mode) or --fix left unmapped homoglyphs.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Cyrillic-block codepoints that are visual homoglyphs of Latin/IAST letters.
# Keys are single Cyrillic characters; values are the Latin replacement.
# Deliberately conservative: only glyphs that unambiguously look like a Latin
# letter used in IAST. Anything Cyrillic not in this map is flagged but never
# auto-substituted (would need a human ruling).
HOMOGLYPHS = {
    # lowercase
    "а": "a",  # а
    "е": "e",  # е
    "о": "o",  # о
    "р": "p",  # р
    "с": "c",  # с
    "у": "y",  # у
    "х": "x",  # х
    "і": "i",  # і (Ukrainian i)
    "ѕ": "s",  # ѕ (dze)
    "ј": "j",  # ј (je)
    "һ": "h",  # һ (Cyrillic shha, looks like h)
    "ґ": "r",  # ґ occasionally; rare — kept out below actually
    # uppercase
    "А": "A",  # А
    "В": "B",  # В
    "Е": "E",  # Е
    "К": "K",  # К
    "М": "M",  # М
    "Н": "H",  # Н
    "О": "O",  # О
    "Р": "P",  # Р
    "С": "C",  # С
    "Т": "T",  # Т
    "Х": "X",  # Х
    "І": "I",  # І
    "Ј": "J",  # Ј
    "Ѕ": "S",  # Ѕ
    "Ү": "Y",  # Ү
}
# ґ (U+0491) is not a clean 'r' homoglyph; drop it to avoid bad fixes.
HOMOGLYPHS.pop("ґ", None)


def is_cyrillic(ch: str) -> bool:
    """True for Cyrillic-block and Cyrillic-supplement codepoints."""
    o = ord(ch)
    return 0x0400 <= o <= 0x04FF or 0x0500 <= o <= 0x052F


def _is_letter(ch, script):
    """True if ch is a letter whose Unicode name names `script` (LATIN/CYRILLIC)."""
    if not ch.isalpha():
        return False
    try:
        return unicodedata.name(ch).startswith(script)
    except ValueError:
        return False


def is_latin_letter(ch):
    return _is_letter(ch, "LATIN")


def is_cyrillic_letter(ch):
    return _is_letter(ch, "CYRILLIC")


# A "word" is a maximal run of letters + combining marks — NOT split on the
# hyphens/braces/HTML-tag angle-brackets/punctuation that separate Latin script
# from a real Russian word. This is what isolates a glued homoglyph
# ("saṃcukoсa", "vipākа") from a legitimately Cyrillic editorial note
# ("Проверить", "не шлока") that merely sits next to Latin HTML tags.
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def token_is_mixed(tok):
    """A letter-run token that mixes Latin and Cyrillic letters — the
    homoglyph-contamination signature."""
    has_lat = any(is_latin_letter(c) for c in tok)
    has_cyr = any(is_cyrillic_letter(c) for c in tok)
    return has_lat and has_cyr


def scan_value(val, field, homoglyphs, russian_runs):
    """Classify Cyrillic in one string. Appends homoglyph offenders (Cyrillic
    inside a mixed letter-run) to `homoglyphs`, and pure-Cyrillic runs
    (legit Russian) to `russian_runs`."""
    if not isinstance(val, str) or not any(is_cyrillic(c) for c in val):
        return
    for m in _WORD.finditer(val):
        tok = m.group()
        start = m.start()
        cyr_positions = [i for i, c in enumerate(tok) if is_cyrillic_letter(c)]
        if not cyr_positions:
            continue
        if token_is_mixed(tok):
            for i in cyr_positions:
                idx = start + i
                ch = tok[i]
                homoglyphs.append(
                    {
                        "field": field,
                        "char": ch,
                        "cp": f"U+{ord(ch):04X}",
                        "char_index": idx,
                        "byte_offset": len(val[:idx].encode("utf-8")),
                        "mapped": HOMOGLYPHS.get(ch),
                        "context": val[max(0, idx - 20): idx + 21],
                    }
                )
        else:
            russian_runs.append({"field": field, "token": tok})


def scan_record(rec):
    """Return (homoglyphs, russian_runs) for a 'sa' record; empties otherwise."""
    if rec.get("seg") != "sa":
        return [], []
    homoglyphs, russian_runs = [], []
    for field, val in rec.items():
        scan_value(val, field, homoglyphs, russian_runs)
    return homoglyphs, russian_runs


def _fix_token(tok, changed_ref, unmapped, field):
    """Return tok with mappable Cyrillic homoglyphs replaced (mixed tokens only)."""
    out = []
    for ch in tok:
        if is_cyrillic_letter(ch):
            repl = HOMOGLYPHS.get(ch)
            if repl is not None:
                out.append(repl)
                changed_ref[0] += 1
            else:
                out.append(ch)
                unmapped.append((field, ch, f"U+{ord(ch):04X}"))
        else:
            out.append(ch)
    return "".join(out)


def fix_record(rec):
    """Substitute homoglyphs inside MIXED letter-runs of a 'sa' record's string
    fields. Pure-Cyrillic (Russian) runs are left untouched. Returns
    (changed:int, unmapped:list) — replacements made and any homoglyph with no
    mapping (a mixed-run Cyrillic letter we could not resolve — needs human)."""
    if rec.get("seg") != "sa":
        return 0, []
    changed_ref = [0]
    unmapped = []
    for field, val in list(rec.items()):
        if not isinstance(val, str) or not any(is_cyrillic(c) for c in val):
            continue

        def _sub(m):
            tok = m.group()
            if token_is_mixed(tok):
                return _fix_token(tok, changed_ref, unmapped, field)
            return tok

        rec[field] = _WORD.sub(_sub, val)
    return changed_ref[0], unmapped


def process_file(path, fix):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    file_offenders = []   # (lineno, rec, homoglyph_offenders)
    russian_lines = 0     # count of 'sa' records carrying a legit Russian run
    fixed_records = 0
    total_changed = 0
    all_unmapped = []
    out_lines = list(lines)

    for lineno, line in enumerate(lines, 1):
        s = line.strip()
        if not s:
            continue
        try:
            rec = json.loads(s)
        except json.JSONDecodeError:
            continue
        homoglyphs, russian_runs = scan_record(rec)
        if russian_runs:
            russian_lines += 1
        if not homoglyphs:
            continue
        file_offenders.append((lineno, rec, homoglyphs))
        if fix:
            changed, unmapped = fix_record(rec)
            total_changed += changed
            if unmapped:
                all_unmapped.extend((lineno, rec.get("id"), *u) for u in unmapped)
            if changed:
                fixed_records += 1
                # Preserve the corpus JSON style (ensure_ascii=False) for a minimal diff.
                out_lines[lineno - 1] = json.dumps(rec, ensure_ascii=False) + "\n"

    if fix and total_changed:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.writelines(out_lines)

    return file_offenders, russian_lines, fixed_records, total_changed, all_unmapped


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="JSONL files (default: all jsonl/*.jsonl)")
    ap.add_argument("--fix", action="store_true", help="rewrite homoglyphs in place")
    ap.add_argument("--show-russian", action="store_true",
                    help="also report the count of legit Russian runs left untouched")
    args = ap.parse_args()

    if args.paths:
        paths = args.paths
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        paths = sorted(glob.glob(os.path.join(here, "jsonl", "*.jsonl")))

    grand_verses = 0
    grand_chars = 0
    grand_fixed = 0
    grand_russian = 0
    grand_unmapped = []

    for path in paths:
        offenders, russian_lines, fixed_records, changed, unmapped = \
            process_file(path, args.fix)
        grand_russian += russian_lines
        if not offenders:
            continue
        rel = os.path.relpath(path)
        n_chars = sum(len(o) for _, _, o in offenders)
        grand_verses += len(offenders)
        grand_chars += n_chars
        grand_fixed += changed
        grand_unmapped.extend(unmapped)
        print(f"\n=== {rel} — {len(offenders)} verse(s), {n_chars} homoglyph char(s) ===")
        for lineno, rec, offs in offenders:
            print(f"  line {lineno}  id={rec.get('id')}  passage={rec.get('passage')}")
            for o in offs:
                m = o["mapped"] or "??? (UNMAPPED — needs human)"
                print(f"      {o['field']:6s} {o['cp']} '{o['char']}' -> {m}  "
                      f"byte={o['byte_offset']} idx={o['char_index']}  "
                      f"…{o['context']}…")

    print("\n" + "=" * 60)
    if args.show_russian or grand_russian:
        print(f"INFO: {grand_russian} 'sa' record(s) carry a legitimate Russian "
              f"run (pure-Cyrillic token) — left untouched by design.")
    if args.fix:
        print(f"FIX: {grand_fixed} homoglyph char(s) replaced across "
              f"{grand_verses} verse(s).")
        if grand_unmapped:
            print(f"WARNING: {len(grand_unmapped)} UNMAPPED homoglyph(s) in mixed "
                  f"tokens left in place:")
            for lineno, rid, field, ch, cp in grand_unmapped:
                print(f"    line {lineno} id={rid} {field} {cp} '{ch}'")
            return 1
        return 0
    else:
        print(f"SCAN: {grand_verses} homoglyph 'sa' verse(s), "
              f"{grand_chars} homoglyph char(s) total.")
        return 1 if grand_verses else 0


if __name__ == "__main__":
    sys.exit(main())
