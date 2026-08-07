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
* **Endnotes are real Word footnotes (default ``bracket`` mode).** Pandoc's
  plain-text writer renders both the inline reference and the collected note
  text bracket-wrapped (``...его[1].`` in the body; ``[1] 1.1(1). <text>``
  in the endnote block) -- an exact ``[N]`` match, simpler and more reliable
  than the DBhP PDF's glued-digit superscript heuristic. Footnote 1 is a
  known pandoc quirk: its ``[1]`` marker lands glued to the endnote *section
  heading* rather than its own note line -- handled as a special case,
  matching the DBhP script's "keep every verse, itemize anomalies in the
  report" policy (a missed footnote never blocks a chapter/verse from being
  emitted).
* **Glued-digit page-local footnotes (``glued-digit`` mode, H2377).** Some
  PDF pressings (Māyā-tantra) put footnotes at the bottom of nearly every
  page in the OLD DBhP-style convention: inline refs are digits glued to
  words (``другую6``), and note bodies start ``N ch.v(pada). text`` (or
  ``Nch.v`` when the space is lost). The single end-of-work
  ``_NOTES_HEAD_RE`` search cannot see those blocks, so they used to pollute
  every chapter body and fake ``(N)`` verse boundaries. Mode
  ``glued-digit`` strips per-page note regions first, then links inline
  digits with the DBhP heuristic. ``--footnote-mode auto`` (default)
  picks ``glued-digit`` when mid-body page-local note-start lines are
  dense, else ``bracket``.

Usage:
    python web/corpus_builder/ignatiev_book_to_canonical.py \
        --input "archive_ignatiev_2026/.../Чиначара-тантра.docx" \
        --work-slug chinachara-tantra \
        --output-dir web/corpus_builder/jsonl
    # Māyā-tantra (or any page-local glued-digit PDF):
    python web/corpus_builder/ignatiev_book_to_canonical.py \
        --input ".../Майя-тантра.pdf" --work-slug maya-tantra \
        --footnote-mode glued-digit

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

from ru_ordinals import (  # noqa: E402
    ordinal_f_to_int,
    ORDINAL_WORD_PATTERN,
    _UNITS_F,
    _TENS_PREFIX,
)

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
    r"Глава\s+(?:"
    # H2376 Bhāgavata partial: "ГЛАВА 14" (digit) as well as word ordinals.
    r"(?P<ord_num>\d{1,3})"
    r"|(?P<ord>" + ORDINAL_WORD_PATTERN +
    r"(?:\s+" + ORDINAL_WORD_PATTERN + r")?)"
    r")"
    r"(?:\s+(?-i:(?P<title>[А-ЯЁ][А-ЯЁ0-9 ,.\-]{1,90})))?"
    r"(?:\s+(?P<rest>\S.*))?"
    # H2376: RTF/print sources often end the heading with a full stop
    # ("ГЛАВА ВТОРАЯ.") — without this the whole open fails and the chapter
    # falls into the implicit-ch.1 bag.
    r"\s*[.…]*\s*$",
    re.IGNORECASE,
)

# Excerpt heading: "Из двадцать второй главы" (H2376 Devī-purāṇa ch.22).
# Genitive ordinal + genitive «главы»; no body text on the same line.
_CHAPTER_FROM_RE = re.compile(
    r"^\s*Из\s+(?P<ord>" + ORDINAL_WORD_PATTERN +
    r"(?:\s+" + ORDINAL_WORD_PATTERN + r")?)"
    r"\s+глав[аыуе]?\s*[.…]*\s*$",
    re.IGNORECASE,
)

# Table-of-contents lines look like "Глава восьмая ……… 48" — same ordinal
# form as a real chapter opening, but the leader-dot / page-number tail is a
# reliable negative signal. Rejecting them here keeps multi-part works from
# inventing empty chapters out of their own ToC (Yoginī 1-7 + 8-19, Kulārṇava).
_TOC_LEADER_RE = re.compile(r"[.…·•]{3,}|\s{2,}\d{1,4}\s*$")

# Colophon line that OLE/PDF sometimes leaves inside the body with a false
# high-N ``(N)`` marker (H2353 Kālikā ch.20: ``...заканчивается двадцатая
# глава... (1401-1464)``). Not a real verse.
_COLOPHON_BODY_RE = re.compile(
    r"Так\s+в\s+\S.+\s+заканчивается\s+",
    re.IGNORECASE,
)


def _peel_glued_unit_ordinal(ord_phrase: str, rest: str) -> tuple[str, str]:
    """Recover a compound ordinal when OLE/PDF glues the unit onto body text.

    H2353: OLE extract of Kālikā-purāṇa ch.62 produced
    ``Глава шестьдесят втораяовно свинцовый...`` — the second ordinal word
    ``вторая`` is glued to the chapter's first body word with no space, so
    the chapter-open regex captures only the tens prefix ``шестьдесят``
    (not itself a full ordinal — ``ordinal_f_to_int`` returns None) and the
    whole chapter body is dropped. Peel a known unit ordinal off the front
    of ``rest`` when the captured ``ord`` is a bare tens prefix.
    """
    if not rest:
        return ord_phrase, rest
    if ordinal_f_to_int(ord_phrase) is not None:
        return ord_phrase, rest
    tens = _TENS_PREFIX.get(ord_phrase.strip().lower().replace("ё", "е"))
    if tens is None:
        tens = _TENS_PREFIX.get(ord_phrase.strip().lower())
    if tens is None:
        return ord_phrase, rest
    rest_norm = rest.lower().replace("ё", "е")
    for unit in sorted(_UNITS_F, key=len, reverse=True):
        unit_norm = unit.replace("ё", "е")
        if rest_norm.startswith(unit_norm):
            peeled = f"{ord_phrase.strip()} {unit}"
            if ordinal_f_to_int(peeled) is not None:
                return peeled, rest[len(unit_norm):].lstrip()
    return ord_phrase, rest


