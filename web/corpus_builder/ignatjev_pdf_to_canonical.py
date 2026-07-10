#!/usr/bin/env python3
"""Ignatjev Devībhāgavata-purāṇa PDF -> canonical JSONL (Russian side).

H534. Parses A. Ignatjev's 6-volume Russian Devībhāgavata-purāṇa (Касталия
2018) into the same canonical segment schema as
``html_to_canonical.py`` (see docs/CONVERTER_SPEC.md §2), so the GRETIL
Sanskrit side can later be aligned onto it under a shared ``group`` key
(docs/ALIGNMENT_SPEC.md) without re-minting IDs.

The Ignatjev PDFs are Russian-only running text with a very regular
structure, all recovered here without layout heuristics:

* **Skandha (книга)** — the volume partitions the 12 skandhas ~2 per volume.
  A skandha's verse text ends at an all-caps colophon
  ``ТАК ЗАКАНЧИВАЕТСЯ <ORD> КНИГА МАХАПУРАНЫ ДЕВИБХАГАВАТА ...`` and its
  endnotes follow under a ``Комментарий`` heading.
* **Chapter (глава)** — opens with a heading ``Глава <ordinal>`` + an
  ALL-CAPS title, and closes with a colophon
  ``Так ... заканчивается <ordinal> глава, называющаяся «<title>».``
  The ordinal (feminine) gives the chapter number (ru_ordinals).
* **Verse** — running text, each verse terminated by its number in
  parentheses at the end: ``... поведай мне. (1)``. A verse may span several
  printed lines; pdftotext joins them with newlines that we re-flow.
* **Speaker** — lines like ``Джанамеджая сказал:`` introduce a block of
  verses; captured as the ``author`` display field (like devi-gita's
  ``translation_author``).
* **Endnotes** — collected per skandha under ``Комментарий``; each is
  ``<n> <ch>.<verse>(<pada>). <text>`` (verse note),
  ``<n> Глава <ch>. <text>`` (chapter note), or the special ``1 оМ (oM) ...``.
  They become ``comment`` segments (``seg=comm{k}``) attached to their verse
  via ``annotates``. Endnote text wraps across lines; continuation lines are
  re-joined using the strictly-increasing footnote numbering.

Passage IDs follow the corpus convention (LINE_ID_SCHEME): zero-padded
``SKANDHA.CHAPTER.VERSE`` -> ``1.006.006`` (skandha 1 digit, chapter/verse
3 digits) so the GRETIL cross-numbering ``DbhP_1,6.6`` is mechanically
alignable and the ID grammar stays uniform with the rest of the corpus.

Usage:
    python web/corpus_builder/ignatjev_pdf_to_canonical.py \
        --pdf "AdnrejIgnatjev/devibhagavata-purana/Девибхагавата-пурана. Том 1.pdf" \
        --output-dir web/corpus_builder/jsonl \
        [--skandha-only 1]        # pilot: emit only this skandha
"""
from __future__ import annotations

import argparse
import html as _htmllib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from ru_ordinals import ordinal_f_to_int, ORDINAL_WORD_PATTERN  # noqa: E402

WORK_SLUG = "devibhagavata-purana"

# --- structural markers -----------------------------------------------------

# Chapter colophon (closes a chapter). The wording between «заканчивается» and
# «глава» varies (an optional «в <genitive-ordinal> книге махапураны
# Девибхагавата» clause may sit on either side), so we anchor on the CHAPTER
# ordinal immediately preceding «глава» — the only *nominative* feminine
# ordinal in the sentence — and derive the skandha separately. The genitive
# «первой» in the book clause is deliberately NOT in ORDINAL_WORD_PATTERN, so
# it cannot be mistaken for the chapter number.
_COLOPHON_RE = re.compile(
    r"заканчивается\b[^»]{0,90}?"
    r"(?P<ord>" + ORDINAL_WORD_PATTERN + r"(?:\s+" + ORDINAL_WORD_PATTERN + r")?)"
    r"\s+глава\b[^»]{0,150}?называющаяся\s+[«\"]([^»\"]+)[»\"]",
    re.IGNORECASE,
)

