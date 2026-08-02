#!/usr/bin/env python3
"""A. Ignatjev single-book (tantra/purāṇa-excerpt) translation -> canonical
JSONL (Russian side).

H1438. Generalizes ``ignatjev_pdf_to_canonical.py``'s proven structural
parsing (chapter headings, trailing ``(N)`` verse-number splitting, speaker
markers, endnote attachment) from the 6-volume, 12-skandha Devībhāgavata-
purāṇa to Ignatjev's ~20 other translations, each a standalone work sourced
as a single ``.docx``/``.doc``/``.pdf`` file with no skandha/volume level.
Schema: docs/CONVERTER_SPEC.md §2.

Differences from the DBhP PDF pipeline this generalizes:

* **Passage ids are flat ``CHAPTER.VERSE``** (no skandha level) -- the house
  convention for standalone works (cf. ``gitagovinda.jsonl``: ``"passage":
  "1.1"``), not DBhP's zero-padded 3-level ``SKANDHA.CHAPTER.VERSE``.
* **Chapter boundaries come from the OPENING heading alone**
  (``Глава <ordinal-word>``). A closing colophon's wording is NOT uniform
  across Ignatjev's translations -- DBhP says "...заканчивается N глава";
  the Chinachara-tantra says "Такова ... N глава" with no "заканчивается"
  at all -- so it is read only as an optional decorative strip, never
  required to split a chapter.
* **Endnotes are real Word footnotes.** Pandoc's plain-text writer renders
  both the inline reference and the collected note text bracket-wrapped
  (``...его[1].`` in the body; ``[1] 1.1(1). <text>`` in the endnote
  block) -- an exact ``[N]`` match, simpler and more reliable than the DBhP
  PDF's glued-digit superscript heuristic. Footnote 1 is a known pandoc
  quirk: its ``[1]`` marker lands glued to the endnote *section heading*
  rather than its own note line -- handled as a special case, matching the
  DBhP script's "keep every verse, itemize anomalies in the report" policy
  (a missed footnote never blocks a chapter/verse from being emitted).

Usage:
    python web/corpus_builder/ignatiev_book_to_canonical.py \
        --input "archive_ignatiev_2026/.../Чиначара-тантра.docx" \
        --work-slug chinachara-tantra \
        --output-dir web/corpus_builder/jsonl

Multi-part works (Ignatjev split some translations across several files,
e.g. Kularnava-tantra "Часть первая"/"Часть вторая", each continuing the
chapter numbering rather than restarting it) take several ``--input`` args,
extracted and concatenated (with a blank-line separator so a chapter heading
at a file boundary is never glued to the previous file's trailing line) into
one text stream before parsing -- the chapter/verse parser needs no other
change since chapter numbers already run continuously across the source
press's own file split.
"""
from __future__ import annotations

import argparse
import html as _htmllib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from ru_ordinals import ordinal_f_to_int, ORDINAL_WORD_PATTERN  # noqa: E402

# --- structural markers -----------------------------------------------------

