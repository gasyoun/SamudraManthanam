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
# ordinal adjacent to «глава» — the only *nominative* feminine ordinal in the
# sentence — and derive the skandha separately. The genitive «первой» in the
# book clause is deliberately NOT in ORDINAL_WORD_PATTERN, so it cannot be
# mistaken for the chapter number.
#
# Two variations across the six volumes are load-bearing:
#   * The «называющаяся «title»» clause is OFTEN ABSENT — skandha 9 (Vol 5, 50
#     chapters) and skandha 8 (Vol 4) use bare «...заканчивается первая глава.».
#     Requiring the title silently dropped every title-less chapter (a whole
#     50-chapter skandha), so the title is OPTIONAL and captured when present.
#   * The ordinal occasionally FOLLOWS «глава» («...заканчивается глава
#     девятнадцатая», Vol 4), so both orders are accepted.
#   * "глава" is occasionally dropped by OCR ("...заканчивается двадцать
#     четвертая, называющаяся «…»", Vol 4) — accepted when the «называющаяся»
#     title clause is present to keep the anchor specific.
_ORD_PAT = ORDINAL_WORD_PATTERN + r"(?:\s+" + ORDINAL_WORD_PATTERN + r")?"
_COLOPHON_RE = re.compile(
    r"заканчивается\b[^»]{0,90}?"
    r"(?:"
    r"(?P<ord>" + _ORD_PAT + r")\s+глава"                      # <ord> глава
    r"|глава\s+(?P<ord2>" + _ORD_PAT + r")"                    # глава <ord>
    r"|(?P<ord3>" + _ORD_PAT + r")\s*,?\s*(?=называющаяся)"    # <ord>, называющаяся
    r")"
    r"(?:[^»]{0,150}?называющаяся\s+[«\"](?P<title>[^»\"]+)[»\"])?",
    re.IGNORECASE,
)

# Skandha-end colophon. The wording is NOT uniform across the six volumes —
# pdftotext yields all of:
#   "ТАК ЗАКАНЧИВАЕТСЯ ПЕРВАЯ КНИГА МАХАПУРАНЫ ..."      (Vol 1)
#   "ТАК В МАХАПУРАНЕ ДЕВИБХАГАВАТА ЗАКАНЧИВАЕТСЯ ЧЕТВЕРТАЯ КНИГА."  (Vol 2 s4)
#   "Так в махапуране Девибхагавата заканчивается десятая книга."   (Vol 5 s10, lc)
# The one invariant across all of them is the *nominative* feminine skandha
# ordinal placed immediately before "книга" and preceded (somewhere on the
# line) by "заканчивается". Chapter colophons instead say "в <ord>ой книгЕ ...
# глава" — "книге" (prepositional, -е), never "книга" (-а) — so anchoring on
# "<nominative-ord> книга" cleanly discriminates a skandha end from a chapter
# end. Case-insensitive to fold the ALL-CAPS variant.
_SKANDHA_ORD_STEM = (
    "перва|втора|треть|четв[её]рта|пята|шеста|седьма|восьма|девята|"
    "десята|одиннадцата|двенадцата"
)
_SKANDHA_COLO_RE = re.compile(
    r"заканчивается[^.]{0,70}?\b(?P<ord>" + _SKANDHA_ORD_STEM + r")я\s+книга\b",
    re.IGNORECASE,
)
_SKANDHA_ORD_NOM = {
    "перва": 1, "втора": 2, "треть": 3, "четверта": 4, "четвёрта": 4,
    "пята": 5, "шеста": 6, "седьма": 7, "восьма": 8, "девята": 9,
    "десята": 10, "одиннадцата": 11, "двенадцата": 12,
}

# The Devī-gītā (DBhP 7.31–40) is embedded in skandha 7 but its chapter
# colophons renumber from 1 ("Так в Деви-гите заканчивается первая глава"),
# which would (a) collide chapter IDs with the skandha's own chapters 1–10 and
# (b) look like a skandha rollover. We detect it by the "Деви-гит" marker and
# offset its chapters by +30 so they become 31–40 (the canonical DBhP numbering).
_DEVI_GITA_RE = re.compile(r"деви[-\s]?гит", re.IGNORECASE)
_DEVI_GITA_OFFSET = 30


