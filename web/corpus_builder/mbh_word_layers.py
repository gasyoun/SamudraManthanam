#!/usr/bin/env python3
"""Parse Anatoly's MBH Word dumps into article + index layers (H2738).

Source (Anatoliy Artemenko shared Drive, shelf «Для Пахтания»):

* articles — ``Все статьи Махабхараты (для чтения).docx``
* indexes  — ``Махабхарата -все указатели.doc``

Comments (``Комментарии Махабхараты.docx``) are **not** a layer: they are
already verse-attached ``comment_item`` blocks in the 18 parva HTML files
(book 13 has none in HTML and none in the dump).

Heading rule for articles: a line that is exactly
``Махабхарата <vol>. <title>`` where ``<vol>`` is ``1`` or ``10-11``.
A line like ``Махабхарата является…`` or ``Махабхарата 117, 121`` is body.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ARTICLE_HEAD = re.compile(
    r"^Махабхарата\s+(\d+(?:-\d+)?)\.\s+(\S.*\S|\S)\s*$"
)
INDEX_HEAD = re.compile(
    r"^(?:<H1>)?Махабхарата\s+(\d+(?:-\d+)?)\.\s+"
    r"(.+?)(?:</H1>)?\s*$",
    re.IGNORECASE,
)
PAGE_MARK = re.compile(r"^\s*-\d+-\s*$")
H1_WRAP = re.compile(r"</?H1>", re.IGNORECASE)


@dataclass(frozen=True)
class Article:
    volume: str
    title: str
    paragraphs: tuple[str, ...]


@dataclass(frozen=True)
class IndexSection:
    volume: str
    title: str
    kind: str  # imen | geo | predmet | flora
    entries: tuple[str, ...]


def strip_page_marks(text: str) -> str:
    """Drop print-page sentinels (``-589-``) and join the split sentence."""
    return re.sub(r"\n+\s*-\d+-\s*\n+", " ", text)


def split_articles(text: str) -> list[Article]:
    # Split on the raw lines first. Page marks often sit BETWEEN a heading
    # and the first paragraph; collapsing them globally would glue the
    # opening sentence into the title.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    heads: list[tuple[int, str, str]] = []
    for i, raw in enumerate(lines):
        m = ARTICLE_HEAD.match(raw.strip())
        if m:
            heads.append((i, m.group(1), m.group(2).strip()))
    articles: list[Article] = []
    for n, (idx, vol, title) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        body = strip_page_marks("\n".join(lines[idx + 1 : end]))
        paras = _paragraphs(body)
        articles.append(Article(volume=vol, title=title, paragraphs=tuple(paras)))
    return articles


def _paragraphs(body: str) -> list[str]:
    chunks: list[str] = []
    buf: list[str] = []
    for ln in body.split("\n"):
        s = ln.strip()
        if not s:
            if buf:
                chunks.append(" ".join(buf))
                buf = []
            continue
        if PAGE_MARK.match(s):
            continue
        buf.append(s)
    if buf:
        chunks.append(" ".join(buf))
    return [c for c in chunks if c]


def classify_index(title: str) -> str:
    t = title.upper()
    if "ФЛОР" in t or "ФАУН" in t:
        return "flora"
    if "ГЕОГРАФ" in t or "ЭТНИЧ" in t:
        return "geo"
    if "ИМЕН" in t or "ПЕРСОНАЖ" in t:
        return "imen"
    return "predmet"


def split_indexes(text: str) -> list[IndexSection]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    heads: list[tuple[int, str, str]] = []
    for i, raw in enumerate(lines):
        s = H1_WRAP.sub("", raw).strip()
        m = INDEX_HEAD.match(s)
        if not m:
            continue
        title = m.group(2).strip().rstrip("*").strip()
        if "УКАЗАТЕЛ" not in title.upper():
            continue
        heads.append((i, m.group(1), title))
    sections: list[IndexSection] = []
    for n, (idx, vol, title) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        entries: list[str] = []
        for raw in lines[idx + 1 : end]:
            s = H1_WRAP.sub("", raw).strip()
            if not s or PAGE_MARK.match(s):
                continue
            if INDEX_HEAD.match(s) and "УКАЗАТЕЛ" in s.upper():
                continue
            entries.append(s)
        sections.append(
            IndexSection(
                volume=vol,
                title=title,
                kind=classify_index(title),
                entries=tuple(entries),
            )
        )
    return sections


def volume_tag(volume: str) -> str:
    return f"[{volume}]"


def prefixed_entries(section: IndexSection) -> list[str]:
    tag = volume_tag(section.volume)
    return [f"{tag} {e}" for e in section.entries]


def article_records(articles: list[Article], slug: str) -> list[dict]:
    recs: list[dict] = []
    seq = 0
    for art_i, art in enumerate(articles, start=1):
        for para_i, para in enumerate(art.paragraphs, start=1):
            seq += 1
            passage = f"1.{art_i}.{para_i}"
            recs.append(
                {
                    "id": f"{slug}:{passage}#ru",
                    "work": slug,
                    "passage": passage,
                    "seg": "ru",
                    "group": f"{slug}:{passage}",
                    "lang": "ru",
                    "script": "cyrillic",
                    "text": para,
                    "html": para,
                    "structure": "prose",
                    "chapter": str(art_i),
                    "skandha": 1,
                    "seq": seq,
                    "deleted": False,
                    "layer": "article",
                    "layer_title": art.title,
                    "volume": art.volume,
                }
            )
    return recs


def article_titles(articles: list[Article]) -> dict[tuple[int, int], str]:
    return {(1, i): f"{a.volume}. {a.title}" for i, a in enumerate(articles, start=1)}


def index_records(entries: list[str], slug: str) -> list[dict]:
    recs: list[dict] = []
    for i, text in enumerate(entries, start=1):
        recs.append(
            {
                "id": f"{slug}:e{i}#head",
                "work": slug,
                "passage": f"e{i}",
                "seg": "head",
                "group": f"{slug}:e{i}",
                "lang": "ru",
                "script": "cyrillic",
                "text": text,
                "html": text,
                "structure": "dictionary",
                "seq": i,
                "deleted": False,
                "layer": "index",
            }
        )
    return recs