# All-caps skandha-end marker: "ТАК ЗАКАНЧИВАЕТСЯ ПЕРВАЯ КНИГА МАХАПУРАНЫ ..."
_SKANDHA_END_RE = re.compile(
    r"ТАК\s+ЗАКАНЧИВАЕТСЯ\s+(?P<ord>[А-ЯЁ]+(?:\s+[А-ЯЁ]+)?)\s+КНИГА\s+МАХАПУРАН",
)
_SKANDHA_ORD_CAPS = {
    "ПЕРВАЯ": 1, "ВТОРАЯ": 2, "ТРЕТЬЯ": 3, "ЧЕТВЕРТАЯ": 4, "ЧЕТВЁРТАЯ": 4,
    "ПЯТАЯ": 5, "ШЕСТАЯ": 6, "СЕДЬМАЯ": 7, "ВОСЬМАЯ": 8, "ДЕВЯТАЯ": 9,
    "ДЕСЯТАЯ": 10, "ОДИННАДЦАТАЯ": 11, "ДВЕНАДЦАТАЯ": 12,
}

# Chapter-opening heading: a line that is exactly "Глава <ordinal>".
_CHAPTER_OPEN_RE = re.compile(
    r"^\s*Глава\s+(?P<ord>" + ORDINAL_WORD_PATTERN +
    r"(?:\s+" + ORDINAL_WORD_PATTERN + r")?)\s*$",
    re.IGNORECASE,
)

# Endnote-block heading.
_NOTES_HEAD_RE = re.compile(r"^\s*(Комментарий|Примечания)\s*$", re.IGNORECASE)

# A bare page-number line (pdftotext emits running page numbers alone).
_PAGENUM_RE = re.compile(r"^\s*\d{1,4}\s*$")

# Verse terminator: a number in parentheses, optionally a range "(3-6)".
_VERSE_NUM_RE = re.compile(r"\((\d+(?:\s*[-–]\s*\d+)?)\)")

# Speaker marker at the start of a verse chunk: "Имя сказал(а/и):" possibly
# with a trailing footnote digit glued to the name ("Шаунака3 сказал:").
_SPEAKER_RE = re.compile(
    r"^\s*([А-ЯЁ][А-Яа-яёЁ \-]{0,60}?\d{0,3})\s+(сказал[аи]?|молвил[аи]?|"
    r"спросил[аи]?|произнесл[аи]?|отвечал[аи]?|воскликнул[аи]?)\s*:\s*",
)

# Endnote entry start (verse note): the leading number is the footnote id,
# followed by the target ``chapter.verse``. The ref tail varies freely — a
# pada ``(а)``, a range ``2.6(б) — 7``, a bare ``1.14`` — so we anchor only on
# ``<fn> <ch>.<verse>`` and let the strictly-increasing ``fn == next`` gate in
# parse_endnotes reject false positives.
_ENDNOTE_VERSE_RE = re.compile(
    r"^(?P<fn>\d+)\s+(?P<ch>\d+)\.(?P<v>\d+)(?:\s*\((?P<pada>[абвгдежзиАБВГ]{1,2})\))?",
)
# Endnote entry start (chapter note): "218 Глава 11. ..."
_ENDNOTE_CHAPTER_RE = re.compile(r"^(?P<fn>\d+)\s+Глава\s+(?P<ch>\d+)\.")
# Endnote entry start (the special footnote 1 invocation): "1 оМ (oM) — ..."
_ENDNOTE_FN1_RE = re.compile(r"^(?P<fn>1)\s+оМ\b")


