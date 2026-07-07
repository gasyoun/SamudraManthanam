#!/usr/bin/env python3
"""GRETIL-TEI -> canonical JSONL converter (Sanskrit side only).

H308 Track 1: converts a GRETIL TEI/XML source into the same canonical
JSONL schema as html_to_canonical.py (CONVERTER_SPEC.md), so a Russian
translation sourced later (H308 Track 2) can be added under the same
`group` key without re-minting Sanskrit IDs.

Scope (deliberately narrow — see docs/DECISIONS_NEEDED.md D5):
  Handles the GRETIL TEI "inline verse marker" convention seen in
  sa_nArAyaNa-hitopadeza.xml: <body> is a flat sequence of <p> (prose)
  and <lg> (verse stanza, one or more <l> lines) elements, with the
  last <l> of a stanza carrying a trailing citation marker
  `// {Prefix}_{chapter}.{verse} //`. There are no TEI <div>/<milestone>
  chapter markers in this convention -- the chapter number is recovered
  from the verse marker itself and carried forward for prose paragraphs.

  Does NOT handle div-based or unmarked prose TEI files (kadambari,
  vishnu-purana style) -- those need a per-genre anchoring decision
  (paragraph? printed page? TEI <div> id?) that H308 Track 2 flags as
  a human call, not something to guess here.

Usage:
    python web/corpus_builder/gretil_tei_to_canonical.py \\
        --tei GRETIL-1_sanskr/tei/sa_nArAyaNa-hitopadeza.xml \\
        --work hitopadesha \\
        --output-dir web/corpus_builder/jsonl
"""

import sys
import re
import json
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WEB_DIR = _REPO_ROOT / "web"
sys.path.insert(0, str(_WEB_DIR))

from corpus_builder.html_to_canonical import _to_slp1, _strip_accents  # noqa: E402

_TEI_NS = "{http://www.tei-c.org/ns/1.0}"

# Trailing citation marker, e.g. "// Hit_4.142 //" -- prefix is whatever the
# source uses (Hit_, BhP_, ...); chapter/verse are plain integers.
_MARKER_RE = re.compile(r"//\s*([A-Za-z]+)_(\d+)\.(\d+)\s*//\s*$")


