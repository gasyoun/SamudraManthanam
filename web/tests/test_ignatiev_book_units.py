"""H1438 unit tests for the generalized Ignatiev single-book parser.

Synthetic-input tests (no source PDF/docx needed) exercising the pieces that
differ from the DBhP-shaped ``ignatjev_pdf_to_canonical.py`` this generalizes:
heading-only chapter splitting (no closing colophon required), bracket-style
``[N]`` endnotes (real Word footnotes via pandoc), and flat ``chapter.verse``
passage ids (no skandha level). See ``ignatiev_book_to_canonical.py``'s module
docstring for why each of these differs from the DBhP PDF pipeline.
"""
import re
import sys
from pathlib import Path

_CB = Path(__file__).resolve().parents[1] / "corpus_builder"
sys.path.insert(0, str(_CB))

import ignatiev_book_to_canonical as ig  # noqa: E402
from ru_ordinals import ordinal_f_to_int  # noqa: E402


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
# H2377: glued-digit page-local footnotes (Māyā-tantra false-verse class)
# ---------------------------------------------------------------------------


def _maya_like_pages() -> str:
    """Synthetic multi-page glued-digit book (form-feed page breaks)."""
    p1 = "\n".join([
        "11",
        "Глава первая",
        "Благословенная Богиня сказала:",
        "Слушай истину другую6, о небо и земля7, (1)",
        "И лишь одна вода8. (2)",
        "КОММЕНТАРИЙ",
        "61.1(1).  я возвещу истину другую – gloss one.",
        "7 1.1(2). небо и земля – three worlds.",
        "8 1.2. Единый океан – ekārṇava.",
    ])
    p2 = "\n".join([
        "12",
        "другого, Владыка вспомнил Майю, (3)",
        "На листе баньяна9. (4)",
        "9 1.4(1). баньян – Ficus indica, sacred tree.",
        "10 1.4(2). играм – līlā of the deity.",
    ])
    p3 = "\n".join([
        "13",
        "Глава вторая",
        "Первый стих второй главы. (1)",
        "Второй стих второй главы. (2)",
        "11 2.1. заметка ко второй главе.",
    ])
    return "\x0c".join([p1, p2, p3])


def test_detect_footnote_mode_is_conservative_bracket():
    # auto always returns bracket so Wave-A re-parses stay count-stable;
    # glued-digit is opt-in via --footnote-mode (H2377 design note).
    pages = []
    for i in range(25):
        pages.append(
            f"{i}\nстих на странице{i+1}. ({i % 5 + 1})\n"
            f"{i+1} 1.{i % 5 + 1}. gloss page {i}."
        )
    text = "\x0c".join(pages)
    assert ig.detect_footnote_mode(text) == "bracket"
    assert ig.detect_footnote_mode(
        "Глава первая\nстих. (1)\nКомментарий\n[1] 1.1. note.\n"
    ) == "bracket"
    sig = ig.glued_digit_signal(text)
    assert sig["strong_note_starts"] >= 20
    assert sig["pages_with_notes"] >= 1


def test_strip_glued_digit_removes_page_notes_from_body():
    body, fn_map, stats = ig.strip_glued_digit_page_notes(_maya_like_pages())
    assert "Ficus indica" not in body
    assert "ekārṇava" not in body
    assert "Владыка вспомнил" in body
    assert "Глава первая" in body
    assert stats["pages_with_notes"] >= 2
    assert 6 in fn_map and 7 in fn_map and 8 in fn_map
    assert "истину другую" in fn_map[6]["text"]


def test_glued_digit_mode_no_false_verse_from_note_citations():
    """The measured Māyā false-verse class: note ``1.1(2)`` must not mint
    a restart verse or id_collision after a real (1)/(2)."""
    text = _maya_like_pages()
    records, report = ig.parse_book(
        text, "maya-test", footnote_mode="glued-digit",
    )
    ru = [r for r in records if r["seg"] == "ru"]
    passages = [r["passage"] for r in ru]
    # ch.1 real verses 1–4; ch.2 real 1–2. No 1.1b collision from note (2).
    assert "1.1" in passages and "1.2" in passages
    assert "1.3" in passages and "1.4" in passages
    assert "2.1" in passages and "2.2" in passages
    assert not any(p.endswith("b") for p in passages), passages
    assert report["footnote_mode"] == "glued-digit"
    assert report["comment_count"] >= 3
    # Glued inline digit stripped from searchable text.
    v1 = next(r for r in ru if r["passage"] == "1.1")
    assert "другую6" not in v1["text"]
    assert "другую" in v1["text"]


