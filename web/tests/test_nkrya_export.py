"""H754 acceptance gates for the НКРЯ triple export (nkrya_export.py).

Two layers, following this repo's convention (hermetic by default, real-corpus
behind `-m corpus`):

  * hermetic  -- a tiny fixture JSONL built in-test; runs everywhere, no data dep.
  * corpus    -- the four real pilot sources; needs web/corpus_builder/jsonl/*,
                 run with ``pytest -m corpus``.

Gates (H754 deliverable 2):
  (a) per-source pair count == both-sides-present group count (== conversion_report seg_counts.sa)
  (b) every emitted XML/TMX file is well-formed (xml.etree parses it)
  (c) TMX carries the required 1.4b elements
  (d) two runs are byte-identical
  (e) zero pairs with an empty side
  (f) monolingual-RU is counted, not silently dropped
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_CB = _REPO / "web" / "corpus_builder"
_JSONL = _CB / "jsonl"

sys.path.insert(0, str(_CB))

import nkrya_export as nx  # noqa: E402

PILOT_EXPECTED = {
    "03_mahabharata-aranyakaparva": 2033,
    "01_ramayana-balakanda": 2268,
    "02_ramayana-ayodhyakanda": 4307,
    "03_ramayana-aranyakanda": 2447,
}


# --------------------------------------------------------------------------- #
# fixture: a hermetic JSONL exercising pair / mono_ru / mono_sa / comm / empty  #
# --------------------------------------------------------------------------- #
def _rec(group, seg, lang, text, **extra):
    r = {"group": group, "seg": seg, "lang": lang, "text": text, "deleted": False}
    r.update(extra)
    return r


@pytest.fixture()
def fixture_jsonl(tmp_path):
    rows = [
        # g1: a clean pair (+ range flag via passage) with a commentary note
        _rec("w:1.1-2", "sa", "sa", "rāmaḥ vanam gacchati", slp1="rAmaH vanam gacCati",
             passage="1.1-2"),
        _rec("w:1.1-2", "ru", "ru", "Рама идёт в лес", passage="1.1-2"),
        _rec("w:1.1-2", "comm1", "ru", "1. Комментарий к стиху.", annotates="1.1-2"),
        # g2: a clean pair, no range, no comm
        _rec("w:1.3", "sa", "sa", "sītā tiṣṭhati", slp1="sItA tizWati", passage="1.3"),
        _rec("w:1.3", "ru", "ru", "Сита стоит", passage="1.3"),
        # g3: monolingual RU (no sa) -> counted, never exported
        _rec("w:1.4", "ru", "ru", "Только русский, без санскрита", passage="1.4"),
        # g4: untranslated sa (no ru) -> counted, never exported
        _rec("w:1.5", "sa", "sa", "anuvāko na anūditaḥ", slp1="anuvAko na anUditaH",
             passage="1.5"),
        # g5: declared ru side but empty text -> empty_side, never exported
        _rec("w:1.6", "sa", "sa", "kaścit ślokaḥ", slp1="kaScit SlokaH", passage="1.6"),
        _rec("w:1.6", "ru", "ru", "   ", passage="1.6"),
        # g6: a deleted row must be ignored entirely
        _rec("w:1.7", "sa", "sa", "should be skipped", passage="1.7", deleted=True),
        _rec("w:1.7", "ru", "ru", "должно быть пропущено", passage="1.7", deleted=True),
    ]
    p = tmp_path / "w.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return p


def test_fixture_classification(fixture_jsonl):
    pairs, stats = nx.classify(str(fixture_jsonl))
    assert stats["pairs"] == 2          # g1, g2
    assert stats["mono_ru"] == 1        # g3 (f: counted, not dropped)
    assert stats["mono_sa"] == 1        # g4
    assert stats["commentary"] == 1     # g1 comm1 (excluded from pairs)
    assert stats["empty_side"] == 1     # g6
    groups = {p["group"] for p in pairs}
    assert groups == {"w:1.1-2", "w:1.3"}
    # (e) no exported pair has an empty side
    for p in pairs:
        assert p["sa_iast"].strip() and p["ru"].strip()
    # flags: range+comm on g1, none on g2
    g1 = next(p for p in pairs if p["group"] == "w:1.1-2")
    assert set(g1["flags"]) == {"range", "comm"}
    g2 = next(p for p in pairs if p["group"] == "w:1.3")
    assert g2["flags"] == []


def test_fixture_natural_sort():
    # 1.2 must sort before 1.10 (natural, not lexicographic)
    keys = ["w:1.10", "w:1.2", "w:1.1"]
    assert sorted(keys, key=nx.natural_key) == ["w:1.1", "w:1.2", "w:1.10"]


def _emit(fixture_jsonl, tmp_path, jsonl_dir=None):
    slug = "w"
    out = tmp_path / "out"
    return nx.export_source(
        slug, str(out),
        jsonl_dir=str(fixture_jsonl.parent),
        meta_dir=str(tmp_path),  # no meta.json -> graceful default
        write=True,
    ), out


def test_fixture_xml_wellformed(fixture_jsonl, tmp_path):
    report, out = _emit(fixture_jsonl, tmp_path)
    # (b) XML + TMX parse
    xml_path = out / "w" / "w.nkrya.xml"
    tmx_path = out / "w" / "w.tmx"
    xroot = ET.parse(xml_path).getroot()
    assert xroot.tag == "document"
    paras = xroot.findall("./body/para")
    assert len(paras) == report["pairs"] == 2
    for para in paras:
        ses = para.findall("se")
        assert len(ses) == 2
        assert ses[0].get("lang") == nx.LANG_SA_XML
        assert ses[0].get("slp1")            # SLP1 rides as an attribute
        assert ses[1].get("lang") == nx.LANG_RU_XML
        assert ses[0].text.strip() and ses[1].text.strip()  # zero empty side
    # (c) TMX 1.4b required elements
    troot = ET.parse(tmx_path).getroot()
    assert troot.tag == "tmx"
    assert troot.get("version") == "1.4"
    header = troot.find("header")
    assert header is not None
    assert header.get("srclang") == nx.LANG_SA_TMX
    assert header.get("segtype")
    tus = troot.findall("./body/tu")
    assert len(tus) == 2
    for tu in tus:
        langs = [tuv.get("{http://www.w3.org/XML/1998/namespace}lang")
                 for tuv in tu.findall("tuv")]
        assert langs == [nx.LANG_SA_TMX, nx.LANG_RU_TMX]
        for tuv in tu.findall("tuv"):
            assert tuv.find("seg").text.strip()


def test_fixture_tsv_shape(fixture_jsonl, tmp_path):
    report, out = _emit(fixture_jsonl, tmp_path)
    lines = (out / "w" / "w.tsv").read_text(encoding="utf-8").splitlines()
    assert lines[0].split("\t") == ["group_id", "sa_iast", "sa_slp1", "ru", "flags"]
    assert len(lines) == 1 + report["pairs"]
    for row in lines[1:]:
        cols = row.split("\t")
        assert len(cols) == 5
        assert cols[1].strip() and cols[3].strip()   # no empty side leaks into TSV


def test_fixture_deterministic(fixture_jsonl, tmp_path):
    # (d) two runs byte-identical
    r1 = nx.export_source("w", str(tmp_path / "a"),
                          jsonl_dir=str(fixture_jsonl.parent),
                          meta_dir=str(tmp_path), write=True)
    r2 = nx.export_source("w", str(tmp_path / "b"),
                          jsonl_dir=str(fixture_jsonl.parent),
                          meta_dir=str(tmp_path), write=True)
    for name in ("w.nkrya.xml", "w.tmx", "w.tsv"):
        a = (tmp_path / "a" / "w" / name).read_bytes()
        b = (tmp_path / "b" / "w" / name).read_bytes()
        assert a == b, name
    # and no BOM
    for name in ("w.nkrya.xml", "w.tmx", "w.tsv"):
        assert not (tmp_path / "a" / "w" / name).read_bytes().startswith(b"\xef\xbb\xbf")


def test_sanskritisms_canonical_order_independent():
    """H821 Wave-4 determinism gate: the singular/plural canonical merge must
    NOT depend on input lemma order (upstream candidate sets iterate in hash
    order, which flipped the sanskritisms index lemma/display across runs).
    Data-free unit test of the fix in sanskritisms/disambiguate.py."""
    import random
    from sanskritisms.disambiguate import merge_plural_singular_duplicates
    lemmas = ["апсара", "апсары", "васу", "рудра", "рудры", "марут", "маруты", "дэва"]
    ref = merge_plural_singular_duplicates(lemmas)
    for _ in range(8):
        shuffled = lemmas[:]
        random.shuffle(shuffled)
        assert merge_plural_singular_duplicates(shuffled) == ref, \
            "canonical merge is order-dependent — sanskritisms index would be non-deterministic"


# --------------------------------------------------------------------------- #
# H905: RU per-token morphology + the Кали→кал rus_words filter               #
# (need pymorphy3 — skipped where the OpenCorpora dict isn't installed)        #
# --------------------------------------------------------------------------- #
def test_ru_morph_shape_and_determinism():
    pytest.importorskip("pymorphy3")
    import ru_morph
    toks = ru_morph.analyze("Богиня Кали собрала кала во тьме.")
    assert [t["surface"] for t in toks] == \
        ["Богиня", "Кали", "собрала", "кала", "во", "тьме"]
    for t in toks:
        assert set(t) == {"surface", "lemma", "pos", "case", "number"}
    # "кала" (common word, genitive of кал) lemmatizes to кал — the very
    # collision the sanskritism filter drops.
    kala = next(t for t in toks if t["surface"] == "кала")
    assert kala["lemma"] == "кал" and kala["pos"] == "NOUN"
    # deterministic: identical output on a second pass
    assert ru_morph.analyze("Рама шёл к рекам великих гандхарвов") == \
        ru_morph.analyze("Рама шёл к рекам великих гандхарвов")


def test_ru_word_filter_kali_kal():
    """The named regression (H905): a lowercase common Russian word that
    collides with a Sanskritism surface form is dropped, while the capitalized
    proper name is kept — Rubanova's opcorpora rus_words filter, via pymorphy3."""
    pytest.importorskip("pymorphy3")
    import json as _json
    import tempfile
    from sanskritisms.extract import ExtractionContext, extract_source
    ctx = ExtractionContext()

    def _lemmas(text):
        d = tempfile.mkdtemp()
        p = Path(d) / "x.jsonl"
        p.write_text(_json.dumps(
            {"group": "g", "seg": "ru", "lang": "ru", "text": text,
             "deleted": False}, ensure_ascii=False) + "\n", encoding="utf-8")
        return set(extract_source(str(p), ctx=ctx)["lexicon"])

    # capitalized proper name mid-sentence → kept
    assert "кали" in _lemmas("Богиня Кали танцевала во тьме.")
    # lowercase common word (кал family) → filtered, no Sanskritism captured
    assert _lemmas("Он не нашёл кала в поле.") == set()
    # a genuine Sanskritism whose form is NOT a known Russian word survives
    assert filters_is_russian("ракшасов") is False