class _ChapterOpen:
    """Lightweight stand-in for a regex match with the same ``.group(name)``
    API, so callers keep working after glued-ordinal peeling rewrites ``ord``
    / ``rest``.
    """

    __slots__ = ("_g",)

    def __init__(self, ord_s, rest_s, title, prefix):
        self._g = {
            "ord": ord_s,
            "rest": rest_s,
            "title": title,
            "prefix": prefix,
        }

    def group(self, name):
        return self._g.get(name)


def _is_chapter_open(line: str):
    """Match a real chapter-opening heading, or None for ToC / non-matches.

    Returns a match-like object (``.group(name)``) on success. ToC leader-dot
    lines (and lines whose 'rest' is only a bare page number) are rejected
    even though they satisfy the raw ordinal form.

    On OLE/PDF glue where the unit ordinal is fused to the first body word
    (H2353 Kālikā ch.62), peels the unit off ``rest`` so the chapter is not
    silently dropped.

    H2376: also matches excerpt headings «Из <ordinal gen> главы» and
    allows a trailing full stop after the ordinal («ГЛАВА ВТОРАЯ.»).
    """
    m = _CHAPTER_OPEN_RE.match(line)
    if m:
        rest = (m.group("rest") or "").strip()
        if rest and _TOC_LEADER_RE.search(rest):
            return None
        # "Глава восьмая ………………………………………………………………48" puts the leaders in
        # the title group when they start with a non-letter — also catch the
        # whole-line form.
        if _TOC_LEADER_RE.search(line):
            return None
        # Digit form "Глава 14" (H2376 Bhāgavata) — synthesise a phrase the
        # walk loop can turn into an int via a numeric short-circuit.
        if m.group("ord_num"):
            return _ChapterOpen(
                m.group("ord_num"), rest or None,
                m.group("title"), m.group("prefix"))
        ord_phrase, rest = _peel_glued_unit_ordinal(m.group("ord") or "", rest)
        # Bare tens-prefix alone is not a usable chapter open (would become
        # chapter=None and drop the body).
        if ordinal_f_to_int(ord_phrase) is None:
            return None
        return _ChapterOpen(
            ord_phrase, rest or None, m.group("title"), m.group("prefix"))
    # Excerpt form: "Из двадцать второй главы" (H2376 Devī-purāṇa).
    fm = _CHAPTER_FROM_RE.match(line)
    if fm:
        ord_phrase = fm.group("ord")
        if ordinal_f_to_int(ord_phrase) is None:
            return None
        return _ChapterOpen(ord_phrase, None, None, None)
    return None

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

# --- glued-digit page-local footnotes (H2377 / Māyā-tantra) -----------------
#
# Mode name: ``glued-digit``. Detection signal + rejected alternatives: see
# docs/MAYA_TANTRA_GLUED_DIGIT_MODE_H2377.md.
#
# Strong note-start: ``N ch.v(pada). text`` with a space after N (DBhP PDF),
# or the space-lost form ``Nch.v(pada). text`` (``61.1(1).`` = fn 6 + 1.1(1)).
# ALL-CAPS ``КОММЕНТАРИЙ`` alone on a line is an optional block head (rare
# in Māyā — only the first page of ch.1 uses it). Title-case TOC
# ``Комментарий`` is deliberately NOT a block head.

_GLUED_NOTES_HEAD_RE = re.compile(r"^\s*КОММЕНТАРИ[ЙИ]\s*$")
_SPACED_GLUED_NOTE_RE = re.compile(
    r"^\s*(?P<fn>\d{1,3})\s+(?P<ch>\d+)\.\s?(?P<v>\d+)"
    r"(?:\s*[-–]\s*\d+)?(?:\((?P<pada>[^)]{0,10})\))?\.\s*(?P<text>.*)"
)
_VERSE_END_LINE_RE = re.compile(r"\(\d+(?:\s*[-–]\s*\d+)?\)\s*$")
_FN_GAP_TOL_GLUED = 8
# Auto-detect thresholds (H2377). Tuned so Māyā (~60 pages with bottom
# notes, ~140 strong starts) selects glued-digit, while Wave-A PDF tantras
# that only have a few coincidental ``N ch.v`` shapes in end-matter stay on
# ``bracket`` (regression: nirvāṇa-tantra must not flip).
_AUTO_GLUED_MIN_STRONG_NOTES = 40
_AUTO_GLUED_MIN_PAGES_WITH_NOTES = 20


def _is_strong_glued_note_start(line: str) -> bool:
    """True if *line* starts a DBhP/Māyā page-local footnote body."""
    if _SPACED_GLUED_NOTE_RE.match(line):
        return True
    s = line.strip()
    for flen in (1, 2, 3):
        if len(s) <= flen or not s[:flen].isdigit():
            continue
        # no space between fn and chapter (``61.1(1).``)
        if s[flen:flen + 1].isspace():
            continue
        rest = s[flen:]
        if re.match(r"\d+\.\s?\d+(?:\s*[-–]\s*\d+)?(?:\([^)]{0,10}\))?\.", rest):
            return True
    return False


