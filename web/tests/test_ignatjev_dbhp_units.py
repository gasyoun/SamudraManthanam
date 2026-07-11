"""H558 unit tests for the Ignatjev DBhP parser's PDF-free logic.

These exercise the endnote re-join and the colophon/heading regexes on synthetic
input, so they run in CI WITHOUT the source PDFs or ``pdftotext`` (unlike the
count-gated tests in ``test_ignatjev_dbhp.py``). They guard the H558 hardening
that made skandhas 2–12 parseable: a gap-tolerant footnote join, chapter-range
and spaced-dot note refs, plural/all-caps note headings, and the varied skandha
and chapter colophon wordings.
"""
import sys
from pathlib import Path

import pytest

_CB = Path(__file__).resolve().parents[1] / "corpus_builder"
sys.path.insert(0, str(_CB))

pytest.importorskip("regex")
import ignatjev_pdf_to_canonical as ig  # noqa: E402
from ru_ordinals import ordinal_f_to_int  # noqa: E402


def test_gap_tolerant_join_survives_chapter_range_note():
    # A chapter-range note ("2 3-6.") whose ref shape the old classifier missed
    # sits mid-run. The old strict fn==next gate stalled and glued every later
    # note into one (the Vol 2/4/5 18/2/71 desync); it must now parse all four.
    lines = [
        "1 1.1. первая заметка",
        "2 3-6. заметка о диапазоне глав",
        "3 3.2. кокиль индийская кукушка",
        "продолжение третьей заметки",
        "4 3.9. слон с четырьмя бивнями",
    ]
    notes = ig.parse_endnotes(lines)
    assert sorted(notes) == [1, 2, 3, 4]
    assert notes[2]["chapter"] == 3            # chapter-range -> first chapter
    assert "продолжение" in notes[3]["text"]   # continuation re-joined


def test_spaced_dot_ref_is_recognised():
    # pdftotext inserts a space after the chapter dot in Vol 4 ("1. 4(1)").
    lines = ["1 1.1(2). a", "2 1.2. b", "3 1. 4(1). c", "4 1.11(1). d"]
    notes = ig.parse_endnotes(lines)
    assert sorted(notes) == [1, 2, 3, 4]
    assert notes[3]["chapter"] == 1


def test_join_survives_source_numbering_gap():
    # a genuine gap in the source's own numbering (3 absent) must not stall.
    notes = ig.parse_endnotes(["1 2.1. a", "2 2.2. b", "4 2.4. d", "5 2.5. e"])
    assert sorted(notes) == [1, 2, 4, 5]


@pytest.mark.parametrize("head", ["Комментарий", "Комментарии", "КОММЕНТАРИЙ", "КОММЕНТАРИИ"])
def test_note_heading_variants_match(head):
    assert ig._NOTES_HEAD_RE.match(head)


def test_note_heading_rejects_non_heading():
    assert not ig._NOTES_HEAD_RE.match("Комментарий к главе")


@pytest.mark.parametrize("line,expected", [
    ("ТАК ЗАКАНЧИВАЕТСЯ ПЕРВАЯ КНИГА МАХАПУРАНЫ ДЕВИБХАГАВАТА.", 1),
    ("ТАК В МАХАПУРАНЕ ДЕВИБХАГАВАТА ЗАКАНЧИВАЕТСЯ ЧЕТВЕРТАЯ КНИГА.", 4),
    ("Так в махапуране Девибхагавата заканчивается десятая книга.", 10),
])
def test_skandha_colophon_variants(line, expected):
    assert ig.skandha_colophon_num(line) == expected


def test_skandha_colophon_not_confused_with_chapter():
    # a chapter colophon ("... книгЕ ... глава") is NOT a skandha end.
    assert ig.skandha_colophon_num(
        "Так в девятой книге махапураны заканчивается первая глава.") is None


@pytest.mark.parametrize("line,expected", [
    ("Так в шестой книге махапураны заканчивается пятнадцатая глава, называющаяся «Царь».", 15),
    ("Так в седьмой книге махапураны заканчивается двадцать четвертая, называющаяся «Жизнь».", 24),
    ("Так в восьмой книге махапураны заканчивается глава девятнадцатая.", 19),
    ("Так в восьмой книге махапураны заканчивается первая глава.", 1),
])
def test_chapter_colophon_variants(line, expected):
    m = ig._COLOPHON_RE.search(line)
    assert m
    ordw = m.group("ord") or m.group("ord2") or m.group("ord3")
    assert ordinal_f_to_int(ordw) == expected