def filters_is_russian(w):
    from sanskritisms import filters
    return filters.is_russian_word(w)


def test_export_ru_morph_sidecar(fixture_jsonl, tmp_path):
    pytest.importorskip("pymorphy3")
    r1 = nx.export_source("w", str(tmp_path / "a"),
                          jsonl_dir=str(fixture_jsonl.parent),
                          meta_dir=str(tmp_path), write=True, with_ru_morph=True)
    side = tmp_path / "a" / "w" / "w.ru_morph.tsv"
    assert side.exists()
    lines = side.read_text(encoding="utf-8").splitlines()
    assert lines[0].split("\t") == \
        ["group_id", "tok_index", "surface", "lemma", "pos", "case", "number"]
    assert len(lines) > 1 and all(len(l.split("\t")) == 7 for l in lines[1:])
    # byte-identical on a second run
    nx.export_source("w", str(tmp_path / "b"), jsonl_dir=str(fixture_jsonl.parent),
                     meta_dir=str(tmp_path), write=True, with_ru_morph=True)
    assert (tmp_path / "a" / "w" / "w.ru_morph.tsv").read_bytes() == \
           (tmp_path / "b" / "w" / "w.ru_morph.tsv").read_bytes()


# --------------------------------------------------------------------------- #
# H906: DCS-anchored SA morphology                                            #
# --------------------------------------------------------------------------- #
def test_dcs_target_mapping():
    """Data-free: slug+passage → DCS text/chapter/verse-range mapping."""
    import dcs_align
    assert dcs_align.dcs_target("03_mahabharata-aranyakaparva", "3.1.1-7") == \
        ("Mahābhārata", "MBh, 3, 1", 1, 7)
    assert dcs_align.dcs_target("05_mahabharata-udyogaparva", "5.12.3") == \
        ("Mahābhārata", "MBh, 5, 12", 3, 3)
    assert dcs_align.dcs_target("03_ramayana-aranyakanda", "1.1") == \
        ("Rāmāyaṇa", "Rām, Ār, 1", 1, 1)
    assert dcs_align.dcs_target("01_atharvaveda", "1.1.1") is None  # not epic-mapped