def _parse_strong_glued_note_start(
    line: str, last_fn: int,
) -> tuple[int, int | None, int | None, str | None, str] | None:
    """Parse a note-start line under a monotonic fn gate.

    Returns ``(fn, chapter, verse, pada, text)`` or None. For the glued form
    ``61.1(1).``, tries expected fn = last_fn+1 .. last_fn+_FN_GAP_TOL so
    ``6``+``1.1(1)`` wins over the false ``61``+``.1(1)`` reading.
    """
    m = _SPACED_GLUED_NOTE_RE.match(line)
    if m:
        fn = int(m.group("fn"))
        if last_fn < fn <= last_fn + _FN_GAP_TOL_GLUED:
            return (
                fn, int(m.group("ch")), int(m.group("v")),
                m.group("pada"), (m.group("text") or "").strip(),
            )
        return None
    s = line.strip()
    for expected in range(last_fn + 1, last_fn + _FN_GAP_TOL_GLUED + 1):
        token = str(expected)
        if not s.startswith(token):
            continue
        rest = s[len(token):]
        m2 = re.match(
            r"^(?P<ch>\d+)\.\s?(?P<v>\d+)"
            r"(?:\s*[-–]\s*\d+)?(?:\((?P<pada>[^)]{0,10})\))?\.\s*(?P<text>.*)",
            rest,
        )
        if m2:
            return (
                expected, int(m2.group("ch")), int(m2.group("v")),
                m2.group("pada"), (m2.group("text") or "").strip(),
            )
    # fn-only gloss with no ch.v target: ``12 Лакуна в оригинале.``
    m3 = re.match(
        r"^\s*(?P<fn>\d{1,3})\s+(?P<text>[А-Яа-яЁё«\[\*].+)$", line,
    )
    if m3:
        fn = int(m3.group("fn"))
        if last_fn < fn <= last_fn + _FN_GAP_TOL_GLUED:
            return fn, None, None, None, m3.group("text").strip()
    return None


def _find_page_notes_start(lines: list[str]) -> int | None:
    """Index of the first page-local footnote line, or None if the page has none.

    Notes sit at the page bottom. Start at the first strong note-start (or
    ALL-CAPS ``КОММЕНТАРИЙ``), then walk backward over note-continuation
    lines left over from the previous page's last note.
    """
    for i, ln in enumerate(lines):
        if _GLUED_NOTES_HEAD_RE.match(ln):
            return i
    first_ns = None
    for i, ln in enumerate(lines):
        if _is_strong_glued_note_start(ln):
            first_ns = i
            break
    if first_ns is None:
        return None
    i = first_ns
    while i > 0:
        prev = lines[i - 1].strip()
        if not prev or _PAGENUM_RE.match(prev):
            i -= 1
            continue
        if _VERSE_END_LINE_RE.search(prev):
            break
        if re.match(r"^Глава\s+", prev, re.IGNORECASE):
            break
        # bare ALL-CAPS running title (not a note continuation)
        if re.match(r"^[А-ЯЁ][А-ЯЁ.\s\-]{5,50}$", prev):
            break
        i -= 1
    return i


def strip_glued_digit_page_notes(
    text: str,
) -> tuple[str, dict[int, dict], dict]:
    """Front-end: peel per-page footnote blocks out of *text*.

    Returns ``(body_text, fn_map, stats)``. ``fn_map`` keys are footnote
    numbers; values carry ``chapter``/``verse``/``pada``/``text`` (chapter/
    verse may be None for fn-only glosses — attached later via nearest).
    Page boundaries are form-feeds (``\\x0c``), as emitted by pdftotext and
    the pymupdf fallback.
    """
    pages = text.split("\x0c")
    body_parts: list[str] = []
    note_lines: list[str] = []
    pages_with_notes = 0
    for page in pages:
        lines = page.split("\n")
        ns = _find_page_notes_start(lines)
        if ns is None:
            body_parts.extend(lines)
        else:
            pages_with_notes += 1
            body_parts.extend(lines[:ns])
            note_lines.extend(lines[ns:])
        body_parts.append("")  # page separator as blank line

    fn_map = parse_glued_digit_endnotes(note_lines)
    stats = {
        "footnote_mode": "glued-digit",
        "pages_total": len(pages),
        "pages_with_notes": pages_with_notes,
        "strong_note_starts": sum(
            1 for ln in note_lines if _is_strong_glued_note_start(ln)
        ),
        "total_endnotes": len(fn_map),
    }
    return "\n".join(body_parts), fn_map, stats


def parse_glued_digit_endnotes(note_lines: list[str]) -> dict[int, dict]:
    """Parse stripped page-local note lines into ``{fn: note_dict}``."""
    notes: dict[int, dict] = {}
    current: dict | None = None
    last_fn = 0
    for raw in note_lines:
        line = raw.rstrip()
        if not line.strip() or _PAGENUM_RE.match(line):
            continue
        if _GLUED_NOTES_HEAD_RE.match(line):
            continue
        info = _parse_strong_glued_note_start(line, last_fn)
        if info is not None:
            fn, ch, v, pada, text = info
            # If chapter/verse missing, inherit from previous note (fn-only
            # glosses like ``12 Лакуна`` sit next to the verse they annotate).
            if ch is None and current is not None:
                ch = current.get("chapter")
                v = current.get("verse")
            current = {
                "fn": fn, "chapter": ch, "verse": v, "pada": pada, "text": text,
            }
            notes[fn] = current
            last_fn = fn
        elif current is not None:
            current["text"] += " " + line.strip()
    for n in notes.values():
        n["text"] = re.sub(r"\s+", " ", n["text"]).strip()
        # Strip a leading ``N ch.v`` echo left in text when the classifier
        # consumed only part of a glued header (defensive).
        n["text"] = re.sub(
            r"^\d+\s+\d+\.\s?\d+(?:\([^)]*\))?\.\s*", "", n["text"],
        ).strip()
        # fn-only glosses with no inherit target: park on 1.1 rather than
        # drop (annotates nearest will move them if needed).
        if n.get("chapter") is None:
            n["chapter"] = 1
        if n.get("verse") is None:
            n["verse"] = 1
    return notes


