"""H759 acceptance gates for the 3-path annotation comparison (nkrya_annotate.py).

Two layers, same convention as test_nkrya_export.py:

  * hermetic  -- tiny fixture JSONL + fixture DCS SQLite built in-test; no data
                 dependency, path C (vidyut) not exercised.
  * corpus    -- the real Balakanda JSONL against the real VisualDCS DCS master;
                 needs both on disk, run with ``pytest -m corpus``.

Gates (H759):
  (a) normalization neutralizes sandhi spacing + daṇḍas/verse numbers
  (b) all three crosswalk tiers (exact / sandhi-skeleton / fuzzy) fire on the
      fixture, unmatched is counted
  (c) DCS mojibake lemmas are dropped AND counted, never silently eaten
  (d) two --skip-c runs are byte-identical (metrics JSON + TSV)
  (e) corpus: real Balakanda B line coverage lands in the measured band
"""
import json
import sqlite3
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_CB = _REPO / "web" / "corpus_builder"

sys.path.insert(0, str(_CB))

import nkrya_annotate as na  # noqa: E402


# ------------------------------------------------------------------ hermetic

def test_norm_iast_neutralizes_spacing_and_dandas():
    ours = "evaṃ dyūtajitāḥ pārthāḥ kopitāśca durātmabhiḥ ।"
    dcs = "evaṃ dyūtajitāḥ pārthāḥ kopitāś ca durātmabhiḥ"
    assert na.norm_iast(ours) == na.norm_iast(dcs)
    assert na.norm_iast("varam ॥1॥") == na.norm_iast("varam")


def test_split_lines_drops_empty_and_numeric_chunks():
    text = "tapaḥsvādhyāyanirataṃ tapasvī vāgvidāṃ varam । nāradaṃ paripapraccha ॥1॥"
    lines = na.split_lines(text)
    assert lines == ["tapaḥsvādhyāyanirataṃ tapasvī vāgvidāṃ varam",
                     "nāradaṃ paripapraccha"]


def test_clean_dcs_lemma_mojibake_dropped():
    assert na.clean_dcs_lemma("kﾱp") is None      # damaged kḷp-family lemma
    assert na.clean_dcs_lemma("prak￞") is None
    assert na.clean_dcs_lemma("") is None
    assert na.clean_dcs_lemma("vac") == "vac"
    assert na.clean_dcs_lemma("vṛ") == "vf"            # IAST -> SLP1


