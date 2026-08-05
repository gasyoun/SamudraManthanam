"""H1207 acceptance gates for `ru_rubric_decline.py` -- the in-port
generator that regenerates `rus_index_declined.txt` from `rus_index.txt`
(replacing the un-mirrorable `Index_items_declension.ipynb` +
`index_lone_declined_manual.json` + `pyphrasy` 2024-11 pipeline; see
docs/RUBANOVA_NKRYA_RUBRIC_DECLENSION_STATUS_2024_11.md).

Two layers, following this repo's convention (hermetic by default, real
data behind `-m corpus`):

  * hermetic -- declension rules exercised directly against pymorphy3 (a
    real dependency, but no repo data needed) on a small set of phrases
    covering every structural pattern plus the historically-broken forms
    named in H1207 (три мира, вездесущий) and the homograph-trap
    overrides (гады, дроны, лука, ганги, манасы, паки, балы, знак,
    индра, пасть).
  * corpus -- regenerates from the real tracked `rus_index.txt` and
    checks it against the real committed `rus_index_declined.txt`
    (parity -- any future drift must be a deliberate regeneration, not
    silent staleness) and against the manual gold JSON (the accuracy
    gate: >= the note's own 86.5% paradigm accuracy).
"""

import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_CB = _REPO / "web" / "corpus_builder"
_DIPLOM = _REPO / "nkrya-parallel" / "diplom-rubanova"

sys.path.insert(0, str(_CB))

from sanskritisms import ru_rubric_decline as rd  # noqa: E402


@pytest.fixture(scope="module")
def morph():
    return rd.load_morph()


# --------------------------------------------------------------------------- #
# the two forms named in the handoff's stop condition                        #
# --------------------------------------------------------------------------- #
def test_tri_mira_numeral_agreement_fixed(morph):
    """Old file: 'три мир'/'трёх мира'/... (pymorphy2's default top parse
    for 'мира' re-inflected the wrong lexeme). Correct Russian numeral
    government: 2/3/4 take genitive-singular noun in nom/acc, and
    genitive/dative/instrumental/locative take the PLURAL noun form."""
    d = rd.decline_phrase("три мира", morph)
    assert d["nomn"] == "три мира"
    assert d["gent"] == "трех миров"
    assert d["datv"] == "трем мирам"
    assert d["accs"] == "три мира"
    assert d["ablt"] == "тремя мирами"
    assert d["loct"] == "трех мирах"


def test_vezdesushiy_adjf_preferred_over_noun_tie(morph):
    """Old file: 'вездесущия'/'вездесущий'/... -- pymorphy2/3 ties
    ADJF,masc,sing,nomn against NOUN,neut,plur,gent at the same score and
    the notebook's raw .inflect() picked the noun reading."""
    d = rd.decline_phrase("вездесущий", morph)
    assert d["nomn"] == "вездесущий"
    assert d["gent"] == "вездесущего"
    assert d["datv"] == "вездесущему"
    assert d["ablt"] == "вездесущим"
    assert d["loct"] == "вездесущем"


# --------------------------------------------------------------------------- #
# numeral government -- both classes                                        #
# --------------------------------------------------------------------------- #
def test_numeral_2_4_class_governs_genitive_singular_in_nom_acc(morph):
    d = rd.decline_phrase("восемь чаш", morph)
    # 5+ class: nom/acc noun stays genitive PLURAL (same surface as гент.pl)
    assert d["nomn"] == "восемь чаш"
    assert d["gent"] == "восьми чаш"
    assert d["ablt"] == "восемью чашами"


def test_compound_numeral_declines_both_words(morph):
    d = rd.decline_phrase("тридцать три бога", morph)
    assert d["nomn"] == "тридцать три бога"
    assert d["gent"] == "тридцати трех богов"
    assert d["datv"] == "тридцати трем богам"
    assert d["ablt"] == "тридцатью тремя богами"


def test_irregular_numeral_tridesyat(morph):
    """'тридесять' (archaic 'thirty') is not in pymorphy3 at all (it
    misparses it as an infinitive verb) -- hand-supplied paradigm."""
    d = rd.decline_phrase("тридесять богов", morph)
    assert d["nomn"] == "тридесять богов"
    assert d["gent"] == "тридесяти богов"
    assert d["ablt"] == "тридесятью богами"


# --------------------------------------------------------------------------- #
# fixed genitive/prepositional tails vs. agreeing heads                      #
# --------------------------------------------------------------------------- #
def test_genitive_tail_stays_fixed(morph):
    d = rd.decline_phrase("сын дхармы", morph)
    for case in rd.CASES:
        assert d[case].endswith("дхармы")
    assert d["nomn"] == "сын дхармы"
    assert d["gent"] == "сына дхармы"