# Chapter-opening heading: "Глава <ordinal>" alone on a line (the docx
# convention), or "Глава <ordinal> <ALL-CAPS TITLE>" on one line (the PDF
# convention -- e.g. "Глава первая ОПИСАНИЕ ПАРАБРАХМАНА"). The optional
# title is captured and discarded, never required to match.
#
# A third PDF variant (Нируттара-тантра ch.5 and similar) has NO paragraph
# break after the heading at all -- pdftotext emits "Глава пятая
# Благословенная Богиня сказала: ..." as one physical line, heading glued
# straight onto the chapter's own first body sentence (mixed-case, not an
# ALL-CAPS title). `rest` captures that trailing text so it is kept as the
# new chapter's opening body line instead of being silently dropped by a
# failed end-of-line anchor (which would merge chapter 5 into chapter 4's
# body and produce duplicate verse-number id collisions).
#
# A fourth variant (Йони-тантра ch.1) glues an ALL-CAPS running section
# title onto the FRONT of the heading instead: "ЙОНИ-ТАНТРА. ПЕРЕВОД Глава
# первая" is one physical line. `prefix` absorbs that leading run so the
# heading is still recognised from line start (an unrecognised chapter 1
# heading silently drops the whole chapter into the discarded front matter,
# not just mis-numbers it -- worse than the ch.5 case above).
#
# `prefix`/`title` MUST be scoped case-sensitive (`(?-i:...)`) despite the
# pattern's overall IGNORECASE flag: under IGNORECASE, `[А-ЯЁ]` matches
# lowercase Cyrillic too, so a mixed-case run (an unrelated table-of-contents
# line, e.g. "СОДЕРЖАНИЕ Предисловие Глава первая Глава вторая ...") would
# otherwise satisfy the "ALL-CAPS" class just as readily as a real ALL-CAPS
# title/prefix, defeating the one signal that distinguishes them from
# ordinary running prose (verified: this over-matched niruttara-tantra's own
# ToC line before the scoped fix, corrupting chapter numbering).
_CHAPTER_OPEN_RE = re.compile(
    r"^\s*(?:(?-i:(?P<prefix>[А-ЯЁ][А-ЯЁ0-9 ,.\-]{1,90}))\s+)?"
    r"Глава\s+(?P<ord>" + ORDINAL_WORD_PATTERN +
    r"(?:\s+" + ORDINAL_WORD_PATTERN + r")?)"
    r"(?:\s+(?-i:(?P<title>[А-ЯЁ][А-ЯЁ0-9 ,.\-]{1,90})))?"
    r"(?:\s+(?P<rest>\S.*))?\s*$",
    re.IGNORECASE,
)

# Table-of-contents lines look like "Глава восьмая ……… 48" — same ordinal
# form as a real chapter opening, but the leader-dot / page-number tail is a
# reliable negative signal. Rejecting them here keeps multi-part works from
# inventing empty chapters out of their own ToC (Yoginī 1-7 + 8-19, Kulārṇava).
_TOC_LEADER_RE = re.compile(r"[.…·•]{3,}|\s{2,}\d{1,4}\s*$")


def _is_chapter_open(line: str):
    """Match a real chapter-opening heading, or None for ToC / non-matches.

    Returns the regex match object on success. ToC leader-dot lines (and
    lines whose 'rest' is only a bare page number) are rejected even though
    they satisfy the raw ordinal form.
    """
    m = _CHAPTER_OPEN_RE.match(line)
    if not m:
        return None
    rest = (m.group("rest") or "").strip()
    if rest and _TOC_LEADER_RE.search(rest):
        return None
    # "Глава восьмая ………………………………………………………………48" puts the leaders in
    # the title group when they start with a non-letter — also catch the
    # whole-line form.
    if _TOC_LEADER_RE.search(line):
        return None
    return m

# Endnote-block heading: "Комментарий"/"Комментарии"/"Примечания" alone on a
# line, optionally with pandoc's glued first footnote marker ("[1]
# КОММЕНТАРИЙ" -- see module docstring).
_NOTES_HEAD_RE = re.compile(
    r"^\s*(?:\[(?P<fn1>\d+)\]\s*)?(Комментари[йи]|Примечани[яе])\s*$",
    re.IGNORECASE,
)

# Back-matter heading that closes the endnote block: an ALL-CAPS line
# standing alone (СЛОВАРЬ ПРЕДМЕТОВ И ТЕРМИНОВ / СПИСОК СОКРАЩЕНИЙ /
# ЛИТЕРАТУРА / ОБ АВТОРЕ ПЕРЕВОДА -- the house convention this press uses
# for every major section heading, matching "КОММЕНТАРИЙ" itself). Deliber-
# ately NOT case-insensitive: an endnote continuation line can start with
# the same word lowercased mid-sentence ("...в сторону конечной
# Реальности» (цит. по [Приложения энергетического усилия...") and must not
# be mistaken for the heading.
#
# No end-of-line anchor: a back-matter heading can be glued to its own first
# line of content, same pdftotext quirk as the chapter-heading variants
# above (Йони-тантра ch.8's true end-colophon is followed immediately by
# "ТЕКСТЫ ПО ПОЧИТАНИЮ ЙОНИ Созерцание йони. Оригинал на санскрите ..." on
# one physical line -- unrelated appendix hymns from OTHER named tantras,
# quoted for reference, that would otherwise bleed into chapter 8's body and
# restart its verse numbering from 1 repeatedly). Requiring only the ALL-CAPS
# lead-in (case-sensitive, so a lowercase continuation sentence never
# qualifies) is enough signal without the whole-line anchor -- BUT the
# minimum run length must stay long (7+ chars after the first) so a short
# in-text title abbreviation (Chinachara-tantra's own endnotes cite "НТ
# (11.6)" -- Niruttara-tantra -- mid-note) can never masquerade as a section
# heading and truncate the endnote block early; every real heading in this
# corpus (СЛОВАРЬ ИМЕН, ЛИТЕРАТУРА, ТЕКСТЫ ПО ПОЧИТАНИЮ ЙОНИ, ...) clears it
# easily, but "НТ", "ГСТ", "ЧЧТ" and similar 2-3 letter work-abbreviations do
# not.
_BACKMATTER_RE = re.compile(r"^[А-ЯЁ][А-ЯЁ \-]{7,45}")

