"""H919 acceptance gates for the санскритизм layer (web/corpus_builder/sanskritisms).

Two layers, following this repo's convention (hermetic by default, real-data
behind ``-m corpus``):

  * hermetic -- the stemmer's stage-2 conditions + stage-3 disambiguation
                rules on synthetic word lists; runs everywhere.
  * corpus   -- precision/recall against the two gold indices already
                tracked in nkrya-parallel/diplom-rubanova/ (Rubanova's own
                finished MBh book-3 and Rāmāyaṇa book-3 санскритизм
                indexes); needs web/corpus_builder/jsonl/*, run with
                ``pytest -m corpus``.

Per SPEC.md §4/§2.5, the gold-comparison tests assert a floor, not exact
thesis-figure reproduction -- the deeppavlov-tier residual disambiguation
is intentionally not ported.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_DIPLOM = _REPO / "nkrya-parallel" / "diplom-rubanova"

sys.path.insert(0, str(_REPO))

from web.corpus_builder.sanskritisms import disambiguate, stemmer  # noqa: E402
from web.corpus_builder.sanskritisms.build_index import discover_verse_sources, run_source  # noqa: E402
from web.corpus_builder.sanskritisms.lexicons import (  # noqa: E402
    LemmaPool,
    RussianDictionary,
    build_sorensen_pool,
    load_foreign_words,
)


# ---------------------------------------------------------------------------
# hermetic: stage-2 six conditions (thesis §3.3.1 worked examples)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "surface,expected_stem,condition",
    [
        ("вигана", "виган", 1),
        ("ахаром", "ахар", 2),
        ("джагудов", "джагуд", 3),
        ("ашвинами", "ашвин", 4),
        ("магхой", "магх", 5),
        ("сурашатрах", "сурашатр", 6),
    ],
)
def test_generate_candidate_stems_worked_examples(surface, expected_stem, condition):
    stems = {s for s, _cond in stemmer.generate_candidate_stems(surface)}
    assert expected_stem in stems


def _pool(*lemmas: str) -> LemmaPool:
    pool = LemmaPool()
    for lemma in lemmas:
        pool.add(lemma)
    return pool


def test_find_candidate_lemmas_matches_condition_1():
    pool = _pool("виган")
    assert stemmer.find_candidate_lemmas("вигана", pool) == {"виган"}


def test_find_candidate_lemmas_matches_condition_3():
    pool = _pool("джагуды")
    assert "джагуды" in stemmer.find_candidate_lemmas("джагудов", pool)


def test_find_candidate_lemmas_indeclinable_exact_match_only():
    pool = _pool("агни")  # ends in -и -> indeclinable pool
    assert stemmer.find_candidate_lemmas("агни", pool) == {"агни"}
    assert stemmer.find_candidate_lemmas("агния", pool) == set()  # no case-stripping for indeclinables


# ---------------------------------------------------------------------------
# hermetic: КРС substitution (pymorphy3) + capitalization rescue
# ---------------------------------------------------------------------------


def test_russian_dictionary_matches_thesis_loanword_collision_examples():
    d = RussianDictionary()
    for word in ("сома", "яма", "брахман"):
        assert d.is_known(word), f"{word} expected known (already-absorbed loanword, thesis §3.3.1)"
    assert not d.is_known("ракшасов")


def test_russian_dictionary_grammatical_word_filter():
    d = RussianDictionary()
    assert d.is_grammatical_word("и")
    assert d.is_grammatical_word("его")
    assert not d.is_grammatical_word("ракшас")


def test_capitalization_rescues_loanword_collision():
    pool = _pool("яма")  # a Sanskrit name homonymous with a Russian dict word (not in foreign_words.txt)
    d = RussianDictionary()
    fw = load_foreign_words()

    # sentence-initial: no rescue, dropped by the КРС filter
    kept_initial = stemmer.detect("Яма судит мертвых.", pool, d, fw)
    assert not any(x.surface == "Яма" for x in kept_initial)

    # mid-sentence capitalized: rescued
    kept_mid = stemmer.detect("Он видел, как Яма судит мертвых.", pool, d, fw)
    rescued = [x for x in kept_mid if x.surface == "Яма"]
    assert rescued and rescued[0].capitalization_rescued


# ---------------------------------------------------------------------------
# hermetic: stage-3 disambiguation (thesis §3.3.3, 9 suffix rules)
# ---------------------------------------------------------------------------


def test_suffix_rule_1_ov_requires_plural():
    refined = disambiguate.refine_by_suffix_rules("ракшасов", {"ракшаси", "ракшас", "ракшаса", "ракшасы"})
    assert refined == {"ракшасы"} or refined <= {"ракшаси", "ракшасы"}


def test_suffix_rule_7_om_requires_singular():
    refined = disambiguate.refine_by_suffix_rules("лакшманом", {"лакшман", "лакшмана", "лакшманы"})
    assert "лакшманы" not in refined
    assert refined == {"лакшман", "лакшмана"}


def test_merge_plural_singular_prefers_plural():
    entries = [
        disambiguate.LemmaEntry("апсара", {"апсара"}, 3, 0),
        disambiguate.LemmaEntry("апсары", {"апсары"}, 5, 0),
    ]
    merged = disambiguate.merge_plural_singular(entries)
    assert len(merged) == 1
    assert merged[0].lemma == "апсары"
    assert merged[0].count == 8


# ---------------------------------------------------------------------------
# corpus: precision/recall against the two gold indices already tracked
# ---------------------------------------------------------------------------


def _load_wordlist_gold(path: Path) -> set[str]:
    words = set()
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            w = line.strip().lower()
            if w:
                words.add(w)
    return words


def _load_annotated_index_gold(path: Path) -> set[str]:
    """3_INDEX/Ramayana_names_clean_united rubrics: bare lemma is the text
    before the first '(', ' см.', or ',' — multi-word phrase rubrics are
    out of scope for this port's bare-lemma matching (SPEC.md §2.5)."""
    words = set()
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip().lower().strip('«»"')
            if not line:
                continue
            bare = re.split(r"\s*\(|\s+см\.|,", line)[0].strip()
            if bare and re.fullmatch(r"[а-яё-]+", bare):
                words.add(bare)
    return words


