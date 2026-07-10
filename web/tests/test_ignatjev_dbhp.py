"""H534 acceptance gate: Ignatjev DBhP Vol-1 / Skandha-1 parse counts.

Marked ``corpus`` because it needs the source PDF (in AdnrejIgnatjev/) and the
``pdftotext`` binary; run with ``-m corpus``. Asserts the pilot counts that the
handoff requires to equal the PDF's own printed numbering.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_CB = _REPO / "web" / "corpus_builder"
_PDF = _REPO / "AdnrejIgnatjev" / "devibhagavata-purana" / "Девибхагавата-пурана. Том 1.pdf"

sys.path.insert(0, str(_CB))

pytestmark = pytest.mark.corpus

pytest.importorskip("regex")


@pytest.fixture(scope="module")
def skandha1():
    if not _PDF.exists():
        pytest.skip("DBhP Vol 1 PDF not present")
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext (poppler) not on PATH")
    import ignatjev_pdf_to_canonical as ig
    text = ig.extract_pdf_text(_PDF)
    records, report = ig.parse_volume(text, 1, skandha_only=1)
    return records, report


def test_chapter_count(skandha1):
    _, report = skandha1
    assert report["chapters"] == 20  # DBhP skandha 1 has 20 adhyayas


def test_verse_count_matches_edition(skandha1):
    # The edition's own preface states skandha 1 = 1184 slokas; merged verse
    # ranges make the record count slightly lower, never higher.
    _, report = skandha1
    assert 1150 <= report["verse_count"] <= 1184


def test_per_chapter_verse_numbering(skandha1):
    """Each chapter's record count must not exceed its printed max verse label
    (a record beyond the max label would mean a spurious verse split)."""
    import re
    from collections import defaultdict
    records, _ = skandha1
    by_ch = defaultdict(list)
    for r in records:
        if r["seg"] == "ru":
            by_ch[r["chapter"]].append(r["passage"].split(".")[-1])
    assert len(by_ch) == 20
    for ch, labels in by_ch.items():
        maxv = max(int(re.split(r"[-–]", l)[-1]) for l in labels)
        assert len(labels) <= maxv, f"ch {ch}: {len(labels)} recs > max {maxv}"


def test_footnotes_contiguous(skandha1):
    """Every comment carries a footnote id and the ids are the contiguous
    1..N sequence the PDF prints (no endnote dropped mid-run)."""
    records, _ = skandha1
    fns = sorted(r["fn"] for r in records if str(r["seg"]).startswith("comm"))
    assert fns, "no comments parsed"
    assert fns == list(range(1, len(fns) + 1)), "footnote ids not contiguous 1..N"
    assert len(fns) >= 420  # skandha 1 has ~429 endnotes


def test_no_glued_footnote_digits_in_verse_text(skandha1):
    """Footnote superscripts must be stripped from the searchable verse text."""
    import re
    records, _ = skandha1
    glued = [r["passage"] for r in records
             if r["seg"] == "ru" and re.search(r"[А-Яа-яё]\d", r["text"])]
    assert not glued, f"verses still carry glued footnote digits: {glued[:5]}"