def _local(tag: str) -> str:
    """Strip the TEI namespace off an element tag."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _itertext_join(el: ET.Element, sep: str) -> str:
    """Join all text content of el (and descendants) with sep between nodes."""
    parts = [t for t in el.itertext()]
    return sep.join(p.strip() for p in parts if p.strip())


def _prose_text_of(p_el: ET.Element) -> str:
    """Text belonging directly to a <p>, excluding any nested <lg> content.

    A GRETIL <p> sometimes wraps a stanza inline (`<p>kiṃ ca-\\n<lg>...</lg></p>`);
    the surrounding narrative text is prose, the <lg> is handled separately.
    """
    fragments = []
    if p_el.text and p_el.text.strip():
        fragments.append(p_el.text.strip())
    for child in p_el:
        if _local(child.tag) != "lg":
            fragments.append(_itertext_join(child, " "))
        if child.tail and child.tail.strip():
            fragments.append(child.tail.strip())
    return " ".join(f for f in fragments if f)


def _iter_lg_elements(root: ET.Element):
    """Yield every <lg> element in document order, at any nesting depth."""
    for el in root.iter(f"{_TEI_NS}lg"):
        yield el


def _build_sa_record(slug: str, passage: str, group: str, text: str,
                      html: str, chapter: str, seq: int, structure: str) -> dict:
    text_stripped = _strip_accents(text)
    slp1 = _to_slp1(text)
    record = {
        "id": f"{slug}:{passage}#sa",
        "work": slug,
        "passage": passage,
        "seg": "sa",
        "group": group,
        "lang": "sa",
        "script": "iast",
        "text": text_stripped,
        "html": html,
        "slp1": slp1,
        "structure": structure,
        "chapter": chapter,
        "seq": seq,
        "deleted": False,
    }
    return record


def convert_tei(tei_path: Path, slug: str):
    """Walk a GRETIL-TEI body, return (records, report)."""
    tree = ET.parse(tei_path)
    root = tree.getroot()
    body = root.find(f".//{_TEI_NS}body")
    if body is None:
        raise ValueError(f"No <body> found in {tei_path}")

    # First pass: which elements are <lg>-covered (so the prose pass can
    # skip their subtree when walking the flat body sequence).
    lg_elements = set(id(el) for el in _iter_lg_elements(body))

    records = []
    report = {"work": slug, "verse_count": 0, "prose_count": 0,
              "unmarked_verse_count": 0, "unmarked_examples": []}

    current_chapter = None
    para_seq_by_chapter = {}
    seq = 0

    def _walk(el: ET.Element):
        nonlocal seq, current_chapter
        tag = _local(el.tag)
        if tag == "lg":
            seq += 1
            l_texts = [
                (_itertext_join(l_el, " "))
                for l_el in el.iter(f"{_TEI_NS}l")
            ]
            full_text = " ".join(t for t in l_texts if t)
            m = _MARKER_RE.search(full_text)
            if m:
                chapter, verse = m.group(2), m.group(3)
                current_chapter = chapter
                passage = f"{chapter}.{verse}"
                clean_text = _MARKER_RE.sub("", full_text).strip()
                html = "<br>".join(t for t in l_texts if t)
                html = _MARKER_RE.sub("", html).strip()
                group = f"{slug}:{passage}"
                records.append(_build_sa_record(
                    slug, passage, group, clean_text, html,
                    current_chapter or "0", seq, "verse",
                ))
                report["verse_count"] += 1
            else:
                report["unmarked_verse_count"] += 1
                if len(report["unmarked_examples"]) < 5:
                    report["unmarked_examples"].append(full_text[:80])
                chapter = current_chapter or "0"
                n = para_seq_by_chapter.get(chapter, 0) + 1
                para_seq_by_chapter[chapter] = n
                passage = f"c{chapter}.p{n}"
                group = f"{slug}:{passage}"
                records.append(_build_sa_record(
                    slug, passage, group, full_text, full_text,
                    chapter, seq, "verse",
                ))
                records[-1]["needs_review"] = True
            return  # do not descend further into an <lg> we've just consumed

        if tag == "p":
            prose = _prose_text_of(el)
            if prose:
                seq += 1
                chapter = current_chapter or "0"
                n = para_seq_by_chapter.get(chapter, 0) + 1
                para_seq_by_chapter[chapter] = n
                passage = f"c{chapter}.p{n}"
                group = f"{slug}:{passage}"
                records.append(_build_sa_record(
                    slug, passage, group, prose, prose,
                    chapter, seq, "prose",
                ))
                report["prose_count"] += 1
            # still descend, in case this <p> wraps an <lg> (handled by
            # the recursive call hitting the lg branch above)
            for child in el:
                _walk(child)
            return

        for child in el:
            _walk(child)

    _walk(body)
    return records, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tei", required=True, help="Path to the GRETIL TEI XML file")
    ap.add_argument("--work", required=True, help="Canonical work slug (e.g. 'hitopadesha')")
    ap.add_argument("--output-dir", default="web/corpus_builder/jsonl")
    args = ap.parse_args()

    tei_path = Path(args.tei)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records, report = convert_tei(tei_path, args.work)

    jsonl_path = out_dir / f"{args.work}.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False))
            f.write("\n")

    report_path = out_dir / f"{args.work}.report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"{args.work}: {len(records)} records "
          f"({report['verse_count']} verse, {report['prose_count']} prose, "
          f"{report['unmarked_verse_count']} unmarked-verse) -> {jsonl_path}")


if __name__ == "__main__":
    main()