def test_adjective_noun_agreement_declines_together(morph):
    d = rd.decline_phrase("великий владыка", morph)
    assert d["nomn"] == "великий владыка"
    assert d["gent"] == "великого владыки"
    assert d["datv"] == "великому владыке"


def test_prepositional_complement_stays_fixed(morph):
    """'не из чрева рожденный': only the trailing participle (the head)
    inflects; the preposition + its genitive object stay put."""
    d = rd.decline_phrase("не из чрева рожденный", morph)
    assert d["nomn"] == "не из чрева рожденный"
    assert d["gent"] == "не из чрева рожденного"
    assert all(f.startswith("не из чрева ") for f in d.values())


def test_hyphenated_compound_both_sides_decline(morph):
    d = rd.decline_phrase("брахманы-мудрецы", morph)
    assert d["nomn"] == "брахманы-мудрецы"
    assert d["gent"] == "брахманов-мудрецов"


def test_comma_joined_coordinate_list_declines_in_unison(morph):
    d = rd.decline_phrase("долг, польза, любовь", morph)
    assert d["nomn"] == "долг, польза, любовь"
    assert d["gent"] == "долга, пользы, любви"
    assert d["ablt"] == "долгом, пользой, любовью"


def test_tot_relative_clause_only_head_inflects(morph):
    """The old file left every 'тот, ...' rubric with an EMPTY form list
    (unhandled by the notebook's curated classes)."""
    d = rd.decline_phrase("тот, чье знамя – бык", morph)
    assert d["nomn"] == "тот, чье знамя – бык"
    assert d["gent"] == "того, чье знамя – бык"
    assert d["datv"] == "тому, чье знамя – бык"
    # everything after "тот" is frozen even though "бык" is itself
    # nominative (an internal clause-subject, not agreeing with "тот")
    assert all(f.endswith(", чье знамя – бык") for f in d.values())


# --------------------------------------------------------------------------- #
# curated homograph-trap overrides (H1207 gold-testing discoveries)          #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "phrase,frozen_tail",
    [
        ("брат гады", "гады"),  # "Гада" (demon) gen.sg, not "гад" pl.nom
        ("владетель лука", "лука"),  # "лук" (bow) gen.sg, not the name "Лука"
        ("врата ганги", "ганги"),  # "Ганга" gen.sg, not "ганг" pl.nom
        ("врата манасы", "манасы"),  # "Манаса" gen.sg, not "манас" pl.nom
        ("губитель паки", "паки"),  # "Пака" (demon) gen.sg, not ADVB/pl.nom
        ("сокрушитель балы", "балы"),  # "Бала" (demon) gen.sg, not "бал" pl.nom
        ("несущий знак", "знак"),  # acc.-inanimate == nom. surface trap
        ("сын дроны", "дроны"),  # "Дрона" gen.sg, not the loanword "дрон"
    ],
)
def test_homograph_trap_tail_stays_fixed(morph, phrase, frozen_tail):
    d = rd.decline_phrase(phrase, morph)
    for case in rd.CASES:
        assert d[case].endswith(frozen_tail), (phrase, case, d[case])


def test_indra_force_declined_as_agreeing_head(morph):
    """pymorphy tags 'индра' Fixd (indeclinable) with no dictionary entry
    -- but Sanskrit deity names in -а are routinely declined in Russian
    scholarship, and here it's the agreeing head noun of 'великий индра',
    not a genitive tail."""
    d = rd.decline_phrase("великий индра", morph)
    assert d["nomn"] == "великий индра"
    assert d["gent"] == "великого индры"
    assert d["ablt"] == "великим индрой"


def test_past_force_declined_not_the_infn_homograph(morph):
    """'пасть' (mouth/jaw) loses the parse tie-break to the unrelated
    infinitive homograph 'пасть' ('to fall') at 0.5 vs 0.25."""
    d = rd.decline_phrase("пасть кобылицы", morph)
    assert d["nomn"] == "пасть кобылицы"
    assert d["gent"] == "пасти кобылицы"
    assert d["ablt"] == "пастью кобылицы"


def test_compound_adjective_unknown_to_pymorphy_still_declines(morph):
    """'десятиликий' isn't in OpenCorpora; pymorphy's guesser ranks a
    spurious NOUN reading above the correct ADJF one by score, not just
    a tie -- position-0 heads override that unconditionally."""
    d = rd.decline_phrase("десятиликий", morph)
    assert d["nomn"] == "десятиликий"
    assert d["gent"] == "десятиликого"
    assert d["datv"] == "десятиликому"


