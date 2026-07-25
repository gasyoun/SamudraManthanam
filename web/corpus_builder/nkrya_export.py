#!/usr/bin/env python
r"""H754 -- НКРЯ parallel-corpus triple export (para-XML + TMX 1.4b + TSV).

Reads the canonical verse-aligned JSONL for a pilot source
(`web/corpus_builder/jsonl/<slug>.jsonl`), groups by the alignment `group` key,
keeps only groups that carry BOTH a Sanskrit (`seg=sa`) and a Russian
translation (`seg=ru`) side with non-empty text, and emits three byte-identical,
timestamp-free artifacts per source:

  1. НКРЯ parallel-corpus **para-XML** (best guess -- see "НКРЯ XML MODEL" below)
  2. **TMX 1.4b** (one <tu> per pair, tuv xml:lang="ru"/"sa")
  3. **TSV** (group_id, sa_iast, sa_slp1, ru, flags)

The alignment is already solved upstream (ALIGNMENT_SPEC.md): one `group` =
Sanskrit verse + its Russian translation siblings. This module is a pure
consumer -- no aligner, no HTML re-parse, no LLM, no clock inside the artifact,
so the same JSONL yields byte-identical output.

Segments that are NOT exported as pairs (counted + flagged in the report, never
silently dropped):
  * `seg=ru` groups with no Sanskrit side  -> monolingual-RU (report `mono_ru`)
  * `seg=sa` groups with no Russian side    -> untranslated  (report `mono_sa`)
  * `seg=comm1..commN`                       -> Russian commentary (report `commentary`)

Text is emitted VERBATIM from the JSONL `text` field (the canonical verse,
dandas + ॥n॥ verse numbers preserved) -- NOT the cleaned/token-stripped form
build_l0.py uses for word alignment. A faithful parallel corpus keeps the verse
surface intact; the SLP1 machine key rides along as an attribute/column/prop.

Prior art consumed (H754 handoff): the pair-extraction + TMX skeleton mirror
SanskritLexicography/RussianTranslation/src/build_l0.py + build_tmx.py. New here:
per-source output, the НКРЯ para-XML emitter, the TSV emitter, and the
bibliographic header from each source's `<slug>.meta.json` sidecar.

RIGHTS: the pilot sources are in-copyright modern Russian academic translations;
the export artifacts (XML/TMX/TSV) are gitignored exactly like the L0/L1 TM.
Only this generator + PILOT_VALIDATION.md are committed. No public release before
per-translator clearance (/publish-safety-check).

НКРЯ XML MODEL (BEST GUESS -- the file most likely revised after НКРЯ answers the
format question, roadmap Wave 5). Assumptions, each explicit so a reviewer can
diff them against the real НКРЯ parallel schema:
  * Root <document corpus="parallel" subcorpus="sanskrit-russian"> with a
    <header> of bibliographic metadata and a <body> of alignment units.
  * One alignment unit = <para id=GROUP align="1-1">, holding exactly two <se>
    (sentence/segment) children: the Sanskrit se first, then the Russian se
    (source-before-target, the НКРЯ convention for a source-language corpus).
  * Sanskrit se: <se lang="san" script="iast" slp1="SLP1">IAST</se> -- the
    printed IAST surface is the element text, the SLP1 machine key an attribute.
  * Russian se: <se lang="ru">...</se>.
  * `lang` values follow the H754 spec literally ("san"/"ru" in XML; the TMX
    layer uses ISO "sa"/"ru" in xml:lang). НКРЯ's own tag set may differ (e.g.
    "rus") -- one place to change if so (LANG_SA_XML / LANG_RU_XML).

Usage:
  python nkrya_export.py --source 03_mahabharata-aranyakaparva --out nkrya-parallel/export
  python nkrya_export.py --all-pilot --out nkrya-parallel/export
  python nkrya_export.py --all-pilot --out DIR --quiet
"""
import argparse
import collections
import json
import os
import re
import sys
from xml.sax.saxutils import escape, quoteattr

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

VERSION = '0.1.0'

HERE = os.path.dirname(os.path.abspath(__file__))
JSONL_DIR = os.path.join(HERE, 'jsonl')

PILOT_SOURCES = [
    '03_mahabharata-aranyakaparva',
    '01_ramayana-balakanda',
    '02_ramayana-ayodhyakanda',
    '03_ramayana-aranyakanda',
]

