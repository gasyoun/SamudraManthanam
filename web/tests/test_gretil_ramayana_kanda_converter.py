"""H765 — GRETIL Ramayana id-attribute TEI -> canonical JSONL converter tests.

Hermetic tests exercise convert_kanda() against small synthetic TEI snippets
(no corpus needed). A corpus-level smoke test runs the real sa_rAmAyaNa.xml
TEI when present and checks kāṇḍas 6 (Yuddha) and 7 (Uttara) round-trip.
"""
import sys
from pathlib import Path

import pytest

_CB_DIR = Path(__file__).parent.parent / "corpus_builder"
sys.path.insert(0, str(_CB_DIR.parent))  # web/ on path so corpus_builder is a package

from corpus_builder.gretil_ramayana_kanda_to_canonical import convert_kanda  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RAMAYANA_TEI = _REPO_ROOT / "GRETIL-1_sanskr" / "tei" / "sa_rAmAyaNa.xml"

_TEI_NS = "http://www.tei-c.org/ns/1.0"


def _write_tei(tmp_path: Path, kanda_xml: str) -> Path:
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="{_TEI_NS}" xml:id="sa_test">
  <teiHeader><fileDesc><titleStmt><title>Test</title></titleStmt>
  <publicationStmt><p>test</p></publicationStmt></fileDesc></teiHeader>
  <text><body>
{kanda_xml}
  </body></text>
</TEI>
"""
    p = tmp_path / "sa_test.xml"
    p.write_text(xml, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Hermetic: synthetic TEI snippets
# ---------------------------------------------------------------------------

def test_id_attribute_extracts_passage(tmp_path):
    body = """
<div type="kāṇḍa" n="6">
  <lg xml:id="R_6.001.001">
    <l xml:id="R_6.001.001ab">pada one</l>
    <l xml:id="R_6.001.001cd">pada two</l>
  </lg>
</div>
"""
    p = _write_tei(tmp_path, body)
    records, report = convert_kanda(p, 6, "test-work")
    assert len(records) == 1
    r = records[0]
    assert r["passage"] == "1.1"
    assert r["id"] == "test-work:1.1#sa"
    assert r["group"] == "test-work:1.1"
    assert r["chapter"] == "1"
    assert r["text"] == "pada one pada two"
    assert report["verse_count"] == 1


def test_leading_zeros_stripped(tmp_path):
    body = """
<div type="kāṇḍa" n="6">
  <lg xml:id="R_6.012.034">
    <l xml:id="R_6.012.034ab">x</l>
  </lg>
</div>
"""
    p = _write_tei(tmp_path, body)
    records, _ = convert_kanda(p, 6, "test-work")
    assert records[0]["passage"] == "12.34"
    assert records[0]["chapter"] == "12"


def test_only_selected_kanda_extracted(tmp_path):
    body = """
<div type="kāṇḍa" n="6">
  <lg xml:id="R_6.001.001"><l xml:id="R_6.001.001ab">six</l></lg>
</div>
<div type="kāṇḍa" n="7">
  <lg xml:id="R_7.001.001"><l xml:id="R_7.001.001ab">seven</l></lg>
</div>
"""
    p = _write_tei(tmp_path, body)
    records6, _ = convert_kanda(p, 6, "test-work-6")
    records7, _ = convert_kanda(p, 7, "test-work-7")
    assert len(records6) == 1 and records6[0]["text"] == "six"
    assert len(records7) == 1 and records7[0]["text"] == "seven"


def test_missing_kanda_raises(tmp_path):
    body = """
<div type="kāṇḍa" n="6">
  <lg xml:id="R_6.001.001"><l xml:id="R_6.001.001ab">x</l></lg>
</div>
"""
    p = _write_tei(tmp_path, body)
    with pytest.raises(ValueError):
        convert_kanda(p, 3, "test-work")


def test_unmarked_lg_flagged_never_dropped(tmp_path):
    body = """
<div type="kāṇḍa" n="6">
  <lg><l>no id at all</l></lg>
</div>
"""
    p = _write_tei(tmp_path, body)
    records, report = convert_kanda(p, 6, "test-work")
    assert len(records) == 1
    assert records[0].get("needs_review") is True
    assert report["unmarked_verse_count"] == 1


def test_ids_unique_within_kanda(tmp_path):
    body = """
<div type="kāṇḍa" n="6">
  <lg xml:id="R_6.001.001"><l xml:id="R_6.001.001ab">a</l></lg>
  <lg xml:id="R_6.001.002"><l xml:id="R_6.001.002ab">b</l></lg>
</div>
"""
    p = _write_tei(tmp_path, body)
    records, _ = convert_kanda(p, 6, "test-work")
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Corpus smoke test: real sa_rAmAyaNa.xml (skips if the file is absent)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def yuddha_records():
    if not _RAMAYANA_TEI.exists():
        pytest.skip("GRETIL sa_rAmAyaNa.xml not present in this checkout")
    return convert_kanda(_RAMAYANA_TEI, 6, "06_ramayana-yuddhakanda")


@pytest.fixture(scope="session")
def uttara_records():
    if not _RAMAYANA_TEI.exists():
        pytest.skip("GRETIL sa_rAmAyaNa.xml not present in this checkout")
    return convert_kanda(_RAMAYANA_TEI, 7, "07_ramayana-uttarakanda")


def test_yuddha_round_trip_id_stability(yuddha_records):
    records_a, _ = yuddha_records
    records_b, _ = convert_kanda(_RAMAYANA_TEI, 6, "06_ramayana-yuddhakanda")
    assert [r["id"] for r in records_a] == [r["id"] for r in records_b]


def test_yuddha_ids_unique(yuddha_records):
    records, _ = yuddha_records
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids))


def test_yuddha_never_drops_unparseable(yuddha_records):
    _, report = yuddha_records
    assert report["unmarked_verse_count"] == 0


def test_uttara_round_trip_id_stability(uttara_records):
    records_a, _ = uttara_records
    records_b, _ = convert_kanda(_RAMAYANA_TEI, 7, "07_ramayana-uttarakanda")
    assert [r["id"] for r in records_a] == [r["id"] for r in records_b]


def test_uttara_ids_unique(uttara_records):
    records, _ = uttara_records
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids))


def test_uttara_never_drops_unparseable(uttara_records):
    _, report = uttara_records
    assert report["unmarked_verse_count"] == 0
