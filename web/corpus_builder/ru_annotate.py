r"""W9.2 (H6402) — Russian-side per-text annotation layer for the НКРЯ export.

The H905 `ru_morph` layer tags every Cyrillic token with pymorphy3's best
parse. On санскритизмы that parse is exactly what breaks: the ВКР's core
finding is that Russian lemmatizers mangle Sanskrit names and terms
(Адхармахан -> a fictitious verb "адхармахать", Кали -> кал). This module
wraps the pymorphy-family deterministic tagger with the **override layer**
the roadmap's Wave 9.2 mandates:

  * **санскритизм-lexicon overrides** — when a token's lowercased surface is
    a paradigm-generated form of a W3 lexicon lemma (`sanskritisms/`), and it
    passes the same trust filter as `extract.py` (capitalized non-sentence-
    initial proper name, or a survivor of the foreign-words / exception-list
    / `is_russian_word` filters), the LEMMA is forced from the lexicon
    instead of pymorphy's, and POS is forced `NOUN` — the W3 pool is proper
    names + terms (nominal by construction), and the tagger's POS on exactly
    these tokens is the ВКР's named failure mode (Адхармахан -> PRTS
    "адхармахать"). Case/number of the inflected surface are kept from the
    tagger when it parsed one (orthogonal to lemma identity, usually right)
    and stay empty when it did not.
  * **normalized name-index forms** — override lemmas go through the W3
    index's own canonical merge (`merge_plural_singular_duplicates`, the
    singular/plural pseudo-duplicate dedup, e.g. апсара/апсары → апсары), so
    the sidecar's lemmas agree with the committed proper-name index.

Stack provenance: 9.1 (`reports/RU_SIDE_TAGGER_BENCHMARK*verdict*.json`)
names the stack for this layer. When the verdict is absent, undecided, or
names a tagger that is not importable here, the **pymorphy deterministic
default** applies (H6402 mission text). The estate's pymorphy is pymorphy3
(H905) — same OpenCorpora dictionary family as the pymorphy2 the roadmap
names, maintained; the chosen stack and its provenance are recorded in every
emitted report (`stack`, `stack_src`) so the 9.1 verdict, when it lands,
re-selects nothing silently.

Determinism (the export's byte-identical gate): pymorphy parse selection is
tie-broken in `ru_morph` by `(-score, normal_form, str(tag))`; candidate
sets are narrowed by `narrow_candidates` (rules only, no scores); the lemma
pick is `sorted(narrowed)[0]`; the canonical merge is order-independent
(H821). Two runs are byte-identical.

Output shape mirrors the Sanskrit W7/H906 emitter (`sa_morph_tsv`): one row
per token keyed by group_id + tok_index, driven by `nkrya_export.ru_anno_tsv`.
"""
import glob
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:  # same local idiom as nkrya_export / the tests
    sys.path.insert(0, _HERE)

from ru_morph import tag_token
from sanskritisms import filters
from sanskritisms.disambiguate import (merge_plural_singular_duplicates,
                                       narrow_candidates)
from sanskritisms.extract import ExtractionContext

# repo-root reports/ (the 9.1 deliverable's home per the W9 roadmap text)
DEFAULT_REPORTS_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'reports'))

VERDICT_PATTERN = 'RU_SIDE_TAGGER_BENCHMARK*verdict*.json'

# Closed POS classes a Sanskrit loanword name can never belong to (the
# capitalized-«И» guard — see RuAnnotator._trusted_sanskritism).
_FUNCTION_POS = frozenset({'CONJ', 'PRCL', 'PREP', 'NPRO', 'INTJ', 'PRED'})


def resolve_stack(reports_dir=None):
    """(stack, provenance) — the 9.1 verdict names the tagger stack for 9.2;
    absent / undecided / unimportable → the pymorphy deterministic default.

    Only stacks this repo can actually run are returned; anything else falls
    back with the reason recorded in the provenance string."""
    d = DEFAULT_REPORTS_DIR if reports_dir is None else reports_dir
    if os.path.isdir(d):
        for path in sorted(glob.glob(os.path.join(d, VERDICT_PATTERN))):
            try:
                with open(path, encoding='utf-8') as f:
                    verdict = json.load(f)
            except Exception:
                continue
            if not isinstance(verdict, dict):
                continue
            named = str(verdict.get('stack') or verdict.get('verdict') or
                        verdict.get('winner') or '').lower()
            if not named:
                break  # an undecided verdict → default below
            if 'deeppavlov' in named:
                try:
                    import deeppavlov  # noqa: F401
                    return 'deeppavlov', '9.1 verdict %s' % path
                except Exception as exc:
                    return 'pymorphy3', (
                        '9.1 verdict %s names DeepPavlov but it is not '
                        'importable here (%s) — pymorphy deterministic '
                        'default per H6402' % (path, exc))
            if 'pymorphy' in named:
                return 'pymorphy3', '9.1 verdict %s' % path
            break  # unrecognized stack name → default below
    return 'pymorphy3', ('9.1 verdict JSON not found (%s under %s) — pymorphy '
                         'deterministic default per H6402 mission text'
                         % (VERDICT_PATTERN, d))


