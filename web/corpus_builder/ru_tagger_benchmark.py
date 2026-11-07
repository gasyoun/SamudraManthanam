#!/usr/bin/env python
r"""H6401 / W9.1 -- RU-side tagger benchmark on our corpus (replaces the VKR 47% figure).

Benchmarks open Russian taggers on OUR Russian side (canonical JSONL,
131-source export) over a seed-fixed stratified sample and measures lemma
accuracy on sanskritisms vs general vocabulary, then the OVERLAY effect
(force lemma from the W3 sanskritism layer, re-score).

Stack (this pass): pymorphy3 top-1 (the deterministic pymorphy2/3 baseline;
pymorphy2 is not installed on this executor, pymorphy3 2.0.6 is its
maintained twin on the same OpenCorpora dictionary). DeepPavlov morphology
and natasha/navec are NOT runnable offline on this executor (estate clone is
Mac-local; model downloads required) -- see the report's estimator caveats.

Gold: the W3 sanskritizm layer itself (Sorensen + MBh vol.3 oneword index
through `paradigms.py` reverse index, filtered exactly as `extract.py`
filters it) for sanskritism tokens; a <=500-token hand-adjudicated slice
(binary correct/incorrect per token in context, judged by the H6401 worker)
covering both sanskritism and general tokens.

Usage (from repo root):
  python web/corpus_builder/ru_tagger_benchmark.py run --out reports/ru_tagger_benchmark_2026
      # sample + tag + layer-match; writes tokens.csv + adjudication_dump.csv
  python web/corpus_builder/ru_tagger_benchmark.py score --dir reports/ru_tagger_benchmark_2026 --verdicts FILE
      # applies hand adjudication (csv: token_id,pym_ok,layer_ok[,note];
      #  unlisted ids = judged correct) and writes numbers.json + verdict.json
  python web/corpus_builder/ru_tagger_benchmark.py selfcheck
      # sampling + overlay determinism gate (runs the pipeline twice)

In-copyright posture: committed artifacts carry per-token rows (token,
lemma, flags, group id) and +-1 context words in the adjudication dump --
quote density only, no running-text bulk.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import random
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from sanskritisms.disambiguate import (  # noqa: E402
    merge_plural_singular_duplicates, narrow_candidates,
)
from sanskritisms.extract import iter_ru_segments  # noqa: E402
from sanskritisms.filters import (  # noqa: E402
    is_capitalized, is_russian_word, load_exclude_forms, load_foreign_words,
    tokenize,
)
from sanskritisms.lexicon import load_lemma_pool  # noqa: E402
from sanskritisms.paradigms import build_reverse_index  # noqa: E402
from sanskritisms._paths import JSONL_DIR  # noqa: E402

import pymorphy3  # noqa: E402

# --- fixed benchmark constitution (H6401: seed-fixed, 3 sources across
# epochs/registers, ~2-3k tokens; change only via a new dated report) ------
SEED = 20261029
PER_SOURCE_BUDGET = 1000
ADJ_SANS_CAP = 150       # hand-adjudicated sanskritism tokens (<=500 total slice)
ADJ_GENERAL_N = 150      # hand-adjudicated general-vocabulary tokens
SOURCES = [
    # (slug, epoch/register stratum)
    ('bhagavadgita-1788', '1788; старая орфография (ять), архаичный прозаический регистр'),
    ('buddhacharita-balmont', 'нач. XX в. (К. Бальмонт); поэтический регистр'),
    ('03_ramayana-aranyakanda', 'современная прозаическая серия; научный прозаический регистр'),
]

_MORPH = None


def morph():
    global _MORPH
    if _MORPH is None:
        _MORPH = pymorphy3.MorphAnalyzer()
    return _MORPH


def build_ctx():
    """Reverse index + filters, mirroring extract.ExtractionContext."""
    pool = load_lemma_pool()
    reverse = build_reverse_index(pool, None)
    all_lemmas = set(pool) | {l for cands in reverse.values() for l in cands}
    canonical = merge_plural_singular_duplicates(all_lemmas)
    return {
        'reverse': reverse,
        'canonical': canonical,
        'foreign': load_foreign_words(),
        'exclude': load_exclude_forms(),
    }


def layer_match(surface, sentence_initial, ctx):
    """The W3 sanskritism layer's verdict for one token, filtered exactly as
    extract.extract_source filters it. Returns sorted canonical lemma list
    (possibly empty)."""
    lower = surface.lower()
    cands = ctx['reverse'].get(lower)
    if not cands:
        return []
    capitalized_name = is_capitalized(surface) and not sentence_initial
    if not capitalized_name:
        if lower in ctx['foreign'] or lower in ctx['exclude']:
            return []
        if is_russian_word(lower):
            return []
    narrowed = narrow_candidates(lower, cands)
    return sorted({ctx['canonical'].get(l, l) for l in narrowed})


def sample_tokens(ctx):
    """Seed-fixed stratified sample: shuffle each source's verse groups,
    accumulate tokens in shuffled group order up to the per-source budget."""
    rows = []
    rng = random.Random(SEED)
    for slug, stratum in SOURCES:
        path = os.path.join(JSONL_DIR, slug + '.jsonl')
        segs = list(iter_ru_segments(path))
        order = list(range(len(segs)))
        rng.shuffle(order)
        taken = 0
        for gi in order:
            group, text = segs[gi]
            toks = list(tokenize(text))
            for i, (surface, _start, sent_init) in enumerate(toks):
                prev = toks[i - 1][0] if i > 0 else ''
                nxt = toks[i + 1][0] if i + 1 < len(toks) else ''
                rows.append({
                    'source': slug,
                    'stratum': stratum,
                    'group': group,
                    'token': surface,
                    'sentence_initial': sent_init,
                    'prev_token': prev,
                    'next_token': nxt,
                })
                taken += 1
            if taken >= PER_SOURCE_BUDGET:
                break
        # trim overflow of the last group to hit the budget exactly
        per_source = [r for r in rows if r['source'] == slug]
        if len(per_source) > PER_SOURCE_BUDGET:
            drop_ids = {id(r) for r in per_source[PER_SOURCE_BUDGET:]}
            rows = [r for r in rows if not (r['source'] == slug and id(r) in drop_ids)]
    for n, r in enumerate(rows):
        r['token_id'] = '%s-%04d' % (r['source'], n)
    return rows


def tag_rows(rows, ctx):
    """pymorphy3 top-1 + layer match for every sampled token."""
    m = morph()
    for r in rows:
        parse = m.parse(r['token'])[0]
        r['pym_lemma'] = parse.normal_form
        r['pym_pos'] = str(parse.tag.POS or '')
        r['pym_score'] = '%.3f' % parse.score
        r['layer_lemmas'] = layer_match(r['token'], r['sentence_initial'], ctx)
        r['is_sanskritism'] = bool(r['layer_lemmas'])
        overlay = r['layer_lemmas'] or [r['pym_lemma']]
        r['overlay_lemma'] = overlay[0]  # sorted-first forced pick (deterministic)
    return rows


def pick_adjudication(rows):
    """Seed-derived (SEED+1) subsample: <=ADJ_SANS_CAP sanskritism tokens +
    ADJ_GENERAL_N general tokens."""
    rng = random.Random(SEED + 1)
    sans = [r for r in rows if r['is_sanskritism']]
    general = [r for r in rows if not r['is_sanskritism']]
    rng.shuffle(sans)
    rng.shuffle(general)
    picked = sans[:ADJ_SANS_CAP] + general[:ADJ_GENERAL_N]
    return sorted(picked, key=lambda r: r['token_id'])


def wilson(p, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    ph = p
    den = 1 + z * z / n
    centre = ph + z * z / (2 * n)
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return ((centre - half) / den, (centre + half) / den)


def write_csv(path, rows, fields):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in fields})


def cmd_run(args):
    ctx = build_ctx()
    rows = tag_rows(sample_tokens(ctx), ctx)
    out = args.out
    os.makedirs(out, exist_ok=True)
    flat = []
    for r in rows:
        fr = dict(r)
        fr['layer_lemmas'] = '|'.join(r['layer_lemmas'])
        flat.append(fr)
    write_csv(os.path.join(out, 'tokens.csv'), flat, [
        'token_id', 'source', 'group', 'token', 'sentence_initial',
        'is_sanskritism', 'pym_lemma', 'pym_pos', 'pym_score',
        'layer_lemmas', 'overlay_lemma',
    ])
    adj = pick_adjudication(rows)
    for r in adj:
        r['layer_lemmas'] = '|'.join(r['layer_lemmas'])
    write_csv(os.path.join(out, 'adjudication_dump.csv'), adj, [
        'token_id', 'source', 'token', 'prev_token', 'next_token',
        'pym_lemma', 'pym_pos', 'layer_lemmas',
    ])
    digest = hashlib.md5('\n'.join(
        r['token_id'] + '|' + r['token'] + '|' + r['pym_lemma'] + '|' + r['overlay_lemma']
        for r in rows).encode('utf-8')).hexdigest()
    n_sans = sum(1 for r in rows if r['is_sanskritism'])
    print('sampled tokens: %d (sanskritism-layer matched: %d) from %d sources'
          % (len(rows), n_sans, len(SOURCES)))
    print('adjudication slice: %d rows -> %s' % (len(adj), os.path.join(out, 'adjudication_dump.csv')))
    print('sample digest: %s' % digest)
    return 0


def cmd_score(args):
    with open(os.path.join(args.dir, 'tokens.csv'), encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    wrong = {}
    if args.verdicts and os.path.exists(args.verdicts):
        with open(args.verdicts, encoding='utf-8') as f:
            for rec in csv.DictReader(f):
                wrong[rec['token_id']] = (
                    str(rec.get('pym_ok', '1')) == '1',
                    str(rec.get('layer_ok', '1')) == '1',
                    rec.get('note', ''),
                )

    def judged_ok(tid, which):
        v = wrong.get(tid)
        return True if v is None else v[0 if which == 'pym' else 1]

    numbers = {'sample': {}, 'baseline': {}, 'overlay': {}, 'adjudicated': {}, 'strata': {}}
    sans = [r for r in rows if r['is_sanskritism'] == 'True']
    gen = [r for r in rows if r['is_sanskritism'] != 'True']
    numbers['sample'] = {
        'seed': SEED,
        'sources': [s[0] for s in SOURCES],
        'tokens_total': len(rows),
        'sanskritism_tokens': len(sans),
        'general_tokens': len(gen),
    }

    # -- baseline, full sample, gold = W3 layer (lenient: pymorphy lemma in
    # the layer's candidate set; strict: equals the sorted-first forced lemma)
    len_ok = sum(1 for r in sans if r['pym_lemma'].lower() in r['layer_lemmas'].split('|'))
    str_ok = sum(1 for r in sans if r['pym_lemma'].lower() == r['layer_lemmas'].split('|')[0])
    amb = sum(1 for r in sans if len(r['layer_lemmas'].split('|')) > 1)
    p_len, p_str = len_ok / len(sans), str_ok / len(sans)
    numbers['baseline'] = {
        'stack': 'pymorphy3 %s (top-1 parse)' % pymorphy3.__version__,
        'sanskritism_lenient_acc': round(p_len, 4),
        'sanskritism_lenient_ci95': [round(x, 4) for x in wilson(p_len, len(sans))],
        'sanskritism_strict_acc': round(p_str, 4),
        'sanskritism_n': len(sans),
        'layer_ambiguity_rate': round(amb / len(sans), 4),
    }

    # -- overlay: forced lemma = sorted-first layer candidate. Against the
    # layer gold this is correct by construction on every matched token; the
    # non-trivial numbers are the ambiguity rate (above) and the adjudicated
    # layer_ok rate below.
    numbers['overlay'] = {
        'policy': 'force sorted-first W3 layer lemma on matched tokens',
        'full_sample_acc_vs_layer_gold': 1.0,
        'note': ('tautological by construction (forced lemma IS the layer gold); '
                 'see adjudicated.* for the non-trivial overlay numbers'),
    }

    # -- adjudicated slice (hand judgments; unlisted = judged correct)
    adj_ids = set(wrong)
    dump_path = os.path.join(args.dir, 'adjudication_dump.csv')
    with open(dump_path, encoding='utf-8') as f:
        dump = list(csv.DictReader(f))
    adj_sans = [r for r in dump if r['layer_lemmas']]
    adj_gen = [r for r in dump if not r['layer_lemmas']]
    for name, sub in (('sans', adj_sans), ('general', adj_gen)):
        n = len(sub)
        pym_ok = sum(1 for r in sub if judged_ok(r['token_id'], 'pym'))
        layer_ok = sum(1 for r in sub if judged_ok(r['token_id'], 'layer'))
        row = {'n': n, 'pymorphy3_top1_acc': round(pym_ok / n, 4) if n else None}
        if n:
            row['pymorphy3_top1_ci95'] = [round(x, 4) for x in wilson(pym_ok / n, n)]
        if name == 'sans':
            row['layer_gold_ok_rate'] = round(layer_ok / n, 4) if n else None
            row['overlay_effect_dp'] = round((layer_ok - pym_ok) / n * 100, 1) if n else None
        numbers['adjudicated'][name] = row
    numbers['adjudicated']['judged_wrong_listed'] = len(adj_ids)

    for slug, _stratum in SOURCES:
        sub = [r for r in sans if r['source'] == slug]
        n = len(sub)
        ok = sum(1 for r in sub if r['pym_lemma'].lower() in r['layer_lemmas'].split('|'))
        allsrc = [r for r in rows if r['source'] == slug]
        numbers['strata'][slug] = {
            'tokens': len(allsrc), 'sanskritism_tokens': n,
            'pymorphy3_lenient_acc': round(ok / n, 4) if n else None,
        }

    verdict = {
        'handoff': 'H6401', 'wave': '9.1', 'date': '2026-10-29',
        'stack_for_9_2': 'pymorphy3',
        'stack_details': {
            'package': 'pymorphy3', 'version': pymorphy3.__version__,
            'dictionary': 'OpenCorpora (bundled)',
            'selection_rule': 'top-1 parse by analyzer score',
            'rationale': ('only stack cheaply runnable offline on this executor; '
                          'pymorphy2 not installed (pymorphy3 = maintained twin, '
                          'same dictionary); DeepPavlov estate clone is Mac-local '
                          'and natasha/navec need model downloads'),
        },
        'overlay': ('W3 sanskritism reverse index (Sorensen 9460 + MBh vol.3 oneword '
                    '+ decl_rules paradigms), extract.py filtering, sorted-first forced pick'),
        'sample': numbers['sample'],
        'numbers': numbers,
        'reproduce': ('python web/corpus_builder/ru_tagger_benchmark.py run --out DIR '
                      '&& (adjudicate DIR/adjudication_dump.csv) && '
                      'python web/corpus_builder/ru_tagger_benchmark.py score --dir DIR --verdicts FILE'),
    }
    with open(os.path.join(args.dir, 'numbers.json'), 'w', encoding='utf-8') as f:
        json.dump(numbers, f, ensure_ascii=False, indent=2, sort_keys=True)
    with open(os.path.join(args.dir, 'verdict.json'), 'w', encoding='utf-8') as f:
        json.dump(verdict, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(json.dumps(numbers, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cmd_selfcheck(_args):
    ctx = build_ctx()
    d1 = tag_rows(sample_tokens(ctx), ctx)
    d2 = tag_rows(sample_tokens(ctx), ctx)
    sig = lambda rows: [  # noqa: E731
        (r['token_id'], r['token'], r['pym_lemma'], r['overlay_lemma']) for r in rows]
    assert sig(d1) == sig(d2), 'sampling/tagging not deterministic'
    a1 = [r['token_id'] for r in pick_adjudication(d1)]
    a2 = [r['token_id'] for r in pick_adjudication(d2)]
    assert a1 == a2, 'adjudication subsample not deterministic'
    print('selfcheck PASS: %d tokens, %d sanskritism, adjudication %d rows, two runs identical'
          % (len(d1), sum(1 for r in d1 if r['is_sanskritism']), len(a1)))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p_run = sub.add_parser('run')
    p_run.add_argument('--out', required=True)
    p_run.set_defaults(func=cmd_run)
    p_score = sub.add_parser('score')
    p_score.add_argument('--dir', required=True)
    p_score.add_argument('--verdicts', required=True)
    p_score.set_defaults(func=cmd_score)
    p_chk = sub.add_parser('selfcheck')
    p_chk.set_defaults(func=cmd_selfcheck)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
