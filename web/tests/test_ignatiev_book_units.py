"""H1438 unit tests for the generalized Ignatiev single-book parser.

Synthetic-input tests (no source PDF/docx needed) exercising the pieces that
differ from the DBhP-shaped ``ignatjev_pdf_to_canonical.py`` this generalizes:
heading-only chapter splitting (no closing colophon required), bracket-style
``[N]`` endnotes (real Word footnotes via pandoc), and flat ``chapter.verse``
passage ids (no skandha level). See ``ignatiev_book_to_canonical.py``'s module
docstring for why each of these differs from the DBhP PDF pipeline.
"""
import sys
from pathlib import Path

_CB = Path(__file__).resolve().parents[1] / "corpus_builder"
sys.path.insert(0, str(_CB))

import ignatiev_book_to_canonical as ig  # noqa: E402


def test_chapter_open_matches_bare_and_titled_forms():
    # docx convention: heading alone on its line.
    m = ig._CHAPTER_OPEN_RE.match("Глава первая")
    assert m and m.group("ord") == "первая"
    # PDF convention: ordinal + ALL-CAPS title on the same line.
    m = ig._CHAPTER_OPEN_RE.match("Глава третья ГАЯТРИ")
    assert m and m.group("ord") == "третья"


def test_chapter_open_rejects_prose_mentioning_glava():
    assert ig._CHAPTER_OPEN_RE.match(
        "в этой главе рассказывается о нирване") is None


def test_split_verses_lifts_speaker_and_carries_forward():
    body = ("Благословенная Богиня сказала: первая строка. (1) "
             "вторая строка без явного оратора. (2)")
    verses = ig.split_verses(body)
    assert [v["verse"] for v in verses] == ["1", "2"]
    assert verses[0]["author"] == "Благословенная Богиня"
    assert verses[1]["author"] == "Благословенная Богиня"  # carried forward


def test_split_verses_handles_range_label():
    verses = ig.split_verses("текст диапазона стихов. (3-4)")
    assert verses[0]["verse"] == "3-4"


def test_split_verses_collapses_nonmonotonic_footnote_restarts():
    """H1829: footnote prose embedding (1)/(2) must not mint restart verses.

    Nirvāṇa-tantra PDF had footnotes mixed into body; each footnote's own
    ``(1)`` citation re-split the chapter and forced 1.1b/1.1c letter suffixes.
    """
    body = (
        "Настоящий первый стих. (1) "
        "Настоящий второй стих. (2) "
        "Настоящий третий стих. (3) "
        "5 1.1 сноска к первому. (1) "
        "продолжение сноски с (2) внутри. "
        "Настоящий четвёртый стих. (4)"
    )
    verses = ig.split_verses(body)
    labels = [v["verse"] for v in verses]
    assert labels == ["1", "2", "3", "4"], labels
    # Debris text from the false restart must land on verse 3, not be dropped.
    assert "сноска" in verses[2]["text"]


def test_split_verses_high_n_debris_does_not_swallow_later_reals():
    """H2273: a false high-N footnote body must not set prev_end and eat 7..N.

    Nirvāṇa-tantra ch.8 had a gloss mis-split as ``(30)`` after real verse 6;
    non-monotonic collapse then absorbed real 7–14 into that note bag.
    Debris-shaped higher-N chunks are absorbed without advancing the mark.
    """
    body = (
        "Реальный стих шесть про янтры. (6) "
        ". на Жемчужном острове – сноска-глосса мифологическая. (30) "
        "Реальный стих девять про знание. (9) "
        "Реальный стих одиннадцать про властелина. (11) "
        "Реальный стих четырнадцать про гуны. (14)"
    )
    verses = ig.split_verses(body)
    labels = [v["verse"] for v in verses]
    assert labels == ["6", "9", "11", "14"], labels
    assert "Жемчужном" in verses[0]["text"]
    assert "знание" in verses[1]["text"]


def test_parse_endnotes_bracket_style_with_continuation():
    lines = [
        "[1] 1.1(1). первая заметка,",
        "продолжение первой заметки.",
        "[2] 1.2. вторая заметка.",
    ]
    notes = ig.parse_endnotes(lines, fn1_glued=False)
    assert sorted(notes) == [1, 2]
    assert "продолжение" in notes[1]["text"]
    assert notes[2]["chapter"] == 1 and notes[2]["verse"] == 2


def test_parse_endnotes_fn1_glued_to_heading():
    # pandoc's plain writer glues footnote 1's "[1]" onto the section
    # heading, so the first note line carries no bracket of its own.
    lines = ["1.1(1). заметка без своей скобки."]
    notes = ig.parse_endnotes(lines, fn1_glued=True)
    assert sorted(notes) == [1]


def test_parse_endnotes_survives_verse_range_target():
    lines = ["[1] 1.1. a", "[2] 1.5-6(1). диапазон стихов", "[3] 1.9. b"]
    notes = ig.parse_endnotes(lines, fn1_glued=False)
    assert sorted(notes) == [1, 2, 3]
    assert notes[2]["chapter"] == 1 and notes[2]["verse"] == 5


