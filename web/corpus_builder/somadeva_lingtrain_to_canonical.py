#!/usr/bin/env python3
"""Somadeva Kathāsaritsāgara (lingtrain SA↔RU alignment) → canonical JSONL.

Source: the upstream ``Marc-Winner/somadeva`` alignment workspace (a
Lingtrain Alignment Studio project). Two artifact kinds carry the *resolved*
sentence alignment:

* ``xml/somadeva_chN.xml`` — Lingtrain ``<book>`` export (authoritative, but
  only committed for 8 of the 10 aligned chapters: ch1-3, ch5-9).
* ``lt_files/somadeva_chN.lt`` — the Lingtrain Studio SQLite project. Its
  ``doc_index`` table holds the resolved alignment (batches of
  ``[from_proc_id, "[from_split_ids]", to_proc_id, "[to_split_ids]"]``). Used
  here to reconstruct ch4 + ch10, which have no committed XML.

Impedance note: SamudraManthanam's native alignment unit is the *verse*
(``lambaka.taraṅga.śloka``), joined by matching keys. The lingtrain output is
*sentence*-aligned (LaBSE) and the ``॥N॥`` śloka numbers were stripped during
preprocessing ("add dots for lt to split"). So we do NOT re-align: we ingest
the existing sentence alignment directly, keyed
``lambaka.taraṅga.sentence-ordinal`` with ``structure="prose"``. The taraṅga
number comes from the Russian h2 header prefix ("1.1.", "1.2.", …).

Sanskrit is stored as IAST (+ SLP1), transliterated from the aligned
Devanagari, to match the 138 existing corpus files.

Usage:
    python web/corpus_builder/somadeva_lingtrain_to_canonical.py \
        --src <path-to-somadeva-clone> \
        --out web/corpus_builder/jsonl/kathasaritsagara.jsonl \
        --slug kathasaritsagara \
        --report web/corpus_builder/jsonl/kathasaritsagara.report.json
"""
from __future__ import annotations
import argparse
import json
import re
import sqlite3
import sys
import html as _html
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# Chapters aligned upstream (lt_files ch1-10). XML committed for these 8:
XML_CHAPTERS = [1, 2, 3, 5, 6, 7, 8, 9]
LT_ONLY_CHAPTERS = [4, 10]
ALL_CHAPTERS = list(range(1, 11))

# "1.1" / "1.12" / "3.1.1" at the start of a Russian header → (lambaka, taraṅga);
# a story header "L.T.S" yields the same (L, T) as its enclosing taraṅga.
LT_PREFIX = re.compile(r"^\s*(\d+)\.(\d+)")


def deva_to_iast(s: str) -> str:
    return transliterate(s, sanscript.DEVANAGARI, sanscript.IAST)


def deva_to_slp1(s: str) -> str:
    return transliterate(s, sanscript.DEVANAGARI, sanscript.SLP1)


def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