def zero_pad_passage(skandha: int, chapter: int, verse: str) -> str:
    """Build the zero-padded SKANDHA.CHAPTER.VERSE passage id.

    verse may be a range like '3-6'; pad each endpoint to width 3.
    """
    def _pad(tok: str) -> str:
        return f"{int(tok):03d}"
    if "-" in verse or "–" in verse:
        a, b = re.split(r"[-–]", verse)
        vpart = f"{_pad(a.strip())}-{_pad(b.strip())}"
    else:
        vpart = _pad(verse)
    return f"{skandha}.{chapter:03d}.{vpart}"


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract UTF-8 text from a PDF via poppler's pdftotext."""
    out = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", str(pdf_path), "-"],
        capture_output=True, encoding="utf-8", errors="replace", check=True,
    )
    # pdftotext prepends a form-feed (\x0c) to the first line of every page,
    # which glues onto page-top text ("\x0c10 1.7(б)...") and breaks the
    # endnote-number and chapter-heading anchors. Turn page breaks into plain
    # blank lines so every marker starts at column 0.
    return out.stdout.replace("\x0c", "\n")


# --- endnote parsing --------------------------------------------------------

def parse_endnotes(note_lines: list[str]) -> dict[int, dict]:
    """Parse a skandha's collected endnotes into {fn_number: {...}}.

    Re-joins wrapped continuation lines using the strictly-increasing footnote
    numbering: a line whose leading integer equals the next expected footnote
    number starts a new endnote; every other line continues the current one.
    """
    notes: dict[int, dict] = {}
    order: list[int] = []
    current: dict | None = None

    def _classify(line: str):
        m = _ENDNOTE_FN1_RE.match(line)
        if m:
            return int(m.group("fn")), None, None, None
        m = _ENDNOTE_VERSE_RE.match(line)
        if m:
            return (int(m.group("fn")), int(m.group("ch")),
                    int(m.group("v")), m.group("pada"))
        m = _ENDNOTE_CHAPTER_RE.match(line)
        if m:
            return int(m.group("fn")), int(m.group("ch")), None, None
        return None

    next_fn = 1
    for raw in note_lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        if _PAGENUM_RE.match(line):
            # A bare page number interrupting an endnote — skip, keep flow.
            continue
        info = _classify(line)
        if info and info[0] == next_fn:
            fn, ch, v, pada = info
            current = {"fn": fn, "chapter": ch, "verse": v, "pada": pada,
                       "text": line}
            notes[fn] = current
            order.append(fn)
            next_fn = fn + 1
        elif current is not None:
            current["text"] += " " + line.strip()
        # else: preamble noise before the first endnote — ignore.

    # Collapse internal whitespace in each note's text.
    for n in notes.values():
        n["text"] = re.sub(r"\s+", " ", n["text"]).strip()
    return notes


# --- verse parsing ----------------------------------------------------------

def _reflow(lines: list[str]) -> str:
    """Join a chapter's body lines into one running string, dropping bare
    page-number lines."""
    kept = [ln.strip() for ln in lines
            if ln.strip() and not _PAGENUM_RE.match(ln)]
    return " ".join(kept)


def split_verses(body: str) -> list[dict]:
    """Split a chapter's running text into verse chunks.

    Returns a list of {verse, text, author} where verse is the label carried
    by the trailing ``(N)`` marker. A leading speaker label is lifted into
    ``author`` and carried forward to subsequent authorless verses (the speaker
    holds until the next speaker marker), mirroring the source layout.
    """
    verses: list[dict] = []
    pos = 0
    carry_author: str | None = None
    for m in _VERSE_NUM_RE.finditer(body):
        chunk = body[pos:m.start()].strip()
        label = m.group(1).replace(" ", "")
        pos = m.end()
        if not chunk:
            continue
        author = None
        sm = _SPEAKER_RE.match(chunk)
        if sm:
            author = re.sub(r"\d+$", "", sm.group(1)).strip()
            chunk = chunk[sm.end():].strip()
            carry_author = author
        else:
            author = carry_author
        verses.append({"verse": label, "text": chunk, "author": author})
    return verses


# --- footnote inline linking ------------------------------------------------