def test_glued_digit_debris_scholarly_note_absorbed():
    """Residual note prose that leaks past the strip must not mint high-N
    verses (the 4.26 / 4.52 Māyā class). Aggressive only in glued-digit mode."""
    body = (
        "Реальный стих шесть. (6) "
        "ту пору для индийцев жертвоприношение [Там же: 72]. (26) "
        "). Остановимся на Ocimum sanctum это базилик. (52) "
        "Реальный стих семь. (7)"
    )
    verses = ig.split_verses(body, aggressive_debris=True)
    labels = [v["verse"] for v in verses]
    assert labels == ["6", "7"], labels
    assert "жертвоприношение" in verses[0]["text"] or "Ocimum" in verses[0]["text"]


def test_toc_soderzhanie_does_not_double_chapters():
    """Bare ToC ``Глава N`` lines under СОДЕРЖАНИЕ must not mint a first
    empty 1..N run before the real chapters (Māyā H2377)."""
    text = "\n".join([
        "СОДЕРЖАНИЕ",
        "Предисловие",
        "Глава первая",
        "Глава вторая",
        "ПРЕДИСЛОВИЕ",
        "Вводный абзац переводчика.",
        "Глава первая",
        "Первый стих. (1)",
        "Второй стих. (2)",
        "Глава вторая",
        "Стих главы два. (1)",
    ])
    records, report = ig.parse_book(text, "toc-test", footnote_mode="bracket")
    assert report["chapters"] == 2
    assert report["chapter_numbers"] == [1, 2]
    assert report["verse_count"] == 3


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


# ---------------------------------------------------------------------------
# H2352: .doc → antiword (preferred) / OLE UTF-16 fallback (CI-safe)
# ---------------------------------------------------------------------------
# CI policy: antiword is OPTIONAL. Hermetic tests always exercise the OLE
# path via a synthetic minimal OLE fixture (no antiword binary vendored).
# When antiword IS on PATH, one extra test exercises it; otherwise it is
# marked skip — never fail CI for a missing optional extractor.


def _write_minimal_ole_doc(path: Path, body: str) -> Path:
    """Write a minimal OLE compound file with a WordDocument stream.

    Payload is UTF-16LE of *body*, padded past the 4096-byte MiniFAT cutoff
    so olefile reads it via the regular FAT chain. Enough for
    ``_extract_doc_ole_utf16`` / ``extract_text`` — not a full Word piece
    table.
    """
    import struct

    magic = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    sector = 512
    endofchain = 0xFFFFFFFE
    freesect = 0xFFFFFFFF
    fatsect = 0xFFFFFFFD
    mini_cutoff = 4096

    data = body.encode("utf-16-le")
    if len(data) < mini_cutoff:
        data = data + b"\x00" * (mini_cutoff - len(data))
    data_sectors = (len(data) + sector - 1) // sector
    padded = data + b"\x00" * (data_sectors * sector - len(data))

    def dir_entry(
        name, obj_type, start_sect, size, *,
        color=1, left=0xFFFFFFFF, right=0xFFFFFFFF, child=0xFFFFFFFF,
    ):
        name_u = (name + "\x00").encode("utf-16-le")
        name_pad = name_u + b"\x00" * (64 - len(name_u))
        entry = bytearray(128)
        entry[0:64] = name_pad
        struct.pack_into("<H", entry, 64, len(name_u))
        entry[66] = obj_type
        entry[67] = color
        struct.pack_into("<I", entry, 68, left)
        struct.pack_into("<I", entry, 72, right)
        struct.pack_into("<I", entry, 76, child)
        struct.pack_into("<I", entry, 116, start_sect & 0xFFFFFFFF)
        struct.pack_into("<Q", entry, 120, size)
        return bytes(entry)

    directory = (
        dir_entry("Root Entry", 5, endofchain, 0, child=1)
        + dir_entry("WordDocument", 2, 2, len(data))
        + bytes(128)
        + bytes(128)
    )
    fat = [fatsect, endofchain]
    for i in range(data_sectors):
        fat.append(2 + i + 1 if i < data_sectors - 1 else endofchain)
    while len(fat) < sector // 4:
        fat.append(freesect)
    fat_bytes = b"".join(struct.pack("<I", x) for x in fat)

    hdr = bytearray(sector)
    hdr[0:8] = magic
    struct.pack_into("<H", hdr, 0x18, 0x003E)
    struct.pack_into("<H", hdr, 0x1A, 0x0003)
    struct.pack_into("<H", hdr, 0x1C, 0xFFFE)
    struct.pack_into("<H", hdr, 0x1E, 9)
    struct.pack_into("<H", hdr, 0x20, 6)
    struct.pack_into("<I", hdr, 0x2C, 1)
    struct.pack_into("<I", hdr, 0x30, 1)
    struct.pack_into("<I", hdr, 0x38, endofchain)
    struct.pack_into("<I", hdr, 0x3C, 0)
    struct.pack_into("<I", hdr, 0x40, endofchain)
    struct.pack_into("<I", hdr, 0x44, 0)
    struct.pack_into("<I", hdr, 0x4C, 0)
    for i in range(1, 109):
        struct.pack_into("<I", hdr, 0x4C + 4 * i, freesect)

    path.write_bytes(bytes(hdr) + fat_bytes + directory + padded)
    return path