def detect_footnote_mode(text: str) -> str:
    """``auto`` detector for page-local glued-digit footnotes (H2377).

    Returns ``bracket`` by default. Several Wave-A PDFs (Nirvāṇa, Yoni, …)
    also carry page-local notes whose counts were frozen under the old
    bracket + H1829 path; flipping them automatically would fail the
    regression gate. Callers that want the front-end on a known Māyā-class
    work must pass ``--footnote-mode glued-digit`` explicitly.

    The density signals below are still computed and exposed via
    ``glued_digit_stats`` when the mode is forced, and the design note
    documents how to re-enable a riskier auto later (dry-run gap/osc
    signature after a Wave-A re-baseline).
    """
    del text  # reserved for a future density-based auto re-enable
    return "bracket"


def glued_digit_signal(text: str) -> dict:
    """Diagnostic density of page-local note markers (does not select mode)."""
    pages = text.split("\x0c") if "\x0c" in text else [text]
    pages_with = 0
    strong = 0
    for page in pages:
        lines = page.split("\n")
        strong += sum(1 for ln in lines if _is_strong_glued_note_start(ln))
        if _find_page_notes_start(lines) is not None:
            pages_with += 1
    return {
        "pages_total": len(pages),
        "pages_with_notes": pages_with,
        "strong_note_starts": strong,
        "would_suggest_glued_digit": (
            pages_with >= _AUTO_GLUED_MIN_PAGES_WITH_NOTES
            and strong >= _AUTO_GLUED_MIN_STRONG_NOTES
        ),
    }


def link_footnotes_glued(text: str, fn_numbers: set[int], used: set[int]):
    """DBhP-style: strip digits glued to Cyrillic/bracket/quote ends.

    Mirrors ``ignatjev_pdf_to_canonical.link_footnotes``. Only consumes a
    digit run when its value is a still-unused real footnote number.
    """
    refs: list[int] = []
    _L, _R = "", ""

    def _repl(mo):
        num = int(mo.group(2))
        if num in fn_numbers and num not in used:
            used.add(num)
            refs.append(num)
            return f"{mo.group(1)}{_L}{num}{_R}"
        return mo.group(0)

    marked = re.sub(r"([А-яёЁ»\)\]])(\d{1,3})(?![\d(])", _repl, text)
    clean = re.sub(_L + r"\d+" + _R, "", marked)
    clean = re.sub(r"\s+", " ", clean).strip()

    def _htmlref(mo):
        num = mo.group(1)
        return (
            "<a href='#comment_" + num + "' class='comment_sub'>"
            "<sup><small>" + num + "</small></sup></a>"
        )

    html_text = _htmllib.escape(marked, quote=False)
    html_text = re.sub(_L + r"(\d+)" + _R, _htmlref, html_text)
    return clean, html_text, refs


# antiword wall-clock budget for a single .doc (H2352). Large multi-MB
# Ignatiev files stay well under this; a hung process is a hard error.
_ANTIWORD_TIMEOUT_S = 120


def _extract_doc_ole_utf16(path: Path) -> str:
    """Best-effort body extract from a Word 97-2003 .doc via the OLE
    WordDocument stream (UTF-16LE). Used when antiword is absent and Word
    COM cannot open the file (common on Office 2007 + nested ObjectPool
    docs). Not a full piece-table parser — good enough for Ignatiev's
    plain-prose scholarly translations where chapter headings and ``(N)``
    verse markers survive as contiguous UTF-16 runs. Requires ``olefile``.
    """
    try:
        import olefile  # lazy: only needed for the .doc fallback path
    except ImportError as e:
        raise RuntimeError(
            f"cannot extract .doc {path}: antiword not on PATH and "
            f"olefile is not installed (pip install olefile)"
        ) from e

    try:
        ole = olefile.OleFileIO(str(path))
    except Exception as e:
        raise RuntimeError(f"cannot open .doc as OLE compound file: {path}") from e
    try:
        if not ole.exists("WordDocument"):
            raise RuntimeError(f"no WordDocument stream in {path}")
        data = ole.openstream("WordDocument").read()
    finally:
        ole.close()
    if not data:
        raise RuntimeError(f"empty WordDocument stream in {path}")
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
    text = text.strip()
    if not text:
        raise RuntimeError(
            f"OLE UTF-16 extract produced empty text for {path} "
            f"(not a silent empty string)"
        )
    return text + "\n"


def _extract_doc_antiword(path: Path) -> str:
    """Run antiword on a legacy .doc; raise RuntimeError with path on failure.

    Encoding: ``-m cp1251.txt`` + decode as cp1251 — Ignatiev's archive is
    Russian Windows Word. Requires ``ANTIWORDHOME`` pointed at the mapping
    directory (derived from the binary's install prefix).
    """
    antiword_bin = shutil.which("antiword")
    if not antiword_bin:
        raise FileNotFoundError("antiword not on PATH")
    mapping_dir = str(Path(antiword_bin).parent.parent / "share" / "antiword")
    env = {**os.environ, "ANTIWORDHOME": mapping_dir}
    try:
        out = subprocess.run(
            [antiword_bin, "-m", "cp1251.txt", "-w", "0", str(path)],
            capture_output=True,
            timeout=_ANTIWORD_TIMEOUT_S,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            f"antiword timed out after {_ANTIWORD_TIMEOUT_S}s on {path}"
        ) from e
    if out.returncode != 0:
        err = (out.stderr or b"").decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"antiword failed (exit {out.returncode}) on {path}"
            + (f": {err}" if err else "")
        )
    text = out.stdout.decode("cp1251", errors="replace").strip()
    if not text:
        raise RuntimeError(f"antiword returned empty text for {path}")
    return text + "\n"