@pytest.fixture
def fixture_env(tmp_path, monkeypatch):
    """Tiny 3-group JSONL + matching fixture DCS DB.

    Group 1: exact match. Group 2: fuzzy match (one aksara off). Group 3: no
    DCS counterpart at all."""
    jsonl_dir = tmp_path / "jsonl"
    jsonl_dir.mkdir()
    slug = "01_ramayana-balakanda"
    rows = []
    verses = [
        ("1.1", "tapaḥsvādhyāyanirataṃ tapasvī vāgvidāṃ varam ॥1॥"),
        # skeleton tier: our sandhied 'rāmo ... śreṣṭho' vs DCS de-sandhied
        # 'rāmaḥ ... śreṣṭhaḥ' -- same consonant skeleton, different norm
        ("1.2", "rāmo dharmabhṛtāṃ śreṣṭho lokasya ca hitāya vai ॥2॥"),
        # fuzzy tier: one consonant differs (r vs the DCS row's m) so the
        # skeleton also differs, but the shared-prefix difflib catches it
        ("1.3", "kāmārthaguṇasaṃyuktaṃ dharmārthaguṇavistaram ॥3॥"),
        ("1.4", "gaṅgākūle vyasarjayat sūtaṃ śṛṅgiberapure tathā ॥4॥"),
    ]
    for passage, text in verses:
        g = f"{slug}:{passage}"
        rows.append({"id": g + "#sa", "work": slug, "passage": passage,
                     "seg": "sa", "group": g, "lang": "sa", "text": text,
                     "deleted": False})
        rows.append({"id": g + "#ru", "work": slug, "passage": passage,
                     "seg": "ru", "group": g, "lang": "ru", "text": "перевод",
                     "deleted": False})
    (jsonl_dir / f"{slug}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")

    db = tmp_path / "dcs.sqlite"
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE chapter (chapter_id INTEGER PRIMARY KEY, text_id INT, ref TEXT);
        CREATE TABLE sentence (id INTEGER PRIMARY KEY, chapter_id INT,
                               sent_counter TEXT, sent_subcounter TEXT,
                               text_sandhied TEXT);
        CREATE TABLE token (id INTEGER PRIMARY KEY, sentence_id INT, idx INT,
                            lemma TEXT, upos TEXT);
    """)
    con.execute("INSERT INTO chapter VALUES (1, 143, 'Rām, Bā, 1')")
    # exact counterpart of verse 1.1 (DCS spaces the sandhi differently)
    con.execute("INSERT INTO sentence VALUES (10, 1, '1', '1',"
                " 'tapaḥsvādhyāyanirataṃ tapasvī vāgvidāṃ varam')")
    # de-sandhied counterpart of verse 1.2 (aḥ vs o twice) -> skeleton tier
    con.execute("INSERT INTO sentence VALUES (11, 1, '1', '2',"
                " 'rāmaḥ dharmabhṛtāṃ śreṣṭhaḥ lokasya ca hitāya vai')")
    # near counterpart of verse 1.3 (one consonant differs -> fuzzy tier)
    con.execute("INSERT INTO sentence VALUES (12, 1, '2', '1',"
                " 'kāmārthaguṇasaṃyuktaṃ dharmārthaguṇavistamam')")
    for i, (lemma, upos) in enumerate(
            [("tapas", "NOUN"), ("svādhyāya", "NOUN"), ("nirata", "ADJ"),
             ("tapasvin", "NOUN"), ("vāc", "NOUN"), ("vid", "ADJ"), ("vara", "ADJ")]):
        con.execute("INSERT INTO token VALUES (NULL, 10, ?, ?, ?)", (i + 1, lemma, upos))
    con.execute("INSERT INTO token VALUES (NULL, 11, 1, 'nārada', 'NOUN')")
    con.execute("INSERT INTO token VALUES (NULL, 11, 2, 'kﾱp', 'VERB')")  # mojibake
    con.execute("INSERT INTO token VALUES (NULL, 12, 1, 'kāma', 'NOUN')")
    con.commit()
    con.close()

    monkeypatch.setattr(na, "JSONL_DIR", str(jsonl_dir))
    return slug, str(db), tmp_path


def test_crosswalk_tiers_and_unmatched(fixture_env):
    slug, db, _tmp = fixture_env
    metrics, groups = na.process_source(slug, db, tagger=None, quiet=True)
    assert metrics["groups"] == 4
    assert metrics["b_lines_exact"] == 1
    assert metrics["b_lines_sandhi"] == 1
    assert metrics["b_lines_fuzzy"] == 1
    assert metrics["b_lines_unmatched"] == 1
    assert metrics["b_groups_full"] == 3
    assert metrics["b_groups_zero"] == 1
    # gate (c): the mojibake token is dropped AND counted
    assert metrics["b_lemma_dropped"] == 1
    by_group = {g["group"]: g for g in groups}
    assert by_group[f"{slug}:1.1"]["b_lemmas"] == sorted(
        ["tapas", "svADyAya", "nirata", "tapasvin", "vAc", "vid", "vara"])
    assert by_group[f"{slug}:1.2"]["b_lemmas"] == ["nArada"]
    assert by_group[f"{slug}:1.3"]["b_lemmas"] == ["kAma"]


def test_two_runs_byte_identical(fixture_env):
    slug, db, tmp = fixture_env
    outs = []
    for run in ("r1", "r2"):
        out = tmp / run
        rc = na.main(["--source", slug, "--skip-c", "--dcs-db", db,
                      "--out", str(out), "--quiet"])
        assert rc == 0
        outs.append({p.relative_to(out).as_posix(): p.read_bytes()
                     for p in out.rglob("*") if p.is_file()})
    assert outs[0] == outs[1]
    assert "annotation_3path_metrics.json" in outs[0]


# -------------------------------------------------------------------- corpus

@pytest.mark.corpus
def test_real_balakanda_b_coverage():
    db = Path(na.DEFAULT_DCS_DB)
    src = Path(na.JSONL_DIR) / "01_ramayana-balakanda.jsonl"
    if not db.exists() or not src.exists():
        pytest.skip("real DCS master / pilot JSONL not on this machine")
    metrics, _groups = na.process_source("01_ramayana-balakanda", str(db),
                                         tagger=None, quiet=True)
    covered = (metrics["b_lines_exact"] + metrics.get("b_lines_sandhi", 0)
               + metrics["b_lines_fuzzy"])
    ratio = covered / metrics["lines"]
    # measured 12-07-2026: ~0.85 on the vulgate Balakanda vs the DCS critical
    # edition (three-tier matcher); the assert guards the band, not the number
    assert 0.6 <= ratio <= 0.97
    assert metrics["b_groups_full"] > 1000