def link_footnotes(text: str, fn_numbers: set[int], used: set[int]):
    """Best-effort: strip glued footnote superscripts from a Russian verse and
    return (clean_text, html_text, refs).

    A footnote reference in pdftotext output is a run of digits glued to the end
    of a word/character (``Знание2``, ``людей4``, ``богов]137``). We only treat
    such a run as a reference when its value is a real footnote number for this
    skandha that has not been consumed yet — this avoids eating ordinary numbers
    and keeps linking monotonic. ``clean_text`` drops the digits (clean search
    payload); ``html_text`` replaces them with a devi-gita-style ``<sup>`` link.
    """
    refs: list[int] = []
    _L, _R = "", ""  # private-use sentinels wrapping a matched ref

    def _repl(mo):
        num = int(mo.group(2))
        if num in fn_numbers and num not in used:
            used.add(num)
            refs.append(num)
            return f"{mo.group(1)}{_L}{num}{_R}"
        return mo.group(0)

    # A footnote superscript is 1-3 digits glued to the end of a
    # letter/closing-bracket/quote and not itself followed by a digit or "(".
    marked = re.sub(r"([А-яёЁ»\)\]])(\d{1,3})(?![\d(])", _repl, text)

    # Clean search text: drop only the sentinel-wrapped refs (real digits in
    # the prose are left untouched).
    clean = re.sub(_L + r"\d+" + _R, "", marked)
    clean = re.sub(r"\s+", " ", clean).strip()

    def _htmlref(mo):
        num = mo.group(1)
        return ("<a href='#comment_" + num + "' class='comment_sub'>"
                "<sup><small>" + num + "</small></sup></a>")

    html_text = _htmllib.escape(marked, quote=False)
    html_text = re.sub(_L + r"(\d+)" + _R, _htmlref, html_text)
    return clean, html_text, refs


# --- top-level volume parse -------------------------------------------------

