"""H308 Track 1 — GRETIL-TEI -> canonical JSONL converter tests.

Hermetic tests exercise convert_tei() against small synthetic TEI snippets
(no corpus needed). A corpus-level smoke test runs the real Hitopadesha
TEI file when present and checks the CONVERTER_SPEC gates that apply
(round-trip ID stability, uniqueness, never-drop-on-unparseable).
"""
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

_CB_DIR = Path(__file__).parent.parent / "corpus_builder"
sys.path.insert(0, str(_CB_DIR.parent))  # web/ on path so corpus_builder is a package

from corpus_builder.gretil_tei_to_canonical import convert_tei  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HITOPADESHA_TEI = _REPO_ROOT / "GRETIL-1_sanskr" / "tei" / "sa_nArAyaNa-hitopadeza.xml"

_TEI_NS = "http://www.tei-c.org/ns/1.0"


def _write_tei(tmp_path: Path, body_xml: str) -> Path:
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="{_TEI_NS}" xml:id="sa_test">
  <teiHeader><fileDesc><titleStmt><title>Test</title></titleStmt>
  <publicationStmt><p>test</p></publicationStmt></fileDesc></teiHeader>
  <text><body>
{body_xml}
  </body></text>
</TEI>
"""
    p = tmp_path / "sa_test.xml"
    p.write_text(xml, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Hermetic: synthetic TEI snippets
# ---------------------------------------------------------------------------

def test_verse_marker_extracts_passage(tmp_path):
    body = """
<p>maṅgalācaraṇam</p>
<lg>
<l>siddhiḥ sādhye satām astu |</l>
<l>jāhnavī-phena-lekheva // Hit_0.1 //</l>
</lg>
"""
    p = _write_tei(tmp_path, body)
    records, report = convert_tei(p, "test-work")
    verse = [r for r in records if r["structure"] == "verse"]
    assert len(verse) == 1
    r = verse[0]
    assert r["passage"] == "0.1"
    assert r["id"] == "test-work:0.1#sa"
    assert r["group"] == "test-work:0.1"
    assert r["seg"] == "sa" and r["lang"] == "sa"
    assert "// Hit_0.1 //" not in r["text"]
    assert "// Hit_0.1 //" not in r["html"]
    assert report["verse_count"] == 1


def test_prose_paragraph_gets_chapter_scoped_id(tmp_path):
    body = """
<p>maṅgalācaraṇam</p>
<lg>
<l>siddhiḥ sādhye satām astu // Hit_0.1 //</l>
</lg>
<p>atha kathā-mukham</p>
"""
    p = _write_tei(tmp_path, body)
    records, _ = convert_tei(p, "test-work")
    prose = [r for r in records if r["structure"] == "prose"]
    assert len(prose) == 2
    assert prose[0]["passage"] == "c0.p1"
    # prose after the chapter-0 verse still keys to chapter 0
    assert prose[1]["passage"] == "c0.p2"
    assert prose[1]["chapter"] == "0"


def test_chapter_advances_across_verse_markers(tmp_path):
    body = """
<lg><l>verse zero // Hit_0.1 //</l></lg>
<lg><l>verse one // Hit_1.1 //</l></lg>
<p>prose after chapter one begins</p>
"""
    p = _write_tei(tmp_path, body)
    records, _ = convert_tei(p, "test-work")
    prose = [r for r in records if r["structure"] == "prose"][0]
    assert prose["chapter"] == "1"
    assert prose["passage"] == "c1.p1"


def test_unmarked_verse_flagged_never_dropped(tmp_path):
    body = """
<lg><l>truncated marker line // Hit_0.</l></lg>
"""
    p = _write_tei(tmp_path, body)
    records, report = convert_tei(p, "test-work")
    assert len(records) == 1
    assert records[0].get("needs_review") is True
    assert report["unmarked_verse_count"] == 1


def test_prose_wrapping_lg_splits_leading_prose_from_verse(tmp_path):
    body = """
<p>kiṃ ca-
<lg>
<l>varaṃ garbha-srāvo varam // Hit_0.14 //</l>
</lg></p>
"""
    p = _write_tei(tmp_path, body)
    records, _ = convert_tei(p, "test-work")
    assert len(records) == 2
    prose = [r for r in records if r["structure"] == "prose"][0]
    verse = [r for r in records if r["structure"] == "verse"][0]
    assert prose["text"] == "kiṃ ca-"
    assert verse["passage"] == "0.14"


def test_ids_unique_within_source(tmp_path):
    body = """
<lg><l>a // Hit_1.1 //</l></lg>
<p>prose one</p>
<lg><l>b // Hit_1.2 //</l></lg>
<p>prose two</p>
"""
    p = _write_tei(tmp_path, body)
    records, _ = convert_tei(p, "test-work")
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Corpus smoke test: real Hitopadesha TEI (skips if the file is absent)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def hitopadesha_records():
    if not _HITOPADESHA_TEI.exists():
        pytest.skip("Hitopadesha GRETIL TEI not present in this checkout")
    records, report = convert_tei(_HITOPADESHA_TEI, "hitopadesha")
    return records, report


def test_hitopadesha_round_trip_id_stability(hitopadesha_records):
    records_a, _ = hitopadesha_records
    records_b, _ = convert_tei(_HITOPADESHA_TEI, "hitopadesha")
    ids_a = [r["id"] for r in records_a]
    ids_b = [r["id"] for r in records_b]
    assert ids_a == ids_b


def test_hitopadesha_ids_unique(hitopadesha_records):
    records, _ = hitopadesha_records
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids))


def test_hitopadesha_five_chapters_covered(hitopadesha_records):
    records, _ = hitopadesha_records
    chapters = {r["chapter"] for r in records}
    assert chapters == {"0", "1", "2", "3", "4"}


def test_hitopadesha_never_drops_unparseable(hitopadesha_records):
    _, report = hitopadesha_records
    # The one known GRETIL source gap (truncated "// Hit_0." marker,
    # missing verse number) must be flagged, not silently dropped.
    assert report["unmarked_verse_count"] >= 1
