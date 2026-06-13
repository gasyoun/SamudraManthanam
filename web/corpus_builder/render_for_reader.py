"""Renderer: JSONL records → reader-compatible citation-block HTML.

CONVERTER_SPEC §7 gate 2 — HTML round-trip fidelity.

Takes the JSONL records produced by html_to_canonical.py for one source
and reconstructs the citation_block HTML structure the legacy corpus
reader produced from the original HTML files. The output is used only
for comparison/validation (diffing against original corpus HTML to
verify zero search-relevant divergence); it is not served in production.
"""
from __future__ import annotations

import re
from pathlib import Path


_STRIP_TAGS = re.compile(r"<[^>]+>")
_BR = re.compile(r"<br\s*/?>", re.IGNORECASE)


def _strip_html(s: str) -> str:
    """Strip HTML tags and collapse whitespace to plain text."""
    s = _BR.sub(" ", s)
    s = _STRIP_TAGS.sub("", s)
    return re.sub(r"\s+", " ", s).strip()


def render_passage_group(recs: list[dict]) -> str:
    """Render one passage group (all JSONL segments for one verse) as HTML.

    Produces a <div class="citation_block"> that mirrors the structure of
    the original corpus HTML: chapter_content with iast/translation blocks,
    followed by a comments div if commentary records are present.

    Prose records (seg=None) are wrapped in a plain div with the passage id.
    """
    if not recs:
        return ""

    recs_sorted = sorted(recs, key=lambda r: r.get("seq", 0))
    passage = recs_sorted[0].get("passage", "")
    seg0 = recs_sorted[0].get("seg")

    # Prose: single block — no sa/ru split
    if seg0 is None:
        html = recs_sorted[0].get("html", "")
        return f'<div class="citation_block" id="{passage}">{html}</div>'

    sa_html = ""
    ru_html = ""
    comm_items: list[str] = []

    for rec in recs_sorted:
        seg = rec.get("seg") or ""
        h = rec.get("html", "")
        if seg == "sa":
            sa_html = h
        elif seg == "ru":
            ru_html = h
        elif seg.startswith("comm"):
            comm_items.append(h)

    parts: list[str] = []

    if sa_html or ru_html:
        inner = ""
        if sa_html:
            inner += f'<div class="chapter_block iast">{sa_html}</div>'
        if ru_html:
            inner += f'<div class="chapter_block translation">{ru_html}</div>'
        parts.append(f'<div class="chapter_content">{inner}</div>')

    if comm_items:
        items_html = "".join(
            f'<div class="comment_item">{c}</div>' for c in comm_items
        )
        parts.append(f'<div class="comments">{items_html}</div>')

    inner_html = "".join(parts)
    return f'<div class="citation_block" id="{passage}">{inner_html}</div>'


def render_source_html(records: list[dict]) -> str:
    """Render all JSONL records for one source into citation-block HTML.

    Groups records by their 'group' key (same as the alignment group from
    ALIGNMENT_SPEC), preserving first-seen ordering (= file sequence order).
    """
    groups: dict[str, list[dict]] = {}
    for rec in records:
        g = rec.get("group") or rec.get("id", "")
        if g not in groups:
            groups[g] = []
        groups[g].append(rec)

    return "\n".join(render_passage_group(recs) for recs in groups.values())


def text_from_records(records: list[dict]) -> str:
    """Extract concatenated plain text from all records (seq-ordered).

    Used to build a searchable text corpus from JSONL for comparison
    with the HTML-stripped text from original corpus files.
    """
    parts = [
        rec.get("text", "")
        for rec in sorted(records, key=lambda r: r.get("seq", 0))
        if rec.get("text")
    ]
    return " ".join(parts)


def load_jsonl_records(jsonl_path: Path) -> list[dict]:
    """Load all records from a JSONL file (skipping blanks and deleted)."""
    import json
    records = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                if not rec.get("deleted"):
                    records.append(rec)
    return records