def parse_volume(text: str, vol_num: int, skandha_only: int | None = None):
    """Parse one Ignatjev volume into (records, report).

    records: list of canonical segment dicts (ru verse + comment segments).
    report: parse diagnostics for the run report / count gates.
    """
    lines = text.split("\n")

    # Pass 1: locate note-blocks (Комментарий ... until next chapter opening or
    # a caps skandha marker for the *next* skandha / EOF) and skandha-end
    # markers. We record, per line index, whether it's inside a note block.
    n = len(lines)
    in_notes = [False] * n
    i = 0
    note_blocks: list[tuple[int, int]] = []  # (start, end) inclusive of notes body
    while i < n:
        if _NOTES_HEAD_RE.match(lines[i]):
            start = i + 1
            j = start
            while j < n and not _CHAPTER_OPEN_RE.match(lines[j]):
                j += 1
            for k in range(start, j):
                in_notes[k] = True
            note_blocks.append((start, j - 1))
            i = j
        else:
            i += 1

    # Pass 2: walk body lines, cut at colophons into chapters, tracking skandha.
    records: list[dict] = []
    report = {
        "work": WORK_SLUG, "volume": vol_num, "skandhas": {},
        "verse_count": 0, "comment_count": 0, "chapters": 0,
        "verse_gaps": [], "orphan_notes": [], "chapter_titles": [],
    }

    # Endnotes per skandha (filled as we cross each note block, in order).
    # We collect them keyed by the skandha they close.
    skandha_seq = 0            # running skandha number within the mula
    seen_chapter_in_skandha = False
    seq = 0
    buf: list[str] = []        # current chapter body buffer (raw lines)
    pending_notes_for_skandha: dict[int, dict[int, dict]] = {}

    # Pre-parse each note block's endnotes now; associate to skandha later by
    # order of appearance.
    parsed_note_blocks = [parse_endnotes(lines[s:e + 1]) for (s, e) in note_blocks]
    note_block_used = [False] * len(parsed_note_blocks)

    def _skandha_of_next_noteblock() -> int | None:
        for idx, used in enumerate(note_block_used):
            if not used:
                return idx
        return None

    # Map skandha -> its endnotes. The k-th note block closes the k-th skandha
    # encountered in this volume; but we need the ABSOLUTE skandha number. We
    # derive the volume's first skandha number from the first caps marker.
    first_skandha_num = None
    for ln in lines:
        m = _SKANDHA_END_RE.search(ln)
        if m:
            first_skandha_num = _SKANDHA_ORD_CAPS.get(m.group("ord").strip())
            break

    # chapters as (skandha, chapter, title, body_lines)
    chapters: list[dict] = []
    cur_skandha = first_skandha_num or 1
    prev_chapter = 0
    skip_title = False
    for idx in range(n):
        if in_notes[idx]:
            continue
        line = lines[idx]
        # A chapter-opening heading ("Глава <ordinal>") marks the true start of
        # a chapter's verse text. Everything buffered before it is front matter
        # (title page, preface, annotation) or inter-chapter noise — discard it,
        # then skip the following ALL-CAPS chapter title line.
        if _CHAPTER_OPEN_RE.match(line):
            buf = []
            skip_title = True
            continue
        if skip_title:
            if line.strip():
                skip_title = False
            continue
        m = _COLOPHON_RE.search(line)
        if m:
            ch_ord = m.group("ord")
            ch_num = ordinal_f_to_int(ch_ord)
            title = m.group(2).strip() if m.lastindex and m.group(2) else ""
            if ch_num is None:
                buf.append(line)
                continue
            # Detect skandha rollover: chapter number reset to 1 (< prev).
            if ch_num <= prev_chapter and prev_chapter != 0:
                cur_skandha += 1
            # colophon line: strip the colophon text itself from the verse body
            colo_start = m.start()
            buf.append(line[:colo_start])
            chapters.append({
                "skandha": cur_skandha, "chapter": ch_num, "title": title,
                "body": list(buf),
            })
            buf = []
            prev_chapter = ch_num
        else:
            buf.append(line)

    # Associate note blocks to skandhas by appearance order.
    # note block k -> skandha (first_skandha_num + k)
    skandha_notes: dict[int, dict[int, dict]] = {}
    base = first_skandha_num or 1
    for k, nb in enumerate(parsed_note_blocks):
        skandha_notes[base + k] = nb

    # Build records per chapter.
    for ch in chapters:
        sk = ch["skandha"]
        if skandha_only is not None and sk != skandha_only:
            continue
        body = _reflow(ch["body"])
        # drop the opening heading "Глава <ord>" + following ALL-CAPS title if
        # present at the very start of the reflowed body.
        body = _strip_chapter_heading(body)
        verses = split_verses(body)
        fn_map = skandha_notes.get(sk, {})
        # Scope inline footnote linking to THIS chapter's own footnotes (those
        # whose endnote target chapter matches), so a stray numeral in a later
        # chapter cannot re-link to an early footnote number.
        fn_numbers = {fn for fn, note in fn_map.items()
                      if note["chapter"] == ch["chapter"]
                      or (fn == 1 and ch["chapter"] == 1)}
        used_fn: set[int] = set()
        report["chapters"] += 1
        report["chapter_titles"].append(
            {"skandha": sk, "chapter": ch["chapter"], "title": ch["title"]})
        sk_rep = report["skandhas"].setdefault(str(sk), {"chapters": 0, "verses": 0, "comments": 0})
        sk_rep["chapters"] += 1

        prev_v = 0
        for v in verses:
            seq += 1
            passage = zero_pad_passage(sk, ch["chapter"], v["verse"])
            group = f"{WORK_SLUG}:{passage}"
            clean, html_text, refs = link_footnotes(v["text"], fn_numbers, used_fn)
            rec = {
                "id": f"{WORK_SLUG}:{passage}#ru",
                "work": WORK_SLUG,
                "passage": passage,
                "seg": "ru",
                "group": group,
                "lang": "ru",
                "script": "cyrillic",
                "text": clean,
                "html": html_text,
                "structure": "verse",
                "chapter": str(ch["chapter"]),
                "skandha": str(sk),
                "seq": seq,
                "deleted": False,
            }
            if v["author"]:
                rec["author"] = v["author"]
            records.append(rec)
            report["verse_count"] += 1
            sk_rep["verses"] += 1
            # gap tracking (single-verse labels only)
            try:
                vv = int(re.split(r"[-–]", v["verse"])[0])
                if prev_v and vv not in (prev_v + 1, prev_v):
                    report["verse_gaps"].append(f"{sk}.{ch['chapter']}: {prev_v}->{vv}")
                prev_v = int(re.split(r"[-–]", v["verse"])[-1])
            except ValueError:
                pass

        # comment records for this chapter: endnotes whose target chapter == ch.
        # A verse-less note (the "оМ" invocation fn 1, or a "Глава N" chapter
        # note) is attached to verse 1 of the chapter so it renders inside a
        # real citation_block rather than an orphan chapter-level block.
        comm_by_verse: dict[str, list[dict]] = {}
        for fn, note in sorted(fn_map.items()):
            tgt_ch = 1 if fn == 1 else note["chapter"]
            if tgt_ch != ch["chapter"]:
                continue
            tgt_v = note["verse"] or 1
            annot = zero_pad_passage(sk, ch["chapter"], str(tgt_v))
            comm_by_verse.setdefault(annot, []).append((fn, note))

        for annot, items in comm_by_verse.items():
            for k, (fn, note) in enumerate(items, 1):
                seq += 1
                cid = f"{WORK_SLUG}:{annot}.comm{k}"
                # Strip the leading footnote number from the note text; the
                # number is shown separately in the comment_number span, and
                # the verse ref ("1.1(а).") stays as the text lead-in.
                text = re.sub(r"^\d+\s+", "", note["text"])
                html_c = (f'<span class="comment_number" '
                          f'title="Девибхагавата-пурана (А. Игнатьев, 2018): {fn}">'
                          f'{fn}. </span><span class="comment_text">'
                          f'{_htmllib.escape(text, quote=False)}</span>')
                records.append({
                    "id": cid, "work": WORK_SLUG, "passage": f"{annot}.comm{k}",
                    "seg": f"comm{k}", "group": f"{WORK_SLUG}:{annot}",
                    "lang": "ru", "script": "cyrillic", "text": text,
                    "html": html_c, "structure": "verse",
                    "chapter": str(ch["chapter"]), "skandha": str(sk),
                    "annotates": annot, "fn": fn, "seq": seq, "deleted": False,
                })
                report["comment_count"] += 1
                sk_rep["comments"] += 1

    return records, report


