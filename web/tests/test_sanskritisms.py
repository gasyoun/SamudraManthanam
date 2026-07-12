"""H760 acceptance gates for the sanskritism extraction package
(web/corpus_builder/sanskritisms/).

Two layers, following this repo's convention (hermetic by default, real
data behind `-m corpus`):

  * hermetic -- synthetic tiny lemma pools / decl rules / JSONL fixtures;
    runs everywhere, no data dependency.
  * corpus   -- the real tracked diplom-rubanova curated lists + a real
                pilot JSONL source; run with ``pytest -m corpus``.
"""
import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_CB = _REPO / "web" / "corpus_builder"

sys.path.insert(0, str(_CB))

from sanskritisms import lexicon as lx  # noqa: E402
from sanskritisms import paradigms as pd  # noqa: E402
from sanskritisms import filters as flt  # noqa: E402
from sanskritisms import annotations as an  # noqa: E402
from sanskritisms import disambiguate as dis  # noqa: E402
from sanskritisms.extract import (  # noqa: E402
    ExtractionContext, build_name_index, discover_ru_sources, extract_source,
    iter_ru_segments,
)


# --------------------------------------------------------------------------- #
# lexicon.py / paradigms.py                                                   #
# --------------------------------------------------------------------------- #
TINY_DECL_RULES = """_
nom _
gen а
dat у
acc а
ins ом
loc е

а
nom а
gen ы, и, а
dat е, у
acc у, а
ins ой
loc е

я
nom я
gen и
dat е
acc ю
ins ей
loc е
"""


@pytest.fixture()
def tiny_rules_path(tmp_path):
    p = tmp_path / "decl_rules.txt"
    p.write_text(TINY_DECL_RULES, encoding="utf-8")
    return p


def test_parse_decl_rules(tiny_rules_path):
    rules = lx.parse_decl_rules(str(tiny_rules_path))
    assert set(rules) == {"_", "а", "я"}
    assert rules["_"]["nom"] == [""]
    assert rules["а"]["gen"] == ["ы", "и", "а"]
    assert rules["я"]["ins"] == ["ей"]


@pytest.mark.parametrize("lemma,expected", [
    ("брахман", "_"),
    ("юдхиштхира", "а"),
    ("дхаумья", "я"),
    ("агни", None),
    ("ваю", None),
    ("шатадату", None),
])
def test_declension_class(lemma, expected):
    assert lx.declension_class(lemma) == expected


def test_generate_forms_consonant_stem(tiny_rules_path):
    rules = lx._freeze(lx.parse_decl_rules(str(tiny_rules_path)))
    forms = pd.generate_forms("брахман", rules)
    assert forms == {"брахман", "брахмана", "брахману", "брахманом", "брахмане"}


def test_generate_forms_a_stem_matches_reference(tiny_rules_path):
    # Cross-checked against the tracked Ram3_automated_index_forms.txt entry:
    # "индра : ['индра', 'индре', 'индры', 'индрой', 'индру']"
    rules = lx._freeze(lx.parse_decl_rules(str(tiny_rules_path)))
    forms = pd.generate_forms("индра", rules)
    for expected in ("индра", "индре", "индры", "индрой", "индру"):
        assert expected in forms


def test_generate_forms_indeclinable(tiny_rules_path):
    rules = lx._freeze(lx.parse_decl_rules(str(tiny_rules_path)))
    assert pd.generate_forms("агни", rules) == {"агни"}


def test_build_reverse_index_maps_ambiguous_surface_forms(tiny_rules_path):
    rules = lx._freeze(lx.parse_decl_rules(str(tiny_rules_path)))
    # ракшас (consonant) gen/acc "ракшаса"; ракшаса (а-stem) nom "ракшаса" -- collide.
    index = pd.build_reverse_index({"ракшас", "ракшаса"}, rules)
    assert index["ракшаса"] == {"ракшас", "ракшаса"}


