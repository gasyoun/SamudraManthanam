r"""vidyut second-opinion morphology, diffed against the DCS gold (H906).

H906's goal: DCS is the **gold** Sanskrit markup source; vidyut is a **second
opinion**, "not the arbiter". [`dcs_align.py`](dcs_align.py) already emits the
gold per-token layer. This module adds the vidyut layer and **diffs it against
DCS** — a committed agreement report (per-token match rate + a categorised
disagreement sample) a reviewer can use to spot where the gold and the analyzer
disagree, without letting vidyut override DCS.

vidyut (`vidyut.cheda.Chedaka`) segments a raw SLP1 verse and analyses each pada;
[vidyut-py](https://github.com/ambuda-org/vidyut) 0.4.0's data pack is
**local-only** (a large `download_data` fetch, ~`chandas/cheda/kosha/prakriya/
sandhi`). Set `VIDYUT_DATA` to override the directory; if it is absent every call
returns `[]`, so — exactly like the DCS layer — the pipeline degrades gracefully
and the diff is simply not produced (never guessed).

The join is **at the group level, on the SLP1 form** (a multiset match): vidyut
and DCS each sandhi-split the verse independently, so their token boundaries can
differ; forms present in both are compared feature-by-feature, forms in only one
side are reported as *segmentation divergence* (not scored as a feature
disagreement). vidyut works in SLP1; DCS forms/lemmas are IAST, so DCS is
transliterated to SLP1 (`indic_transliteration.sanscript`) before the join. Both
sides are mapped into the **DCS feature vocabulary** (UPOS / Nom-Acc-… / Masc-
Fem-Neut / Sing-Dual-Plur) so the comparison is like-for-like.

Deterministic: vidyut's segmentation is fixed for a given input and data pack,
the greedy form-pairing walks tokens in index order, and the report rounds are
explicit — two runs are byte-identical.
"""
import os
import re
import sys

VIDYUT_DATA = os.environ.get(
    'VIDYUT_DATA', os.path.expanduser('~/vidyut-data'))

# --- vidyut → DCS feature vocabulary -----------------------------------------
# vidyut enum member .name → the DCS feat_* string. DCS uses UD-style tags
# (see dcs_full.sqlite token.feat_case/gender/number).
_VIBHAKTI_TO_CASE = {
    'Prathama': 'Nom', 'Dvitiya': 'Acc', 'Trtiya': 'Ins', 'Caturthi': 'Dat',
    'Panchami': 'Abl', 'Sasthi': 'Gen', 'Saptami': 'Loc', 'Sambodhana': 'Voc',
}
_LINGA_TO_GENDER = {'Pum': 'Masc', 'Stri': 'Fem', 'Napumsaka': 'Neut'}
_VACANA_TO_NUMBER = {'Eka': 'Sing', 'Dvi': 'Dual', 'Bahu': 'Plur'}
_PURUSHA_TO_PERSON = {'Prathama': '3', 'Madhyama': '2', 'Uttama': '1'}

# SLP1 alphabet (+ avagraha ' and the nasal ~) — everything else in a raw verse
# (dandas ।॥, ASCII/Devanagari verse digits, stray punctuation) is a separator.
_SLP1_KEEP = set("aAiIuUfFxXeEoOMHkKgGNcCjJYwWqQRtTdDnpPbBmyrlvSzshL'~")


def clean_slp1(text):
    """Reduce a canonical verse's SLP1 surface to analyzer-ready SLP1: dandas,
    ॥n॥ verse markers, digits and stray punctuation become spaces; SLP1 letters
    and avagraha are kept. Whitespace is collapsed."""
    out = []
    for ch in (text or ''):
        out.append(ch if ch in _SLP1_KEEP else ' ')
    return re.sub(r'\s+', ' ', ''.join(out)).strip()


def _enum_name(v):
    """Stable member name for a vidyut grammar enum value ('' if None)."""
    if v is None:
        return ''
    return getattr(v, 'name', '') or ''


def _to_slp1(iast):
    """DCS IAST form/lemma → SLP1 for the join key. Falls back to the input
    unchanged if the transliterator is unavailable (degrade, don't crash)."""
    try:
        from indic_transliteration import sanscript
        return sanscript.transliterate(iast or '', sanscript.IAST, sanscript.SLP1)
    except Exception:  # pragma: no cover - env-dependent
        return iast or ''