# A bare page-number line (pdftotext emits running page numbers alone).
_PAGENUM_RE = re.compile(r"^\s*\d{1,4}\s*$")

# Verse terminator: a number in parentheses, optionally a range "(3-6)".
_VERSE_NUM_RE = re.compile(r"\((\d+(?:\s*[-–]\s*\d+)?)\)")

# Speaker marker at the start of a verse chunk: "Имя(-title) сказал(а/и):".
_SPEAKER_RE = re.compile(
    r"^\s*([А-ЯЁ][А-Яа-яёЁ \-]{0,60}?)\s+(сказал[аи]?|молвил[аи]?|"
    r"спросил[аи]?|произнесл[аи]?|отвечал[аи]?|воскликнул[аи]?|рекл[аи]?)"
    r"\s*:\s*",
)

# Bracketed inline footnote reference: "...его[1]." A run of 1-3 digits in
# square brackets glued to the preceding token, not followed by another
# digit or "(" (so a bracketed verse-range like "[3-6]" is not mistaken).
_INLINE_FN_RE = re.compile(r"\[(\d{1,3})\](?!\d|\()")

# Endnote entry start: "[N] ch.v(pada). text", "[N] ch.v1-v2(pada). text"
# (a note spanning a verse range), or "[N] ch.v. text" (pada optional).
# Also matches the bare "ch.v(pada). text" form that footnote 1 takes when
# pandoc glues its "[1]" onto the section heading instead.
_ENDNOTE_RE = re.compile(
    r"^(?:\[(?P<fn>\d+)\]\s*)?(?P<ch>\d+)\.\s?(?P<v>\d+)"
    r"(?:\s*[-–]\s*\d+)?(?:\((?P<pada>[^)]{0,10})\))?\.\s*(?P<text>.*)"
)


def _extract_doc_ole_utf16(path: Path) -> str:
    """Best-effort body extract from a Word 97-2003 .doc via the OLE
    WordDocument stream (UTF-16LE). Used when antiword is absent and Word
    COM cannot open the file (common on Office 2007 + nested ObjectPool
    docs). Not a full piece-table parser — good enough for Ignatiev's
    plain-prose scholarly translations where chapter headings and ``(N)``
    verse markers survive as contiguous UTF-16 runs. Requires ``olefile``.
    """
    import olefile  # lazy: only needed for the .doc fallback path

    ole = olefile.OleFileIO(str(path))
    try:
        if not ole.exists("WordDocument"):
            raise ValueError(f"no WordDocument stream in {path}")
        data = ole.openstream("WordDocument").read()
    finally:
        ole.close()
    if len(data) % 2:
        data = data[:-1]
    raw = data.decode("utf-16le", errors="ignore")
    out: list[str] = []
    for ch in raw:
        o = ord(ch)
        if ch in "\n\r\t":
            out.append("\n" if ch != "\t" else " ")
        elif 0x20 <= o <= 0x7E or 0x0400 <= o <= 0x04FF:
            out.append(ch)
        elif ch in "«»—–…„“”‚‘’°§±×÷" or (0xA0 <= o < 0x250):
            out.append(ch)
        else:
            out.append("\n")
    text = "".join(out)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def extract_text(path: Path) -> str:
    """Extract plain UTF-8 text from a .docx / .pdf / .doc / .txt source."""
    suffix = path.suffix.lower()
    if suffix == ".txt":
        # Pre-extracted plain text (e.g. a one-shot .doc salvage, or a
        # pandoc dump parked next to the source). Read as UTF-8.
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".docx":
        out = subprocess.run(
            ["pandoc", "-f", "docx", "-t", "plain", str(path)],
            capture_output=True, encoding="utf-8", errors="replace", check=True,
        )
        return out.stdout
    if suffix == ".pdf":
        out = subprocess.run(
            ["pdftotext", "-enc", "UTF-8", str(path), "-"],
            capture_output=True, encoding="utf-8", errors="replace", check=True,
        )
        # pdftotext prepends a form-feed to the first line of every page.
        return out.stdout.replace("\x0c", "\n")
    if suffix == ".doc":
        # Legacy binary Word format. Prefer antiword (correct Cyrillic when
        # ANTIWORDHOME + -m cp1251.txt are set); fall back to an OLE
        # WordDocument UTF-16LE scan when antiword is missing or Word COM
        # cannot open nested-ObjectPool files (Office 2007 rejects some).
        antiword_bin = shutil.which("antiword")
        if antiword_bin:
            mapping_dir = str(Path(antiword_bin).parent.parent / "share" / "antiword")
            env = {**os.environ, "ANTIWORDHOME": mapping_dir}
            out = subprocess.run(
                ["antiword", "-m", "cp1251.txt", "-w", "0", str(path)],
                capture_output=True, check=True, env=env,
            )
            return out.stdout.decode("cp1251", errors="replace")
        return _extract_doc_ole_utf16(path)
    raise ValueError(f"unsupported source format: {suffix} ({path})")