def _extract_pdf_pymupdf(path: Path) -> str:
    """pdftotext fallback via PyMuPDF; form-feed between pages (H2377)."""
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise RuntimeError(
            f"cannot extract PDF {path}: pdftotext not on PATH and "
            f"pymupdf is not installed (pip install pymupdf)"
        ) from e
    doc = fitz.open(str(path))
    try:
        parts = [doc[i].get_text("text") for i in range(doc.page_count)]
    finally:
        doc.close()
    return "\x0c".join(parts)

def _extract_pdf_pypdf(path: Path) -> str:
    """Fallback PDF text extract when ``pdftotext`` is not on PATH (H2376).

    Uses ``pypdf`` (already a host dependency for the Nirvana re-ingest path).
    Form-feeds are not produced; page breaks become newlines.
    """
    try:
        from pypdf import PdfReader  # lazy: only the no-pdftotext path
    except ImportError as e:
        raise RuntimeError(
            f"cannot extract PDF {path}: pdftotext not on PATH and "
            f"pypdf is not installed (pip install pypdf)"
        ) from e
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    text = "\n".join(pages).replace("\x0c", "\n").strip()
    if not text:
        raise RuntimeError(f"pypdf produced empty text for {path}")
    return text + "\n"


def _extract_rtf_pandoc(path: Path) -> str:
    """Extract RTF (incl. ``.doc`` files that are actually RTF — H2376).

    Pandoc's RTF reader mis-labels cp1251 body text as Latin-1 and re-encodes
    it as UTF-8, producing classic mojibake for Russian. Reverse the round-
    trip (UTF-8 → latin-1 bytes → cp1251) when the source declares
    ``\\ansicpg1251`` (Ignatiev archive default).
    """
    raw = path.read_bytes()
    if not raw.lstrip().startswith(b"{\\rtf"):
        raise RuntimeError(f"not an RTF payload: {path}")
    out = subprocess.run(
        ["pandoc", "-f", "rtf", "-t", "plain", str(path)],
        capture_output=True, check=False,
    )
    if out.returncode != 0:
        err = (out.stderr or b"").decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"pandoc RTF failed (exit {out.returncode}) on {path}"
            + (f": {err}" if err else "")
        )
    if not out.stdout:
        raise RuntimeError(f"pandoc RTF returned empty text for {path}")
    # Detect source code page from the RTF header.
    head = raw[:2048].decode("latin-1", errors="replace").lower()
    if "ansicpg1251" in head or "deflang1049" in head:
        text = out.stdout.decode("utf-8", errors="replace")
        # Pandoc re-encodes cp1251 body as Latin-1 codepoints → UTF-8.
        # Smart quotes and a few Unicode punctuation marks survive as real
        # multi-byte chars; replace those on encode so the reverse path
        # still recovers the Cyrillic mass (H2376 Bhāgavata).
        text = (
            text
            .replace("\u201c", '"').replace("\u201d", '"')
            .replace("\u2018", "'").replace("\u2019", "'")
            .replace("\u2013", "-").replace("\u2014", "-")
            .replace("\u2026", "...")
        )
        try:
            text = text.encode("latin-1", errors="strict").decode(
                "cp1251", errors="replace")
        except UnicodeEncodeError:
            # Residual non-Latin-1 chars: replace rather than keep mojibake.
            text = text.encode("latin-1", errors="replace").decode(
                "cp1251", errors="replace")
    else:
        text = out.stdout.decode("utf-8", errors="replace")
    text = text.strip()
    if not text:
        raise RuntimeError(f"RTF extract produced empty text for {path}")
    return text + "\n"


def extract_text(path: Path) -> str:
    """Extract plain UTF-8 text from a .docx / .pdf / .doc / .txt source."""
    suffix = path.suffix.lower()
    if suffix == ".txt":
        # Pre-extracted plain text (e.g. a one-shot .doc salvage, or a
        # pandoc dump parked next to the source). Read as UTF-8.
        # Preserve form-feeds if present (glued-digit page markers).
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".docx":
        out = subprocess.run(
            ["pandoc", "-f", "docx", "-t", "plain", str(path)],
            capture_output=True, encoding="utf-8", errors="replace", check=True,
        )
        return out.stdout
    if suffix == ".pdf":
        # Prefer pdftotext (form-feeds for glued-digit H2377).
        # Fall back: pymupdf (keeps page markers) then pypdf (H2376).
        if shutil.which("pdftotext"):
            out = subprocess.run(
                ["pdftotext", "-enc", "UTF-8", str(path), "-"],
                capture_output=True, encoding="utf-8", errors="replace",
                check=True,
            )
            # Keep \x0c as page markers for strip_glued_digit_page_notes.
            return out.stdout
        try:
            return _extract_pdf_pymupdf(path)
        except RuntimeError:
            return _extract_pdf_pypdf(path)
    if suffix == ".doc":
        # H2376: some archive ".doc" files are RTF with a .doc extension
        # (Bhāgavata partial). Detect by magic and route through pandoc RTF
        # before the OLE path (which correctly refuses non-OLE payloads).
        head = path.read_bytes()[:16]
        if head.lstrip().startswith(b"{\\rtf"):
            return _extract_rtf_pandoc(path)
        # Legacy binary Word (H2352). Prefer antiword (correct Cyrillic when
        # ANTIWORDHOME + -m cp1251.txt are set); fall back to an OLE
        # WordDocument UTF-16LE scan when antiword is missing, times out,
        # or returns non-zero. Never return a silent empty string — both
        # paths raise RuntimeError with the source path on failure.
        # CI policy: antiword is OPTIONAL; hermetic tests exercise the OLE
        # path with a synthetic fixture; antiword tests skip when absent.
        errors: list[str] = []
        if shutil.which("antiword"):
            try:
                return _extract_doc_antiword(path)
            except (RuntimeError, FileNotFoundError, OSError) as e:
                errors.append(f"antiword: {e}")
        try:
            return _extract_doc_ole_utf16(path)
        except RuntimeError as e:
            errors.append(f"ole: {e}")
            detail = "; ".join(errors) if errors else "no extractor available"
            raise RuntimeError(
                f"cannot extract text from .doc {path} ({detail})"
            ) from e
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