# lang tokens -- one place to change if НКРЯ's real schema uses different codes.
LANG_SA_XML = 'san'
LANG_RU_XML = 'ru'
LANG_SA_TMX = 'sa'   # ISO 639-1 for the TMX xml:lang
LANG_RU_TMX = 'ru'

CYR = re.compile('[Ѐ-ӿԀ-ԯⷠ-ⷿꙀ-ꚟ]')
_NATKEY = re.compile(r'(\d+)')


def has_cyr(s):
    return bool(s) and bool(CYR.search(s))


def natural_key(s):
    """Deterministic natural-order key for a canonical group id so 3.1.2 sorts
    before 3.1.10. Splits into (text, int, text, int, ...) chunks."""
    parts = _NATKEY.split(s or '')
    return tuple((int(p) if p.isdigit() else p) for p in parts)


def iter_groups(path):
    """Yield (group, {seg: record}) for one work's JSONL in file order, skipping
    deleted rows. Mirrors build_l0.iter_groups."""
    by_group = collections.OrderedDict()
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get('deleted'):
                continue
            by_group.setdefault(e.get('group'), {})[e.get('seg')] = e
    for g, d in by_group.items():
        yield g, d


def _txt(rec):
    return (rec.get('text') or '').strip() if rec else ''


def group_flags(group, d):
    """Small, documented flag set carried on every emitted pair.
      range : the passage spans several verses (e.g. 3.1.1-7)
      comm  : the group carries >=1 Russian commentary note (excluded from pairs)
    """
    flags = []
    sa = d.get('sa') or {}
    passage = sa.get('passage') or group.split(':', 1)[-1]
    if '-' in passage:
        flags.append('range')
    if any(seg and seg.startswith('comm') for seg in d):
        flags.append('comm')
    return flags


def classify(path):
    """Single pass over a source: returns (pairs, stats).

    pairs: list of dicts {group, sa_iast, sa_slp1, ru, flags} for groups with
           both a non-empty Sanskrit and Russian side, sorted by natural group id.
    stats: counts of pairs / mono_ru / mono_sa / commentary / empty_side.
    """
    pairs = []
    mono_ru = mono_sa = commentary = empty_side = 0
    for group, d in iter_groups(path):
        sa = d.get('sa')
        ru = d.get('ru')
        sa_txt = _txt(sa)
        ru_txt = _txt(ru)
        # count commentary notes (never exported as pairs)
        commentary += sum(1 for seg in d if seg and seg.startswith('comm'))
        # a group that DECLARES a side (key present) but left its text empty is a
        # defect -> flagged, never emitted, and kept distinct from a side that is
        # genuinely absent (no key at all -> that's mono_ru / mono_sa below).
        declared_empty = (sa is not None and not sa_txt) or (ru is not None and not ru_txt)
        if declared_empty:
            empty_side += 1
        if sa_txt and ru_txt:
            pairs.append({
                'group': group,
                'sa_iast': sa_txt,
                'sa_slp1': (sa.get('slp1') or '').strip(),
                'ru': ru_txt,
                'flags': group_flags(group, d),
            })
        elif declared_empty:
            pass  # already counted as empty_side; not a clean monolingual unit
        elif ru_txt and sa is None:
            mono_ru += 1   # Russian-only: no Sanskrit side present at all
        elif sa_txt and ru is None:
            mono_sa += 1   # untranslated: no Russian side present at all
    pairs.sort(key=lambda p: natural_key(p['group']))
    stats = {
        'pairs': len(pairs),
        'mono_ru': mono_ru,
        'mono_sa': mono_sa,
        'commentary': commentary,
        'empty_side': empty_side,
    }
    return pairs, stats


# ---------------------------------------------------------------------------
# emitters (all deterministic, no clock)
# ---------------------------------------------------------------------------

def load_meta(slug, meta_dir=HERE):
    path = os.path.join(meta_dir, slug + '.meta.json')
    if os.path.exists(path):
        return json.load(open(path, encoding='utf-8'))
    return {'slug': slug, 'needs_review': True}


def _hdr_field(tag, val):
    if val in (None, ''):
        return ''
    return '    <%s>%s</%s>\n' % (tag, escape(str(val)), tag)


