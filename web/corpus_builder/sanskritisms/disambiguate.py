r"""Lemma-disambiguation rules for multi-candidate surface forms (ВКР §3.3.3).

When a surface form's stem matches more than one lemma in the pool (e.g.
"ракшасов" -> {ракшас, ракшаса, ракшаси}), the thesis derived nine
morphological suffix rules from Russian declension paradigms to narrow the
candidate set (order-independent by construction -- each rule constrains a
disjoint ending class). A rule is applied only if it would leave >=1
candidate; per the thesis, a rule that would eliminate every remaining
candidate is skipped rather than applied ("отмести сразу все... не
представляется возможным").

Residual ambiguity (~20% of cases per the thesis measurement) was resolved
in the ВКР with deeppavlov case/context analysis. That external dependency
is NOT ported here (no deeppavlov in this repo's stack) -- surviving
multi-candidate cases are surfaced with `ambiguous=True` and all candidate
lemmas, rather than forced to a single pick. See README "Scope vs the
thesis".
"""

VOWELS = set('аеёиоуыэюя')
CONS_89 = set('слрнзфвпдмтб')


def _is_plural_lemma(lemma):
    return lemma.endswith('и') or lemma.endswith('ы')


def _plurality_constraint(surface):
    """Rules 6/7/3/2/1/4/5 -- which plurality the lemma must have, or None."""
    if surface.endswith('ам') or surface.endswith('ям'):
        return True    # rule 6
    if surface.endswith('ом') or surface.endswith('ем'):
        return False   # rule 7
    if surface.endswith('ми'):
        return True    # rule 3
    if surface.endswith('ой'):
        return False   # rule 2
    if surface.endswith('в'):
        return True    # rule 1
    if surface.endswith('х'):
        return True    # rule 4
    if surface[-1:] in ('у', 'е', 'ю', 'о'):
        return False   # rule 5
    return None


def _endsi_constraint(surface):
    """Rules 8/9 -- vowel-final surface, preceded by a listed consonant."""
    if len(surface) < 2:
        return None
    last, prev = surface[-1], surface[-2]
    if last not in VOWELS or prev not in CONS_89:
        return None
    return last == 'и'


def narrow_candidates(surface, candidates):
    """Apply the nine rules to `candidates` (lemma strings) for `surface`.

    Never returns an empty set if `candidates` was non-empty.
    """
    survivors = set(candidates)
    if len(survivors) <= 1:
        return survivors

    plurality = _plurality_constraint(surface)
    if plurality is not None:
        narrowed = {c for c in survivors if _is_plural_lemma(c) == plurality}
        if narrowed:
            survivors = narrowed

    endsi = _endsi_constraint(surface)
    if endsi is not None:
        narrowed = {c for c in survivors if c.endswith('и') == endsi}
        if narrowed:
            survivors = narrowed

    return survivors


def _stem_for_merge(lemma):
    """Strip a trailing plural -и/-ы (or singular -а/-я/-и/-у/-ю) to compare
    number-variant lemmas sharing the same root (§3.3.3 final merge step)."""
    if lemma.endswith(('и', 'ы', 'а', 'я', 'у', 'ю')):
        return lemma[:-1]
    return lemma


def merge_plural_singular_duplicates(lemmas):
    """Given an iterable of lemma strings extracted for one source, merge
    singular/plural pseudo-duplicate pairs sharing a stem (e.g. апсара /
    апсары) into the plural form, matching the thesis's final dedup pass
    (525 -> 380 rubrics on the Rāmāyaṇa vol. 3 pilot).

    Returns {original_lemma: canonical_lemma}.
    """
    lemmas = list(lemmas)
    by_stem = {}
    for lemma in lemmas:
        by_stem.setdefault(_stem_for_merge(lemma), []).append(lemma)

    canonical = {}
    for stem, group in by_stem.items():
        if len(group) == 1:
            canonical[group[0]] = group[0]
            continue
        # sorted() so the canonical winner is deterministic regardless of the
        # input lemma order (upstream candidate sets iterate in hash order) —
        # H821 Wave-4 export determinism gate.
        plural_forms = sorted(l for l in group if _is_plural_lemma(l))
        winner = plural_forms[0] if plural_forms else sorted(group)[0]
        for lemma in group:
            canonical[lemma] = winner
    return canonical
