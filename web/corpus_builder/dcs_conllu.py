r"""H6371 -- DCS path-B CoNLL-U layer (Wave 7).

Parses the pinned DCS CoNLL-U distribution (gasyoun/dcs-conllu, CC BY 4.0 --
the same snapshot that built the VisualDCS ``dcs_full.sqlite`` of W2) and
exposes its sentences through the W2 three-tier text-keyed crosswalk
(``nkrya_annotate.py``): every DCS sentence is indexed under the aggressive
``norm_iast`` key of its sandhied ``# text`` surface, so OUR half-verse lines
match at tier 1 exact / tier 2 sandhi-skeleton / tier 3 fuzzy exactly as in
W2. This module is the data half of the 4th emitter (``nkrya_export.py
--conllu``); the serialization half lives there.

Why CoNLL-U files instead of the sqlite: the W2 crosswalk ran against
``dcs_full.sqlite`` (920 MB, local-only, Mac seat). The public pinned mirror
carries the SAME annotation (lemma/UPOS/FEATS per desandhied word) already in
CoNLL-U shape -- including the sandhi structure this wave needs: the sandhied
surface is the ``n-m`` multiword-token range row, the desandhied words are the
interior rows. Cloning the needed books is one sparse checkout (see
DCS_CONLLU_GLOBS below), no VPS dependency, reproducible anywhere.

DCS -> UD UPOS mapping (explicit, audited 29-10-2026 over the pilot books:
36,986 sentences / 252,476 words). DCS tags observed: NOUN VERB PRON ADJ ADV
PART CONJ NUM SCONJ ADP INTJ. All are valid UD UPOS except ``CONJ`` (the
pre-UD tag; UD splits coordinating CCONJ from subordinating SCONJ, and DCS
already tags subordinators SCONJ) -> ``CCONJ``. Any tag NOT in DCS_UPOS_MAP is
emitted VERBATIM and counted as unmapped (``stats['unmapped_upos']``) plus
flagged by ``conllu_validate.py`` -- never silently coerced.

DCS feature extensions are passed through verbatim and inventoried in the
coverage report (also never coerced): ``Formation`` (verb formation class,
DCS-specific key), ``Case=Cpd`` (compound-member case, DCS-specific value),
``Tense=Impf``/``Mood=Cond``/``Mood=Prec`` (attested but outside the UD
default inventory).

Data layout of the sibling clone (sparse, pilot scope only):

  git clone --depth 1 --filter=blob:none --sparse \\
      https://github.com/gasyoun/dcs-conllu.git dcs-conllu
  git -C dcs-conllu sparse-checkout set --no-cone \\
      '/files/Mahābhārata/*MBh, 3, *.conllu' \\
      '/files/Rāmāyaṇa/*Rām, Bā, *.conllu' \\
      '/files/Rāmāyaṇa/*Rām, Ay, *.conllu' \\
      '/files/Rāmāyaṇa/*Rām, Ār, *.conllu'
"""
import collections
import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))

DCS_CONLLU_DIR = os.environ.get(
    'DCS_CONLLU',
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))),
                 'dcs-conllu', 'files'))

# our source slug -> (subdirectory, filename infix) in the dcs-conllu clone.
# Mirrors nkrya_annotate.DCS_SCOPE (same pilot texts, same book granularity).
DCS_CONLLU_GLOBS = {
    '03_mahabharata-aranyakaparva': ('Mahābhārata', 'MBh, 3, '),
    '01_ramayana-balakanda': ('Rāmāyaṇa', 'Rām, Bā, '),
    '02_ramayana-ayodhyakanda': ('Rāmāyaṇa', 'Rām, Ay, '),
    '03_ramayana-aranyakanda': ('Rāmāyaṇa', 'Rām, Ār, '),
}

# The 17 UD UPOS tags (validation target; anything else is non-UD).
UD_UPOS = frozenset(('ADJ ADP ADV AUX CCONJ DET INTJ NOUN NUM PART PRON '
                     'PROPN PUNCT SCONJ SYM VERB X').split())

# DCS tag -> UD UPOS. Identity rows are explicit ON PURPOSE: the table is the
# audit artifact the W7 handoff demands ("explicit DCS-to-UPOS mapping table
# with unmapped tags flagged, never silently coerced"). Observed 29-10-2026.
DCS_UPOS_MAP = {
    'NOUN': 'NOUN',
    'VERB': 'VERB',
    'PRON': 'PRON',
    'ADJ': 'ADJ',
    'ADV': 'ADV',
    'PART': 'PART',
    'NUM': 'NUM',
    'SCONJ': 'SCONJ',
    'ADP': 'ADP',
    'INTJ': 'INTJ',
    'CONJ': 'CCONJ',   # pre-UD coordinating tag; DCS tags subordinators SCONJ
}

# DCS feature extensions passed through verbatim (documented, not coerced).
DCS_FEAT_EXTENSIONS = {
    'Formation',        # verb formation class (peri/root/them/s/is/red/sa)
}
DCS_FEATVAL_EXTENSIONS = {
    ('Case', 'Cpd'),    # compound-member case marker
}


