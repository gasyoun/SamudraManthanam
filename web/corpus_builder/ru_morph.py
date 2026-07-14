r"""Per-token Russian morphology for the seg=ru side of the НКРЯ export (H905).

НКРЯ (ruscorpora) is a *morphologically annotated* corpus; the shipped export
carries the Russian translation as plain text, which makes it "a bilingua
edition, not a corpus" (MG, 14-07-2026). This module tags every Cyrillic token
of a Russian segment with **lemma · POS · case · number**, using **pymorphy3**
— which ships the OpenCorpora dictionary (`pymorphy3-dicts-ru`), the very
КРС/opcorpora data Rubanova's 271 MB `dict.opcorpora.txt` held. So the tagger is
faithful to the thesis (she drove declension with pymorphy2, the same family)
and portable (no raw dump, no heavy DeepPavlov install).

Determinism (the export's byte-identical gate): `MorphAnalyzer.parse` returns
candidates score-sorted, but ties would otherwise depend on DAWG traversal, so
`analyze` breaks ties explicitly by `(-score, normal_form, str(tag))` before
taking the top parse. Two runs are therefore byte-identical.

Scope note: this is the RU morphology *layer*. Folding it inline into each
`<se>` as НКРЯ `<w><ana lex= gr=/>` elements is deliberately deferred to the
H906-coordinated per-token attribute scheme (so the SA side lands the same
shape) — see H905 "open questions". Until then the layer ships as a companion
`<slug>.ru_morph.tsv` next to the para-XML/TMX/TSV.
"""
import re
import sys

# Cyrillic word tokens (hyphenated compounds kept whole, matching filters.py).
_TOKEN_RE = re.compile(r'[а-яА-ЯёЁ]+(?:-[а-яА-ЯёЁ]+)*')

_MORPH = None


def _morph():
    global _MORPH
    if _MORPH is None:
        try:
            import pymorphy3
            _MORPH = pymorphy3.MorphAnalyzer()
        except Exception as exc:  # pragma: no cover - env-dependent
            print('ru_morph: pymorphy3 unavailable (%s); RU morphology layer '
                  'disabled (install pymorphy3).' % exc, file=sys.stderr)
            _MORPH = False
    return _MORPH


def available():
    """True if pymorphy3 is importable (the layer can be produced)."""
    return bool(_morph())


def _best_parse(surface):
    """The single most-likely parse, chosen deterministically."""
    m = _morph()
    if not m:
        return None
    parses = m.parse(surface)
    if not parses:
        return None
    # score-sort with an explicit, dictionary-hash-independent tie-break
    parses = sorted(parses, key=lambda p: (-p.score, p.normal_form, str(p.tag)))
    return parses[0]


def tag_token(surface):
    """Return {surface, lemma, pos, case, number} for one token.

    `pos`/`case`/`number` are pymorphy's short grammemes (NOUN/gent/plur …) or
    '' when the parser has no value. `lemma` falls back to the lowercased
    surface when the token is unknown or pymorphy3 is unavailable.
    """
    lower = surface.lower()
    p = _best_parse(surface)
    if p is None:
        return {'surface': surface, 'lemma': lower, 'pos': '',
                'case': '', 'number': ''}
    tag = p.tag
    return {
        'surface': surface,
        'lemma': p.normal_form,
        'pos': tag.POS or '',
        'case': tag.case or '',
        'number': tag.number or '',
    }


def analyze(text):
    """Tokenize `text` and return a list of per-token morphology dicts, in
    text order. Non-Cyrillic runs are skipped (the corpus's Russian side is
    Cyrillic; digits/Latin/punctuation carry no Russian morphology)."""
    return [tag_token(m.group(0)) for m in _TOKEN_RE.finditer(text)]