# --------------------------------------------------------------------------
# XML path
# --------------------------------------------------------------------------
def pairs_from_xml(xml_path: Path):
    """Yield (lambaka, taranga, sa_deva, ru) tuples in document order.

    lambaka/taranga come from the Russian h2 header numeric prefix. Content of
    an h1 (book-intro / maṅgala) section is keyed to taraṅga 0 of that book.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    body = root.find("body")
    sections = list(body.findall("section"))

    # First resolve each section's (lambaka, taranga).
    resolved = []  # (idx, type, lambaka_or_None, taranga_or_None)
    for i, sec in enumerate(sections):
        stype = sec.get("type")
        hdr = sec.find("header")
        ru_hdr = ""
        if hdr is not None:
            to = hdr.find("su[@lang='to']")
            if to is not None and to.text:
                ru_hdr = to.text
        # The Russian header prefix "L.T." (h2 taraṅga) or "L.T.S." (h3 story)
        # both yield (lambaka, taraṅga); a story folds into its taraṅga's
        # running ordinal (the platform passage is exactly 3 levels).
        m = LT_PREFIX.match(ru_hdr or "")
        if m:
            resolved.append([i, stype, int(m.group(1)), int(m.group(2))])
        else:
            resolved.append([i, stype, None, None])
    # Backfill h1 (or unnumbered) sections: lambaka from nearest numbered h2.
    def nearest_lambaka(idx):
        for j in range(idx, len(resolved)):
            if resolved[j][2] is not None:
                return resolved[j][2]
        for j in range(idx, -1, -1):
            if resolved[j][2] is not None:
                return resolved[j][2]
        return 1  # lone-file fallback
    for r in resolved:
        if r[2] is None:
            r[2] = nearest_lambaka(r[0])
            r[3] = 0  # maṅgala / pre-taraṅga content

    for (i, stype, lam, tar) in resolved:
        sec = sections[i]
        for p in sec.findall("p"):
            for sent in p.findall("sentence"):
                sf = sent.find("su[@lang='from']")
                st = sent.find("su[@lang='to']")
                sa = norm_ws(sf.text if sf is not None else "")
                ru = norm_ws(st.text if st is not None else "")
                if not sa and not ru:
                    continue
                yield (lam, tar, sa, ru)


# --------------------------------------------------------------------------
# .lt (doc_index) path
# --------------------------------------------------------------------------
def pairs_from_lt(lt_path: Path):
    """Yield (lambaka, taranga, sa_deva, ru) reconstructed from doc_index."""
    con = sqlite3.connect(str(lt_path))
    cur = con.cursor()

    # paragraph -> (lambaka, taranga) map from Russian h2 headers in `meta`.
    hdr_rows = cur.execute(
        "SELECT val, par_id FROM meta WHERE key='h2_to' ORDER BY par_id"
    ).fetchall()
    boundaries = []  # (par_id, lambaka, taranga)
    for val, par_id in hdr_rows:
        m = LT_PREFIX.match(val or "")
        if m:
            boundaries.append((par_id, int(m.group(1)), int(m.group(2))))
    # Fallback lambaka for content before the first numbered header.
    first_lam = boundaries[0][1] if boundaries else 1

    def section_for(paragraph):
        cur_lt = (first_lam, 0)
        for par_id, lam, tar in boundaries:
            if paragraph >= par_id:
                cur_lt = (lam, tar)
            else:
                break
        return cur_lt

    # splitted_to id -> (text, paragraph); splitted_from id -> text
    to_text = {}
    to_par = {}
    for _id, text, para in cur.execute(
        "SELECT id, text, paragraph FROM splitted_to"
    ):
        to_text[_id] = text
        to_par[_id] = para
    from_text = {
        _id: text for _id, text in cur.execute("SELECT id, text FROM splitted_from")
    }

    di = json.loads(cur.execute("SELECT contents FROM doc_index").fetchone()[0])
    con.close()

    for batch in di:
        for entry in batch:
            f_ids = json.loads(entry[1])
            t_ids = json.loads(entry[3])
            sa = norm_ws(" ".join(from_text.get(i, "") for i in f_ids))
            ru = norm_ws(" ".join(to_text.get(i, "") for i in t_ids))
            if not sa and not ru:
                continue
            para = to_par.get(t_ids[0], 0) if t_ids else 0
            lam, tar = section_for(para)
            yield (lam, tar, sa, ru)


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------
def build(src: Path, slug: str):
    """Return (records, report). Numbers sentences continuously per (lam,tar)
    across chapter files so a taraṅga split over two files keeps unique keys."""
    per_key_count: dict[tuple[int, int], int] = {}
    records = []
    seq = 0
    report = {"slug": slug, "chapters": {}, "taranga_counts": {}, "warnings": []}

    for ch in ALL_CHAPTERS:
        xml_path = src / "xml" / f"somadeva_ch{ch}.xml"
        lt_path = src / "lt_files" / f"somadeva_ch{ch}.lt"
        if ch in XML_CHAPTERS and xml_path.exists():
            source = "xml"
            gen = pairs_from_xml(xml_path)
        elif lt_path.exists():
            source = "lt/doc_index"
            gen = pairs_from_lt(lt_path)
        else:
            report["warnings"].append(f"ch{ch}: no xml or lt found — skipped")
            continue

        ch_pairs = 0
        for (lam, tar, sa_deva, ru) in gen:
            key = (lam, tar)
            n = per_key_count.get(key, 0) + 1
            per_key_count[key] = n
            passage = f"{lam}.{tar}.{n}"
            group = f"{slug}:{passage}"
            has_sa = bool(sa_deva)
            has_ru = bool(ru)

            if has_sa:
                iast = deva_to_iast(sa_deva)
                seq += 1
                records.append({
                    "id": f"{group}#sa", "work": slug, "passage": passage,
                    "seg": "sa", "group": group, "lang": "sa", "script": "iast",
                    "text": iast, "html": _html.escape(iast) + "<br>",
                    "slp1": deva_to_slp1(sa_deva),
                    "structure": "prose", "chapter": str(tar),
                    "seq": seq, "deleted": False,
                })
            if has_ru:
                seq += 1
                records.append({
                    "id": f"{group}#ru", "work": slug, "passage": passage,
                    "seg": "ru", "group": group, "lang": "ru",
                    "script": "cyrillic", "text": ru,
                    "html": _html.escape(ru) + "<br>",
                    "structure": "prose", "chapter": str(tar),
                    "seq": seq, "deleted": False,
                })
            ch_pairs += 1
        report["chapters"][f"ch{ch}"] = {"source": source, "pairs": ch_pairs}

    report["taranga_counts"] = {
        f"{lam}.{tar}": cnt for (lam, tar), cnt in sorted(per_key_count.items())
    }
    report["total_pairs"] = sum(per_key_count.values())
    report["total_records"] = len(records)
    report["lambakas"] = sorted({lam for (lam, _t) in per_key_count})
    return records, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="path to somadeva clone")
    ap.add_argument("--out", required=True, help="output canonical JSONL")
    ap.add_argument("--slug", default="kathasaritsagara")
    ap.add_argument("--report", help="write a JSON stats report here")
    args = ap.parse_args()

    src = Path(args.src)
    records, report = build(src, args.slug)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Also emit one JSONL per lambaka (kathasaritsagara-<L>.jsonl) so each
    # split HTML file (kathasaritsagara-<L>.html) has the matching canonical
    # JSONL that ingest.py derives from its filename slug. Records keep the
    # base `work`/`id` (the DBhP split precedent), only the file is split.
    by_lam: dict[int, list[dict]] = {}
    for r in records:
        by_lam.setdefault(int(r["passage"].split(".")[0]), []).append(r)
    for lam, recs in sorted(by_lam.items()):
        p = out.parent / f"{args.slug}-{lam}.jsonl"
        with p.open("w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(by_lam)} per-lambaka JSONL files")

    if args.report:
        Path(args.report).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(f"wrote {len(records)} records to {out}")
    print(f"total aligned pairs: {report['total_pairs']}")
    print(f"lambakas: {report['lambakas']}")
    print("per-chapter:", json.dumps(report["chapters"], ensure_ascii=False))
    print("taranga counts:", json.dumps(report["taranga_counts"], ensure_ascii=False))
    if report["warnings"]:
        print("WARNINGS:", report["warnings"])


if __name__ == "__main__":
    main()
