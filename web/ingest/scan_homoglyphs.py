# -*- coding: utf-8 -*-
"""Corpus-wide scan for Cyrillic homoglyphs in Latin/IAST contexts.

A 'Latin-context' field must not contain Cyrillic; any Cyrillic letter there is
a homoglyph masquerading as Latin (с->c, а->a, …) that silently corrupts the
word / alignment key. We check:
  - every record's `slp1` field            (always SLP1-Latin)
  - `text`/`html` of IAST segments         (id endswith '#sa', or script iast/slp1/hk/roman)

Reads git-HEAD copies so the ORIGINAL corruption is reported even after a local
fix.  Emits HOMOGLYPH_WORDS.tsv  (bad_token  good_token  field  canonical_id  file).
"""
import json, sys, re, glob, os, subprocess, collections
sys.stdout.reconfigure(encoding='utf-8')
CYR = re.compile('[А-Яа-яЁё]')
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
JREL = 'web/corpus_builder/jsonl'
LATIN_SCRIPTS = {'iast', 'slp1', 'hk', 'roman', 'latin', 'translit'}
# full visual-confusable Cyrillic->Latin map (lower+upper)
HOMO = {'а':'a','А':'A','е':'e','Е':'E','о':'o','О':'O','р':'p','Р':'P','с':'c','С':'C',
        'у':'y','х':'x','Х':'X','і':'i','ј':'j','ѕ':'s','к':'k','К':'K','м':'M','М':'M',
        'н':'H','Н':'H','т':'T','Т':'T','в':'B','В':'B','г':'r','ь':'b'}

def from_head(relpath):
    try:
        return subprocess.run(['git','-C',REPO,'show',f'HEAD:{relpath}'],
                              capture_output=True, encoding='utf-8').stdout
    except Exception:
        return ''

# Latin / IAST letters (incl. diacritics + Latin-1) — what a homoglyph hides among
LAT = re.compile('[A-Za-zÀ-ɏḀ-ỿ]')
def is_homoglyph_word(tok):
    """True iff tok mixes Latin/IAST with ONLY visually-confusable Cyrillic
    (so it is a corrupted Latin word, not genuine Russian)."""
    cyrs = [c for c in tok if CYR.match(c)]
    if not cyrs or not LAT.search(tok):
        return False
    return all(c in HOMO for c in cyrs)
def fix_token(tok):
    return ''.join(HOMO.get(c, c) for c in tok)

rows = []
for fp in sorted(glob.glob(os.path.join(REPO, JREL, '*.jsonl'))):
    rel = JREL + '/' + os.path.basename(fp)
    content = from_head(rel) or open(fp, encoding='utf-8').read()
    fn = os.path.basename(fp)
    for line in content.splitlines():
        if not line.strip():
            continue
        try: r = json.loads(line)
        except Exception: continue
        cid = r.get('id', '')
        ctx = 'iast-sa' if str(cid).endswith('#sa') else 'other'
        for field in ('text', 'html', 'slp1'):
            val = r.get(field)
            if not val or not CYR.search(val):
                continue
            for tok in re.findall(r'\S+', val):
                if not is_homoglyph_word(tok):
                    continue
                good = fix_token(tok)
                if CYR.search(good):
                    continue
                rows.append((ctx, tok.strip('.,;:!?()"«»<>'), good.strip('.,;:!?()"«»<>'), field, cid, fn))

rows = sorted(set(rows))
byctx = collections.Counter(r[0] for r in rows)
# ONLY iast-sa (verse Sanskrit) tokens are genuine homoglyph corruptions: in an
# IAST field, Cyrillic is always an error. The 'other' matches are FALSE
# POSITIVES — real Russian words glued to Latin HTML/punctuation (&quot;огонь&quot)
# or Vasmer's deliberate Latin+Cyrillic Proto-Slavic notation (*Dunajь). Not fixed.
sa = [r for r in rows if r[0] == 'iast-sa']
print(f'total mixed-script tokens: {len(rows)}  (by context: {dict(byctx)})')
print(f'GENUINE homoglyph corruptions (iast-sa): {len(sa)} occurrences, '
      f'{len({r[1] for r in sa})} distinct words')
print(f"'other' = {byctx.get('other',0)} FALSE POSITIVES (Russian text / Vasmer notation) — NOT fixed")
out = os.path.join(HERE, 'HOMOGLYPH_WORDS.tsv')
with open(out, 'w', encoding='utf-8') as f:
    f.write('bad_token\tgood_token\tfield\tcanonical_id\tfile\n')
    for _ctx, bad, good, field, cid, fn in sa:
        f.write(f'{bad}\t{good}\t{field}\t{cid}\t{fn}\n')
print('wrote', out, '(iast-sa only)')
print('\n--- genuine homoglyph corruptions ---')
for _c, bad, good, field, cid, fn in sa:
    print(f'  {bad} -> {good}  [{field}]  {cid}')
