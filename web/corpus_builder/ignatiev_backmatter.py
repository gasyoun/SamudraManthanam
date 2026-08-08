#!/usr/bin/env python3
"""Ignatiev front/back-matter as registered corpus layers (H2449).

H2415 verse ingest deliberately cut at ``КОММЕНТАРИЙ`` / ``СЛОВАРЬ`` /
``ЛИТЕРАТУРА`` so parenthetical glossary numbers never became false verses.
This module recovers the cut layers:

* **preface** — ALL-CAPS ``ПРЕДИСЛОВИЕ`` prose paragraphs
* **glossary** — ``СЛОВАРЬ …`` entry blocks (headword — definition)
* **bibliography** — ``ЛИТЕРАТУРА`` / ``БИБЛИОГРАФИЯ`` / ``ИСТОЧНИКИ …``
* **about_author** — ``ОБ АВТОРЕ ПЕРЕВОДА``

``КОММЕНТАРИЙ`` / ``ПРИМЕЧАНИЯ`` prose notes are **out of scope** (H2450).

Records mirror house conventions:

* glossary → ``structure=dictionary``, ``seg=head``, ``passage=eN``
  (same shape as ``slovar-grintsera-*.jsonl``)
* preface / bibliography / about → ``structure=prose``, ``seg=ru``,
  ``passage=1.N`` (paragraph units; HTML via ``build_corpus_html.py``)
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import Iterator

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Known layer heads. Order matters only for classification; discovery is
# line-by-line. КОММЕНТАРИЙ deliberately omitted (H2450).
_LAYER_SPECS: list[tuple[re.Pattern[str], str, str]] = [
    # kind, default slug_suffix
    (re.compile(r"^\s*ПРЕДИСЛОВИЕ\s*$"), "preface", "preface"),
    (
        re.compile(r"^\s*СЛОВАРЬ\s+ИМЕН(?:\s+ЭПИЧЕСКИХ\s+ПЕРСОНАЖЕЙ)?\s*$"),
        "glossary",
        "slovar-imen",
    ),
    (
        re.compile(r"^\s*СЛОВАРЬ\s+ПРЕДМЕТОВ(?:\s+И\s+ТЕРМИНОВ)?\s*$"),
        "glossary",
        "slovar-predmetov",
    ),
    (
        re.compile(r"^\s*СЛОВАРЬ\s+ТОПОНИМОВ(?:\s+И\s+ЭТНОНИМОВ)?\s*$"),
        "glossary",
        "slovar-toponimov",
    ),
    (
        re.compile(r"^\s*СЛОВАРЬ\s+ФЛОРЫ(?:\s+И\s+ФАУНЫ)?\s*$"),
        "glossary",
        "slovar-flory",
    ),
    (
        re.compile(r"^\s*СЛОВАРЬ\s+ТЕРМИНОВ\s*$"),
        "glossary",
        "slovar-terminov",
    ),
    (
        re.compile(r"^\s*СЛОВАРЬ\b.{0,40}\s*$"),
        "glossary",
        "slovar",
    ),
    (
        re.compile(r"^\s*СПИСОК\s+СОКРАЩЕНИЙ\s*$"),
        "glossary",
        "spisok-sokrashcheniy",
    ),
    (
        re.compile(r"^\s*(?:ЛИТЕРАТУРА|БИБЛИОГРАФИЯ)\s*$"),
        "bibliography",
        "literatura",
    ),
    (
        re.compile(r"^\s*ИСТОЧНИКИ\b.{0,40}\s*$"),
        "bibliography",
        "istochniki",
    ),
    (
        re.compile(r"^\s*ИЗВЕСТНЫЕ\s+АНТОЛОГИИ\b.{0,40}\s*$"),
        "bibliography",
        "antologii",
    ),
    (
        re.compile(r"^\s*ОБ\s+АВТОРЕ(?:\s+ПЕРЕВОДА)?\s*$"),
        "about_author",
        "ob-avtore",
    ),
]

# Section heads that bound layers but are NOT registered here.
_BOUNDARY_ONLY_RE = re.compile(
    r"^\s*(?:КОММЕНТАРИ[ЙЯ]|ПРИМЕЧАНИ[ЯЕ]|СОДЕРЖАНИЕ)\s*$",
    re.IGNORECASE,
)

# ALL-CAPS standalone line (same spirit as ignatiev_book_to_canonical).
_ALLCAPS_HEAD_RE = re.compile(r"^[А-ЯЁ][А-ЯЁ \-«»\"']{5,60}$")

# Glossary entry start: Capital Cyrillic headword, optional (iast), dash, rest.
_GLOSS_START_RE = re.compile(
    r"^(?P<head>[А-ЯЁ][А-Яа-яёЁIVXLC\-\s]{0,80}?)"
    r"(?:\s*\((?P<iast>[^)]{1,80})\))?"
    r"\s*[–—\-−]\s+"
    r"(?P<body>.+)$"
)

# Bibliography entry: short label then en-dash (``Kama Samuha 2008 – …``)
# or indented continuation; also bare multi-line blocks separated by blank.
_BIB_START_RE = re.compile(
    r"^(?P<label>\S.{0,80}?)\s*[–—]\s+(?P<body>.+)$"
)

# Subhead inside literature (``  Санскритские тексты…``) — keep as prose unit.
_SUBHEAD_RE = re.compile(r"^\s{0,4}[А-ЯЁA-Z].{3,80}$")


@dataclass
class LayerSection:
    kind: str
    title: str
    slug_suffix: str
    start_line: int  # 0-based index of heading line
    end_line: int  # exclusive
    body_lines: list[str] = field(default_factory=list)


def classify_heading(line: str) -> tuple[str, str] | None:
    """Return (kind, slug_suffix) if *line* is a registered layer heading."""
    s = line.strip()
    if not s:
        return None
    for pat, kind, suffix in _LAYER_SPECS:
        if pat.match(s):
            return kind, suffix
    return None


def is_boundary_heading(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if _BOUNDARY_ONLY_RE.match(s):
        return True
    if classify_heading(s) is not None:
        return True
    # Generic ALL-CAPS section (e.g. book titles after preface) ends a preface
    # but is not itself a layer we register here.
    if _ALLCAPS_HEAD_RE.match(s) and s == s.upper():
        return True
    return False


_HYPERLINK_RE = re.compile(
    r'HYPERLINK\s+"[^"]*"(?:\s*\\\\o\s+"[^"]*")?',
    re.IGNORECASE,
)


def clean_ole_noise(text: str) -> str:
    """Strip Word/OLE field garbage that otherwise becomes false paragraphs."""
    text = _HYPERLINK_RE.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _cyr_ratio(s: str) -> float:
    if not s:
        return 0.0
    c = sum(1 for ch in s if "А" <= ch <= "я" or ch in "Ёё")
    # also count Latin letters as content (URLs, English bib titles)
    lat = sum(1 for ch in s if ("A" <= ch <= "Z") or ("a" <= ch <= "z"))
    return (c + lat) / max(1, len(s))


def _is_binary_junk_line(s: str) -> bool:
    """True for single-glyph / high-control OLE residue lines."""
    t = s.strip()
    if not t:
        return False
    if len(t) <= 2 and _cyr_ratio(t) < 0.5:
        return True
    # Mostly non-letters (control / box-drawing / private-use)
    letters = sum(
        1
        for ch in t
        if ch.isalpha() or ch.isdigit() or ch in ".,;:!?–—-()[]«»\"'/\\@ "
    )
    return letters / max(1, len(t)) < 0.4


def find_layer_sections(text: str) -> list[LayerSection]:
    """Locate every registered front/back-matter section in *text*."""
    text = clean_ole_noise(text)
    lines = text.replace("\x0c", "\n").split("\n")
    n = len(lines)
    heads: list[tuple[int, str, str, str]] = []
    for i, ln in enumerate(lines):
        cl = classify_heading(ln)
        if cl is not None:
            kind, suffix = cl
            heads.append((i, kind, suffix, ln.strip()))

    sections: list[LayerSection] = []
    for hi, (start, kind, suffix, title) in enumerate(heads):
        # Soft ceiling: next registered layer head (if any).
        soft_end = heads[hi + 1][0] if hi + 1 < len(heads) else n
        end = soft_end
        junk_run = 0
        for j in range(start + 1, soft_end):
            s = lines[j].strip()
            if not s:
                continue
            # Notes apparatus is never part of preface/glossary layers (H2450).
            if _BOUNDARY_ONLY_RE.match(s):
                end = j
                break
            # Preface sits *before* the verse body: stop at the next ALL-CAPS
            # work/chapter title that is not itself a registered layer head.
            if (
                kind == "preface"
                and _ALLCAPS_HEAD_RE.match(s)
                and s == s.upper()
                and classify_heading(s) is None
            ):
                end = j
                break
            # OLE .doc tails trail into binary residue after real about-author
            # prose (Kādambara H2449). Cut after a short run of junk lines.
            if _is_binary_junk_line(s):
                junk_run += 1
                if junk_run >= 3:
                    # rewind to first junk line of this run
                    k = j
                    seen = 0
                    while k > start and seen < junk_run:
                        if lines[k].strip() and _is_binary_junk_line(lines[k]):
                            seen += 1
                            end = k
                        k -= 1
                    break
            else:
                junk_run = 0
        body = lines[start + 1 : end]
        # Drop trailing junk / blanks
        while body and (
            not body[-1].strip() or _is_binary_junk_line(body[-1])
        ):
            body.pop()
        sections.append(
            LayerSection(
                kind=kind,
                title=title,
                slug_suffix=suffix,
                start_line=start,
                end_line=end,
                body_lines=body,
            )
        )
    return sections


def _collapse_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def split_paragraphs(body_lines: list[str]) -> list[str]:
    """Blank-line-separated prose paragraphs (preface / about-author)."""
    paras: list[str] = []
    buf: list[str] = []
    for ln in body_lines:
        if not ln.strip() or _is_binary_junk_line(ln):
            if buf:
                paras.append(_collapse_ws(" ".join(buf)))
                buf = []
            continue
        buf.append(ln.strip())
    if buf:
        paras.append(_collapse_ws(" ".join(buf)))
    # Drop residual single-glyph / empty-ish units
    return [p for p in paras if p and len(p) >= 3 and _cyr_ratio(p) >= 0.15]


def parse_glossary_entries(body_lines: list[str]) -> list[dict]:
    """Parse ``Headword (iast) – definition`` multi-line blocks."""
    entries: list[dict] = []
    i = 0
    n = len(body_lines)
    while i < n:
        ln = body_lines[i].strip()
        if not ln:
            i += 1
            continue
        m = _GLOSS_START_RE.match(ln)
        if not m:
            # Orphan line (sub-note) — attach to previous entry if any.
            if entries:
                entries[-1]["text"] = _collapse_ws(
                    entries[-1]["text"] + " " + ln
                )
            i += 1
            continue
        head = m.group("head").strip()
        iast = (m.group("iast") or "").strip()
        body = m.group("body").strip()
        i += 1
        while i < n:
            nxt = body_lines[i]
            if not nxt.strip():
                # peek: blank then new entry or end
                j = i + 1
                while j < n and not body_lines[j].strip():
                    j += 1
                if j >= n:
                    i = j
                    break
                if _GLOSS_START_RE.match(body_lines[j].strip()):
                    i = j
                    break
                # blank inside entry (rare) — skip blanks, continue body
                i = j
                continue
            if _GLOSS_START_RE.match(nxt.strip()):
                break
            body = body + " " + nxt.strip()
            i += 1
        text = _collapse_ws(
            f"{head}"
            + (f" ({iast})" if iast else "")
            + f" – {body}"
        )
        entries.append(
            {
                "headword": head,
                "iast": iast,
                "definition": _collapse_ws(body),
                "text": text,
            }
        )
    return entries


def parse_bibliography_entries(body_lines: list[str]) -> list[dict]:
    """Bibliography / sources: dash-labelled entries or paragraph units."""
    entries: list[dict] = []
    i = 0
    n = len(body_lines)
    while i < n:
        raw = body_lines[i]
        ln = raw.strip()
        if not ln:
            i += 1
            continue
        m = _BIB_START_RE.match(ln)
        if m:
            label = m.group("label").strip()
            body = m.group("body").strip()
            i += 1
            while i < n and body_lines[i].strip() and not _BIB_START_RE.match(
                body_lines[i].strip()
            ):
                # continuation or indented line
                cont = body_lines[i].strip()
                if classify_heading(cont):
                    break
                body = body + " " + cont
                i += 1
            text = _collapse_ws(f"{label} – {body}")
            entries.append({"label": label, "text": text})
            continue
        # Subhead or free paragraph
        buf = [ln]
        i += 1
        while i < n and body_lines[i].strip() and not _BIB_START_RE.match(
            body_lines[i].strip()
        ):
            if classify_heading(body_lines[i].strip()):
                break
            buf.append(body_lines[i].strip())
            i += 1
        text = _collapse_ws(" ".join(buf))
        if text:
            entries.append({"label": "", "text": text})
    return entries


def records_for_section(
    section: LayerSection,
    *,
    work_slug: str,
) -> list[dict]:
    """Emit canonical JSONL records for one layer section."""
    recs: list[dict] = []
    if section.kind == "glossary":
        entries = parse_glossary_entries(section.body_lines)
        for seq, ent in enumerate(entries, 1):
            passage = f"e{seq}"
            rid = f"{work_slug}:{passage}"
            recs.append(
                {
                    "id": rid,
                    "work": work_slug,
                    "passage": passage,
                    "seg": "head",
                    "group": rid,
                    "lang": "ru",
                    "script": "cyrillic",
                    "text": ent["text"],
                    "html": ent["text"],
                    "slp1": "",
                    "structure": "dictionary",
                    "chapter": "",
                    "forms": {
                        "headword": ent["headword"],
                        "iast": ent.get("iast") or "",
                    },
                    "seq": seq,
                    "deleted": False,
                    "layer": "glossary",
                    "layer_title": section.title,
                }
            )
        return recs

    if section.kind == "bibliography":
        entries = parse_bibliography_entries(section.body_lines)
        units = [e["text"] for e in entries]
        structure = "prose"
        layer = "bibliography"
    elif section.kind in ("preface", "about_author"):
        units = split_paragraphs(section.body_lines)
        structure = "prose"
        layer = section.kind
    else:
        units = split_paragraphs(section.body_lines)
        structure = "prose"
        layer = section.kind

    for seq, text in enumerate(units, 1):
        passage = f"1.{seq}"
        rid = f"{work_slug}:{passage}#ru"
        recs.append(
            {
                "id": rid,
                "work": work_slug,
                "passage": passage,
                "seg": "ru",
                "group": f"{work_slug}:{passage}",
                "lang": "ru",
                "script": "cyrillic",
                "text": text,
                "html": text,
                "structure": structure,
                "chapter": "1",
                "seq": seq,
                "deleted": False,
                "layer": layer,
                "layer_title": section.title,
            }
        )
    return recs


def slugify_layer(parent_slug: str, section: LayerSection) -> str:
    return f"{parent_slug}-{section.slug_suffix}"


def iter_work_layers(
    text: str, parent_slug: str
) -> Iterator[tuple[str, LayerSection, list[dict]]]:
    """Yield (layer_slug, section, records) for every non-empty layer."""
    for section in find_layer_sections(text):
        layer_slug = slugify_layer(parent_slug, section)
        recs = records_for_section(section, work_slug=layer_slug)
        if recs:
            yield layer_slug, section, recs
