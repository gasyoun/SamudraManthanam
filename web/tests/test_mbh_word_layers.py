"""Hermetic tests for H2738 MBH Word article/index splitters."""
from __future__ import annotations

import sys
from pathlib import Path

WEB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WEB / "corpus_builder"))

import mbh_word_layers as ml  # noqa: E402

ARTICLES = """\
Махабхарата 1. Послесловие (Академик А. П. Баранников)

-589-

Первый абзац статьи.

Второй абзац

-590-

продолжается после колонцифры.

Махабхарата является одним из ценнейших памятников.

Махабхарата 2. Послесловие (В. И. Кальянов)

Только том два.
"""

INDEXES = """\
<H1>Махабхарата 1. ИМЕННОЙ УКАЗАТЕЛЬ</H1>
-679-
Абхиманью (Саубхадра), сын Арджуны 17, 27
Агни, бог огня 15
<H1>Махабхарата 1. ГЕОГРАФИЧЕСКИЙ УКАЗАТЕЛЬ</H1>
Хастинапур, город 11, 20
<H1>Махабхарата 1. ПРЕДМЕТНО-ТЕРМИНОЛОГИЧЕСКИЙ УКАЗАТЕЛЬ</H1>
дхарма 3, 5
<H1>Махабхарата 3. АННОТИРОВАННЫЙ УКАЗАТЕЛЬ ФЛОРЫ И ФАУНЫ</H1>
ашока, дерево 40
Махабхарата 117, 121, 122
<H1>Махабхарата 14. УКАЗАТЕЛЬ САНСКРИТСКИХ ИМЕН И ТЕРМИНОВ</H1>
Арджуна 1
"""


def test_article_heads_ignore_body_mentions():
    arts = ml.split_articles(ARTICLES)
    assert len(arts) == 2
    assert arts[0].volume == "1"
    assert arts[0].title == "Послесловие (Академик А. П. Баранников)"
    assert "Первый абзац" not in arts[0].title
    assert arts[1].volume == "2"
    body = " ".join(arts[0].paragraphs)
    assert "является одним из ценнейших" in body
    assert "Только том два" not in body


def test_page_mark_joins_split_sentence():
    arts = ml.split_articles(ARTICLES)
    joined = " ".join(arts[0].paragraphs)
    assert "Второй абзац продолжается после колонцифры." in joined
    assert "-590-" not in joined


def test_index_kinds_and_volume_prefix():
    secs = ml.split_indexes(INDEXES)
    kinds = [s.kind for s in secs]
    assert kinds == ["imen", "geo", "predmet", "flora", "imen"]
    assert secs[0].volume == "1"
    assert secs[3].volume == "3"
    assert secs[4].volume == "14"
    # page-list line is an entry, not a heading
    assert any(e.startswith("Махабхарата 117") for e in secs[3].entries)
    tagged = ml.prefixed_entries(secs[0])
    assert tagged[0].startswith("[1] Абхиманью")


def test_index_head_requires_ukazatel():
    secs = ml.split_indexes("Махабхарата 5. Послесловие\nне указатель\n")
    assert secs == []


def test_article_records_passage_shape():
    arts = ml.split_articles(ARTICLES)
    recs = ml.article_records(arts, "mahabharata-stati")
    assert recs[0]["passage"].startswith("1.1.")
    assert recs[0]["structure"] == "prose"
    assert recs[-1]["chapter"] == "2"
