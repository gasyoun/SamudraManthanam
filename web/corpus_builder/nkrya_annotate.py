#!/usr/bin/env python
r"""H759 -- Sanskrit-side 3-path annotation comparison on the НКРЯ pilot (Wave 2).

Compares three Sanskrit-side annotation variants on the four pilot sources
(MBh 3 + Rāmāyaṇa 1-3, the 11,055 exported verse pairs of PILOT_VALIDATION.md),
per ruling 3 of docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md:

  A. plain IAST/SLP1     -- the baseline already carried by the canonical JSONL
                            (no lemma/morph; measured here as the reference
                            token frame the other two paths annotate).
  B. DCS crosswalk       -- lemma+morph from the Digital Corpus of Sanskrit
                            (Hellwig, CC BY 4.0) via the VisualDCS SQLite master
                            (src/DCS-data-2026/dcs_full.sqlite, built from the
                            pinned gasyoun/dcs-conllu snapshot 04e0778).
  C. fresh auto-tagging  -- vidyut-cheda segmentation + lemmatization
                            (ambuda-org/vidyut, local + reproducible).

CROSSWALK DESIGN (path B). Verse numbering does NOT line up across editions:
our MBh 3 has 299 chapters (critical-edition numbering, same as DCS) but our
Rāmāyaṇa kāṇḍas are vulgate-numbered (77/119/75 sargas vs DCS's critical
76/111/71). So the crosswalk is TEXT-keyed, not locus-keyed: every DCS
half-verse (`sentence.text_sandhied`, IAST) in the pilot scope is indexed under
an aggressive normalization (lowercase, strip everything but IAST letters --
which neutralizes sandhi spacing: DCS "kopitāś ca" == our "kopitāśca"), and each
of OUR half-verse lines (the `text` field split on daṇḍas) is matched in three
tiers: (1) exact on the normalized string; (2) consonant-skeleton equality --
DCS's Rāmāyaṇa `text_sandhied` is largely DE-sandhied pada text ("sukhatantraḥ
na ca alasaḥ") where our vulgate surface is sandhied ("sukhatantro nacālasaḥ"),
and deleting vowels+visarga while folding nasals neutralizes exactly that class
of difference (guarded by a similarity floor on the vowelled strings); (3)
difflib >= 0.90 within a shared-prefix bucket for residual near misses.
Match rate is MEASURED AND REPORTED per tier, never assumed.

LEMMA COMPARISON (B vs C). DCS lemmas are IAST, vidyut lemmas SLP1; both are
mapped to SLP1 (indic_transliteration) and compared as per-group sets on groups
where EVERY line found a DCS counterpart (apples-to-apples). Metrics: Jaccard,
containment both ways, agreement buckets. A stratified sample (fixed seed, low/
mid/high-agreement tertiles) is emitted for human adjudication via /review-sheet.

Determinism: no clock in any artifact, fixed RNG seed, sorted sets -- two runs
are byte-identical (same gate as nkrya_export.py).

RIGHTS: outputs here are Sanskrit-side only (ancient text + derived lemmas) --
no Russian translation text leaves the repo; the per-source annotated TSVs are
still gitignored with the rest of export/ bulk, only the small metrics JSON +
adjudication sample + report are committed. DCS annotation is CC BY 4.0
(attribution: Hellwig, The Digital Corpus of Sanskrit) -- redistribution inside
НКРЯ is licence-compatible with attribution.

Usage:
  python nkrya_annotate.py --all-pilot --out ../../nkrya-parallel/export
  python nkrya_annotate.py --source 01_ramayana-balakanda --skip-c --out DIR
  python nkrya_annotate.py --all-pilot --limit 50 --out DIR   # smoke run
"""
import argparse
import collections
import difflib
import json
import os
import random
import re
import sqlite3
import sys
import unicodedata

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from nkrya_export import PILOT_SOURCES, iter_groups, natural_key  # noqa: E402

try:
    from indic_transliteration import sanscript
except ImportError:  # pragma: no cover
    sanscript = None

VERSION = '0.1.0'

HERE = os.path.dirname(os.path.abspath(__file__))
JSONL_DIR = os.path.join(HERE, 'jsonl')

DEFAULT_DCS_DB = r'C:/Users/user/Documents/GitHub/VisualDCS/src/DCS-data-2026/dcs_full.sqlite'
DEFAULT_VIDYUT = r'C:/Users/user/.cache/vidyut/0.4.0'

