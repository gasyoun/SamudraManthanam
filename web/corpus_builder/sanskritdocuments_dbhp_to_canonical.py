#!/usr/bin/env python3
r"""sanskritdocuments.org ITRANS DBhP -> canonical Sanskrit JSONL.

H534 Phase 2 (Sanskrit source = sanskritdocuments.org, MG @DECIDE 10-07-2026,
option (a)). The full Devibhagavata-purana is **not on GRETIL** (only the
devi-gita fragment, skandha 7), so ``gretil_tei_to_canonical.py`` cannot supply
the Sanskrit pane. sanskritdocuments.org publishes the whole DBhP as 12
per-skandha ITRANS ``.itx`` files (``devIbhAgavatam01.itx`` ...
``devIbhAgavatam12.itx``, Vishwas Bhide, satsangdhara.net), Devanagari+IAST with
``skandha.adhyaya`` chapter markers and per-chapter verse numbering.

This converter turns one ``.itx`` skandha file into the same canonical ``#sa``
JSONL schema the aligner (``align_sanskrit.py``) consumes, keyed by
``SKANDHA.CHAPTER.VERSE`` so it joins mechanically onto the Ignatjev Russian.

Source conventions (measured 10-07-2026 on devIbhAgavatam01.itx):
  - ``\section{1\.1 prathamo.adhyAyaH | ... |}`` -> skandha.adhyaya. The chapter
    number resets the verse counter.
  - Verses are one or more ITRANS pada lines; a ``|`` ends a half-verse (ardha),
    and a trailing ``|| N||`` closes the verse with its in-chapter number N.
  - Speaker rubrics stand on their own line: ``shaunaka uvAcha \-`` -> carried
    into an ``author`` field (like devi-gita's ``janamejaya uvAcha``).
  - Chapter colophons ``iti shrImaddevIbhAgavate ... || 1\.C||`` are skipped
    (compound ``S.C`` marker, never a bare ``|| N||``).

ITRANS is transcoded to IAST for display/search and to SLP1 for the ``slp1``
field via ``indic_transliteration.sanscript`` (the canonical transcoder, per the
org SHARED_CODE ITRANS note).

Usage:
    python web/corpus_builder/sanskritdocuments_dbhp_to_canonical.py \
        --itx web/corpus_builder/sanskrit_src/devIbhAgavatam01.itx \
        --skandha 1 --work devibhagavata-purana \
        --output-dir web/corpus_builder/jsonl
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from indic_transliteration import sanscript  # noqa: E402

# ``\section{1\.1 prathamo.adhyAyaH | shaunakaprashnaH |}`` -> skandha, chapter
_SECTION_RE = re.compile(r"\\section\{\s*(\d+)\\?\.(\d+)\s")
# A verse closes with ``|| N||`` (bare integer). A colophon closes with
# ``|| 1\.C||`` (compound) and is intentionally NOT matched here.
_VERSE_END_RE = re.compile(r"\|\|\s*(\d+)\s*\|\|")
# Speaker rubric, e.g. ``shaunaka uvAcha \-`` / ``vyAsa uvAcha`` / ``devyuvAcha``
_SPEAKER_RE = re.compile(r"^(.*?uvA?cha)\b", re.IGNORECASE)
_COLOPHON = "iti shrImaddevIbhAgavate"


def _iast(itrans: str) -> str:
    return sanscript.transliterate(itrans, sanscript.ITRANS, sanscript.IAST)


def _slp1(itrans: str) -> str:
    return sanscript.transliterate(itrans, sanscript.ITRANS, sanscript.SLP1)


def _clean_itrans(s: str) -> str:
    """Drop ITRANS control glyphs that are not part of the readable text."""
    s = s.replace(r"\-", "")   # explicit hiatus / word-break dash
    s = s.replace("~", "")     # any stray tilde outside a cluster
    return s.strip()


def parse_skandha(itx_path: Path, skandha: int, slug: str):
    """Return (records, report) for one .itx skandha file."""
    lines = itx_path.read_text(encoding="utf-8").splitlines()

    records: list[dict] = []
    report = {
        "work": slug, "skandha": skandha,
        "chapters": 0, "verse_count": 0,
        "by_chapter": {}, "speakers_seen": 0,
    }

    chapter: int | None = None
    author_itrans: str | None = None
    buf: list[str] = []          # accumulated pada lines (ITRANS) of current verse
    seq = 0

    def flush(verse_no: int) -> None:
        nonlocal seq, buf
        nonlocal author_itrans
        padas = [p for p in buf if p]
        buf = []
        if not padas or chapter is None:
            return
        seq += 1
        passage = f"{skandha}.{chapter:03d}.{verse_no:03d}"
        group = f"{slug}:{passage}"
        # Display: half-verses joined by ' / ', a clean reference marker appended.
        text_iast = " / ".join(_iast(p) for p in padas)
        ref = f"{skandha}.{chapter}.{verse_no}"
        text = f"{text_iast} // {ref} //"
        html = ("<br>".join(_iast(p) for p in padas)
                + f" // {ref} //<br>")
        slp1 = " ".join(_slp1(p) for p in padas)
        rec = {
            "id": f"{slug}:{passage}#sa",
            "work": slug,
            "passage": passage,
            "seg": "sa",
            "group": group,
            "lang": "sa",
            "script": "iast",
            "text": text,
            "html": html,
            "slp1": slp1,
            "structure": "verse",
            "chapter": str(chapter),
            "skandha": str(skandha),
            "seq": seq,
            "deleted": False,
        }
        if author_itrans:
            rec["author"] = _iast(author_itrans)
        records.append(rec)
        report["verse_count"] += 1
        bc = report["by_chapter"].setdefault(str(chapter), 0)
        report["by_chapter"][str(chapter)] = bc + 1

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        sec = _SECTION_RE.search(line)
        if sec:
            chapter = int(sec.group(2))
            report["chapters"] += 1
            author_itrans = None
            buf = []
            continue

        if chapter is None:
            continue  # skip preamble / mangala before the first \section

        if _COLOPHON in line:
            buf = []   # discard any colophon spillover
            continue
        if line.startswith("%") or line.startswith("\\"):
            continue   # ITRANS/LaTeX control lines

        # Speaker rubric on its own line -> set the carried author.
        stripped = _clean_itrans(line).rstrip("|").strip()
        sp = _SPEAKER_RE.match(stripped)
        if sp and _VERSE_END_RE.search(line) is None and len(stripped.split()) <= 3:
            author_itrans = sp.group(1).strip()
            report["speakers_seen"] += 1
            continue

        m = _VERSE_END_RE.search(line)
        if m:
            head = _clean_itrans(line[: m.start()]).rstrip("|").strip()
            if head:
                buf.append(head)
            flush(int(m.group(1)))
        else:
            body = _clean_itrans(line).rstrip("|").strip()
            if body:
                buf.append(body)

    report["chapters"] = len(report["by_chapter"])
    return records, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--itx", required=True, help="Path to a devIbhAgavatamNN.itx file")
    ap.add_argument("--skandha", required=True, type=int, help="Skandha number (1-12)")
    ap.add_argument("--work", default="devibhagavata-purana")
    ap.add_argument("--output-dir", default="web/corpus_builder/jsonl")
    args = ap.parse_args()

    itx_path = Path(args.itx)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records, report = parse_skandha(itx_path, args.skandha, args.work)

    stem = f"{args.work}_s{args.skandha}.sanskrit"
    jsonl_path = out_dir / f"{stem}.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    report_path = out_dir / f"{stem}.report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"{args.work} skandha {args.skandha}: {report['verse_count']} verses "
          f"in {report['chapters']} chapters, {report['speakers_seen']} speaker "
          f"rubrics -> {jsonl_path}")


if __name__ == "__main__":
    main()