def split_verses(body: str, *, aggressive_debris: bool = False) -> list[dict]:
    """Split a chapter's running text into verse chunks. See
    ignatjev_pdf_to_canonical.split_verses (identical algorithm).

    After the raw ``(N)`` split, non-monotonic restarts are collapsed
    (H1829): footnote prose that embeds citation markers like ``1.1(2)``
    or bare ``(1)`` was being minted as new verses that re-hit verse 1/2
    and forced letter-suffix id collisions (nirvana-tantra: 284 of 361
    corpus-wide dup-suffixes). A decrease in verse number within a
    chapter is treated as footnote debris — its text is appended to the
    previous verse rather than minted as a new passage.

    ``aggressive_debris`` (H2377 glued-digit mode only) also absorbs
    scholarly note residue (``[Там же]``, botanical Latin glosses) so
    residual leaks past the page-local strip do not mint high-N false
    verses. Left off by default so Wave-A bracket re-parses stay
    count-stable against committed ``.raw.jsonl``.
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
    return _collapse_nonmonotonic_verses(
        verses, aggressive_debris=aggressive_debris,
    )


def _verse_num_start(label: str) -> int | None:
    """Leading integer of a verse label (``3``, ``3-6``); None if unparseable."""
    try:
        return int(re.split(r"[-–]", label)[0])
    except (ValueError, IndexError):
        return None


def _looks_like_footnote_debris(
    text: str, *, aggressive: bool = False,
) -> bool:
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
    # Chapter colophon left in body with a false high-N marker (H2353).
    if _COLOPHON_BODY_RE.search(t):
        return True
    if not aggressive:
        return False
    # --- H2377 aggressive extras (glued-digit mode only) ---
    if t.startswith("). ") or t.startswith(") "):
        return True
    if re.search(
        r"\[Там же|цит\.?\s*по|Goudriaan|Biernacki|"
        r"\d{4}:\s*\d|см\.\s+[А-ЯA-Z]|Индуизм\s+\d{4}",
        t,
    ):
        return True
    if re.search(r"\b[A-Z][a-z]+ [a-z]+\b", t) and len(t) > 80:
        if re.search(r"это |является |называ|означа", t):
            return True
    return False


def _collapse_nonmonotonic_verses(
    verses: list[dict], *, aggressive_debris: bool = False,
) -> list[dict]:
    """Merge false ``(N)`` splits from footnote prose (H1829 / H2273 / H2353).

    Four classes of debris:
      1. Non-monotonic restarts (e.g. 5→1, 3→1) — always merge into previous.
      2. Same-N or early-N chunks whose text looks like a footnote header /
         gloss continuation — merge; genuine same-N duplicates with real
         verse-length prose still pass through and get letter suffixes.
      3. Higher-N chunks that still look like footnote debris (H2273) —
         merge too. Without this, a false high-N footnote body (e.g. a
         gloss mis-split as ``(30)`` after real verse 6) becomes the new
         high-water mark and every later real verse 7…14 is swallowed as a
         "non-monotonic restart" into that note bag. Measured on
         nirvāṇa-tantra ch.8 pre-H1829 JSONL.
      4. Impossible forward jumps (H2353): start-N ≥ prev_end + 50 while
         prev_end ≥ 1 — a colophon/endnote marker like ``(1401-1464)`` after
         real verse 158. Drop (do not merge — colophon text is not verse).
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
            # Same-or-higher N that is still debris-shaped: absorb so a false
            # high-N footnote never becomes prev_end (class 2 + class 3).
            if (
                _looks_like_footnote_debris(text, aggressive=aggressive_debris)
                and n >= prev_end
            ):
                # Colophon debris: drop rather than glue onto the last verse.
                if _COLOPHON_BODY_RE.search(text):
                    continue
                out[-1]["text"] = (out[-1]["text"] + " " + text).strip()
                continue
            # Class 4: absurd forward jump (colophon/range misread as verse N).
            if prev_end >= 1 and n >= prev_end + 50:
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


