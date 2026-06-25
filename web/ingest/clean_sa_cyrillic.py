# -*- coding: utf-8 -*-
"""Strip Cyrillic leakage from verse-Sanskrit (#sa) segments of the corpus jsonl.

Three defect classes, all editorial artifacts that do not belong in a Sanskrit
(IAST) text field:
  1. `БхГ X.Y`  Bhagavad-Gītā cross-reference markers      -> delete
  2. `{…}` / `[…]` notes containing Cyrillic (e.g. {Проверить!}, [Нет на GRETIL]) -> delete
  3. Cyrillic homoglyphs inside IAST words (с->c, а->a)     -> transliterate

ONLY touches records whose id ends in '#sa'. Russian (#ru) and dictionary
glosses (legitimately Cyrillic) are never touched. Hard-asserts that no Cyrillic
remains in a cleaned field — an unexpected Cyrillic char aborts the run rather
than risk silent corruption.

  python clean_sa_cyrillic.py            # dry-run: report + sample diffs
  python clean_sa_cyrillic.py --apply    # rewrite the jsonl in place
"""
import json, sys, re, glob, os, collections
sys.stdout.reconfigure(encoding='utf-8')
CYR = re.compile('[А-Яа-яЁё]')
HERE = os.path.dirname(os.path.abspath(__file__))
JDIR = os.path.join(HERE, '..', 'corpus_builder', 'jsonl')
APPLY = '--apply' in sys.argv

BHG  = re.compile(r'\s*БхГ\s*\d+(?:\.\d+)*')                 # 1. citation marker
NOTE = re.compile(r'\s*\{[^}]*[А-Яа-яЁё][^}]*\}|\s*\[[^\]]*[А-Яа-яЁё][^\]]*\]')  # 2. cyr notes
HOMO = {'с': 'c', 'С': 'C', 'а': 'a', 'А': 'A'}             # 3. confirmed homoglyphs

def clean(s):
    if not s or not CYR.search(s):
        return s
    s = BHG.sub('', s)
    s = NOTE.sub('', s)
    s = ''.join(HOMO.get(ch, ch) for ch in s)
    # tidy spacing the deletions leave behind
    s = re.sub(r'\s+([।॥])', r' \1', s)        # " ।" not "  ।"
    s = re.sub(r'([।॥])(\d+)\s+([।॥])', r'\1\2\3', s)  # "॥1 ॥" -> "॥1॥"
    s = re.sub(r'[ \t]{2,}', ' ', s).strip()
    if CYR.search(s):                          # safety: never leave Cyrillic behind
        bad = sorted({c for c in s if CYR.match(c)})
        raise SystemExit(f'ABORT: un-handled Cyrillic {bad} remains in: {s[:120]!r}')
    return s

cat = collections.Counter(); changed = 0; samples = []
for fp in sorted(glob.glob(os.path.join(JDIR, '*.jsonl'))):
    out = []; file_changed = False
    for raw in open(fp, encoding='utf-8'):
        line = raw.rstrip('\n')
        if not line.strip():
            out.append(raw); continue
        r = json.loads(line)
        if str(r.get('id', '')).endswith('#sa'):
            orig = (r.get('text'), r.get('html'), r.get('slp1'))
            for f in ('text', 'html', 'slp1'):
                if r.get(f):
                    if BHG.search(r[f]): cat['БхГ'] += BHG.subn('', r[f])[1] if f == 'text' else 0
                    r[f] = clean(r[f])
            if (r.get('text'), r.get('html'), r.get('slp1')) != orig:
                changed += 1; file_changed = True
                if len(samples) < 6 and orig[0] != r.get('text'):
                    samples.append((r['id'], orig[0], r.get('text')))
                out.append(json.dumps(r, ensure_ascii=False) + '\n')
                continue
        out.append(raw if raw.endswith('\n') else raw + '\n')
    if file_changed and APPLY:
        open(fp, 'w', encoding='utf-8', newline='').write(''.join(out))

print(f"{'APPLIED' if APPLY else 'DRY-RUN'}: {changed} #sa records cleaned")
print('БхГ markers removed (text):', cat['БхГ'])
print('\nsample before -> after:')
for cid, a, b in samples:
    print(f'  {cid}')
    print(f'    -  {a[:95]!r}')
    print(f'    +  {b[:95]!r}')
