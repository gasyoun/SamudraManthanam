r"""Curated annotation layers for the printed-index display format (ВКР §3.3.2).

  * `3_INDEX_phrases.txt` -- "рубрики-фразы": lemma -> full annotated
    rubric string ("см." cross-references, plant/animal Latin binomials,
    parenthetical glosses). Format: ``lemma: full string`` (one per line).
  * `3_INDEX_options.txt` -- "рубрики с пояснениями": homonym lemmas that
    resolve to different rubrics depending on a disambiguating context word
    found in the same sentence (e.g. Айравата -> elephant vs. serpent).
    Format: ``Lemma: word1 - rubric1; word2 - rubric2``.
  * `append if found.txt` -- a small supplementary override list in the
    same ``lemma: rubric`` shape as the phrases file.
  * `rus_index.txt` / `rus_index_declined.txt` -- Russian-language epithet
    phrases that refer to a Sanskrit entity by translation rather than
    transliteration (e.g. "Великий Владыка"), plus their generated
    case-declined forms for in-text search (§3.3.2). These are matched
    against the running text as an independent phrase-search pass, not
    through the lemma/paradigm pipeline.
"""
import ast

from ._paths import diplom_path

PHRASES_FILE = '3_INDEX_phrases.txt'
OPTIONS_FILE = '3_INDEX_options.txt'
APPEND_FILE = 'append if found.txt'
RUS_INDEX_FILE = 'rus_index.txt'
RUS_INDEX_DECLINED_FILE = 'rus_index_declined.txt'


def _lines(path):
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.strip():
                yield line


def load_phrases(path=None):
    """{lemma_lower: rubric_string} from a ``lemma: rubric`` list file."""
    path = diplom_path(PHRASES_FILE) if path is None else path
    out = {}
    for line in _lines(path):
        lemma, sep, rubric = line.partition(': ')
        if not sep:
            continue
        out[lemma.strip().lower()] = rubric.strip()
    return out


def load_append_if_found(path=None):
    path = diplom_path(APPEND_FILE) if path is None else path
    return load_phrases(path)


def load_options(path=None):
    """{lemma_lower: [(context_word_lower, rubric_string), ...]}."""
    path = diplom_path(OPTIONS_FILE) if path is None else path
    out = {}
    for line in _lines(path):
        lemma, sep, rest = line.partition(': ')
        if not sep:
            continue
        variants = []
        for chunk in rest.split('; '):
            word, sep2, rubric = chunk.partition(' - ')
            if not sep2:
                continue
            variants.append((word.strip().lower(), rubric.strip()))
        if variants:
            out[lemma.strip().lower()] = variants
    return out


def resolve_options(lemma, sentence_lower, options):
    """Pick the best-matching rubric for a homonym `lemma` given the
    sentence it occurred in, or None if there is no options entry / no
    context word matched (caller falls back to the bare lemma or phrases)."""
    variants = options.get(lemma)
    if not variants:
        return None
    for context_word, rubric in variants:
        if context_word in sentence_lower:
            return rubric
    return None


def load_rus_index_declined(path=None):
    """[(base_phrase_lower, [declined_form_lower, ...]), ...] from
    `rus_index_declined.txt` (``phrase : ['form1', 'form2', ...]``)."""
    path = diplom_path(RUS_INDEX_DECLINED_FILE) if path is None else path
    out = []
    for line in _lines(path):
        base, sep, forms_repr = line.partition(' : ')
        if not sep:
            continue
        try:
            forms = ast.literal_eval(forms_repr.strip())
        except (ValueError, SyntaxError):
            continue
        out.append((base.strip().lower(), [f.lower() for f in forms]))
    return out
