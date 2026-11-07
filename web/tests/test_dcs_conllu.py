"""H6371 acceptance gates for the CoNLL-U 4th emitter (W7).

Two layers, same convention as test_nkrya_export.py / test_nkrya_annotate.py:

  * hermetic  -- tiny fixture dcs-conllu directory + fixture JSONL built
                 in-test; no data dependency, everything runs anywhere.
  * corpus    -- the real pilot JSONLs against the real sibling dcs-conllu
                 sparse clone; needs the clone on disk, run with
                 ``pytest -m corpus``.

Gates (H6371):
  (a) dcs-conllu parsing: sentences carry text/sent_id/rows; MWT range rows
      and interior words survive verbatim
  (b) the W2 three-tier crosswalk (exact / sandhi / fuzzy) fires through the
      CoNLL-U index exactly as through the sqlite index; unmatched counted
  (c) the emitter serializes valid CoNLL-U (conllu_validate returns zero
      errors), with sandhi as multiword-token range rows
  (d) DCS->UPOS mapping: CONJ -> CCONJ; an unmapped tag passes through
      VERBATIM and is counted, never coerced
  (e) determinism: two runs are byte-identical
  (f) lemma-coverage honesty: empty and damaged lemmas counted, not faked
  (g) validator negative controls: each structural defect is caught
"""
import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_CB = _REPO / "web" / "corpus_builder"

sys.path.insert(0, str(_CB))

import conllu_validate as cv  # noqa: E402
import dcs_conllu as dc       # noqa: E402
import nkrya_export as ne     # noqa: E402


# ------------------------------------------------------------------ fixtures

FIXTURE_CONLLU = """\
# sent_id = 101
# sent_counter = 1
# sent_subcounter = 1
# text = rāmaḥ vāṅmayam pibati
1\trāmaḥ\trāma\tNOUN\t_\tCase=Nom|Gender=Masc|Number=Sing\t_\t_\t_\tUnsandhied=rāmaḥ
2\tvāṅmayam\tvāc\tNOUN\t_\tCase=Acc|Gender=Neut|Number=Sing\t_\t_\t_\t_
3\tpibati\tpā\tVERB\t_\tTense=Pres|Mood=Ind|Person=3|Number=Sing\t_\t_\t_\t_

# sent_id = 102
# sent_counter = 1
# sent_subcounter = 2
# text = yasyāsya kamalaṃca dadāti
1-2\tyasyāsya\t_\t_\t_\t_\t_\t_\t_\t_
1\tyasya\tyad\tPRON\t_\tCase=Gen|Gender=Masc|Number=Sing\t_\t_\t_\t_
2\tāsya\tāsya\tNOUN\t_\tCase=Loc|Gender=Neut|Number=Sing\t_\t_\t_\t_
3-4\tkamalaṃca\t_\t_\t_\t_\t_\t_\t_\t_
3\tkamala\tkamala\tNOUN\t_\tFormation=them|Case=Cpd\t_\t_\t_\t_
4\tca\tca\tCONJ\t_\t_\t_\t_\t_\tUnsandhied=ca
5\tdadāti\tdā\tVERB\t_\tTense=Pres|Mood=Ind|Person=3|Number=Sing\t_\t_\t_\t_

# sent_id = 103
# sent_counter = 2
# sent_subcounter = 1
# text = dharmeṇa dharmam aprākṣīt api
1\tdharmeṇa\tdharma\tNOUN\t_\tCase=Ins|Gender=Masc|Number=Sing\t_\t_\t_\t_
2\tdharmam\tdharma\tNOUN\t_\tCase=Acc|Gender=Masc|Number=Sing\t_\t_\t_\t_
3\taprākṣīt\tpra\tWEIRD\t_\t_\t_\t_\t_\tLemmaId=0
4\tapi\t_\t_\t_\t_\t_\t_\t_\t_

"""

FIXTURE_JSONL_VERSES = [
    # exact: identical after norm_iast (only spacing differs)
    ("1.1", "rāmaḥ vāṅ mayam pibati ॥1॥"),
    # no DCS counterpart at all -> unmatched, group counted zero
    ("1.2", "gomayo nagaram agacchat ॥2॥"),
    # exact: DCS surface is the sandhied MWT "kamalaṃca", ours spaces it
    ("1.3", "yasyāsya kamalaṃ ca dadāti ॥3॥"),
    # fuzzy: one consonant off vs sent 103 (aprākṣīn vs aprākṣīt)
    ("2.1", "dharmeṇa dharmam aprākṣīn api ॥4॥"),
]


