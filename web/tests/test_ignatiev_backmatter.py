"""Unit tests for H2449 Ignatiev front/back-matter layer extraction."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WEB / "corpus_builder"))

import ignatiev_backmatter as bm  # noqa: E402


SAMPLE = """\
КАМА-САМУХА

СОДЕРЖАНИЕ
Предисловие ::::: 3
Словарь имен ::::: 10

ПРЕДИСЛОВИЕ

Первый абзац предисловия про Каму.

Второй абзац с ссылкой [Apte 1988: 1].

КАМА-САМУХА
Глава первая
Стих один. (1)

КОММЕНТАРИЙ
1. Источник: чужой комментарий.

СЛОВАРЬ ИМЕН

Бестелесный (ana~Nga) – эпитет бога любви Камы. Согласно преданию,
Шива испепелил Каму.

Брахма (brahmA) – бог-творец.

СЛОВАРЬ ПРЕДМЕТОВ И ТЕРМИНОВ

Амрита (amR^ita) – напиток бессмертия.

ЛИТЕРАТУРА

  Санскритские тексты

Kama Samuha 2008 – Kama Samuha of Sri Anant Kavi. N.D.: Chaukhambha, 2008.

Артхашастра 1993 – Артхашастра. Пер. Кальянова. М.: Наука, 1993.

ОБ АВТОРЕ ПЕРЕВОДА

Андрей Игнатьев родился в 1977 г.

Сайт: www.example.ru
"""


def test_find_layer_sections_kinds_and_bounds():
    secs = bm.find_layer_sections(SAMPLE)
    kinds = [s.kind for s in secs]
    assert kinds == [
        "preface",
        "glossary",
        "glossary",
        "bibliography",
        "about_author",
    ]
    # preface ends before work title / body, not at glossary
    pref = secs[0]
    body = "\n".join(pref.body_lines)
    assert "Первый абзац" in body
    assert "Стих один" not in body
    assert "КОММЕНТАРИЙ" not in body
    # glossary does not swallow commentary
    names = secs[1]
    assert names.title == "СЛОВАРЬ ИМЕН"
    assert "Бестелесный" in "\n".join(names.body_lines)
    assert "Источник: чужой" not in "\n".join(names.body_lines)


def test_preface_paragraphs():
    secs = bm.find_layer_sections(SAMPLE)
    pref = next(s for s in secs if s.kind == "preface")
    paras = bm.split_paragraphs(pref.body_lines)
    assert len(paras) == 2
    assert paras[0].startswith("Первый абзац")
    assert "Второй абзац" in paras[1]


def test_glossary_entries_multiline_and_iast():
    secs = bm.find_layer_sections(SAMPLE)
    names = next(s for s in secs if s.slug_suffix == "slovar-imen")
    ents = bm.parse_glossary_entries(names.body_lines)
    assert len(ents) == 2
    assert ents[0]["headword"] == "Бестелесный"
    assert "ana~Nga" in ents[0]["iast"]
    assert "испепелил" in ents[0]["definition"]
    assert ents[1]["headword"] == "Брахма"


def test_glossary_heading_not_swallowed_as_entry():
    """Regression twin of test_endnotes_stop_at_glossary in book units."""
    text = "\n".join(
        [
            "СЛОВАРЬ ИМЕН",
            "",
            "Агни — бог огня.",
            "",
            "СЛОВАРЬ ПРЕДМЕТОВ И ТЕРМИНОВ",
            "",
            "Йони — лоно.",
        ]
    )
    secs = bm.find_layer_sections(text)
    assert len(secs) == 2
    e1 = bm.parse_glossary_entries(secs[0].body_lines)
    assert len(e1) == 1 and e1[0]["headword"] == "Агни"
    assert "СЛОВАРЬ" not in e1[0]["text"]


def test_records_for_glossary_shape():
    secs = bm.find_layer_sections(SAMPLE)
    names = next(s for s in secs if s.slug_suffix == "slovar-imen")
    recs = bm.records_for_section(names, work_slug="kama-samuha-slovar-imen")
    assert recs[0]["structure"] == "dictionary"
    assert recs[0]["seg"] == "head"
    assert recs[0]["passage"] == "e1"
    assert recs[0]["forms"]["headword"] == "Бестелесный"


def test_records_for_preface_prose_shape():
    secs = bm.find_layer_sections(SAMPLE)
    pref = next(s for s in secs if s.kind == "preface")
    recs = bm.records_for_section(pref, work_slug="kama-samuha-preface")
    assert all(r["structure"] == "prose" for r in recs)
    assert all(r["seg"] == "ru" for r in recs)
    assert recs[0]["passage"] == "1.1"


def test_bibliography_dash_entries():
    secs = bm.find_layer_sections(SAMPLE)
    bib = next(s for s in secs if s.kind == "bibliography")
    ents = bm.parse_bibliography_entries(bib.body_lines)
    labels = {e.get("label") for e in ents}
    assert "Kama Samuha 2008" in labels
    assert "Артхашастра 1993" in labels


def test_iter_work_layers_skips_empty():
    layers = list(bm.iter_work_layers(SAMPLE, "kama-samuha"))
    slugs = [s for s, _, _ in layers]
    assert "kama-samuha-preface" in slugs
    assert "kama-samuha-slovar-imen" in slugs
    assert "kama-samuha-literatura" in slugs
    assert "kama-samuha-ob-avtore" in slugs
    # commentary never becomes a layer
    assert not any("komment" in s for s in slugs)


def test_mbh_style_glossary_without_iast_parens():
    text = "\n".join(
        [
            "СЛОВАРЬ ИМЕН ЭПИЧЕСКИХ ПЕРСОНАЖЕЙ",
            "",
            "Абхиманью — сын Арджуны от второй его супруги Субхадры.",
            "Убит на Курукшетре.",
            "",
            "Агни — бог огня.",
        ]
    )
    secs = bm.find_layer_sections(text)
    assert secs[0].slug_suffix == "slovar-imen"
    ents = bm.parse_glossary_entries(secs[0].body_lines)
    assert len(ents) == 2
    assert "Курукшетре" in ents[0]["definition"]


def test_about_author_cuts_ole_binary_tail():
    text = "\n".join(
        [
            "ОБ АВТОРЕ ПЕРЕВОДА",
            "",
            "Андрей Игнатьев родился в 1977 г.",
            "",
            "Сайт: www.example.ru",
            "",
            "J",
            "J",
            "h",
            "Ī",
            "*",
            "J",
        ]
    )
    secs = bm.find_layer_sections(text)
    assert len(secs) == 1 and secs[0].kind == "about_author"
    paras = bm.split_paragraphs(secs[0].body_lines)
    assert any("1977" in p for p in paras)
    assert all(len(p) > 2 for p in paras)
    assert not any(p in {"J", "h", "*"} for p in paras)