def test_extract_text_doc_ole_fallback_hermetic(tmp_path):
    """OLE path extracts Cyrillic body without antiword (CI default)."""
    import shutil

    doc = _write_minimal_ole_doc(
        tmp_path / "sample.doc",
        "Глава первая\nТестовый стих. (1)\n",
    )
    # Force the OLE path even if a developer machine has antiword installed.
    real_which = shutil.which

    def _no_antiword(cmd):
        if cmd == "antiword":
            return None
        return real_which(cmd)

    shutil.which = _no_antiword  # type: ignore[assignment]
    try:
        text = ig.extract_text(doc)
    finally:
        shutil.which = real_which  # type: ignore[assignment]
    assert "Глава первая" in text
    assert "Тестовый стих" in text
    assert text.strip()  # never silent empty


def test_extract_text_doc_raises_on_corrupt_ole(tmp_path):
    """Corrupt .doc must raise with the path — not return ''."""
    import pytest

    bad = tmp_path / "broken.doc"
    bad.write_bytes(b"not-an-ole-file-at-all")
    with pytest.raises(RuntimeError, match=re.escape(str(bad))):
        ig.extract_text(bad)


def test_extract_text_doc_antiword_failure_falls_back_to_ole(tmp_path, monkeypatch):
    """antiword non-zero → OLE fallback, still non-empty."""
    import subprocess

    doc = _write_minimal_ole_doc(
        tmp_path / "sample.doc",
        "Глава вторая\nВторой стих. (1)\n",
    )
    monkeypatch.setattr(ig.shutil, "which", lambda cmd: "/fake/antiword" if cmd == "antiword" else None)

    def _fail_antiword(*_a, **_k):
        return subprocess.CompletedProcess(
            args=["antiword"], returncode=1, stdout=b"", stderr=b"boom",
        )

    monkeypatch.setattr(ig.subprocess, "run", _fail_antiword)
    text = ig.extract_text(doc)
    assert "Глава вторая" in text


def test_extract_text_rejects_unsupported_suffix(tmp_path):
    p = tmp_path / "x.rtf"
    p.write_text("hi", encoding="utf-8")
    import pytest
    with pytest.raises(ValueError, match="unsupported source format"):
        ig.extract_text(p)


def test_chapter_open_peels_ole_glued_unit_ordinal():
    """H2353: OLE glue ``Глава шестьдесят втораяовно…`` must open ch.62."""
    line = "Глава шестьдесят втораяовно свинцовый сурик, (104)"
    m = ig._is_chapter_open(line)
    assert m is not None
    assert m.group("ord") == "шестьдесят вторая"
    assert ordinal_f_to_int(m.group("ord")) == 62
    rest = (m.group("rest") or "")
    assert rest.startswith("овно") or "свинцовый" in rest
    # Bare tens-prefix alone is not a chapter open.
    assert ig._is_chapter_open("Глава шестьдесят") is None