def map_upos(tag):
    """(mapped_upos, unmapped_flag). An unmapped tag maps to itself verbatim
    and is flagged -- never coerced to X or dropped. ``_``/empty are the
    format's own unspecified markers: passed through, not counted as
    unmapped (the validator reports a W1 only for non-``_`` tags)."""
    if tag in ('', '_'):
        return tag, False
    if tag in DCS_UPOS_MAP:
        return DCS_UPOS_MAP[tag], False
    return tag, True


class Sentence:
    """One DCS CoNLL-U sentence (one pāda = half-verse)."""

    __slots__ = ('sent_id', 'sent_counter', 'sent_subcounter', 'chapter',
                 'text', 'rows')

    def __init__(self, sent_id, sent_counter, sent_subcounter, chapter,
                 text, rows):
        self.sent_id = sent_id
        self.sent_counter = sent_counter
        self.sent_subcounter = sent_subcounter
        self.chapter = chapter
        self.text = text
        self.rows = rows          # list of 10-column lists, verbatim


def parse_conllu_file(path):
    """Parse one dcs-conllu chapter file -> [Sentence, ...] in file order.

    Tolerant by design (this is a read of a pinned external distribution):
    structural oddities in the source are carried through, not guessed at --
    our own emitted files are what ``conllu_validate.py`` polices.
    """
    subdir = os.path.basename(os.path.dirname(path))
    sents = []
    comments, rows = [], []
    sent_id = counter = subcounter = None
    text = ''

    def flush():
        if rows:
            sents.append(Sentence(sent_id, counter, subcounter,
                                  '%s/%s' % (subdir, os.path.basename(path)),
                                  text, rows))

    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.strip():
                flush()
                comments, rows = [], []
                sent_id = counter = subcounter = None
                text = ''
                continue
            if line.startswith('#'):
                m = re.match(r'#\s*sent_id\s*=\s*(\S+)', line)
                if m:
                    sent_id = m.group(1)
                m = re.match(r'#\s*sent_counter\s*=\s*(\S+)', line)
                if m:
                    counter = m.group(1)
                m = re.match(r'#\s*sent_subcounter\s*=\s*(\S+)', line)
                if m:
                    subcounter = m.group(1)
                m = re.match(r'#\s*text\s*=\s*(.*)$', line)
                if m:
                    text = m.group(1).strip()
                continue
            rows.append(line.split('\t'))
    flush()
    return sents


class DcsConllu:
    """Read-only dcs-conllu lookup with the W2 three-tier crosswalk index.

    One instance is reused across a whole export run; per-slug indexes are
    built once (sorted file iteration -> deterministic). ``available`` is
    False when no pilot chapter file is found under dcs_dir.
    """

    def __init__(self, dcs_dir=DCS_CONLLU_DIR):
        self.dcs_dir = dcs_dir
        self._cache = {}    # slug -> (index, sk_index, buckets, n_sentences)

    @staticmethod
    def _files_for(slug, dcs_dir):
        sub, infix = DCS_CONLLU_GLOBS[slug]
        return sorted(glob.glob(os.path.join(dcs_dir, sub, '*' + infix + '*.conllu')))

    def available_for(self, slug):
        return bool(self._files_for(slug, self.dcs_dir))

    @property
    def available(self):
        return any(self.available_for(s) for s in DCS_CONLLU_GLOBS)

    def index_for(self, slug):
        """(index, sk_index, buckets, n_sentences) for one slug, built once.

        index: norm_iast(text) -> [Sentence, ...] sorted by sent_id (DCS
        repeats half-verses; smallest sent_id wins deterministically).
        sk_index / buckets: the W2 tier-2/tier-3 structures, same shapes
        nkrya_annotate.match_line expects.
        """
        if slug in self._cache:
            return self._cache[slug]
        import nkrya_annotate as na
        by_key = collections.defaultdict(list)
        n = 0
        for path in self._files_for(slug, self.dcs_dir):
            for s in parse_conllu_file(path):
                key = na.norm_iast(s.text)
                if not key:
                    continue
                by_key[key].append(s)
                n += 1
        index = {k: sorted(v, key=lambda s: str(s.sent_id))
                 for k, v in by_key.items()}
        sk_index = collections.defaultdict(list)
        buckets = collections.defaultdict(list)
        for key in index:
            sk_index[na.skeleton(key)].append(key)
            buckets[key[:na._FUZZY_PREFIX]].append(key)
        self._cache[slug] = (index, sk_index, buckets, n)
        return self._cache[slug]

    def match(self, slug, line):
        """(tier, sentence, ambiguous) for one of OUR IAST half-verse lines.

        tier in {'exact','sandhi','fuzzy',None}; the W2 tiers via the W2
        matcher. Multiple DCS sentences under one key -> smallest sent_id,
        ambiguous=True (counted, never hidden)."""
        import nkrya_annotate as na
        index, sk_index, buckets, _n = self.index_for(slug)
        kind, hits = na.match_line(na.norm_iast(line), index, sk_index, buckets)
        if not kind or not hits:
            return None, None, False
        sent = hits[0]
        return kind, sent, len(hits) > 1