def test_link_footnotes_strips_bracket_and_links_known_refs():
    clean, html, refs = ig.link_footnotes(
        "текст со ссылкой[3] и незнакомой[99].", {3}, set())
    assert "[3]" not in clean and "[99]" in clean  # only known refs consumed
    assert refs == [3]
    assert "comment_3" in html


def test_parse_book_flat_ids_no_skandha_level():
    text = "\n".join([
        "Заголовок книги", "", "Глава первая", "",
        "Первый стих без оратора. (1)", "Второй стих. (2)", "",
        "Глава вторая", "", "Третий стих новой главы. (1)", "",
        "Комментарий", "[1] 1.1. заметка к первому стиху.",
        "", "СЛОВАРЬ ТЕРМИНОВ", "не должно попасть в заметки",
    ])
    records, report = ig.parse_book(text, "test-work")
    assert report["chapters"] == 2
    assert report["verse_count"] == 3
    ru = [r for r in records if r["seg"] == "ru"]
    assert {r["passage"] for r in ru} == {"1.1", "1.2", "2.1"}
    comm = [r for r in records if r["seg"].startswith("comm")]
    assert len(comm) == 1 and comm[0]["annotates"] == "1.1"
    # the glossary heading must not have been swallowed into note text.
    assert "СЛОВАРЬ" not in comm[0]["text"]


def test_unordinal_glava_line_is_not_a_chapter_boundary():
    # "Глава" followed by a word outside ORDINAL_WORD_PATTERN doesn't match
    # _CHAPTER_OPEN_RE at all (the <ord> group is required, not optional), so
    # a stray prose line starting with "Глава ..." merges into the current
    # chapter's body instead of being mistaken for a new chapter heading.
    text = "\n".join([
        "Глава первая", "Первый стих. (1)",
        "Глава невероятная — это просто фраза внутри текста. (2)",
    ])
    records, report = ig.parse_book(text, "test-work")
    assert report["chapters"] == 1
    ru = [r for r in records if r["seg"] == "ru"]
    assert {r["passage"] for r in ru} == {"1.1", "1.2"}


# --- Wave-A-tail regressions (Нируттара/Гуптасадхана/Йони-тантра, H1438) ---


def test_chapter_open_captures_body_glued_to_heading():
    # Нируттара-тантра ch.5: no paragraph break at all after the heading --
    # pdftotext runs the heading straight into the chapter's own first
    # sentence. `rest` must carry that text forward as body, not drop it.
    m = ig._CHAPTER_OPEN_RE.match(
        "Глава пятая Благословенная Богиня сказала: тест. (1)")
    assert m and m.group("ord") == "пятая"
    assert m.group("rest") == "Благословенная Богиня сказала: тест. (1)"


def test_chapter_open_captures_running_title_prefix():
    # Йони-тантра ch.1: an ALL-CAPS running section title is glued onto the
    # FRONT of the heading on one physical line. `prefix` must absorb it so
    # the heading is still recognised (a missed ch.1 heading silently drops
    # the whole chapter, not just mis-numbers it).
    m = ig._CHAPTER_OPEN_RE.match("ЙОНИ-ТАНТРА. ПЕРЕВОД Глава первая")
    assert m and m.group("ord") == "первая"
    assert m.group("prefix") == "ЙОНИ-ТАНТРА. ПЕРЕВОД"


def test_chapter_open_prefix_and_title_are_case_sensitive():
    # Regression: under the pattern's overall re.IGNORECASE, an unscoped
    # ALL-CAPS class also matches lowercase Cyrillic, so a mixed-case table-
    # of-contents line ("SODERZHANIE Предисловие Глава первая Глава
    # вторая ...") would otherwise satisfy the "prefix" class just as
    # readily as a real running title -- exactly what corrupted
    # niruttara-tantra's chapter numbering before the `(?-i:...)` scoping.
    assert ig._CHAPTER_OPEN_RE.match(
        "СОДЕРЖАНИЕ Предисловие Глава первая Глава вторая") is None


def test_backmatter_matches_heading_glued_to_content():
    # Йони-тантра ch.8's true end-colophon is followed immediately by
    # "ТЕКСТЫ ПО ПОЧИТАНИЮ ЙОНИ Созерцание йони. Оригинал ..." on one
    # physical line -- an appendix of hymns quoted from OTHER named tantras.
    # No end-of-line anchor: the ALL-CAPS lead-in alone is the signal.
    assert ig._BACKMATTER_RE.match(
        "ТЕКСТЫ ПО ПОЧИТАНИЮ ЙОНИ Созерцание йони. Оригинал на санскрите")


def test_backmatter_rejects_short_in_text_abbreviation():
    # Chinachara-tantra's own endnotes cite "НТ (11.6)" (Niruttara-tantra)
    # mid-note -- a short work-abbreviation must never masquerade as a
    # section heading and truncate the endnote block early.
    assert ig._BACKMATTER_RE.match("НТ (11.6). Что касается ...") is None