def parse_book(
    text: str,
    work_slug: str,
    footnote_mode: str = "auto",
) -> tuple[list[dict], dict]:
    """Parse one Ignatjev single-book translation into (records, report).

    ``footnote_mode``: ``auto`` | ``bracket`` | ``glued-digit`` (H2377).
    """
    mode = footnote_mode
    glued_stats: dict = {}
    pre_fn_map: dict[int, dict] | None = None
    if mode == "auto":
        mode = detect_footnote_mode(text)
    if mode == "glued-digit":
        text, pre_fn_map, glued_stats = strip_glued_digit_page_notes(text)
    elif mode != "bracket":
        raise ValueError(
            f"unknown footnote_mode {footnote_mode!r} "
            f"(resolved {mode!r}); expected auto|bracket|glued-digit"
        )
    # Form-feeds are page markers for the glued-digit front-end; once notes
    # are stripped (or in bracket mode) treat them as plain newlines so
    # chapter/verse regexes see one line per physical line.
    text = text.replace("\x0c", "\n")
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
    if pre_fn_map is not None:
        # Glued-digit front-end already collected page-local notes; do not
        # also parse a trailing bracket end-block (would double-count).
        fn_map = pre_fn_map
        # Still cut body_end at backmatter / trailing notes heading so a
        # glossary after the last chapter is not verse-split.
        if notes_start is not None:
            body_end = notes_start - 1
        elif backmatter_idx is not None:
            body_end = backmatter_idx
        else:
            body_end = n
    else:
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
    #
    # Māyā-tantra (and some other PDFs) list bare ``Глава N`` lines in a
    # ``СОДЕРЖАНИЕ`` block with no leader dots — those would otherwise mint
    # a first empty 1..N run and then a second real run (24 chapters for a
    # 12-chapter book). Suppress chapter opens while inside that ToC window.
    _TOC_HEAD_RE = re.compile(r"^\s*СОДЕРЖАНИЕ\s*$", re.IGNORECASE)
    # Real preface heading is ALL-CAPS (``ПРЕДИСЛОВИЕ``). Title-case
    # ``Предисловие`` is only a ToC *entry* listing the preface and must
    # NOT exit the ToC window (Māyā-tantra H2377).
    _PREFACE_HEAD_RE = re.compile(r"^\s*ПРЕДИСЛОВИЕ\s*$")
    chapters: list[dict] = []
    cur: dict | None = None
    idx = 0
    in_toc = False
    while idx < body_end:
        line = lines[idx]
        if _TOC_HEAD_RE.match(line):
            in_toc = True
            idx += 1
            continue
        if in_toc and _PREFACE_HEAD_RE.match(line):
            in_toc = False
            # preface itself is front matter; keep suppressing until a real
            # chapter open with body (in_toc stays False, next chapter wins).
            idx += 1
            continue
        if in_toc:
            # Exit ToC early when a chapter open is followed by real verse
            # markers (works with no separate ПРЕДИСЛОВИЕ heading).
            om_peek = _is_chapter_open(line)
            if om_peek and _VERSE_NUM_RE.search(
                "\n".join(lines[idx: min(idx + 20, body_end)])
            ):
                in_toc = False
                # fall through and treat this line as a real chapter open
            else:
                idx += 1
                continue
        om = _is_chapter_open(line)
        if om:
            if cur is not None:
                chapters.append(cur)
            ord_raw = om.group("ord")
            if ord_raw and re.fullmatch(r"\d{1,3}", ord_raw.strip()):
                onum = int(ord_raw.strip())
            else:
                onum = ordinal_f_to_int(ord_raw)
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

    # Drop ToC ghost chapters: a bare ``Глава N`` list under СОДЕРЖАНИЕ can
    # still slip through when the ToC window is missed; those ghosts have
    # empty (or verse-marker-free) bodies and are followed by a second real
    # run of the same chapter numbers. Keep the last non-empty body per
    # chapter number (H2377 Māyā).
    if chapters:
        best: dict[int, dict] = {}
        order: list[int] = []
        for ch in chapters:
            n = ch["chapter"]
            body_text = " ".join(ch.get("body") or [])
            has_verse = bool(_VERSE_NUM_RE.search(body_text))
            if n not in best:
                best[n] = ch
                order.append(n)
            elif has_verse:
                best[n] = ch
            # else: keep the earlier entry if the new one is also empty
        # Prefer the later non-empty run's order when numbers restart.
        if len(chapters) > len(best):
            chapters = [best[n] for n in order if n in best]

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
        # H2219: audit trail for the H1828 nearest-verse annotates fallback.
        "annotates_remapped": 0, "annotates_remap_max_delta": 0,
        "annotates_remaps": [],
        "footnote_mode": mode,
        "footnote_mode_requested": footnote_mode,
    }
    if glued_stats:
        report["glued_digit_stats"] = glued_stats
    seq = 0
    seen_passages: set[str] = set()
    all_fn = set(fn_map)
    used_fn: set[int] = set()
    # Glued-digit notes are book-global (fn numbers rise across chapters);
    # bracket endnotes are scoped per chapter in the pandoc block. Inline
    # linking: glued mode may see any remaining unused fn; bracket mode
    # keeps the per-chapter set.
    all_fn_numbers = set(fn_map)

    for ch in chapters:
        if ch["chapter"] is None:
            report.setdefault("warnings", []).append(
                f"unrecognised chapter ordinal, body dropped: {ch['body'][:1]}")
            continue
        chn = ch["chapter"]
        body = _reflow(ch["body"])
        verses = split_verses(
            body, aggressive_debris=(mode == "glued-digit"),
        )
        # H2376: some partials (Bhāgavata-purāṇa RTF) are prose with chapter
        # heads but no trailing ``(N)`` verse markers. Fall back to
        # blank-line paragraphs as sequential units so the chapter is not
        # silently emptied. Flagged in the report as prose_paragraph_split.
        if not verses and any(ln.strip() for ln in ch["body"]):
            paras = [
                re.sub(r"\s+", " ", p).strip()
                for p in re.split(r"\n\s*\n", "\n".join(ch["body"]))
                if p.strip()
            ]
            verses = [
                {"verse": str(i), "text": para, "author": None}
                for i, para in enumerate(paras, 1)
                if para
            ]
            if verses:
                report.setdefault(
                    "prose_paragraph_split_chapters", []
                ).append(chn)
        if mode == "glued-digit":
            fn_numbers = all_fn_numbers
            link_fn = link_footnotes_glued
        else:
            fn_numbers = {
                fn for fn, note in fn_map.items()
                if note.get("chapter") == chn
            }
            link_fn = link_footnotes
        report["chapters"] += 1
        report["chapter_numbers"].append(chn)

        prev_v = 0
        empty_skipped = 0
        for v in verses:
            label = v["verse"].replace(" ", "")
            if "-" in label or "–" in label:
                passage = f"{chn}.{re.split(r'[-–]', label)[0]}-{re.split(r'[-–]', label)[1]}"
            else:
                passage = f"{chn}.{label}"
            clean, html_text, _refs = link_fn(v["text"], fn_numbers, used_fn)
            # OLE/PDF sometimes leaves a bare ``(1)`` with no body after the
            # chapter heading (H2353 Devīmāhātmya ch.1/2/13). Empty verses are
            # not real passages — skip rather than mint blank cards.
            if not clean.strip():
                empty_skipped += 1
                continue
            if passage in seen_passages:
                report.setdefault("id_collisions", []).append(passage)
                suffix = "b"
                while f"{passage}{suffix}" in seen_passages:
                    suffix = chr(ord(suffix) + 1)
                passage = f"{passage}{suffix}"
            seen_passages.add(passage)
            group = f"{work_slug}:{passage}"
            seq += 1
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
        if empty_skipped:
            report.setdefault("empty_verses_skipped", 0)
            report["empty_verses_skipped"] += empty_skipped

        # H1828: resolve endnote targets to passages actually emitted this chapter.
        chapter_passages = sorted(
            p for p in seen_passages
            if p.startswith(f"{chn}.") and ".comm" not in p
        )
        comm_by_verse: dict[str, list[tuple[int, dict, str, str]]] = {}
        for fn, note in sorted(fn_map.items()):
            if note.get("chapter") != chn:
                continue
            nverse = note.get("verse") or 1
            requested = f"{chn}.{nverse}"
            annot, resolution, delta = _resolve_flat_annotates(
                requested, chapter_passages, chn)
            if resolution == "nearest":
                report["annotates_remapped"] += 1
                report["annotates_remap_max_delta"] = max(
                    report["annotates_remap_max_delta"], delta)
                report["annotates_remaps"].append(
                    {"requested": requested, "resolved": annot, "delta": delta, "fn": fn})
            comm_by_verse.setdefault(annot, []).append((fn, note, requested, resolution))
        for annot, items in comm_by_verse.items():
            for k, (fn, note, requested, resolution) in enumerate(items, 1):
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
                    # H2219 provenance for the H1828 nearest-verse fallback.
                    "annotates_resolution": resolution,
                    **({"annotates_requested": requested}
                       if resolution != "exact" else {}),
                })
                report["comment_count"] += 1

    report["unrecognised_endnotes"] = len(all_fn - used_fn - {
        fn for fn, note in fn_map.items()
        if note["chapter"] not in {c["chapter"] for c in chapters if c["chapter"]}
    }) if all_fn else 0
    report["total_endnotes"] = len(all_fn)
    return records, report


