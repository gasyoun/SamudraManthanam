"""The 6-condition санскритизм stemmer — ported from ВКР §3.3.1.

Faithful to the thesis's worked examples (see SPEC.md §2.3):
  вигана -> виган (condition 1)   Ахаром -> Ахар (condition 2)
  джагудов -> джагуды (condition 3)   Ашвинами -> Ашвины (condition 4)
  магхой -> магха (condition 5)   сурашатрах -> сурашатры (condition 6)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .lexicons import LemmaPool, RussianDictionary

RUSSIAN_VOWELS = set("аеёиоуыэюя")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+")
WORD_RE = re.compile(r"[Ёёа-яА-Я]+(?:-[Ёёа-яА-Я]+)?")


def generate_candidate_stems(word_lower: str) -> list[tuple[str, int]]:
    """Six conditions (thesis §3.3.1). Returns (stem, condition_id) pairs."""
    n = len(word_lower)
    out: list[tuple[str, int]] = [(word_lower, 1)]
    if n > 1:
        out.append((word_lower[:-1], 1))
    if n >= 3 and word_lower[-1] == "м" and word_lower[-2] in RUSSIAN_VOWELS:
        out.append((word_lower[:-2], 2))
    if n >= 3 and word_lower[-1] == "в" and word_lower[-2] in RUSSIAN_VOWELS:
        out.append((word_lower[:-2], 3))
    if n >= 4 and word_lower[-2:] == "ми" and word_lower[-3] in RUSSIAN_VOWELS:
        out.append((word_lower[:-3], 4))
    if n >= 3 and word_lower[-1] == "й" and word_lower[-2] in RUSSIAN_VOWELS:
        out.append((word_lower[:-2], 5))
    if n >= 3 and word_lower[-1] == "х" and word_lower[-2] in RUSSIAN_VOWELS:
        out.append((word_lower[:-2], 6))
    return out


def find_candidate_lemmas(word_lower: str, pool: LemmaPool) -> set[str]:
    candidates: set[str] = set()
    if word_lower in pool.indeclinable:
        candidates.add(word_lower)
    for stem, _rule_id in generate_candidate_stems(word_lower):
        if stem in pool.stem_index:
            candidates |= pool.stem_index[stem]
    return candidates


@dataclass
class Token:
    surface: str
    sentence_initial: bool


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    for sentence in SENTENCE_SPLIT_RE.split(text):
        for i, m in enumerate(WORD_RE.finditer(sentence)):
            tokens.append(Token(surface=m.group(0), sentence_initial=(i == 0)))
    return tokens


@dataclass
class Detection:
    surface: str
    lemma_candidates: set[str]
    capitalization_rescued: bool


def detect(
    text: str,
    pool: LemmaPool,
    dictionary: RussianDictionary,
    foreign_words: frozenset[str],
) -> list[Detection]:
    """Stage 2 (six conditions) + stage 3/4 (КРС filter) + stage 5
    (capitalization rescue) of the thesis's final-version algorithm."""
    detections: list[Detection] = []
    for token in tokenize(text):
        word_lower = token.surface.lower()
        if len(word_lower) < 2 or dictionary.is_grammatical_word(word_lower):
            continue
        candidates = find_candidate_lemmas(word_lower, pool)
        if not candidates:
            continue

        known_russian = dictionary.is_known(word_lower) and word_lower not in foreign_words
        rescued = False
        if known_russian:
            is_capitalized = token.surface[:1].isupper()
            if is_capitalized and not token.sentence_initial:
                rescued = True
            else:
                continue  # dropped by the КРС filter, not rescued

        detections.append(
            Detection(surface=token.surface, lemma_candidates=candidates, capitalization_rescued=rescued)
        )
    return detections
