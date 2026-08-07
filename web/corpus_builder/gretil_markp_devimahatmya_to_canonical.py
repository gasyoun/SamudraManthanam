#!/usr/bin/env python3
"""GRETIL Mārkaṇḍeya-purāṇa → Devīmāhātmya Sanskrit JSONL (flat chapter.verse).

H2353. The Devīmāhātmya is the 13-adhyāya block inside the Mārkaṇḍeya-purāṇa.
GRETIL's Sansknet-derived file keys verses as ``MarkP_<adhy>.<verse>``;
standard Bombay/Poona numbering places DM at adhyāyas 81–93. This script
extracts that block and renumbers to flat 1..13 so it joins Ignatiev's
Russian ``devimahatmya`` JSONL via ``align_sanskrit.py`` (markup/key join).

Usage:
    python web/corpus_builder/gretil_markp_devimahatmya_to_canonical.py \\
        --input web/corpus_builder/sanskrit_src/mkp1-93u.htm \\
        --out web/corpus_builder/jsonl/devimahatmya.sanskrit.jsonl \\
        [--start-adhy 81]

Source: http://gretil.sub.uni-goettingen.de/gretil/1_sanskr/3_purana/mkp1-93u.htm
License: GRETIL terms (reference / research use; not proof-read).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# // MarkP_81.12 // or // MarkP_Mang.1 //
_MARK_RE = re.compile(
    r"//\s*MarkP_(?:Mang|(\d+))\.(\d+[a-z]?)\s*//",
    re.IGNORECASE,
)
# half-verse lines end with / ; full with // MarkP_...
_LINE_SPLIT = re.compile(r"\s*/\s*")


def parse_gretil_markp(text: str, start_adhy: int, n_chapters: int = 13):
    """Return (sa_records, report) for adhy start_adhy .. start_adhy+n-1."""
    end_adhy = start_adhy + n_chapters - 1
    # Strip HTML tags if any
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    records: list[dict] = []
    seen: set[str] = set()
    report = {
        "source": "gretil_markp",
        "start_adhy": start_adhy,
        "end_adhy": end_adhy,
        "verses": 0,
        "by_chapter": {},
        "skipped_mangala": 0,
    }
    seq = 0
    # Walk marker positions; body for a verse is text between previous
    # marker end and this marker start (GRETIL puts the key after the śloka).
    matches = list(_MARK_RE.finditer(text))
    for i, m in enumerate(matches):
        adhy_s, verse_s = m.group(1), m.group(2)
        if adhy_s is None:
            report["skipped_mangala"] += 1
            continue
        adhy = int(adhy_s)
        if adhy < start_adhy or adhy > end_adhy:
            continue
        # Body: from previous match end (or nearby) — actually GRETIL has
        # the verse text BEFORE the // MarkP_N.M // marker.
        prev_end = matches[i - 1].end() if i > 0 else 0
        body = text[prev_end:m.start()]
        body = re.sub(r"_{5,}", " ", body)
        # Drop HTML leftovers and collapse whitespace for cleaning steps.
        body = re.sub(r"<[^>]+>", " ", body)
        body = body.replace("\n", " ")
        # Prefer the verse after the last speaker / chapter-colophon label so
        # we don't drag ``iti śrīmārkaṇḍeyapurāṇe … 'dhyāyaḥ`` into 1.1.
        for cut in (
            r"mārkaṇḍeya\s*uvāca",
            r"ṛṣir?\s*uvāca",
            r"devy?\s*uvāca",
            r"rājovāca",
            r"suratha\s*uvāca",
            r"medha\s*uvāca",
            r"brahmovāca",
            r"śakr[ao]\s*uvāca",
            r"viṣṇur?\s*uvāca",
            r"'dhyāyaḥ\s*-?\s*\d*",
            r"adhyāyaḥ",
        ):
            parts = re.split(cut, body, flags=re.IGNORECASE)
            if len(parts) > 1:
                body = parts[-1]
        body = re.sub(r"\s+", " ", body).strip(" /|\n\t- ")
        if not body:
            continue
        dm_ch = adhy - start_adhy + 1
        # verse may be "12" or "12a"
        v_core = re.match(r"(\d+)", verse_s)
        if not v_core:
            continue
        v_num = v_core.group(1)
        passage = f"{dm_ch}.{v_num}"
        if passage in seen:
            # letter-suffix if GRETIL has a/b padas as separate keys with same n
            suffix = "b"
            while f"{passage}{suffix}" in seen:
                suffix = chr(ord(suffix) + 1)
            passage = f"{passage}{suffix}"
        seen.add(passage)
        seq += 1
        # Clean half-verse slashes into spaces for reader text.
        clean = body.replace(" / ", " ").replace("/", " ").strip()
        clean = re.sub(r"\s+", " ", clean)
        # Drop a trailing bare chapter numeral left by the colophon cut.
        clean = re.sub(r"^\d+\s+", "", clean).strip()
        rec = {
            "id": f"devimahatmya:{passage}#sa",
            "work": "devimahatmya",
            "passage": passage,
            "seg": "sa",
            "group": f"devimahatmya:{passage}",
            "lang": "sa",
            "script": "iast",
            "text": clean,
            "html": clean,  # already IAST plain; emitter escapes
            "structure": "verse",
            "chapter": str(dm_ch),
            "seq": seq,
            "deleted": False,
            "sa_source_key": f"MarkP_{adhy}.{verse_s}",
        }
        records.append(rec)
        report["verses"] += 1
        report["by_chapter"][str(dm_ch)] = report["by_chapter"].get(str(dm_ch), 0) + 1
    return records, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--start-adhy", type=int, default=81,
                    help="Mārkaṇḍeya adhyāya that is DM ch.1 (default 81)")
    ap.add_argument("--chapters", type=int, default=13)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()

    text = args.input.read_text(encoding="utf-8", errors="replace")
    recs, report = parse_gretil_markp(text, args.start_adhy, args.chapters)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    print(
        f"devimahatmya SA: {report['verses']} verses "
        f"(MarkP {args.start_adhy}–{args.start_adhy + args.chapters - 1}) "
        f"-> {args.out}"
    )
    print("by_chapter:", report["by_chapter"])


if __name__ == "__main__":
    main()
