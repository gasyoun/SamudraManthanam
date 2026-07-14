"""Lexicon loading for the sanskritisms stemmer — see SPEC.md §2.1-2.2.

Loads the Cyrillic Sanskrit-lemma pool (Sørensen 9460-list), the foreign-words
carve-out, the Russian epithet lists, and wraps pymorphy3 as the КРС
(corpus-of-Russian-words) membership check the ВКР's own 271 MB OpenCorpora
dump is substituted with (that dump is absent from disk in this environment).
"""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from pathlib import Path

VOWEL_ENDINGS = ("а", "я", "ы")
INDECLINABLE_ENDINGS = ("и", "у", "ю")

DIPLOM_DIR = Path(__file__).resolve().parents[3] / "nkrya-parallel" / "diplom-rubanova"

SORENSEN_PATH = DIPLOM_DIR / "9460-osnov-sanskritskikh-slov.txt"
FOREIGN_WORDS_PATH = DIPLOM_DIR / "foreign_words.txt"
RUS_INDEX_DECLINED_PATH = DIPLOM_DIR / "rus_index_declined.txt"

# Thesis §3.3.1: pronouns/adverbs the suffix rules repeatedly mis-caught.
# Kept as a small seed list; the *primary* filter is POS-based (see
# `is_grammatical_word` below) which generalizes better than a hand list.
SEED_EXCLUSIONS = {
    "тот", "та", "то", "те", "меня", "нас", "наш", "наша", "наше", "наши",
    "ней", "нее", "неё", "нею", "него", "них", "ним", "ними", "нём",
    "там", "том", "тут", "чем", "эти", "это", "этот", "эта", "сами", "сам",
    "и", "их", "им", "к", "в", "на", "с", "у", "о", "об", "от", "до", "по",
}


@dataclass
class LemmaPool:
    """Partitions a Cyrillic lemma list into the three morphological classes
    the ВКР's stemmer conditions operate on (thesis §3.3.1)."""

    indeclinable: set[str] = field(default_factory=set)
    stem_index: dict[str, set[str]] = field(default_factory=dict)
    original_case: dict[str, str] = field(default_factory=dict)

    def add(self, lemma: str) -> None:
        lemma = lemma.strip()
        if not lemma or " " in lemma or not lemma.isalpha():
            return
        low = lemma.lower()
        self.original_case.setdefault(low, lemma)
        if low.endswith(INDECLINABLE_ENDINGS):
            # -и/-у/-ю is genuinely ambiguous (thesis §3.3.1/§3.3.3): some are
            # true indeclinables (гаятри, ваю), others are -и nominative
            # plurals (упанги, раматхи) that DO decline. Index both ways.
            self.indeclinable.add(low)
            self.stem_index.setdefault(low[:-1], set()).add(low)
            return
        stem = low[:-1] if low.endswith(VOWEL_ENDINGS) else low
        self.stem_index.setdefault(stem, set()).add(low)

    def merge(self, other: "LemmaPool") -> None:
        self.indeclinable |= other.indeclinable
        for stem, lemmas in other.stem_index.items():
            self.stem_index.setdefault(stem, set()).update(lemmas)
        for low, orig in other.original_case.items():
            self.original_case.setdefault(low, orig)


def load_word_list(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def build_sorensen_pool(path: Path = SORENSEN_PATH) -> LemmaPool:
    pool = LemmaPool()
    for word in load_word_list(path):
        pool.add(word)
    return pool


@functools.lru_cache(maxsize=1)
def load_foreign_words(path: Path = FOREIGN_WORDS_PATH) -> frozenset[str]:
    return frozenset(w.lower() for w in load_word_list(path))


@functools.lru_cache(maxsize=1)
def load_rus_epithet_forms(path: Path = RUS_INDEX_DECLINED_PATH) -> dict[str, str]:
    """`lemma : [forms...]` file -> {form: lemma} reverse index."""
    import ast

    forms_to_lemma: dict[str, str] = {}
    if not path.exists():
        return forms_to_lemma
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or " : " not in line:
                continue
            lemma, raw_forms = line.split(" : ", 1)
            lemma = lemma.strip()
            try:
                forms = ast.literal_eval(raw_forms.strip())
            except (ValueError, SyntaxError):
                continue
            for form in forms:
                forms_to_lemma.setdefault(form.lower(), lemma)
            forms_to_lemma.setdefault(lemma.lower(), lemma)
    return forms_to_lemma


class RussianDictionary:
    """КРС substitute (SPEC.md §2.2): pymorphy3 + pymorphy3-dicts-ru instead
    of the ВКР's missing 271 MB OpenCorpora dump."""

    _GRAMMATICAL_POS = {"NPRO", "PREP", "CONJ", "PRCL", "INTJ"}

    def __init__(self) -> None:
        import pymorphy3

        self._morph = pymorphy3.MorphAnalyzer()

    @functools.lru_cache(maxsize=200_000)
    def is_known(self, word: str) -> bool:
        return self._morph.word_is_known(word.lower())

    @functools.lru_cache(maxsize=200_000)
    def is_grammatical_word(self, word: str) -> bool:
        """True for pronouns/prepositions/conjunctions/particles/interjections
        — a POS-based generalization of the thesis's hand-picked exclusion
        list (SEED_EXCLUSIONS), which is kept as a fallback for words
        pymorphy3 mis-tags."""
        low = word.lower()
        if low in SEED_EXCLUSIONS:
            return True
        parses = self._morph.parse(low)
        if not parses:
            return False
        return parses[0].tag.POS in self._GRAMMATICAL_POS
