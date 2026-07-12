r"""False-positive filters (ВКР §3.3.1 stages 2-3) + tokenizer.

  * `foreign_words.txt` -- 14,712 non-Sanskrit loanwords (Абрамович 1986);
    excludes matches that are actually ordinary foreign borrowings
    (French/German/etc.), not Sanskritisms.
  * `rusforms.txt` -- the thesis's hand-built exception list of Russian
    pronouns/adverbs/verb-forms that were discovered to collide with a
    generated Sanskritism surface form (§3.3.1 "список исключений").

The thesis's third filter -- a full Russian word corpus (КРС, 3M forms
from OpenCorpora) -- is NOT ported: `dict.opcorpora.txt` is untracked,
271 MB, and not portable to a fresh clone (see README "Scope vs the
thesis"). Its role is approximated by the two lists above plus the
capitalization boost (stage 5): a capitalized, non-sentence-initial token
is trusted as a candidate proper name and is exempted from both filters
below, matching the thesis's own rationale for that stage.
"""
import re

from ._paths import diplom_path

FOREIGN_WORDS_FILE = 'foreign_words.txt'
EXCLUDE_FORMS_FILE = 'rusforms.txt'

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
