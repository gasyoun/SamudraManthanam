r"""Per-source sanskritism extraction + proper-name index (ВКР method, H760).

Pipeline per source (одна JSONL-книга, `web/corpus_builder/jsonl/<slug>.jsonl`):

  1. Read every `seg=ru` group's text (the Russian translation running
     text -- "Do NOT: No dictionaries -- running text only").
  2. Tokenize; for every Cyrillic token, look up its paradigm-generated
     surface form against the reverse lemma index (`paradigms.py`).
  3. A match is kept if it is a trusted capitalized proper name (§3.3.1
     stage 5), or otherwise survives the foreign-words / exception-list
     filters (`filters.py`, the portable approximation of the thesis's
     Russian-word-corpus filter -- see README).
  4. Multi-candidate matches are narrowed by the nine suffix rules
     (`disambiguate.py`); residual multi-candidate matches are kept
     `ambiguous=True` rather than force-resolved (no deeppavlov here).
  5. Singular/plural pseudo-duplicate lemmas are merged (§3.3.3 final
     step).
  6. Each surviving lemma is annotated for display using the curated
     rubric files (`annotations.py`): options (context-disambiguated),
     else phrases/append, else the bare lemma.
  7. Independently, curated Russian epithet phrases (`rus_index_declined`)
     are searched in the same running text and recorded as a second,
     parallel "epithet" layer of the index.

Output: `{"lexicon": {...}, "epithets": {...}, "stats": {...}}` -- see
README for the full shape. Two views over the same lexicon are written by
`build_all.py`: a full-detail JSON (the "sanskritism lexicon") and a
sorted, annotated Markdown/JSON index (the "proper-name index").
"""
import collections
import json
import os
import re

from . import annotations, filters
from .disambiguate import merge_plural_singular_duplicates, narrow_candidates
from .lexicon import default_decl_rules, load_lemma_pool
from .paradigms import build_reverse_index
from ._paths import JSONL_DIR

SAMPLE_CAP = 25


def discover_ru_sources(jsonl_dir=None):
    """Slugs of every JSONL source that carries at least one seg="ru"
    record (the "all verse sources" this handoff's goal refers to)."""
    jsonl_dir = JSONL_DIR if jsonl_dir is None else jsonl_dir
    slugs = []
    for name in sorted(os.listdir(jsonl_dir)):
        if not name.endswith('.jsonl'):
            continue
        path = os.path.join(jsonl_dir, name)
        with open(path, encoding='utf-8') as f:
            for line in f:
                if '"seg": "ru"' in line or '"seg":"ru"' in line:
                    slugs.append(name[:-len('.jsonl')])
                    break
    return slugs