def _resolve_flat_annotates(
    annot: str, chapter_passages: list[str], chn: int,
) -> tuple[str, str, int]:
    """Map flat CHAPTER.VERSE annotates onto an emitted passage (H1828).

    Returns ``(resolved, resolution, delta)`` — ``"exact"`` when the endnote's
    own target was emitted, ``"nearest"`` when the anchor had to move, and how
    far it moved. See ``ignatjev_pdf_to_canonical._resolve_annotates_to_emitted``
    for why the provenance is emitted rather than discarded (H2219).
    """
    if annot in chapter_passages:
        return annot, "exact", 0
    if not chapter_passages:
        return annot, "exact", 0

    def _vkey(p: str) -> int:
        tail = p.split(".", 1)[-1]
        m = re.match(r"(\d+)", tail)
        return int(m.group(1)) if m else 0

    target = _vkey(annot)
    best = min(chapter_passages, key=lambda p: (abs(_vkey(p) - target), _vkey(p)))
    return best, "nearest", abs(_vkey(best) - target)


def parse_parts(
    paths: list[Path],
    work_slug: str,
    footnote_mode: str = "auto",
) -> tuple[list[dict], dict]:
    """Parse one or more source files of a multi-part work.

    Each file is parsed independently (so part-1 endnotes / back-matter are
    bound to part-1's last chapter and never leak into part-2's body), then
    records and report counters are merged. Chapter numbers are expected to
    continue across parts (Ignatiev's "Часть первая/вторая" convention), not
    restart.
    """
    if len(paths) == 1:
        return parse_book(
            extract_text(paths[0]), work_slug, footnote_mode=footnote_mode,
        )

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
        "annotates_remapped": 0,
        "annotates_remap_max_delta": 0,
        "annotates_remaps": [],
        "parts": [],
        "footnote_mode": footnote_mode,
    }
    seen_passages: dict[str, int] = {}
    for path in paths:
        text = extract_text(path)
        recs, rep = parse_book(text, work_slug, footnote_mode=footnote_mode)
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
        merged["annotates_remapped"] += rep.get("annotates_remapped", 0)
        merged["annotates_remap_max_delta"] = max(
            merged["annotates_remap_max_delta"], rep.get("annotates_remap_max_delta", 0))
        merged["annotates_remaps"].extend(rep.get("annotates_remaps") or [])
        if rep.get("empty_verses_skipped"):
            merged.setdefault("empty_verses_skipped", 0)
            merged["empty_verses_skipped"] += rep["empty_verses_skipped"]
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
    ap.add_argument(
        "--footnote-mode",
        choices=("auto", "bracket", "glued-digit"),
        default="auto",
        help="endnote front-end: auto-detect (default), pandoc bracket [N] "
             "block, or page-local glued-digit (DBhP/Māyā PDF convention)",
    )
    ap.add_argument("--stdout-report", action="store_true")
    args = ap.parse_args()

    src_paths = [Path(p) for p in args.input]
    records, report = parse_parts(
        src_paths, args.work_slug, footnote_mode=args.footnote_mode,
    )

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