@pytest.fixture(scope="module")
def sanskritisms_engine():
    return build_sorensen_pool(), RussianDictionary(), load_foreign_words()


@pytest.mark.corpus
def test_mbh3_gold_precision_recall_floor(sanskritisms_engine):
    pool, dictionary, foreign_words = sanskritisms_engine
    result = run_source("03_mahabharata-aranyakaparva", pool, dictionary, foreign_words)
    predicted = {e.lemma for e in result["entries"] if not e.needs_review}
    gold = _load_wordlist_gold(_DIPLOM / "3_INDEX_oneword.txt")

    inter = predicted & gold
    recall = len(inter) / len(gold)
    precision = len(inter) / max(1, len(predicted))
    print(f"\nMBh-3: precision={precision:.3f} recall={recall:.3f} (predicted={len(predicted)}, gold={len(gold)})")

    assert recall >= 0.55, f"recall floor breached: {recall:.3f}"
    assert precision >= 0.45, f"precision floor breached: {precision:.3f}"


@pytest.mark.corpus
def test_ramayana3_gold_precision_recall_floor(sanskritisms_engine):
    pool, dictionary, foreign_words = sanskritisms_engine
    result = run_source("03_ramayana-aranyakanda", pool, dictionary, foreign_words)
    predicted = {e.lemma for e in result["entries"] if not e.needs_review}
    gold = _load_annotated_index_gold(_DIPLOM / "Ramayana_names_clean_united.txt")

    inter = predicted & gold
    recall = len(inter) / len(gold)
    precision = len(inter) / max(1, len(predicted))
    print(f"\nRam-3: precision={precision:.3f} recall={recall:.3f} (predicted={len(predicted)}, gold={len(gold)})")

    assert recall >= 0.40, f"recall floor breached: {recall:.3f}"
    assert precision >= 0.35, f"precision floor breached: {precision:.3f}"


@pytest.mark.corpus
def test_discover_verse_sources_matches_roadmap_figure():
    have, missing = discover_verse_sources()
    # SPEC.md §5: 123 verse sources currently have canonical JSONL (matches
    # the roadmap's own figure); the DBhP skandhas (H558) are the documented
    # gap. If this count drifts, it should drift because new JSONL landed
    # (grow), not silently shrink.
    assert len(have) >= 123, f"expected >=123 verse sources with JSONL, found {len(have)}: missing={missing}"
