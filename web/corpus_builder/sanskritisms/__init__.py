"""H760 -- sanskritism extraction + proper-name index, corpus-wide.

Ports the ВКР (Е. Рубанова, "Полуавтоматическая морфологическая разметка
параллельного русско-санскритского корпуса") sanskrit-stemmer method from
notebooks to a documented, tested package. See README.md for the algorithm
and its scope relative to the thesis.
"""
from .extract import extract_source, discover_ru_sources
from .lexicon import load_lemma_pool
from .paradigms import build_reverse_index, generate_forms

__all__ = [
    "extract_source",
    "discover_ru_sources",
    "load_lemma_pool",
    "build_reverse_index",
    "generate_forms",
]