def _dcs_or_skip():
    import os
    import dcs_align
    if not os.path.exists(dcs_align.DCS_SQLITE):
        pytest.skip("DCS sqlite not present (local-only, see dcs_align.py)")
    g = dcs_align.DcsGold()
    if not g.available:
        pytest.skip("DCS sqlite not available")
    return g


def test_dcs_gold_tokens_and_determinism():
    g = _dcs_or_skip()
    toks = g.gold_tokens("03_mahabharata-aranyakaparva", "3.1.1-7")
    assert toks, "expected DCS gold tokens for a covered MBh verse"
    jana = next(t for t in toks if t["form"] == "janamejaya")
    assert jana["lemma"] == "janamejaya" and jana["upos"] == "NOUN" \
        and jana["case"] == "Nom" and jana["number"] == "Sing"
    # deterministic
    import dcs_align
    g2 = dcs_align.DcsGold()
    assert g2.gold_tokens("03_mahabharata-aranyakaparva", "3.1.1-7") == toks


def test_export_sa_morph_sidecar(fixture_jsonl, tmp_path):
    _dcs_or_skip()
    # the hermetic fixture slug "w" is not DCS-mappable → header-only, but the
    # sidecar must still be well-formed and byte-identical across runs.
    for d in ("a", "b"):
        nx.export_source("w", str(tmp_path / d), jsonl_dir=str(fixture_jsonl.parent),
                         meta_dir=str(tmp_path), write=True, with_sa_morph=True)
    side = tmp_path / "a" / "w" / "w.sa_morph.tsv"
    assert side.read_text(encoding="utf-8").splitlines()[0].split("\t") == \
        ["group_id", "verse", "tok_index", "form", "lemma", "upos", "case",
         "gender", "number"]
    assert side.read_bytes() == (tmp_path / "b" / "w" / "w.sa_morph.tsv").read_bytes()


