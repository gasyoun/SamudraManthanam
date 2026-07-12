r"""Lemma pool + declension-class rules for the sanskritism stemmer (ВКР §3.3.1).

Two tracked input files (`nkrya-parallel/diplom-rubanova/`) supply the lemma
pool:

  * `9460-osnov-sanskritskikh-slov.txt` -- Sørensen's ~9,460 Mahābhārata
    proper names (category 1+4 in the thesis's санскритизм taxonomy: people,
    places, ethnonyms).
  * `3_INDEX_oneword.txt` -- single-word items curated from the printed MBh
    vol. 3 index; supplements Sørensen with the thesis's category 2+3
    санскритизмы (plants/animals, objects/terms) that a proper-name list
    does not cover.

`decl_rules.txt` encodes the three Russian declension classes the thesis
hand-derived for Sanskritisms (consonant stem, -а stem, -я stem); words
ending in -и/-у/-ю are indeclinable per the thesis (§2.4).
"""
import functools
import os

from ._paths import diplom_path

SORENSEN_FILE = '9460-osnov-sanskritskikh-slov.txt'
ONEWORD_FILE = '3_INDEX_oneword.txt'
DECL_RULES_FILE = 'decl_rules.txt'

INDECLINABLE_ENDINGS = ('и', 'у', 'ю')


def _read_lines(path):
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                yield line


def load_sorensen_names(diplom_dir=None):
    """Sørensen's proper-name list, lowercased. Source: category 1+4."""
    path = diplom_path(SORENSEN_FILE) if diplom_dir is None else \
        os.path.join(diplom_dir, SORENSEN_FILE)
    return {line.lower() for line in _read_lines(path)}


def load_oneword_terms(diplom_dir=None):
    """Single-word санскритизмы curated from the printed MBh vol.3 index.
    Source: category 2+3 (plants/animals, objects/terms)."""
    path = diplom_path(ONEWORD_FILE) if diplom_dir is None else \
        os.path.join(diplom_dir, ONEWORD_FILE)
    return {line.lower() for line in _read_lines(path)}


def load_lemma_pool(diplom_dir=None):
    """Union of both curated lemma sources, lowercased, deduplicated.
    Returns {lemma: frozenset(source_tags)}."""
    pool = {}
    for lemma in load_sorensen_names(diplom_dir):
        pool.setdefault(lemma, set()).add('sorensen')
    for lemma in load_oneword_terms(diplom_dir):
        pool.setdefault(lemma, set()).add('index3')
    return {lemma: frozenset(tags) for lemma, tags in pool.items()}


def parse_decl_rules(path=None):
    """Parse decl_rules.txt into {class_key: {case: [suffixes]}}.

    class_key is one of '_' (consonant stem), 'а', 'я'. Suffix '_' means the
    empty string (thesis: nominative of a consonant-stem lemma == the lemma
    itself, no ending added).
    """
    path = diplom_path(DECL_RULES_FILE) if path is None else path
    rules = {}
    current = None
    with open(path, encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                current = None
                continue
            if current is None:
                current = line
                rules[current] = {}
                continue
            case, _, suffixes = line.partition(' ')
            forms = [s.strip() for s in suffixes.split(',')]
            forms = ['' if s == '_' else s for s in forms]
            rules[current][case] = forms
    return rules


def declension_class(lemma):
    """Classify a lowercased lemma into one of the three thesis classes, or
    None if it is indeclinable (ends in -и/-у/-ю, §2.4)."""
    if not lemma:
        return '_'
    last = lemma[-1]
    if last in INDECLINABLE_ENDINGS:
        return None
    if last in ('а', 'я'):
        return last
    return '_'


@functools.lru_cache(maxsize=1)
def default_decl_rules():
    return _freeze(parse_decl_rules())


def _freeze(rules):
    return {k: {kk: tuple(vv) for kk, vv in v.items()} for k, v in rules.items()}