def _join_key(slp1_form):
    """Sandhi-surface-normalized key for pairing a DCS token to a vidyut token.

    DCS keeps the printed surface (anusvara `M`, visarga `H`: `evaM`, `pArTAH`);
    vidyut returns the underlying pada form (`evam`, `pArTAs`). Both are the same
    word, so the anusvara/visarga surface variants are folded (`M`→`m`, `H`→`s`)
    before matching — a measured +14pp form-match on the Āraṇyakaparva
    (35%→49%). Display forms in the diff rows keep their real spelling; only the
    match key is folded. (Visarga from underlying `r` — `punar`→`punaH` — still
    won't fold to vidyut's `punar`; those show as a segmentation divergence, not
    a wrong fold.)"""
    return (slp1_form or '').replace('M', 'm').replace('H', 's')


class VidyutAnalyzer:
    """Lazy `Chedaka` wrapper. `available` is False when the data pack is
    absent; one instance is reused across an export run (model load is the
    cost)."""

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or VIDYUT_DATA
        self.available = bool(self.data_dir) and os.path.isdir(self.data_dir)
        self._chedaka = None
        self._load_error = None

    def _cheda(self):
        if self._chedaka is None and self.available:
            try:
                from vidyut.cheda import Chedaka
                self._chedaka = Chedaka(self.data_dir)
            except Exception as exc:  # pragma: no cover - env-dependent
                self._load_error = str(exc)
                self.available = False
                print('vidyut_diff: Chedaka load failed (%s); vidyut layer '
                      'disabled.' % exc, file=sys.stderr)
        return self._chedaka

    def analyze_slp1(self, slp1_text):
        """Analyse a whole SLP1 passage. Returns a list of per-token dicts in
        vidyut's segmentation order, each mapped into the DCS vocabulary:
        {form, lemma, upos, case, gender, number, person} (SLP1 form + lemma)."""
        c = self._cheda()
        if c is None:
            return []
        cleaned = clean_slp1(slp1_text)
        if not cleaned:
            return []
        out = []
        for tok in c.run(cleaned):
            out.append(self._map_token(tok))
        return out

    @staticmethod
    def _map_token(tok):
        form = tok.text or ''
        lemma = tok.lemma or ''
        d = tok.data
        rec = {'form': form, 'lemma': lemma, 'upos': '', 'case': '',
               'gender': '', 'number': '', 'person': ''}
        if d is None:
            return rec  # vidyut could not analyse this pada (unknown)
        kind = type(d).__name__
        if 'Tinanta' in kind:
            rec['upos'] = 'VERB'
            rec['number'] = _VACANA_TO_NUMBER.get(_enum_name(getattr(d, 'vacana', None)), '')
            rec['person'] = _PURUSHA_TO_PERSON.get(_enum_name(getattr(d, 'purusha', None)), '')
        elif 'Subanta' in kind:
            if getattr(d, 'is_avyaya', False):
                # avyaya: indeclinable — DCS marks these ADV/PART/… with no
                # case/gender/number. vidyut sometimes carries a spurious case
                # on an avyaya; drop it so the comparison is fair.
                rec['upos'] = 'ADV'
            else:
                rec['upos'] = 'NOUN'
                rec['case'] = _VIBHAKTI_TO_CASE.get(_enum_name(getattr(d, 'vibhakti', None)), '')
                rec['gender'] = _LINGA_TO_GENDER.get(_enum_name(getattr(d, 'linga', None)), '')
                rec['number'] = _VACANA_TO_NUMBER.get(_enum_name(getattr(d, 'vacana', None)), '')
        return rec


# --- POS coarsening: DCS's fine UPOS and vidyut's 3-way split compared fairly -
_NOMINAL = {'NOUN', 'PROPN', 'ADJ', 'PRON', 'DET', 'NUM'}
_VERBAL = {'VERB', 'AUX'}
# everything else DCS emits (ADV, ADP, PART, CCONJ, SCONJ, INTJ, X, …) is
# "indeclinable" for the coarse comparison.


def _coarse_pos(upos):
    if upos in _NOMINAL:
        return 'nominal'
    if upos in _VERBAL:
        return 'verbal'
    return 'indecl'


def _agree(a, b):
    """Feature agreement over a matched pair — only counted when BOTH sides
    carry a value (an empty on either side is 'not comparable', not a miss)."""
    if not a or not b:
        return None
    return a == b