# --------------------------------------------------------------------------- #
# H906: vidyut second-opinion diff against DCS gold                           #
# --------------------------------------------------------------------------- #
def test_vidyut_mapping_and_clean():
    """Data-free: SLP1 cleaning, sandhi-fold join key, feature mapping."""
    import vidyut_diff as vd
    # dandas / verse markers / digits → spaces; SLP1 + avagraha kept
    assert vd.clean_slp1("evaM dyUtajitAH । pArTAH ॥1॥") == "evaM dyUtajitAH pArTAH"
    # anusvara/visarga folded so DCS surface pairs with vidyut's pada form
    assert vd._join_key("evaM") == "evam"
    assert vd._join_key("pArTAH") == "pArTAs"
    # DCS vocabulary tables are complete
    assert set(vd._VIBHAKTI_TO_CASE.values()) == \
        {"Nom", "Acc", "Ins", "Dat", "Abl", "Gen", "Loc", "Voc"}
    assert vd._LINGA_TO_GENDER == {"Pum": "Masc", "Stri": "Fem", "Napumsaka": "Neut"}
    assert vd._coarse_pos("PROPN") == vd._coarse_pos("NOUN") == "nominal"
    assert vd._coarse_pos("VERB") == "verbal"
    assert vd._coarse_pos("ADV") == "indecl"