class RuAnnotator:
    """Deterministic per-token RU annotator: pymorphy-family best parse +
    санскритизм-lexicon lemma overrides + normalized name-index lemmas.

    Build once (the ExtractionContext loads the ~10k-lemma pool and its
    paradigm reverse index), reuse across sources — same contract as
    `sanskritisms_ctx` in nkrya_export."""

    def __init__(self, ctx=None, reports_dir=None):
        self.stack, self.stack_src = resolve_stack(reports_dir)
        self.ctx = ctx or ExtractionContext()
        # The W3 index's canonical dedup over the WHOLE pool, so sidecar
        # lemmas agree with the committed proper-name index (апсара → апсары).
        # Sorted input is belt-and-braces; the merge is order-independent.
        self.canonical = merge_plural_singular_duplicates(
            sorted(self.ctx.lemma_pool))

    @property
    def pymorphy_available(self):
        from ru_morph import available
        return available()

    def _trusted_sanskritism(self, surface, lower, sentence_initial, base_pos):
        """The extract.py trust filter, with one annotation-layer guard.

        Shared with extract.py: a capitalized, non-sentence-initial token is
        trusted as a proper name (ВКР §3.3.1 stage 5 — it bypasses the
        curated lists and the opcorpora filter alike, which is what rescues
        capitalized Кали, itself on Абрамович's loanword list, and Рама, a
        known Russian wordform); any other match must survive the
        foreign-words / exception-list / `is_russian_word` filters (the
        Кали→кал class).

        Guard (H6402, annotation layer only — the W3 index pipeline is
        untouched): a capitalized token the tagger parses as a CLOSED
        function class (CONJ/PRCL/PREP/NPRO/INTJ/PRED) is never a proper
        name — those classes take no loanword members. Poetic enjambment
        capitalizes «И вот…» after a line break, and stage 5's blanket
        exemption trusted it as the pool lemma «и»/NOUN (642 tokens in the
        Aranyakāṇḍa alone). The guard leaves unknown-to-pymorphy capitals
        (the адхармахан class) trusted: base_pos is empty exactly when the
        tagger had no parse."""
        if filters.is_capitalized(surface) and not sentence_initial:
            return base_pos not in _FUNCTION_POS
        if lower in self.ctx.foreign_words or lower in self.ctx.exclude_forms:
            return False
        return not filters.is_russian_word(lower)

    def tag(self, surface, sentence_initial=False):
        """One token → {surface, lemma, pos, case, number, lemma_src}.

        lemma_src: 'pymorphy' (tagger's own lemma) · 'sanskritizm' (lexicon
        override, unambiguous) · 'sanskritizm-amb' (override, ambiguous
        candidate set resolved by the deterministic sorted-first pick) ·
        'unknown' (no parse and no lexicon match — lemma = lowercased
        surface)."""
        base = tag_token(surface)
        lower = surface.lower()
        candidates = self.ctx.reverse_index.get(lower)
        if candidates and self._trusted_sanskritism(surface, lower,
                                                    sentence_initial,
                                                    base['pos']):
            narrowed = narrow_candidates(lower, candidates)
            lemma = sorted(narrowed)[0]
            lemma = self.canonical.get(lemma, lemma)
            # POS is forced NOUN: the W3 pool is proper names + terms —
            # nominal by construction — and the tagger's POS on exactly
            # these tokens is the ВКР's named failure mode (Адхармахан ->
            # PRTS "адхармахать"). Case/number of the inflected surface are
            # kept when the tagger parsed it (they are orthogonal to lemma
            # identity and usually right); both stay empty when it did not.
            pos = 'NOUN'
            src = 'sanskritizm' if len(narrowed) == 1 else 'sanskritizm-amb'
            return {'surface': surface, 'lemma': lemma, 'pos': pos,
                    'case': base['case'], 'number': base['number'],
                    'lemma_src': src}
        src = 'pymorphy' if base['pos'] else 'unknown'
        return {'surface': surface, 'lemma': base['lemma'], 'pos': base['pos'],
                'case': base['case'], 'number': base['number'], 'lemma_src': src}

    def annotate(self, text):
        """Tokenize `text` (the W3 tokenizer — it also yields the
        sentence-initial flag the trust filter needs) and tag every Cyrillic
        token in text order."""
        return [self.tag(surface, sentence_initial)
                for surface, _start, sentence_initial in filters.tokenize(text)]
