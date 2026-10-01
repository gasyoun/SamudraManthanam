#!/usr/bin/env python
"""H5281 — build the НКРЯ showcase package («витрина», MG P3 23-09-2026).

Exports the 24 SHOWCASE_SOURCES (Rigveda I–X, ten Bhagavadgītā translations,
MBh III, Rām I–III) as para-XML (НКРЯ header fields + inline <w><ana/>) + TMX +
TSV + the DCS gold `sa_morph.tsv` sidecar, and writes into the staging dir:

  * MANIFEST.tsv            one row per text: НКРЯ fields + package-only fields
  * SHOWCASE_VALIDATION.md  per-text pairs vs the committed FULL_CORPUS_VALIDATION
  * README.md               what is inside, citation, attribution, rights, gaps
  * nkrya-showcase-v1.zip           everything (GitHub release asset; in-copyright
                                    texts — the release is a DRAFT until MG rules)
  * nkrya-showcase-pd-v1.zip        public-domain texts only (TSV + TMX) — the
                                    samskrtam.ru corpus-linguist page downloads

MANIFEST.tsv and SHOWCASE_VALIDATION.md carry metadata only (no text) and are
committed under nkrya-parallel/export/showcase/; the bulk stays out of git.
Deterministic: no clock in any artifact; zip entries carry a fixed timestamp.

Usage:
  DCS_SQLITE=.../dcs_full.sqlite python build_nkrya_showcase_package.py --out /tmp/showcase
"""
import argparse
import hashlib
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nkrya_export as nx  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
VALIDATION_MD = os.path.join(REPO, 'nkrya-parallel', 'export', 'FULL_CORPUS_VALIDATION.md')
BLOB = 'https://github.com/gasyoun/SamudraManthanam/blob/main/'
ZIP_DATE = (2026, 9, 23, 0, 0, 0)
DATE = '23-09-2026'

MANIFEST_COLS = ['slug', *nx.NKRYA_HEADER_FIELDS, 'publisher', 'series', 'edition',
                 'via_lang', 'rights_class', 'pairs', 'commentary_excluded',
                 'sa_inline_ana', 'sa_morph_units_covered', 'doubt']

DCS_GAPS = {
    'rigveda': 'DCS holds the Ṛgveda (1,028 hymns) but its sentences carry no verse '
               'number (sent_counter NULL), so gold cannot be attached per verse '
               'without guessing — not attached.',
    'bhagavadgita': 'the DCS 2026 dump has no Bhagavadgītā text and no MBh 6.23–40 '
                    'chapters — not covered.',
}


def frozen_counts(path=VALIDATION_MD):
    rows = re.findall(r'^\| `([^`]+)` \| \*\*(\d+)\*\*', open(path, encoding='utf-8').read(), re.M)
    return {s: int(n) for s, n in rows}


def tsv_cell(v):
    return re.sub(r'[\t\r\n]+', ' ', '' if v is None else str(v))