class _FakeToken:
    def __init__(self, text, lemma, data=None):
        self.text, self.lemma, self.data = text, lemma, data


class _FakeAnalyzer:
    """Injects a fixed vidyut analysis so diff_group's join/scoring is tested
    without the (local-only) vidyut data pack."""
    available = True

    def __init__(self, tokens):
        self._tokens = tokens

    def analyze_slp1(self, slp1_text):
        return list(self._tokens)


def test_diff_group_join_and_scoring():
    """diff_group pairs on the folded form and scores per-feature agreement only
    where both sides carry the value; unmatched tokens are reported, not scored."""
    import vidyut_diff as vd
    dcs = [
        {"form": "pārthāḥ", "lemma": "pārtha", "upos": "NOUN",
         "case": "Nom", "gender": "Masc", "number": "Plur"},   # matches, case differs
        {"form": "gacchati", "lemma": "gam", "upos": "VERB",
         "case": "", "gender": "", "number": "Sing"},          # matches, all agree
        {"form": "vanam", "lemma": "vana", "upos": "NOUN",
         "case": "Acc", "gender": "Neut", "number": "Sing"},   # dcs_only (no vidyut)
    ]
    vid = [
        {"form": "pArTAs", "lemma": "pArTa", "upos": "NOUN",
         "case": "Acc", "gender": "Masc", "number": "Plur"},   # case disagrees
        {"form": "gacCati", "lemma": "gam", "upos": "VERB",
         "case": "", "gender": "", "number": "Sing"},
        {"form": "extra", "lemma": "x", "upos": "NOUN",
         "case": "Nom", "gender": "Masc", "number": "Sing"},   # vidyut_only
    ]
    rows, c = vd.diff_group(dcs, "ignored (fake analyzer)", _FakeAnalyzer(vid))
    assert c["dcs_tokens"] == 3 and c["vidyut_tokens"] == 3
    assert c["matched"] == 2 and c["dcs_only"] == 1 and c["vidyut_only"] == 1
    # gender/number agree on both matched nominal+verb; case compared once (the
    # verb has no case on either side → not comparable) and disagrees there
    assert c["case_cmp"] == 1 and c["case_ok"] == 0
    assert c["gender_cmp"] == 1 and c["gender_ok"] == 1
    assert c["number_cmp"] == 2 and c["number_ok"] == 2
    agg = vd.aggregate([c])
    assert agg["form_match_rate"] == 2 / 3
    assert agg["case_agree_rate"] == 0.0 and agg["number_agree_rate"] == 1.0


def _vidyut_or_skip():
    import vidyut_diff
    a = vidyut_diff.VidyutAnalyzer()
    if not a.available:
        pytest.skip("vidyut data pack not present (local-only, set $VIDYUT_DATA)")
    # a smoke run also guards against a present-but-unloadable pack
    try:
        toks = a.analyze_slp1("rAmaH vanaM gacCati")
    except Exception as exc:  # pragma: no cover
        pytest.skip("vidyut pack unloadable: %s" % exc)
    if not toks:
        pytest.skip("vidyut produced no tokens")
    return a