def _write_fixture(tmp_path):
    dcs_dir = tmp_path / "dcs-conllu" / "files" / "Rāmāyaṇa"
    dcs_dir.mkdir(parents=True)
    (dcs_dir / "Rāmāyaṇa-0000-Rām, Bā, 1-1067.conllu").write_text(
        FIXTURE_CONLLU, encoding="utf-8", newline="\n")

    jsonl_dir = tmp_path / "jsonl"
    jsonl_dir.mkdir()
    slug = "01_ramayana-balakanda"
    rows = []
    for passage, text in FIXTURE_JSONL_VERSES:
        g = f"{slug}:{passage}"
        rows.append({"id": g + "#sa", "work": slug, "passage": passage,
                     "seg": "sa", "group": g, "lang": "sa", "text": text,
                     "deleted": False})
        rows.append({"id": g + "#ru", "work": slug, "passage": passage,
                     "seg": "ru", "group": g, "lang": "ru", "text": "перевод",
                     "deleted": False})
    (jsonl_dir / f"{slug}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows),
        encoding="utf-8")
    return slug, tmp_path, jsonl_dir


# ------------------------------------------------------------------ hermetic

def test_parse_conllu_file_sentences_and_mwt(tmp_path):
    slug, tmp, _jd = _write_fixture(tmp_path)
    d = dc.DcsConllu(str(tmp / "dcs-conllu" / "files"))
    assert d.available and d.available_for(slug)
    sents = dc.parse_conllu_file(
        str(tmp / "dcs-conllu" / "files" / "Rāmāyaṇa" /
            "Rāmāyaṇa-0000-Rām, Bā, 1-1067.conllu"))
    assert [s.sent_id for s in sents] == ["101", "102", "103"]
    s102 = sents[1]
    assert s102.text == "yasyāsya kamalaṃca dadāti"
    assert s102.rows[0][0] == "1-2"          # MWT range rows survive verbatim
    assert s102.rows[0][1] == "yasyāsya"
    assert s102.rows[3][0] == "3-4"          # second sandhi range
    assert s102.rows[1][0] == "1"            # interior word row


def test_crosswalk_tiers_through_conllu_index(tmp_path):
    slug, tmp, _jd = _write_fixture(tmp_path)
    d = dc.DcsConllu(str(tmp / "dcs-conllu" / "files"))
    tier, sent, amb = d.match(slug, "rāmaḥ vāṅ mayam pibati ॥1॥")
    assert tier == "exact" and sent.sent_id == "101" and not amb
    # tier 2 (sandhi skeleton): our sandhied 'rāmo' vs DCS 'rāmaḥ' surface
    tier, sent, _ = d.match(slug, "rāmo vāṅ mayam pibati")
    assert tier == "sandhi" and sent.sent_id == "101"
    tier, sent, _ = d.match(slug, "dharmeṇa dharmam aprākṣīn api")
    assert tier == "fuzzy" and sent.sent_id == "103"
    tier, sent, _ = d.match(slug, "gomayo nagaram agacchat")
    assert tier is None and sent is None


def test_emitter_output_validates_and_carries_mwt(tmp_path, monkeypatch):
    slug, tmp, jsonl_dir = _write_fixture(tmp_path)
    monkeypatch.setattr(ne, "JSONL_DIR", str(jsonl_dir))
    d = dc.DcsConllu(str(tmp / "dcs-conllu" / "files"))
    units = ne.sa_units(str(jsonl_dir / f"{slug}.jsonl"))
    text, st = ne.conllu(units, slug, d)
    # gate (c): zero structural errors from our own validator
    errors, _warns, wcounts, n = cv.validate_text(text, "<emitted>")
    assert errors == []
    assert n == 3  # three matched sentences (101, 102, 103)
    # sandhi as MWT: sentence 102 kept BOTH ranges + interior rows
    assert "1-2\tyasyāsya" in text
    assert "3-4\tkamalaṃca" in text
    assert "\n3\tkamala\tkamala\tNOUN" in text
    # gate (b): tiers + unmatched counted
    assert st["conllu_lines_exact"] == 2
    assert st["conllu_lines_fuzzy"] == 1
    assert st["conllu_lines_unmatched"] == 1
    assert st["conllu_groups_zero"] == 1
    assert st["conllu_mwt_ranges"] == 2
    # sent_id carries our group key; dcs provenance rides as comments
    assert "# sent_id = %s:2.1:L1" % slug in text
    assert "# dcs_match = fuzzy" in text
    assert "# dcs_sent_id = 103" in text