# --------------------------------------------------------------------------- #
# generate/format/write round trip                                          #
# --------------------------------------------------------------------------- #
def test_format_line_matches_committed_file_shape():
    line = rd.format_line(
        "владыка", ["владыка", "владыки", "владыке", "владыку", "владыкой", "владыке"]
    )
    assert line == (
        "владыка : ['владыка', 'владыки', 'владыке', 'владыку', "
        "'владыкой', 'владыке']"
    )


def test_generate_declined_index_hermetic(tmp_path, morph):
    rus_index = tmp_path / "rus_index.txt"
    rus_index.write_text("владыка\nсын дхармы\n", encoding="utf-8")
    entries = rd.generate_declined_index(str(rus_index), morph=morph)
    assert entries == [
        (
            "владыка",
            ["владыка", "владыки", "владыке", "владыку", "владыкой", "владыке"],
        ),
        (
            "сын дхармы",
            [
                "сын дхармы",
                "сына дхармы",
                "сыну дхармы",
                "сына дхармы",
                "сыном дхармы",
                "сыне дхармы",
            ],
        ),
    ]
    out = tmp_path / "out.txt"
    rd.write_declined_index(entries, str(out))
    written = out.read_text(encoding="utf-8")
    assert written.splitlines()[0] == rd.format_line(*entries[0])
    assert "\r\n" in out.read_bytes().decode("utf-8")


def test_score_against_gold():
    entries = [
        ("а", ["а1", "а2", "а3", "а4", "а5", "а6"]),
        ("б", ["б1", "б2", "б3", "б4", "б5", "wrong"]),
    ]
    gold = {
        "а": ["а1", "а2", "а3", "а4", "а5", "а6"],
        "б": ["б1", "б2", "б3", "б4", "б5", "б6"],
    }
    report = rd.score_against_gold(entries, gold)
    assert report["total_paradigms"] == 2
    assert report["correct_paradigms"] == 1
    assert report["total_forms"] == 12
    assert report["correct_forms"] == 11
    assert len(report["mismatches"]) == 1


def test_yo_is_stripped(morph):
    d = rd.decline_phrase("быкознаменный", morph)
    assert "ё" not in d["gent"]
    assert d["gent"] == "быкознаменного"


# --------------------------------------------------------------------------- #
# corpus gates: the real tracked rus_index.txt + committed declined file     #
# --------------------------------------------------------------------------- #
@pytest.mark.corpus
def test_real_rus_index_regenerates_identically_to_committed_file():
    """Parity check (H1207 deliverable): the committed
    rus_index_declined.txt IS the generator's output over the committed
    rus_index.txt -- any future edit to either must regenerate the other,
    never hand-drift."""
    rus_index_path = _DIPLOM / "rus_index.txt"
    declined_path = _DIPLOM / "rus_index_declined.txt"
    if not rus_index_path.exists() or not declined_path.exists():
        pytest.skip("diplom-rubanova data not present")
    morph = rd.load_morph()
    entries = rd.generate_declined_index(str(rus_index_path), morph=morph)

    # Compared line-ending-agnostically, which does not loosen the gate. The
    # parity property is that the committed file IS the generator's output — a
    # claim about content. Line endings are git's to decide: the org-wide
    # `.gitattributes` LF policy sets `* text=auto eol=lf`, so this file now
    # materialises with LF on every platform and the hardcoded `\r\n` could
    # never match again. It had been failing since that policy landed, unseen,
    # because `-m corpus` did not run in CI until H1927 added the corpus gate.
    def _lf(text: str) -> str:
        return text.replace("\r\n", "\n")

    regenerated = _lf("\n".join(rd.format_line(b, f) for b, f in entries) + "\n")
    committed = _lf(declined_path.read_text(encoding="utf-8"))
    assert regenerated == committed


@pytest.mark.corpus
def test_real_rus_index_meets_accuracy_gate():
    """H1207 stop condition: paradigm accuracy against the manual gold
    >= the note's own 86.5%."""
    rus_index_path = _DIPLOM / "rus_index.txt"
    gold_path = _DIPLOM / "rus_index_declined_manual_gold.json"
    if not rus_index_path.exists() or not gold_path.exists():
        pytest.skip("diplom-rubanova data not present")
    morph = rd.load_morph()
    entries = rd.generate_declined_index(str(rus_index_path), morph=morph)
    gold_raw = json.loads(gold_path.read_text(encoding="utf-8"))
    gold_raw.pop("_comment", None)
    report = rd.score_against_gold(entries, gold_raw)
    assert report["paradigm_accuracy"] >= 0.865, report["mismatches"]