def diff_group(dcs_tokens, slp1_text, analyzer):
    """Diff one group's DCS gold tokens against vidyut's analysis of the same
    SLP1 passage. Returns (rows, counts) where rows are per matched/unmatched
    token and counts aggregate the group.

    Match: greedy multiset pairing on the SLP1 form (DCS forms transliterated to
    SLP1). Feature agreement (lemma/upos/case/gender/number) is scored only over
    matched pairs, and only where both sides carry the feature."""
    vid = analyzer.analyze_slp1(slp1_text)
    # index vidyut tokens by the sandhi-folded join key → queue of positions
    # (multiset match, so repeated forms in a verse each get paired once)
    from collections import defaultdict, deque
    vid_by_form = defaultdict(deque)
    for i, t in enumerate(vid):
        vid_by_form[_join_key(t['form'])].append(i)
    used = [False] * len(vid)
    rows = []
    matched = 0
    lemma_ok = lemma_cmp = 0
    pos_ok = pos_cmp = 0
    case_ok = case_cmp = 0
    gen_ok = gen_cmp = 0
    num_ok = num_cmp = 0
    for g in dcs_tokens:
        dform = _to_slp1(g.get('form', ''))
        dlemma = _to_slp1(g.get('lemma', ''))
        q = vid_by_form.get(_join_key(dform))
        if q:
            vi = q.popleft()
            used[vi] = True
            v = vid[vi]
            matched += 1
            la = _agree(dlemma, v['lemma'])
            pa = _agree(_coarse_pos(g.get('upos', '')),
                        _coarse_pos(v['upos']) if v['upos'] else '')
            ca = _agree(g.get('case', ''), v['case'])
            ga = _agree(g.get('gender', ''), v['gender'])
            na = _agree(g.get('number', ''), v['number'])
            if la is not None:
                lemma_cmp += 1; lemma_ok += int(la)
            if pa is not None:
                pos_cmp += 1; pos_ok += int(pa)
            if ca is not None:
                case_cmp += 1; case_ok += int(ca)
            if ga is not None:
                gen_cmp += 1; gen_ok += int(ga)
            if na is not None:
                num_cmp += 1; num_ok += int(na)
            rows.append({
                'status': 'matched', 'form': dform,
                'dcs_lemma': dlemma, 'vid_lemma': v['lemma'],
                'dcs_upos': g.get('upos', ''), 'vid_upos': v['upos'],
                'dcs_case': g.get('case', ''), 'vid_case': v['case'],
                'dcs_gender': g.get('gender', ''), 'vid_gender': v['gender'],
                'dcs_number': g.get('number', ''), 'vid_number': v['number'],
                'lemma_agree': la, 'pos_agree': pa, 'case_agree': ca,
                'gender_agree': ga, 'number_agree': na,
            })
        else:
            rows.append({'status': 'dcs_only', 'form': dform,
                         'dcs_lemma': dlemma, 'dcs_upos': g.get('upos', ''),
                         'dcs_case': g.get('case', ''),
                         'dcs_gender': g.get('gender', ''),
                         'dcs_number': g.get('number', '')})
    for i, t in enumerate(vid):
        if not used[i]:
            rows.append({'status': 'vidyut_only', 'form': t['form'],
                         'vid_lemma': t['lemma'], 'vid_upos': t['upos'],
                         'vid_case': t['case'], 'vid_gender': t['gender'],
                         'vid_number': t['number']})
    counts = {
        'dcs_tokens': len(dcs_tokens), 'vidyut_tokens': len(vid),
        'matched': matched,
        'dcs_only': sum(1 for r in rows if r['status'] == 'dcs_only'),
        'vidyut_only': sum(1 for r in rows if r['status'] == 'vidyut_only'),
        'lemma_ok': lemma_ok, 'lemma_cmp': lemma_cmp,
        'pos_ok': pos_ok, 'pos_cmp': pos_cmp,
        'case_ok': case_ok, 'case_cmp': case_cmp,
        'gender_ok': gen_ok, 'gender_cmp': gen_cmp,
        'number_ok': num_ok, 'number_cmp': num_cmp,
    }
    return rows, counts


def _rate(ok, cmp_):
    return (ok / cmp_) if cmp_ else None


def aggregate(all_counts):
    """Sum per-group counts into a source-level agreement summary with rates."""
    keys = ('dcs_tokens', 'vidyut_tokens', 'matched', 'dcs_only', 'vidyut_only',
            'lemma_ok', 'lemma_cmp', 'pos_ok', 'pos_cmp', 'case_ok', 'case_cmp',
            'gender_ok', 'gender_cmp', 'number_ok', 'number_cmp')
    total = {k: 0 for k in keys}
    for c in all_counts:
        for k in keys:
            total[k] += c.get(k, 0)
    total['form_match_rate'] = _rate(total['matched'], total['dcs_tokens'])
    total['lemma_agree_rate'] = _rate(total['lemma_ok'], total['lemma_cmp'])
    total['pos_agree_rate'] = _rate(total['pos_ok'], total['pos_cmp'])
    total['case_agree_rate'] = _rate(total['case_ok'], total['case_cmp'])
    total['gender_agree_rate'] = _rate(total['gender_ok'], total['gender_cmp'])
    total['number_agree_rate'] = _rate(total['number_ok'], total['number_cmp'])
    return total