_CAPS_TITLE_RE = re.compile(r"^[А-ЯЁ][А-ЯЁ0-9 ,.«»\-—:()]{2,}?(?=[А-ЯЁ][а-яё])")


def _strip_chapter_heading(body: str) -> str:
    """Remove a leading 'Глава <ord>' + ALL-CAPS title from a reflowed body."""
    b = re.sub(r"^\s*Глава\s+" + ORDINAL_WORD_PATTERN +
               r"(?:\s+" + ORDINAL_WORD_PATTERN + r")?\s+", "", body,
               flags=re.IGNORECASE)
    # Drop a leading run of ALL-CAPS words (the title) up to the first
    # lowercase-initial word or the invocation "оМ"/digit.
    m = re.match(r"^((?:[А-ЯЁ][А-ЯЁ\-]*[ ,]+){1,12})", b)
    if m:
        b = b[m.end():]
    return b.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--output-dir", default="web/corpus_builder/jsonl")
    ap.add_argument("--skandha-only", type=int, default=None)
    ap.add_argument("--stdout-report", action="store_true")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    vol_m = re.search(r"Том\s*(\d+)", pdf_path.name)
    vol_num = int(vol_m.group(1)) if vol_m else 0

    text = extract_pdf_text(pdf_path)
    records, report = parse_volume(text, vol_num, args.skandha_only)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"_s{args.skandha_only}" if args.skandha_only else f"_vol{vol_num}"
    jsonl_path = out_dir / f"{WORK_SLUG}{suffix}.raw.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # Conversion report (chapter titles + counts) — consumed by the emitter for
    # chapter headings and used as the run audit trail (CONVERTER_SPEC §8).
    report_path = out_dir / f"{WORK_SLUG}{suffix}.report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"vol {vol_num}: {report['chapters']} chapters, "
          f"{report['verse_count']} verses, {report['comment_count']} comments "
          f"-> {jsonl_path}")
    if args.stdout_report:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
