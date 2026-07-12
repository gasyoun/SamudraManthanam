r"""Forward paradigm generation from lemma + declension class (ВКР §3.2/§3.3.1).

The thesis tried two approaches to surface-form matching:

  1. Backward stemming -- strip a wordform's ending and look up the
     remainder in the lemma lists (§3.3.1, six ad hoc sub-conditions).
  2. Forward generation -- from each lemma, generate its full paradigm with
     `pymorphy2.lexeme`, then search the text for those surface forms
     (§3.2). This was *more accurate in principle* but pymorphy2 frequently
     mis-tags Sanskrit names as verbs/adjectives (e.g. Адхармахан -> a
     fictitious verb "адхармахать"), which corrupts the generated paradigm.

This module keeps the forward-generation strategy (its surface-form search
is simpler and gives a clean reverse index) but drives it from
`decl_rules.txt` -- the thesis's own hand-authored declension table for
Sanskritisms -- instead of pymorphy2, sidestepping the mis-tagging failure
mode entirely. Cross-checked against the tracked automated-index-forms
files (e.g. `Ram3_automated_index_forms.txt`: "индра : ['индра', 'индре',
'индры', 'индрой', 'индру']"), which this module reproduces exactly for
consonant/а/я-stem lemmas.
"""
from .lexicon import declension_class, default_decl_rules

CASES = ('nom', 'gen', 'dat', 'acc', 'ins', 'loc')


def generate_forms(lemma, rules=None):
    """Return the set of surface forms for a lowercased lemma.

    Indeclinable lemmas (ending -и/-у/-ю) yield a single form: the lemma
    itself. Otherwise every case's every suffix variant is generated.
    """
    cls = declension_class(lemma)
    if cls is None:
        return {lemma}
    rules = default_decl_rules() if rules is None else rules
    stem = lemma[:-1] if cls in ('а', 'я') else lemma
    class_rules = rules.get(cls, {})
    forms = {lemma}
    for case in CASES:
        for suffix in class_rules.get(case, ()):
            forms.add(stem + suffix)
    return forms


def build_reverse_index(lemma_pool, rules=None):
    """{surface_form: {lemma, ...}} across the whole lemma pool.

    A surface form can map to >1 lemma (e.g. "ракшасов" derived candidates
    ракшас/ракшаса/ракшаси per §3.3.3) -- these are exactly the cases
    `disambiguate.py` narrows.
    """
    rules = default_decl_rules() if rules is None else rules
    index = {}
    for lemma in lemma_pool:
        for form in generate_forms(lemma, rules):
            index.setdefault(form, set()).add(lemma)
    return index