def nkrya_xml(slug, pairs, meta, inline_ana=False, dcs=None):
    """НКРЯ parallel-corpus para-XML (best guess -- see module docstring).

    With `inline_ana`, each `<se>` carries per-token НКРЯ `<w><ana lex= gr=/>`
    markup instead of plain text — the shared H905/H906 scheme (see
    `inline_ana.py`). The Russian side is annotated whenever pymorphy3 is
    available; the Sanskrit side only for verses whose DCS gold attaches to the
    surface words end-to-end, and stays plain text otherwise — never guessed.
    Returns the XML string; `ana_stats` is filled in place when passed."""
    out = ['<?xml version="1.0" encoding="UTF-8"?>\n']
    out.append('<document corpus="parallel" subcorpus="sanskrit-russian" '
               'slug=%s>\n' % quoteattr(slug))
    out.append('  <header>\n')
    out.append(_hdr_field('title', meta.get('title_ru')))
    out.append(_hdr_field('title_orig', meta.get('title_en')))
    out.append(_hdr_field('author', meta.get('author_orig')))
    out.append(_hdr_field('translator', meta.get('credit')))
    out.append(_hdr_field('translator_role', meta.get('credit_role')))
    out.append(_hdr_field('publisher', meta.get('publisher')))
    out.append(_hdr_field('imprint', meta.get('imprint')))
    out.append(_hdr_field('year', meta.get('year')))
    out.append(_hdr_field('series', meta.get('series')))
    out.append(_hdr_field('lang_source', 'san'))
    out.append(_hdr_field('lang_target', 'rus'))
    out.append(_hdr_field('date_source_ce', meta.get('composition_date_ce')))
    out.append(_hdr_field('period', meta.get('period')))
    out.append(_hdr_field('provenance', meta.get('provenance')))
    out.append(_hdr_field('rights', meta.get('rights')))
    out.append(_hdr_field('bibliography_status', meta.get('bibliography_status')))
    out.append('  </header>\n')
    out.append('  <body>\n')
    ia = ru_mod = None
    stats = {'sa_paras': 0, 'sa_inline': 0, 'ru_paras': 0, 'ru_inline': 0}
    if inline_ana:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import inline_ana as ia
        import ru_morph as ru_mod
    for p in pairs:
        flags = ' flags=%s' % quoteattr(','.join(p['flags'])) if p['flags'] else ''
        out.append('    <para id=%s align="1-1"%s>\n' % (quoteattr(p['group']), flags))
        sa_body, ru_body = escape(p['sa_iast']), escape(p['ru'])
        sa_attr = ''
        if inline_ana:
            stats['sa_paras'] += 1
            stats['ru_paras'] += 1
            if dcs is not None and dcs.available:
                passage = p['group'].split(':', 1)[1] if ':' in p['group'] else ''
                gold = dcs.gold_tokens(slug, passage)
                marked = ia.annotate_sa(p['sa_iast'], gold) if gold else None
                if marked is not None:
                    sa_body = marked
                    sa_attr = ' ana="dcs-ud"'
                    stats['sa_inline'] += 1
            if ru_mod.available():
                ru_body = ia.annotate_ru(p['ru'], ru_mod.analyze(p['ru']))
                stats['ru_inline'] += 1
        ru_attr = ' ana="opencorpora"' if inline_ana and ru_body != escape(p['ru']) else ''
        out.append('      <se lang="%s" script="iast" slp1=%s%s>%s</se>\n'
                   % (LANG_SA_XML, quoteattr(p['sa_slp1']), sa_attr, sa_body))
        out.append('      <se lang="%s"%s>%s</se>\n'
                   % (LANG_RU_XML, ru_attr, ru_body))
        out.append('    </para>\n')
    out.append('  </body>\n')
    out.append('</document>\n')
    nkrya_xml.last_ana_stats = stats
    return ''.join(out)