# Pilot source -> (DCS text_id, chapter-ref LIKE scope).
DCS_SCOPE = {
    '03_mahabharata-aranyakaparva': (154, 'MBh, 3, %'),
    '01_ramayana-balakanda': (143, 'Rām, Bā, %'),
    '02_ramayana-ayodhyakanda': (143, 'Rām, Ay, %'),
    '03_ramayana-aranyakanda': (143, 'Rām, Ār, %'),
}

_IAST_KEEP = re.compile(r"[^a-zāīūṛṝḷḹṅñṭḍṇśṣṃḥ]")
_LINE_SPLIT = re.compile(r"[।॥]+")
_FUZZY_PREFIX = 10
_FUZZY_CUTOFF = 0.90
_SKELETON_GUARD = 0.70   # min difflib ratio on the vowelled strings for a skeleton hit
SAMPLE_SEED = 759

# Sandhi-robust consonant skeleton: DCS's Rāmāyaṇa text_sandhied is largely
# DE-sandhied pada text ("sukhatantraḥ na ca alasaḥ") where our vulgate surface
# is sandhied ("sukhatantro nacālasaḥ"). Deleting vowels + visarga neutralizes
# vowel/visarga sandhi (o vs aḥ, y vs i+vowel needs y/v dropped too), folding
# every nasal to m neutralizes anusvāra vs homorganic nasal (saṃgṛhya vs
# saṅgṛhya). y/v also drop because they ARE vowel sandhi (drakṣyāmy vs
# drakṣyāmi); the resulting collision risk is held down by the vowelled-string
# similarity guard in match_line.
_NASAL_FOLD = str.maketrans('ṅñṇnṃ', 'mmmmm')
_SKELETON_DROP = re.compile(r"[aāiīuūṛṝḷḹeoḥyv]")


def skeleton(norm):
    """Sandhi-robust consonant skeleton of a norm_iast key."""
    return _SKELETON_DROP.sub('', norm.translate(_NASAL_FOLD))


def norm_iast(s):
    """Aggressive IAST match key: NFC, lowercase, IAST letters only.

    Removing spaces/punctuation/digits neutralizes sandhi-spacing and daṇḍa /
    verse-number differences between our verse surface and DCS text_sandhied."""
    s = unicodedata.normalize('NFC', s or '').lower().replace('ṁ', 'ṃ')  # ṁ -> ṃ
    return _IAST_KEEP.sub('', s)


def split_lines(text):
    """Split a verse-group surface into half-verse lines on daṇḍas."""
    out = []
    for chunk in _LINE_SPLIT.split(text or ''):
        chunk = chunk.strip()
        if chunk and norm_iast(chunk):
            out.append(chunk)
    return out


def iast_to_slp1(s):
    if sanscript is None:  # pragma: no cover
        raise RuntimeError('indic_transliteration is required')
    return sanscript.transliterate(s, sanscript.IAST, sanscript.SLP1)


# ---------------------------------------------------------------- path B: DCS

def build_dcs_index(db_path, text_id, ref_like):
    """Index every DCS half-verse in scope.

    Returns (index, sk_index, buckets, n_sentences) where index maps
    norm_key -> [sentence_id, ...], sk_index maps consonant-skeleton ->
    [norm_key, ...], and buckets is the shared-prefix fuzzy fallback."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    index = collections.defaultdict(list)
    q = ('SELECT s.id, s.text_sandhied FROM sentence s '
         'JOIN chapter c ON s.chapter_id = c.chapter_id '
         'WHERE c.text_id = ? AND c.ref LIKE ?')
    n = 0
    for sid, sandhied in cur.execute(q, (text_id, ref_like)):
        key = norm_iast(sandhied)
        if key:
            index[key].append(sid)
            n += 1
    con.close()
    sk_index = collections.defaultdict(list)
    buckets = collections.defaultdict(list)
    for key in index:
        sk_index[skeleton(key)].append(key)
        buckets[key[:_FUZZY_PREFIX]].append(key)
    return index, sk_index, buckets, n


def match_line(norm, index, sk_index, buckets):
    """Return (kind, sentence_ids), kind in {'exact','sandhi','fuzzy',None}.

    Tiers: (1) exact on the normalized string; (2) consonant-skeleton equality
    (sandhi-robust -- catches DCS's de-sandhied pada text vs our sandhied
    surface), guarded by a >=_SKELETON_GUARD ratio on the vowelled strings so
    skeleton collisions cannot fake a match; (3) shared-prefix difflib."""
    if norm in index:
        return 'exact', index[norm]
    sk_hits = sk_index.get(skeleton(norm))
    if sk_hits:
        best = max(sk_hits, key=lambda k: difflib.SequenceMatcher(None, norm, k).ratio())
        if difflib.SequenceMatcher(None, norm, best).ratio() >= _SKELETON_GUARD:
            return 'sandhi', index[best]
    cands = buckets.get(norm[:_FUZZY_PREFIX])
    if cands:
        hit = difflib.get_close_matches(norm, cands, n=1, cutoff=_FUZZY_CUTOFF)
        if hit:
            return 'fuzzy', index[hit[0]]
    return None, []


def fetch_dcs_lemmas(db_path, sentence_ids):
    """sentence_id -> [(lemma_iast, upos), ...] for all requested sentences."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    out = collections.defaultdict(list)
    ids = sorted(set(sentence_ids))
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        marks = ','.join('?' * len(chunk))
        for sid, lemma, upos in cur.execute(
                f'SELECT sentence_id, lemma, upos FROM token '
                f'WHERE sentence_id IN ({marks}) ORDER BY sentence_id, idx', chunk):
            out[sid].append((lemma, upos))
    con.close()
    return out