def test_vidyut_analyzer_maps_real_tokens():
    """With the real pack: a finite verb → VERB, a declined noun → NOUN with a
    DCS-vocabulary case/gender/number."""
    a = _vidyut_or_skip()
    toks = a.analyze_slp1("nalaH")
    nala = next((t for t in toks if t["form"].startswith("nal")), None)
    assert nala and nala["upos"] == "NOUN"
    assert nala["case"] == "Nom" and nala["gender"] == "Masc"


def test_export_vidyut_diff_sidecar(fixture_jsonl, tmp_path):
    """The vidyut_diff sidecar is well-formed and byte-identical across runs."""
    _dcs_or_skip()
    _vidyut_or_skip()
    for d in ("a", "b"):
        nx.export_source("w", str(tmp_path / d), jsonl_dir=str(fixture_jsonl.parent),
                         meta_dir=str(tmp_path), write=True, with_vidyut_diff=True)
    side = tmp_path / "a" / "w" / "w.vidyut_diff.tsv"
    header = side.read_text(encoding="utf-8").splitlines()[0].split("\t")
    assert header[:5] == ["group_id", "status", "form", "dcs_lemma", "vid_lemma"]
    assert side.read_bytes() == (tmp_path / "b" / "w" / "w.vidyut_diff.tsv").read_bytes()


# --------------------------------------------------------------------------- #
# corpus gates: the real four pilots                                          #
# --------------------------------------------------------------------------- #
@pytest.mark.corpus
@pytest.mark.parametrize("slug,expected", sorted(PILOT_EXPECTED.items()))
def test_pilot_pair_count(slug, expected):
    jsonl = _JSONL / f"{slug}.jsonl"
    if not jsonl.exists():
        pytest.skip(f"{jsonl} not present")
    pairs, stats = nx.classify(str(jsonl))
    # (a) parity: exported pairs == both-sides group count == expected sa seg_count
    assert stats["pairs"] == expected
    assert stats["empty_side"] == 0     # (e)
    # (f) mono_ru is a real integer count in the stats, reported not dropped
    assert isinstance(stats["mono_ru"], int)


@pytest.mark.corpus
def test_pilot_parity_matches_conversion_report():
    report = json.load(open(_CB / "conversion_report.json", encoding="utf-8"))
    by_slug = {s["slug"]: s for s in report["sources"]}
    for slug, expected in PILOT_EXPECTED.items():
        jsonl = _JSONL / f"{slug}.jsonl"
        if not jsonl.exists():
            pytest.skip(f"{jsonl} not present")
        _, stats = nx.classify(str(jsonl))
        assert stats["pairs"] == by_slug[slug]["seg_counts"]["sa"] == expected


@pytest.mark.corpus
@pytest.mark.parametrize("slug", sorted(PILOT_EXPECTED))
def test_pilot_export_wellformed_and_deterministic(slug, tmp_path):
    jsonl = _JSONL / f"{slug}.jsonl"
    if not jsonl.exists():
        pytest.skip(f"{jsonl} not present")
    r1 = nx.export_source(slug, str(tmp_path / "a"), write=True)
    r2 = nx.export_source(slug, str(tmp_path / "b"), write=True)
    for name in (f"{slug}.nkrya.xml", f"{slug}.tmx"):
        # well-formed
        ET.parse(tmp_path / "a" / slug / name)
        # byte-identical across runs
        assert (tmp_path / "a" / slug / name).read_bytes() == \
               (tmp_path / "b" / slug / name).read_bytes()
    assert (tmp_path / "a" / slug / f"{slug}.tsv").read_bytes() == \
           (tmp_path / "b" / slug / f"{slug}.tsv").read_bytes()
    assert r1["pairs"] == r2["pairs"] == PILOT_EXPECTED[slug]