# --------------------------------------------------------------------------- #
# filters.py                                                                   #
# --------------------------------------------------------------------------- #
def test_tokenize_sentence_initial_flags():
    text = "Рама вошёл в лес. Сита осталась дома! Лакшмана искал оленя."
    toks = list(flt.tokenize(text))
    by_surface = {}
    for surface, start, sentence_initial in toks:
        by_surface.setdefault(surface, []).append((start, sentence_initial))
    assert by_surface["Рама"][0][1] is True          # first word of the text
    assert by_surface["Сита"][0][1] is True           # follows ". "
    assert by_surface["Лакшмана"][0][1] is True        # follows "! "
    assert by_surface["вошёл"][0][1] is False
    assert by_surface["дома"][0][1] is False


def test_is_capitalized():
    assert flt.is_capitalized("Дхаумья")
    assert not flt.is_capitalized("дхаумья")


# --------------------------------------------------------------------------- #
# disambiguate.py                                                              #
# --------------------------------------------------------------------------- #
def test_narrow_candidates_plural_rule():
    # rule 1: surface ends in -в -> lemma must be plural (-и/-ы)
    survivors = dis.narrow_candidates("джагудов", {"джагуды", "джагуда"})
    assert survivors == {"джагуды"}


def test_narrow_candidates_singular_rule():
    # rule 7: surface ends in -ом -> lemma must be singular
    survivors = dis.narrow_candidates("лакшманом", {"лакшман", "лакшманы"})
    assert survivors == {"лакшман"}


def test_narrow_candidates_never_empties():
    # a rule that would eliminate every candidate is skipped (thesis rule:
    # "отмести сразу все... не представляется возможным"). Surface ends in
    # -ам (rule 6: lemma must be plural -и/-ы) but neither candidate is.
    survivors = dis.narrow_candidates("брахманам", {"брахман", "раджа"})
    assert survivors == {"брахман", "раджа"}


def test_narrow_candidates_single_candidate_passthrough():
    assert dis.narrow_candidates("яду", {"яду"}) == {"яду"}


def test_merge_plural_singular_duplicates():
    canonical = dis.merge_plural_singular_duplicates(["апсара", "апсары", "гаруда"])
    assert canonical["апсара"] == "апсары"
    assert canonical["апсары"] == "апсары"
    assert canonical["гаруда"] == "гаруда"


# --------------------------------------------------------------------------- #
# annotations.py                                                               #
# --------------------------------------------------------------------------- #
@pytest.fixture()
def tiny_annotations(tmp_path):
    (tmp_path / "phrases.txt").write_text(
        "аджамидха: аджамидха см. видура, юдхиштхира\n"
        "адитья: адитья см. солнце\n",
        encoding="utf-8",
    )
    (tmp_path / "options.txt").write_text(
        "Айравата: змей - Айравата, змей; слон - Айравата, слон\n",
        encoding="utf-8",
    )
    (tmp_path / "rus_index_declined.txt").write_text(
        "великий владыка : ['великий владыка', 'великого владыки', 'великому владыке']\n",
        encoding="utf-8",
    )
    return tmp_path


def test_load_phrases(tiny_annotations):
    phrases = an.load_phrases(str(tiny_annotations / "phrases.txt"))
    assert phrases["аджамидха"] == "аджамидха см. видура, юдхиштхира"
    assert phrases["адитья"] == "адитья см. солнце"


def test_load_options_and_resolve(tiny_annotations):
    options = an.load_options(str(tiny_annotations / "options.txt"))
    assert options["айравата"] == [
        ("змей", "Айравата, змей"),
        ("слон", "Айравата, слон"),
    ]
    resolved = an.resolve_options(
        "айравата", "тут стоял огромный слон айравата у ворот.", options)
    assert resolved == "Айравата, слон"
    assert an.resolve_options("айравата", "ничего не сказано.", options) is None
    assert an.resolve_options("нетлемма", "текст", options) is None


