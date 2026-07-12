"""GRETIL-TEI Ramayana (id-attribute convention) -> canonical JSONL converter.

H765: `sa_rAmAyaNa.xml` (GRETIL's full-recension Valmiki Ramayana TEI) uses a
different verse-anchoring convention than the one `gretil_tei_to_canonical.py`
handles (H308 Track 1, "inline trailing marker" e.g. Hitopadesha). Here every
<lg> carries its citation directly as an `xml:id` attribute, and each kāṇḍa
(book) is its own <div type="kāṇḍa" n="N">:

    <div type="kāṇḍa" n="6">
      <lg xml:id="R_6.001.001">
        <l xml:id="R_6.001.001ab">...</l>
        <l xml:id="R_6.001.001cd">...</l>
      </lg>
      ...

There is no per-sarga (chapter) <div> -- the chapter number is recovered from
the lg's own xml:id (the middle dotted segment). This is Sanskrit-only, same
canonical schema as html_to_canonical.py so a Russian translation sourced
later can be added under the same `group` key without re-minting Sanskrit IDs
(same contract as gretil_tei_to_canonical.py).

Usage:
    python web/corpus_builder/gretil_ramayana_kanda_to_canonical.py \
        --tei GRETIL-1_sanskr/tei/sa_rAmAyaNa.xml \
        --kanda 6 --work 06_ramayana-yuddhakanda \
        --output-dir web/corpus_builder/jsonl
"""

import sys
import re
import json
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WEB_DIR = _REPO_ROOT / 'web'
sys.path.insert(0, str(_WEB_DIR))

from corpus_builder.html_to_canonical import _to_slp1, _strip_accents

_TEI_NS = '{http://www.tei-c.org/ns/1.0}'

_LG_ID_RE = re.compile(r'^R_(\d+)\.(\d+)\.(\d+)$')


def _local(tag: str) -> str:
    if '}' in tag:
        return tag.split('}', 1)[-1]
    return tag


def _l_text(l_el: ET.Element) -> str:
    """Text of an <l>, joining any nested <seg type="pāda"> children."""
    parts = [t for t in l_el.itertext()]
    return ' '.join(p.strip() for p in parts if p.strip())


def _build_sa_record(
    slug: str, passage: str, group: str, text: str, html: str,
    chapter: str, seq: int,
) -> dict:
    text_stripped = _strip_accents(text)
    slp1 = _to_slp1(text)

    return {
        'id': f'{slug}:{passage}#sa',
        'work': slug,
        'passage': passage,
        'seg': 'sa',
        'group': group,
        'lang': 'sa',
        'script': 'iast',
        'text': text_stripped,
        'html': html,
        'slp1': slp1,
        'structure': 'verse',
        'chapter': chapter,
        'seq': seq,
        'deleted': False,
    }


def convert_kanda(tei_path: Path, kanda: int, slug: str):
    tree = ET.parse(tei_path)
    root = tree.getroot()

    kanda_div = None
    for div in root.iter(f'{_TEI_NS}div'):
        if div.get('type') == 'kāṇḍa' and div.get('n') == str(kanda):
            kanda_div = div
            break

    if kanda_div is None:
        raise ValueError(f'No <div type="kāṇḍa" n="{kanda}"> in {tei_path}')

    records = []
    report = {
        'work': slug,
        'kanda': kanda,
        'verse_count': 0,
        'unmarked_verse_count': 0,
        'unmarked_examples': [],
    }
    seq = 0

    for lg in kanda_div.iter(f'{_TEI_NS}lg'):
        lg_id = (
            lg.get(f'{_TEI_NS}id')
            or lg.get('id')
            or lg.get('{http://www.w3.org/XML/1998/namespace}id')
        )

        l_texts = [_l_text(l_el) for l_el in lg.findall(f'{_TEI_NS}l')]
        full_text = ' '.join(t for t in l_texts if t)
        seq += 1

        m = _LG_ID_RE.match(lg_id) if lg_id else None
        if m:
            _book, chapter_raw, verse_raw = m.groups()
            chapter = str(int(chapter_raw))
            verse = str(int(verse_raw))
            passage = f'{chapter}.{verse}'
            html = '<br>'.join(t for t in l_texts if t)
            group = f'{slug}:{passage}'
            records.append(_build_sa_record(slug, passage, group, full_text, html, chapter, seq))
            report['verse_count'] += 1
        else:
            report['unmarked_verse_count'] += 1
            if len(report['unmarked_examples']) < 5:
                report['unmarked_examples'].append((lg_id, full_text[:80]))
            passage = f'unmarked.{seq}'
            group = f'{slug}:{passage}'
            records.append(_build_sa_record(slug, passage, group, full_text, full_text, '0', seq))
            records[-1]['needs_review'] = True

    return records, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--tei', required=True, help='Path to the GRETIL TEI XML file')
    ap.add_argument('--kanda', required=True, type=int, help='Kāṇḍa number (1-7)')
    ap.add_argument('--work', required=True, help='Canonical work slug')
    ap.add_argument('--output-dir', default='web/corpus_builder/jsonl')
    args = ap.parse_args()

    tei_path = Path(args.tei)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    records, report = convert_kanda(tei_path, args.kanda, args.work)

    jsonl_path = out_dir / f'{args.work}.jsonl'
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False))
            f.write('\n')

    report_path = out_dir / f'{args.work}.report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f'{args.work}: {len(records)} records ({report["verse_count"]} verse, {report["unmarked_verse_count"]} unmarked) -> {jsonl_path}')


if __name__ == '__main__':
    main()
