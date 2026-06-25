# -*- coding: utf-8 -*-
"""SERVER-SIDE fix: strip Cyrillic leakage from verse-Sanskrit (#sa) rows of a
deployed corpus.db, so the live corpus matches the cleaned jsonl source without
a full re-ingest. Idempotent and safe to re-run.

corpus_lines is an fts5 table, so a plain UPDATE maintains the search index.
Three defect classes are handled (all editorial artifacts, never real Sanskrit):
  1. `БхГ X.Y`           Bhagavad-Gītā cross-ref markers      -> delete
  2. `{…}` / `[…]` notes containing Cyrillic                  -> delete
  3. Cyrillic homoglyphs inside IAST words (с→c, а→a)         -> transliterate
     (the genuine word-corrupting class; see HOMOGLYPH_WORDS.tsv)

ONLY rows whose canonical_id ends in '#sa' are touched. A hard assert aborts the
run if any un-handled Cyrillic would remain — never risk silent corruption.

  python fix_corpus_db_sa.py --db /path/to/corpus.db          # dry-run
  python fix_corpus_db_sa.py --db /path/to/corpus.db --apply  # write
"""
import sqlite3, sys, re, os, argparse, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

CYR  = re.compile('[А-Яа-яЁё]')
BHG  = re.compile(r'\s*БхГ\s*\d+(?:\.\d+)*')
NOTE = re.compile(r'\s*\{[^}]*[А-Яа-яЁё][^}]*\}|\s*\[[^\]]*[А-Яа-яЁё][^\]]*\]')
HOMO = {'с': 'c', 'С': 'C', 'а': 'a', 'А': 'A'}   # confirmed Latin-look-alike Cyrillic

def clean(s):
    if not s or not CYR.search(s):
        return s, False
    had_homo = any(c in HOMO for c in BHG.sub('', NOTE.sub('', s)))
    s = BHG.sub('', s)
    s = NOTE.sub('', s)
    s = ''.join(HOMO.get(ch, ch) for ch in s)
    s = re.sub(r'\s+([।॥])', r' \1', s)
    s = re.sub(r'([।॥])(\d+)\s+([।॥])', r'\1\2\3', s)
    s = re.sub(r'[ \t]{2,}', ' ', s).strip()
    if CYR.search(s):
        bad = sorted({c for c in s if CYR.match(c)})
        raise SystemExit(f'ABORT: un-handled Cyrillic {bad} in: {s[:120]!r}')
    return s, had_homo

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', required=True, help='path to the server corpus.db')
    ap.add_argument('--apply', action='store_true', help='write changes (default: dry-run)')
    a = ap.parse_args()
    if not os.path.exists(a.db):
        raise SystemExit(f'db not found: {a.db}')
    db = sqlite3.connect(a.db)
    rows = db.execute(
        "SELECT rowid, canonical_id, line_text, line_html FROM corpus_lines "
        "WHERE canonical_id LIKE '%#sa' AND (line_text GLOB '*[А-Яа-яЁё]*' "
        "   OR line_html GLOB '*[А-Яа-яЁё]*')").fetchall()
    changed = 0; homo_rows = []
    for rid, cid, txt, html in rows:
        ntxt, txt_homo = clean(txt) if txt else (txt, False)
        nhtml, html_homo = clean(html) if html else (html, False)
        if ntxt != txt or nhtml != html:
            changed += 1
            if txt_homo or html_homo:
                homo_rows.append((cid, txt, ntxt))
            if a.apply:
                db.execute("UPDATE corpus_lines SET line_text=?, line_html=? WHERE rowid=?",
                           (ntxt, nhtml, rid))
    if a.apply:
        db.commit()
    left = db.execute("SELECT COUNT(*) FROM corpus_lines WHERE canonical_id LIKE '%#sa' "
                      "AND line_text GLOB '*[А-Яа-яЁё]*'").fetchone()[0]
    print(f"{'APPLIED' if a.apply else 'DRY-RUN'}: {changed} #sa rows cleaned "
          f"({len(homo_rows)} contained homoglyph words)")
    print(f"#sa rows with Cyrillic remaining after: {left if a.apply else '(dry-run)'}")
    for cid, before, after in homo_rows:
        bad = [t for t in re.findall(r'\S+', before or '') if CYR.search(t) and 'БхГ' not in t]
        print(f"  homoglyph fixed @ {cid}: {' '.join(bad)!r}")
    db.close()

if __name__ == '__main__':
    main()
