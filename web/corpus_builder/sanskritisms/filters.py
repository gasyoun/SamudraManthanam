r"""False-positive filters (ВКР §3.3.1 stages 2-3) + tokenizer.

  * `foreign_words.txt` -- 14,712 non-Sanskrit loanwords (Абрамович 1986);
    excludes matches that are actually ordinary foreign borrowings
    (French/German/etc.), not Sanskritisms.
  * `rusforms.txt` -- the thesis's hand-built exception list of Russian
    pronouns/adverbs/verb-forms that were discovered to collide with a
    generated Sanskritism surface form (§3.3.1 "список исключений").

The thesis's third filter -- a full Russian word corpus (КРС, ~3M forms
from OpenCorpora, `dict.opcorpora.txt`, 271 MB) -- is reproduced here via
**pymorphy3** (`is_russian_word`): pymorphy3 ships the *same* OpenCorpora
dictionary as `pymorphy-dicts-ru`, so `word_is_known(surface)` answers
exactly the "is this a real Russian wordform?" question Rubanova's raw
`rus_words` set answered -- without the 271 MB dump, and portable to a
fresh clone. This is the primary defence against the Кали→кал class of
false positives (a lowercased common word colliding with a Sanskritism's
surface form). It is applied only to non-capitalized tokens; a capitalized,
non-sentence-initial token is still trusted as a candidate proper name and
exempted (stage 5). If pymorphy3 is not installed the filter degrades to
the old two-list approximation (H905).
"""
import re

from ._paths import diplom_path

FOREIGN_WORDS_FILE = 'foreign_words.txt'
EXCLUDE_FORMS_FILE = 'rusforms.txt'

# Sanskritisms that ALSO happen to be known Russian wordforms. Rubanova
# explicitly REMOVED these from her opcorpora `rus_words` set
# (sans_stemmer.ipynb `open_files()`) so the corpus filter would not drop
# them; kept verbatim so `is_russian_word` reproduces her behaviour, not a
# stricter one. See docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md §4.
RUS_WORD_FILTER_EXCEPTIONS = frozenset({
    'даму', 'дама', 'кишку', 'пилу', 'руру', 'турья', 'турье',
    'кшатрия', 'кшатрии',
})

_SENTENCE_END = re.compile(r'[.!?…»"]$')
_TOKEN_RE = re.compile(r'[а-яА-ЯёЁ]+(?:-[а-яА-ЯёЁ]+)*')


def _read_set(path):
    with open(path, encoding='utf-8') as f:
        return {line.strip().lower() for line in f if line.strip()}


def load_foreign_words(diplom_dir=None):
    import os
    path = diplom_path(FOREIGN_WORDS_FILE) if diplom_dir is None else \
        os.path.join(diplom_dir, FOREIGN_WORDS_FILE)
    return _read_set(path)


def load_exclude_forms(diplom_dir=None):
    import os
    path = diplom_path(EXCLUDE_FORMS_FILE) if diplom_dir is None else \
        os.path.join(diplom_dir, EXCLUDE_FORMS_FILE)
    return _read_set(path)


def tokenize(text):
    """Yield (surface, start, sentence_initial) for every Cyrillic token.

    sentence_initial is True for the first token of `text` and for any
    token immediately following [.!?…»"] (thesis §3.3.1 stage 5: a
    capitalized token is trusted as a proper name only when it is NOT at
    the start of a sentence, since sentence-initial capitals are
    uninformative).
    """
    prev_end = 0
    seen_any = False
    for m in _TOKEN_RE.finditer(text):
        between = text[prev_end:m.start()]
        sentence_initial = (not seen_any) or bool(_SENTENCE_END.search(between.rstrip()))
        yield m.group(0), m.start(), sentence_initial
        prev_end = m.end()
        seen_any = True


def is_capitalized(token):
    return bool(token) and token[0].isupper()


# --- Russian-word filter (opcorpora rus_words, via pymorphy3) ------------- #
# Lazy singleton: importing/instantiating pymorphy3 is ~0.3 s and loads the
# OpenCorpora dictionary once. `False` sentinel means "tried and unavailable"
# so we only warn once and then behave as the pre-H905 approximation.
_MORPH = None


def _morph():
    global _MORPH
    if _MORPH is None:
        try:
            import pymorphy3
            _MORPH = pymorphy3.MorphAnalyzer()
        except Exception as exc:  # pragma: no cover - env-dependent
            import sys
            print('sanskritisms.filters: pymorphy3 unavailable (%s); '
                  'is_russian_word filter disabled — Кали→кал class of false '
                  'positives will not be caught (install pymorphy3).' % exc,
                  file=sys.stderr)
            _MORPH = False
    return _MORPH


def is_russian_word(surface_lower):
    """True if `surface_lower` is a known Russian wordform in the OpenCorpora
    dictionary (pymorphy3 — the same КРС/opcorpora data Rubanova's
    `dict.opcorpora.txt` rus_words filter used). Reproduces the thesis's
    primary false-positive filter WITHOUT the 271 MB dump.

    Curated Sanskritism collisions (`RUS_WORD_FILTER_EXCEPTIONS`) are never
    reported as Russian, matching Rubanova's own removals. Returns False when
    pymorphy3 is unavailable, so callers fall back to the two-list
    approximation rather than crashing.
    """
    if surface_lower in RUS_WORD_FILTER_EXCEPTIONS:
        return False
    m = _morph()
    if not m:
        return False
    return m.word_is_known(surface_lower)