def test_load_rus_index_declined(tiny_annotations):
    rid = an.load_rus_index_declined(str(tiny_annotations / "rus_index_declined.txt"))
    assert rid == [("великий владыка", [
        "великий владыка", "великого владыки", "великому владыке"])]


# --------------------------------------------------------------------------- #
# extract.py -- end-to-end on synthetic fixtures                              #
# --------------------------------------------------------------------------- #
@pytest.fixture()
def fixture_diplom_dir(tmp_path):
    d = tmp_path / "diplom-rubanova"
    d.mkdir()
    (d / lx.SORENSEN_FILE).write_text("Юдхиштхира\nДхаумья\nАгни\n", encoding="utf-8")
    (d / lx.ONEWORD_FILE).write_text("", encoding="utf-8")
    (d / "decl_rules.txt").write_text(TINY_DECL_RULES, encoding="utf-8")
    (d / "foreign_words.txt").write_text("абажур\n", encoding="utf-8")
    (d / "rusforms.txt").write_text("века\n", encoding="utf-8")
    (d / an.PHRASES_FILE).write_text("агни: агни (огонь)\n", encoding="utf-8")
    (d / an.OPTIONS_FILE).write_text("", encoding="utf-8")
    (d / an.APPEND_FILE).write_text("", encoding="utf-8")
    (d / an.RUS_INDEX_FILE).write_text("", encoding="utf-8")
    (d / an.RUS_INDEX_DECLINED_FILE).write_text("", encoding="utf-8")
    return d


@pytest.fixture()
def fixture_jsonl(tmp_path):
    rows = [
        {"group": "w:1.1", "seg": "sa", "lang": "sa", "text": "yudhiṣṭhiraḥ", "deleted": False},
        {"group": "w:1.1", "seg": "ru", "lang": "ru",
         "text": "Юдхиштхира вошёл в лес. Дхаумьи там не было.", "deleted": False},
        {"group": "w:1.2", "seg": "ru", "lang": "ru",
         "text": "Юдхиштхире поклонились брахманы.", "deleted": False},
        {"group": "w:1.3", "seg": "ru", "lang": "ru", "text": "   ", "deleted": False},
        {"group": "w:1.4", "seg": "ru", "lang": "ru", "text": "должно быть пропущено",
         "deleted": True},
    ]
    p = tmp_path / "w.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return p


def test_iter_ru_segments(fixture_jsonl):
    groups = list(iter_ru_segments(str(fixture_jsonl)))
    assert [g for g, _ in groups] == ["w:1.1", "w:1.2"]  # empty + deleted skipped


def test_extract_source_end_to_end(fixture_jsonl, fixture_diplom_dir):
    ctx = ExtractionContext(diplom_dir=str(fixture_diplom_dir))
    result = extract_source(str(fixture_jsonl), ctx=ctx)
    lexicon = result["lexicon"]
    assert "юдхиштхира" in lexicon
    assert lexicon["юдхиштхира"]["total_occurrences"] == 2  # nom + dat, both groups
    assert "юдхиштхире" in lexicon["юдхиштхира"]["forms"]
    assert "дхаумья" in lexicon  # genitive "Дхаумьи" resolved via paradigm
    assert result["stats"]["groups"] == 2

    index = build_name_index(result, ctx)
    entry = next(e for e in index if e["lemma"] == "юдхиштхира")
    assert entry["count"] == 2
    assert entry["ambiguous"] is False


def test_extract_source_capitalization_and_exclusions(fixture_diplom_dir, tmp_path):
    # "века" is in rusforms.txt (exclude list) and not capitalized -> filtered
    # even though it happens to share no lemma here; this test instead checks
    # that a lowercase, non-excluded, non-lemma word never appears at all.
    rows = [{"group": "w:1", "seg": "ru", "lang": "ru",
             "text": "агни горел в лесу агни.", "deleted": False}]
    p = tmp_path / "w2.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    ctx = ExtractionContext(diplom_dir=str(fixture_diplom_dir))
    result = extract_source(str(p), ctx=ctx)
    assert result["lexicon"]["агни"]["total_occurrences"] == 2
    assert "лесу" not in result["lexicon"]