def tmx(slug, pairs, meta):
    """TMX 1.4b -- one <tu> per pair, no creationdate (determinism)."""
    out = ['<?xml version="1.0" encoding="UTF-8"?>\n']
    out.append('<tmx version="1.4">\n')
    out.append(' <header\n')
    out.append('   creationtool="nkrya_export.py"\n')
    out.append('   creationtoolversion=%s\n' % quoteattr(VERSION))
    out.append('   segtype="block"\n')
    out.append('   o-tmf="jsonl"\n')
    out.append('   adminlang="en"\n')
    out.append('   srclang=%s\n' % quoteattr(LANG_SA_TMX))
    out.append('   datatype="plaintext"\n')
    out.append('   o-encoding="UTF-8">\n')
    out.append('  <prop type="slug">%s</prop>\n' % escape(slug))
    out.append('  <prop type="title">%s</prop>\n' % escape(str(meta.get('title_ru') or slug)))
    out.append('  <prop type="translator">%s</prop>\n' % escape(str(meta.get('credit') or '')))
    out.append('  <prop type="rights">%s</prop>\n' % escape(str(meta.get('rights') or '')))
    out.append(' </header>\n')
    out.append(' <body>\n')
    for p in pairs:
        out.append('  <tu tuid=%s segtype="block">\n' % quoteattr(p['group']))
        out.append('   <prop type="group">%s</prop>\n' % escape(p['group']))
        out.append('   <prop type="slp1">%s</prop>\n' % escape(p['sa_slp1']))
        if p['flags']:
            out.append('   <prop type="flags">%s</prop>\n' % escape(','.join(p['flags'])))
        out.append('   <tuv xml:lang="%s"><seg>%s</seg></tuv>\n'
                   % (LANG_SA_TMX, escape(p['sa_iast'])))
        out.append('   <tuv xml:lang="%s"><seg>%s</seg></tuv>\n'
                   % (LANG_RU_TMX, escape(p['ru'])))
        out.append('  </tu>\n')
    out.append(' </body>\n')
    out.append('</tmx>\n')
    return ''.join(out)


def _tsv_cell(s):
    # TSV: strip tab/newline from cell content so the row shape is invariant.
    return re.sub(r'[\t\r\n]+', ' ', s or '')


def tsv(pairs):
    """TSV: group_id, sa_iast, sa_slp1, ru, flags -- one row per pair."""
    out = ['group_id\tsa_iast\tsa_slp1\tru\tflags\n']
    for p in pairs:
        out.append('\t'.join([
            _tsv_cell(p['group']),
            _tsv_cell(p['sa_iast']),
            _tsv_cell(p['sa_slp1']),
            _tsv_cell(p['ru']),
            ','.join(p['flags']),
        ]) + '\n')
    return ''.join(out)


def sa_units(path):
    """Every group carrying a non-empty Sanskrit side, translated or not —
    {group, sa_iast, sa_slp1}, in natural group order.

    Deliberately NOT derived from classify()'s `pairs`. A pair requires BOTH a
    Sanskrit and a Russian side, because it models the *bilingual* unit; but the
    Sanskrit morphology layer depends only on the Sanskrit side, so binding it to
    `pairs` silently discarded every untranslated source. That is exactly what
    happened to the GRETIL-ingested Rāmāyaṇa yuddha/uttarakāṇḍa (H906): both are
    Sanskrit-only, so they produced zero pairs and were written up as "0% DCS
    coverage — the ref mapper doesn't parse their passage convention", when in
    fact their passages align to DCS at 100.0% / 99.9%. Keeping this list
    separate is the fix and the guard against the same class of bug.
    """
    units = []
    for group, d in iter_groups(path):
        sa = d.get('sa')
        sa_txt = _txt(sa)
        if not sa_txt:
            continue
        units.append({
            'group': group,
            'sa_iast': sa_txt,
            'sa_slp1': (sa.get('slp1') or '').strip(),
        })
    units.sort(key=lambda u: natural_key(u['group']))
    return units


def sa_morph_tsv(units, slug, dcs):
    """Per-token Sanskrit morphology layer, anchored on DCS gold (H906): one row
    per DCS-aligned SA token — group_id, verse, tok_index, form, lemma, upos,
    case, gender, number. Verses DCS does not cover produce no rows (reported as
    a coverage gap). Additive companion; the inline НКРЯ `<w><ana/>` fold is the
    shared H905/H906 per-token scheme, deferred until agreed.

    Takes SA units (see sa_units), not bilingual pairs — an untranslated
    Sanskrit source still gets its gold morphology."""
    out = ['group_id\tverse\ttok_index\tform\tlemma\tupos\tcase\tgender\tnumber\n']
    for p in units:
        passage = p['group'].split(':', 1)[1] if ':' in p['group'] else ''
        for t in dcs.gold_tokens(slug, passage):
            out.append('\t'.join([
                _tsv_cell(p['group']), str(t['verse']), str(t['idx']),
                _tsv_cell(t['form']), _tsv_cell(t['lemma']), t['upos'],
                t['case'], t['gender'], t['number'],
            ]) + '\n')
    return ''.join(out)