def iter_ru_segments(jsonl_path):
    """Yield (group_id, text) for every non-deleted, non-empty seg="ru"
    record in file order."""
    with open(jsonl_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get('deleted') or rec.get('seg') != 'ru':
                continue
            text = (rec.get('text') or '').strip()
            if text:
                yield rec.get('group'), text


def _new_entry():
    return {
        'count': 0,
        'forms': set(),
        'groups': [],
        'total_occurrences': 0,
        'capitalized_seen': False,
        'ambiguous_with': set(),
        'rubric_votes': collections.Counter(),
    }


def _compile_epithet_pattern(rus_index_declined):
    form_to_base = {}
    for base, forms in rus_index_declined:
        for form in forms:
            form_to_base.setdefault(form, base)
    if not form_to_base:
        return None, form_to_base
    ordered = sorted(form_to_base, key=len, reverse=True)
    pattern = re.compile('|'.join(re.escape(f) for f in ordered))
    return pattern, form_to_base


class ExtractionContext:
    """Bundles the (expensive-to-build) shared inputs so `extract_source`
    can be called once per source without re-loading/re-indexing lists."""

    def __init__(self, diplom_dir=None):
        self.lemma_pool = load_lemma_pool(diplom_dir)
        if diplom_dir is None:
            self.rules = default_decl_rules()
        else:
            from .lexicon import parse_decl_rules, _freeze
            self.rules = _freeze(parse_decl_rules(
                os.path.join(diplom_dir, 'decl_rules.txt')))
        self.reverse_index = build_reverse_index(self.lemma_pool, self.rules)
        self.foreign_words = filters.load_foreign_words(diplom_dir)
        self.exclude_forms = filters.load_exclude_forms(diplom_dir)
        self.phrases = annotations.load_phrases(
            None if diplom_dir is None else os.path.join(diplom_dir, annotations.PHRASES_FILE))
        self.options = annotations.load_options(
            None if diplom_dir is None else os.path.join(diplom_dir, annotations.OPTIONS_FILE))
        self.append = annotations.load_append_if_found(
            None if diplom_dir is None else os.path.join(diplom_dir, annotations.APPEND_FILE))
        rid = annotations.load_rus_index_declined(
            None if diplom_dir is None else os.path.join(diplom_dir, annotations.RUS_INDEX_DECLINED_FILE))
        self.epithet_pattern, self.epithet_form_to_base = _compile_epithet_pattern(rid)


def extract_source(jsonl_path, ctx=None, diplom_dir=None):
    """Extract the sanskritism lexicon + epithet layer for one source.

    Returns a dict: {'lexicon': {lemma: entry}, 'epithets': {base: entry},
    'stats': {...}}. `entry['forms']`/`['ambiguous_with']` are lists in the
    return value (JSON-serializable); sets are used internally.
    """
    ctx = ctx or ExtractionContext(diplom_dir)

    lexicon = {}
    epithets = {}
    n_groups = 0
    n_tokens = 0
    n_matches = 0

    for group, text in iter_ru_segments(jsonl_path):
        n_groups += 1
        text_lower = text.lower()

        for surface, _start, sentence_initial in filters.tokenize(text):
            n_tokens += 1
            lower = surface.lower()
            candidates = ctx.reverse_index.get(lower)
            if not candidates:
                continue
            capitalized_name = filters.is_capitalized(surface) and not sentence_initial
            if not capitalized_name:
                if lower in ctx.foreign_words or lower in ctx.exclude_forms:
                    continue
                # H905: Rubanova's opcorpora `rus_words` filter (via pymorphy3).
                # A non-capitalized token that is a known Russian wordform is a
                # false positive (e.g. lowercase "кала" = genitive of the common
                # word "кал", colliding with the Sanskritism "кала"/Kāla) — the
                # Кали→кал class. Capitalized proper names are exempt above.
                if filters.is_russian_word(lower):
                    continue
            n_matches += 1

            narrowed = narrow_candidates(lower, candidates)
            ambiguous = len(narrowed) > 1
            for lemma in sorted(narrowed):   # deterministic lexicon order (H821 determinism gate)
                entry = lexicon.setdefault(lemma, _new_entry())
                entry['count'] += 1
                entry['forms'].add(lower)
                if capitalized_name:
                    entry['capitalized_seen'] = True
                if ambiguous:
                    entry['ambiguous_with'] |= (narrowed - {lemma})
                if len(entry['groups']) < SAMPLE_CAP:
                    entry['groups'].append(group)
                entry['total_occurrences'] += 1

                rubric = annotations.resolve_options(lemma, text_lower, ctx.options)
                if rubric:
                    entry['rubric_votes'][rubric] += 1

        if ctx.epithet_pattern is not None:
            for m in ctx.epithet_pattern.finditer(text_lower):
                base = ctx.epithet_form_to_base[m.group(0)]
                entry = epithets.setdefault(base, _new_entry())
                entry['count'] += 1
                entry['forms'].add(m.group(0))
                if len(entry['groups']) < SAMPLE_CAP:
                    entry['groups'].append(group)
                entry['total_occurrences'] += 1

    canonical = merge_plural_singular_duplicates(lexicon.keys())
    merged = {}
    for lemma, entry in lexicon.items():
        target = canonical[lemma]
        agg = merged.setdefault(target, _new_entry())
        agg['count'] += entry['count']
        agg['forms'] |= entry['forms']
        agg['capitalized_seen'] = agg['capitalized_seen'] or entry['capitalized_seen']
        agg['ambiguous_with'] |= {canonical.get(a, a) for a in entry['ambiguous_with']}
        agg['ambiguous_with'].discard(target)
        agg['total_occurrences'] += entry['total_occurrences']
        for g in entry['groups']:
            if len(agg['groups']) < SAMPLE_CAP:
                agg['groups'].append(g)
        agg['rubric_votes'].update(entry['rubric_votes'])

    def _finalize(d):
        out = {}
        for key, entry in d.items():
            out[key] = {
                'count': entry['count'],
                'total_occurrences': entry['total_occurrences'],
                'forms': sorted(entry['forms']),
                'groups': entry['groups'],
                'capitalized_seen': entry.get('capitalized_seen', False),
                'ambiguous_with': sorted(entry.get('ambiguous_with', ())),
                'rubric_votes': dict(entry.get('rubric_votes', {})),
            }
        return out

    result = {
        'lexicon': _finalize(merged),
        'epithets': _finalize(epithets),
        'stats': {
            'groups': n_groups,
            'tokens': n_tokens,
            'candidate_matches': n_matches,
            'lemmas': len(merged),
            'epithet_bases': len(epithets),
        },
    }
    return result


def build_name_index(extraction, ctx):
    """Sorted, annotated ("printed-index"-style) view of one source's
    lexicon: [{'lemma', 'display', 'count', 'ambiguous'}], sorted
    alphabetically by lemma."""
    entries = []
    for lemma, entry in extraction['lexicon'].items():
        display = None
        if entry['rubric_votes']:
            display = max(entry['rubric_votes'].items(), key=lambda kv: kv[1])[0]
        if display is None:
            display = ctx.phrases.get(lemma) or ctx.append.get(lemma)
        if display is None:
            display = lemma
        entries.append({
            'lemma': lemma,
            'display': display,
            'count': entry['total_occurrences'],
            'ambiguous': bool(entry['ambiguous_with']),
        })
    entries.sort(key=lambda e: e['lemma'])
    return entries