def test_wired_into_nkrya_export(fixture_jsonl, fixture_diplom_dir, tmp_path):
    """H760 deliverable 3: --with-sanskritisms adds the proper-name index to
    the same per-slug export bundle nkrya_export.py already writes."""
    import nkrya_export as nx  # noqa: E402  (same sys.path insert as test_nkrya_export.py)
    from sanskritisms.extract import ExtractionContext

    ctx = ExtractionContext(diplom_dir=str(fixture_diplom_dir))
    out = tmp_path / "out"
    report = nx.export_source(
        "w", str(out),
        jsonl_dir=str(fixture_jsonl.parent),
        meta_dir=str(tmp_path),
        write=True,
        with_sanskritisms=True,
        sanskritisms_ctx=ctx,
    )
    assert "w.sanskritisms_index.json" in report["files"]
    index_path = out / "w" / "w.sanskritisms_index.json"
    assert index_path.exists()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert any(e["lemma"] == "юдхиштхира" for e in index)


def test_discover_ru_sources(tmp_path):
    (tmp_path / "a.jsonl").write_text(
        '{"group":"g","seg":"ru","lang":"ru","text":"x"}\n', encoding="utf-8")
    (tmp_path / "b.jsonl").write_text(
        '{"group":"g","seg":"sa","lang":"sa","text":"y"}\n', encoding="utf-8")
    assert discover_ru_sources(str(tmp_path)) == ["a"]


# --------------------------------------------------------------------------- #
# corpus gates: real tracked curated lists + a real pilot source              #
# --------------------------------------------------------------------------- #
@pytest.mark.corpus
def test_real_lemma_pool_loads():
    pool = lx.load_lemma_pool()
    assert len(pool) > 8000
    assert "юдхиштхира" in pool
    assert "дхритараштра" in pool


@pytest.mark.corpus
def test_real_extraction_finds_known_names():
    jsonl = _CB / "jsonl" / "03_mahabharata-aranyakaparva.jsonl"
    if not jsonl.exists():
        pytest.skip(f"{jsonl} not present")
    ctx = ExtractionContext()
    result = extract_source(str(jsonl), ctx=ctx)
    lexicon = result["lexicon"]
    for name in ("юдхиштхира", "драупади", "агни"):
        assert name in lexicon, name
        assert lexicon[name]["total_occurrences"] > 0
    assert result["stats"]["lemmas"] > 500


@pytest.mark.corpus
def test_real_extraction_overlaps_thesis_ramayana_reference():
    """Rubanova's own final Rāmāyaṇa vol.3 index (Ramayana_names_clean_united.txt,
    380 rubrics -- her §3.3.3 output, kept as a tracked reference/validation
    artifact) should meaningfully overlap this package's independent run over
    the same source (03_ramayana-aranyakanda == kāṇḍa 3 == "vol. 3")."""
    jsonl = _CB / "jsonl" / "03_ramayana-aranyakanda.jsonl"
    ref_path = _REPO / "nkrya-parallel" / "diplom-rubanova" / "Ramayana_names_clean_united.txt"
    if not jsonl.exists() or not ref_path.exists():
        pytest.skip("reference source(s) not present")
    ref_lemmas = set()
    for line in ref_path.read_text(encoding="utf-8").splitlines():
        line = line.strip().lower()
        if not line:
            continue
        head = line.split(",")[0].split(" см.")[0].split(" (")[0].strip()
        if head:
            ref_lemmas.add(head)

    ctx = ExtractionContext()
    result = extract_source(str(jsonl), ctx=ctx)
    found = set(result["lexicon"])
    overlap = ref_lemmas & found
    assert len(overlap) >= 30, (
        f"only {len(overlap)} of {len(ref_lemmas)} reference lemmas overlapped")