def test_appendix_after_last_chapter_does_not_absorb_body():
    # End-to-end reproduction of the Йони-тантра ch.8 bug: the last chapter's
    # true colophon is followed by an appendix (its own ALL-CAPS heading
    # glued to content) that itself contains a LATER, unrelated "Комментарий"
    # section for the appendix's own citations. The appendix's notes heading
    # must not be mistaken for this work's endnote block and drag body_end
    # out past the real backmatter boundary.
    text = "\n".join([
        "Глава первая", "Единственный стих главы. (1)",
        "ТЕКСТЫ ПО ПОЧИТАНИЮ ЙОНИ Некий гимн из другого текста, не часть этой",
        "тантры вовсе.",
        "Комментарий",
        "9.1(1). заметка к чужому гимну, не к этой тантре.",
    ])
    records, report = ig.parse_book(text, "test-work")
    assert report["chapters"] == 1
    ru = [r for r in records if r["seg"] == "ru"]
    assert {r["passage"] for r in ru} == {"1.1"}
    # the appendix's own note must not be attached to this work's chapter 1.
    assert not any(r["seg"].startswith("comm") for r in records)


# --- Wave-B regressions (docx tantras/upapurāṇas, H1438) ---


def test_toc_leader_dot_line_is_not_a_chapter_open():
    # Yoginī / Kulārṇava ToC lines: "Глава восьмая ……… 48". Same ordinal
    # form as a real heading, but the leader-dot / page-number tail is the
    # negative signal. Without the reject, multi-part works invent empty
    # chapters out of their own table of contents.
    assert ig._is_chapter_open(
        "Глава восьмая ………………………………………………………………48") is None
    assert ig._is_chapter_open("Глава первая") is not None


def test_last_chapter_allcaps_title_is_not_backmatter():
    # Kulārṇava ch.8 / Mahābhāgavata last-of-part: the ALL-CAPS running
    # title on the line after the heading matches _BACKMATTER_RE by
    # construction. Scanning from last_chapter_idx must skip that title
    # so the last chapter keeps its body (otherwise verse_count of the
    # last chapter collapses to 0).
    text = "\n".join([
        "Глава первая",
        "О ТРЕХ ТАТТВАХ, РАЗЛИЧНЫХ ВИДАХ ВИНА И ИНОМ",
        "Благословенная Богиня сказала: первая. (1)",
        "вторая. (2)",
        "СЛОВАРЬ ИМЕН",
        "какой-то термин.",
    ])
    records, report = ig.parse_book(text, "test-work")
    assert report["chapters"] == 1
    ru = [r for r in records if r["seg"] == "ru"]
    assert {r["passage"] for r in ru} == {"1.1", "1.2"}


def test_parse_parts_isolates_per_part_endnotes():
    # Multi-part works (часть 1/2) must be parsed independently so part-1
    # endnotes never leak into part-2's body as fake verse markers.
    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        p1 = Path(td) / "p1.txt"
        p2 = Path(td) / "p2.txt"
        p1.write_text(
            "\n".join([
                "Глава первая",
                "стих один. (1)",
                "Комментарий",
                "[1] 1.1(1). заметка части 1.",
            ]),
            encoding="utf-8",
        )
        p2.write_text(
            "\n".join([
                "Глава вторая",
                "стих два. (1)",
            ]),
            encoding="utf-8",
        )
        records, report = ig.parse_parts([p1, p2], "test-multi")
    ru = [r for r in records if r["seg"] == "ru"]
    assert {r["passage"] for r in ru} == {"1.1", "2.1"}
    assert report["chapters"] == 2
    assert report["verse_count"] == 2
    comm = [r for r in records if r["seg"].startswith("comm")]
    assert len(comm) == 1


# ---------------------------------------------------------------------------
# H2219: annotates-remap provenance (audit trail for the H1828 fallback)
# ---------------------------------------------------------------------------

def test_resolve_flat_annotates_reports_exact_when_target_was_emitted():
    """An endnote naming a verse that exists must not be recorded as moved."""
    resolved, resolution, delta = ig._resolve_flat_annotates(
        "3.7", ["3.5", "3.6", "3.7", "3.8"], 3)
    assert (resolved, resolution, delta) == ("3.7", "exact", 0)


def test_resolve_flat_annotates_reports_distance_when_anchor_moves():
    """A moved anchor reports 'nearest' plus how far it travelled.

    Before H2219 this returned the bare passage, so a 19-verse move
    (12.8.111 -> 12.008.092 in the shipped DBhP data) was indistinguishable
    from an exact hit and Gate 5 counted both as zero orphans.
    """
    resolved, resolution, delta = ig._resolve_flat_annotates(
        "3.111", ["3.90", "3.92", "3.95"], 3)
    assert resolution == "nearest"
    assert resolved == "3.95"
    assert delta == 16


def test_resolve_flat_annotates_leaves_empty_chapter_untouched():
    """No emitted verse to anchor to → the original target survives unchanged."""
    resolved, resolution, delta = ig._resolve_flat_annotates("4.1", [], 4)
    assert (resolved, resolution, delta) == ("4.1", "exact", 0)