def test_chapter_open_from_excerpt_genitive_heading():
    """H2376: «Из двадцать второй главы» must open chapter 22, not fall back to 1."""
    m = ig._is_chapter_open("Из двадцать второй главы")
    assert m is not None
    assert ordinal_f_to_int(m.group("ord")) == 22
    text = (
        "Деви-пурана\n"
        "Из двадцать второй главы\n"
        "Индра сказал:\n"
        "Я желаю услышать о постах. (3)\n"
        "Брахма сказал:\n"
        "Слушай, о Шакра. (4)\n"
    )
    recs, rep = ig.parse_book(text, "devi-purana")
    ru = [r for r in recs if r.get("seg") == "ru"]
    assert rep["chapter_numbers"] == [22]
    assert [r["passage"] for r in ru] == ["22.3", "22.4"]


def test_chapter_open_allows_trailing_period():
    """H2376: RTF «ГЛАВА ВТОРАЯ.» must open, not fall into implicit ch.1."""
    m = ig._is_chapter_open("ГЛАВА ВТОРАЯ.")
    assert m is not None
    assert ordinal_f_to_int(m.group("ord")) == 2
    m2 = ig._is_chapter_open("Глава семнадцатая.")
    assert m2 is not None
    assert ordinal_f_to_int(m2.group("ord")) == 17


def test_chapter_open_digit_form_and_prose_paragraph_split():
    """H2376: «ГЛАВА 14» digit heads + prose without (N) still emits units."""
    m = ig._is_chapter_open("ГЛАВА 14")
    assert m is not None
    assert m.group("ord") == "14"
    text = (
        "ГЛАВА ВТОРАЯ.\n"
        "ДАКША ПРОКЛИНАЕТ\n"
        "\n"
        "Видура сказал:\n"
        "\n"
        "Почему Дакша возненавидел Бхаву.\n"
        "\n"
        "Майтрейя сказал:\n"
        "\n"
        "Некогда на жертвоприношении собрались риши.\n"
        "\n"
        "ГЛАВА 14\n"
        "\n"
        "Первый абзац четырнадцатой.\n"
        "\n"
        "Второй абзац четырнадцатой.\n"
    )
    recs, rep = ig.parse_book(text, "bhagavata-purana")
    ru = [r for r in recs if r.get("seg") == "ru"]
    assert 2 in rep["chapter_numbers"]
    assert 14 in rep["chapter_numbers"]
    assert rep["verse_count"] >= 4
    assert any(r["passage"].startswith("14.") for r in ru)
    assert rep.get("prose_paragraph_split_chapters")


def test_extract_text_pdf_pypdf_fallback(tmp_path, monkeypatch):
    """H2376: when pdftotext is missing, pypdf must still return text."""
    import shutil
    real_which = shutil.which

    def fake_which(name, *args, **kwargs):
        if name == "pdftotext":
            return None
        return real_which(name, *args, **kwargs)

    monkeypatch.setattr(shutil, "which", fake_which)
    # Prefer a real archive PDF when present; else skip (pypdf needs real PDF bytes).
    archive = (
        Path(__file__).resolve().parents[2]
        / "archive_ignatiev_2026"
        / "Переводы с санскрита"
        / "Линга-пурана"
        / "Линга-пурана. Глава 17.pdf"
    )
    import pytest
    if not archive.is_file():
        pytest.skip("archive Liṅga PDF not present (gitignored)")
    text = ig.extract_text(archive)
    assert "Глава" in text or "глава" in text.lower()
    assert "линга" in text.lower() or "Линга" in text or "ЛИНГА" in text


