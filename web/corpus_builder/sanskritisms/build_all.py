#!/usr/bin/env python
r"""H760 -- run the sanskritism extractor across every ru-bearing source.

Writes, per source, a gitignored full-detail lexicon+index JSON (bulk
output -- same rights posture as the H754 export artifacts: in-copyright
running text feeds the extraction, but only counts leave the gitignore),
and one committed counts report summarizing every source.

Usage:
  python build_all.py --out nkrya-parallel/sanskritisms
  python build_all.py --out DIR --source 03_mahabharata-aranyakaparva
  python build_all.py --out DIR --quiet
"""
import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from sanskritisms.extract import (  # noqa: E402
    ExtractionContext, build_name_index, discover_ru_sources, extract_source,
)
from sanskritisms._paths import JSONL_DIR  # noqa: E402


def run_source(slug, ctx, out_dir, write=True):
    jsonl_path = os.path.join(JSONL_DIR, slug + '.jsonl')
    extraction = extract_source(jsonl_path, ctx=ctx)
    index = build_name_index(extraction, ctx)
    report = {
        'slug': slug,
        **extraction['stats'],
        'epithet_occurrences': sum(e['count'] for e in extraction['epithets'].values()),
    }
    if write:
        dest = os.path.join(out_dir, slug)
        os.makedirs(dest, exist_ok=True)
        with open(os.path.join(dest, slug + '.lexicon.json'), 'w', encoding='utf-8') as f:
            json.dump(extraction['lexicon'], f, ensure_ascii=False, indent=2, sort_keys=True)
        with open(os.path.join(dest, slug + '.epithets.json'), 'w', encoding='utf-8') as f:
            json.dump(extraction['epithets'], f, ensure_ascii=False, indent=2, sort_keys=True)
        with open(os.path.join(dest, slug + '.index.json'), 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    return report


def write_counts_report(reports, out_dir):
    total = {
        'sources': len(reports),
        'groups': sum(r['groups'] for r in reports),
        'tokens': sum(r['tokens'] for r in reports),
        'candidate_matches': sum(r['candidate_matches'] for r in reports),
        'lemmas_total': sum(r['lemmas'] for r in reports),
        'epithet_bases_total': sum(r['epithet_bases'] for r in reports),
        'epithet_occurrences_total': sum(r['epithet_occurrences'] for r in reports),
    }
    lines = [
        '# H760 sanskritisms -- corpus-wide counts report',
        '',
        '_Committed validation artifact (H760 deliverable 2). Bulk per-source',
        'lexicon/epithets/index JSON is gitignored; regenerate with',
        '`python web/corpus_builder/sanskritisms/build_all.py --out nkrya-parallel/sanskritisms`._',
        '',
        '## Totals',
        '',
        '| sources | groups (verses) | tokens | candidate matches | lemmas (summed) | epithet bases (summed) | epithet occurrences |',
        '|---:|---:|---:|---:|---:|---:|---:|',
        '| %d | %d | %d | %d | %d | %d | %d |' % (
            total['sources'], total['groups'], total['tokens'],
            total['candidate_matches'], total['lemmas_total'],
            total['epithet_bases_total'], total['epithet_occurrences_total']),
        '',
        '## Per source',
        '',
        '| slug | groups | tokens | candidate matches | lemmas | epithet bases | epithet occurrences |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for r in sorted(reports, key=lambda r: r['slug']):
        lines.append('| %s | %d | %d | %d | %d | %d | %d |' % (
            r['slug'], r['groups'], r['tokens'], r['candidate_matches'],
            r['lemmas'], r['epithet_bases'], r['epithet_occurrences']))
    lines.append('')
    path = os.path.join(out_dir, 'COUNTS_REPORT.md')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines))
    return path, total


def main(argv=None):
    ap = argparse.ArgumentParser(description='Sanskritism extractor, corpus-wide (H760).')
    ap.add_argument('--out', required=True, help='output directory')
    ap.add_argument('--source', help='run one slug only (default: all ru-bearing sources)')
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args(argv)

    ctx = ExtractionContext()
    slugs = [a.source] if a.source else discover_ru_sources()

    reports = []
    for slug in slugs:
        r = run_source(slug, ctx, a.out)
        reports.append(r)
        if not a.quiet:
            print('%-40s groups=%-5d lemmas=%-5d matches=%-6d epithets=%d'
                  % (slug, r['groups'], r['lemmas'], r['candidate_matches'],
                     r['epithet_occurrences']))

    os.makedirs(a.out, exist_ok=True)
    path, total = write_counts_report(reports, a.out)
    if not a.quiet:
        print('counts report:', path)
        print('total lemmas (summed across sources):', total['lemmas_total'])
    return reports


if __name__ == '__main__':
    main()