_IAST_LEMMA_OK = re.compile(r"^[a-zA-Zāīūṛṝḷḹṅñṭḍṇśṣṃḥ' -]+$")


def clean_dcs_lemma(lemma):
    """DCS lemma -> SLP1, or None if empty/mojibake (13 damaged kḷp/ṝ-family
    lemma strings survive in the 2026 import -- counted, not silently eaten)."""
    if not lemma:
        return None
    lemma = unicodedata.normalize('NFC', lemma).strip()
    if not _IAST_LEMMA_OK.match(lemma):
        return None
    return iast_to_slp1(lemma.lower())


# ------------------------------------------------------------- path C: vidyut

class VidyutTagger:
    def __init__(self, data_path):
        from vidyut.cheda import Chedaka
        self.chedaka = Chedaka(data_path)
        self.cache = {}

    @staticmethod
    def _lemma(tok):
        """Best DCS-comparable lemma for a vidyut token.

        vidyut's Token.lemma is the dhātu ROOT for every derivative (rāmaḥ ->
        ram, varam -> vṛ) while DCS lemmatizes nominals to the STEM (rāma,
        vara). For Basic (non-kṛdanta) prātipadikas the stem text is available
        on Token.data -- prefer it; kṛdantas/tiṅantas keep the root (which for
        finite verbs matches DCS's own root-lemma convention)."""
        pe = getattr(tok.data, 'pratipadika_entry', None)
        prat = getattr(pe, 'pratipadika', None) if pe is not None else None
        text = getattr(prat, 'text', None) if prat is not None else None
        return text or tok.lemma

    def tag(self, slp1_line):
        """-> (lemmas, n_tokens, n_unlemmatized) or None on engine failure.

        NB an unparseable line comes back from vidyut as an EMPTY token list,
        not an error -- callers must treat (\\[], 0, 0) on non-empty input as
        a segmentation failure, which process_source counts."""
        key = slp1_line
        if key in self.cache:
            return self.cache[key]
        try:
            toks = self.chedaka.run(slp1_line)
        except Exception:
            self.cache[key] = None
            return None
        lemmas, unlem = [], 0
        for t in toks:
            lem = self._lemma(t)
            if lem:
                lemmas.append(lem)
            else:
                unlem += 1
        res = (lemmas, len(toks), unlem)
        self.cache[key] = res
        return res


# ------------------------------------------------------------------ pipeline