def test_extract_text_doc_rtf_masquerade(tmp_path):
    """H2376: a .doc whose bytes are RTF must route through pandoc RTF, not OLE."""
    # Minimal RTF with ansicpg1251 + a short Cyrillic body encoded as the
    # bytes pandoc would mis-label; prefer real archive sample when present.
    archive = (
        Path(__file__).resolve().parents[2]
        / "archive_ignatiev_2026"
        / "Переводы с санскрита"
        / "Бхагавата-пурана"
        / "Бхагавата-пурана Некоторые главы.doc"
    )
    import pytest
    if not archive.is_file():
        # Hermetic: write a tiny RTF .doc with ASCII (no mojibake path) so
        # the magic-byte branch is still covered without the archive.
        p = tmp_path / "probe.doc"
        p.write_bytes(
            b"{\\rtf1\\ansi\\ansicpg1251\\deff0 "
            b"Glava vtoraya. Vidura skazal: text. (1)}"
        )
        # Pandoc may still produce text; if pandoc missing, skip.
        import shutil
        if not shutil.which("pandoc"):
            pytest.skip("pandoc not on PATH")
        try:
            text = ig.extract_text(p)
        except RuntimeError as e:
            pytest.skip(f"pandoc RTF unavailable: {e}")
        assert text.strip()
        return
    text = ig.extract_text(archive)
    assert "ГЛАВА" in text or "Глава" in text
    assert "сказал" in text or "Сказал" in text


def test_colophon_and_absurd_jump_dropped_not_emitted():
    """H2353: colophon + high-N marker after real verses is not a verse."""
    body = (
        "Последний реальный стих главы. (158) "
        "Так в Калика-пуране заканчивается двадцатая глава, "
        "называющаяся «Дакша проклинает Чандру». (1401-1464)"
    )
    verses = ig.split_verses(body)
    labels = [v["verse"] for v in verses]
    assert labels == ["158"], labels
    assert "заканчивается" not in verses[0]["text"]


def test_empty_verse_after_heading_not_emitted():
    """H2353: bare ``(1)`` with no body must not mint a blank passage.

    ``split_verses`` already skips empty pre-marker chunks; the emit-side
    empty filter is an extra guard when text is non-empty but cleans to
    blank after footnote stripping. Either path must leave no blank cards.
    """
    text = (
        "Глава первая\n"
        " (1) "
        "Реальный первый стих с текстом. (2) "
        "Ещё один. (3)\n"
    )
    recs, rep = ig.parse_book(text, "probe")
    ru = [r for r in recs if r.get("seg") == "ru"]
    assert [r["passage"] for r in ru] == ["1.2", "1.3"]
    assert all(r["text"].strip() for r in ru)
    assert rep["verse_count"] == 2


def test_extract_text_doc_antiword_live_or_skip():
    """When antiword is on PATH, run it on the synthetic fixture; else skip.

    Marker is intentional: CI without antiword stays green. Local machines
    with antiword get an extra live smoke of the preferred branch.
    """
    import pytest
    import shutil
    import tempfile

    if not shutil.which("antiword"):
        pytest.skip("antiword not on PATH — optional; OLE path covered hermetically")

    with tempfile.TemporaryDirectory() as td:
        # antiword needs a real Word .doc, not our synthetic OLE UTF-16
        # payload. Prefer a real archive sample when present; otherwise skip
        # (synthetic OLE is not a valid Word piece table for antiword).
        archive = (
            Path(__file__).resolve().parents[2]
            / "archive_ignatiev_2026"
            / "Переводы с санскрита"
            / "Деви-махатмья"
            / "Деви-махатмья.doc"
        )
        if not archive.is_file():
            pytest.skip("archive .doc not present (gitignored) for live antiword smoke")
        text = ig._extract_doc_antiword(archive)
        assert text.strip()
        assert len(text) > 100


def test_extract_text_doc_archive_ole_smoke_or_skip():
    """Optional real-archive smoke via OLE when the gitignored tree exists."""
    import pytest
    import shutil

    archive = (
        Path(__file__).resolve().parents[2]
        / "archive_ignatiev_2026"
        / "Переводы с санскрита"
        / "Деви-махатмья"
        / "Деви-махатмья.doc"
    )
    if not archive.is_file():
        pytest.skip("archive .doc not present (gitignored)")
    # Prefer OLE path for determinism in this smoke (antiword may mangle).
    real_which = shutil.which

    def _no_antiword(cmd):
        if cmd == "antiword":
            return None
        return real_which(cmd)

    shutil.which = _no_antiword  # type: ignore[assignment]
    try:
        text = ig.extract_text(archive)
    finally:
        shutil.which = real_which  # type: ignore[assignment]
    assert text.strip()
    assert len(text) > 500