def ru_morph_tsv(pairs):
    """Per-token Russian morphology layer (H905): one row per RU token, in
    (pair, text) order — group_id, tok_index, surface, lemma, pos, case,
    number. Deterministic (see ru_morph.analyze). Additive companion to the
    para-XML/TMX/TSV; the inline НКРЯ `<w><ana/>` fold is the H906-coordinated
    step."""
    import ru_morph
    out = ['group_id\ttok_index\tsurface\tlemma\tpos\tcase\tnumber\n']
    for p in pairs:
        for i, t in enumerate(ru_morph.analyze(p['ru'])):
            out.append('\t'.join([
                _tsv_cell(p['group']), str(i),
                _tsv_cell(t['surface']), _tsv_cell(t['lemma']),
                t['pos'], t['case'], t['number'],
            ]) + '\n')
    return ''.join(out)


def vidyut_diff_tsv(units, slug, dcs, analyzer):
    """The vidyut second-opinion diff against DCS gold (H906): per DCS-aligned
    group, run vidyut on the same SLP1 passage and pair tokens on the sandhi-
    folded form. Returns (tsv_text, agg) — the per-token TSV plus the aggregate
    agreement summary (form-match rate + per-feature agreement) that feeds the
    committed report. DCS is gold, vidyut is the second opinion; disagreements
    are reported, never used to override DCS.

    Takes SA units (see sa_units), not bilingual pairs — same reason as
    sa_morph_tsv."""
    import vidyut_diff
    out = ['group_id\tstatus\tform\tdcs_lemma\tvid_lemma\tdcs_upos\tvid_upos\t'
           'dcs_case\tvid_case\tdcs_gender\tvid_gender\tdcs_number\tvid_number\t'
           'lemma_agree\tpos_agree\tcase_agree\tgender_agree\tnumber_agree\n']
    all_counts = []
    for p in units:
        passage = p['group'].split(':', 1)[1] if ':' in p['group'] else ''
        gold = dcs.gold_tokens(slug, passage)
        if not gold:
            continue
        rows, counts = vidyut_diff.diff_group(gold, p['sa_slp1'], analyzer)
        all_counts.append(counts)
        for r in rows:
            out.append('\t'.join([
                _tsv_cell(p['group']), r['status'], _tsv_cell(r.get('form', '')),
                _tsv_cell(r.get('dcs_lemma', '')), _tsv_cell(r.get('vid_lemma', '')),
                r.get('dcs_upos', ''), r.get('vid_upos', ''),
                r.get('dcs_case', ''), r.get('vid_case', ''),
                r.get('dcs_gender', ''), r.get('vid_gender', ''),
                r.get('dcs_number', ''), r.get('vid_number', ''),
                _agree_cell(r.get('lemma_agree')), _agree_cell(r.get('pos_agree')),
                _agree_cell(r.get('case_agree')), _agree_cell(r.get('gender_agree')),
                _agree_cell(r.get('number_agree')),
            ]) + '\n')
    return ''.join(out), vidyut_diff.aggregate(all_counts)


def _agree_cell(v):
    """TSV cell for a tri-state agreement flag: 1 / 0 / '' (not comparable)."""
    return '' if v is None else ('1' if v else '0')


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def _write(path, text):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def _sanskritisms_artifact(slug, jsonl_path, sanskritisms_ctx):
    """H760 Wave 3 wiring: the per-source proper-name index, added into the
    same export bundle as the para-XML/TMX/TSV triple. Import is local so
    nkrya_export has no hard dependency on the sanskritisms package unless
    --with-sanskritisms is actually requested."""
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    from sanskritisms.extract import ExtractionContext, build_name_index, extract_source

    ctx = sanskritisms_ctx or ExtractionContext()
    extraction = extract_source(jsonl_path, ctx=ctx)
    index = build_name_index(extraction, ctx)
    return ctx, json.dumps(index, ensure_ascii=False, indent=2) + '\n'