def skandha_colophon_num(line: str):
    """Return the skandha number closed by this line, or None."""
    m = _SKANDHA_COLO_RE.search(line)
    if not m:
        return None
    return _SKANDHA_ORD_NOM.get(m.group("ord").lower())

# Chapter-opening heading: a line that is exactly "Глава <ordinal>".
_CHAPTER_OPEN_RE = re.compile(
    r"^\s*Глава\s+(?P<ord>" + ORDINAL_WORD_PATTERN +
    r"(?:\s+" + ORDINAL_WORD_PATTERN + r")?)\s*$",
    re.IGNORECASE,
)

# Endnote-block heading. The wording varies across the six volumes: title-case
# singular "Комментарий" and plural "Комментарии" (Vols 1–2), ALL-CAPS
# "КОММЕНТАРИЙ"/"КОММЕНТАРИИ" (Vols 3–6). IGNORECASE folds the caps; the [йи]
# class folds singular vs plural. Missing the plural form silently dropped
# Vol 2 skandha 4's ~230 notes ("Комментарии" at its head).
_NOTES_HEAD_RE = re.compile(r"^\s*(Комментари[йи]|Примечани[яе])\s*$", re.IGNORECASE)

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
# pada ``(а)`` or numeric ``(1)``/``(2)``, a range ``2.6(б) — 7``, a bare
# ``1.14`` — and pdftotext sometimes inserts a space after the chapter dot
# (``1. 4(1)`` in Vol 4). We anchor only on ``<fn> <ch>.<verse>`` (tolerating
# that space) and let the monotonic ``fn`` gate in parse_endnotes reject false
# positives. Missing the spaced-dot form stalled the gate at fn 2 on Vol 4.
_ENDNOTE_VERSE_RE = re.compile(
    r"^(?P<fn>\d+)\s+(?P<ch>\d+)\.\s?(?P<v>\d+)",
)
# Endnote entry start (chapter-range note): "46 3-6. миф о ..." — a note whose
# ref is a span of chapters, not a single verse. Target = the first chapter,
# no verse. Missing this form stalled the gate at fn 45 on Vol 2.
_ENDNOTE_CHRANGE_RE = re.compile(
    r"^(?P<fn>\d+)\s+(?P<ch>\d+)\s*[-–]\s*(?P<ch2>\d+)\b",
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

# A single note whose start-shape slips through recognition would, under a
# strict fn==next gate, glue every following note onto itself. We instead accept
# any classified start whose fn advances monotonically within a small window,
# so one unrecognised note (or a genuine gap in the source's own numbering)
# costs at most that one note instead of the whole tail. The window caps the
# jump so a stray "<big-number> <ch>.<v>"-shaped line inside prose can't hijack
# the sequence.
_FN_GAP_TOL = 8


def parse_endnotes(note_lines: list[str]) -> dict[int, dict]:
    """Parse a skandha's collected endnotes into {fn_number: {...}}.

    Re-joins wrapped continuation lines using the footnote numbering: a line
    whose leading integer is the next expected footnote number — or, to survive
    an unrecognised note or a source numbering gap, any monotonic advance within
    ``_FN_GAP_TOL`` — starts a new endnote; every other line continues the
    current one.
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
                    int(m.group("v")), None)
        m = _ENDNOTE_CHRANGE_RE.match(line)
        if m:
            # chapter-range note ("46 3-6. …") — target the first chapter.
            return int(m.group("fn")), int(m.group("ch")), None, None
        m = _ENDNOTE_CHAPTER_RE.match(line)
        if m:
            return int(m.group("fn")), int(m.group("ch")), None, None
        return None

    last_fn = 0
    for raw in note_lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        if _PAGENUM_RE.match(line):
            # A bare page number interrupting an endnote — skip, keep flow.
            continue
        info = _classify(line)
        is_start = info is not None and last_fn < info[0] <= last_fn + _FN_GAP_TOL
        if is_start:
            fn, ch, v, pada = info
            current = {"fn": fn, "chapter": ch, "verse": v, "pada": pada,
                       "text": line}
            notes[fn] = current
            order.append(fn)
            last_fn = fn
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

    # The six volumes partition the 12 skandhas two-per-volume, in order:
    # Vol N holds skandhas (2N-1, 2N). This regular split is the robust base —
    # far more reliable than scraping the first colophon, whose wording is not
    # uniform (and whose skandha-7 colophon pdftotext drops entirely). We derive
    # base = 2N-1 and *validate* it against whatever colophons we can read,
    # flagging (not trusting) any volume that disagrees.
    base = 2 * vol_num - 1 if vol_num else 1
    detected = sorted({skandha_colophon_num(ln) for ln in lines
                       if skandha_colophon_num(ln) is not None})
    report["skandha_base"] = base
    report["skandha_colophons_detected"] = detected
    if detected and not set(detected) <= {base, base + 1}:
        report.setdefault("warnings", []).append(
            f"vol {vol_num}: detected skandha colophons {detected} not within "
            f"expected {{{base}, {base + 1}}} — check volume→skandha map")

    # chapters as (skandha, chapter, title, body_lines). Skandha rollover is
    # driven by the END OF A NOTE BLOCK: in this edition every skandha ends with
    # its Комментарий, so the text after a note block is the next skandha. This
    # is more robust than either a chapter-number reset (the embedded Devī-gītā
    # resets chapters without being a new skandha) or the skandha "книга"
    # colophon (Vol 4 skandha 7's colophon is dropped by pdftotext entirely).
    # The only skandha with no trailing note block, Vol 4 skandha 8, is the last
    # in its volume, so no rollover is owed after it.
    chapters: list[dict] = []
    cur_skandha = base
    devi_gita_active = False
    skip_title = False
    in_note_block = False
    pending_open: int | None = None   # chapter opened by a heading, not yet closed
    last_ch: dict[int, int] = {}       # skandha -> last emitted chapter number
    idx = 0

    def _emit(sk, chn, ttl, body_lines):
        # Chapter numbers strictly increase within a skandha. A colophon that
        # repeats (or undershoots) the previous number is a source misprint —
        # skandha 10 prints two "пятая глава" — so bump it to keep numbering (and
        # thus passage ids) monotonic and gapless-of-duplicates.
        prev = last_ch.get(sk, 0)
        if chn <= prev:
            report.setdefault("renumbered_chapters", []).append(
                f"skandha {sk}: colophon says {chn}, renumbered to {prev + 1}")
            chn = prev + 1
        last_ch[sk] = chn
        chapters.append({"skandha": sk, "chapter": chn, "title": ttl,
                         "body": list(body_lines)})

    while idx < n:
        if in_notes[idx]:
            in_note_block = True
            idx += 1
            continue
        if in_note_block:
            # first body line after a note block -> next skandha
            in_note_block = False
            cur_skandha += 1
            devi_gita_active = False
            pending_open = None
            buf = []
        line = lines[idx]
        # A chapter-opening heading ("Глава <ordinal>" / "ГЛАВА <ORD>") marks the
        # true start of a chapter's verse text. It is also the recovery anchor
        # for a chapter whose CLOSING colophon pdftotext dropped (skandha 5 ch17,
        # skandha 9 ch16/36): if a chapter was opened but never closed by a
        # colophon, the next opening flushes it under that opening's own number.
        om = _CHAPTER_OPEN_RE.match(line)
        if om:
            if pending_open is not None and any(_VERSE_NUM_RE.search(b) for b in buf):
                _emit(cur_skandha, pending_open, "", buf)
            onum = ordinal_f_to_int(om.group("ord"))
            if onum is not None and devi_gita_active:
                onum += _DEVI_GITA_OFFSET
            pending_open = onum
            buf = []
            skip_title = True
            idx += 1
            continue
        if skip_title:
            if line.strip():
                skip_title = False
            idx += 1
            continue
        # A chapter colophon may be broken across two printed lines by pdftotext
        # ("…заканчивается пятнадцатая" / "глава, называющаяся «…»"). Try the
        # line alone, then joined with the next non-blank line(s), so a wrapped
        # colophon still cuts the chapter.
        m = _COLOPHON_RE.search(line)
        consumed_to = idx
        if not m and "заканчивается" in line:
            joined = line
            j = idx
            while j + 1 < n and j - idx < 3:
                j += 1
                if not lines[j].strip():
                    continue
                joined = joined + " " + lines[j]
                m = _COLOPHON_RE.search(joined)
                if m:
                    consumed_to = j
                    break
                if not lines[j].startswith(" ") and lines[j].strip():
                    # only bridge a couple of continuation lines
                    pass
        if m:
            ch_ord = m.group("ord") or m.group("ord2") or m.group("ord3")
            ch_num = ordinal_f_to_int(ch_ord) if ch_ord else None
            title = (m.group("title") or "").strip()
            if ch_num is None:
                buf.append(line)
            else:
                # Devī-gītā chapters renumber from 1 inside skandha 7; offset
                # them by +30 so they become 31–40 (canonical DBhP) and don't
                # collide with the skandha's own chapters 1–10.
                if _DEVI_GITA_RE.search(line) or _DEVI_GITA_RE.search(
                        " ".join(lines[idx:consumed_to + 1])):
                    devi_gita_active = True
                eff_ch = ch_num + _DEVI_GITA_OFFSET if devi_gita_active else ch_num
                # keep the pre-colophon verse text on the first line as body; the
                # colophon starts at "заканчивается" (possibly wrapped onward).
                cut = line.find("заканчивается")
                buf.append(line[:cut] if cut >= 0 else line)
                _emit(cur_skandha, eff_ch, title, buf)
                pending_open = None   # this chapter is now authoritatively closed
                buf = []
                idx = consumed_to + 1
                continue
        if not m:
            buf.append(line)
        idx += 1

    # Associate note blocks to skandhas by appearance order: the k-th note block
    # closes the k-th skandha that has notes in this volume, i.e. skandha base+k.
    # A skandha without a Комментарий block (e.g. Vol 4 skandha 8, cosmology,
    # has none) simply gets no notes and the mapping stays aligned.
    skandha_notes: dict[int, dict[int, dict]] = {}
    for k, nb in enumerate(parsed_note_blocks):
        skandha_notes[base + k] = nb

    # Skandha 7's notes cover the main chapters (1–30) then the Devī-gītā, whose
    # note refs renumber from chapter 1. Mirror the verse-side +30 offset on the
    # note side so a Devī-gītā note ("10.43") attaches to the Devī-gītā verse
    # (7.040.043) and not to main chapter 10. Detect the reset in the fn-ordered
    # note stream (a chapter that drops back to ≤12 after the mula reached ≥25).
    if 7 in skandha_notes:
        fn_map7 = skandha_notes[7]
        running_max = 0
        reset_at = None
        for fn in sorted(fn_map7):
            c = fn_map7[fn]["chapter"]
            if c is None:
                continue
            if reset_at is None and running_max >= 25 and c <= 12:
                reset_at = fn
            running_max = max(running_max, c)
        if reset_at is not None:
            for fn in sorted(fn_map7):
                if fn >= reset_at and fn_map7[fn]["chapter"] is not None:
                    fn_map7[fn]["chapter"] += _DEVI_GITA_OFFSET
            report.setdefault("notes", {})["devi_gita_offset_from_fn"] = reset_at

    # Build records per chapter.
    # Passage-ID integrity guard: a handful of chapters can't be split cleanly
    # from OCR (skandha 9 ch16/ch36 have BOTH their colophon and next opening
    # dropped, so their verses merge into the neighbour; skandha 10 prints two
    # "пятая глава" colophons — a genuine edition misnumbering). Either can mint
    # a duplicate SKANDHA.CHAPTER.VERSE id. We keep every verse (never drop) but
    # suffix any colliding passage id so the corpus has no duplicate ids, and
    # itemise the collisions in the report as a data finding.
    seen_passages: set[str] = set()
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
            if passage in seen_passages:
                report.setdefault("id_collisions", []).append(passage)
                suffix = "b"
                while f"{passage}{suffix}" in seen_passages:
                    suffix = chr(ord(suffix) + 1)
                passage = f"{passage}{suffix}"
            seen_passages.add(passage)
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
