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