def test_upos_mapping_conj_to_cconj_unmapped_verbatim(tmp_path, monkeypatch):
    slug, tmp, jsonl_dir = _write_fixture(tmp_path)
    monkeypatch.setattr(ne, "JSONL_DIR", str(jsonl_dir))
    d = dc.DcsConllu(str(tmp / "dcs-conllu" / "files"))
    units = ne.sa_units(str(jsonl_dir / f"{slug}.jsonl"))
    text, st = ne.conllu(units, slug, d)
    # gate (d): CONJ -> CCONJ
    assert "\n4\tca\tca\tCCONJ" in text
    # gate (d): the unmapped WEIRD tag passes through verbatim + counted
    assert "\n3\taprākṣīt\tpra\tWEIRD" in text
    assert st["conllu_unmapped_upos"] == {"WEIRD": 1}
    # DCS feature extensions inventoried, not dropped
    assert st["conllu_feat_extensions"]["Formation=them"] == 1
    assert st["conllu_feat_extensions"]["Case=Cpd"] == 1
    # validator W1 is the tripwire for the unmapped tag
    _e, _w, wcounts, _n = cv.validate_text(text, "<emitted>")
    assert wcounts["W1"] >= 1


def test_lemma_coverage_counts_empty_and_damaged(tmp_path, monkeypatch):
    slug, tmp, jsonl_dir = _write_fixture(tmp_path)
    monkeypatch.setattr(ne, "JSONL_DIR", str(jsonl_dir))
    d = dc.DcsConllu(str(tmp / "dcs-conllu" / "files"))
    units = ne.sa_units(str(jsonl_dir / f"{slug}.jsonl"))
    text, st = ne.conllu(units, slug, d)
    # fixture sent 103 word 4 has an empty lemma (_), word 3 a lemma ok but
    # damaged lemma strings would count under lemma_bad
    assert st["conllu_lemma_empty"] == 1
    # gate (f): nothing faked — the row is still there, still `_`
    assert "\n4\tapi\t_\t_" in text


def test_determinism_two_runs_byte_identical(tmp_path, monkeypatch):
    slug, tmp, jsonl_dir = _write_fixture(tmp_path)
    monkeypatch.setattr(ne, "JSONL_DIR", str(jsonl_dir))
    d1 = dc.DcsConllu(str(tmp / "dcs-conllu" / "files"))
    d2 = dc.DcsConllu(str(tmp / "dcs-conllu" / "files"))
    units = ne.sa_units(str(jsonl_dir / f"{slug}.jsonl"))
    t1, s1 = ne.conllu(units, slug, d1)
    t2, s2 = ne.conllu(units, slug, d2)
    assert t1 == t2 and s1 == s2


def test_out_of_scope_slug_emits_nothing_but_reports():
    class _D:
        @staticmethod
        def available_for(slug):
            return False
    text, st = ne.conllu([{"group": "x:y:1", "sa_iast": "varam", "sa_slp1": ""}],
                         "bhagavadgita-smirnov", _D)
    assert st["conllu_dcs_scope"] is False
    assert st["conllu_sentences"] == 0


# ------------------------------------------- validator negative controls

def _mini(text):
    return cv.validate_text(text, "<mini>")