def export_source(slug, out_dir, jsonl_dir=JSONL_DIR, meta_dir=HERE, write=True,
                   with_sanskritisms=False, sanskritisms_ctx=None,
                   with_ru_morph=False, with_sa_morph=False, dcs_gold=None,
                   with_vidyut_diff=False, vidyut_analyzer=None,
                   with_inline_ana=False):
    """Export one source into out_dir/<slug>/. Returns a stats dict (also
    written as export_report.json when write=True).

    with_sanskritisms=True additionally writes <slug>.sanskritisms_index.json
    into the same directory (H760 Wave 3 deliverable 3: wire the указатели
    into the export frame). sanskritisms_ctx lets a caller reuse one
    ExtractionContext (lemma pool + reverse index) across many sources
    instead of rebuilding it per call.
    """
    jsonl_path = os.path.join(jsonl_dir, slug + '.jsonl')
    if not os.path.exists(jsonl_path):
        raise FileNotFoundError(jsonl_path)
    meta = load_meta(slug, meta_dir)
    pairs, stats = classify(jsonl_path)
    if with_inline_ana and dcs_gold is None:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        from dcs_align import DcsGold
        dcs_gold = DcsGold()
    artifacts = {
        slug + '.nkrya.xml': nkrya_xml(slug, pairs, meta,
                                       inline_ana=with_inline_ana, dcs=dcs_gold),
        slug + '.tmx': tmx(slug, pairs, meta),
        slug + '.tsv': tsv(pairs),
    }
    inline_ana_stats = {}
    if with_inline_ana:
        s = getattr(nkrya_xml, 'last_ana_stats', {}) or {}
        inline_ana_stats = {'inline_ana': dict(s)}
    if with_sanskritisms:
        sanskritisms_ctx, index_json = _sanskritisms_artifact(slug, jsonl_path, sanskritisms_ctx)
        artifacts[slug + '.sanskritisms_index.json'] = index_json
    if with_ru_morph:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        artifacts[slug + '.ru_morph.tsv'] = ru_morph_tsv(pairs)
    # The SA-side layers key off every Sanskrit-bearing group, NOT the bilingual
    # pairs — an untranslated source (GRETIL yuddha/uttarakāṇḍa) still has gold.
    units = sa_units(jsonl_path) if (with_sa_morph or with_vidyut_diff) else []
    sa_morph_stats = {}
    if with_sa_morph:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        if dcs_gold is None:
            from dcs_align import DcsGold
            dcs_gold = DcsGold()
        artifacts[slug + '.sa_morph.tsv'] = sa_morph_tsv(units, slug, dcs_gold)
        covered = sum(1 for p in units
                      if dcs_gold.gold_tokens(
                          slug, p['group'].split(':', 1)[1] if ':' in p['group'] else ''))
        sa_morph_stats = {
            'sa_morph_dcs_available': dcs_gold.available,
            'sa_morph_units': len(units),
            'sa_morph_units_covered': covered,
            # kept under the old key so existing dashboards don't break; it now
            # counts SA units, which is a superset of the bilingual pairs.
            'sa_morph_pairs_covered': covered,
        }
    vidyut_diff_stats = {}
    if with_vidyut_diff:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        if dcs_gold is None:
            from dcs_align import DcsGold
            dcs_gold = DcsGold()
        if vidyut_analyzer is None:
            from vidyut_diff import VidyutAnalyzer
            vidyut_analyzer = VidyutAnalyzer()
        diff_text, diff_agg = vidyut_diff_tsv(units, slug, dcs_gold, vidyut_analyzer)
        artifacts[slug + '.vidyut_diff.tsv'] = diff_text
        vidyut_diff_stats = {
            'vidyut_available': vidyut_analyzer.available,
            'vidyut_diff': diff_agg,
        }
    report = {
        'slug': slug,
        'exporter_version': VERSION,
        'title': meta.get('title_ru') or slug,
        'translator': meta.get('credit'),
        'rights': meta.get('rights'),
        'needs_review': meta.get('needs_review', True),
        **stats,
        **sa_morph_stats,
        **vidyut_diff_stats,
        **inline_ana_stats,
        'files': sorted(artifacts),
    }
    if write:
        dest = os.path.join(out_dir, slug)
        os.makedirs(dest, exist_ok=True)
        for name, text in artifacts.items():
            _write(os.path.join(dest, name), text)
        _write(os.path.join(dest, 'export_report.json'),
               json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    report['_artifacts'] = artifacts  # in-memory only, not serialized
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description='НКРЯ parallel triple export (H754).')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--source', help='one pilot slug')
    g.add_argument('--all-pilot', action='store_true',
                   help='export all %d pilot sources' % len(PILOT_SOURCES))
    g.add_argument('--all-ru', action='store_true',
                   help='export EVERY seg=ru source (discover_ru_sources; ~131) — Wave 4 full-corpus freeze (H821)')
    ap.add_argument('--out', required=True, help='output directory')
    ap.add_argument('--with-sanskritisms', action='store_true',
                     help='also write <slug>.sanskritisms_index.json (H760 Wave 3)')
    ap.add_argument('--ru-morph', action='store_true',
                     help='also write <slug>.ru_morph.tsv — per-token RU morphology '
                          'layer, lemma/POS/case/number via pymorphy3 (H905)')
    ap.add_argument('--sa-morph', action='store_true',
                     help='also write <slug>.sa_morph.tsv — per-token SA morphology '
                          'anchored on DCS gold (lemma/upos/case/gender/number); needs '
                          'the local DCS sqlite (set $DCS_SQLITE) (H906)')
    ap.add_argument('--vidyut-diff', action='store_true',
                     help='also write <slug>.vidyut_diff.tsv — the vidyut second-opinion '
                          'diff against DCS gold (form-match + per-feature agreement); '
                          'needs the local DCS sqlite AND the vidyut data pack '
                          '(set $VIDYUT_DATA) (H906)')
    ap.add_argument('--inline-ana', action='store_true',
                     help='fold the morphology INTO the para-XML as НКРЯ '
                          '<w><ana lex= gr=/> per token (shared H905/H906 '
                          'scheme). RU via pymorphy3; SA only where the DCS '
                          'gold attaches to the surface end-to-end, plain text '
                          'otherwise — never guessed (H906)')
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args(argv)

    if a.all_ru:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        from sanskritisms.extract import discover_ru_sources
        slugs = discover_ru_sources()
    elif a.all_pilot:
        slugs = PILOT_SOURCES
    else:
        slugs = [a.source]
    sanskritisms_ctx = None
    if a.with_sanskritisms:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        from sanskritisms.extract import ExtractionContext
        sanskritisms_ctx = ExtractionContext()  # built once, reused across slugs
    dcs_gold = None
    if a.sa_morph or a.vidyut_diff or a.inline_ana:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        from dcs_align import DcsGold
        dcs_gold = DcsGold()  # one read-only DCS connection, reused across slugs
        if not dcs_gold.available and not a.quiet:
            print('DCS sqlite not found (set $DCS_SQLITE); DCS-anchored layers '
                  'will be empty.')
    vidyut_analyzer = None
    if a.vidyut_diff:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        from vidyut_diff import VidyutAnalyzer
        vidyut_analyzer = VidyutAnalyzer()  # one Chedaka, reused across slugs
        if not vidyut_analyzer.available and not a.quiet:
            print('--vidyut-diff: vidyut data pack not found (set $VIDYUT_DATA); '
                  'vidyut_diff.tsv will be empty.')
    reports = []
    for slug in slugs:
        r = export_source(slug, a.out, with_sanskritisms=a.with_sanskritisms,
                           sanskritisms_ctx=sanskritisms_ctx,
                           with_ru_morph=a.ru_morph,
                           with_sa_morph=a.sa_morph, dcs_gold=dcs_gold,
                           with_vidyut_diff=a.vidyut_diff,
                           vidyut_analyzer=vidyut_analyzer,
                           with_inline_ana=a.inline_ana)
        reports.append(r)
        if not a.quiet:
            print('%-32s pairs=%-5d mono_ru=%-3d mono_sa=%-3d comm=%-5d empty=%d'
                  % (slug, r['pairs'], r['mono_ru'], r['mono_sa'],
                     r['commentary'], r['empty_side']))
    if not a.quiet:
        print('total pairs:', sum(r['pairs'] for r in reports))
    return reports


if __name__ == '__main__':
    main()