def extract_text_multi(paths: list[Path]) -> str:
    """Extract + concatenate several source files (a multi-part work) in
    argument order. A blank-line separator between parts guarantees a
    chapter-opening heading at the start of part N+1 is never glued onto
    part N's trailing body line (the same hazard the chapter-heading regex
    already guards against within a single file)."""
    return "\n\n".join(extract_text(p) for p in paths)


def _reflow(lines: list[str]) -> str:
    kept = [ln.strip() for ln in lines
            if ln.strip() and not _PAGENUM_RE.match(ln)]
    return " ".join(kept)


def split_verses(body: str) -> list[dict]:
    """Split a chapter's running text into verse chunks. See
    ignatjev_pdf_to_canonical.split_verses (identical algorithm).

    After the raw ``(N)`` split, non-monotonic restarts are collapsed
    (H1829): footnote prose that embeds citation markers like ``1.1(2)``
    or bare ``(1)`` was being minted as new verses that re-hit verse 1/2
    and forced letter-suffix id collisions (nirvana-tantra: 284 of 361
    corpus-wide dup-suffixes). A decrease in verse number within a
    chapter is treated as footnote debris — its text is appended to the
    previous verse rather than minted as a new passage.
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
        sm = _SPEAKER_RE.match(chunk)
        if sm:
            author = sm.group(1).strip()
            chunk = chunk[sm.end():].strip()
            carry_author = author
        else:
            author = carry_author
        verses.append({"verse": label, "text": chunk, "author": author})
    return _collapse_nonmonotonic_verses(verses)


def _verse_num_start(label: str) -> int | None:
    """Leading integer of a verse label (``3``, ``3-6``); None if unparseable."""
    try:
        return int(re.split(r"[-–]", label)[0])
    except (ValueError, IndexError):
        return None


def _looks_like_footnote_debris(text: str) -> bool:
    """Heuristic: chunk is footnote prose, not a real verse body (H1829)."""
    t = (text or "").strip()
    if not t:
        return True
    # Bare "5 1.1" / "10 1.4" footnote headers from glued-digit PDFs.
    if re.match(r"^\d{1,3}\s+\d+\.\d+", t) and len(t) < 80:
        return True
    # Continuation after a footnote number was stripped: ". gloss …".
    if t.startswith(". ") or t.startswith("– ") or t.startswith("- "):
        return True
    return False


def _collapse_nonmonotonic_verses(verses: list[dict]) -> list[dict]:
    """Merge false ``(N)`` splits from footnote prose (H1829).

    Two classes of debris:
      1. Non-monotonic restarts (e.g. 5→1, 3→1) — always merge into previous.
      2. Same-N or early-N chunks whose text looks like a footnote header /
         gloss continuation — merge; genuine same-N duplicates with real
         verse-length prose still pass through and get letter suffixes.
    """
    if not verses:
        return verses
    out: list[dict] = []
    prev_end = 0
    for v in verses:
        n = _verse_num_start(v["verse"])
        text = v.get("text") or ""
        if n is not None and out:
            if n < prev_end:
                out[-1]["text"] = (out[-1]["text"] + " " + text).strip()
                continue
            if n <= prev_end and _looks_like_footnote_debris(text):
                out[-1]["text"] = (out[-1]["text"] + " " + text).strip()
                continue
        out.append(v)
        if n is not None:
            try:
                prev_end = int(re.split(r"[-–]", v["verse"])[-1])
            except (ValueError, IndexError):
                prev_end = n
    return out


def parse_endnotes(note_lines: list[str], fn1_glued: bool) -> dict[int, dict]:
    """Parse the collected endnote block into {fn_number: {...}}.

    Mirrors ignatjev_pdf_to_canonical.parse_endnotes: a line whose leading
    marker is the next expected footnote number (monotonic, small-gap
    tolerant) starts a new note; every other line continues the current one.
    If the section heading glued footnote 1's "[1]" marker (fn1_glued), the
    first classified note line is assigned fn=1 even though it carries no
    bracket of its own.
    """
    notes: dict[int, dict] = {}
    current: dict | None = None
    last_fn = 0
    gap_tol = 8
    first_note = True

    for raw in note_lines:
        line = raw.rstrip()
        if not line.strip() or _PAGENUM_RE.match(line):
            continue
        m = _ENDNOTE_RE.match(line)
        fn = int(m.group("fn")) if (m and m.group("fn")) else None
        if m and fn is None and first_note and fn1_glued:
            fn = 1
        is_start = m is not None and fn is not None and last_fn < fn <= last_fn + gap_tol
        if is_start:
            current = {
                "fn": fn, "chapter": int(m.group("ch")), "verse": int(m.group("v")),
                "pada": m.group("pada"), "text": m.group("text"),
            }
            notes[fn] = current
            last_fn = fn
            first_note = False
        elif current is not None:
            current["text"] += " " + line.strip()
        # else: preamble noise before the first recognised note -- ignore.

    for n in notes.values():
        n["text"] = re.sub(r"\s+", " ", n["text"]).strip()
    return notes


def link_footnotes(text: str, fn_numbers: set[int], used: set[int]):
    """Replace ``[N]`` inline footnote refs with sup-link HTML; return
    (clean_text, html_text, refs). Only refs that are real, unconsumed
    footnote numbers for this chapter are linked -- see module docstring."""
    refs: list[int] = []
    # Real private-use-area sentinels (not empty strings -- an empty sentinel
    # would make the "strip consumed refs" regex below match ANY digit run,
    # including an unconsumed/unknown ref's own bracketed number).
    _L, _R = "", ""

    def _repl(mo):
        num = int(mo.group(1))
        if num in fn_numbers and num not in used:
            used.add(num)
            refs.append(num)
            return f"{_L}{num}{_R}"
        return mo.group(0)

    marked = _INLINE_FN_RE.sub(_repl, text)
    clean = re.sub(_L + r"\d+" + _R, "", marked)
    clean = re.sub(r"\s+", " ", clean).strip()

    def _htmlref(mo):
        num = mo.group(1)
        return ("<a href='#comment_" + num + "' class='comment_sub'>"
                "<sup><small>" + num + "</small></sup></a>")

    html_text = _htmllib.escape(marked, quote=False)
    html_text = re.sub(_L + r"(\d+)" + _R, _htmlref, html_text)
    return clean, html_text, refs


def parse_book(text: str, work_slug: str) -> tuple[list[dict], dict]:
    """Parse one Ignatjev single-book translation into (records, report)."""
    lines = text.split("\n")
    n = len(lines)

    # A table-of-contents entry near the top of the file ("Содержание") can
    # read as a bare "Комментарий" line too -- search for the endnote-block
    # heading only from the LAST chapter-opening heading onward, so the real
    # section (which always follows the last chapter) is the one found.
    last_chapter_idx = max(
        (i for i, ln in enumerate(lines) if _is_chapter_open(ln)),
        default=0,
    )

    # Back matter (СЛОВАРЬ ИМЕН / СЛОВАРЬ ТЕРМИНОВ / ЛИТЕРАТУРА / ... -- or an
    # appendix of quoted hymns from OTHER named works, e.g. Йони-тантра's
    # "ТЕКСТЫ ПО ПОЧИТАНИЮ ЙОНИ") closes the body even when there is NO
    # endnote section to anchor on (Nirvāṇa-tantra has none) -- otherwise a
    # glossary/bibliography/appendix entry's own parenthesised number can be
    # mistaken for a trailing verse marker and glued onto the last chapter.
    # Found FIRST (from the last chapter opening onward), independent of the
    # notes-heading search below, so a work's true content boundary is
    # whichever of the two actually comes first structurally.
    # Start the back-matter scan AFTER the last chapter heading, skipping
    # blank lines and one optional ALL-CAPS running title that sits on the
    # next line (e.g. Kulārṇava ch.8 "О ТРЕХ ТАТТВАХ, РАЗЛИЧНЫХ ВИДАХ ВИНА
    # И ИНОМ"). That title matches _BACKMATTER_RE by construction (7+
    # uppercase Cyrillic chars) and, if accepted, would set body_end to the
    # title line and empty the entire last chapter. Real back-matter
    # (СЛОВАРЬ / ЛИТЕРАТУРА / ОБ АВТОРЕ / appendix of other works) always
    # appears later, after verse body.
    backmatter_idx = None
    scan_from = last_chapter_idx + 1
    while scan_from < n and not lines[scan_from].strip():
        scan_from += 1
    if scan_from < n and _BACKMATTER_RE.match(lines[scan_from]):
        scan_from += 1  # skip the last chapter's own ALL-CAPS title
    for i in range(scan_from, n):
        if _BACKMATTER_RE.match(lines[i]):
            backmatter_idx = i
            break

    # Locate the endnote block: the first "Комментарий"/"Примечания" heading
    # after the last chapter, up to the first back-matter heading (or EOF).
    # Bounded ABOVE by backmatter_idx, not just EOF: an appendix of quoted
    # material from other works can carry its own, LATER "Комментарий"
    # section for ITS OWN citations (Йони-тантра ch.8's true colophon sits at
    # backmatter_idx, but a stray "КОММЕНТАРИЙ" for the appended hymns turns
    # up ~140 lines further on) -- an unbounded search would treat that as
    # *this* work's endnotes and drag the body all the way out to it.
    search_end = backmatter_idx if backmatter_idx is not None else n
    notes_start = notes_end = None
    fn1_glued = False
    for i in range(last_chapter_idx, search_end):
        hm = _NOTES_HEAD_RE.match(lines[i])
        if hm:
            notes_start = i + 1
            fn1_glued = hm.group("fn1") is not None
            break
    if notes_start is not None:
        j = notes_start
        while j < n and not _BACKMATTER_RE.match(lines[j]):
            j += 1
        notes_end = j
    note_lines = lines[notes_start:notes_end] if notes_start is not None else []
    fn_map = parse_endnotes(note_lines, fn1_glued) if note_lines else {}

    if notes_start is not None:
        body_end = notes_start - 1
    elif backmatter_idx is not None:
        body_end = backmatter_idx
    else:
        body_end = n

    # Walk the body: cut at chapter-opening headings. The FIRST chapter
    # opening marks the true start of the work (front matter -- title page,
    # table of contents, preface -- precedes it and is discarded).
    # ToC leader-dot lines are rejected by _is_chapter_open (see below).
    chapters: list[dict] = []
    cur: dict | None = None
    idx = 0
    while idx < body_end:
        line = lines[idx]
        om = _is_chapter_open(line)
        if om:
            if cur is not None:
                chapters.append(cur)
            onum = ordinal_f_to_int(om.group("ord"))
            cur = {"chapter": onum, "body": []}
            # Keep trailing body text glued onto the heading line (the
            # pre-existing rest-group behaviour of _CHAPTER_OPEN_RE).
            rest = (om.group("rest") or "").strip()
            if rest:
                cur["body"].append(rest)
        elif cur is not None:
            cur["body"].append(line)
        idx += 1
    if cur is not None:
        chapters.append(cur)

    # Some excerpted works (e.g. Nīlamata-purāṇa's śloka 1-411 fragment) carry
    # no "Глава <ordinal>" heading at all -- a single continuous run of
    # verses with no chapter division. Fall back to one implicit chapter 1
    # covering the whole body. A short liturgical preamble (title, "Ом
    # свасти", invocations) before the first verse's trailing "(1)" marker
    # has no marker of its own to anchor a clean cut on, so it is left to
    # split_verses' normal reflow -- it becomes part of verse 1's text
    # rather than a separately-dropped chunk. Harmless (an invocation glued
    # onto verse 1 is not unusual for these texts) and, critically, lossless
    # -- an earlier version that tried to strip it by cutting AT the first
    # "(1)" line silently deleted verse 1 itself.
    if not chapters:
        chapters = [{"chapter": 1, "body": lines[:body_end]}]

    records: list[dict] = []
    report = {
        "work": work_slug, "chapters": 0, "verse_count": 0, "comment_count": 0,
        "verse_gaps": [], "chapter_numbers": [], "unrecognised_endnotes": 0,
    }
    seq = 0
    seen_passages: set[str] = set()
    all_fn = set(fn_map)
    used_fn: set[int] = set()

    for ch in chapters:
        if ch["chapter"] is None:
            report.setdefault("warnings", []).append(
                f"unrecognised chapter ordinal, body dropped: {ch['body'][:1]}")
            continue
        chn = ch["chapter"]
        body = _reflow(ch["body"])
        verses = split_verses(body)
        fn_numbers = {fn for fn, note in fn_map.items() if note["chapter"] == chn}
        report["chapters"] += 1
        report["chapter_numbers"].append(chn)

        prev_v = 0
        for v in verses:
            seq += 1
            label = v["verse"].replace(" ", "")
            if "-" in label or "–" in label:
                passage = f"{chn}.{re.split(r'[-–]', label)[0]}-{re.split(r'[-–]', label)[1]}"
            else:
                passage = f"{chn}.{label}"
            if passage in seen_passages:
                report.setdefault("id_collisions", []).append(passage)
                suffix = "b"
                while f"{passage}{suffix}" in seen_passages:
                    suffix = chr(ord(suffix) + 1)
                passage = f"{passage}{suffix}"
            seen_passages.add(passage)
            group = f"{work_slug}:{passage}"
            clean, html_text, _refs = link_footnotes(v["text"], fn_numbers, used_fn)
            rec = {
                "id": f"{work_slug}:{passage}#ru", "work": work_slug,
                "passage": passage, "seg": "ru", "group": group, "lang": "ru",
                "script": "cyrillic", "text": clean, "html": html_text,
                "structure": "verse", "chapter": str(chn), "seq": seq,
                "deleted": False,
            }
            if v["author"]:
                rec["author"] = v["author"]
            records.append(rec)
            report["verse_count"] += 1
            try:
                vv = int(re.split(r"[-–]", label)[0])
                if prev_v and vv not in (prev_v + 1, prev_v):
                    report["verse_gaps"].append(f"{chn}: {prev_v}->{vv}")
                prev_v = int(re.split(r"[-–]", label)[-1])
            except ValueError:
                pass

        # H1828: resolve endnote targets to passages actually emitted this chapter.
        chapter_passages = sorted(
            p for p in seen_passages
            if p.startswith(f"{chn}.") and ".comm" not in p
        )
        comm_by_verse: dict[str, list[tuple[int, dict]]] = {}
        for fn, note in sorted(fn_map.items()):
            if note["chapter"] != chn:
                continue
            annot = f"{chn}.{note['verse']}"
            annot = _resolve_flat_annotates(annot, chapter_passages, chn)
            comm_by_verse.setdefault(annot, []).append((fn, note))
        for annot, items in comm_by_verse.items():
            for k, (fn, note) in enumerate(items, 1):
                seq += 1
                cid = f"{work_slug}:{annot}.comm{k}"
                html_c = (
                    f'<span class="comment_number" '
                    f'title="{work_slug} (А. Игнатьев): {fn}">{fn}. </span>'
                    f'<span class="comment_text">'
                    f'{_htmllib.escape(note["text"], quote=False)}</span>'
                )
                records.append({
                    "id": cid, "work": work_slug, "passage": f"{annot}.comm{k}",
                    "seg": f"comm{k}", "group": f"{work_slug}:{annot}",
                    "lang": "ru", "script": "cyrillic", "text": note["text"],
                    "html": html_c, "structure": "verse", "chapter": str(chn),
                    "annotates": annot, "fn": fn, "seq": seq, "deleted": False,
                })
                report["comment_count"] += 1

    report["unrecognised_endnotes"] = len(all_fn - used_fn - {
        fn for fn, note in fn_map.items()
        if note["chapter"] not in {c["chapter"] for c in chapters if c["chapter"]}
    }) if all_fn else 0
    report["total_endnotes"] = len(all_fn)
    return records, report


def _resolve_flat_annotates(annot: str, chapter_passages: list[str], chn: int) -> str:
    """Map flat CHAPTER.VERSE annotates onto an emitted passage (H1828)."""
    if annot in chapter_passages:
        return annot
    if not chapter_passages:
        return annot

    def _vkey(p: str) -> int:
        tail = p.split(".", 1)[-1]
        m = re.match(r"(\d+)", tail)
        return int(m.group(1)) if m else 0

    target = _vkey(annot)
    return min(chapter_passages, key=lambda p: (abs(_vkey(p) - target), _vkey(p)))


def parse_parts(paths: list[Path], work_slug: str) -> tuple[list[dict], dict]:
    """Parse one or more source files of a multi-part work.

    Each file is parsed independently (so part-1 endnotes / back-matter are
    bound to part-1's last chapter and never leak into part-2's body), then
    records and report counters are merged. Chapter numbers are expected to
    continue across parts (Ignatiev's "Часть первая/вторая" convention), not
    restart.
    """
    if len(paths) == 1:
        return parse_book(extract_text(paths[0]), work_slug)

    all_records: list[dict] = []
    merged = {
        "work": work_slug,
        "chapters": 0,
        "verse_count": 0,
        "comment_count": 0,
        "verse_gaps": [],
        "chapter_numbers": [],
        "unrecognised_endnotes": 0,
        "id_collisions": [],
        "total_endnotes": 0,
        "parts": [],
    }
    seen_passages: dict[str, int] = {}
    for path in paths:
        text = extract_text(path)
        recs, rep = parse_book(text, work_slug)
        # Re-seq across parts so build_corpus_html's order is stable.
        base_seq = len(all_records)
        for r in recs:
            r["seq"] = base_seq + r.get("seq", 0)
            # Surface cross-part passage collisions (should not happen if
            # chapter numbers continue rather than restart).
            if r.get("seg") == "ru":
                psg = r.get("passage", "")
                seen_passages[psg] = seen_passages.get(psg, 0) + 1
        all_records.extend(recs)
        merged["chapters"] += rep.get("chapters", 0)
        merged["verse_count"] += rep.get("verse_count", 0)
        merged["comment_count"] += rep.get("comment_count", 0)
        merged["verse_gaps"].extend(rep.get("verse_gaps") or [])
        merged["chapter_numbers"].extend(rep.get("chapter_numbers") or [])
        merged["unrecognised_endnotes"] += rep.get("unrecognised_endnotes", 0)
        merged["id_collisions"].extend(rep.get("id_collisions") or [])
        merged["total_endnotes"] += rep.get("total_endnotes", 0)
        merged["parts"].append({
            "path": str(path),
            "chapters": rep.get("chapters", 0),
            "verse_count": rep.get("verse_count", 0),
            "chapter_numbers": rep.get("chapter_numbers") or [],
        })
    cross = [p for p, n in seen_passages.items() if n > 1]
    if cross:
        merged["id_collisions"].extend(cross)
        merged["cross_part_collisions"] = cross
    return all_records, merged


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, nargs="+",
                     help="one or more source files, in reading order "
                          "(multi-part works are parsed per-file then merged)")
    ap.add_argument("--work-slug", required=True)
    ap.add_argument("--output-dir", default="web/corpus_builder/jsonl")
    ap.add_argument("--stdout-report", action="store_true")
    args = ap.parse_args()

    src_paths = [Path(p) for p in args.input]
    records, report = parse_parts(src_paths, args.work_slug)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / f"{args.work_slug}.raw.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    report_path = out_dir / f"{args.work_slug}.report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"{args.work_slug}: {report['chapters']} chapters, "
          f"{report['verse_count']} verses, {report['comment_count']} comments "
          f"({report.get('total_endnotes', 0)} endnotes found, "
          f"{report.get('unrecognised_endnotes', 0)} unattached) -> {jsonl_path}")
    if args.stdout_report:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