def build(out, dcs):
    stage = os.path.join(out, 'nkrya-showcase-v1')
    rows, reports = [], {}
    for slug in nx.SHOWCASE_SOURCES:
        r = nx.export_source(slug, stage, with_inline_ana=True, with_sa_morph=True, dcs_gold=dcs)
        reports[slug] = r
        meta = nx.load_meta(slug)
        b = meta.get('nkrya') or {}
        hdr = r['nkrya_header']
        rows.append({**{'slug': slug}, **hdr, 'publisher': b.get('publisher'),
                     'series': b.get('series'), 'edition': b.get('edition'),
                     'via_lang': b.get('via_lang'), 'rights_class': b.get('rights_class'),
                     'pairs': r['pairs'], 'commentary_excluded': r['commentary'],
                     'sa_inline_ana': r['inline_ana']['sa_inline'],
                     'sa_morph_units_covered': r.get('sa_morph_units_covered', 0),
                     'doubt': b.get('doubt')})
    manifest = '\t'.join(MANIFEST_COLS) + '\n' + ''.join(
        '\t'.join(tsv_cell(row.get(c)) for c in MANIFEST_COLS) + '\n' for row in rows)
    with open(os.path.join(stage, 'MANIFEST.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(manifest)

    frozen = frozen_counts()
    v = [f'# НКРЯ showcase package v1 — validation report (H5281)\n',
         f'_Created: {DATE} · Last updated: {DATE}_\n',
         'Showcase («витрина», MG ruling P3 in '
         f'[DECISIONS_NKRYA_PARALLEL_SUBMISSION_23-09-2026.md]({BLOB}docs/DECISIONS_NKRYA_PARALLEL_SUBMISSION_23-09-2026.md)): '
         f'{len(rows)} texts, built by [`build_nkrya_showcase_package.py`]({BLOB}web/corpus_builder/build_nkrya_showcase_package.py). '
         'Pair counts are checked against the committed '
         f'[FULL_CORPUS_VALIDATION.md]({BLOB}nkrya-parallel/export/FULL_CORPUS_VALIDATION.md) (Wave-4 freeze, 13-07-2026). '
         'Commentary segments are excluded (MG P9). Sanskrit stays IAST with an SLP1 attribute (MG P5).\n',
         '| Text | НКРЯ translator | date_trans | sphere | Pairs | Frozen | Match | SA inline (DCS) | DCS gold units |',
         '|---|---|---:|---|---:|---:|:---:|---:|---:|']
    ok = 0
    for row in rows:
        fz = frozen.get(row['slug'])
        match = fz == row['pairs']
        ok += match
        v.append(f"| `{row['slug']}` | {row['translator']} | {row['date_trans']} | {row['sphere']} | "
                 f"{row['pairs']} | {fz if fz is not None else '—'} | {'✅' if match else '❌'} | "
                 f"{row['sa_inline_ana']} | {row['sa_morph_units_covered']} |")
    total = sum(r['pairs'] for r in rows)
    v.append(f"\n**{ok} of {len(rows)} texts match the frozen pair counts; {total:,} pairs in the package.**\n")
    v.append('## DCS morphology (MG P7, CC BY 4.0)\n')
    v.append('1. MBh III and Rām I–III: DCS gold ships in full as `<slug>.sa_morph.tsv`; inline '
             '`<w><ana/>` only where DCS tokens attach to the printed surface end-to-end '
             '(all-or-nothing, never guessed) — the same ~1 % as H906 '
             f'([INLINE_ANA_H906_REPORT.md]({BLOB}web/corpus_builder/INLINE_ANA_H906_REPORT.md)).')
    v.append(f"2. Ṛgveda: {DCS_GAPS['rigveda']}")
    v.append(f"3. Bhagavadgītā: {DCS_GAPS['bhagavadgita']}")
    v.append('4. Russian side: pymorphy3 inline `<w><ana/>` on 100 % of pairs.\n')
    v.append('## Artifact checksums (sha256)\n')
    zips = write_zips(out, stage, rows)
    for name, digest in zips:
        v.append(f'- `{name}` — `{digest}`')
    v.append('\n_Dr. Mārcis Gasūns_')
    with open(os.path.join(stage, 'SHOWCASE_VALIDATION.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(v) + '\n')
    return rows, ok, total


README = """# НКРЯ showcase package v1 — Sanskrit–Russian parallel texts (Samudra Manthanam)

Rigveda I–X (Т. Я. Елизаренкова), ten Russian Bhagavadgītā translations (1788–2016),
Mahābhārata III (Я. В. Васильков, С. Л. Невелева), Rāmāyaṇa I–III (П. А. Гринцер).

Per text: `<slug>.nkrya.xml` (НКРЯ meta header: headers_all, authors_all, created,
translator, lang_orig, date_trans, sphere, words; body = 1:1 verse pairs, Sanskrit IAST
with an SLP1 attribute, inline `<w><ana/>`), `<slug>.tmx` (TMX 1.4b), `<slug>.tsv`,
`<slug>.sa_morph.tsv` (DCS gold, where covered), `export_report.json`.
`MANIFEST.tsv` holds every text's bibliography, including fields НКРЯ has no slot for.

Cite: Gasūns M. Samudra Manthanam: a markup-aligned Sanskrit–Russian parallel corpus
(paper A41, in preparation). Corpus dataset DOI 10.5281/zenodo.22149933; software concept
DOI 10.5281/zenodo.21317315. Contact: gasyoun@ya.ru.

Sanskrit morphology: Digital Corpus of Sanskrit (O. Hellwig), CC BY 4.0.
Russian morphology: pymorphy3 / OpenCorpora.

Rights: the 1788, 1909 and 1914 Gītā translations are public domain. All other texts are
in-copyright academic translations, supplied to НКРЯ for search; they are not for
redistribution as a dump.
"""


def _zip(path, files, stage):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            info = zipfile.ZipInfo(rel, ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(stage, rel), 'rb') as f:
                z.writestr(info, f.read())
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def write_zips(out, stage, rows):
    with open(os.path.join(stage, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(README)
    every = sorted(os.path.relpath(os.path.join(d, n), stage)
                   for d, _, ns in os.walk(stage) for n in ns
                   if n != 'SHOWCASE_VALIDATION.md')
    pd = sorted(f"{r['slug']}/{r['slug']}{ext}" for r in rows
                if r['rights_class'] == 'public-domain' for ext in ('.tsv', '.tmx'))
    pd += ['README.md', 'MANIFEST.tsv']
    return [('nkrya-showcase-v1.zip', _zip(os.path.join(out, 'nkrya-showcase-v1.zip'), every, stage)),
            ('nkrya-showcase-pd-v1.zip', _zip(os.path.join(out, 'nkrya-showcase-pd-v1.zip'), pd, stage))]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    from dcs_align import DcsGold
    dcs = DcsGold()
    if not dcs.available:
        sys.exit('DCS sqlite not found — set $DCS_SQLITE (MG P7 needs the gold layer)')
    rows, ok, total = build(a.out, dcs)
    print(f'{len(rows)} texts, {total:,} pairs, {ok}/{len(rows)} match frozen counts')
    if ok != len(rows):
        sys.exit(1)


if __name__ == '__main__':
    main()