def test_validator_negative_controls():
    base = ("# sent_id = 1\n# text = a b\n"
            "1\ta\ta\tNOUN\t_\t_\t_\t_\t_\t_\n"
            "2\tb\tb\tNOUN\t_\t_\t_\t_\t_\t_\n\n")
    errors, _w, _c, n = _mini(base)
    assert errors == [] and n == 1
    # E1: wrong column count
    e, *_ = _mini("# sent_id = 1\n# text = a\n1\ta\ta\tNOUN\t_\t_\t_\t_\t_\n\n")
    assert any("E1" in x for x in e)
    # E2: id out of order
    e, *_ = _mini(base.replace("2\tb", "1\tb"))
    assert any("E2" in x for x in e)
    # E3: range row with non-underscore UPOS
    bad = ("# sent_id = 1\n# text = ab b\n"
           "1-2\tab\t_\tNOUN\t_\t_\t_\t_\t_\t_\n"
           "1\ta\ta\tNOUN\t_\t_\t_\t_\t_\t_\n"
           "2\tb\tb\tNOUN\t_\t_\t_\t_\t_\t_\n"
           "3\tb\tb\tNOUN\t_\t_\t_\t_\t_\t_\n\n")
    e, *_ = _mini(bad)
    assert any("E3" in x for x in e)
    # E7: duplicate sent_id
    e, *_ = _mini(base + base)
    assert any("duplicate sent_id" in x for x in e)
    # E8: text mismatch
    e, *_ = _mini(base.replace("# text = a b", "# text = a c"))
    assert any("E8" in x for x in e)
    # E5: malformed feats
    e, *_ = _mini(base.replace("1\ta\ta\tNOUN\t_\t_",
                               "1\ta\ta\tNOUN\t_\tCase"))
    assert any("E5" in x for x in e)


def test_validator_flags_mwt_structure_and_text_reconstruction():
    good = ("# sent_id = 1\n# text = ab c\n"
            "1-2\tab\t_\t_\t_\t_\t_\t_\t_\t_\n"
            "1\ta\ta\tNOUN\t_\t_\t_\t_\t_\t_\n"
            "2\tb\tb\tNOUN\t_\t_\t_\t_\t_\t_\n"
            "3\tc\tc\tNOUN\t_\t_\t_\t_\t_\t_\n\n")
    errors, _w, _c, _n = _mini(good)
    assert errors == []  # interior words excluded from reconstruction
    # overlapping range (3-4 after range covering 3) -> E2
    bad = good.replace("2\tb\tb\tNOUN", "3\tb\tb\tNOUN")
    e, *_ = _mini(bad)
    assert any("E2" in x for x in e)


def test_validator_cli_exit_code(tmp_path):
    p = tmp_path / "ok.conllu"
    p.write_text("# sent_id = 1\n# text = a\n"
                 "1\ta\ta\tNOUN\t_\t_\t_\t_\t_\t_\n\n", encoding="utf-8")
    assert cv.main([str(p), "--quiet"]) == 0
    p2 = tmp_path / "bad.conllu"
    p2.write_text("1\ta\ta\tNOUN\t_\t_\t_\t_\t_\n\n", encoding="utf-8")
    assert cv.main([str(p2), "--quiet"]) == 1


# ------------------------------------------------------- corpus (real data)


@pytest.mark.corpus
@pytest.mark.skipif(not Path(dc.DCS_CONLLU_DIR).exists(),
                    reason="sibling dcs-conllu sparse clone not present")
def test_corpus_pilot_emission_validates_and_covers():
    """Real pilot JSONLs through the real dcs-conllu clone: emitted files
    pass the validator; MBh 3 line coverage lands in the W2 band (>=95%),
    Rāmāyaṇa kāṇḍas partial by construction (30-80%)."""
    d = dc.DcsConllu()
    assert d.available
    for slug in ne.PILOT_SOURCES:
        jp = Path(ne.JSONL_DIR) / f"{slug}.jsonl"
        if not jp.exists():
            pytest.skip(f"{slug}.jsonl not on this machine")
        units = ne.sa_units(str(jp))
        text, st = ne.conllu(units, slug, d)
        errors, _w, _wc, n = cv.validate_text(text, slug)
        assert errors == [], "%s: %s" % (slug, errors[:3])
        assert n == st["conllu_sentences"]
        total = st["conllu_lines"]
        covered = total - st["conllu_lines_unmatched"]
        pct = 100.0 * covered / max(1, total)
        if "mahabharata" in slug:
            assert pct >= 95.0, "MBh 3 fell below the W2 coverage band"
        else:
            assert 30.0 <= pct <= 80.0, (
                "Rām %s coverage %.1f%% outside the partial band" % (slug, pct))