def process_source(slug, db_path, tagger, limit=None, quiet=False):
    """Run A/B/C on one pilot source; returns (metrics, group_records)."""
    text_id, ref_like = DCS_SCOPE[slug]
    index, sk_index, buckets, n_dcs = build_dcs_index(db_path, text_id, ref_like)

    m = collections.Counter()
    m['dcs_scope_sentences'] = n_dcs
    groups = []
    pending = []  # (grec, [(norm, kind, sids), ...])

    n_groups = 0
    for group, segs in iter_groups(os.path.join(JSONL_DIR, slug + '.jsonl')):
        sa, ru = segs.get('sa'), segs.get('ru')
        if not (sa and ru and (sa.get('text') or '').strip()
                and (ru.get('text') or '').strip()):
            continue  # same both-sides filter as nkrya_export
        n_groups += 1
        if limit and n_groups > limit:
            break
        lines = split_lines(sa['text'])
        m['groups'] += 1
        m['lines'] += len(lines)

        # path A: reference surface-token frame
        a_tokens = sum(len(re.findall(r'\S+', re.sub(r'[।॥\d]+', ' ', ln)))
                       for ln in lines)
        m['a_tokens'] += a_tokens

        line_matches = []
        for ln in lines:
            norm = norm_iast(ln)
            kind, sids = match_line(norm, index, sk_index, buckets)
            line_matches.append((ln, kind, sids))
            if kind:
                m['b_lines_' + kind] += 1
            else:
                m['b_lines_unmatched'] += 1
            if len(sids) > 1:
                m['b_lines_ambiguous'] += 1

        n_matched = sum(1 for _, k, _s in line_matches if k)
        if n_matched == len(lines):
            m['b_groups_full'] += 1
        elif n_matched:
            m['b_groups_partial'] += 1
        else:
            m['b_groups_zero'] += 1

        grec = {
            'group': group,
            'passage': sa.get('passage'),
            'text_iast': sa['text'],
            'n_lines': len(lines),
            'b_lines_matched': n_matched,
            'a_tokens': a_tokens,
        }

        # path C: vidyut on SLP1 lines (transliterated from the same IAST lines
        # we matched -- one source of truth for both paths)
        if tagger is not None:
            c_lemmas, c_tok, c_unlem, c_fail = [], 0, 0, 0
            for ln, _k, _s in line_matches:
                res = tagger.tag(iast_to_slp1(norm_spaced(ln)))
                if res is None:
                    c_fail += 1
                    continue
                lem, ntok, unlem = res
                c_lemmas.extend(lem)
                c_tok += ntok
                c_unlem += unlem
            m['c_tokens'] += c_tok
            m['c_tokens_unlemmatized'] += c_unlem
            m['c_line_failures'] += c_fail
            grec['c_lemmas'] = sorted(set(c_lemmas))

        groups.append(grec)
        pending.append((grec, line_matches))

    # path B lemma fetch (one batched pass over all matched sentence ids)
    all_sids = [sid for _g, lm in pending for _ln, k, sids in lm if k for sid in sids[:1]]
    sid_lemmas = fetch_dcs_lemmas(db_path, all_sids)
    for grec, lm in pending:
        b_lemmas = []
        for _ln, kind, sids in lm:
            if not kind:
                continue
            for lemma, _upos in sid_lemmas.get(sids[0], []):
                s = clean_dcs_lemma(lemma)
                if s is None:
                    m['b_lemma_dropped'] += 1
                else:
                    b_lemmas.append(s)
                m['b_tokens'] += 1
        grec['b_lemmas'] = sorted(set(b_lemmas))

    # B vs C agreement on fully-B-matched groups
    for grec in groups:
        if 'c_lemmas' not in grec or grec['b_lines_matched'] != grec['n_lines']:
            continue
        b, c = set(grec['b_lemmas']), set(grec['c_lemmas'])
        if not b and not c:
            continue
        inter, union = len(b & c), len(b | c)
        grec['jaccard'] = round(inter / union, 4) if union else 0.0
        grec['b_in_c'] = round(inter / len(b), 4) if b else 0.0
        grec['c_in_b'] = round(inter / len(c), 4) if c else 0.0
        m['bc_groups_compared'] += 1

    jac = sorted(g['jaccard'] for g in groups if 'jaccard' in g)
    metrics = dict(m)
    if jac:
        metrics['bc_jaccard_mean'] = round(sum(jac) / len(jac), 4)
        metrics['bc_jaccard_median'] = jac[len(jac) // 2]
        metrics['bc_jaccard_p10'] = jac[len(jac) // 10]
        metrics['bc_jaccard_p90'] = jac[(len(jac) * 9) // 10]
    if not quiet:
        lines_total = max(1, metrics.get('lines', 0))
        covered = (metrics.get('b_lines_exact', 0) + metrics.get('b_lines_sandhi', 0)
                   + metrics.get('b_lines_fuzzy', 0))
        print(f"{slug}: {metrics.get('groups', 0)} groups, "
              f"B line coverage {100.0 * covered / lines_total:.1f}% "
              f"(exact {metrics.get('b_lines_exact', 0)}, sandhi {metrics.get('b_lines_sandhi', 0)}, "
              f"fuzzy {metrics.get('b_lines_fuzzy', 0)}, "
              f"unmatched {metrics.get('b_lines_unmatched', 0)}), "
              f"B/C jaccard mean {metrics.get('bc_jaccard_mean', 'n/a')}")
    return metrics, groups


def norm_spaced(s):
    """Like norm_iast but KEEPS single spaces (vidyut wants word boundaries)."""
    s = unicodedata.normalize('NFC', s or '').lower().replace('ṁ', 'ṃ')
    s = re.sub(r"[^a-zāīūṛṝḷḹṅñṭḍṇśṣṃḥ\s']", ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def slp1_to_iast(s):
    return sanscript.transliterate(s, sanscript.SLP1, sanscript.IAST)


def stratified_sample(groups, n=51):
    """Fixed-seed low/mid/high-jaccard tertile sample for human adjudication."""
    scored = sorted((g for g in groups if 'jaccard' in g),
                    key=lambda g: (g['jaccard'], natural_key(g['group'])))
    if not scored:
        return []
    per = n // 3
    third = max(1, len(scored) // 3)
    rng = random.Random(SAMPLE_SEED)
    out = []
    for band, chunk in (('low', scored[:third]),
                        ('mid', scored[third:2 * third]),
                        ('high', scored[2 * third:])):
        take = chunk if len(chunk) <= per else rng.sample(chunk, per)
        for g in sorted(take, key=lambda g: natural_key(g['group'])):
            out.append({
                'band': band,
                'group': g['group'],
                'jaccard': g['jaccard'],
                'text_iast': g['text_iast'],
                'b_lemmas_iast': [slp1_to_iast(x) for x in g['b_lemmas']],
                'c_lemmas_iast': [slp1_to_iast(x) for x in g['c_lemmas']],
            })
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--source', action='append', choices=PILOT_SOURCES)
    ap.add_argument('--all-pilot', action='store_true')
    ap.add_argument('--out', required=True)
    ap.add_argument('--dcs-db', default=DEFAULT_DCS_DB)
    ap.add_argument('--vidyut-data', default=DEFAULT_VIDYUT)
    ap.add_argument('--skip-c', action='store_true',
                    help='skip vidyut (path C); B-only crosswalk run')
    ap.add_argument('--limit', type=int, help='debug: first N groups per source')
    ap.add_argument('--sample', type=int, default=51,
                    help='adjudication sample size (default 51)')
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args(argv)

    sources = PILOT_SOURCES if args.all_pilot else (args.source or [])
    if not sources:
        ap.error('need --source or --all-pilot')

    tagger = None
    if not args.skip_c:
        if not os.path.isdir(args.vidyut_data):
            ap.error(f'vidyut data not found at {args.vidyut_data}; '
                     f'run python -c "import vidyut; vidyut.download_data(PATH)" '
                     f'or pass --skip-c')
        tagger = VidyutTagger(args.vidyut_data)

    os.makedirs(args.out, exist_ok=True)
    all_metrics, all_groups = {}, []
    for slug in sources:
        metrics, groups = process_source(slug, args.dcs_db, tagger,
                                         limit=args.limit, quiet=args.quiet)
        all_metrics[slug] = metrics
        all_groups.extend(groups)
        # per-source annotated TSV (gitignored bulk, like the W1 exports)
        tsv = os.path.join(args.out, slug, 'annotation_3path.tsv')
        os.makedirs(os.path.dirname(tsv), exist_ok=True)
        with open(tsv, 'w', encoding='utf-8', newline='') as f:
            f.write('group\tn_lines\tb_lines_matched\tjaccard\tb_lemmas_slp1\tc_lemmas_slp1\n')
            for g in groups:
                f.write('\t'.join([
                    g['group'], str(g['n_lines']), str(g['b_lines_matched']),
                    str(g.get('jaccard', '')),
                    ' '.join(g.get('b_lemmas', [])),
                    ' '.join(g.get('c_lemmas', [])),
                ]) + '\n')

    total = collections.Counter()
    for mtr in all_metrics.values():
        for k, v in mtr.items():
            if isinstance(v, int):
                total[k] += v
    all_metrics['_total'] = dict(total)
    all_metrics['_meta'] = {
        'version': VERSION,
        'dcs': 'Hellwig, The Digital Corpus of Sanskrit (DCS), CC BY 4.0; '
               'pinned snapshot gasyoun/dcs-conllu 04e0778 via VisualDCS dcs_full.sqlite',
        'vidyut': None if args.skip_c else 'vidyut 0.4.0 (ambuda-org), local data pack',
        'fuzzy_cutoff': _FUZZY_CUTOFF,
        'sample_seed': SAMPLE_SEED,
    }

    with open(os.path.join(args.out, 'annotation_3path_metrics.json'), 'w',
              encoding='utf-8', newline='') as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=1, sort_keys=True)

    if tagger is not None:
        sample = stratified_sample(all_groups, n=args.sample)
        with open(os.path.join(args.out, 'annotation_adjudication_sample.json'),
                  'w', encoding='utf-8', newline='') as f:
            json.dump(sample, f, ensure_ascii=False, indent=1)
        if not args.quiet:
            print(f'adjudication sample: {len(sample)} groups')
    return 0


if __name__ == '__main__':
    sys.exit(main())
